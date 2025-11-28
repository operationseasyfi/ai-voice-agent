"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Bell, LogOut, Settings, User, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { ThemeToggle } from "./theme-toggle"
import { Button } from "@/components/ui/button"
import { logout, getAuthToken } from "@/lib/api"
import { useState, useEffect } from "react"

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
  const [isProfileOpen, setIsProfileOpen] = useState(false)
  const [userName, setUserName] = useState("User")

  useEffect(() => {
    // Get user name from localStorage
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user')
      if (user) {
        try {
          const parsed = JSON.parse(user)
          setUserName(parsed.full_name || parsed.username || 'User')
        } catch {}
      }
    }
  }, [])

  const handleLogout = () => {
    logout()
    window.location.href = "/login"
  }

  const userInitials = userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl">
      <div className="container mx-auto flex h-16 items-center px-4">
        {/* Logo - EasyFinance */}
        <div className="mr-8 flex items-center space-x-3">
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="relative">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white font-bold text-sm shadow-lg shadow-purple-500/25 group-hover:shadow-purple-500/40 transition-shadow">
                EF
              </div>
              <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full bg-emerald-500 border-2 border-background" title="System Online" />
            </div>
            <div className="hidden sm:block">
              <span className="font-bold text-lg tracking-tight">EasyFinance</span>
              <span className="text-xs text-muted-foreground block -mt-1">Voice AI Platform</span>
            </div>
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
                  "relative rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                  isActive
                    ? "text-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )}
              >
                {item.name}
                {isActive && (
                  <div className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-8 rounded-full bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500" />
                )}
              </Link>
            )
          })}
        </div>

        {/* Right Section */}
        <div className="flex items-center space-x-2">
          {/* Notification Bell */}
          <Button 
            variant="ghost" 
            size="icon" 
            className="relative hover:bg-accent/50"
            onClick={() => {
              // TODO: Implement notifications panel
              alert('Notifications coming soon!')
            }}
          >
            <Bell className="h-5 w-5" />
            {/* Notification dot */}
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-red-500" />
            <span className="sr-only">Notifications</span>
          </Button>

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* User Profile Dropdown */}
          <div className="relative ml-2">
            <button 
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              onBlur={() => setTimeout(() => setIsProfileOpen(false), 150)}
              className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 outline-none transition-all hover:bg-accent/50 focus:ring-2 focus:ring-purple-500/20"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 text-white text-xs font-semibold shadow-md">
                {userInitials}
              </div>
              <span className="hidden text-sm font-medium sm:inline-block max-w-[100px] truncate">
                {userName}
              </span>
              <ChevronDown className={cn(
                "h-4 w-4 text-muted-foreground transition-transform duration-200",
                isProfileOpen && "rotate-180"
              )} />
            </button>

            {isProfileOpen && (
              <div className="absolute right-0 z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border/50 bg-popover/95 backdrop-blur-xl p-1.5 text-popover-foreground shadow-xl">
                <div className="px-3 py-2 border-b border-border/50 mb-1.5">
                  <p className="text-sm font-medium">{userName}</p>
                  <p className="text-xs text-muted-foreground">Administrator</p>
                </div>
                <Link
                  href="/profile"
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                >
                  <User className="h-4 w-4" />
                  Profile
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>
                <hr className="my-1.5 border-border/50" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-left text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}
