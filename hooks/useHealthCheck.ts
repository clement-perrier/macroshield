"use client";

import { useEffect, useState } from "react";

import { getHealth } from "@/lib/api-client";
import type { HealthResponse } from "@/types/health";

interface HealthCheckState {
  data: HealthResponse | null;
  error: string | null;
  loading: boolean;
}

export function useHealthCheck(): HealthCheckState {
  const [state, setState] = useState<HealthCheckState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    getHealth()
      .then((data) => {
        if (!cancelled) setState({ data, error: null, loading: false });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            data: null,
            error: err instanceof Error ? err.message : "Unknown error",
            loading: false,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
