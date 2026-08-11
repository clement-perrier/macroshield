import { AlertTriangle, Flame, Rocket, Shield } from "lucide-react";
import type { ComponentType } from "react";

import type { MacroPhase } from "@/types/macro";

interface PhaseConfig {
  headline: string;
  subtext: string;
  icon: ComponentType<{ className?: string }>;
  accent: string;
  bg: string;
  border: string;
}

export const PHASE_CONFIG: Record<MacroPhase, PhaseConfig> = {
  recovery: {
    headline: "Early Cycle: Active Industrial Expansion",
    subtext: "Recommended strategy: Cyclicals & Tech.",
    icon: Rocket,
    accent: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/40",
  },
  // Not specified in the original brief — provisional pending confirmation
  // from the business-logic owner. See frontend-CLAUDE.md open questions.
  expansion: {
    headline: "Peak Cycle: Broad-Based Growth",
    subtext: "Recommended strategy: Broad equities.",
    icon: Flame,
    accent: "text-amber-300",
    bg: "bg-amber-400/10",
    border: "border-amber-400/40",
  },
  slowdown: {
    headline: "Stagflation / Braking",
    subtext: "Recommended strategy: Defensive sectors only.",
    icon: Shield,
    accent: "text-orange-400",
    bg: "bg-orange-500/10",
    border: "border-orange-500/40",
  },
  recession: {
    headline: "Bear Market / Crisis",
    subtext: "Recommended strategy: Cash, Bonds, or Short.",
    icon: AlertTriangle,
    accent: "text-red-500",
    bg: "bg-red-600/10",
    border: "border-red-600/40",
  },
};
