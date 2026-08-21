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

Backend and database both run on `macroshield-vm` (deployed 2026-08-20),
deliberately co-located so the app can reach Postgres over `127.0.0.1`
without ever exposing the database to the network — see ADR 0001.
`oracle-vm` remains conjugationapp-only; no MacroShield process, systemd
unit, or files exist there.

- **Backend**: FastAPI under `uvicorn`, run as the `macroshield-backend`
  systemd service (`User=ubuntu`, auto-restart, starts on boot), bound to
  `127.0.0.1:8000` — not exposed directly. Deployed to `/opt/macroshield`
  (shallow clone of this repo), dependencies via `uv`/`uv.lock`, Python
  3.11 installed via `uv python install` (the VM's system Python is
  3.10). Secrets live in `/opt/macroshield/backend/.env` (mode 600, never
  committed), same shape as the local dev `.env`.
- **Reverse proxy / TLS**: nginx proxies `api-macroshield.crcbp.com` (A
  record in Route 53 → `192.9.224.120`) to `127.0.0.1:8000`, with a
  Let's Encrypt cert via `certbot --nginx` (auto-renews via
  `certbot.timer`, expires 2026-11-18, HTTP→HTTPS redirect on). TLS is
  required, not cosmetic: the frontend serves over HTTPS from Vercel, and
  browsers block `fetch` calls from an HTTPS page to a plain-HTTP origin
  (mixed content), so the backend has to terminate TLS for the frontend
  to be able to call it at all.
- **Firewall**: OS-level `iptables` on the VM only allowed port 22
  inbound by default (Oracle's stock image config) — ports 80/443 were
  added explicitly and persisted via `netfilter-persistent`; the matching
  OCI Security List ingress rules were opened in the console. Postgres
  itself is untouched by this — still `127.0.0.1`-only per ADR 0001, only
  reachable from processes on the box itself (the backend) or a dev
  machine's SSH tunnel.
- **CORS**: `app/main.py` currently only allows `http://localhost:3000`.
  Needs updating once the frontend has a real Vercel URL — not done yet
  since the frontend isn't deployed.
- Frontend: **Vercel** (decided 2026-08-12) — path of least resistance for
  Next.js; the backend/DB stay on the Oracle VM, so the frontend will call
  it over its public endpoint (`https://api-macroshield.crcbp.com`) rather
  than the VM's private subnet.
- Both repos currently have no CI/CD (no `.github/workflows`) — see
  root `CLAUDE.md` § "Global conventions" for the GitHub Actions plan.

## History note

`backend/` and `frontend/` were merged into this monorepo from two
previously separate repos (`macroshield-backend`, `macroshield-frontend`)
via `git subtree`, preserving full original commit history. Those two
repos still exist standalone on GitHub as archives; this monorepo is where
active development happens going forward.
