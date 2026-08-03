# Production Checklist

## Security
- [x] OAuth CSRF `state` parameter verified on callback (constant-time compare)
- [x] JWT in httpOnly + SameSite=Lax cookies, `Secure` in production
- [x] Refresh tokens: server-side SHA-256 hashes, rotation on use, revocation on logout
- [x] All secrets in AWS Secrets Manager (API keys, OAuth, JWT, full DATABASE_URL) — no plaintext in task definitions, code, or git
- [x] RDS + Redis in private subnets; security groups chained ALB → ECS → data stores
- [x] CI → AWS via GitHub OIDC (no stored AWS keys); IAM roles least-privilege
- [x] SSE/API errors return generic messages; stack traces only in CloudWatch
- [x] Production settings validator refuses to boot with default/missing secrets
- [ ] (Post-challenge) Rate limiting on chat + ingestion endpoints
- [ ] (Post-challenge) WAF on CloudFront

## Reliability
- [x] Health checks at 3 layers: container HEALTHCHECK, ALB target groups, ECS circuit breaker
- [x] **Automatic rollback**: ECS deployment circuit breaker reverts failed deploys
- [x] Migrations run as a gated one-off task; non-zero exit fails the pipeline
- [x] Post-deploy smoke tests (backend /health with retry, frontend 200, API auth behavior)
- [x] Ingestion idempotent + advisory-locked (safe under concurrent scheduled/manual runs)
- [x] DB pool: pre-ping, recycle 1800s; RDS 7-day backups, storage autoscaling 20→100GB
- [x] Images SHA-tagged in ECR (last 10 kept) — any previous version redeployable

## Observability
- [x] Structured JSON logs (structlog) → CloudWatch, 14-day retention
- [x] Dashboard: ECS CPU/mem, ALB traffic/errors/latency, RDS health
- [x] 6 alarms: backend CPU/mem >80%, ALB 5xx>10/5min, latency>5s, RDS CPU>80%, storage<2GB
- [ ] (Post-challenge) Alarm → SNS/email notifications
- [ ] (Post-challenge) Request tracing (X-Ray/OTel)

## Quality
- [x] 39 unit tests on the algorithmic core (scoring, confidence, ranking, chunking, dedup)
- [x] CI gates: ruff lint + format, pytest with pgvector+redis services, tsc, eslint, prod builds of both Docker images
- [x] Frontend production build clean (13 routes, type-safe)
- [ ] (Post-challenge) Integration tests against a live agent graph with mocked LLMs
- [ ] (Post-challenge) Load test SSE chat under concurrency

## AI correctness (challenge-graded)
- [x] Every claim cited (`[Source N]` → title/URL/date/snippet + relevance score)
- [x] Confidence gate 0.35 → "I don't have that in the data" (no invented numbers)
- [x] All figures INR (Rs. / Lakh / Crore) — enforced at ingestion and response
- [x] Recommendations: action + confidence + reasoning + risks + catalysts + 9-factor scorecard with `data_available` honesty
- [x] Persona learned from chat; memories decay/supersede; scoring is algorithmic, not per-stock LLM calls

## Submission (do these manually)
- [ ] GCP OAuth test users added: **harisankar@sentellent.com**, **naga@sentellent.com**
- [ ] `terraform apply` completed; secrets populated; first pipeline green
- [ ] Production redirect URI added in GCP (CloudFront domain)
- [ ] End-to-end walkthrough on the live URL: login → follow RELIANCE → wait for ingestion → ask sentiment question (check citations + INR) → ask for recommendation (check scorecard) → say "I'm a conservative dividend investor" → re-ask recommendation (check persona applied)
- [ ] Screenshots: AWS Console (ECS services, RDS), CloudWatch dashboard, green GitHub Actions run
- [ ] Push repo; submit form at forms.gle/qWxabTxLjEkJ2LcEA — **aim 2 days early (Aug 3) for the speed bonus**
