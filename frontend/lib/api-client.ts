import type { HealthResponse } from "@/types/health";
import type { ZoneMacroResponse } from "@/types/macro";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json();
}

export async function getZoneMacro(zone: string): Promise<ZoneMacroResponse> {
  const response = await fetch(`${API_BASE_URL}/zones/${zone}/macro`);

  if (!response.ok) {
    // FastAPI error responses carry a `detail` string with the actual
    // reason (e.g. "Need at least 61 momentum observations, got 49") —
    // surface that instead of a generic status-code message, since a 422
    // (bad/insufficient data) reads very differently to a user than a 5xx
    // (server actually unreachable).
    const detail = await response
      .json()
      .then((body: { detail?: string }) => body.detail)
      .catch(() => undefined);

    throw new Error(
      detail ?? `Zone macro fetch failed with status ${response.status}`,
    );
  }

  return response.json();
}
