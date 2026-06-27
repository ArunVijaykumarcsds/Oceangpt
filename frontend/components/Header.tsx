export function Header() {
  return (
    <header className="border-b border-line-soft bg-abyss-950/80 backdrop-blur-sm sticky top-0 z-20">
      <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <DepthMark />
          <div>
            <h1 className="font-display font-semibold text-lg tracking-tight text-text-primary">
              OceanGPT
            </h1>
            <p className="font-mono text-[11px] text-text-tertiary tracking-wide">
              MARINE INTELLIGENCE DASHBOARD
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-mono text-[11px] text-text-secondary">
          <LiveDot />
          <span>OBIS · WoRMS · NOAA · OPEN-METEO</span>
        </div>
      </div>
    </header>
  );
}

/** Signature mark: a simplified depth-gauge tick, this dashboard's recurring motif. */
function DepthMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
      <circle cx="14" cy="14" r="12.5" stroke="var(--bio-500)" strokeWidth="1" opacity="0.4" />
      <circle cx="14" cy="14" r="8.5" stroke="var(--bio-500)" strokeWidth="1" opacity="0.6" />
      <circle cx="14" cy="14" r="2" fill="var(--bio-500)" />
      <line x1="14" y1="1.5" x2="14" y2="4.5" stroke="var(--bio-400)" strokeWidth="1.5" />
    </svg>
  );
}

export function LiveDot() {
  return (
    <span className="relative flex h-2 w-2">
      <span className="absolute inline-flex h-full w-full rounded-full bg-bio-500 animate-pulse-glow" />
    </span>
  );
}
