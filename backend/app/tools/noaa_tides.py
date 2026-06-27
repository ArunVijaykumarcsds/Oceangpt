"""
NOAA CO-OPS (Center for Operational Oceanographic Products and Services) integration.

API docs: https://api.tidesandcurrents.noaa.gov/api/prod/
No API key required. Provides real-time and historical water level, tide,
temperature, and meteorological data for US coastal/Great Lakes stations.

NOTE: This API is US-only (NOAA stations). For global wave/marine weather,
see open_meteo.py instead.
"""

from datetime import datetime, timezone

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import TideReading, TideResponse

settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
async def get_water_level(
    station_id: str,
    hours_back: int = 6,
) -> TideResponse:
    """
    Fetch recent real-time water level readings for a NOAA tide station.

    Args:
        station_id: 7-digit NOAA CO-OPS station ID, e.g. "9414290" (San Francisco, CA)
        hours_back: how many hours of recent data to pull (NOAA's "range" param, max 24 for this endpoint use)
    """
    hours_back = max(1, min(hours_back, 24))

    params = {
        "product": "water_level",
        "station": station_id,
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "range": hours_back,
        "application": settings.noaa_application_name,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(settings.noaa_coops_base_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(f"NOAA CO-OPS error: {data['error'].get('message', 'unknown error')}")

    readings = [
        TideReading(time=item["t"], water_level=_safe_float(item.get("v")), units="meters")
        for item in data.get("data", [])
    ]

    return TideResponse(station_id=station_id, station_name=None, readings=readings)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
async def get_tide_predictions(
    station_id: str,
    days_ahead: int = 2,
) -> TideResponse:
    """
    Fetch upcoming high/low tide predictions for a NOAA station.

    Args:
        station_id: 7-digit NOAA CO-OPS station ID
        days_ahead: number of days of predictions to fetch (1-7)
    """
    days_ahead = max(1, min(days_ahead, 7))
    today = datetime.now(timezone.utc).strftime("%Y%m%d")

    params = {
        "product": "predictions",
        "station": station_id,
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": "metric",
        "format": "json",
        "interval": "hilo",
        "begin_date": today,
        "range": days_ahead * 24,
        "application": settings.noaa_application_name,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(settings.noaa_coops_base_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data:
        raise ValueError(f"NOAA CO-OPS error: {data['error'].get('message', 'unknown error')}")

    readings = [
        TideReading(
            time=item["t"],
            water_level=_safe_float(item.get("v")),
            units=f"meters ({item.get('type', '')})",
        )
        for item in data.get("predictions", [])
    ]

    return TideResponse(station_id=station_id, station_name=None, readings=readings)


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
