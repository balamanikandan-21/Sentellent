# Sentellent Hiring Challenge — Project State

## Project Overview
**Contextual Agentic AI Indian Stock Analyst** — full-stack RAG application: LangGraph agent, FastAPI, Next.js 15, PostgreSQL+pgvector, AWS (Terraform + GitHub Actions CI/CD).

**Role:** Full Stack AI SDE Intern at Sentellent
**Deadline:** Wed, Aug 5th 2026, 11:59 PM (submit by **Aug 3** for the explicit speed bonus)
**Submission:** forms.gle/qWxabTxLjEkJ2LcEA — GitHub repo, live URL, AWS Console + CI/CD screenshots
**Challenge PDF:** `C:\Users\Admin\Downloads\Sentellent_Hiring_Challenge.pdf` (fully parsed; all requirements mapped — see README "Challenge Compliance" table)

## Current Phase
**Phase:** Code complete + production audit done. **ALL implementation phases finished (1–6 + audit).**
**Next:** MANUAL deployment steps only (see "Remaining manual steps" below), then submit.

## What is built (all verified working)

1. **Auth** — Google OAuth 2.0 (+ CSRF `state` cookie verification), JWT httpOnly cookies (15 min), refresh rotation (7 d, SHA-256 server-side, revocation), Next.js middleware route protection.
2. **Ingestion** — yfinance fundamentals (INR formatted) + 4 Indian RSS feeds → full-text enrichment → SHA-256 content-hash + URL dedup → tiktoken chunking (512/64) → OpenAI text-embedding-3-small (1536) → pgvector. Idempotency keys; **per-ticker advisory lock held on a dedicated DB connection** (fixed in audit — see below). Background asyncio tasks + status API.
3. **RAG** — hybrid search (0.7 pgvector cosine + 0.3 ts_rank_cd via CTE), Haiku rerank 25→6, weighted confidence (0.40 avg + 0.25 best + 0.20 quality + 0.15 diversity), gate at 0.35 → "I don't have that in the data".
4. **LangGraph agent** — 10 nodes: router (Haiku classify+tickers), retrieve, memory, persona, analysis/recommend branch, citations, response (INR enforcement), memory_update (every non-greeting turn), sentiment_update. All LLM via langchain-anthropic; Sonnet 5 = `claude-sonnet-5`, Haiku = `claude-haiku-4-5`.
5. **Memory** — user_memories (7 categories, vector 1536, HNSW), extraction each turn, supersedes lifecycle, rank = 0.45 sim + 0.30 conf + 0.25 recency-decay(90d), synced to investor_personas, MemoryProfile injected into prompts.
6. **Recommendation engine** — 9 algorithmic factors (Fundamentals .20, Value .12, Growth .12, Risk .10, Momentum .10, Dividend .10, Quality .10, News Sentiment .08, Persona .08); composite ≥.65 BUY / ≤.35 SELL; `data_available` honesty; Sonnet explains with citations, risks, catalysts; scorecard streamed via SSE + rendered in chat UI; persisted in recommendations.scores JSONB.
7. **Frontend** — 13 routes: landing, login/callback, dashboard, search, watchlist, chat (SSE + markdown + citations + scorecard + confidence shields), profile, settings, 404/error. Responsive, dark mode, skeletons. **Production build passes clean.**
8. **Infra** — backend/frontend multi-stage Dockerfiles (health checks, non-root FE), docker-compose (pgvector:pg16 + redis + both apps), Terraform in `infra/` (17 files): VPC 2-AZ, ECS Fargate (+circuit-breaker rollback, execute-command), RDS pg16+pgvector, ElastiCache, ALB path routing, **CloudFront for HTTPS** (Google OAuth requires https redirect URIs), ECR+lifecycle, Secrets Manager (incl. composed DATABASE_URL), CloudWatch (6 alarms + dashboard), GitHub OIDC role, **EventBridge Scheduler nightly refresh** (02:00 IST → run-task `python -m app.jobs.refresh`), bootstrap state stack.
9. **CI/CD** — ci.yml (ruff, pytest w/ pgvector+redis services, tsc, eslint, docker builds); deploy.yml (OIDC → ECR push SHA+latest → ECS rolling deploy w/ stability wait → **migrations as gated one-off run-task** → smoke tests). Manual rollback = redeploy previous task-def revision.
10. **Tests** — `backend/tests/`: **39 passing unit tests** (scorecard math, 9-factor scorer incl. D/E normalization, confidence, memory ranker, chunker, dedup). Pure logic — no DB/LLM needed (package `__init__`s lazy-import LLM clients for this).
11. **Docs** — README.md (mermaid diagrams, compliance table), docs/{ARCHITECTURE,API,DEPLOYMENT,DEVELOPMENT,PRODUCTION_CHECKLIST}.md.

