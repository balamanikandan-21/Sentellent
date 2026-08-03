# Developer Guide

## Prerequisites

- Python 3.11+, Node 20+, Docker Desktop
- Anthropic + OpenAI API keys; Google OAuth client (localhost redirect)

## Local setup

### Option A — everything in Docker

```bash
cp .env.example .env      # fill in keys
docker compose up --build
docker compose exec backend alembic upgrade head
```

### Option B — hot-reload dev servers (recommended while coding)

```bash
# 1. Infra only
docker compose up -d postgres redis

# 2. Backend
cd backend
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -e .[dev]
copy ..\.env.example .env                          # edit values
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Frontend (second terminal)
cd frontend
npm ci
npm run dev                                        # http://localhost:3000
```

The Next.js dev server proxies `/api/*` to `http://localhost:8000` (see `next.config.ts` rewrites).

## Project layout

```
backend/
  app/
    agent/          LangGraph graph, nodes, prompts, service
    api/v1/         REST + SSE endpoints (chat, tickers, ingestion)
    auth/           Google OAuth, JWT, refresh rotation
    config/         Pydantic settings (all env vars documented here)
    core/           logging, redis, exceptions, formatting
    db/             engine/session factories
    ingestion/      fetchers (yfinance, RSS), processors (chunk/embed/dedup), pipeline
    jobs/           scheduled refresh entrypoint (python -m app.jobs.refresh)
    memory/         extractor, ranker, store, types (long-term memory)
    middleware/     error handler, request logging
    models/         15 SQLAlchemy models
    rag/            chunker, retriever (hybrid), reranker, confidence
    recommendation/ 9-factor scorer, engine, types
    repositories/   data access (BaseRepository[T] + domain repos)
  alembic/versions/ 4 migrations (includes pgvector + HNSW indexes)
  tests/            39 unit tests (pure logic — no DB/LLM required)
frontend/
  src/app/          App Router pages ((auth), (dashboard), landing)
  src/components/   layout, ui (skeleton, markdown, empty-state)
  src/stores/       Zustand (auth, sidebar)
  src/services/     typed API clients
infra/              Terraform (16 files) + bootstrap/
.github/workflows/  ci.yml (lint+test+build), deploy.yml (ECS deploy)
```

## Testing

```bash
cd backend
pytest -q                 # 39 tests, no external services needed
pytest --cov=app          # with coverage
```

Tests cover the algorithmic core: 9-factor scoring, scorecard composite/thresholds, retrieval confidence, memory ranking, chunking, dedup hashing. Package `__init__`s lazy-import LLM clients specifically so this pure logic stays testable without API keys.

Frontend:

```bash
cd frontend
npx tsc --noEmit          # type-check
npx next lint             # eslint
npm run build             # full production build
```

## Database migrations

```bash
cd backend
alembic revision --autogenerate -m "describe_change"   # inspect the generated file!
alembic upgrade head
alembic downgrade -1
```

Vector columns and HNSW indexes are raw SQL in migrations — autogenerate won't produce them; copy the pattern from `0004_long_term_memory.py`.

## Conventions

- **Money**: always INR. Use `app.core.formatting.format_inr` (Rs. / Lakh / Crore).
- **LLM calls**: only via `langchain-anthropic`. Sonnet 5 (`PRIMARY_MODEL`) for reasoning, Haiku 4.5 (`TAGGING_MODEL`) for classification/tagging. Never call an LLM for work a plain function can do (challenge requirement — scoring is pure Python).
- **Grounding**: any new agent output path must carry citations and respect `CONFIDENCE_THRESHOLD` — never emit un-sourced numbers.
- **DB access**: through repositories; commit at the API/service boundary, `flush()` inside.
- **Ingestion**: must stay idempotent — dedup by content hash before embedding; anything touching a ticker's corpus runs under `_ticker_lock(symbol)`.
- **Linting**: `ruff check . && ruff format .` (line length 100). Frontend: eslint `next/core-web-vitals`.
- **Settings**: add new config to `app/config/settings.py` with a sane default; document required prod vars in `.env.example` and Terraform `secrets`/`environment`.

## Common tasks

| Task | Command |
|---|---|
| Ingest a ticker manually | `POST /api/v1/ingestion/trigger {"symbol":"TCS"}` or follow it in the UI |
| Run the nightly refresh locally | `cd backend && python -m app.jobs.refresh` |
| Inspect the vector store | `docker compose exec postgres psql -U postgres sentellent -c "select count(*) from article_chunks;"` |
| Reset local DB | `docker compose down -v && docker compose up -d postgres && alembic upgrade head` |
