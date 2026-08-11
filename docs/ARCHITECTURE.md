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
- **Database** — PostgreSQL, self-hosted on the Oracle Cloud Always Free VM
  (`oracle-vm`) — decided 2026-08-10. Oracle has no free *managed* Postgres
  offering: their paid "OCI Database with PostgreSQL" service is billed per
  OCPU/storage, and the free Autonomous Database is a different, non-Postgres
  engine. Running it ourselves on the free compute/storage allocation is the
  only $0 way to get real Postgres, at the cost of owning patching, backups,
  and tuning ourselves. TimescaleDB extension still to evaluate for the
  time-series indicator history.

## API contract

The backend generates an OpenAPI schema (`/openapi.json`); the frontend is
meant to codegen its TypeScript types from that rather than hand-syncing
response shapes — see `backend/CLAUDE.md` § "Contract-sharing tip". This
matters more, not less, now that both live in one repo: it's tempting to
just import backend types directly, but keep them decoupled through the
generated contract so the boundary stays enforced.

## Deployment

Nothing is deployed yet. Confirmed by SSH to the Oracle Cloud VM
(2026-08-10): the VM currently runs one unrelated Spring Boot app
(`conjugationapp.service`, a different project) — no MacroShield backend or
frontend process, systemd unit, or files exist there. When deployment is
set up:

- Backend: presumably a systemd service on the Oracle VM (matching the
  existing pattern used for the other app), reachable from the frontend
  over the VM's subnet or a public endpoint.
- Database: PostgreSQL installed directly on the same free VM (or a second
  Always Free VM for isolation from the unrelated `conjugationapp`
  workload — Always Free includes 2 AMD VMs plus up to 4 Arm OCPUs to split
  across instances). Not yet installed as of 2026-08-10.
- Frontend: target not yet decided (Vercel is the path of least resistance
  for Next.js; self-hosting alongside the backend is the alternative if
  everything should live on the one VM).
- Both repos currently have no CI/CD (no `.github/workflows`) — see
  root `CLAUDE.md` § "Global conventions" for the GitHub Actions plan.

## History note

`backend/` and `frontend/` were merged into this monorepo from two
previously separate repos (`macroshield-backend`, `macroshield-frontend`)
via `git subtree`, preserving full original commit history. Those two
repos still exist standalone on GitHub as archives; this monorepo is where
active development happens going forward.
