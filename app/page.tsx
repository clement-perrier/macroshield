"use client";

import { useHealthCheck } from "@/hooks/useHealthCheck";

export default function Home() {
  const { data, error, loading } = useHealthCheck();

  return (
    <main>
      <h1>Backend connection check</h1>
      {loading && <p>Loading...</p>}
      {error && <pre>Error calling backend: {error}</pre>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
    </main>
  );
}
