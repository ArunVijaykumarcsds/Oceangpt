// Mirrors app/models.py on the backend. Keep these in sync manually -
// this is a small enough API surface that a codegen step isn't worth it yet.

export type SourceType = "knowledge_base" | "obis" | "worms" | "noaa" | "open_meteo";

export interface SourceRef {
  type: SourceType;
  label: string;
  detail?: string | null;
  url?: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  sources: SourceRef[];
}

export interface SpeciesOccurrence {
  scientific_name: string | null;
  decimal_longitude: number | null;
  decimal_latitude: number | null;
  depth: number | null;
  event_date: string | null;
  locality: string | null;
  dataset_name: string | null;
}

export interface SpeciesSearchResult {
  query: string;
  total_matched: number;
  occurrences: SpeciesOccurrence[];
}

export interface TaxonInfo {
  aphia_id: number | null;
  scientific_name: string | null;
  authority: string | null;
  status: string | null;
  rank: string | null;
  kingdom: string | null;
  phylum: string | null;
  class: string | null;
  order: string | null;
  family: string | null;
  genus: string | null;
  is_marine: boolean | null;
}

export interface TideReading {
  time: string;
  water_level: number | null;
  units: string;
}

export interface TideResponse {
  station_id: string;
  station_name: string | null;
  readings: TideReading[];
}

export interface MarineWeatherPoint {
  time: string;
  wave_height_m: number | null;
  wave_period_s: number | null;
  wave_direction_deg: number | null;
  sea_surface_temperature_c: number | null;
}

export interface MarineWeatherResponse {
  latitude: number;
  longitude: number;
  hourly: MarineWeatherPoint[];
}
