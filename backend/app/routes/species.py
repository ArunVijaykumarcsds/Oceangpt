from fastapi import APIRouter, HTTPException, Query

from app.models import SpeciesSearchResult, TaxonInfo
from app.tools import obis, worms

router = APIRouter(prefix="/api/species", tags=["species"])


@router.get("/search", response_model=SpeciesSearchResult)
async def search_species(
    name: str = Query(..., description="Scientific name, e.g. 'Chelonia mydas'"),
    size: int = Query(10, ge=1, le=50),
):
    try:
        return await obis.search_species_occurrences(name, size=size)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"OBIS lookup failed: {exc}") from exc


@router.get("/taxonomy", response_model=TaxonInfo | None)
async def get_taxonomy(name: str = Query(..., description="Scientific name to look up")):
    try:
        return await worms.lookup_taxon_by_name(name)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"WoRMS lookup failed: {exc}") from exc
