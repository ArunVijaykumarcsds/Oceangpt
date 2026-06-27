"""
Tool registry: defines the OpenAI function-calling schemas for every live
data tool OceanGPT can use, and dispatches tool calls to the actual
implementation functions.

This is the single place to add a new tool - define its JSON schema here,
add the implementation in app/tools/<name>.py, and register the dispatcher
in TOOL_DISPATCH below.
"""

from typing import Any, Awaitable, Callable

from app.tools import noaa_tides, obis, open_meteo, worms

# ---------------------------------------------------------------------------
# OpenAI function-calling schemas
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_species_occurrences",
            "description": (
                "Search the OBIS (Ocean Biodiversity Information System) database for "
                "real occurrence records of a marine species - where and when it has "
                "been observed. Use this when the user asks about a specific species' "
                "distribution, habitat, or sightings."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scientific_name": {
                        "type": "string",
                        "description": "Scientific (Latin binomial) name, e.g. 'Chelonia mydas'. "
                                        "If the user gave a common name, translate it first.",
                    },
                    "size": {
                        "type": "integer",
                        "description": "Number of occurrence records to retrieve (default 10, max 50)",
                    },
                },
                "required": ["scientific_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_taxon_by_name",
            "description": (
                "Look up authoritative taxonomic classification for a marine species via "
                "WoRMS (World Register of Marine Species) - kingdom, phylum, class, order, "
                "family, genus, taxonomic status, and whether it's confirmed marine. Use this "
                "for classification questions or to verify a name is a real, valid marine species."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "scientific_name": {
                        "type": "string",
                        "description": "Scientific name to look up, e.g. 'Orcinus orca'",
                    }
                },
                "required": ["scientific_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_water_level",
            "description": (
                "Get recent real-time water level (tide) readings for a US coastal or Great "
                "Lakes NOAA station. Only works for US locations with a known NOAA station ID. "
                "If you don't know the station ID for a location, say so rather than guessing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "7-digit NOAA CO-OPS station ID, e.g. '9414290' for San Francisco, CA",
                    },
                    "hours_back": {
                        "type": "integer",
                        "description": "How many hours of recent data to fetch (default 6, max 24)",
                    },
                },
                "required": ["station_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_tide_predictions",
            "description": (
                "Get upcoming predicted high/low tide times and heights for a US NOAA station. "
                "Use this for 'when is the next high tide' type questions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "station_id": {
                        "type": "string",
                        "description": "7-digit NOAA CO-OPS station ID",
                    },
                    "days_ahead": {
                        "type": "integer",
                        "description": "Number of days of predictions (default 2, max 7)",
                    },
                },
                "required": ["station_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_marine_forecast",
            "description": (
                "Get global wave height, wave period, wave direction, and sea surface "
                "temperature for ANY ocean coordinate worldwide (not limited to the US). "
                "Use this for wave/swell/sea-temperature questions anywhere in the world, "
                "or as a global fallback when no NOAA station is known."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "-90 to 90"},
                    "longitude": {"type": "number", "description": "-180 to 180"},
                    "forecast_hours": {
                        "type": "integer",
                        "description": "Number of hourly forecast points to return (default 24, max 72)",
                    },
                },
                "required": ["latitude", "longitude"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatch: tool name -> async implementation
# ---------------------------------------------------------------------------

TOOL_DISPATCH: dict[str, Callable[..., Awaitable[Any]]] = {
    "search_species_occurrences": obis.search_species_occurrences,
    "lookup_taxon_by_name": worms.lookup_taxon_by_name,
    "get_water_level": noaa_tides.get_water_level,
    "get_tide_predictions": noaa_tides.get_tide_predictions,
    "get_marine_forecast": open_meteo.get_marine_forecast,
}


async def dispatch_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    """Run a tool by name with the given arguments, raising if unknown."""
    if name not in TOOL_DISPATCH:
        raise ValueError(f"Unknown tool: {name}")
    return await TOOL_DISPATCH[name](**arguments)
