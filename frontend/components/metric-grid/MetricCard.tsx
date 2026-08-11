import type { ReactNode } from "react";

interface MetricCardProps {
  label: string;
  helpText: string;
  value: string;
  tag?: ReactNode;
  footer?: ReactNode;
  alert?: boolean;
}

export function MetricCard({
  label,
  helpText,
  value,
  tag,
  footer,
  alert = false,
}: MetricCardProps) {
  return (
    <div
      className={`flex flex-col gap-2 rounded-2xl border bg-white/5 p-4 ${
        alert ? "animate-pulse border-red-500" : "border-white/10"
      }`}
    >
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs font-medium tracking-wide text-white/50 uppercase">
          {label}
        </span>
        {tag}
      </div>
      <span className="text-2xl font-semibold text-white">{value}</span>
      <span className="text-xs text-white/40">{helpText}</span>
      {footer}
    </div>
  );
}
