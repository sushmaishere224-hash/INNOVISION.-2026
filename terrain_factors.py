"""
Terrain, Slope, Elevation, and Soil Characteristics Model for Uttarakhand Himalayas.
Calibrated with Geological Survey of India (GSI) NLSM and ICAR/NBSS&LUP Soil Mapping.
"""

from __future__ import annotations
import math

from .historical_data import find_nearest_landslide
from .susceptibility import get_district, get_susceptibility


# Key monitored locations across Uttarakhand with verified terrain benchmarks
KNOWN_LOCATIONS = {
    "joshimath": {
        "name": "Joshimath",
        "district": "Chamoli",
        "lat": 30.556,
        "lon": 79.567,
        "elevation_m": 1890,
        "slope_deg": 38.5,
        "soil_type": "Skeletal gravelly colluvium over fragile high-grade gneiss",
        "soil_depth_cm": 65,
        "porosity": 0.44,
        "permeability": "High",
        "gsi_class": 5,
        "geology": "Vaikrita Group (MCT Hanging Wall)",
    },
    "kedarnath": {
        "name": "Kedarnath",
        "district": "Rudraprayag",
        "lat": 30.735,
        "lon": 79.067,
        "elevation_m": 3584,
        "slope_deg": 44.0,
        "soil_type": "Glacial moraine and fractured granitic till",
        "soil_depth_cm": 40,
        "porosity": 0.40,
        "permeability": "Very High",
        "gsi_class": 5,
        "geology": "Central Crystalline Gneisses",
    },
    "chamoli": {
        "name": "Chamoli",
        "district": "Chamoli",
        "lat": 30.417,
        "lon": 79.333,
        "elevation_m": 1550,
        "slope_deg": 36.0,
        "soil_type": "Weathered phyllite and gravelly clayey loam",
        "soil_depth_cm": 80,
        "porosity": 0.42,
        "permeability": "Moderate",
        "gsi_class": 5,
        "geology": "Garhwal Group (Carbonates & Quartzites)",
    },
    "uttarkashi": {
        "name": "Uttarkashi",
        "district": "Uttarkashi",
        "lat": 30.727,
        "lon": 78.435,
        "elevation_m": 1158,
        "slope_deg": 35.0,
        "soil_type": "Colluvial sandy silt with fractured slate scree",
        "soil_depth_cm": 75,
        "porosity": 0.43,
        "permeability": "High",
        "gsi_class": 5,
        "geology": "Bhagirathi Window Zone",
    },
    "rudraprayag": {
        "name": "Rudraprayag",
        "district": "Rudraprayag",
        "lat": 30.284,
        "lon": 78.981,
        "elevation_m": 895,
        "slope_deg": 32.5,
        "soil_type": "Quartzite talus and steep river-terrace silts",
        "soil_depth_cm": 90,
        "porosity": 0.41,
        "permeability": "Moderate",
        "gsi_class": 5,
        "geology": "Alaknanda Fault Shear Zone",
    },
    "pithoragarh": {
        "name": "Pithoragarh",
        "district": "Pithoragarh",
        "lat": 29.583,
        "lon": 80.218,
        "elevation_m": 1627,
        "slope_deg": 34.0,
        "soil_type": "Weathered dolomitic colluvium and calcareous loam",
        "soil_depth_cm": 70,
        "porosity": 0.42,
        "permeability": "Moderate",
        "gsi_class": 4,
        "geology": "Tejam Group (Dolomite & Slate)",
    },
    "tehri garhwal": {
        "name": "Tehri Garhwal",
        "district": "Tehri Garhwal",
        "lat": 30.393,
        "lon": 78.480,
        "elevation_m": 1750,
        "slope_deg": 31.0,
        "soil_type": "Clayey loam over weathered phyllite",
        "soil_depth_cm": 85,
        "porosity": 0.45,
        "permeability": "Moderate",
        "gsi_class": 4,
        "geology": "Chandpur Phyllites",
    },
    "nainital": {
        "name": "Nainital",
        "district": "Nainital",
        "lat": 29.392,
        "lon": 79.454,
        "elevation_m": 2084,
        "slope_deg": 37.0,
        "soil_type": "Fractured limestone and shale talus",
        "soil_depth_cm": 60,
        "porosity": 0.43,
        "permeability": "High",
        "gsi_class": 4,
        "geology": "Krol-Infra Krol Structural Syncline",
    },
    "bageshwar": {
        "name": "Bageshwar",
        "district": "Bageshwar",
        "lat": 29.840,
        "lon": 79.769,
        "elevation_m": 1004,
        "slope_deg": 29.5,
        "soil_type": "Micaceous sandstone and valley silt loam",
        "soil_depth_cm": 95,
        "porosity": 0.44,
        "permeability": "Moderate",
        "gsi_class": 4,
        "geology": "Saryu Valley Sedimentary Belt",
    },
    "almora": {
        "name": "Almora",
        "district": "Almora",
        "lat": 29.597,
        "lon": 79.659,
        "elevation_m": 1600,
        "slope_deg": 26.0,
        "soil_type": "Granitic sandy loam and weathered saprolite",
        "soil_depth_cm": 100,
        "porosity": 0.46,
        "permeability": "High",
        "gsi_class": 3,
        "geology": "Almora Crystalline Nappe",
    },
    "dehradun": {
        "name": "Dehradun",
        "district": "Dehradun",
        "lat": 30.317,
        "lon": 78.032,
        "elevation_m": 650,
        "slope_deg": 12.0,
        "soil_type": "Fluventic boulder gravel and loamy alluvium",
        "soil_depth_cm": 150,
        "porosity": 0.48,
        "permeability": "High",
        "gsi_class": 3,
        "geology": "Intermontane Doon Gravel Basin",
    },
    "rishikesh": {
        "name": "Rishikesh",
        "district": "Dehradun",
        "lat": 30.087,
        "lon": 78.268,
        "elevation_m": 372,
        "slope_deg": 14.5,
        "soil_type": "Sub-Himalayan coarse gravel and alluvial sand",
        "soil_depth_cm": 140,
        "porosity": 0.47,
        "permeability": "Very High",
        "gsi_class": 2,
        "geology": "Siwalik Foothills / Main Boundary Thrust",
    },
    "haldwani": {
        "name": "Haldwani",
        "district": "Nainital",
        "lat": 29.218,
        "lon": 79.513,
        "elevation_m": 424,
        "slope_deg": 8.0,
        "soil_type": "Bhabar boulder beds and deep porous gravel",
        "soil_depth_cm": 180,
        "porosity": 0.50,
        "permeability": "Very High",
        "gsi_class": 2,
        "geology": "Piedmont Fan Alluvium",
    },
    "haridwar": {
        "name": "Haridwar",
        "district": "Hardwar",
        "lat": 29.946,
        "lon": 78.164,
        "elevation_m": 314,
        "slope_deg": 4.5,
        "soil_type": "Gangetic deep alluvial plains",
        "soil_depth_cm": 250,
        "porosity": 0.52,
        "permeability": "Moderate",
        "gsi_class": 1,
        "geology": "Indo-Gangetic Deep Quaternary Alluvium",
    },
}


