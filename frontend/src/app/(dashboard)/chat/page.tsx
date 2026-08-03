"use client"

import { useState, useRef, useEffect, useCallback } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { chatApi } from "@/services/api"
import type { ChatSession, ChatMessage, Citation, RetrievalMetadata, ScorecardData } from "@/types"
import { Markdown } from "@/components/ui/markdown"
import { MessageSkeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import {
  Send,
  Plus,
  Loader2,
  MessageSquare,
  Trash2,
  ExternalLink,
  Bot,
  User,
  Shield,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react"

export default function ChatPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [input, setInput] = useState("")
  const [streaming, setStreaming] = useState(false)
  const [streamedContent, setStreamedContent] = useState("")
  const [streamedCitations, setStreamedCitations] = useState<Citation[]>([])
  const [streamedMetadata, setStreamedMetadata] = useState<RetrievalMetadata | null>(null)
  const [streamedScorecard, setStreamedScorecard] = useState<ScorecardData | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const queryClient = useQueryClient()

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: async () => (await chatApi.listSessions()).data,
  })

  const { data: messages, isLoading: loadingMessages } = useQuery({
    queryKey: ["chat", "messages", activeSessionId],
    queryFn: async () =>
      activeSessionId ? (await chatApi.getMessages(activeSessionId)).data : [],
    enabled: !!activeSessionId,
  })

  const createSessionMutation = useMutation({
    mutationFn: async () => (await chatApi.createSession()).data,
    onSuccess: (session) => {
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] })
      setActiveSessionId(session.id)
    },
  })

  const deleteSessionMutation = useMutation({
    mutationFn: (id: string) => chatApi.deleteSession(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] })
      if (activeSessionId === deletedId) setActiveSessionId(null)
    },
  })

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, streamedContent])

  const handleSend = useCallback(async () => {
    if (!input.trim() || !activeSessionId || streaming) return

    const userMessage = input.trim()
    setInput("")
    setStreaming(true)
    setStreamedContent("")
    setStreamedCitations([])
    setStreamedMetadata(null)
    setStreamedScorecard(null)

    try {
      const response = await chatApi.sendMessageSSE(activeSessionId, userMessage)
      if (!response.body) throw new Error("No response body")

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const data = line.slice(6)
          try {
            const event = JSON.parse(data)
            if (event.type === "content") {
              setStreamedContent(event.content)
            } else if (event.type === "citations") {
              setStreamedCitations(event.citations)
            } else if (event.type === "metadata") {
              setStreamedMetadata({
                confidence: event.confidence,
                retrieval_method: event.retrieval_method,
                sources_count: event.sources_count,
              })
            } else if (event.type === "scorecard") {
              setStreamedScorecard(event.scorecard)
            } else if (event.type === "error") {
              setStreamedContent(`Error: ${event.error}`)
            }
          } catch {
            // skip malformed events
          }
        }
      }
    } catch {
      setStreamedContent("Failed to get response. Please try again.")
    } finally {
      setStreaming(false)
      queryClient.invalidateQueries({ queryKey: ["chat", "messages", activeSessionId] })
      queryClient.invalidateQueries({ queryKey: ["chat", "sessions"] })
    }
  }, [input, activeSessionId, streaming, queryClient])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-full -m-6">
      {/* Sessions Sidebar */}
      <div className="hidden sm:flex w-64 shrink-0 border-r bg-card flex-col">
        <div className="p-3 border-b">
          <button
            onClick={() => createSessionMutation.mutate()}
            disabled={createSessionMutation.isPending}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            {createSessionMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Plus className="h-4 w-4" />
            )}
            New Chat
          </button>
        </div>

        <div className="flex-1 overflow-auto p-2 space-y-1">
          {loadingSessions ? (
            <div className="space-y-2 py-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="animate-pulse rounded-md bg-muted h-9" />
              ))}
            </div>
          ) : !sessions || sessions.length === 0 ? (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-2 rounded-md px-3 py-2 text-sm cursor-pointer transition-colors ${
                  activeSessionId === session.id
                    ? "bg-accent text-accent-foreground"
                    : "hover:bg-muted"
                }`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                <span className="truncate flex-1">
                  {session.title || "New Chat"}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    deleteSessionMutation.mutate(session.id)
                  }}
                  className="opacity-0 group-hover:opacity-100 shrink-0 text-muted-foreground hover:text-destructive transition-opacity"
                  aria-label="Delete session"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Mobile session selector */}
      <div className="sm:hidden flex items-center gap-2 border-b bg-card px-3 py-2 absolute top-0 left-0 right-0 z-10">
        <button
          onClick={() => createSessionMutation.mutate()}
          className="p-1.5 rounded-md bg-primary text-primary-foreground"
        >
          <Plus className="h-4 w-4" />
        </button>
        {sessions && sessions.length > 0 && (
          <select
            value={activeSessionId || ""}
            onChange={(e) => setActiveSessionId(e.target.value || null)}
            className="flex-1 text-sm bg-background border rounded-md px-2 py-1.5"
          >
            <option value="">Select a chat...</option>
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title || "New Chat"}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Chat Area */}
      <div className="flex flex-1 flex-col min-w-0 sm:pt-0 pt-12">
        {!activeSessionId ? (
          <div className="flex-1 flex items-center justify-center px-4">
            <div className="text-center space-y-4 max-w-md">
              <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-8 w-8 text-primary" />
              </div>
              <h2 className="text-xl font-semibold">Sentellent Stock Analyst</h2>
              <p className="text-muted-foreground text-sm">
                Ask about Indian stocks, get sentiment analysis, or request
                buy/hold/sell recommendations. Start a new chat to begin.
              </p>
              <div className="grid gap-2 text-sm text-left">
                {[
                  "What's the latest news on Reliance?",
                  "Should I buy TCS right now?",
                  "What's the market sentiment around INFY?",
                  "I'm a conservative investor looking for dividends",
                ].map((example) => (
                  <button
                    key={example}
                    onClick={() => {
                      createSessionMutation.mutate()
                      setInput(example)
                    }}
                    className="rounded-lg border px-4 py-3 text-left hover:bg-muted transition-colors"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {loadingMessages ? (
                <div className="space-y-6">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <MessageSkeleton key={i} />
                  ))}
                </div>
              ) : (
                <>
                  {messages?.map((msg) => (
                    <ChatBubble key={msg.id} message={msg} />
                  ))}

                  {streaming && streamedContent && (
                    <div className="flex gap-3">
                      <div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0 space-y-2">
                        <Markdown content={streamedContent} />
                        {streamedScorecard && (
                          <ScorecardDisplay scorecard={streamedScorecard} />
                        )}
                        {streamedCitations.length > 0 && (
                          <CitationList citations={streamedCitations} />
                        )}
                        {streamedMetadata && (
                          <ConfidenceBadge metadata={streamedMetadata} />
                        )}
                      </div>
                    </div>
                  )}

                  {streaming && !streamedContent && (
                    <div className="flex gap-3">
                      <div className="shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                        <Bot className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Retrieving and analyzing...
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input */}
            <div className="border-t p-3 sm:p-4">
              <div className="flex items-end gap-2 max-w-3xl mx-auto">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about stocks, sentiment, or recommendations..."
                  rows={1}
                  className="flex-1 resize-none rounded-lg border bg-background px-3 sm:px-4 py-2.5 sm:py-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  style={{ maxHeight: "120px" }}
                  disabled={streaming}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || streaming}
                  className="shrink-0 rounded-lg bg-primary p-2.5 sm:p-3 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {streaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </button>
              </div>
              <p className="text-center text-xs text-muted-foreground mt-2 hidden sm:block">
                All figures in INR. Not financial advice. Always verify with your advisor.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user"

  return (
    <div className="flex gap-3">
      <div
        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? "bg-muted" : "bg-primary/10"
        }`}
      >
        {isUser ? (
          <User className="h-4 w-4 text-muted-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>
      <div className="flex-1 min-w-0 space-y-2">
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        ) : (
          <Markdown content={message.content} />
        )}
        {message.citations && message.citations.length > 0 && (
          <CitationList citations={message.citations} />
        )}
      </div>
    </div>
  )
}

