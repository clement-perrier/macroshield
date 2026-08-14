# MacroShield — Backend

This file is project memory for Claude Code. Read it before writing code in this repo.
Never push any thing to the github repo with Claude trailer. 
Keep in mind Pythin is not my speciality, don't hesitate to explain lines of code.
After any non-trivial backend change, walk through it in plain language —
see `.claude/skills/explain-changes/SKILL.md` (auto-triggers, no slash command needed).

## What this app does

MacroShield is a web app that automates a full trading research pipeline in one funnel:

1. **Macro screening** — pull 4 economic indicators per geographic zone (US, Eurozone/Germany, China) and classify each zone into one of 4 economic cycle phases: **Recovery, Expansion, Slowdown, Recession**.
2. **Sector rotation** — cross-reference the zone's phase against sector valuation to produce a **green / orange / blue** signal (good macro + cheap sector / good macro but expensive sector / bad macro but a contrarian bargain).
3. **Fundamental filter** — score stocks with valuation ratios (P/E, EV/EBITDA, Debt/Equity, FCF yield) and a DCF-based intrinsic value estimate, to isolate undervalued companies.
4. **Technical/AI timing signal** — MACD/RSI plus an ML model (LSTM/Transformer) trained to tell a real breakout from a false signal ("bull trap").
5. **Alerts** — push a notification when a stock has passed all four filters.

This repo is the **backend**: data ingestion, the rules engine, the ML layer, and the API the frontend consumes. The frontend is a **separate repo** (Next.js) — treat the API as a public contract, not something you can silently reshape.

## Roles — who decides what

- **My brother**: owns business logic — the exact thresholds, financial formulas, phase-matrix rules, and legal/compliance sign-off. Numbers he specifies (e.g. "+0.3%/month for 3 months = rising inflation") are **starting values**, not hardcoded truths.
- **Me (this repo)**: implementation — API integrations, the rules/classification engine, ML, backend services.
- **Rule for Claude Code**: any threshold, weight, or cutoff that came from the business logic (Z-score bands, PMI cutoffs, valuation thresholds) must live in **config** (a settings module, DB table, or YAML — not a magic number buried in a function), because these will change as the strategy gets tuned. See "Auto-Tune" in the roadmap below — thresholds are meant to be mutated at runtime by users and by the ML layer.

## Tech stack

- **Confirmed**: Python 3.11+, FastAPI. Database: PostgreSQL, self-hosted —
  decided 2026-08-10, provisioned 2026-08-13. Oracle has no free managed
  Postgres offering (their paid "OCI Database with PostgreSQL" is billed per
  OCPU/storage; the free Autonomous Database is a different, non-Postgres
  engine), so this runs unmanaged: we own patching, backups, and tuning
  ourselves. TimescaleDB was considered and explicitly deferred (2026-08-13)
  — nothing in the schema depends on it yet; revisit once there's an actual
  performance reason to.
  - **Runs on a second, dedicated Always Free VM** (`macroshield-vm`,
    `192.9.224.120`, SSH alias in `~/.ssh/config`) — **not** `oracle-vm`,
    which is a different VM that only runs the unrelated `conjugationapp`.
    Both are free `VM.Standard.E2.1.Micro` (1 OCPU, ~956MB RAM) instances;
    `macroshield-vm` was created 2026-08-13 specifically to keep MacroShield
    off a box that was already at ~50% RAM from `conjugationapp`.
  - Postgres 17 via the official PGDG apt repo (Ubuntu 22.04 ships 14).
    Tuned down for the 956MB box: `max_connections=20`,
    `effective_cache_size=384MB`, `maintenance_work_mem=48MB` (`ALTER
    SYSTEM`, so it survives `apt` upgrades). 2GB swapfile added as an OOM
    safety net.
  - Listens on `127.0.0.1` only — not reachable from the network at all,
    by design. From a dev machine, tunnel first: `ssh -N -L
    5433:127.0.0.1:5432 macroshield-vm`, then point `DATABASE_URL` at
    `127.0.0.1:5433` (see `backend/.env`, gitignored — real credentials
    live only there, never in this file or in git).
  - `app.services.fred_cache.refresh_series` batches upserts at ~8191
    rows/statement — Postgres's 32,767-bind-parameter limit is real and
    was hit in practice by daily series' full history (`T10Y2Y`, ~13k
    rows) the first time this ran against actual Postgres; the sqlite test
    fixture never had enough rows to catch it. Don't remove the batching.
