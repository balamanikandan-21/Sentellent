"use client"

import { useState } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { tickerApi, ingestionApi } from "@/services/api"
import type { Ticker, IngestionJob } from "@/types"
import {
  Search,
  Plus,
  Minus,
  RefreshCw,
  Loader2,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
  Clock,
  Building2,
  ArrowUpDown,
} from "lucide-react"
import { CardSkeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"

export default function SearchPage() {
  const [search, setSearch] = useState("")
  const queryClient = useQueryClient()

  const { data: followed, isLoading: loadingFollowed } = useQuery({
    queryKey: ["tickers", "followed"],
    queryFn: async () => (await tickerApi.getFollowed()).data,
  })

  const { data: searchResults, isFetching: searching } = useQuery({
    queryKey: ["tickers", "search", search],
    queryFn: async () => (await tickerApi.list(search)).data,
    enabled: search.length >= 2,
  })

  const { data: jobs } = useQuery({
    queryKey: ["ingestion", "jobs"],
    queryFn: async () => (await ingestionApi.jobs()).data,
    refetchInterval: 5000,
  })

  const followMutation = useMutation({
    mutationFn: (symbol: string) => tickerApi.follow(symbol),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tickers"] })
      queryClient.invalidateQueries({ queryKey: ["ingestion"] })
    },
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

  const followedSymbols = new Set(followed?.map((t) => t.symbol) ?? [])

  const getJobStatus = (symbol: string): IngestionJob | undefined =>
    jobs?.find((j) => j.ticker_symbol === symbol)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Stock Search</h1>
        <p className="text-muted-foreground mt-1">
          Search NSE-listed companies and follow stocks to start ingesting data
        </p>
      </div>

      <div className="relative max-w-lg">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by symbol or name (e.g. RELIANCE, TCS, Infosys)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-lg border border-input bg-background pl-10 pr-10 py-2.5 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        {searching && (
          <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
        )}
      </div>

      {search.length >= 2 && (
        <div>
          <h2 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
            <ArrowUpDown className="h-3.5 w-3.5" />
            Search Results
            {searchResults && (
              <span className="text-xs">({searchResults.length})</span>
            )}
          </h2>
          {searching ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          ) : !searchResults || searchResults.length === 0 ? (
            <div className="space-y-4">
              <EmptyState
                icon={Search}
                title="No results"
                description={`No stocks found matching "${search}". New tickers aren't pre-loaded — if you know the exact NSE symbol, follow it directly below.`}
              />
              {/^[A-Za-z0-9&]{1,20}$/.test(search.trim()) && (
                <div className="mx-auto flex max-w-sm items-center justify-between gap-3 rounded-lg border bg-card p-4">
                  <div className="min-w-0">
                    <div className="text-xs text-muted-foreground">Follow it directly</div>
                    <div className="font-semibold text-sm truncate">
                      {search.trim().toUpperCase()}
                    </div>
                  </div>
                  <button
                    onClick={() => followMutation.mutate(search.trim().toUpperCase())}
                    disabled={followMutation.isPending}
                    className="shrink-0 flex items-center gap-1 rounded-md bg-primary px-2.5 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
                  >
                    {followMutation.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <>
                        <Plus className="h-3 w-3" /> Follow
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {searchResults.map((ticker) => (
                <StockCard
                  key={ticker.symbol}
                  ticker={ticker}
                  isFollowed={followedSymbols.has(ticker.symbol)}
                  job={getJobStatus(ticker.symbol)}
                  onFollow={() => followMutation.mutate(ticker.symbol)}
                  onUnfollow={() => unfollowMutation.mutate(ticker.symbol)}
                  onReingest={() => reingestMutation.mutate(ticker.symbol)}
                  loading={followMutation.isPending || unfollowMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {search.length < 2 && (
        <div>
          <h2 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
            <TrendingUp className="h-3.5 w-3.5" />
            Currently Following ({followed?.length ?? 0})
          </h2>
          {loadingFollowed ? (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <CardSkeleton key={i} />
              ))}
            </div>
          ) : !followed || followed.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No stocks followed"
              description="Search for a stock above and click Follow to start tracking it. Followed stocks are automatically ingested for AI analysis."
            />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {followed.map((ticker) => (
                <StockCard
                  key={ticker.symbol}
                  ticker={ticker}
                  isFollowed={true}
                  job={getJobStatus(ticker.symbol)}
                  onFollow={() => {}}
                  onUnfollow={() => unfollowMutation.mutate(ticker.symbol)}
                  onReingest={() => reingestMutation.mutate(ticker.symbol)}
                  loading={unfollowMutation.isPending}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StockCard({
  ticker,
  isFollowed,
  job,
  onFollow,
  onUnfollow,
  onReingest,
  loading,
}: {
  ticker: Ticker
  isFollowed: boolean
  job?: IngestionJob
  onFollow: () => void
  onUnfollow: () => void
  onReingest: () => void
  loading: boolean
}) {
  return (
    <div className="rounded-lg border bg-card p-4 space-y-3 hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="font-semibold text-sm">{ticker.symbol}</div>
          <div className="text-xs text-muted-foreground truncate">
            {ticker.company_name}
          </div>
        </div>
        <button
          onClick={isFollowed ? onUnfollow : onFollow}
          disabled={loading}
          className={`shrink-0 flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors disabled:opacity-50 ${
            isFollowed
              ? "bg-destructive/10 text-destructive hover:bg-destructive/20"
              : "bg-primary text-primary-foreground hover:bg-primary/90"
          }`}
        >
          {loading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : isFollowed ? (
            <>
              <Minus className="h-3 w-3" /> Unfollow
            </>
          ) : (
            <>
              <Plus className="h-3 w-3" /> Follow
            </>
          )}
        </button>
      </div>

      <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
        <span className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5">
          {ticker.exchange}
        </span>
        {ticker.sector && (
          <span className="inline-flex items-center gap-1 truncate">
            <Building2 className="h-3 w-3 shrink-0" />
            {ticker.sector}
          </span>
        )}
      </div>

      {isFollowed && (
        <div className="flex items-center justify-between border-t pt-2.5">
          <IngestionBadge job={job} />
          <button
            onClick={onReingest}
            disabled={job?.status === "running"}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${job?.status === "running" ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      )}
    </div>
  )
}

function IngestionBadge({ job }: { job?: IngestionJob }) {
  if (!job) {
    return (
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Clock className="h-3 w-3" /> Pending
      </span>
    )
  }

  switch (job.status) {
    case "running":
      return (
        <span className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
          <Loader2 className="h-3 w-3 animate-spin" /> Ingesting...
        </span>
      )
    case "completed":
      return (
        <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
          <CheckCircle2 className="h-3 w-3" /> {job.articles_processed} articles
        </span>
      )
    case "failed":
      return (
        <span
          className="flex items-center gap-1 text-xs text-red-600 dark:text-red-400"
          title={job.error_message ?? ""}
        >
          <AlertCircle className="h-3 w-3" /> Failed
        </span>
      )
    default:
      return (
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" /> {job.status}
        </span>
      )
  }
}
