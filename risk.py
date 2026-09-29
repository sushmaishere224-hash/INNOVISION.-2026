"""
LEWS landslide risk and weather prediction scoring for Uttarakhand Himalayas.

Model:
  risk = weather_trigger × susceptibility_predisposition

- Rainfall is the primary trigger (calibrated to IMD & Himalayan rainfall thresholds).
- Soil moisture reflects antecedent wetness & pore-water pressure priming.
- Susceptibility (0–5 class from GSI NLSM terrain mapping) pinpoints where
  heavy precipitation will cause slope failures.
- Multi-horizon prediction scores both current conditions and 24h/48h forecasted weather.
"""

from __future__ import annotations



# ============================================================
# NORMALIZE
# ============================================================

def normalize(value, minimum, maximum) -> float:
    if maximum == minimum:
        return 0.0

    value = max(minimum, min(maximum, float(value)))
    return (value - minimum) / (maximum - minimum)


# ============================================================
# SUSCEPTIBILITY → PREDISPOSITION
# ============================================================

# Maps susceptibility class (GSI/NLSM for Uttarakhand) → how strongly a weather trigger expresses as risk.
# Low classes stay muted even in heavy rain; class 5 fully expresses the trigger.
SUSCEPTIBILITY_FACTOR = {
    None: 0.18,
    0: 0.18,
    1: 0.32,
    2: 0.48,
    3: 0.65,
    4: 0.84,
    5: 1.00,
}


def predisposition_factor(susceptibility) -> float:
    """Pinpoint factor in [0.20, 1.00] from susceptibility class."""
    if susceptibility is None:
        key = None
    else:
        try:
            key = int(susceptibility)
        except (TypeError, ValueError):
            key = None
        if key is not None and key not in SUSCEPTIBILITY_FACTOR:
            key = max(0, min(5, key))

    sus_f = SUSCEPTIBILITY_FACTOR.get(key, 0.18)
    # Keep a small floor so extreme rain on low-sus ground still registers.
    return 0.20 + 0.80 * sus_f


# ============================================================
# RAINFALL TRIGGER (Himalayan/Uttarakhand-calibrated 24h curve)
# ============================================================

def rainfall_trigger_score(rainfall_24h_mm) -> float:
    """
    Map 24h rainfall (mm) → 0–100 trigger intensity.

    Breakpoints reflect Himalayan/Uttarakhand landslide rainfall response:
    drizzle stays low, 20–40 mm builds concern on steep ground,
    40–75 mm is a serious trigger, 75+ mm approaches saturation of the curve.
    """
    mm = max(0.0, float(rainfall_24h_mm or 0))

    if mm <= 5:
        return normalize(mm, 0, 5) * 10
    if mm <= 20:
        return 10 + normalize(mm, 5, 20) * 25
    if mm <= 40:
        return 35 + normalize(mm, 20, 40) * 25
    if mm <= 75:
        return 60 + normalize(mm, 40, 75) * 25
    return 85 + normalize(mm, 75, 150) * 15


# ============================================================
# WEATHER TRIGGER
# ============================================================

def weather_trigger_score(rainfall_24h, soil_moisture) -> float:
    """
    Combine rainfall + antecedent soil into a 0–100 weather trigger.

    Soil uses the natural 0–1 m³/m³ range (Open-Meteo). It amplifies rain and
    only contributes a priming term once rainfall is present — damp ground
    alone cannot push a cell into HIGH.
    """
    rain = max(0.0, float(rainfall_24h or 0))
    # Volumetric soil moisture; 1.0 is fully saturated (not 0.6).
    soil_n = normalize(float(soil_moisture or 0), 0.0, 1.0)
    rain_t = rainfall_trigger_score(rain)

    # Antecedent wetness multiplies rainfall impact.
    antecedent = 0.50 + 0.50 * soil_n
    # Soil priming engages as rain appears (fully by ~15 mm).
    rain_act = normalize(rain, 1.5, 15.0)

    trigger = rain_t * antecedent + soil_n * rain_act * 18.0
    return min(100.0, trigger)


# ============================================================
# CALCULATE RISK
# ============================================================

def calculate_risk(
    rainfall_24h,
    soil_moisture,
    susceptibility,
):
    rain = max(0.0, float(rainfall_24h or 0))
    soil_n = normalize(float(soil_moisture or 0), 0.0, 1.0)
    rain_act = normalize(rain, 1.5, 15.0)

    trigger = weather_trigger_score(rainfall_24h, soil_moisture)
    predisposition = predisposition_factor(susceptibility)

    # Light dry-day texture from terrain (≤5 pts), never an alert by itself.
    dry_texture = predisposition * 5.0 * (1.0 - rain_act) * (0.4 + 0.6 * soil_n)
    trigger = min(100.0, trigger + dry_texture)

    risk = trigger * predisposition
    return round(min(100.0, risk), 2)