- WHen adding new features, suggests frameworks or any that would be more optimized or good practice. E.g asyncio
- **Assumed defaults** (flag if you want something else — not yet locked in):
  - `pandas` + `pandas-ta` (or `TA-Lib` if available in the environment) for MACD/RSI.
  - `scikit-learn` for the backtester / auto-tune logic; `PyTorch` if/when the LSTM/Transformer pattern-recognition model is built.
  - APScheduler (simple) or Celery + Redis (if we need distributed/retryable jobs) for the periodic FRED pulls and the 6-hourly news scan.
  - `pydantic` v2 for schemas, `alembic` for migrations, `pytest` for tests, `ruff` + `black` for lint/format, `uv` or `poetry` for dependency management.
- Treat all of the above as defaults to confirm with me, not settled decisions — say so explicitly if you change one.
- Keep in mind we have to setup a CI/CD pipeline to streamline the updates and deployement processes (backend and frontend), bring this subjects when you think it's time to set it up. Beside I would like to use a tool such as Github Actions if possible, to be discussed.

## Zones & indicators — canonical data sources

Do not substitute different series IDs without flagging it — these were chosen deliberately (see Legal section below for *why*).

| Zone | Industrial/PMI proxy | Inflation | Central bank rate | Yield curve |
|---|---|---|---|---|
| 🇺🇸 US | `INDPRO` (Industrial Production Index) — proxy for PMI; `MANEMP` as an alternate proxy | `CPIAUCSL` | `FEDFUNDS` | `T10Y2Y` (FRED computes this directly) |
| 🇪🇺 Eurozone/Germany | `DEUPRMNVG01IXOBM` (German manufacturing production) or `BSCILM02DEM160S` (German manufacturing business confidence — closer PMI equivalent) | `CP0000EZ19M086NEST` | `ECBMAINREFTR` | Computed: `IRLTLT01DEM156N` (DE 10Y) − `IR3TIB01DEM156N` (3-month interbank rate, used as the 2Y stand-in for Europe) |
| 🇨🇳 China | `CHIPRMNTO01G00M` (industrial production growth) | `CHNCPIALLMINMEI` | `INTDSRCNM193N` (PBOC rate) | Not available pre-built — likely needs a manual proxy or omission; flag to me before inventing one |

All series above are pulled from the **FRED API** (`https://api.stlouisfed.org/fred/...`), never scraped.

## Legal / compliance — hard constraints

These come directly from FRED's terms of use and are non-negotiable, not style preferences:

- **No data reselling.** Never build a screen that just displays a raw FRED chart behind a paywall. The product must always be the *derived* output (phase classification, Z-score, cross-referenced signal) — never the raw series itself.
- **No scraping.** All FRED access goes through the official API with a key read from an environment variable (e.g. `FRED_API_KEY`). Never write a scraper against fred.stlouisfed.org — this is an IP-ban risk for the whole app, not just bad practice.
- **Avoid licensed third-party series.** Official ISM or S&P Global PMI series are privately owned and licensed — do not wire those up for paid features. This is exactly why the table above uses `INDPRO`/`BSCILM02DEM160S` as free, public proxies instead of the real PMI. If you're ever tempted to add a "real" PMI series to improve accuracy, check with me first — it changes the legal posture of the whole product.
- **Disclaimer.** The app (frontend, but confirm text originates here or in shared config) must display: *"MacroShield uses the FRED (Federal Reserve Economic Data) API to collect public macroeconomic indicators. MacroShield is not affiliated with or endorsed by the Federal Reserve Bank of St. Louis."*
- This app is **not providing personalized financial advice** — keep language in code/comments/API responses framed as "signals" and "classifications," not "recommendations," in case that framing matters later for compliance.

