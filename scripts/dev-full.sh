#!/usr/bin/env bash
# Full dev stack: SSH tunnel to macroshield-vm's Postgres, backend, frontend,
# then opens the browser once both are up. Ctrl+C tears everything down.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

TUNNEL_PID=""
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  [[ -n "$FRONTEND_PID" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  [[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "$TUNNEL_PID" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

wait_for() {
  # wait_for <url> <tries>
  for _ in $(seq 1 "$2"); do
    curl -sf "$1" >/dev/null 2>&1 && return 0
    sleep 0.5
  done
  echo "Timed out waiting for $1" >&2
  return 1
}

# 1. SSH tunnel — macroshield-vm's Postgres listens on 127.0.0.1 only
#    (see backend/CLAUDE.md), so DATABASE_URL points at 127.0.0.1:5433.
if lsof -iTCP:5433 -sTCP:LISTEN -n -P >/dev/null 2>&1; then
  echo "Port 5433 already has a listener — reusing existing tunnel."
else
  echo "Opening SSH tunnel to macroshield-vm..."
  ssh -N -L 5433:127.0.0.1:5432 macroshield-vm &
  TUNNEL_PID=$!
  for _ in $(seq 1 20); do
    lsof -iTCP:5433 -sTCP:LISTEN -n -P >/dev/null 2>&1 && break
    sleep 0.5
  done
fi

# 2. Backend
echo "Starting backend..."
(cd "$ROOT/backend" && uv run uvicorn app.main:app --reload) &
BACKEND_PID=$!
wait_for http://localhost:8000/health 40

# 3. Frontend
echo "Starting frontend..."
(cd "$ROOT/frontend" && npm run dev) &
FRONTEND_PID=$!
wait_for http://localhost:3000 40

# 4. Open browser
open "http://localhost:3000"

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop everything."
wait
