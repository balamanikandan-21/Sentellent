"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"

export default function CallbackPage() {
  const router = useRouter()
  const setUser = useAuthStore((s) => s.setUser)

  useEffect(() => {
    fetch("/api/v1/auth/me", { credentials: "include" })
      .then((r) => {
        if (!r.ok) throw new Error("Not authenticated")
        return r.json()
      })
      .then((user) => {
        setUser(user)
        router.replace("/dashboard")
      })
      .catch(() => {
        router.replace("/login?error=oauth_failed")
      })
  }, [router, setUser])

  return (
    <div className="flex min-h-screen items-center justify-center text-muted-foreground">
      Signing in...
    </div>
  )
}
