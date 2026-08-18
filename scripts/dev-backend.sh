#!/usr/bin/env bash
# Run the backend only. Doesn't touch the DB tunnel or the frontend — use
# this when you already have a tunnel open (or the DB isn't needed for
# what you're testing). See dev-full.sh for the everything-at-once version.
set -euo pipefail
cd "$(dirname "$0")/../backend"

exec uv run uvicorn app.main:app --reload
