"""
Open-Meteo Marine Weather API integration.

API docs: https://open-meteo.com/en/docs/marine-weather-api
No API key required for non-commercial use. Provides global wave height,
period, direction, and sea surface temperature - unlike NOAA CO-OPS this
works anywhere in the world's oceans, not just US stations.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import MarineWeatherPoint, MarineWeatherResponse

settings = get_settings()

HOURLY_VARS = "wave_height,wave_period,wave_direction,sea_surface_temperature"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
async def get_marine_forecast(
    latitude: float,
    longitude: float,
    forecast_hours: int = 24,
) -> MarineWeatherResponse:
    """
    Fetch wave height/period/direction and sea surface temperature for any
    ocean coordinate worldwide.

    Args:
        latitude: -90 to 90
        longitude: -180 to 180
        forecast_hours: how many hourly data points to return (capped at 72)
    """
    forecast_hours = max(1, min(forecast_hours, 72))

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": HOURLY_VARS,
        "length_unit": "metric",
        "timezone": "UTC",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(settings.open_meteo_marine_base_url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if "error" in data and data["error"]:
        raise ValueError(f"Open-Meteo error: {data.get('reason', 'unknown error')}")

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])[:forecast_hours]
    heights = hourly.get("wave_height", [])
    periods = hourly.get("wave_period", [])
    directions = hourly.get("wave_direction", [])
    sst = hourly.get("sea_surface_temperature", [])

    points = [
        MarineWeatherPoint(
            time=times[i],
            wave_height_m=_at(heights, i),
            wave_period_s=_at(periods, i),
            wave_direction_deg=_at(directions, i),
            sea_surface_temperature_c=_at(sst, i),
        )
        for i in range(len(times))
    ]

    return MarineWeatherResponse(latitude=latitude, longitude=longitude, hourly=points)


def _at(lst: list, i: int):
    return lst[i] if i < len(lst) else None
