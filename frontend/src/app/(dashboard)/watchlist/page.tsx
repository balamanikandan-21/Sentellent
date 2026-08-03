"use client"

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { tickerApi, ingestionApi } from "@/services/api"
import Link from "next/link"
import {
  TrendingUp,
  RefreshCw,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Clock,
  Minus,
  Building2,
  Search,
  MessageSquare,
} from "lucide-react"
import { CardSkeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"

export default function WatchlistPage() {
  const queryClient = useQueryClient()

  const { data: followed, isLoading } = useQuery({
    queryKey: ["tickers", "followed"],
    queryFn: async () => (await tickerApi.getFollowed()).data,
  })

  const { data: jobs } = useQuery({
    queryKey: ["ingestion", "jobs"],
    queryFn: async () => (await ingestionApi.jobs()).data,
    refetchInterval: 5000,
  })

  const unfollowMutation = useMutation({
    mutationFn: (symbol: string) => tickerApi.unfollow(symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickers"] })
    },
  })

  const reingestMutation = useMutation({
    mutationFn: (symbol: string) => ingestionApi.trigger(symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ingestion"] })
    },
  })

  const getJob = (symbol: string) =>
    jobs?.find((j) => j.ticker_symbol === symbol)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Watchlist</h1>
          <p className="text-muted-foreground mt-1">
            Stocks you&apos;re following — ingested for AI analysis
          </p>
        </div>
        <Link
          href="/search"
          className="inline-flex items-center gap-2 rounded-md border px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors"
        >
          <Search className="h-3.5 w-3.5" />
          Add stocks
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : !followed || followed.length === 0 ? (
        <EmptyState
          icon={TrendingUp}
          title="Your watchlist is empty"
          description="Follow stocks from the search page to add them here. Followed stocks are automatically ingested so you can chat about them."
          action={
            <Link
              href="/search"
              className="inline-flex items-center gap-1 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Search stocks
            </Link>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {followed.map((ticker) => {
            const job = getJob(ticker.symbol)
            return (
              <div
                key={ticker.symbol}
                className="rounded-lg border bg-card p-4 space-y-3 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-base font-semibold">{ticker.symbol}</div>
                    <div className="text-sm text-muted-foreground truncate">
                      {ticker.company_name}
                    </div>
                  </div>
                  <button
                    onClick={() => unfollowMutation.mutate(ticker.symbol)}
                    disabled={unfollowMutation.isPending}
                    className="shrink-0 flex items-center gap-1 rounded-md bg-destructive/10 px-2 py-1 text-xs font-medium text-destructive hover:bg-destructive/20 transition-colors"
                  >
                    <Minus className="h-3 w-3" /> Unfollow
                  </button>
                </div>

                <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
                  <span className="rounded bg-muted px-1.5 py-0.5">{ticker.exchange}</span>
                  {ticker.sector && (
                    <span className="inline-flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      {ticker.sector}
                    </span>
                  )}
                  {ticker.industry && (
                    <span className="hidden sm:inline truncate">{ticker.industry}</span>
                  )}
                </div>

                {ticker.market_cap && (
                  <div className="text-xs text-muted-foreground">
                    Market Cap:{" "}
                    <span className="font-medium text-foreground">
                      {formatMarketCap(ticker.market_cap)}
                    </span>
                  </div>
                )}

                <div className="flex items-center justify-between border-t pt-2.5 gap-2">
                  <JobStatus job={job} />
                  <div className="flex items-center gap-1">
                    <Link
                      href="/chat"
                      className="flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors"
                      title={`Ask about ${ticker.symbol}`}
                    >
                      <MessageSquare className="h-3 w-3" />
                      Ask
                    </Link>
                    <button
                      onClick={() => reingestMutation.mutate(ticker.symbol)}
                      disabled={
                        reingestMutation.isPending || job?.status === "running"
                      }
                      className="flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
                    >
                      <RefreshCw
                        className={`h-3 w-3 ${job?.status === "running" ? "animate-spin" : ""}`}
                      />
                      Refresh
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function JobStatus({ job }: { job?: ReturnType<typeof Array.prototype.find> }) {
  if (!job) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" /> Pending
      </span>
    )
  }
  const j = job as { status: string; articles_processed: number; error_message: string | null; completed_at: string | null }

  switch (j.status) {
    case "running":
      return (
        <span className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
          <Loader2 className="h-3 w-3 animate-spin" /> Ingesting...
        </span>
      )
    case "completed":
      return (
        <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" />
          <span>{j.articles_processed} articles</span>
          {j.completed_at && (
            <span className="text-muted-foreground ml-1">
              {new Date(j.completed_at).toLocaleDateString()}
            </span>
          )}
        </div>
      )
    case "failed":
      return (
        <span
          className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400"
          title={j.error_message ?? ""}
        >
          <AlertCircle className="h-3 w-3" /> Failed
        </span>
      )
    default:
      return (
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" /> {j.status}
        </span>
      )
  }
}

function formatMarketCap(value: number): string {
  if (value >= 1e12) return `Rs. ${(value / 1e12).toFixed(1)} L Cr`
  if (value >= 1e7) return `Rs. ${(value / 1e7).toFixed(0)} Cr`
  if (value >= 1e5) return `Rs. ${(value / 1e5).toFixed(0)} L`
  return `Rs. ${value.toLocaleString("en-IN")}`
}
