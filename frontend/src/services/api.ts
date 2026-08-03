import { api } from "@/lib/axios"
import type {
  User,
  Ticker,
  FollowResponse,
  IngestionStatus,
  IngestionJob,
  ChatSession,
  ChatMessage,
} from "@/types"

export const authApi = {
  getMe: () => api.get<User>("/auth/me"),
  logout: () => api.post("/auth/logout"),
  refresh: () => api.post("/auth/refresh"),
}

export const tickerApi = {
  list: (q?: string) => api.get<Ticker[]>("/tickers", { params: q ? { q } : undefined }),
  getFollowed: () => api.get<Ticker[]>("/tickers/followed"),
  follow: (symbol: string) => api.post<FollowResponse>(`/tickers/${symbol}/follow`),
  unfollow: (symbol: string) => api.delete(`/tickers/${symbol}/follow`),
  get: (symbol: string) => api.get<Ticker>(`/tickers/${symbol}`),
}

export const ingestionApi = {
  trigger: (symbol: string) =>
    api.post<IngestionStatus>("/ingestion/trigger", { symbol }),
  status: (symbol: string) =>
    api.get<IngestionStatus>(`/ingestion/status/${symbol}`),
  jobs: (symbol?: string) =>
    api.get<IngestionJob[]>("/ingestion/jobs", { params: symbol ? { symbol } : undefined }),
}

export const chatApi = {
  listSessions: () => api.get<ChatSession[]>("/chat/sessions"),
  createSession: () => api.post<ChatSession>("/chat/sessions"),
  getMessages: (sessionId: string) =>
    api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`),
  deleteSession: (sessionId: string) =>
    api.delete(`/chat/sessions/${sessionId}`),
  sendMessageSSE: (sessionId: string, content: string) =>
    fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
      credentials: "include",
    }),
}
