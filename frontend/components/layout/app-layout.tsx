"use client"

import { usePathname } from "next/navigation"
import { Sidebar, Header } from "./sidebar"

export function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  
  // Pages that should not show the sidebar/header
  const noLayoutPages = ['/login', '/register', '/forgot-password']
  const showLayout = !noLayoutPages.includes(pathname)

  if (!showLayout) {
    return <>{children}</>
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-[220px]">
        <Header />
        <main className="pt-14 p-6 page-transition">
          {children}
        </main>
      </div>
    </div>
  )
}

