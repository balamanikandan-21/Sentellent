"use client"

import { useAuth } from "@/hooks/use-auth"
import { useQuery } from "@tanstack/react-query"
import { tickerApi, chatApi } from "@/services/api"
import {
  User as UserIcon,
  Mail,
  Calendar,
  Eye,
  MessageSquare,
  Shield,
  TrendingUp,
  Target,
  Brain,
  Loader2,
} from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"

export default function ProfilePage() {
  const { user, isLoading: loadingUser } = useAuth()

  const { data: followed } = useQuery({
    queryKey: ["tickers", "followed"],
    queryFn: async () => (await tickerApi.getFollowed()).data,
  })

  const { data: sessions } = useQuery({
    queryKey: ["chat", "sessions"],
    queryFn: async () => (await chatApi.listSessions()).data,
  })

  if (loadingUser) {
    return (
      <div className="space-y-6 max-w-2xl">
        <Skeleton className="h-8 w-48" />
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <div className="flex items-center gap-4">
            <Skeleton className="h-16 w-16 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-4 w-48" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-muted-foreground mt-1">Your account and investor profile</p>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="p-6">
          <div className="flex items-center gap-4">
            {user?.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="h-16 w-16 rounded-full border"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <UserIcon className="h-8 w-8 text-primary" />
              </div>
            )}
            <div>
              <h2 className="text-lg font-semibold">{user?.name}</h2>
              <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <Mail className="h-3.5 w-3.5" />
                {user?.email}
              </div>
            </div>
          </div>
        </div>

        <div className="border-t px-6 py-4 grid grid-cols-2 sm:grid-cols-3 gap-4">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Calendar className="h-3 w-3" /> Joined
            </div>
            <div className="text-sm font-medium">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString("en-IN", {
                    month: "short",
                    year: "numeric",
                  })
                : "—"}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <Eye className="h-3 w-3" /> Following
            </div>
            <div className="text-sm font-medium">{followed?.length ?? 0} stocks</div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground flex items-center gap-1">
              <MessageSquare className="h-3 w-3" /> Conversations
            </div>
            <div className="text-sm font-medium">{sessions?.length ?? 0}</div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card">
        <div className="px-6 py-4 border-b">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Brain className="h-4 w-4 text-primary" />
            Investor Profile
          </h3>
          <p className="text-xs text-muted-foreground mt-0.5">
            Learned from your conversations — the AI adapts recommendations to your style
          </p>
        </div>
        <div className="p-6 space-y-4">
          <ProfileField
            icon={Shield}
            label="Risk Appetite"
            value="Set via conversation"
            hint="Tell the analyst your risk tolerance (e.g., 'I'm a conservative investor')"
          />
          <ProfileField
            icon={TrendingUp}
            label="Investment Style"
            value="Set via conversation"
            hint="Mention your style (e.g., 'I prefer value investing' or 'I'm a growth investor')"
          />
          <ProfileField
            icon={Target}
            label="Investment Goals"
            value="Set via conversation"
            hint="Share your goals (e.g., 'I'm building a retirement portfolio')"
          />
        </div>

        {followed && followed.length > 0 && (
          <div className="border-t px-6 py-4">
            <div className="text-xs text-muted-foreground mb-2">Followed Sectors</div>
            <div className="flex flex-wrap gap-1.5">
              {Array.from(new Set(followed.map((t) => t.sector).filter(Boolean))).map(
                (sector) => (
                  <span
                    key={sector}
                    className="rounded-full border bg-muted/50 px-2.5 py-0.5 text-xs"
                  >
                    {sector}
                  </span>
                ),
              )}
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Your investor profile is automatically updated as you interact with the analyst.
        All preferences are stored securely and used only for personalized recommendations.
      </p>
    </div>
  )
}

function ProfileField({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof Shield
  label: string
  value: string
  hint: string
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-md bg-muted flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <div className="text-sm font-medium">{label}</div>
        <div className="text-xs text-muted-foreground">{value}</div>
        <div className="text-xs text-muted-foreground/70 mt-0.5">{hint}</div>
      </div>
    </div>
  )
}
