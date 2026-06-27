"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { MarineWeatherResponse } from "@/lib/types";

const LOCATIONS = [
  { label: "Florida Keys", lat: 25.46, lon: -80.12 },
  { label: "Bay of Bengal", lat: 13.08, lon: 85.0 },
  { label: "Great Barrier Reef", lat: -18.29, lon: 147.7 },
  { label: "North Sea", lat: 56.0, lon: 3.0 },
];

export function MarineConditionsCard() {
  const [location, setLocation] = useState(LOCATIONS[0]);
  const [data, setData] = useState<MarineWeatherResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await api.marineForecast(location.lat, location.lon, 24);
        if (!cancelled) setData(res);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't reach backend");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [location]);

  const current = data?.hourly[0];

  return (
    <div className="bg-abyss-900/60 border border-line-soft rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-display text-sm font-semibold text-text-primary">Sea Conditions</span>
        <select
          value={location.label}
          onChange={(e) =>
            setLocation(LOCATIONS.find((l) => l.label === e.target.value) ?? LOCATIONS[0])
          }
          className="font-mono text-[11px] bg-abyss-800 border border-line rounded-md px-2 py-1 text-text-secondary outline-none focus:border-bio-500"
        >
          {LOCATIONS.map((l) => (
            <option key={l.label} value={l.label}>
              {l.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <div className="h-16 bg-abyss-800 rounded-lg animate-pulse-glow" />}

      {error && (
        <p className="text-xs text-coral-400 font-mono">
          {error}. Backend may be offline — start it with <code>uvicorn app.main:app --reload</code>.
        </p>
      )}

      {!loading && !error && current && (
        <div className="grid grid-cols-3 gap-3">
          <Metric
            label="Wave height"
            value={current.wave_height_m?.toFixed(1) ?? "—"}
            unit="m"
          />
          <Metric
            label="Wave period"
            value={current.wave_period_s?.toFixed(1) ?? "—"}
            unit="s"
          />
          <Metric
            label="Sea temp"
            value={current.sea_surface_temperature_c?.toFixed(1) ?? "—"}
            unit="°C"
          />
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, unit }: { label: string; value: string; unit: string }) {
  return (
    <div>
      <p className="font-mono text-[10px] text-text-tertiary uppercase tracking-wide">{label}</p>
      <p className="font-mono text-xl text-coral-400 mt-0.5">
        {value}
        <span className="text-xs text-text-tertiary ml-0.5">{unit}</span>
      </p>
    </div>
  );
}
