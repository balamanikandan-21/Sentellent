import Link from "next/link"
import {
  Brain,
  TrendingUp,
  Shield,
  MessageSquare,
  BarChart3,
  Zap,
  BookOpen,
  Target,
  ArrowRight,
} from "lucide-react"

const FEATURES = [
  {
    icon: Brain,
    title: "Agentic AI Analysis",
    description:
      "LangGraph-powered multi-node agent routes queries through retrieval, analysis, and recommendation pipelines.",
  },
  {
    icon: BarChart3,
    title: "Multi-Factor Scoring",
    description:
      "9-dimension scorecard evaluating fundamentals, momentum, value, growth, quality, risk, dividends, sentiment, and persona alignment.",
  },
  {
    icon: Shield,
    title: "Anti-Hallucination",
    description:
      "Every claim cites its source. Below confidence threshold, the agent says \"I don't have that in the data\" instead of guessing.",
  },
  {
    icon: MessageSquare,
    title: "Streaming Chat",
    description:
      "Real-time SSE streaming with markdown rendering, citation cards, and confidence badges for every response.",
  },
  {
    icon: BookOpen,
    title: "RAG Pipeline",
    description:
      "Hybrid search combining vector similarity and full-text search with LLM reranking and confidence scoring.",
  },
  {
    icon: Target,
    title: "Investor Memory",
    description:
      "Long-term memory system learns your risk appetite, investment style, and sector preferences across sessions.",
  },
]

const STATS = [
  { value: "9", label: "Scoring Factors" },
  { value: "100%", label: "INR Native" },
  { value: "NSE", label: "Exchange Coverage" },
  { value: "<2s", label: "Response Time" },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <nav className="border-b bg-card/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="mx-auto max-w-6xl flex items-center justify-between px-4 sm:px-6 h-14">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <span className="font-semibold tracking-tight">Sentellent</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Sign in
            </Link>
            <Link
              href="/login"
              className="inline-flex items-center rounded-md bg-primary px-3.5 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      <section className="mx-auto max-w-6xl px-4 sm:px-6 pt-16 sm:pt-24 pb-16">
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full border bg-muted/50 px-3 py-1 text-xs text-muted-foreground mb-6">
            <Zap className="h-3 w-3" />
            Powered by Claude Sonnet 5 + LangGraph
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]">
            AI-Powered Indian
            <span className="text-primary block sm:inline"> Stock Analyst</span>
          </h1>
          <p className="mt-4 sm:mt-6 text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Research NSE-listed companies, get data-driven buy/hold/sell recommendations,
            and track market sentiment — all backed by cited sources in INR. Never
            hallucinated, always verifiable.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 rounded-md bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors w-full sm:w-auto justify-center"
            >
              Start Analyzing
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="#features"
              className="inline-flex items-center gap-2 rounded-md border px-5 py-2.5 text-sm font-medium hover:bg-accent transition-colors w-full sm:w-auto justify-center"
            >
              See Features
            </Link>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 max-w-2xl mx-auto">
          {STATS.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-2xl sm:text-3xl font-bold text-primary">{stat.value}</div>
              <div className="text-xs sm:text-sm text-muted-foreground mt-0.5">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="features" className="border-t bg-muted/30 py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Built for Serious Analysis
            </h2>
            <p className="mt-2 text-muted-foreground">
              Every feature designed around Indian equity markets
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <div
                key={feature.title}
                className="rounded-lg border bg-card p-5 space-y-3 hover:shadow-sm transition-shadow"
              >
                <div className="w-9 h-9 rounded-md bg-primary/10 flex items-center justify-center">
                  <feature.icon className="h-4.5 w-4.5 text-primary" />
                </div>
                <h3 className="font-semibold text-sm">{feature.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="rounded-xl border bg-card p-8 sm:p-12 text-center">
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Ready to analyze?
            </h2>
            <p className="mt-2 text-muted-foreground max-w-md mx-auto">
              Sign in with Google and start researching Indian stocks in seconds.
              All analysis in INR, every claim cited.
            </p>
            <Link
              href="/login"
              className="mt-6 inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Get Started Free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t py-6">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-muted-foreground">
          <span>Sentellent Stock Analyst</span>
          <span>Not financial advice. All figures in INR.</span>
        </div>
      </footer>
    </div>
  )
}
