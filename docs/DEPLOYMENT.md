# Deployment Guide (AWS + Terraform + GitHub Actions)

## Prerequisites

- AWS account with admin credentials configured (`aws configure`), region **ap-south-1**
- Terraform ≥ 1.5, Docker, GitHub repository with this code
- Google Cloud project (OAuth only), Anthropic + OpenAI API keys

## 1. Google OAuth setup (GCP Console)

1. **APIs & Services → OAuth consent screen**: External, app name "Sentellent Stock Analyst".
2. > **CRITICAL (challenge requirement):** under **Test users**, add
   > `harisankar@sentellent.com` and `naga@sentellent.com`
   > so the reviewers can log in without app verification. Add your own email too.
3. **Credentials → Create OAuth client ID → Web application**:
   - Authorized redirect URI (local): `http://localhost:8000/api/v1/auth/google/callback`
   - The production URI is added in step 5 after CloudFront exists.
4. Note the **Client ID** and **Client Secret**.

## 2. Bootstrap Terraform state (one time)

```bash
cd infra/bootstrap
terraform init && terraform apply     # S3 state bucket + DynamoDB lock table
```

## 3. Provision infrastructure

```bash
cd infra
terraform init
terraform plan -out=tfplan            # review: VPC, ECS, RDS, Redis, ALB, CloudFront, ECR, IAM, Secrets, Scheduler
terraform apply tfplan                # ~15–20 min (RDS + CloudFront are slow)
terraform output                      # note app_url, ecr URLs, github_actions_role_arn
```

If your GitHub repo is not `balamanikandan231/sentellent`, set it first:
`terraform apply -var="github_repo=<owner>/<repo>"`.

## 4. Populate secrets

Terraform creates the secrets; fill in the values (DB URL + JWT are auto-generated):

```bash
aws secretsmanager put-secret-value --secret-id sentellent-production/anthropic-api-key --secret-string "sk-ant-..."
aws secretsmanager put-secret-value --secret-id sentellent-production/openai-api-key   --secret-string "sk-..."
aws secretsmanager put-secret-value --secret-id sentellent-production/google-oauth \
  --secret-string '{"client_id":"<CLIENT_ID>","client_secret":"<CLIENT_SECRET>"}'
```

## 5. Finish OAuth wiring

```bash
terraform output app_url    # e.g. https://d1234abcd.cloudfront.net
```

In GCP Console add the production redirect URI:
`https://<cloudfront-domain>/api/v1/auth/google/callback`
(Google requires HTTPS — that is exactly why CloudFront fronts the ALB.)

## 6. Wire up CI/CD

GitHub repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | `terraform output github_actions_role_arn` |

Push to `main`. The pipeline (`.github/workflows/deploy.yml`):

1. **Build & push** backend image → ECR (tagged `latest` + commit SHA)
2. **Rolling deploy** backend to ECS (waits for service stability, 10 min cap)
3. **Migrations** — one-off Fargate task runs `alembic upgrade head`, fails the pipeline on non-zero exit
4. **Build & push + deploy** frontend (API_URL baked as build arg)
5. **Smoke tests** — polls `/health` until 200, checks frontend 200 and API 401-for-unauthenticated

First deploy note: ECS services start with the `:latest` image reference before any image exists — the first pipeline run populates ECR and the services become healthy.

## Health checks & rollback

| Layer | Mechanism |
|---|---|
| Container | Docker `HEALTHCHECK` — backend `curl /health` (verifies DB), frontend `wget /` |
| Load balancer | Target-group checks: `/health` (backend), `/` (frontend), 2 healthy / 3 unhealthy thresholds |
| Deployment | **ECS deployment circuit breaker with automatic rollback** — if new tasks fail health checks, ECS reverts to the previous task definition without manual action |
| Pipeline | `wait-for-service-stability` + smoke tests fail the workflow visibly |
| Manual rollback | `aws ecs update-service --cluster sentellent-production-cluster --service sentellent-production-backend --task-definition sentellent-production-backend:<PREVIOUS_REV> --force-new-deployment` — or `git revert` + push (images are SHA-tagged) |

## Monitoring

- **CloudWatch dashboard** `sentellent-production-dashboard`: ECS CPU/memory, ALB requests + 4xx/5xx + latency, RDS CPU/connections/storage — screenshot this for the submission.
- **Alarms**: backend CPU>80%, memory>80%, ALB 5xx>10/5min, latency>5s, RDS CPU>80%, storage<2GB.
- **Logs**: `/ecs/sentellent-production/backend` and `/frontend` (14-day retention, structlog JSON).

## Scheduled refresh

EventBridge Scheduler `sentellent-production-news-refresh` runs nightly at 02:00 IST: a one-off Fargate task executes `python -m app.jobs.refresh`, re-ingesting news + fundamentals for every followed ticker. Safe by design — ingestion is idempotent and per-ticker advisory locks skip anything already running.

## Costs (approx, ap-south-1)

The stack is deliberately cost-optimized for a demo/evaluation deployment:

| Component | Cost | Note |
|---|---|---|
| RDS db.t3.micro | ~$15/mo | Free-tier eligible for 12 months on new accounts |
| 2× small Fargate tasks | ~$25/mo | 0.25–0.5 vCPU each |
| ALB | ~$20/mo | Partially free-tier eligible |
| CloudFront | ~$0 | Pay-per-request; negligible at demo traffic |
| Secrets Manager | ~$2/mo | 5 secrets |
| **Total** | **~$60/mo** | ≈ $2/day |

**Deliberately omitted to save cost:**
- **NAT Gateway** (~$32/mo, never free-tier) — ECS tasks run in public subnets with public IPs instead. Inbound is still restricted to the ALB security group; RDS stays private.
- **ElastiCache** (~$12/mo) — Redis is registered as an injectable dependency but no route uses it, and the client connects lazily, so its absence is a no-op.

New AWS accounts can earn up to $100 in credits via the Console's "Explore AWS" activities, which covers this comfortably.

> **Tear down when evaluation is finished:** `cd infra && terraform destroy`. Set an AWS Budgets alert first — it takes two minutes and is itself one of the credit-earning activities.

## Submission checklist (challenge)

- [ ] GCP test users added: `harisankar@sentellent.com`, `naga@sentellent.com`
- [ ] Live URL = `terraform output app_url`, login works end-to-end
- [ ] Screenshots: ECS services running, RDS instance, CloudWatch dashboard, GitHub Actions green pipeline
- [ ] GitHub repo contains frontend + backend + infra
- [ ] Submit at forms.gle/qWxabTxLjEkJ2LcEA **2 days early for the speed bonus**
