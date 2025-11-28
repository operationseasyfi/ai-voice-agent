"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Calendar, Filter, Download, Upload, Plus, Trash2, ShieldAlert, AlertTriangle, MessageSquare, Gavel } from "lucide-react"
import { getDNCEntries, getDNCStats, getDNCExportUrl, type DNCEntry } from "@/lib/api"

export default function DNCPage() {
  const [entries, setEntries] = useState<DNCEntry[]>([])
  const [stats, setStats] = useState<{ total: number; today: number; by_method: Record<string, number> } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const limit = 25

  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const [entriesData, statsData] = await Promise.all([
          getDNCEntries({ skip: page * limit, limit }),
          getDNCStats()
        ])
        setEntries(entriesData.dnc_entries)
        setTotal(entriesData.total)
        setStats(statsData)
      } catch (err) {
        console.error("Error fetching DNC data:", err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [page])

  const filteredEntries = entries.filter(entry => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      entry.phone_number?.toLowerCase().includes(query) ||
      entry.reason?.toLowerCase().includes(query)
    )
  })

  const getStatusBadge = (method: string) => {
    switch (method?.toLowerCase()) {
      case 'ai_detection':
      case 'phrase_detection':
        return { text: "Flagged", class: "badge-flagged" }
      case 'litigator':
      case 'tcpa':
        return { text: "Litigator", class: "badge-litigator" }
      case 'user_request':
      case 'manual':
      default:
        return { text: "Blocked", class: "badge-blocked" }
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">DNC & Compliance</h1>
          <p className="page-description">Manage blocked numbers, litigator lists, and compliance settings.</p>
        </div>
        <div className="flex items-center gap-2">
          <a href={getDNCExportUrl()} download className="btn-secondary flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export CSV
          </a>
          <button className="btn-secondary flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Import List
          </button>
          <button className="btn-primary flex items-center gap-2">
            <Plus className="h-4 w-4" />
            Add Number
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Calls Blocked</span>
              <ShieldAlert className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.total?.toLocaleString() || "0"}
            </div>
            <p className="text-xs text-primary mt-1">+12% from last month</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Flagged Numbers</span>
              <AlertTriangle className="h-4 w-4 text-amber-400" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.by_method?.ai_detection || "0"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Requires review</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Phrases Detected</span>
              <MessageSquare className="h-4 w-4 text-destructive" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : (stats?.by_method?.phrase_detection || 0) + (stats?.by_method?.ai_detection || 0)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">&quot;Stop calling&quot;, &quot;Lawyer&quot;, etc.</p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Litigators Blocked</span>
              <Gavel className="h-4 w-4 text-purple-400" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.by_method?.litigator || "0"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">Known TCPA plaintiffs</p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search number, reason, or source..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4"
          />
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          Date Range
        </button>
        <button className="btn-secondary flex items-center gap-2">
          <Filter className="h-4 w-4" />
          Filter
        </button>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <table>
            <thead>
              <tr>
                <th>Phone Number</th>
                <th>Status</th>
                <th>Date Added</th>
                <th>Reason</th>
                <th>Added By</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-muted-foreground">
                    Loading DNC entries...
                  </td>
                </tr>
              ) : filteredEntries.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-muted-foreground">
                    No DNC entries found
                  </td>
                </tr>
              ) : (
                filteredEntries.map((entry) => {
                  const status = getStatusBadge(entry.detection_method)
                  return (
                    <tr key={entry.id}>
                      <td>
                        <div className="flex items-center gap-2">
                          <ShieldAlert className="h-4 w-4 text-destructive" />
                          <span className="font-medium">{entry.phone_number}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`text-xs px-2 py-1 ${status.class}`}>
                          {status.text}
                        </span>
                      </td>
                      <td className="text-muted-foreground">
                        {new Date(entry.flagged_at).toLocaleDateString()}
                      </td>
                      <td className="font-medium">
                        {entry.reason || entry.detected_phrase || "User Request"}
                      </td>
                      <td className="text-muted-foreground">
                        {entry.detection_method === 'ai_detection' ? 'AI Sentinel' :
                         entry.detection_method === 'manual' ? 'Admin' :
                         entry.detection_method === 'user_request' ? 'System' : 'System'}
                      </td>
                      <td>
                        <button className="p-1 text-muted-foreground hover:text-destructive transition-colors">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {total > limit && (
            <div className="flex items-center justify-between p-4 border-t border-border">
              <p className="text-sm text-muted-foreground">
                Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={(page + 1) * limit >= total}
                  className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
