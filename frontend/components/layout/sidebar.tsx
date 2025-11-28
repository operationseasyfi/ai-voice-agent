"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState, useEffect } from "react"
import { cn } from "@/lib/utils"
import { getAuthToken, logout } from "@/lib/api"
import {
  LayoutDashboard,
  Activity,
  History,
  Phone,
  Bot,
  ShieldAlert,
  CreditCard,
  Settings,
  Bell,
  MessageSquare,
  User,
  Users,
  LogOut,
  ChevronDown,
  Check,
  Plus
} from "lucide-react"

const navigationItems = [
  { 
    section: "OVERVIEW",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
      { name: "Live Monitor", href: "/live-monitor", icon: Activity, badge: "LIVE" },
      { name: "Call History", href: "/call-history", icon: History },
      { name: "Phone Numbers", href: "/phone-numbers", icon: Phone },
      { name: "AI Agents", href: "/ai-agents", icon: Bot },
      { name: "DNC List", href: "/dnc", icon: ShieldAlert },
    ]
  }
]

export function Sidebar() {
  const pathname = usePathname()
  const [workspaceName, setWorkspaceName] = useState("Main Workspace")
  const [isWorkspaceOpen, setIsWorkspaceOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [userName, setUserName] = useState("Admin User")
  const [userEmail, setUserEmail] = useState("admin@easyfinance.ai")

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user')
      if (user) {
        try {
          const parsed = JSON.parse(user)
          setUserName(parsed.full_name || parsed.username || 'Admin User')
          setUserEmail(parsed.email || 'admin@easyfinance.ai')
        } catch {}
      }
    }
  }, [])

  const handleLogout = () => {
    logout()
    window.location.href = "/login"
  }

  const userInitials = userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  // Don't show sidebar on login page
  if (pathname === '/login') {
    return null
  }

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-[220px] bg-card border-r border-border flex flex-col">
      {/* Workspace Selector */}
      <div className="relative">
        <button
          onClick={() => setIsWorkspaceOpen(!isWorkspaceOpen)}
          className="w-full flex items-center justify-between px-4 py-4 border-b border-border hover:bg-secondary/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 bg-primary/20 flex items-center justify-center">
              <Activity className="h-3.5 w-3.5 text-primary" />
            </div>
            <span className="text-sm font-medium">{workspaceName}</span>
          </div>
          <ChevronDown className={cn(
            "h-4 w-4 text-muted-foreground transition-transform",
            isWorkspaceOpen && "rotate-180"
          )} />
        </button>

        {isWorkspaceOpen && (
          <div className="absolute top-full left-0 w-full bg-popover border border-border shadow-lg z-50">
            <div className="px-3 py-2 text-xs text-muted-foreground">Switch Workspace</div>
            <button className="w-full flex items-center justify-between px-3 py-2 text-sm hover:bg-secondary/50">
              <span>Main Workspace</span>
              <Check className="h-4 w-4 text-primary" />
            </button>
            <div className="border-t border-border">
              <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:bg-secondary/50 hover:text-foreground">
                <Plus className="h-4 w-4" />
                Create Workspace
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 overflow-y-auto">
        {navigationItems.map((section) => (
          <div key={section.section} className="mb-4">
            <div className="px-4 mb-2 text-xs font-medium text-muted-foreground tracking-wider">
              {section.section}
            </div>
            <div className="space-y-0.5">
              {section.items.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
                const Icon = item.icon
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 mx-2 px-3 py-2 text-sm transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary border-l-2 border-primary -ml-[2px] pl-[14px]"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                    )}
                  >
                    <Icon className="h-4 w-4" />
                    <span className="flex-1">{item.name}</span>
                    {item.badge && (
                      <span className="live-badge">{item.badge}</span>
                    )}
                  </Link>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* System Status */}
      <div className="px-4 py-3 border-t border-border">
        <div className="flex items-center gap-2 text-xs">
          <span className="status-dot online"></span>
          <span className="text-muted-foreground">All Systems Operational</span>
        </div>
      </div>
    </aside>
  )
}

export function Header() {
  const pathname = usePathname()
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  const [userName, setUserName] = useState("Admin User")
  const [userEmail, setUserEmail] = useState("admin@easyfinance.ai")

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user')
      if (user) {
        try {
          const parsed = JSON.parse(user)
          setUserName(parsed.full_name || parsed.username || 'Admin User')
          setUserEmail(parsed.email || 'admin@easyfinance.ai')
        } catch {}
      }
    }
  }, [])

  const handleLogout = () => {
    logout()
    window.location.href = "/login"
  }

  const userInitials = userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)

  // Get page title from pathname
  const getPageTitle = () => {
    const titles: Record<string, string> = {
      '/': 'DASHBOARD',
      '/live-monitor': 'LIVE MONITOR',
      '/call-history': 'CALL HISTORY',
      '/phone-numbers': 'PHONE NUMBERS',
      '/ai-agents': 'AI AGENTS',
      '/dnc': 'DNC LIST',
      '/billing': 'BILLING',
      '/settings': 'SETTINGS',
    }
    return titles[pathname] || 'DASHBOARD'
  }

  // Don't show header on login page
  if (pathname === '/login') {
    return null
  }

  return (
    <header className="fixed top-0 left-[220px] right-0 z-30 h-14 bg-background border-b border-border flex items-center justify-between px-6">
      {/* Page Title */}
      <div className="text-sm font-medium tracking-wider text-muted-foreground">
        {getPageTitle()}
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        {/* Feedback */}
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors">
          <MessageSquare className="h-4 w-4" />
          Feedback
        </button>

        {/* Notifications */}
        <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors relative">
          <Bell className="h-4 w-4" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* User Menu */}
        <div className="relative ml-2">
          <button
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            onBlur={() => setTimeout(() => setIsUserMenuOpen(false), 150)}
            className="p-2 text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors"
          >
            <User className="h-4 w-4" />
          </button>

          {isUserMenuOpen && (
            <div className="absolute right-0 top-full mt-1 w-56 bg-popover border border-border shadow-lg z-50">
              <div className="px-4 py-3 border-b border-border">
                <p className="text-sm font-medium">{userName}</p>
                <p className="text-xs text-muted-foreground">{userEmail}</p>
              </div>
              <div className="py-1">
                <Link
                  href="/settings"
                  className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                >
                  <Users className="h-4 w-4" />
                  Team Members
                </Link>
                <Link
                  href="/billing"
                  className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                >
                  <CreditCard className="h-4 w-4" />
                  Billing
                </Link>
                <Link
                  href="/settings"
                  className="flex items-center gap-3 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                >
                  <Settings className="h-4 w-4" />
                  Settings
                </Link>
              </div>
              <div className="border-t border-border py-1">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-3 px-4 py-2 text-sm text-primary hover:bg-secondary/50"
                >
                  <LogOut className="h-4 w-4" />
                  Log out
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

