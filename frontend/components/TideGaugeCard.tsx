"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { TideResponse } from "@/lib/types";

const NOAA_STATIONS = [
  { id: "9414290", label: "San Francisco, CA" },
  { id: "8518750", label: "The Battery, NY" },
  { id: "8724580", label: "Key West, FL" },
  { id: "9447130", label: "Seattle, WA" },
];

export function TideGaugeCard() {
  const [stationId, setStationId] = useState(NOAA_STATIONS[0].id);
  const [data, setData] = useState<TideResponse | null>(null);
  const [predictions, setPredictions] = useState<TideResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [current, preds] = await Promise.all([
          api.currentWaterLevel(stationId, 6),
          api.tidePredictions(stationId, 1),
        ]);
        if (cancelled) return;
        setData(current);
        setPredictions(preds);
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
  }, [stationId]);

  const latest = data?.readings.at(-1);
  const nextEvent = predictions?.readings[0];

  return (
    <div className="bg-abyss-900/60 border border-line-soft rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="font-display text-sm font-semibold text-text-primary">Tide Gauge</span>
        <select
          value={stationId}
          onChange={(e) => setStationId(e.target.value)}
          className="font-mono text-[11px] bg-abyss-800 border border-line rounded-md px-2 py-1 text-text-secondary outline-none focus:border-bio-500"
        >
          {NOAA_STATIONS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {loading && <SkeletonRow />}

      {error && (
        <p className="text-xs text-coral-400 font-mono">
          {error}. Backend may be offline — start it with <code>uvicorn app.main:app --reload</code>.
        </p>
      )}

      {!loading && !error && latest && (
        <div className="flex items-end justify-between">
          <div>
            <div className="font-mono text-3xl font-medium text-bio-400">
              {latest.water_level?.toFixed(2) ?? "—"}
              <span className="text-sm text-text-tertiary ml-1">m</span>
            </div>
            <p className="text-[11px] text-text-tertiary mt-1">
              MLLW datum · {formatTime(latest.time)}
            </p>
          </div>

          {nextEvent && (
            <div className="text-right">
              <p className="text-[11px] text-text-secondary">
                Next {nextEvent.units.includes("H") ? "high" : "low"} tide
              </p>
              <p className="font-mono text-sm text-text-primary">
                {nextEvent.water_level?.toFixed(2)}m · {formatTime(nextEvent.time)}
              </p>
            </div>
          )}
        </div>
      )}

      {!loading && !error && !latest && (
        <EmptyState message="No recent readings for this station." />
      )}
    </div>
  );
}

function formatTime(t: string): string {
  // NOAA format: "2026-06-25 06:00"
  const parts = t.split(" ");
  return parts[1] ?? t;
}

function SkeletonRow() {
  return <div className="h-12 bg-abyss-800 rounded-lg animate-pulse-glow" />;
}

function EmptyState({ message }: { message: string }) {
  return <p className="text-xs text-text-tertiary font-mono">{message}</p>;
}
