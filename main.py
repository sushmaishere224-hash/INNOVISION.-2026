import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from shapely.geometry import shape, Polygon, mapping
from shapely.prepared import prep
from shapely.ops import unary_union

from .h3_grid import get_uttarakhand_cells, get_ner_cells, get_cell_info
from .weather import (
    get_weather_points,
    find_nearest_weather,
    sum_last_hours,
    sum_forecast_hours,
    mean_last_hours,
    fetch_uttarakhand_point_prediction,
    fetch_all_districts_weather_prediction,
    get_weather_condition_desc,
    UTTARAKHAND_DISTRICTS,
)
from .susceptibility import get_susceptibility, get_district
from .risk import (
    calculate_risk,
    calculate_predicted_risk,
    get_severity,
)
from .config import get_cors_origins
from .database import Base, engine
from .models import Alert, Report, ReportMedia, User  # noqa: F401
from .routers import alerts_router, reports_router, users_router
from .routers.reports import UPLOAD_ROOT
from .location_risk import evaluate_location_risk
from .historical_data import get_historical_landslides_geojson, HISTORICAL_LANDSLIDES
from .terrain_factors import KNOWN_LOCATIONS


# ============================================================
# PATHS / CACHE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
UK_GEOJSON_PATH = BASE_DIR / "data" / "uttarakhand.geojson"
NER_GEOJSON_PATH = BASE_DIR / "data" / "ner.geojson"

# Primary boundary is Uttarakhand; fallback to NER if missing
BOUNDARY_GEOJSON_PATH = UK_GEOJSON_PATH if UK_GEOJSON_PATH.exists() else NER_GEOJSON_PATH

# Hourly by default; override with RISK_GRID_REFRESH_SECONDS
REFRESH_INTERVAL_SECONDS = int(os.getenv("RISK_GRID_REFRESH_SECONDS", "3600"))
# Built-in scheduler (set RISK_GRID_AUTO_REFRESH=0 if you only use the POST script)
AUTO_REFRESH = os.getenv("RISK_GRID_AUTO_REFRESH", "1").strip().lower() not in {
    "0",
    "false",
    "no",
    "off",
}

BOUNDARY_SHAPE = None
PREPARED_BOUNDARY = None
GRID_CELLS = None

# Backwards compatibility globals
NER_SHAPE = None
PREPARED_NER = None
NER_CELLS = None

RISK_RESULT = None
RISK_GENERATED_AT = None
RISK_GENERATING = False
_risk_lock: asyncio.Lock | None = None
_refresh_task: asyncio.Task | None = None


def _get_risk_lock() -> asyncio.Lock:
    global _risk_lock
    if _risk_lock is None:
        _risk_lock = asyncio.Lock()
    return _risk_lock


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ============================================================
# LOAD BOUNDARY
# ============================================================

