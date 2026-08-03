export interface User {
  id: string
  email: string
  name: string
  picture: string | null
  created_at: string
}

export interface Ticker {
  symbol: string
  company_name: string
  exchange: string
  sector: string | null
  industry: string | null
  market_cap: number | null
}

export interface FollowResponse {
  symbol: string
  followed: boolean
  ingestion_status: string
}

export interface IngestionStatus {
  symbol: string
  status: "idle" | "started" | "running" | "completed" | "failed" | "already_running"
  error: string | null
}

export interface IngestionJob {
  id: string
  idempotency_key: string
  source: string
  ticker_symbol: string | null
  status: string
  articles_processed: number
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface ChatSession {
  id: string
  title: string | null
  created_at: string
  updated_at: string
}

export interface ChatMessage {
  id: string
  session_id: string
  role: "user" | "assistant"
  content: string
  citations: Citation[]
  created_at: string
}

export interface Citation {
  source_title: string
  source_url: string | null
  source_name: string | null
  published_at: string | null
  snippet: string
  relevance_score: number | null
}

export interface RetrievalMetadata {
  confidence: number
  retrieval_method: string
  sources_count: number
}

export interface FactorScoreData {
  name: string
  score: number
  weight: number
  weighted_score: number
  data_available: boolean
  reasoning: string
  sources: string[]
}

export interface ScorecardData {
  ticker: string
  composite_score: number
  action: "BUY" | "HOLD" | "SELL"
  confidence: string
  data_coverage: number
  factors: FactorScoreData[]
}
