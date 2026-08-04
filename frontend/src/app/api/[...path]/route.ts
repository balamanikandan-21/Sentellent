import { type NextRequest } from "next/server"

// Runtime proxy to the FastAPI backend.
//
// This replaces next.config rewrites for the API. Rewrites bake their
// destination in at build time, so changing API_URL required a full rebuild —
// and on Vercel a stale value silently 502s. Reading it per-request keeps the
// backend URL a true runtime setting.
//
// It also lets the SSE chat stream through untouched: the upstream body is
// piped straight to the client, and redirects (the Google OAuth 307) and
// Set-Cookie headers are forwarded rather than followed or swallowed.

export const dynamic = "force-dynamic"
export const maxDuration = 60

// A URL can never contain whitespace, so keep only the first token and drop a
// trailing slash. Guards against stray newlines or pasted text in the env var,
// which otherwise surface as a confusing ENOTFOUND on a mangled hostname.
function normalizeBackendUrl(raw: string | undefined): string {
  const first = (raw ?? "").trim().split(/\s/)[0]
  return (first || "http://localhost:8000").replace(/\/+$/, "")
}

const BACKEND_URL = normalizeBackendUrl(process.env.API_URL)

// Hop-by-hop headers must not be forwarded.
const STRIPPED_REQUEST_HEADERS = new Set([
  "host",
  "connection",
  "content-length",
  "transfer-encoding",
  "accept-encoding",
])

const STRIPPED_RESPONSE_HEADERS = new Set([
  "content-encoding",
  "content-length",
  "transfer-encoding",
  "connection",
])

async function proxy(request: NextRequest): Promise<Response> {
  const url = new URL(request.url)
  const target = `${BACKEND_URL}${url.pathname}${url.search}`

  const headers = new Headers()
  request.headers.forEach((value, key) => {
    if (!STRIPPED_REQUEST_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value)
    }
  })

  const hasBody = request.method !== "GET" && request.method !== "HEAD"

  let upstream: Response
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      // Required by undici whenever a streaming body is sent.
      ...(hasBody ? { duplex: "half" } : {}),
      // Pass 3xx back to the browser (Google OAuth) instead of following it.
      redirect: "manual",
      cache: "no-store",
    } as RequestInit)
  } catch (error) {
    console.error("api_proxy_failed", { target, error })
    return Response.json(
      { detail: "Upstream API is unreachable." },
      { status: 502 },
    )
  }

  const responseHeaders = new Headers()
  upstream.headers.forEach((value, key) => {
    if (!STRIPPED_RESPONSE_HEADERS.has(key.toLowerCase())) {
      responseHeaders.append(key, value)
    }
  })

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  })
}

export const GET = proxy
export const POST = proxy
export const PUT = proxy
export const PATCH = proxy
export const DELETE = proxy
export const HEAD = proxy
export const OPTIONS = proxy
