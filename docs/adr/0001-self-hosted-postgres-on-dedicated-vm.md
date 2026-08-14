# 0001. Self-hosted PostgreSQL on a dedicated Oracle Cloud Always Free VM

## Status

Accepted. Decided 2026-08-10, provisioned 2026-08-13.

## Context

The backend needed a storage layer for two reasons: trailing history for
the macro engine's Z-score normalization (`backend/CLAUDE.md` § "Cycle
classification logic"), and to stop hitting the FRED API on every request
for indicators that only update monthly.

Options considered for the database engine/hosting:

- **Oracle "OCI Database with PostgreSQL"** (managed) — billed per
  OCPU/storage, not part of Always Free. Rejected on cost.
- **Oracle Autonomous Database** (Always Free tier) — free, but a
  different, non-Postgres engine. Rejected: not actually Postgres.
- **SQLite** — raised independently mid-project by another suggestion as
  a "fine for a prototype" default. Rejected: the project had already
  verified self-hosted Postgres is genuinely free (see below), so there
  was no cost/complexity reason to use a different engine than the one
  actually planned for production, and `TimescaleDB` (a Postgres
  extension, no SQLite equivalent) was already flagged as worth
  evaluating for the time-series indicator data.
- **Self-hosted PostgreSQL on Oracle Always Free compute** — the only $0
  path to *real* Postgres. Costs us patching, backups, and tuning
  ourselves instead of a managed provider doing it.

Once self-hosting was settled, a second question came up at actual
provisioning time (2026-08-13): which VM. The obvious option — the
existing `oracle-vm` — was already running an unrelated Spring Boot app
(`conjugationapp.service`) at ~956MB total RAM with **zero swap and only
~65–120MB free**. Installing Postgres there risked resource contention
with a live app on shared infrastructure.

## Decision

Self-host PostgreSQL, on a **second, dedicated** Always Free VM
(`VM.Standard.E2.1.Micro`, SSH alias `macroshield-vm`, 192.9.224.120) —
not `oracle-vm`. Oracle's Always Free tier includes 2 AMD micro instances;
only 1 of 2 was in use, so the second was free to claim rather than
squeezing onto an already-strained box.

Implementation specifics:

- PostgreSQL **17** via the official PGDG apt repository (Ubuntu 22.04's
  own repo only ships 14).
- 2GB swapfile added as an OOM safety net on a 956MB-RAM box.
- Tuned down from Postgres's defaults for that RAM budget:
  `max_connections=20`, `effective_cache_size=384MB`,
  `maintenance_work_mem=48MB` (via `ALTER SYSTEM`, so it survives package
  upgrades).
- Listens on `127.0.0.1` only — never exposed to the network. Reached
  from a dev machine via SSH tunnel (`ssh -N -L 5433:127.0.0.1:5432
  macroshield-vm`), never a public port.
- `macroshield` role + database, password generated with `openssl rand
  -hex 24`, stored only in `backend/.env` (gitignored) — never committed,
  never logged.
- TimescaleDB: evaluated and explicitly deferred — nothing in the schema
  depends on it yet (see ADR-worthy note in `backend/CLAUDE.md` § "Tech
  stack" if that changes).

## Consequences

**Positive**: real Postgres semantics (matters for `ON CONFLICT DO
UPDATE` upserts, future TimescaleDB path), fully isolated from
`conjugationapp` — no shared-resource risk, $0 cost, swap headroom
absorbs memory spikes instead of triggering the OOM killer.

**Negative**: we own patching/backups/tuning with no managed fallback;
956MB RAM is a hard ceiling that will eventually force either a bigger
(no-longer-free) shape or moving the workload elsewhere; no automated
backup strategy exists yet (not addressed by this ADR).

**Discovered in the process**: running the actual migration and app
against this real instance (rather than the sqlite fixture used in unit
tests) surfaced a real bug — daily FRED series' full history (e.g.
`T10Y2Y`, ~13k rows) exceeded Postgres's 32,767-bind-parameter-per-
statement limit on upsert. Fixed by batching upserts at ~8,191
rows/statement, with a regression test added
(`tests/test_fred_cache.py::test_refresh_series_batches_large_series`).
This is a concrete argument for testing against the real target engine
before considering a storage layer done, not just a mocked/sqlite
substitute.
