"""Shared request/response schemas used across routes."""

from typing import Any, Literal
from pydantic import BaseModel, Field


# ---------- Chat ----------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[ChatMessage] = Field(default_factory=list)


class SourceRef(BaseModel):
    """A piece of evidence the assistant used to ground its answer."""
    type: Literal["knowledge_base", "obis", "worms", "noaa", "open_meteo"]
    label: str
    detail: str | None = None
    url: str | None = None


class ChatResponse(BaseModel):
    reply: str
    sources: list[SourceRef] = Field(default_factory=list)


# ---------- Species ----------

class SpeciesOccurrence(BaseModel):
    scientific_name: str | None = None
    decimal_longitude: float | None = None
    decimal_latitude: float | None = None
    depth: float | None = None
    event_date: str | None = None
    locality: str | None = None
    dataset_name: str | None = None


class SpeciesSearchResult(BaseModel):
    query: str
    total_matched: int
    occurrences: list[SpeciesOccurrence]


class TaxonInfo(BaseModel):
    aphia_id: int | None = None
    scientific_name: str | None = None
    authority: str | None = None
    status: str | None = None
    rank: str | None = None
    kingdom: str | None = None
    phylum: str | None = None
    class_: str | None = Field(default=None, alias="class")
    order: str | None = None
    family: str | None = None
    genus: str | None = None
    is_marine: bool | None = None


# ---------- Environment (tides / waves) ----------

class TideReading(BaseModel):
    time: str
    water_level: float | None = None
    units: str = "meters"


class TideResponse(BaseModel):
    station_id: str
    station_name: str | None = None
    readings: list[TideReading]


class MarineWeatherPoint(BaseModel):
    time: str
    wave_height_m: float | None = None
    wave_period_s: float | None = None
    wave_direction_deg: float | None = None
    sea_surface_temperature_c: float | None = None


class MarineWeatherResponse(BaseModel):
    latitude: float
    longitude: float
    hourly: list[MarineWeatherPoint]


class ToolCallTrace(BaseModel):
    """Used for debugging / displaying which tools the agent invoked."""
    name: str
    arguments: dict[str, Any]
    result_summary: str
