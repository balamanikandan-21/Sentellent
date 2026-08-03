"use client"

import { useTheme } from "next-themes"
import { useAuth } from "@/hooks/use-auth"
import {
  Sun,
  Moon,
  Monitor,
  LogOut,
  Bell,
  Palette,
  Database,
  Info,
} from "lucide-react"

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { user, logout } = useAuth()

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">Application preferences</p>
      </div>

      <div className="rounded-lg border bg-card divide-y">
        <div className="px-6 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Palette className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Appearance</h3>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: "light", label: "Light", icon: Sun },
              { value: "dark", label: "Dark", icon: Moon },
              { value: "system", label: "System", icon: Monitor },
            ].map(({ value, label, icon: Icon }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={`flex flex-col items-center gap-1.5 rounded-lg border p-3 text-xs transition-colors ${
                  theme === value
                    ? "border-primary bg-primary/5 text-primary"
                    : "border-transparent hover:bg-muted"
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </div>

        <div className="px-6 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Chat Preferences</h3>
          </div>
          <div className="space-y-3">
            <label className="flex items-center justify-between">
              <span className="text-sm">Show confidence scores</span>
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded border-input accent-primary"
              />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Show citation cards</span>
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded border-input accent-primary"
              />
            </label>
            <label className="flex items-center justify-between">
              <span className="text-sm">Show scorecard on recommendations</span>
              <input
                type="checkbox"
                defaultChecked
                className="h-4 w-4 rounded border-input accent-primary"
              />
            </label>
          </div>
        </div>

        <div className="px-6 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Database className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-semibold">Data</h3>
          </div>
          <div className="space-y-2 text-sm text-muted-foreground">
            <div className="flex justify-between">
              <span>Currency</span>
              <span className="font-medium text-foreground">INR (Rs.)</span>
            </div>
            <div className="flex justify-between">
              <span>Exchange</span>
              <span className="font-medium text-foreground">NSE / BSE</span>
            </div>
            <div className="flex justify-between">
              <span>AI Model</span>
              <span className="font-medium text-foreground">Claude Sonnet 5</span>
            </div>
            <div className="flex justify-between">
              <span>Embedding Model</span>
              <span className="font-medium text-foreground">text-embedding-3-small</span>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-card px-6 py-4">
        <div className="flex items-center gap-2 mb-3">
          <Info className="h-4 w-4 text-muted-foreground" />
          <h3 className="text-sm font-semibold">Account</h3>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between items-center text-sm">
            <span className="text-muted-foreground">Signed in as</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <button
            onClick={logout}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-destructive/30 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </div>

      <p className="text-xs text-muted-foreground text-center">
        Sentellent Stock Analyst v0.1.0 — All figures in INR. Not financial advice.
      </p>
    </div>
  )
}
