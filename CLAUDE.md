# MacroShield

This is a monorepo. Read this file for cross-cutting context, then the
project-specific file for whichever half you're working in:

- [`backend/CLAUDE.md`](./backend/CLAUDE.md) — API integrations, rules
  engine, ML layer, business-logic ownership, legal/compliance constraints.
- [`frontend/CLAUDE.md`](./frontend/CLAUDE.md) — design system, app
  structure, copy conventions.

See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for how the two talk to
each other and how the system is deployed.

## What this app does

MacroShield automates a full trading research pipeline in one funnel:
macro screening (economic cycle phase per zone) → sector rotation signal →
fundamental filter (valuation ratios + DCF) → technical/AI timing signal
(MACD/RSI + ML breakout probability) → alerts when a stock passes all four.

## Repo layout

```
macroshield/
  backend/     Python 3.11+ / FastAPI — the API, rules engine, ML layer
  frontend/    Next.js (App Router) / TypeScript / React — the web app
  docs/        Architecture notes and ADRs
```

Each subproject keeps its own dependency manifest, lockfile, and
`.gitignore` scoped to itself; the root `.gitignore` only adds monorepo-level
concerns on top.

## Global conventions

- Conventional commits (`feat:`, `fix:`, `chore:`, `docs:`) — see your
  global `~/.claude/CLAUDE.md` for the rest of your standing preferences
  (macOS-only shell commands, run tests before suggesting a commit, never
  hardcode secrets).
- Never push with a Claude Code trailer to this repo (per both subproject
  files) — confirm this still applies at the monorepo level or update if
  it's changed.
- The two subprojects were previously separate repos
  (`macroshield-backend`, `macroshield-frontend`, both public on GitHub)
  merged here with full commit history via `git subtree`. Those originals
  are kept around indefinitely as archives — this repo is the active one
  going forward.
- CI/CD (GitHub Actions) is not set up yet — both subproject files flag
  this as a near-term want. Worth revisiting now that both apps live in one
  repo (a single workflow can gate both, or two workflows path-filtered by
  `backend/**` / `frontend/**`).

## Open questions (carried over from the subproject files)

- Backend DB choice: Postgres is the *assumed* default in
  `backend/CLAUDE.md`, but your global stack notes say MySQL HeatWave on
  Oracle Cloud — these disagree and should be reconciled before the DB
  layer is built.
- Auth model — not designed on either side yet.
- Deployment target for MacroShield itself: nothing is deployed to the
  Oracle VM yet (verified — the VM currently only runs an unrelated app,
  `conjugationapp.service`). Hosting/deploy setup for MacroShield is still
  to be decided.