def estimate_elevation_and_slope(lat: float, lon: float, api_elevation: float | None = None) -> tuple[float, float, str]:
    """
    Estimate elevation (meters) and slope angle (degrees) based on
    Uttarakhand Himalayan topography and known benchmark stations.
    """
    # Check if point is very close to a known station
    for key, data in KNOWN_LOCATIONS.items():
        dist = math.hypot(lat - data["lat"], lon - data["lon"])
        if dist < 0.08:  # ~8 km radius
            elev = api_elevation if (api_elevation is not None and api_elevation > 100) else data["elevation_m"]
            return elev, data["slope_deg"], data["soil_type"]

    # Topographic estimation model for Uttarakhand:
    # Latitude correlates strongly with Himalayan elevation bands:
    # 28.7-29.5: Foothills/Terai/Bhabar (300m - 1200m)
    # 29.5-30.3: Lesser/Middle Himalayas (1200m - 2400m)
    # 30.3-31.5: Higher Himalayas (2400m - 4800m+)
    if api_elevation is not None and api_elevation > 150:
        elev = float(api_elevation)
    else:
        lat_factor = max(0.0, min(1.0, (lat - 29.0) / 2.0))
        elev = 350.0 + (lat_factor ** 1.8) * 3600.0

    # Slope angle increases with elevation and northern latitude in Uttarakhand:
    if elev >= 2200:
        slope = min(52.0, 36.0 + (lat - 30.2) * 8.0 + (elev - 2200) / 300.0)
    elif elev >= 1200:
        slope = min(40.0, 26.0 + (elev - 1200) / 80.0)
    elif elev >= 600:
        slope = min(25.0, 12.0 + (elev - 600) / 60.0)
    else:
        slope = max(2.5, min(10.0, 4.0 + elev / 150.0))

    slope = round(max(2.0, min(55.0, slope)), 1)
    elev = round(elev, 0)

    # Determine general soil characteristic
    if elev > 2500:
        soil = "Glacial moraine, skeletal gravel and fractured gneiss"
    elif elev > 1400:
        soil = "Colluvial sandy loam with fractured phyllite/schist talus"
    elif elev > 700:
        soil = "Clayey gravelly loam over Sub-Himalayan sandstone"
    else:
        soil = "Alluvial silt and boulder gravel"

    return elev, slope, soil


