from fastapi import APIRouter, HTTPException, Query

from app.models import MarineWeatherResponse, TideResponse
from app.tools import noaa_tides, open_meteo

router = APIRouter(prefix="/api/environment", tags=["environment"])


@router.get("/tides/current", response_model=TideResponse)
async def current_water_level(
    station_id: str = Query(..., description="7-digit NOAA CO-OPS station ID"),
    hours_back: int = Query(6, ge=1, le=24),
):
    try:
        return await noaa_tides.get_water_level(station_id, hours_back=hours_back)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"NOAA lookup failed: {exc}") from exc


@router.get("/tides/predictions", response_model=TideResponse)
async def tide_predictions(
    station_id: str = Query(..., description="7-digit NOAA CO-OPS station ID"),
    days_ahead: int = Query(2, ge=1, le=7),
):
    try:
        return await noaa_tides.get_tide_predictions(station_id, days_ahead=days_ahead)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"NOAA lookup failed: {exc}") from exc


@router.get("/marine-forecast", response_model=MarineWeatherResponse)
async def marine_forecast(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    forecast_hours: int = Query(24, ge=1, le=72),
):
    try:
        return await open_meteo.get_marine_forecast(latitude, longitude, forecast_hours=forecast_hours)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Open-Meteo lookup failed: {exc}") from exc