## Production audit (2026-08-01) — issues found & FIXED

1. **CRITICAL — advisory lock was void**: `pg_try_advisory_xact_lock` on the request session was released by the first `commit()` inside the pipeline. Fixed: `_ticker_lock()` context manager in `app/ingestion/pipeline.py` holds a **session-level** lock on a **dedicated engine connection** for the whole run (auto-release on close/crash); stale `running` job rows are reset under the lock.
2. **OAuth CSRF**: no `state` param → added state cookie + constant-time verification in `app/auth/{service,router}.py`.
3. **SSE error leak**: raw `str(e)` sent to client → generic message (details in logs).
4. **CI broken**: `pip install .[test]` but extra is `dev`; no tests existed (pytest exit 5). Both fixed.
5. **pyproject**: missing `[tool.setuptools.packages.find] include=["app*"]` (flat-layout multi-dir break).
6. **Frontend build blockers**: no `public/` dir (Docker COPY fails) → added robots.txt; no `package-lock.json` (`npm ci` fails) → generated (540 pkgs); no eslint config (`next lint` hangs in CI) → `.eslintrc.json`; 4 `react/no-unescaped-entities` errors failing `next build` → escaped. **Verified: tsc, lint, and full prod build all pass.**
7. **Next.js standalone bakes rewrite URLs at build time** → `API_URL` now a Docker build ARG (compose passes `http://backend:8000`; deploy.yml passes ALB DNS).
8. **Google OAuth needs HTTPS** → added CloudFront distribution (CachingDisabled+AllViewer for app, CachingOptimized for `/_next/static/*`); all app URLs/CORS/redirect-URI use `local.public_url`.
9. **Migration step unrunnable** (ECS exec needs session-manager-plugin absent on GH runners) → one-off `aws ecs run-task` with exit-code gate; `enable_execute_command` + SSM perms added for manual debugging.
10. **DATABASE_URL plaintext in task def** → moved to Secrets Manager secret.
11. **RDS `16.3` pin risk** → `engine_version = "16"` + auto minor upgrades. Dead data block removed from github-oidc.tf; `ecs:RunTask` added to CI role.
12. **Layering**: `format_inr` moved to `app/core/formatting.py` (scorer no longer imports yfinance fetcher).
13. **Gap closed**: scheduled news refresh (challenge Phase 2) — `app/jobs/refresh.py` + `infra/scheduler.tf`.

## Remaining MANUAL steps (user must do — nothing left to code)

1. **GCP Console**: OAuth consent screen → add Test Users **harisankar@sentellent.com** and **naga@sentellent.com** (challenge-critical); create OAuth client; localhost redirect URI for dev.
2. `git init` + push to GitHub (repo must contain frontend+backend; set `github_repo` TF var if name ≠ `balamanikandan231/sentellent`).
3. AWS: `make tf-bootstrap` → `cd infra && terraform init && terraform apply` (~20 min).
4. Populate 3 secrets (anthropic, openai, google-oauth JSON) — exact commands in docs/DEPLOYMENT.md §4.
5. Add production redirect URI in GCP: `https://<terraform output app_url>/api/v1/auth/google/callback`.
6. GitHub secret `AWS_DEPLOY_ROLE_ARN` = `terraform output github_actions_role_arn`; push to main → pipeline deploys.
7. Verify E2E on live URL (walkthrough script in PRODUCTION_CHECKLIST.md), take screenshots (ECS, RDS, CloudWatch dashboard, green Actions), submit form.

**Note:** AWS/GCP hosting is NOT yet provisioned — nothing has been deployed; the steps above are the entire remaining path to "live on the internet".

## Key facts for future sessions

- Local: Windows 11, project at `C:\Users\Admin\OneDrive - vit.ac.in\Desktop\sent`, NOT yet a git repo.
- Backend health endpoint is **`/health`** (root level, no /api/v1 prefix); checks DB.
- Settings: `app/config/settings.py` — refuses prod boot without real secrets. CORS_ORIGINS is a JSON list env var.
- Region ap-south-1; name prefix `sentellent-production`; state bucket `sentellent-terraform-state`.
- Models: PRIMARY `claude-sonnet-5`, TAGGING `claude-haiku-4-5`; embeddings OpenAI text-embedding-3-small.
- Run tests: `cd backend && pytest -q` (39 tests, no services needed). Frontend: `npm run build` passes.
- Deploy order caveat: backend rolls out before migrations run (additive-migration assumption) — documented, acceptable for challenge.
- CloudFront origin_read_timeout 60s — very long agent turns could 504 through CDN; SSE emits `start` immediately, normal turns fine.
