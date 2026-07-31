"use client";

import { useEffect, useState } from "react";

import { getZoneMacro } from "@/lib/api-client";
import type { ZoneMacroResponse } from "@/types/macro";

interface ZoneMacroState {
  data: ZoneMacroResponse | null;
  error: string | null;
  loading: boolean;
}

export function useZoneMacro(zone: string): ZoneMacroState {
  const [state, setState] = useState<ZoneMacroState>({
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    getZoneMacro(zone)
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
  }, [zone]);

  return state;
}
