import type { MacroMetric } from "@/types/macro";

import { MetricCard } from "./MetricCard";

interface MetricGridProps {
  metrics: MacroMetric[];
}

// Match by `label`, not `series_id`: the backend picks a different source
// FRED series per zone (e.g. EU's PMI proxy is BSCICP02DEM460S, not US's
// IPMAN — see backend/app/core/zones.py), but always assigns the same fixed
// label per metric role regardless of zone (see backend/app/routers/macro.py).
function findMetric(
  metrics: MacroMetric[],
  label: string,
): MacroMetric | undefined {
  return metrics.find((metric) => metric.label === label);
}

// Backend trends arrive as enum-ish strings (e.g. "falling_fast"); turn them
// into plain-language text rather than hardcoding every known value.
function humanizeTrend(trend: string): string {
  return trend
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function MetricGrid({ metrics }: MetricGridProps) {
  const pmi = findMetric(metrics, "PMI proxy growth momentum");
  const inflation = findMetric(metrics, "Inflation momentum");
  const rate = findMetric(metrics, "Central bank rate");
  const yieldCurve = findMetric(metrics, "Yield curve");

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {pmi && (
        <MetricCard
          label="PMI Proxy"
          helpText="A momentum read on industrial activity, standing in for the manufacturing PMI."
          value={pmi.value.toFixed(1)}
          tag={
            pmi.growth_score !== undefined && (
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  pmi.growth_score > 0
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-red-500/15 text-red-400"
                }`}
              >
                {pmi.growth_score > 0 ? "Expansionary ↑" : "Contracting ↓"}
              </span>
            )
          }
        />
      )}

      {inflation && (
        <MetricCard
          label="Inflation (CPI)"
          helpText="Consumer Price Index level. Red dot means prices are running hot."
          value={inflation.value.toFixed(1)}
          tag={
            inflation.inflation_score !== undefined && (
              <span
                className={`h-2.5 w-2.5 rounded-full ${
                  inflation.inflation_score > 0 ? "bg-red-500" : "bg-white/30"
                }`}
                title={
                  inflation.inflation_score > 0 ? "Overheating" : "Stagnant"
                }
              />
            )
          }
        />
      )}

      {rate && (
        <MetricCard
          label="Central Bank Rate"
          helpText="This zone's key policy interest rate."
          value={`${rate.value.toFixed(2)}%`}
          footer={
            rate.trend && (
              <span className="text-xs text-white/50">
                {humanizeTrend(rate.trend)}
              </span>
            )
          }
        />
      )}

      {yieldCurve && (
        <MetricCard
          label="Yield Curve"
          helpText="Spread between long- and short-term government bond yields. Negative means the curve is inverted, a classic recession warning."
          value={`${yieldCurve.value >= 0 ? "+" : ""}${yieldCurve.value.toFixed(2)}%`}
          alert={yieldCurve.value < 0}
          tag={
            yieldCurve.value < 0 && (
              <span className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs font-semibold text-red-400">
                INVERTED
              </span>
            )
          }
          footer={
            yieldCurve.trend && (
              <span className="text-xs text-white/50">
                {humanizeTrend(yieldCurve.trend)}
              </span>
            )
          }
        />
      )}
    </div>
  );
}
