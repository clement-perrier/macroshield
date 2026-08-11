# MacroShield

MacroShield automates a full trading research pipeline — macro screening,
sector rotation, fundamental filtering, and a technical/AI timing signal —
behind a single dashboard.

This is a monorepo combining two previously separate projects:

- [`backend/`](./backend) — Python 3.11+ / FastAPI service (data ingestion,
  rules engine, ML layer, public API).
- [`frontend/`](./frontend) — Next.js (App Router) / TypeScript / React web
  app.

Each has its own `CLAUDE.md` with project-specific context; see
[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for how they fit together.

## Getting started

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```

Requires a `.env` file (see `.env.example`) with `FRED_API_KEY` and any other
secrets — never commit these.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Requires a `.env.local`
with `NEXT_PUBLIC_API_BASE_URL` pointing at the backend (defaults to
`http://localhost:8000`).
