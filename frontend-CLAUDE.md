# MacroShield — Frontend

This file is project memory for Claude Code. Read it before writing code in this repo.

## What this app does

MacroShield turns a full trading research pipeline into a no-code web app:

1. **Macro dashboard** — for 3 zones (US, Eurozone/Germany, China), show which economic cycle phase each zone is in: **Recovery, Expansion, Slowdown, Recession**.
2. **Sector rotation** — within the selected zone, show which sectors are green-lit (good macro + cheap), a value trap (good macro but expensive), or a contrarian opportunity (bad macro but a cheap cyclical sector turning up).
3. **Fundamental filter** — stocks ranked by valuation ratios and a DCF-based intrinsic value estimate.
4. **Technical/AI signal** — MACD/RSI plus an ML-derived probability that the current setup is a real breakout vs a false signal.
5. **Alerts** — a live feed of stocks that passed all four filters.

This repo is the **frontend** (Next.js/React web app). The **backend is a separate repo** (Python/FastAPI) — treat its API as an external contract you consume, not something to reshape locally. See "API integration" below for how to keep the two in sync.

## Tech stack

- **Confirmed**: Next.js (App Router), React, TypeScript.
- WHen adding new features, suggests frameworks or any tools that would be more optimized or good practice. E.g: Zustand, Tanstack etc..
- **Assumed defaults** (confirm/override as needed — not locked in):
  - Tailwind CSS for styling.
  - TanStack Query for server-state/data fetching against the backend API.
  - A charting library for the metric cards/sparklines — `recharts` is a reasonable default; swap for `visx`/`lightweight-charts` if we need candlestick-style technical charts later.
  - `shadcn/ui` or Radix primitives for the accordion (Studio tab) and other interactive components.
  - Local UI state via `useState`; only reach for a state library (Zustand etc.) if cross-page state actually needs it.

## App structure — 3 tabs

**Tab 1 — Macro Dashboard.** The "weather report" for the market: zone selector + verdict card + 4-metric grid. This is the highest-priority screen to build first (mirrors backend Prototype 1).

**Tab 2 — Studio.** Where the user builds a custom strategy: a vertical accordion checklist (Macro filter → Sector valuation threshold → Fundamental health criteria → Technical signal), ending in an "Activate Strategy" action that saves to the backend.

**Tab 3 — Alerts.** A real-time, vertical feed of stocks that just passed all four filters, each showing which specific checks it passed.

## Design system

