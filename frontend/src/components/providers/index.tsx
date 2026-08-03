"use client"

import { ThemeProvider } from "./theme-provider"
import { QueryProvider } from "./query-provider"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <ThemeProvider>{children}</ThemeProvider>
    </QueryProvider>
  )
}