def explain_risk(
    rainfall_24h,
    soil_moisture,
    susceptibility,
) -> dict:
    """Component breakdown for APIs / debugging."""
    rain = max(0.0, float(rainfall_24h or 0))
    soil_n = normalize(float(soil_moisture or 0), 0.0, 1.0)
    rain_t = rainfall_trigger_score(rain)
    rain_act = normalize(rain, 1.5, 15.0)
    predisposition = predisposition_factor(susceptibility)

    base_trigger = weather_trigger_score(rainfall_24h, soil_moisture)
    dry_texture = predisposition * 5.0 * (1.0 - rain_act) * (0.4 + 0.6 * soil_n)
    trigger = min(100.0, base_trigger + dry_texture)
    risk = round(min(100.0, trigger * predisposition), 2)

    return {
        "rainfall_24h": round(rain, 2),
        "soil_moisture": round(float(soil_moisture or 0), 4),
        "soil_normalized": round(soil_n, 4),
        "susceptibility": susceptibility,
        "rainfall_trigger": round(rain_t, 2),
        "weather_trigger": round(trigger, 2),
        "predisposition": round(predisposition, 3),
        "risk": risk,
        "severity": get_severity(risk),
    }


# ============================================================
# SEVERITY
# ============================================================

def get_severity(risk) -> str:
    """
    LOW      < 30  — normal / quiet
    MODERATE < 55  — watch (building rain on susceptible ground)
    HIGH     < 78  — elevated action band
    EXTREME  ≥ 78  — severe monsoon on high-susceptibility terrain
    """
    risk = float(risk or 0)

    if risk < 30:
        return "LOW"

    if risk < 55:
        return "MODERATE"

    if risk < 78:
        return "HIGH"

    return "EXTREME"


# ============================================================
# PREDICTED RISK & MULTI-HORIZON EARLY WARNING
# ============================================================

def calculate_predicted_risk(
    predicted_rainfall_24h: float,
    current_soil_moisture: float,
    susceptibility: int | None,
    snowmelt_mm: float = 0.0,
) -> float:
    """
    Compute predicted landslide risk for the upcoming 24h forecast window.
    Accounts for forecasted rainfall and projected saturation increase.
    """
    pred_rain = max(0.0, float(predicted_rainfall_24h or 0)) + max(0.0, float(snowmelt_mm or 0))
    current_soil = max(0.0, min(1.0, float(current_soil_moisture or 0)))

    # Projected soil moisture increase as forecast rain infiltrates steep slopes
    infiltrated_soil = min(1.0, current_soil + (pred_rain / 120.0) * 0.4)

    return calculate_risk(
        rainfall_24h=pred_rain,
        soil_moisture=infiltrated_soil,
        susceptibility=susceptibility,
    )


def calculate_multi_horizon_risk(
    past_rainfall_24h: float,
    predicted_rainfall_24h: float,
    predicted_rainfall_48h: float,
    soil_moisture: float,
    susceptibility: int | None,
) -> dict:
    """
    Multi-horizon landslide hazard evaluation:
    - Current (antecedent 24h)
    - Short-term forecast (upcoming 24h)
    - Medium-term forecast (cumulative 48h)
    """
    curr_risk = calculate_risk(
        rainfall_24h=past_rainfall_24h,
        soil_moisture=soil_moisture,
        susceptibility=susceptibility,
    )
    pred_risk_24h = calculate_predicted_risk(
        predicted_rainfall_24h=predicted_rainfall_24h,
        current_soil_moisture=soil_moisture,
        susceptibility=susceptibility,
    )
    # 48h outlook: discount second 24h slightly for model uncertainty
    rain_48h = max(0.0, float(predicted_rainfall_48h or 0))
    pred_risk_48h = calculate_predicted_risk(
        predicted_rainfall_24h=rain_48h * 0.9,
        current_soil_moisture=soil_moisture,
        susceptibility=susceptibility,
    )

    max_risk = max(curr_risk, pred_risk_24h, pred_risk_48h)
    max_severity = get_severity(max_risk)

    if max_severity == "EXTREME":
        action = "Evacuate high-risk slopes immediately; major debris flow threat."
    elif max_severity == "HIGH":
        action = "High landslide alert; avoid mountain road corridors and vulnerable cuts."
    elif max_severity == "MODERATE":
        action = "Watch advisory; check ground fissures and drainage pathways."
    else:
        action = "Normal monitoring; conditions stable."

    return {
        "current_risk": curr_risk,
        "current_severity": get_severity(curr_risk),
        "predicted_risk_24h": pred_risk_24h,
        "predicted_severity_24h": get_severity(pred_risk_24h),
        "predicted_risk_48h": pred_risk_48h,
        "predicted_severity_48h": get_severity(pred_risk_48h),
        "peak_risk": max_risk,
        "peak_severity": max_severity,
        "recommended_action": action,
    }