function CitationList({ citations }: { citations: Citation[] }) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">Sources:</p>
      {citations.map((citation, i) => (
        <div
          key={i}
          className="flex items-start gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-xs"
        >
          <span className="shrink-0 font-semibold text-primary mt-0.5 w-5 text-right">
            [{i + 1}]
          </span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-medium leading-tight">{citation.source_title}</span>
              {citation.source_url && (
                <a
                  href={citation.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-primary hover:underline shrink-0"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
            <div className="flex items-center gap-1.5 mt-1 flex-wrap">
              {citation.source_name && (
                <span className="rounded bg-muted px-1.5 py-0.5 text-muted-foreground">
                  {citation.source_name}
                </span>
              )}
              {citation.published_at && (
                <span className="text-muted-foreground">
                  {citation.published_at.slice(0, 10)}
                </span>
              )}
              {citation.relevance_score != null && (
                <span
                  className={`rounded px-1.5 py-0.5 font-mono ${
                    citation.relevance_score >= 0.7
                      ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                      : citation.relevance_score >= 0.4
                        ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
                        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                  }`}
                >
                  {(citation.relevance_score * 100).toFixed(0)}%
                </span>
              )}
            </div>
            {citation.snippet && (
              <p className="text-muted-foreground mt-1 line-clamp-2 leading-relaxed">
                {citation.snippet}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

function ScorecardDisplay({ scorecard }: { scorecard: ScorecardData }) {
  const ActionIcon =
    scorecard.action === "BUY"
      ? TrendingUp
      : scorecard.action === "SELL"
        ? TrendingDown
        : Minus

  const actionColor =
    scorecard.action === "BUY"
      ? "text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
      : scorecard.action === "SELL"
        ? "text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
        : "text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"

  return (
    <div className="rounded-lg border bg-card">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-sm">{scorecard.ticker}</span>
          <span className="text-xs text-muted-foreground hidden sm:inline">
            Multi-Factor Analysis
          </span>
        </div>
        <div
          className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold ${actionColor}`}
        >
          <ActionIcon className="h-3.5 w-3.5" />
          {scorecard.action}
        </div>
      </div>

      <div className="px-4 py-3 grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Composite Score</span>
          <span className="font-mono font-medium">
            {(scorecard.composite_score * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Data Coverage</span>
          <span className="font-mono font-medium">
            {(scorecard.data_coverage * 100).toFixed(0)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Confidence</span>
          <span className="font-medium capitalize">{scorecard.confidence}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Factors</span>
          <span className="font-mono font-medium">
            {scorecard.factors.filter((f) => f.data_available).length}/
            {scorecard.factors.length}
          </span>
        </div>
      </div>

      <div className="px-4 pb-3">
        <div className="space-y-1.5">
          {scorecard.factors.map((factor) => (
            <div key={factor.name} className="group">
              <div className="flex items-center gap-2 text-xs">
                <span className="w-24 sm:w-32 shrink-0 text-muted-foreground capitalize truncate">
                  {factor.name.replace(/_/g, " ")}
                </span>
                <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden">
                  {factor.data_available ? (
                    <div
                      className={`h-full rounded-full transition-all ${
                        factor.score >= 0.65
                          ? "bg-green-500 dark:bg-green-400"
                          : factor.score >= 0.4
                            ? "bg-yellow-500 dark:bg-yellow-400"
                            : "bg-red-500 dark:bg-red-400"
                      }`}
                      style={{ width: `${factor.score * 100}%` }}
                    />
                  ) : (
                    <div className="h-full w-full bg-muted-foreground/10" />
                  )}
                </div>
                <span className="w-10 text-right font-mono text-muted-foreground">
                  {factor.data_available
                    ? `${(factor.score * 100).toFixed(0)}%`
                    : "N/A"}
                </span>
              </div>
              {factor.data_available && factor.reasoning && (
                <p className="ml-[6.5rem] sm:ml-[8.5rem] text-[10px] text-muted-foreground mt-0.5 hidden group-hover:block leading-relaxed">
                  {factor.reasoning}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ConfidenceBadge({ metadata }: { metadata: RetrievalMetadata }) {
  const { confidence, sources_count } = metadata
  const pct = Math.round(confidence * 100)

  let color: string
  let Icon: typeof Shield

  if (confidence >= 0.7) {
    color = "text-green-600 dark:text-green-400"
    Icon = ShieldCheck
  } else if (confidence >= 0.35) {
    color = "text-yellow-600 dark:text-yellow-400"
    Icon = Shield
  } else {
    color = "text-red-600 dark:text-red-400"
    Icon = ShieldAlert
  }

  return (
    <div className={`flex items-center gap-1.5 text-xs ${color}`}>
      <Icon className="h-3.5 w-3.5" />
      <span>
        Confidence: {pct}% &middot; {sources_count} source
        {sources_count !== 1 ? "s" : ""}
      </span>
    </div>
  )
}
