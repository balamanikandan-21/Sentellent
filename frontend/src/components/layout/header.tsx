"use client"

import { LogOut, Moon, Sun, Menu } from "lucide-react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/hooks/use-auth"
import { useSidebarStore } from "@/stores/sidebar-store"

export function Header() {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const toggleSidebar = useSidebarStore((s) => s.toggle)

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-4 sm:px-6">
      <button
        onClick={toggleSidebar}
        className="lg:hidden p-2 -ml-2 rounded-md hover:bg-muted"
        aria-label="Toggle sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="hidden lg:block" />

      <div className="flex items-center gap-2 sm:gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Toggle theme"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>
        {user && (
          <>
            {user.picture ? (
              <img
                src={user.picture}
                alt={user.name}
                className="h-7 w-7 rounded-full border"
                referrerPolicy="no-referrer"
              />
            ) : (
              <span className="text-sm text-muted-foreground hidden sm:inline">{user.name}</span>
            )}
            <Button variant="ghost" size="icon" onClick={logout} aria-label="Sign out">
              <LogOut className="h-4 w-4" />
            </Button>
          </>
        )}
      </div>
    </header>
  )
}
