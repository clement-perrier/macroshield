export type MacroPhase = "recovery" | "expansion" | "slowdown" | "recession";

/**
 * The backend's OpenAPI schema types this response as a generic object
 * (`additionalProperties: true`, no field-level schema yet), so these types
 * are hand-written from the live `/zones/{zone}/macro` response rather than
 * generated. Revisit once the backend publishes a concrete schema.
 */
export interface MacroMetric {
  series_id: string;
  label: string;
  date: string;
  value: number;
  growth_score?: number;
  inflation_score?: number;
  trend?: string;
}

export interface ZoneMacroResponse {
  phase: MacroPhase;
  confidence: number;
  is_transition: boolean;
  recession_override: boolean;
  metrics: MacroMetric[];
}
