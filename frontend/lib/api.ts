import type {
  ChatMessage,
  ChatResponse,
  MarineWeatherResponse,
  SpeciesSearchResult,
  TaxonInfo,
  TideResponse,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(body.detail ?? "Request failed", res.status);
  }

  return res.json() as Promise<T>;
}

export const api = {
  chat: (message: string, history: ChatMessage[]) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),

  searchSpecies: (name: string, size = 10) =>
    request<SpeciesSearchResult>(
      `/api/species/search?name=${encodeURIComponent(name)}&size=${size}`
    ),

  getTaxonomy: (name: string) =>
    request<TaxonInfo | null>(`/api/species/taxonomy?name=${encodeURIComponent(name)}`),

  currentWaterLevel: (stationId: string, hoursBack = 6) =>
    request<TideResponse>(
      `/api/environment/tides/current?station_id=${stationId}&hours_back=${hoursBack}`
    ),

  tidePredictions: (stationId: string, daysAhead = 2) =>
    request<TideResponse>(
      `/api/environment/tides/predictions?station_id=${stationId}&days_ahead=${daysAhead}`
    ),

  marineForecast: (latitude: number, longitude: number, forecastHours = 24) =>
    request<MarineWeatherResponse>(
      `/api/environment/marine-forecast?latitude=${latitude}&longitude=${longitude}&forecast_hours=${forecastHours}`
    ),
};

export { ApiError };