def load_boundary():
    global BOUNDARY_SHAPE, PREPARED_BOUNDARY, NER_SHAPE, PREPARED_NER

    if BOUNDARY_SHAPE is not None:
        return BOUNDARY_SHAPE

    print(f"Loading boundary from {BOUNDARY_GEOJSON_PATH.name}...")

    with open(BOUNDARY_GEOJSON_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("type") == "FeatureCollection":
        geometries = [
            feature["geometry"]
            for feature in data["features"]
            if feature.get("geometry")
        ]

        if not geometries:
            raise ValueError(f"{BOUNDARY_GEOJSON_PATH.name} contains no geometries.")

        BOUNDARY_SHAPE = unary_union(
            [shape(geometry) for geometry in geometries]
        )

    elif data.get("type") == "Feature":
        BOUNDARY_SHAPE = shape(data["geometry"])

    else:
        BOUNDARY_SHAPE = shape(data)

    PREPARED_BOUNDARY = prep(BOUNDARY_SHAPE)
    NER_SHAPE = BOUNDARY_SHAPE
    PREPARED_NER = PREPARED_BOUNDARY

    print("Boundary loaded successfully.")
    return BOUNDARY_SHAPE


def load_ner_boundary():
    """Backwards-compatible alias for primary boundary loader."""
    return load_boundary()


# ============================================================
# H3 GENERATION & CACHE
# ============================================================

def get_cached_cells():
    global GRID_CELLS, NER_CELLS

    if GRID_CELLS is not None:
        return GRID_CELLS

    print("Generating H3 grid for Uttarakhand...")
    boundary_shape = load_boundary()

    raw_cells = [get_cell_info(c) for c in get_uttarakhand_cells()]

    # Filter to cells intersecting Uttarakhand boundary
    filtered_cells = []
    for cell in raw_cells:
        poly = Polygon(cell["boundary"])
        if PREPARED_BOUNDARY.intersects(poly):
            filtered_cells.append(cell)

    GRID_CELLS = filtered_cells
    NER_CELLS = GRID_CELLS

    print(f"Generated {len(GRID_CELLS)} H3 cells covering Uttarakhand.")
    return GRID_CELLS


# ============================================================
# CLIP H3 CELL TO BOUNDARY
# ============================================================

def clip_cell_to_boundary(cell, boundary_shape):
    polygon = Polygon(cell["boundary"])

    if not PREPARED_BOUNDARY.intersects(polygon):
        return None

    intersection = polygon.intersection(boundary_shape)

    if intersection.is_empty:
        return None

    return intersection


def clip_cell_to_ner(cell, ner_shape):
    """Backwards-compatible alias for clip function."""
    return clip_cell_to_boundary(cell, ner_shape)


# ============================================================
# RISK GRID BUILD WITH PREDICTIVE WEATHER
# ============================================================

async def build_risk_grid(*, force: bool = False) -> dict:
    """Build (or return cached) Uttarakhand landslide risk GeoJSON with weather predictions."""

    global RISK_RESULT
    global RISK_GENERATED_AT
    global RISK_GENERATING

    lock = _get_risk_lock()

    async with lock:
        if RISK_RESULT is not None and not force:
            print("Returning cached risk grid.")
            return RISK_RESULT

        RISK_GENERATING = True
        print("Building Uttarakhand risk grid with weather predictions...")

        try:
            boundary_shape = load_boundary()
            cells = get_cached_cells()

            print("Fetching live weather points across Uttarakhand...")
            weather_points, weather_data = await get_weather_points(cells)
            print(f"Weather points sampled: {len(weather_points)}")

            features = []
            total_cells = len(cells)

            for index, cell in enumerate(cells):
                clipped_geometry = clip_cell_to_boundary(cell, boundary_shape)

                if clipped_geometry is None:
                    continue

                weather = find_nearest_weather(
                    cell,
                    weather_points,
                    weather_data,
                )

                hourly = weather.get("hourly", {})
                precipitation = hourly.get("precipitation", [])
                soil_moisture = hourly.get("soil_moisture_0_to_7cm", [])
                temperatures = hourly.get("temperature_2m", [])
                weather_codes = hourly.get("weather_code", [])

                # Past 24h antecedent rainfall
                rainfall_24h = sum_last_hours(precipitation, 24)
                # Next 24h forecasted rainfall
                predicted_rainfall_24h = sum_forecast_hours(precipitation, start_hour=24, hours=24)
                # Soil moisture
                soil_value = mean_last_hours(soil_moisture, 24)

                susceptibility = get_susceptibility(
                    cell["lat"],
                    cell["lon"],
                )
                district = get_district(
                    cell["lat"],
                    cell["lon"],
                )

                # Current risk score
                risk = calculate_risk(
                    rainfall_24h=rainfall_24h,
                    soil_moisture=soil_value,
                    susceptibility=susceptibility,
                )
                severity = get_severity(risk)

                # Predicted forecast risk score
                predicted_risk = calculate_predicted_risk(
                    predicted_rainfall_24h=predicted_rainfall_24h,
                    current_soil_moisture=soil_value,
                    susceptibility=susceptibility,
                )
                predicted_severity = get_severity(predicted_risk)

                cur_code = weather_codes[23] if len(weather_codes) > 23 else (weather_codes[-1] if weather_codes else None)
                cur_temp = temperatures[23] if len(temperatures) > 23 else (temperatures[-1] if temperatures else None)

                feature = {
                    "type": "Feature",
                    "properties": {
                        "h3": cell["h3"],
                        "district": district,
                        "risk": risk,
                        "severity": severity,
                        "predicted_risk": predicted_risk,
                        "predicted_severity": predicted_severity,
                        "susceptibility": susceptibility,
                        "rainfall_24h": round(rainfall_24h, 2),
                        "predicted_rainfall_24h": round(predicted_rainfall_24h, 2),
                        "soil_moisture": round(soil_value, 4),
                        "temperature": cur_temp,
                        "weather_code": cur_code,
                        "weather_condition": get_weather_condition_desc(cur_code),
                        "lat": cell["lat"],
                        "lon": cell["lon"],
                    },
                    "geometry": mapping(clipped_geometry),
                }

                features.append(feature)

                if index % 500 == 0:
                    print(f"Processed {index}/{total_cells} cells...")

            generated_at = _utc_now_iso()

            result = {
                "type": "FeatureCollection",
                "region": "Uttarakhand, India",
                "features": features,
                "count": len(features),
                "generated_at": generated_at,
            }

            RISK_RESULT = result
            RISK_GENERATED_AT = generated_at

            print(f"Returning {len(features)} clipped Uttarakhand risk cells.")
            return result

        finally:
            RISK_GENERATING = False


async def hourly_risk_grid_loop() -> None:
    """Keep the risk grid fresh while the API is running."""

    # Short delay so the API can finish booting before the heavy job.
    await asyncio.sleep(8)

    try:
        if RISK_RESULT is None:
            print("[scheduler] Warming risk grid cache...")
            await build_risk_grid(force=False)
            print("[scheduler] Initial risk grid ready.")
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"[scheduler] Initial risk grid warm failed: {exc}")

    while True:
        await asyncio.sleep(REFRESH_INTERVAL_SECONDS)
        try:
            print(
                f"[scheduler] Regenerating risk grid "
                f"(interval={REFRESH_INTERVAL_SECONDS}s)..."
            )
            await build_risk_grid(force=True)
            print("[scheduler] Risk grid refresh complete.")
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[scheduler] Risk grid refresh failed: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _refresh_task

    Base.metadata.create_all(bind=engine)
    print("Database ready (users, reports, alerts tables).")

    if AUTO_REFRESH:
        _refresh_task = asyncio.create_task(hourly_risk_grid_loop())
        print(
            f"Risk-grid hourly refresh scheduled "
            f"every {REFRESH_INTERVAL_SECONDS}s."
        )
    else:
        print(
            "Risk-grid auto-refresh disabled "
            "(use backend/scripts/hourly_risk_grid.py)."
        )

    try:
        yield
    finally:
        if _refresh_task is not None:
            _refresh_task.cancel()
            try:
                await _refresh_task
            except asyncio.CancelledError:
                pass


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Landslide Early Warning System (LEWS)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(reports_router)
app.include_router(alerts_router)

UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Landslide Early Warning System (LEWS)",
        "risk_grid_generated_at": RISK_GENERATED_AT,
        "risk_grid_generating": RISK_GENERATING,
        "risk_grid_refresh_seconds": REFRESH_INTERVAL_SECONDS,
    }


# ============================================================
# RISK GRID
# ============================================================

@app.get("/risk-grid")
async def risk_grid():
    """Return the cached risk grid, building it on first request if needed."""
    return await build_risk_grid(force=False)


@app.post("/risk-grid/generate")
async def generate_risk_grid():
    """
    Force-regenerate the Uttarakhand risk grid with fresh weather.
    Intended for the hourly automation script (and manual refresh).
    """
    if RISK_GENERATING:
        raise HTTPException(
            status_code=409,
            detail="Risk grid generation already in progress.",
        )

    try:
        result = await build_risk_grid(force=True)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Risk grid generation failed: {exc}",
        ) from exc

    return {
        "status": "ok",
        "message": "Risk grid regenerated",
        "count": result.get("count", 0),
        "generated_at": result.get("generated_at"),
    }


# ============================================================
# WEATHER PREDICTION & FORECAST (UTTARAKHAND)
# ============================================================

@app.get("/weather/prediction")
async def get_weather_prediction(
    lat: float = Query(30.3165, description="Latitude (default: Dehradun)"),
    lon: float = Query(78.0322, description="Longitude (default: Dehradun)"),
    days: int = Query(7, ge=1, le=14, description="Forecast days outlook"),
):
    """
    Fetch comprehensive 7-day predictive weather and landslide hazard forecast
    for any coordinate across Uttarakhand.
    """
    try:
        return await fetch_uttarakhand_point_prediction(
            latitude=lat,
            longitude=lon,
            forecast_days=days,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Weather prediction failed: {exc}",
        ) from exc


@app.get("/weather/districts")
async def get_districts_weather():
    """
    Fetch live weather conditions, 24h & 7-day predicted rainfall,
    and landslide hazard warnings for all 13 Uttarakhand districts.
    """
    try:
        return await fetch_all_districts_weather_prediction()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Districts weather prediction failed: {exc}",
        ) from exc


# ============================================================
# DISTRICT BOUNDARIES
# ============================================================

@app.get("/districts")
async def get_districts_geojson():
    """Return Uttarakhand district boundaries GeoJSON."""
    if UK_GEOJSON_PATH.exists():
        with open(UK_GEOJSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Uttarakhand boundary not found")


# ============================================================
# LOCATION RISK EVALUATION (WITH ENVIRONMENTAL FACTORS)
# ============================================================

@app.get("/risk/evaluate")
async def get_evaluated_risk(
    lat: float = Query(30.556, description="Latitude (default: Joshimath)"),
    lon: float = Query(79.567, description="Longitude (default: Joshimath)"),
    rainfall_intensity: float | None = Query(None, description="Optional simulated rainfall intensity (mm/h)"),
    threshold: float = Query(70.0, description="Risk alert threshold score"),
    location: str | None = Query(None, description="Location name"),
):
    """
    Evaluate real-time landslide risk for any Uttarakhand coordinate.
    Factors: rainfall intensity, slope angle, elevation, soil characteristics, and historical landslide proximity.
    """
    return await evaluate_location_risk(
        latitude=lat,
        longitude=lon,
        rainfall_intensity=rainfall_intensity,
        threshold=threshold,
        location_name=location,
    )


# ============================================================
# HISTORICAL LANDSLIDES
# ============================================================

@app.get("/historical-landslides")
async def get_historical_landslides():
    """Return GeoJSON of documented Uttarakhand historical landslide events."""
    return get_historical_landslides_geojson()


# ============================================================
# MONITORED BENCHMARK LOCATIONS
# ============================================================

@app.get("/locations")
async def get_monitored_locations():
    """Return benchmark monitoring locations and pilgrim corridors in Uttarakhand."""
    return list(KNOWN_LOCATIONS.values())

