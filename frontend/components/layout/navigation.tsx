"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Bell, LogOut } from "lucide-react"
import { cn } from "@/lib/utils"
import { ThemeToggle } from "./theme-toggle"
import { Button } from "@/components/ui/button"
import { logout } from "@/lib/api"

const navigationItems = [
  { name: "Dashboard", href: "/" },
  { name: "Call History", href: "/call-history" },
  { name: "Phone Numbers", href: "/phone-numbers" },
  { name: "AI Agents", href: "/ai-agents" },
  { name: "DNC List", href: "/dnc" },
  { name: "Billing", href: "/billing" },
]

export function Navigation() {
  const pathname = usePathname()

  const handleLogout = () => {
    logout()
    window.location.href = "/login"
  }

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-backdrop-filter:bg-background/60">
      <div className="container mx-auto flex h-16 items-center px-4">
        {/* Logo */}
        <div className="mr-8 flex items-center space-x-2">
          <Link href="/" className="flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground font-bold">
              AI
            </div>
            <span className="hidden font-bold sm:inline-block">Voice Agent</span>
          </Link>
        </div>

        {/* Navigation Links */}
        <div className="flex flex-1 items-center space-x-1">
          {navigationItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground"
                )}
              >
                {item.name}
              </Link>
            )
          })}
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-2">
          {/* Notification Bell */}
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
            <span className="sr-only">Notifications</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Profile Dropdown */}
          <details className="relative ml-2">
            <summary className="flex cursor-pointer items-center rounded-md px-2 py-1 outline-none transition hover:bg-accent hover:text-accent-foreground">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-medium">
                U
              </div>
              <span className="hidden ml-2 text-sm font-medium sm:inline-block">User</span>
            </summary>

            <div className="absolute right-0 z-50 mt-2 w-48 overflow-hidden rounded-md border bg-popover p-2 text-popover-foreground shadow-lg">
              <Link
                href="/profile"
                className="block rounded px-2 py-1 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                Profile
              </Link>
              <Link
                href="/settings"
                className="mt-1 block rounded px-2 py-1 text-sm hover:bg-accent hover:text-accent-foreground"
              >
                Settings
              </Link>
              <hr className="my-2 border-muted-foreground/20" />
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-2 rounded px-2 py-1 text-left text-sm hover:bg-accent hover:text-accent-foreground"
              >
                <LogOut className="h-4 w-4" />
                Sign out
              </button>
            </div>
          </details>
        </div>
      </div>
    </nav>
  )
}
