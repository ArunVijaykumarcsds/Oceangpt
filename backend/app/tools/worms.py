"""
WoRMS (World Register of Marine Species) integration.

API docs: https://www.marinespecies.org/rest/
No API key required. Used here for authoritative taxonomic verification -
e.g. confirming a name is a valid marine species before trusting OBIS data
or answering questions about classification.
"""

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.models import TaxonInfo

settings = get_settings()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
async def lookup_taxon_by_name(scientific_name: str) -> TaxonInfo | None:
    """
    Look up taxonomic record(s) for a scientific name via WoRMS fuzzy match,
    then fetch the full classification for the best (first) AphiaID match.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        match_resp = await client.get(
            f"{settings.worms_base_url}/AphiaRecordsByMatchNames",
            params={"scientificnames[]": scientific_name, "marine_only": "true"},
        )
        if match_resp.status_code == 204:
            return None
        match_resp.raise_for_status()
        matches = match_resp.json()

    # Response shape: list of lists (one list per input name)
    if not matches or not matches[0]:
        return None

    best = matches[0][0]
    return TaxonInfo(
        aphia_id=best.get("AphiaID"),
        scientific_name=best.get("scientificname"),
        authority=best.get("authority"),
        status=best.get("status"),
        rank=best.get("rank"),
        kingdom=best.get("kingdom"),
        phylum=best.get("phylum"),
        **{"class": best.get("class")},
        order=best.get("order"),
        family=best.get("family"),
        genus=best.get("genus"),
        is_marine=bool(best.get("isMarine")) if best.get("isMarine") is not None else None,
    )
