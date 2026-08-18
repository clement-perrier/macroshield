"use client";

import { useEffect, useState } from "react";

import { getZoneMacro } from "@/lib/api-client";
import type { ZoneMacroResponse } from "@/types/macro";

interface ZoneMacroState {
  data: ZoneMacroResponse | null;
  error: string | null;
  loading: boolean;
}

// Result is tagged with the zone it was fetched for, so a render can tell
// whether `state` is still catching up to a just-changed `zone` prop and
// report `loading` instead of flashing the previous zone's data.
interface FetchedFor extends ZoneMacroState {
  zone: string;
}

export function useZoneMacro(zone: string): ZoneMacroState {
  const [state, setState] = useState<FetchedFor>({
    zone,
    data: null,
    error: null,
    loading: true,
  });

  useEffect(() => {
    let cancelled = false;

    getZoneMacro(zone)
      .then((data) => {
        if (!cancelled) setState({ zone, data, error: null, loading: false });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            zone,
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

  if (state.zone !== zone) {
    return { data: null, error: null, loading: true };
  }

  return state;
}
