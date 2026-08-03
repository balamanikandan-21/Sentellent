# API Reference

Base URL: `/api/v1` · All endpoints (except auth redirects and `/health`) require the `access_token` httpOnly cookie set by the OAuth flow.

Interactive docs (development only): `GET /api/docs` (Swagger UI).

## Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` (root, no prefix) | `{"status": "ok"\|"degraded", "database": "connected"\|"disconnected"}` — used by ALB target group + container health checks |

## Auth (`/auth`)

| Method | Path | Description |
|---|---|---|
| GET | `/auth/google/login` | Redirects to Google consent screen. Sets a CSRF `oauth_state` cookie. |
| GET | `/auth/google/callback?code=&state=` | Verifies `state`, exchanges the code, upserts the user, sets `access_token` (15 min) + `refresh_token` (7 d, rotated) cookies, redirects to `{FRONTEND_URL}/callback`. |
| POST | `/auth/refresh` | Rotates the refresh token, issues a new access token. 401 if revoked/expired. |
| POST | `/auth/logout` | Revokes the refresh token, clears both cookies. |
| GET | `/auth/me` | Current user profile: `{id, email, name, picture, role, created_at}`. |

Cookie security: `httpOnly`, `SameSite=Lax`, `Secure` in production; refresh token scoped to `/api/v1/auth`; tokens stored server-side as SHA-256 hashes with revocation.

## Tickers (`/tickers`)

| Method | Path | Description |
|---|---|---|
| GET | `/tickers?q=RELIANCE` | Search NSE tickers (symbol / company-name match). |
| GET | `/tickers/followed` | Tickers followed by the current user. |
| POST | `/tickers/{symbol}/follow` | Follow a ticker. Triggers background ingestion (fundamentals + news → chunks → embeddings). Returns follow + ingestion status. |
| DELETE | `/tickers/{symbol}/follow` | Unfollow. |
| GET | `/tickers/{symbol}` | Ticker detail incl. cached fundamentals (INR-formatted). |

## Ingestion (`/ingestion`)

| Method | Path | Description |
|---|---|---|
| POST | `/ingestion/trigger` | `{"symbol": "TCS"}` — manually (re-)ingest a ticker. Idempotent; returns `already_running`/`locked` when applicable. |
| GET | `/ingestion/status/{symbol}` | Live status of the in-process ingestion task. |
| GET | `/ingestion/jobs` | Recent ingestion jobs with status, article counts, errors. |

## Chat (`/chat`)

| Method | Path | Description |
|---|---|---|
| GET | `/chat/sessions` | List the user's chat sessions. |
| POST | `/chat/sessions` | Create a session. |
| DELETE | `/chat/sessions/{id}` | Delete a session (and its messages). |
| GET | `/chat/sessions/{id}/messages` | Message history with stored citations. |
| POST | `/chat/sessions/{id}/messages` | **SSE stream** — send `{"content": "..."}`, receive `text/event-stream`. |

### SSE event protocol

Each event is a `data: {json}\n\n` frame:

| `type` | Payload | Notes |
|---|---|---|
| `start` | — | Stream opened |
| `content` | `content: string` | The full markdown answer |
| `citations` | `citations: [{index, title, url, source, published_at, snippet, relevance}]` | Every factual claim maps to `[Source N]` |
| `metadata` | `confidence: float, retrieval_method, sources_count` | Retrieval confidence 0–1 (threshold 0.35) |
| `scorecard` | `scorecard: {ticker, composite_score, action, confidence, data_coverage, factors[9]}` | Only for recommendation queries |
| `done` | — | Stream complete |
| `error` | `error: string` | Generic message; details stay server-side |

### Recommendation scorecard shape

```json
{
  "ticker": "TCS",
  "composite_score": 0.68,
  "action": "BUY",
  "confidence": "high",
  "data_coverage": 0.89,
  "factors": [
    {
      "name": "fundamentals",
      "score": 0.72,
      "weight": 0.2,
      "weighted_score": 0.14,
      "data_available": true,
      "reasoning": "P/E 24.1 (elevated vs Nifty median ~22); ROE 46.9% (strong); ...",
      "sources": ["Fundamentals"]
    }
  ]
}
```

Action thresholds: composite ≥ 0.65 → BUY, ≤ 0.35 → SELL, else HOLD. Factors without data are excluded from the weighted average and flagged `data_available: false`.

## Error format

```json
{ "detail": "Human-readable message" }
```

`401` missing/invalid token · `403` role not authorized · `404` resource not found · `422` validation error · `500` generic (details logged, never leaked).