def compute_terrain_factor_scores(
    elevation_m: float,
    slope_deg: float,
    soil_moisture: float,
    gsi_class: int,
    rainfall_24h_mm: float,
    distance_to_historical_km: float,
) -> dict:
    """
    Compute individual normalized factor scores (0–100) and explainable weights.
    Total risk is a multi-criteria decision combination:
      - Rainfall trigger (35%)
      - Slope angle & terrain gradient (25%)
      - Soil saturation & pore water pressure (15%)
      - Geological susceptibility class GSI NLSM (12%)
      - Elevation & orographic exposure (8%)
      - Proximity to historical landslide zones (5%)
    """
    # 1. Rainfall score (0-100)
    # 0 mm -> 0; 25 mm -> 35; 65 mm (IMD heavy threshold) -> 75; 100+ mm -> 95-100
    r = max(0.0, float(rainfall_24h_mm or 0))
    if r <= 5:
        rain_score = (r / 5.0) * 15.0
    elif r <= 35:
        rain_score = 15.0 + ((r - 5) / 30.0) * 35.0
    elif r <= 70:
        rain_score = 50.0 + ((r - 35) / 35.0) * 30.0
    else:
        rain_score = min(100.0, 80.0 + ((r - 70) / 50.0) * 20.0)

    # 2. Slope angle score (0-100)
    # <15 deg: 10-25 (stable); 15-30 deg: 30-55 (moderate); 30-45 deg: 60-90 (critical shear); >45: 90-100
    if slope_deg <= 15:
        slope_score = (slope_deg / 15.0) * 25.0
    elif slope_deg <= 30:
        slope_score = 25.0 + ((slope_deg - 15) / 15.0) * 30.0
    elif slope_deg <= 45:
        slope_score = 55.0 + ((slope_deg - 30) / 15.0) * 35.0
    else:
        slope_score = min(100.0, 90.0 + ((slope_deg - 45) / 10.0) * 10.0)

    # 3. Soil Saturation & Pore Pressure (0-100)
    # Volumetric moisture 0 to 0.45 m3/m3. 0.35+ is critical saturation in Himalayan colluvium
    sm = max(0.0, min(1.0, float(soil_moisture or 0)))
    saturation_pct = min(100.0, (sm / 0.45) * 100.0)
    if saturation_pct <= 40:
        soil_score = (saturation_pct / 40.0) * 25.0
    elif saturation_pct <= 70:
        soil_score = 25.0 + ((saturation_pct - 40) / 30.0) * 35.0
    else:
        soil_score = min(100.0, 60.0 + ((saturation_pct - 70) / 30.0) * 40.0)

    # 4. Geological Susceptibility (0-100)
    # GSI class 1 -> 15; 2 -> 35; 3 -> 55; 4 -> 78; 5 -> 96
    gsi_map = {1: 15, 2: 35, 3: 58, 4: 80, 5: 96}
    geol_score = gsi_map.get(int(gsi_class), 58)

    # 5. Elevation & Orographic Exposure (0-100)
    # <600m -> 15; 600-1500m -> 40; 1500-2800m -> 80 (cloudburst & MCT belt); >2800m -> 95
    if elevation_m <= 600:
        elev_score = 15.0 + (elevation_m / 600.0) * 15.0
    elif elevation_m <= 1500:
        elev_score = 30.0 + ((elevation_m - 600) / 900.0) * 30.0
    elif elevation_m <= 2800:
        elev_score = 60.0 + ((elevation_m - 1500) / 1300.0) * 28.0
    else:
        elev_score = min(100.0, 88.0 + ((elevation_m - 2800) / 1500.0) * 12.0)

    # 6. Proximity to Historical Landslide (0-100)
    d = max(0.1, float(distance_to_historical_km))
    if d < 3:
        hist_score = 95.0
    elif d < 8:
        hist_score = 75.0
    elif d < 18:
        hist_score = 55.0
    elif d < 35:
        hist_score = 35.0
    else:
        hist_score = 15.0

    # Weights
    weights = {
        "rainfall": 0.35,
        "slope": 0.25,
        "soil_moisture": 0.15,
        "geology_gsi": 0.12,
        "elevation": 0.08,
        "historical_proximity": 0.05,
    }

    # Combined composite score
    composite = (
        rain_score * weights["rainfall"]
        + slope_score * weights["slope"]
        + soil_score * weights["soil_moisture"]
        + geol_score * weights["geology_gsi"]
        + elev_score * weights["elevation"]
        + hist_score * weights["historical_proximity"]
    )

    composite = round(max(5.0, min(100.0, composite)), 1)

    return {
        "composite_risk_score": composite,
        "factors": {
            "rainfall": {
                "score": round(rain_score, 1),
                "weight": weights["rainfall"],
                "contribution_pts": round(rain_score * weights["rainfall"], 1),
                "label": f"Rainfall Intensity ({round(r, 1)} mm/h or 24h)",
            },
            "slope": {
                "score": round(slope_score, 1),
                "weight": weights["slope"],
                "contribution_pts": round(slope_score * weights["slope"], 1),
                "label": f"Slope Steepness ({slope_deg}° Gradient)",
            },
            "soil_moisture": {
                "score": round(soil_score, 1),
                "weight": weights["soil_moisture"],
                "contribution_pts": round(soil_score * weights["soil_moisture"], 1),
                "label": f"Soil Saturation ({round(saturation_pct, 1)}% pore saturation)",
            },
            "geology_gsi": {
                "score": round(geol_score, 1),
                "weight": weights["geology_gsi"],
                "contribution_pts": round(geol_score * weights["geology_gsi"], 1),
                "label": f"GSI NLSM Susceptibility Class {gsi_class}",
            },
            "elevation": {
                "score": round(elev_score, 1),
                "weight": weights["elevation"],
                "contribution_pts": round(elev_score * weights["elevation"], 1),
                "label": f"Elevation & Relief ({int(elevation_m)} m ASL)",
            },
            "historical_proximity": {
                "score": round(hist_score, 1),
                "weight": weights["historical_proximity"],
                "contribution_pts": round(hist_score * weights["historical_proximity"], 1),
                "label": f"Historical Zone Proximity ({round(d, 1)} km)",
            },
        },
        "saturation_pct": round(saturation_pct, 1),
    }


