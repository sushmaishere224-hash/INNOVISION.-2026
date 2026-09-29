import json
from pathlib import Path
from shapely.geometry import shape, Point
from shapely.prepared import prep

BASE_DIR = Path(__file__).resolve().parent.parent
UK_GEOJSON_PATH = BASE_DIR / "data" / "uttarakhand.geojson"
NER_RASTER_PATH = BASE_DIR / "data" / "ner.tif"

# ============================================================
# UTTARAKHAND LANDSLIDE SUSCEPTIBILITY (GSI NLSM CALIBRATION)
# ============================================================
# Calibrated according to Geological Survey of India (GSI)
# National Landslide Susceptibility Mapping (NLSM) for Uttarakhand:
# Class 5: Very High (MCT zone, steep Himalayan gorges, Kedarnath, Chamoli, Uttarkashi)
# Class 4: High (Steep catchment slopes, Nainital lake slopes, Tehri rim, Pithoragarh)
# Class 3: Moderate (Middle hills: Almora, Pauri, Champawat)
# Class 2: Low-Moderate (Doon Valley foothills)
# Class 1: Very Low (Haridwar, Udham Singh Nagar plains)

DISTRICT_BASE_SUSCEPTIBILITY = {
    "Chamoli": 5,
    "Rudraprayag": 5,
    "Uttarkashi": 5,
    "Pithoragarh": 4,
    "Tehri Garhwal": 4,
    "Bageshwar": 4,
    "Nainital": 4,
    "Almora": 3,
    "Champawat": 3,
    "Garhwal": 3,
    "Dehradun": 3,
    "Hardwar": 1,
    "Udham Singh Nagar": 1,
}

_districts_cache = None
_ner_raster = None


def _load_districts():
    global _districts_cache
    if _districts_cache is not None:
        return _districts_cache

    cached = []
    if UK_GEOJSON_PATH.exists():
        try:
            with open(UK_GEOJSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for feature in data.get("features", []):
                geom = shape(feature["geometry"])
                name = feature.get("properties", {}).get("Dist_Name", "Unknown")
                code = feature.get("properties", {}).get("Dist_Code", "")
                cached.append({
                    "name": name,
                    "code": code,
                    "geom": geom,
                    "prep": prep(geom),
                    "bounds": geom.bounds,
                })
        except Exception as exc:
            print(f"Warning: Failed to load Uttarakhand geojson: {exc}")

    _districts_cache = cached
    return _districts_cache


def _get_ner_raster():
    global _ner_raster
    if _ner_raster is not None:
        return _ner_raster
    if NER_RASTER_PATH.exists():
        try:
            import rasterio
            _ner_raster = rasterio.open(str(NER_RASTER_PATH))
        except Exception:
            _ner_raster = False
    else:
        _ner_raster = False
    return _ner_raster


def get_district(lat: float, lon: float) -> str | None:
    """Find the Uttarakhand district containing the (lat, lon) coordinate."""
    districts = _load_districts()
    pt = Point(lon, lat)

    for item in districts:
        minx, miny, maxx, maxy = item["bounds"]
        if minx <= lon <= maxx and miny <= lat <= maxy:
            if item["prep"].contains(pt) or item["geom"].contains(pt):
                return item["name"]

    return None


def get_susceptibility(lat: float, lon: float) -> int | None:
    """
    Sample landslide susceptibility class (0–5) at (lat, lon).

    Uses the calibrated Uttarakhand district terrain model (GSI/NLSM classes).
    Falls back to raster sampling for points outside known district boundaries.
    """
    # 1. Check Uttarakhand district
    district = get_district(lat, lon)
    if district:
        base = DISTRICT_BASE_SUSCEPTIBILITY.get(district, 3)

        # Micro-relief adjustments for diverse topography within districts:
        # Northern Dehradun (>30.38 N) is steep Mussoorie ridge -> Class 4
        # Southern Dehradun (<30.25 N) is flat Doon Valley -> Class 2
        if district == "Dehradun":
            if lat >= 30.38:
                return 4
            if lat <= 30.25:
                return 2

        # Northern Pithoragarh / Dharchula high peaks (>30.2 N) -> Class 5
        if district == "Pithoragarh" and lat >= 30.20:
            return 5

        # Northern Nainital around lake catchment / Balia ravine (>29.35 N) -> Class 4
        # Southern plains boundary of Nainital (<29.20 N) -> Class 2
        if district == "Nainital" and lat <= 29.20:
            return 2

        return base

    # 2. Fallback to ner.tif if point is in NER region
    raster = _get_ner_raster()
    if raster and raster is not False:
        try:
            row, col = raster.index(lon, lat)
            if 0 <= row < raster.height and 0 <= col < raster.width:
                value = raster.read(
                    1,
                    window=((row, row + 1), (col, col + 1)),
                )[0, 0]
                if value != 127:
                    klass = int(value)
                    if 0 <= klass <= 5:
                        return klass
        except Exception:
            pass

    # If within Uttarakhand bounding box but on edge, return regional average
    if 77.5 <= lon <= 81.1 and 28.7 <= lat <= 31.5:
        return 3

    return None

