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
    throw new Error(`Zone macro fetch failed with status ${response.status}`);
  }

  return response.json();
}
