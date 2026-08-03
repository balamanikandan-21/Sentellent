"use client"

import { useQuery } from "@tanstack/react-query"
import { tickerApi, chatApi, ingestionApi } from "@/services/api"
import { useAuth } from "@/hooks/use-auth"
import Link from "next/link"
import {
  TrendingUp,
  MessageSquare,
  BarChart3,
  Clock,
  Eye,
  Activity,
  Loader2,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import { DashboardSkeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"

export default function DashboardPage() {
  const { user } = useAuth()

  const { data: followed, isLoading: loadingTickers } = useQuery({
    queryKey: ["tickers", "followed"],
    queryFn: async () => (await tickerApi.getFollowed()).data,
  })

  const { data: sessions, isLoading: loadingSessions } = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: async () => (await chatApi.listSessions()).data,
  })

  const { data: jobs, isLoading: loadingJobs } = useQuery({
    queryKey: ["ingestion", "jobs"],
    queryFn: async () => (await ingestionApi.jobs()).data,
  })

  const isLoading = loadingTickers || loadingSessions || loadingJobs

  if (isLoading) return <DashboardSkeleton />

  const completedJobs = jobs?.filter((j) => j.status === "completed") ?? []
  const failedJobs = jobs?.filter((j) => j.status === "failed") ?? []
  const totalArticles = completedJobs.reduce((sum, j) => sum + j.articles_processed, 0)

  const stats = [
    {
      label: "Stocks Followed",
      value: followed?.length ?? 0,
      icon: Eye,
      color: "text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20",
    },
    {
      label: "Chat Sessions",
      value: sessions?.length ?? 0,
      icon: MessageSquare,
      color: "text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/20",
    },
    {
      label: "Articles Ingested",
      value: totalArticles,
      icon: BarChart3,
      color: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20",
    },
    {
      label: "Ingestion Jobs",
      value: completedJobs.length,
      icon: Activity,
      color: "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20",
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          {user ? `Welcome, ${user.name.split(" ")[0]}` : "Dashboard"}
        </h1>
        <p className="text-muted-foreground mt-1">
          Your stock research overview
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="rounded-lg border bg-card p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{stat.label}</span>
              <div className={`w-8 h-8 rounded-md flex items-center justify-center ${stat.color}`}>
                <stat.icon className="h-4 w-4" />
              </div>
            </div>
            <div className="mt-2 text-2xl font-bold">{stat.value}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-card">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h2 className="text-sm font-semibold">Watchlist</h2>
            <Link
              href="/watchlist"
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {!followed || followed.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No stocks followed"
              description="Follow stocks to start tracking them."
              action={
                <Link
                  href="/search"
                  className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                >
                  Search stocks
                </Link>
              }
            />
          ) : (
            <div className="divide-y">
              {followed.slice(0, 5).map((ticker) => {
                const job = jobs?.find((j) => j.ticker_symbol === ticker.symbol)
                return (
                  <div key={ticker.symbol} className="flex items-center justify-between px-4 py-3">
                    <div className="min-w-0">
                      <div className="font-medium text-sm">{ticker.symbol}</div>
                      <div className="text-xs text-muted-foreground truncate">
                        {ticker.company_name}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {ticker.sector && (
                        <span className="hidden sm:inline text-xs text-muted-foreground rounded bg-muted px-1.5 py-0.5">
                          {ticker.sector}
                        </span>
                      )}
                      {job?.status === "completed" ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      ) : job?.status === "failed" ? (
                        <AlertCircle className="h-3.5 w-3.5 text-red-500" />
                      ) : job?.status === "running" ? (
                        <Loader2 className="h-3.5 w-3.5 animate-spin text-blue-500" />
                      ) : (
                        <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="rounded-lg border bg-card">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h2 className="text-sm font-semibold">Recent Chats</h2>
            <Link
              href="/chat"
              className="text-xs text-primary hover:underline flex items-center gap-1"
            >
              Open chat <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          {!sessions || sessions.length === 0 ? (
            <EmptyState
              icon={MessageSquare}
              title="No conversations"
              description="Start a chat to research stocks."
              action={
                <Link
                  href="/chat"
                  className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90"
                >
                  New chat
                </Link>
              }
            />
          ) : (
            <div className="divide-y">
              {sessions.slice(0, 5).map((session) => (
                <Link
                  key={session.id}
                  href="/chat"
                  className="flex items-center justify-between px-4 py-3 hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                    <span className="text-sm truncate">
                      {session.title || "Untitled conversation"}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground shrink-0 ml-2">
                    {new Date(session.updated_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {failedJobs.length > 0 && (
        <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/10 p-4">
          <div className="flex items-center gap-2 text-sm font-medium text-red-700 dark:text-red-400">
            <AlertCircle className="h-4 w-4" />
            {failedJobs.length} ingestion job{failedJobs.length > 1 ? "s" : ""} failed
          </div>
          <p className="mt-1 text-xs text-red-600/80 dark:text-red-400/80">
            Check the search page to retry ingestion for affected tickers.
          </p>
        </div>
      )}
    </div>
  )
}