The product brief already pins down a specific visual direction — **follow it exactly rather than defaulting to a generic AI-app look** (this happens to overlap with a common "dark mode + single bright accent" template, but here it's a deliberate spec, not a fallback, so match it precisely):

- **Background**: pure black `#000000`. Title "Global Macro Shield" in white.
- **Zone tab bar**: horizontal, rounded, 3 buttons — US / EU / CN. Active tab: electric blue with a subtle background blur. Inactive tabs: greyed out.
- **Verdict card** (~30% of viewport height, the dashboard's focal point) — color, icon, and copy change with the zone's classified phase:
  - **Phase 1 (Recovery)**: soft emerald green, rocket icon, headline "Early Cycle: Active Industrial Expansion," subtext "Recommended strategy: Cyclicals & Tech."
  - **Phase 2 (Expansion)**: _not specified in the original brief_ — needs a color/icon decision before this state can ship. My instinct: a warmer/bolder variant in the same green-to-red spectrum (e.g. a golden-amber-yet-positive tone) so the 4 phases read as a clear progression, but confirm with the business-logic owner before locking it in.
  - **Phase 3 (Slowdown)**: amber/orange, shield icon, headline "Stagflation / Braking," subtext "Recommended strategy: Defensive sectors only."
  - **Phase 4 (Recession)**: brick red, exclamation icon, headline "Bear Market / Crisis," subtext "Recommended strategy: Cash, Bonds, or Short."
- **Metric grid** (2×2, just below the verdict card):
  - PMI proxy card: big value (e.g. `52.4`), small green ">50 ↑" tag when expansionary.
  - Inflation card (CPI MoM): value (e.g. `+0.4%`), a colored dot driven by the backend's Z-score classification (red = overheating, grey = stagnant).
  - Central bank rate card: raw rate (e.g. `4.50%`) plus a plain-text recent-history line (e.g. "Stable for 2 meetings").
  - Yield curve card: spread (e.g. `-0.18%`); if negative, render a blinking red border with an "INVERTED" label — this one has a real alert state, not just a static tag.
- **Sector badges**: horizontal row of GICS sector badges under the verdict, unlocked based on the zone's verdict. Clicking a badge is meant to drill into that sector's stock list (planned for a later version).
- **Studio accordion**: 4 collapsible steps, each configuring one stage of the funnel; ends in a single "Activate Strategy" call-to-action.
- **Alerts feed cards**: black background, green left border/glow for a fresh buy signal, ticker name/exchange as the headline, and a 4-line checklist underneath (Macro ✓ / Sector ✓ / Fundamental ✓ / Technical ✓) showing exactly why it qualified.

## Copy conventions

The person building this isn't a finance professional and neither are most end users — don't assume familiarity with jargon:

- Every ratio or indicator label (P/E, EV/EBITDA, MACD, Z-score, etc.) should have an inline explainer available (tooltip, subtext, or info icon) rather than assuming the label alone is self-explanatory.
- Error and empty states should say what happened and what to do next, in plain language — not silently render nothing.
- Keep button/action language literal and consistent: whatever a button says it does (e.g. "Activate Strategy"), the resulting confirmation should echo that same word.

## API integration

- The backend is a separate FastAPI service exposing (draft, will evolve): `/zones/{zone}/macro`, `/zones/{zone}/sectors`, `/stocks`, `/stocks/{ticker}/technical`, `/alerts`, `/strategies`.
- **Keep types in sync without hand-copying them**: generate TypeScript types from the backend's OpenAPI schema (`/openapi.json`) rather than manually re-declaring response shapes in this repo — the two repos will drift otherwise.
- **Real-time feed (Tab 3)**: the original concept describes native push notifications, which don't map directly onto a web app. Start with polling (TanStack Query's refetch interval) for the alerts feed; consider Server-Sent Events or WebSockets once the backend supports push, and browser Push API/service worker if we want true background notifications on web.
- Base API URL via an environment variable (e.g. `NEXT_PUBLIC_API_BASE_URL`), never hardcoded.

## Localization

Source material for this product is in French, but no target-market decision has been made yet for the shipped UI language. Default assumption: **build UI copy in English for now, but keep strings externalized** (a simple i18n setup, even if only one locale exists today) so French can be added without a rewrite. Flag to me before hardcoding either language throughout.

## Suggested repo structure

```
frontend/
  app/
    (dashboard)/         # Tab 1
    (studio)/            # Tab 2
    (alerts)/            # Tab 3
    layout.tsx
  components/
    verdict-card/
    metric-grid/
    sector-badges/
    strategy-accordion/
    alert-feed/
  lib/
    api-client.ts        # generated/typed client against the backend OpenAPI schema
  hooks/
  types/
```

## Code conventions

- TypeScript strict mode; no `any` without a comment explaining why.
- ESLint + Prettier (or Biome — confirm on setup); keep them non-negotiable in CI.
- Component tests via React Testing Library; consider Playwright for the Studio flow (multi-step accordion + save) since it's the most stateful screen.
- Server state (API data) lives in TanStack Query; don't duplicate it into local component state.

## Build order / current priority

1. Tab 1 (Macro Dashboard) — depends on the backend's `/zones/{zone}/macro` endpoint landing first.
2. Tab 3 (Alerts feed) — simplest data shape, good second screen.
3. Tab 2 (Studio) — most complex state management (multi-step config + persistence), build last.

## Open questions / not yet decided

- Exact color/icon for the Phase 2 (Expansion) verdict card — not specified in the original brief.
- Charting library choice for any technical (MACD/RSI) visualizations.
- Auth model — Studio strategies are saved per-user, which implies accounts; not yet designed on either side.
- Real-time mechanism for the Alerts tab (polling vs SSE/WebSocket vs web push).
- Target UI language (English vs French vs both).
