"use client"

import { useState, useEffect, Suspense } from "react"
import { useSearchParams } from "next/navigation"
import { Card, CardContent } from "@/components/ui/card"
import { Search, Calendar, Filter, Download, MoreHorizontal, CheckCircle } from "lucide-react"
import { getCalls, getAgents, getCallsExportUrl, type CallRecord, type Agent } from "@/lib/api"

function CallHistoryContent() {
  const searchParams = useSearchParams()
  
  const [calls, setCalls] = useState<CallRecord[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [activeTab, setActiveTab] = useState<"transfers" | "all">(
    searchParams.get('tab') === 'all' ? 'all' : 'transfers'
  )
  
  const [page, setPage] = useState(0)
  const limit = 25

  const [searchQuery, setSearchQuery] = useState("")
  const [fromDate, setFromDate] = useState<string>(searchParams.get('from_date') || "")
  const [toDate, setToDate] = useState<string>(searchParams.get('to_date') || "")

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        
        const params: Record<string, any> = {
          skip: page * limit,
          limit
        }
        
        if (fromDate) params.from_date = fromDate
        if (toDate) params.to_date = toDate
        if (activeTab === 'transfers') {
          params.disconnection_reason = 'transferred'
        }
        
        const [callsData, agentsData] = await Promise.all([
          getCalls(params),
          getAgents({ is_active: true })
        ])
        
        setCalls(callsData.calls)
        setTotal(callsData.total)
        setAgents(agentsData.agents)
      } catch (err) {
        console.error("Error fetching calls:", err)
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchData()
  }, [page, fromDate, toDate, activeTab])

  const filteredCalls = calls.filter(call => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      call.from_number?.toLowerCase().includes(query) ||
      call.lead_name?.toLowerCase().includes(query)
    )
  })

  const getTierBadge = (tier: string) => {
    switch (tier?.toLowerCase()) {
      case 'high': return { text: "High Tier (>35k)", class: "tier-high" }
      case 'mid': return { text: "Mid Tier (10-35k)", class: "tier-mid" }
      case 'low': return { text: "Low Tier (<10k)", class: "tier-low" }
      default: return { text: "N/A", class: "bg-secondary text-muted-foreground" }
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Call History</h1>
          <p className="page-description">Detailed logs of all inbound and outbound calls.</p>
        </div>
        <a 
          href={getCallsExportUrl({ from_date: fromDate, to_date: toDate })}
          download
          className="btn-secondary flex items-center gap-2"
        >
          <Download className="h-4 w-4" />
          Export CSV
        </a>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by number, name, or queue..."
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

      {/* Tabs */}
      <div className="flex border-b border-border">
        <button
          onClick={() => setActiveTab('transfers')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${
            activeTab === 'transfers' 
              ? 'text-foreground' 
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Successful Transfers
          {activeTab === 'transfers' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('all')}
          className={`px-6 py-3 text-sm font-medium transition-colors relative ${
            activeTab === 'all' 
              ? 'text-foreground' 
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          All Calls
          {activeTab === 'all' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
          )}
        </button>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <table>
            <thead>
              <tr>
                <th>Customer</th>
                <th>Loan Amount</th>
                <th>Use Case</th>
                <th>Employment</th>
                <th>CC Debt</th>
                <th>Personal Loans</th>
                <th>Other Debt</th>
                <th>Income (Mo)</th>
                <th>Confirmed</th>
                <th>Queue Tier</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-muted-foreground">
                    Loading calls...
                  </td>
                </tr>
              ) : filteredCalls.length === 0 ? (
                <tr>
                  <td colSpan={11} className="text-center py-8 text-muted-foreground">
                    No calls found
                  </td>
                </tr>
              ) : (
                filteredCalls.map((call) => {
                  const tier = getTierBadge(call.transfer_tier)
                  return (
                    <tr key={call.id}>
                      <td>
                        <div>
                          <div className="font-medium">{call.lead_name || "Unknown"}</div>
                          <div className="text-xs text-muted-foreground">{call.from_number}</div>
                        </div>
                      </td>
                      <td className="text-primary font-medium">
                        ${call.total_debt?.toLocaleString() || "0"}
                      </td>
                      <td className="text-muted-foreground">Debt Consolidation</td>
                      <td className="text-muted-foreground">Employed</td>
                      <td>${((call.total_debt || 0) * 0.7).toLocaleString()}</td>
                      <td>${((call.total_debt || 0) * 0.2).toLocaleString()}</td>
                      <td>${((call.total_debt || 0) * 0.1).toLocaleString()}</td>
                      <td className="font-medium">${((call.total_debt || 0) * 0.15).toLocaleString()}</td>
                      <td>
                        {call.transfer_success ? (
                          <span className="flex items-center gap-1 text-primary">
                            <CheckCircle className="h-4 w-4" />
                            ${call.total_debt?.toLocaleString() || "0"}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td>
                        <span className={`text-xs px-2 py-1 ${tier.class}`}>
                          {tier.text}
                        </span>
                      </td>
                      <td>
                        <button className="p-1 text-muted-foreground hover:text-foreground">
                          <MoreHorizontal className="h-4 w-4" />
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

export default function CallHistoryPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading call history...</p>
      </div>
    }>
      <CallHistoryContent />
    </Suspense>
  )
}
