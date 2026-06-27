import { Header } from "@/components/Header";
import { ChatPanel } from "@/components/ChatPanel";
import { TideGaugeCard } from "@/components/TideGaugeCard";
import { MarineConditionsCard } from "@/components/MarineConditionsCard";
import { SpeciesLookupCard } from "@/components/SpeciesLookupCard";

export default function DashboardPage() {
  return (
    <>
      <Header />
      <main className="flex-1 max-w-[1400px] w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-6 h-[calc(100vh-120px)]">
          {/* Left: live data widgets, stacked */}
          <div className="flex flex-col gap-4 overflow-y-auto pr-1">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TideGaugeCard />
              <MarineConditionsCard />
            </div>
            <SpeciesLookupCard />

            <footer className="font-mono text-[10px] text-text-tertiary pt-2 pb-6">
              Data sources: Ocean Biodiversity Information System (OBIS) · World Register of
              Marine Species (WoRMS) · NOAA CO-OPS Tides &amp; Currents · Open-Meteo Marine
              Weather API. Built for research and educational use.
            </footer>
          </div>

          {/* Right: persistent chat panel */}
          <div className="h-full min-h-[500px]">
            <ChatPanel />
          </div>
        </div>
      </main>
    </>
  );
}
