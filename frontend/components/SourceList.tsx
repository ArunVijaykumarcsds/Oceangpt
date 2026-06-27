import type { SourceRef, SourceType } from "@/lib/types";

const SOURCE_LABELS: Record<SourceType, string> = {
  knowledge_base: "Knowledge base",
  obis: "OBIS",
  worms: "WoRMS",
  noaa: "NOAA CO-OPS",
  open_meteo: "Open-Meteo",
};

const SOURCE_COLORS: Record<SourceType, string> = {
  knowledge_base: "text-text-secondary border-line",
  obis: "text-bio-400 border-bio-600/40",
  worms: "text-bio-400 border-bio-600/40",
  noaa: "text-coral-400 border-coral-500/30",
  open_meteo: "text-coral-400 border-coral-500/30",
};

export function SourceList({ sources }: { sources: SourceRef[] }) {
  if (sources.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {sources.map((source, i) => (
        <span
          key={`${source.type}-${i}`}
          className={`font-mono text-[10px] px-2 py-1 rounded-full border ${SOURCE_COLORS[source.type]} bg-abyss-900/60`}
          title={source.detail ?? undefined}
        >
          {SOURCE_LABELS[source.type]}
          {source.detail === "failed" && <span className="text-coral-500 ml-1">⚠</span>}
        </span>
      ))}
    </div>
  );
}
