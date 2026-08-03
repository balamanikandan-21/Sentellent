"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import { authApi } from "@/services/api"

export function useAuth() {
  const { user, isAuthenticated, setUser, logout: clearStore } = useAuthStore()
  const queryClient = useQueryClient()
  const router = useRouter()

  const { data, isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.getMe().then((r) => r.data),
    retry: false,
    enabled: !user,
  })

  useEffect(() => {
    if (data) setUser(data)
  }, [data, setUser])

  const logout = async () => {
    try {
      await authApi.logout()
    } finally {
      clearStore()
      queryClient.clear()
      router.push("/login")
    }
  }

  return { user, isAuthenticated, isLoading, logout }
}