def generate_explanation_narrative(
    location_name: str,
    district: str,
    risk_score: float,
    severity: str,
    rainfall_24h_mm: float,
    slope_deg: float,
    elevation_m: float,
    soil_saturation_pct: float,
    gsi_class: int,
    nearest_hist: dict,
) -> str:
    """
    Generate transparent, plain-English explanation for why this specific risk level was predicted.
    """
    hist_name = nearest_hist.get("name", "historical slide area")
    hist_dist = nearest_hist.get("distance_km", 10)

    if severity in {"EXTREME", "HIGH"}:
        rain_str = f"critical rainfall load ({rainfall_24h_mm:.1f} mm)" if rainfall_24h_mm >= 30 else f"antecedent precipitation ({rainfall_24h_mm:.1f} mm)"
        narrative = (
            f"The predicted risk score of {risk_score:.0f}/100 ({severity}) for {location_name} ({district}) "
            f"is primarily driven by steep Himalayan terrain slopes ({slope_deg:.0f}°) combined with {rain_str} "
            f"and high pore-water saturation in the soil profile ({soil_saturation_pct:.0f}%). "
            f"This zone lies in GSI NLSM Class {gsi_class} susceptibility territory and is located within {hist_dist} km of "
            f"the {hist_name}, indicating high vulnerability to shear failure and debris flows."
        )
    elif severity == "MODERATE":
        narrative = (
            f"Moderate risk ({risk_score:.0f}/100) detected at {location_name}. Slopes are moderately steep ({slope_deg:.0f}° at {int(elevation_m)} m), "
            f"with soil saturation currently at {soil_saturation_pct:.0f}%. "
            f"While current rainfall ({rainfall_24h_mm:.1f} mm) is within manageable limits, forecasted rain can rapidly reduce slope shear strength. "
            f"Regular monitoring of drainage channels and highway cuttings is advised."
        )
    else:
        narrative = (
            f"Risk conditions at {location_name} are currently LOW ({risk_score:.0f}/100). The terrain gradient ({slope_deg:.0f}°) and stable soil saturation "
            f"({soil_saturation_pct:.0f}%) indicate adequate slope Factor of Safety under current environmental inputs. "
            f"No immediate landslide danger thresholds are crossed."
        )

    return narrative
