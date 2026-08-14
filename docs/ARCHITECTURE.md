# Architecture

## Components

```
┌──────────────┐        HTTP (JSON)        ┌──────────────┐        HTTPS        ┌─────────────┐
│   frontend   │ ───────────────────────▶  │   backend    │ ──────────────────▶ │   FRED API   │
│  Next.js/TS  │ ◀───────────────────────  │ FastAPI/Py   │ ◀────────────────── │ (St. Louis   │
│  localhost:  │                            │ localhost:   │                     │  Fed)        │
│  3000        │                            │ 8000         │                     └─────────────┘
└──────────────┘                            └──────────────┘
                                                    │
                                                    ▼
                                             ┌──────────────┐
                                             │  PostgreSQL  │
                                             │  self-hosted │
                                             │  on the free │
                                             │  Oracle VM   │
                                             └──────────────┘
```

- **frontend** (`frontend/`) — Next.js App Router app. Talks to the backend
  over HTTP via `NEXT_PUBLIC_API_BASE_URL` (`http://localhost:8000` in dev).
  No direct access to the database or to FRED.
- **backend** (`backend/`) — FastAPI service. Owns all external data
  access (FRED API only — never scraped, per FRED's terms of use), the
  macro/sector/fundamental/technical rules engine, and (later) the ML
  breakout model. Exposes the public API contract the frontend consumes.
- **Database** — PostgreSQL 17, self-hosted on a dedicated Oracle Cloud
  Always Free VM (`macroshield-vm`, separate from `oracle-vm` which runs
  the unrelated `conjugationapp`) — decided 2026-08-10, provisioned
  2026-08-13. See `docs/adr/0001-self-hosted-postgres-on-dedicated-vm.md`
  for the full reasoning, alternatives considered, and tuning applied.
  TimescaleDB extension evaluated and deferred — nothing depends on it yet.

## API contract

The backend generates an OpenAPI schema (`/openapi.json`); the frontend is
meant to codegen its TypeScript types from that rather than hand-syncing
response shapes — see `backend/CLAUDE.md` § "Contract-sharing tip". This
matters more, not less, now that both live in one repo: it's tempting to
just import backend types directly, but keep them decoupled through the
generated contract so the boundary stays enforced.

## Deployment

The backend app itself is not deployed yet. Database is: PostgreSQL 17
runs on `macroshield-vm`, provisioned 2026-08-13 (see ADR 0001), listening
on `127.0.0.1` only — not reachable from the network, only via SSH tunnel
from a dev machine for now. `oracle-vm` remains conjugationapp-only; no
MacroShield process, systemd unit, or files exist there.

- Backend: not yet deployed. Once it is, presumably a systemd service on
  `macroshield-vm` (matching the existing pattern used for
  `conjugationapp` on its own VM), reachable from the frontend over a
  public endpoint.
- Frontend: **Vercel** (decided 2026-08-12) — path of least resistance for
  Next.js; the backend/DB stay on the Oracle VM, so the frontend will call
  it over its public endpoint rather than the VM's private subnet.
- Both repos currently have no CI/CD (no `.github/workflows`) — see
  root `CLAUDE.md` § "Global conventions" for the GitHub Actions plan.

## History note

`backend/` and `frontend/` were merged into this monorepo from two
previously separate repos (`macroshield-backend`, `macroshield-frontend`)
via `git subtree`, preserving full original commit history. Those two
repos still exist standalone on GitHub as archives; this monorepo is where
active development happens going forward.
