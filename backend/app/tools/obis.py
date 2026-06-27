"""
OBIS (Ocean Biodiversity Information System) integration.

API docs: https://api.obis.org/
No API key required. Public REST API over Darwin Core occurrence records.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import SpeciesOccurrence, SpeciesSearchResult

settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
async def search_species_occurrences(
    scientific_name: str,
    size: int = 10,
    geometry_wkt: str | None = None,
) -> SpeciesSearchResult:
    """
    Search OBIS for occurrence records of a given species.

    Args:
        scientific_name: e.g. "Chelonia mydas" (green sea turtle)
        size: max number of records to return (capped at 50 for performance)
        geometry_wkt: optional Well-Known-Text polygon to restrict the search
                      geographically, e.g. "POLYGON((...))"
    """
    size = min(size, 50)
    params: dict[str, str | int] = {"scientificname": scientific_name, "size": size}
    if geometry_wkt:
        params["geometry"] = geometry_wkt

    url = f"{settings.obis_base_url}/occurrence"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results", [])
    occurrences = [
        SpeciesOccurrence(
            scientific_name=rec.get("scientificName"),
            decimal_longitude=rec.get("decimalLongitude"),
            decimal_latitude=rec.get("decimalLatitude"),
            depth=rec.get("depth"),
            event_date=rec.get("eventDate") or rec.get("date_year"),
            locality=rec.get("locality"),
            dataset_name=rec.get("dataset_id"),
        )
        for rec in results
    ]

    return SpeciesSearchResult(
        query=scientific_name,
        total_matched=data.get("total", len(occurrences)),
        occurrences=occurrences,
    )
