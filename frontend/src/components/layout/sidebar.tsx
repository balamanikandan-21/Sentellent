"use client"

import { useEffect } from "react"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  MessageSquare,
  Search,
  Eye,
  User,
  Settings,
  TrendingUp,
  X,
} from "lucide-react"
import { NavItem } from "./nav-item"
import { useSidebarStore } from "@/stores/sidebar-store"

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/search", label: "Stock Search", icon: Search },
  { href: "/watchlist", label: "Watchlist", icon: Eye },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/settings", label: "Settings", icon: Settings },
]

export function Sidebar() {
  const { open, close } = useSidebarStore()
  const pathname = usePathname()

  useEffect(() => {
    close()
  }, [pathname, close])

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={close}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex h-full w-64 shrink-0 flex-col border-r bg-card transition-transform duration-200 lg:static lg:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-14 items-center justify-between border-b px-4">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <span className="font-semibold tracking-tight">Sentellent</span>
          </div>
          <button
            onClick={close}
            className="lg:hidden p-1 rounded hover:bg-muted"
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <nav className="flex-1 space-y-1 p-2 overflow-auto">
          {navItems.map((item) => (
            <NavItem key={item.href} {...item} />
          ))}
        </nav>

        <div className="border-t p-3">
          <div className="rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
            All analysis in INR. Not financial advice.
          </div>
        </div>
      </aside>
    </>
  )
}