## Cycle classification logic

**Trend definitions** (used to bucket each raw indicator before applying the phase matrix):

- **Inflation (CPI)** — look at the 3-month trend:
  - Rising fast: >+0.3%/month for 3 consecutive months (or annual CPI stepping 2% → 2.5% → 3%).
  - Stagnant: monthly variation between −0.1% and +0.1%.
  - Falling: worse than −0.2%/month (disinflation).
- **Central bank rate** — compare current rate to 3–6 months ago:
  - Rising/high: hikes at recent meetings (e.g. +0.25/+0.50%) → intentional slowdown.
  - Plateau: unchanged for 3+ months (distinguish "high plateau" = end of tightening vs "low plateau" = end of a crisis — this distinction isn't automatable from the rate alone, may need the CPI/PMI context to disambiguate).
  - Falling/low: cuts at recent meetings → stimulus.
- **Yield curve (10Y−2Y)** — direct sign read from `T10Y2Y` (US) or the computed spread (Europe):
  - Positive = normal.
  - Negative = inverted = recession warning (historically ~12–18 months lead time).

**Z-score normalization** — instead of hardcoding thresholds per indicator, compute the Z-score against trailing 5-year history:

```
Z = (current_value - historical_mean) / historical_stddev
```

- `-1 <= Z <= 1` → normal/stagnant.
- `Z > 1.5` → abnormally high (e.g. overheating inflation or rates).
- `Z < -1.5` → abnormally low (e.g. economy at a standstill).

**4-phase decision matrix** (the starting IF/ELSE — expect this to get refined):

| PMI proxy trend | Inflation | Central bank rate | Yield curve | Phase |
|---|---|---|---|---|
| Rising (>50) | Low/stable | Low or stable | Normal | **Phase 1 — Recovery** (favor cyclicals) |
| Rising (>55) | Rising fast | Rising | Normal | **Phase 2 — Expansion** (favor energy/materials) |
| Falling (<50) | High/stagnant | High | Inverted | **Phase 3 — Slowdown** (favor healthcare/defensive) |
| Falling (<45) | Falling fast | Falling fast | Normalizing post-inversion | **Phase 4 — Recession** (cash / short) |

Implement this as a pure, testable function per zone — it's the single most important piece of business logic in the backend, and it should be trivial to unit test against fixed input vectors.

## Sector rotation signal

Cross-reference the zone's phase against sector valuation (e.g. sector P/E vs its own historical range):

- **Green** — phase favors cyclicals *and* the cyclical sector is undervalued → strong signal, start ranking individual stocks inside it.
- **Orange** (the "value trap") — phase favors cyclicals but the sector is already overvalued → the rally is priced in, look for another compatible sector or wait for a pullback.
- **Blue** (contrarian alert) — phase still looks bad, but a cyclical sector is deeply undervalued and weekly MACD is turning up from below zero → possible early accumulation.

## Fundamental filter (plain-language definitions, for consistent naming in code/docs)

- **P/E (Price/Earnings)**: share price ÷ earnings per share — how many years of current profit you're paying for.
- **EV/EBITDA**: enterprise value ÷ operating earnings before interest/tax/depreciation — similar idea to P/E but capital-structure-neutral, useful for comparing companies with different debt levels.
- **Debt/EBITDA**: leverage relative to operating earnings — how many years of earnings it'd take to pay off debt.
- **FCF yield**: free cash flow ÷ market cap — cash actually generated, as a percentage of what you'd pay for the company.
- **DCF (Discounted Cash Flow) intrinsic value**: project a company's future free cash flows and discount them back to today's dollars to estimate what the business is "really" worth, then compare to the current price.

## Technical + AI timing signal

- **MACD**: difference between two moving averages of price; a cross from below zero to above is read as a potential trend-reversal-to-the-upside signal.
- **RSI**: momentum oscillator (0–100) flagging overbought/oversold conditions.
- **ML layer**: not just "MACD crossed zero" in isolation — a model (LSTM or Transformer, TBD) trained on historical price/indicator sequences to classify whether the *current* setup on a cyclical stock historically preceded a real breakout or a false signal ("bull trap"). This is a classification/probability output (e.g. "84% historical success rate"), not a black box buy/sell command — the UI should always show the checklist of what passed, not just the verdict.

## Secondary feature (later phase): news anomaly detector

FRED data lags by design (a month's PMI/CPI is published the following month). Plan for a lightweight scheduled job (every ~6h) that scans financial news headlines (RSS or a free news API) for the target zone, does sentiment + keyword detection for shock events (e.g. bank failure, war, oil shock), and raises a flag *alongside* the FRED-based verdict rather than overriding it — e.g. "FRED data says expansion (based on last month), but today's headlines suggest an energy-market shock." Don't let this feature block Prototype 1.

## Suggested API surface (draft — expect to refine as the frontend solidifies)

```
GET  /zones/{zone}/macro          -> current phase + the 4 raw/derived metrics
GET  /zones/{zone}/sectors        -> sector rotation signals for that zone
GET  /stocks?zone=&sector=        -> fundamentally-filtered stock list
GET  /stocks/{ticker}/technical   -> MACD/RSI + ML breakout probability
GET  /alerts                      -> real-time feed of stocks passing all filters
GET  /strategies                  -> user's saved Studio configs
POST /strategies                  -> create/update a custom strategy
POST /strategies/{id}/backtest    -> historical win-rate / avg return / max drawdown
POST /strategies/{id}/auto-tune   -> ML-adjusted threshold suggestion
```

**Contract-sharing tip**: since frontend and backend are separate repos, generate the OpenAPI schema from FastAPI (`/openapi.json`) and have the frontend codegen its TypeScript types from it, rather than hand-syncing shapes between repos.

## Suggested repo structure

```
backend/
  app/
    main.py
    core/            # settings/config, env loading
    routers/         # FastAPI routers per resource above
    services/
      fred_client.py       # official FRED API wrapper (never scraping)
      macro_engine.py       # phase classification (pure functions, heavily unit-tested)
      sector_engine.py
      fundamentals.py       # ratio calcs + DCF
      technical.py          # MACD/RSI
      ml/
        breakout_model.py   # LSTM/Transformer inference
        backtester.py
        auto_tune.py
    models/          # pydantic schemas + ORM models
    db/              # session, migrations (alembic)
  tests/
  pyproject.toml
```

## Code conventions

- Type-hint everything; pydantic models for all request/response shapes.
- Business-logic functions (phase classification, Z-score, sector cross-reference) should be pure and unit-tested against fixed inputs — these are the functions most likely to get tuned later, so tests are the safety net.
- Secrets (`FRED_API_KEY`, DB credentials) via environment variables only, never committed.
- Run formatting/lint before considering a change done: `ruff check .` and `black .` (or whatever the repo settles on — confirm on first setup).

## Build order / current priority

1. Macro screening engine + `/zones/{zone}/macro` endpoint (Prototype 1) — this unblocks the frontend's main dashboard.
2. Sector rotation cross-reference.
3. Fundamental filter + DCF.
4. Technical signal + ML breakout model.
5. Alerts feed + Studio (custom strategy) persistence.
6. News anomaly detector (nice-to-have, not blocking).

## Open questions / not yet decided

- Job scheduler (APScheduler vs Celery+Redis) — depends on expected data volume/concurrency.
- ML framework (scikit-learn only vs adding PyTorch) — depends on how soon the LSTM/Transformer work starts.
- Hosting/deployment target.
- Auth model — Studio strategies are per-user and persisted "locally and on the server," which implies user accounts; not yet designed.
- China yield-curve proxy — no clean FRED equivalent identified yet.
