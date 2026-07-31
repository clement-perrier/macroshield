"use client";

import { MetricGrid } from "@/components/metric-grid/MetricGrid";
import { VerdictCard } from "@/components/verdict-card/VerdictCard";
import { useZoneMacro } from "@/hooks/useZoneMacro";

// Hardcoded until the zone tab-switching UI is built.
const ZONE = "us";

export default function Home() {
  const { data, error, loading } = useZoneMacro(ZONE);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-2xl flex-col gap-6 bg-black px-4 py-8 text-white">
      <h1 className="text-xl font-semibold">Global Macro Shield</h1>

      {loading && (
        <p className="text-sm text-white/50">Loading the latest macro read…</p>
      )}

      {error && (
        <p className="rounded-xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-300">
          Couldn&apos;t reach the macro data backend ({error}). Check that the
          API server is running and try refreshing.
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
