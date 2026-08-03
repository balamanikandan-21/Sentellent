# START HERE

Fastest path from a fresh clone to a running app, and from there to the live AWS submission.
Deep dives live in [README.md](README.md) and [docs/](docs/) — this file is just the order of operations.

## 0. What this is

Sentellent Hiring Challenge — **Contextual Agentic AI Indian Stock Analyst** (RAG).
Log in with Google → follow NSE tickers → the app ingests fundamentals + Indian news into pgvector → chat with a LangGraph agent that answers with **cited sources, in INR**, refuses when data is missing, learns your investor persona, and produces 9-factor BUY/HOLD/SELL scorecards.

**Deadline: Wed, Aug 5th, 11:59 PM — submitting by Aug 3 earns the speed bonus.**

## 1. Prerequisites

| Tool | Needed for |
|---|---|
| Docker Desktop | local run |
| Python 3.11+ / Node 20+ | dev servers & tests (optional if Docker-only) |
| Anthropic + OpenAI API keys | LLM + embeddings |
| Google Cloud project | OAuth login |
| AWS account + Terraform ≥ 1.5 | deployment |

## 2. Google OAuth (10 minutes, do this first)

1. GCP Console → APIs & Services → **OAuth consent screen** → External.
2. **Test users — add these (challenge requirement):**
   - `harisankar@sentellent.com`
   - `naga@sentellent.com`
   - your own Gmail
3. **Credentials → Create OAuth client ID → Web application**, redirect URI:
   `http://localhost:8000/api/v1/auth/google/callback`
4. Keep the Client ID + Secret for the next step.

## 3. Run locally

```bash
cp .env.example .env    # paste your keys + OAuth credentials
docker compose up --build
```

Then apply DB migrations (one time):

```bash
docker compose exec backend alembic upgrade head
```

Open **http://localhost:3000** → Sign in with Google → follow `RELIANCE` or `TCS` → wait for the ingestion badge to complete → open Chat and try:

- *"What's the sentiment on TCS this week?"* → cited answer in INR
- *"I'm a conservative, dividend-focused investor who avoids high-debt companies."* → persona saved
- *"Recommend stocks for my profile."* → personalized picks + scorecard

Hot-reload dev setup instead of Docker: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## 4. Run the tests

```bash
cd backend && pip install -e .[dev] && pytest -q     # 39 tests, no DB/LLM needed
cd frontend && npm ci && npm run build               # type-check + lint + prod build
```

## 5. Deploy to AWS

Follow [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) top to bottom. Compressed version:

```bash
make tf-bootstrap                        # one-time state bucket
cd infra && terraform init && terraform apply
# populate 3 secrets (anthropic / openai / google-oauth) — commands in the guide
terraform output app_url                 # your HTTPS CloudFront URL
```

Then:
1. Add `https://<app_url>/api/v1/auth/google/callback` as a redirect URI in GCP.
2. Set GitHub secret `AWS_DEPLOY_ROLE_ARN` = `terraform output github_actions_role_arn`.
3. Push to `main` → GitHub Actions builds, deploys, migrates, smoke-tests automatically.

## 6. Submit

Walk through [docs/PRODUCTION_CHECKLIST.md](docs/PRODUCTION_CHECKLIST.md) → take screenshots (ECS services, RDS, CloudWatch dashboard, green pipeline) → submit at **forms.gle/qWxabTxLjEkJ2LcEA**.

## Where things live

```
backend/    FastAPI + LangGraph agent + RAG + memory + 9-factor engine + tests
frontend/   Next.js 15 app (chat, dashboard, watchlist, search, profile, settings)
infra/      Terraform: VPC, ECS Fargate, RDS+pgvector, Redis, ALB, CloudFront, Scheduler
.github/    CI (lint/test/build) + CD (ECR → ECS → migrations → smoke tests)
docs/       ARCHITECTURE · API · DEPLOYMENT · DEVELOPMENT · PRODUCTION_CHECKLIST
```

Current project status + audit history for future work sessions: [PROJECT_STATE.md](PROJECT_STATE.md)
