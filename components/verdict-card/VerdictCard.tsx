import type { MacroPhase } from "@/types/macro";

import { PHASE_CONFIG } from "./phase-config";

interface VerdictCardProps {
  phase: MacroPhase;
}

export function VerdictCard({ phase }: VerdictCardProps) {
  const config = PHASE_CONFIG[phase];
  const Icon = config.icon;

  return (
    <section
      className={`flex min-h-[30vh] flex-col items-center justify-center gap-3 rounded-3xl border px-6 py-10 text-center backdrop-blur-sm ${config.bg} ${config.border}`}
    >
      <Icon className={`h-10 w-10 ${config.accent}`} />
      <h2 className={`text-2xl font-semibold sm:text-3xl ${config.accent}`}>
        {config.headline}
      </h2>
      <p className="text-sm text-white/70 sm:text-base">{config.subtext}</p>
    </section>
  );
}
