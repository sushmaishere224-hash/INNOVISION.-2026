"""Calibration checks for the LEWS risk model."""

from app.risk import calculate_risk, get_severity, predisposition_factor


def test_dry_day_stays_low_even_on_high_susceptibility():
    risk = calculate_risk(rainfall_24h=3, soil_moisture=0.41, susceptibility=5)
    assert risk < 30
    assert get_severity(risk) == "LOW"


def test_damp_soil_alone_cannot_alert():
    risk = calculate_risk(rainfall_24h=0, soil_moisture=0.55, susceptibility=5)
    assert get_severity(risk) == "LOW"


def test_heavy_rain_pinpoints_high_susceptibility():
    high = calculate_risk(rainfall_24h=55, soil_moisture=0.45, susceptibility=5)
    low = calculate_risk(rainfall_24h=55, soil_moisture=0.45, susceptibility=1)
    assert get_severity(high) == "HIGH"
    assert get_severity(low) == "LOW"
    assert high > low * 1.5


def test_building_rain_is_moderate_on_steep_ground():
    risk = calculate_risk(rainfall_24h=30, soil_moisture=0.45, susceptibility=5)
    assert get_severity(risk) == "MODERATE"


def test_extreme_monsoon_on_class_5():
    risk = calculate_risk(rainfall_24h=130, soil_moisture=0.55, susceptibility=5)
    assert get_severity(risk) == "EXTREME"


def test_extreme_rain_on_low_sus_stays_muted():
    risk = calculate_risk(rainfall_24h=130, soil_moisture=0.55, susceptibility=2)
    assert get_severity(risk) in {"LOW", "MODERATE"}


def test_predisposition_increases_with_class():
    factors = [predisposition_factor(s) for s in (1, 2, 3, 4, 5)]
    assert factors == sorted(factors)
    assert factors[-1] == 1.0
