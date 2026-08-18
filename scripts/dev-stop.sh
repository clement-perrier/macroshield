#!/usr/bin/env bash
# Kill anything still listening on the dev ports (backend, frontend, DB
# tunnel). Safety net for when dev-full.sh's Ctrl+C cleanup didn't run
# (terminal force-closed, crash) or left a child process (uvicorn --reload's
# worker, next-server) orphaned and still holding a port.
set -euo pipefail

PORTS=(8000 3000 5433)
NAMES=("backend" "frontend" "DB tunnel")

for i in "${!PORTS[@]}"; do
  port="${PORTS[$i]}"
  name="${NAMES[$i]}"
  pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null || true)
  if [[ -z "$pids" ]]; then
    echo "Port $port ($name): nothing listening."
    continue
  fi
  echo "Port $port ($name): killing $pids"
  kill $pids 2>/dev/null || true
done
