"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { SpeciesSearchResult, TaxonInfo } from "@/lib/types";

const EXAMPLE_SPECIES = ["Chelonia mydas", "Orcinus orca", "Rhincodon typus"];

export function SpeciesLookupCard() {
  const [query, setQuery] = useState("");
  const [taxon, setTaxon] = useState<TaxonInfo | null>(null);
  const [occurrences, setOccurrences] = useState<SpeciesSearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function runSearch(name: string) {
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const [taxonRes, occRes] = await Promise.all([
        api.getTaxonomy(name).catch(() => null),
        api.searchSpecies(name, 5),
      ]);
      setTaxon(taxonRes);
      setOccurrences(occRes);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reach backend");
      setOccurrences(null);
      setTaxon(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-abyss-900/60 border border-line-soft rounded-xl p-4">
      <span className="font-display text-sm font-semibold text-text-primary block mb-3">
        Species Lookup
      </span>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          runSearch(query);
        }}
        className="flex gap-2 mb-3"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Scientific name, e.g. Chelonia mydas"
          className="flex-1 bg-abyss-800 border border-line rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:border-bio-500 outline-none"
        />
        <button
          type="submit"
          disabled={loading}
          className="font-mono text-xs font-medium bg-bio-500 text-abyss-950 rounded-lg px-3 py-2 hover:bg-bio-400 disabled:opacity-40 transition-colors"
        >
          Search
        </button>
      </form>

      {!searched && (
        <div className="flex flex-wrap gap-1.5">
          {EXAMPLE_SPECIES.map((name) => (
            <button
              key={name}
              onClick={() => {
                setQuery(name);
                runSearch(name);
              }}
              className="font-mono text-[11px] text-text-secondary border border-line rounded-full px-2.5 py-1 hover:border-bio-500 hover:text-bio-400 transition-colors italic"
            >
              {name}
            </button>
          ))}
        </div>
      )}

      {loading && <div className="h-20 bg-abyss-800 rounded-lg animate-pulse-glow mt-2" />}

      {error && <p className="text-xs text-coral-400 font-mono mt-2">{error}</p>}

      {!loading && taxon && (
        <div className="mt-3 pb-3 border-b border-line-soft">
          <p className="font-display text-sm italic text-text-primary">{taxon.scientific_name}</p>
          <p className="text-[11px] text-text-secondary mt-0.5">
            {[taxon.kingdom, taxon.phylum, taxon.class, taxon.order, taxon.family]
              .filter(Boolean)
              .join(" › ")}
          </p>
          {taxon.is_marine !== null && (
            <span
              className={`inline-block mt-1.5 font-mono text-[10px] px-2 py-0.5 rounded-full border ${
                taxon.is_marine
                  ? "border-bio-600/40 text-bio-400"
                  : "border-line text-text-tertiary"
              }`}
            >
              {taxon.is_marine ? "Confirmed marine" : "Not confirmed marine"}
            </span>
          )}
        </div>
      )}

      {!loading && occurrences && occurrences.occurrences.length > 0 && (
        <div className="mt-3">
          <p className="text-[11px] text-text-secondary mb-2">
            {occurrences.total_matched.toLocaleString()} occurrence records in OBIS · showing{" "}
            {occurrences.occurrences.length}
          </p>
          <ul className="space-y-1.5">
            {occurrences.occurrences.slice(0, 4).map((occ, i) => (
              <li key={i} className="font-mono text-[11px] text-text-tertiary flex justify-between">
                <span className="truncate">{occ.locality ?? "Unknown locality"}</span>
                <span className="text-text-secondary ml-2 shrink-0">
                  {occ.event_date?.slice(0, 10) ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && searched && occurrences && occurrences.occurrences.length === 0 && !error && (
        <p className="text-xs text-text-tertiary font-mono mt-2">
          No occurrence records found. Try the exact scientific (Latin) name.
        </p>
      )}
    </div>
  );
}
