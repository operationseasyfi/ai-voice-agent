"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Download, AlertTriangle, Search, X } from "lucide-react"
import { getDNCEntries, getDNCStats, getDNCExportUrl, type DNCEntry } from "@/lib/api"

export default function DNCPage() {
  const [entries, setEntries] = useState<DNCEntry[]>([])
  const [stats, setStats] = useState<{ total: number; today: number; by_method: Record<string, number> } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const limit = 25
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [fromDate, setFromDate] = useState<string>("")
  const [toDate, setToDate] = useState<string>("")

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        
        const [entriesData, statsData] = await Promise.all([
          getDNCEntries({
            from_date: fromDate || undefined,
            to_date: toDate || undefined,
            skip: page * limit,
            limit
          }),
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
  }, [page, fromDate, toDate])

  const filteredEntries = entries.filter(entry => {
    if (!searchQuery) return true
    return entry.phone_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
           entry.reason?.toLowerCase().includes(searchQuery.toLowerCase()) ||
           entry.detected_phrase?.toLowerCase().includes(searchQuery.toLowerCase())
  })

  const handleExport = () => {
    const url = getDNCExportUrl({ from_date: fromDate, to_date: toDate })
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">DNC Management</h1>
          <p className="text-muted-foreground">
            Manage do-not-call entries detected by AI or added manually
          </p>
        </div>
        <Button onClick={handleExport} variant="outline">
          <Download className="h-4 w-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total DNC Entries</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flagged Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.today || 0}</div>
            <p className="text-xs text-muted-foreground">New DNC requests</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auto-Detected</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.by_method?.auto || 0}</div>
            <p className="text-xs text-muted-foreground">By AI phrase detection</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by phone number or phrase..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 w-full rounded-md border bg-background px-10 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                placeholder="From date"
                className="h-10 rounded-md border bg-background px-3 text-sm"
              />
              <span className="text-muted-foreground">to</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                placeholder="To date"
                className="h-10 rounded-md border bg-background px-3 text-sm"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DNC List */}
      <Card>
        <CardHeader>
          <CardTitle>DNC Entries</CardTitle>
          <CardDescription>
            {total} total entries • Page {page + 1} of {Math.ceil(total / limit) || 1}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading...</p>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <AlertTriangle className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-2">No DNC entries found</p>
              <p className="text-sm text-muted-foreground">
                DNC entries will appear here when callers request to be removed from the list
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid gap-4">
                {/* Header */}
                <div className="grid grid-cols-5 gap-4 px-4 py-2 bg-muted/50 rounded-lg text-sm font-medium">
                  <div>Phone Number</div>
                  <div>Detection Method</div>
                  <div>Detected Phrase</div>
                  <div>Reason</div>
                  <div>Flagged At</div>
                </div>
                
                {/* Rows */}
                {filteredEntries.map(entry => (
                  <div key={entry.id} className="grid grid-cols-5 gap-4 px-4 py-3 border rounded-lg items-center">
                    <div className="font-mono text-sm">{entry.phone_number}</div>
                    <div>
                      <Badge variant={entry.detection_method === "auto" ? "success" : "secondary"} size="sm">
                        {entry.detection_method}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground truncate" title={entry.detected_phrase || ""}>
                      {entry.detected_phrase || "-"}
                    </div>
                    <div className="text-sm text-muted-foreground truncate" title={entry.reason || ""}>
                      {entry.reason || "-"}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {entry.flagged_at ? new Date(entry.flagged_at).toLocaleString() : "-"}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Pagination */}
              <div className="flex items-center justify-between pt-4">
                <p className="text-sm text-muted-foreground">
                  Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={(page + 1) * limit >= total}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

