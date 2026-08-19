"use client";

import { useState } from "react";

import { MetricGrid } from "@/components/metric-grid/MetricGrid";
import { VerdictCard } from "@/components/verdict-card/VerdictCard";
import { ZoneTabBar } from "@/components/zone-tab-bar/ZoneTabBar";
import { useZoneMacro } from "@/hooks/useZoneMacro";

export default function Home() {
  const [zone, setZone] = useState("us");
  const { data, error, loading } = useZoneMacro(zone);

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-6 bg-black px-4 py-8 text-white">
      <h1 className="text-xl font-semibold">Global Macro Shield</h1>

      <ZoneTabBar activeZone={zone} onZoneChange={setZone} />

      {loading && (
        <p className="text-sm text-white/50">Loading the latest macro read…</p>
      )}

      {error && (
        <p className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Couldn&apos;t load this zone&apos;s macro data: {error}. Try
          refreshing, or switch zones.
        </p>
      )}

      {data && (
        <>
          <VerdictCard phase={data.phase} />
          <MetricGrid metrics={data.metrics} />
        </>
      )}
    </main>
  );
}
