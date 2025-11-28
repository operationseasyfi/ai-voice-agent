"use client"

import { useState, useEffect } from "react"
import { useSearchParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AudioPlayer } from "@/components/ui/audio-player"
import { TranscriptViewer } from "@/components/ui/transcript-viewer"
import { Search, X, Phone, TrendingUp, Clock, AlertTriangle, Download, FileText } from "lucide-react"
import { getCalls, getAgents, getDashboardStats, getCallDetails, getTierColor, getTierLabel, getCallsExportUrl, type CallRecord, type Agent, type DashboardStats, type CallDetails } from "@/lib/api"

export default function CallHistoryPage() {
  const searchParams = useSearchParams()
  
  // State
  const [calls, setCalls] = useState<CallRecord[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [selectedCall, setSelectedCall] = useState<CallDetails | null>(null)
  const [callTranscript, setCallTranscript] = useState<string | null>(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  
  // Pagination
  const [page, setPage] = useState(0)
  const limit = 25

  // Filters - initialize from URL params if present
  const [searchQuery, setSearchQuery] = useState("")
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || "all")
  const [agentFilter, setAgentFilter] = useState(searchParams.get('agent_id') || "")
  const [tierFilter, setTierFilter] = useState(searchParams.get('transfer_tier') || "all")
  const [dncFilter, setDncFilter] = useState(searchParams.get('is_dnc') === 'true')
  const [reasonFilter, setReasonFilter] = useState(searchParams.get('disconnection_reason') || "all")
  const [fromDate, setFromDate] = useState<string>(searchParams.get('from_date') || "")
  const [toDate, setToDate] = useState<string>(searchParams.get('to_date') || "")

  // Fetch data
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
        if (agentFilter) params.agent_id = agentFilter
        if (statusFilter !== "all") params.status = statusFilter
        if (tierFilter !== "all") params.transfer_tier = tierFilter
        if (dncFilter) params.is_dnc = true
        if (reasonFilter !== "all") params.disconnection_reason = reasonFilter
        
        const [callsData, agentsData, statsData] = await Promise.all([
          getCalls(params),
          getAgents({ is_active: true }),
          getDashboardStats({
            from_date: fromDate || undefined,
            to_date: toDate || undefined,
            agent_id: agentFilter || undefined
          })
        ])
        
        setCalls(callsData.calls)
        setTotal(callsData.total)
        setAgents(agentsData.agents)
        setStats(statsData)
      } catch (err) {
        console.error("Error fetching calls:", err)
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchData()
  }, [page, fromDate, toDate, agentFilter, statusFilter, tierFilter, dncFilter, reasonFilter])

  // Fetch call details with transcript when a call is selected
  const handleSelectCall = async (call: CallRecord) => {
    setSelectedCall(call)
    setLoadingDetails(true)
    setCallTranscript(null)
    
    try {
      const details = await getCallDetails(call.id)
      setSelectedCall(details)
      setCallTranscript(details.transcript || null)
    } catch (err) {
      console.error("Error fetching call details:", err)
    } finally {
      setLoadingDetails(false)
    }
  }

  // Client-side search filter
  const filteredCalls = calls.filter(call => {
    if (!searchQuery) return true
    const query = searchQuery.toLowerCase()
    return (
      call.from_number?.toLowerCase().includes(query) ||
      call.lead_name?.toLowerCase().includes(query) ||
      call.to_number?.toLowerCase().includes(query)
    )
  })

  const clearFilters = () => {
    setSearchQuery("")
    setStatusFilter("all")
    setAgentFilter("")
    setTierFilter("all")
    setDncFilter(false)
    setReasonFilter("all")
    setFromDate("")
    setToDate("")
    setPage(0)
  }

  const hasActiveFilters = searchQuery || statusFilter !== "all" || agentFilter || tierFilter !== "all" || dncFilter || reasonFilter !== "all" || fromDate || toDate

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Call History</h1>
          <p className="text-muted-foreground">
            Complete record of all calls with recordings and transcripts
          </p>
        </div>
        <a 
          href={getCallsExportUrl({
            from_date: fromDate || undefined,
            to_date: toDate || undefined,
            agent_id: agentFilter || undefined,
            status: statusFilter !== "all" ? statusFilter : undefined,
            transfer_tier: tierFilter !== "all" ? tierFilter : undefined,
            is_dnc: dncFilter || undefined
          })}
          download
        >
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </a>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search by phone number or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="h-10 w-full rounded-md border bg-background px-10 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                {searchQuery && (
                  <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2">
                    <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                  </button>
                )}
              </div>
              {hasActiveFilters && (
                <Button variant="outline" onClick={clearFilters}>Clear Filters</Button>
              )}
            </div>
            <div className="grid gap-4 md:grid-cols-5">
              <div className="space-y-2">
                <label className="text-sm font-medium">From Date</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => { setFromDate(e.target.value); setPage(0); }}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">To Date</label>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => { setToDate(e.target.value); setPage(0); }}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="in_progress">In Progress</option>
                </select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Transfer Tier</label>
                <select
                  value={tierFilter}
                  onChange={(e) => { setTierFilter(e.target.value); setPage(0); }}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                >
                  <option value="all">All Tiers</option>
                  <option value="high">High ($35K+)</option>
                  <option value="mid">Mid ($10K-$35K)</option>
                  <option value="low">Low (&lt;$10K)</option>
                </select>
              </div>
              {agents.length > 1 && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Agent</label>
                  <select
                    value={agentFilter}
                    onChange={(e) => { setAgentFilter(e.target.value); setPage(0); }}
                    className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  >
                    <option value="">All Agents</option>
                    {agents.map(agent => (
                      <option key={agent.id} value={agent.id}>{agent.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">{hasActiveFilters ? "Filtered results" : "All calls"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Transferred</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.successful_transfers || 0}</div>
            <p className="text-xs text-muted-foreground">{stats?.transfer_rate || 0}% rate</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Duration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_duration_minutes.toLocaleString() || 0} min</div>
            <p className="text-xs text-muted-foreground">Voice minutes</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">DNC Flagged</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.dnc_count || 0}</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>
      </div>

      {/* Call Records Table */}
      <Card>
        <CardHeader>
          <CardTitle>Call Records</CardTitle>
          <CardDescription>
            Page {page + 1} of {Math.ceil(total / limit) || 1} • {total} total calls
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading calls...</p>
            </div>
          ) : filteredCalls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <p className="text-muted-foreground mb-2">No calls found</p>
              <p className="text-sm text-muted-foreground">Try adjusting your filters</p>
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {filteredCalls.map(call => (
                  <div
                    key={call.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => handleSelectCall(call)}
                  >
                    <div className="space-y-1 min-w-[200px]">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{call.lead_name || "Unknown"}</p>
                        {call.transfer_tier && call.transfer_tier !== "none" && (
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getTierColor(call.transfer_tier)}`}>
                            {getTierLabel(call.transfer_tier)}
                          </span>
                        )}
                        {call.is_dnc_flagged && (
                          <Badge variant="destructive" size="sm">DNC</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground font-mono">{call.from_number}</p>
                      <p className="text-xs text-muted-foreground">
                        {call.disconnection_reason === "transferred" ? "Transferred successfully" :
                         call.disconnection_reason === "caller_hangup" ? "Caller hung up" :
                         call.disconnection_reason === "dnc_detected" ? "DNC detected" :
                         call.disconnection_reason === "no_answer" ? "No answer" :
                         call.disconnection_reason || "Unknown"}
                        {call.total_debt > 0 && ` • $${call.total_debt.toLocaleString()} total debt`}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      {call.recording_url && (
                        <AudioPlayer audioSrc={call.recording_url} className="w-32" />
                      )}
                      <div className="text-right min-w-[100px]">
                        <p className="text-sm font-medium">{call.duration_formatted}</p>
                        <p className="text-xs text-muted-foreground">
                          {call.call_started_at 
                            ? new Date(call.call_started_at).toLocaleString() 
                            : new Date(call.created_at).toLocaleString()}
                        </p>
                      </div>
                      <Badge
                        variant={
                          call.transfer_success ? "success" :
                          call.is_dnc_flagged ? "destructive" :
                          call.status === "completed" ? "secondary" :
                          "outline"
                        }
                      >
                        {call.transfer_success ? "Transferred" : call.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between pt-6">
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
            </>
          )}
        </CardContent>
      </Card>

      {/* Call Details Panel */}
      {selectedCall && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  Call Details
                  {loadingDetails && <span className="text-sm font-normal text-muted-foreground">(Loading...)</span>}
                </CardTitle>
                <CardDescription>
                  {selectedCall.lead_name || "Unknown"} • {selectedCall.from_number}
                </CardDescription>
              </div>
              <Button variant="outline" onClick={() => { setSelectedCall(null); setCallTranscript(null); }}>Close</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Call Info */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Call Information</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Call ID:</span>
                    <span className="font-mono text-xs">{selectedCall.call_sid}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">From:</span>
                    <span>{selectedCall.from_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">To:</span>
                    <span>{selectedCall.to_number}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Duration:</span>
                    <span>{selectedCall.duration_formatted}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant={selectedCall.transfer_success ? "success" : "secondary"}>
                      {selectedCall.transfer_success ? "Transferred" : selectedCall.status}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Disconnect Reason:</span>
                    <span>{selectedCall.disconnection_reason}</span>
                  </div>
                </div>
              </div>

              {/* Intake Data */}
              <div className="space-y-4">
                <h4 className="text-sm font-medium">Intake Data</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Lead Name:</span>
                    <span>{selectedCall.lead_name || "Not collected"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Total Debt:</span>
                    <span className="font-medium">${selectedCall.total_debt?.toLocaleString() || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Transfer Tier:</span>
                    {selectedCall.transfer_tier && selectedCall.transfer_tier !== "none" ? (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getTierColor(selectedCall.transfer_tier)}`}>
                        {getTierLabel(selectedCall.transfer_tier)}
                      </span>
                    ) : (
                      <span>N/A</span>
                    )}
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">DNC Flagged:</span>
                    <span>{selectedCall.is_dnc_flagged ? <Badge variant="destructive" size="sm">Yes</Badge> : "No"}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Recording */}
            {selectedCall.recording_url && (
              <div className="mt-6 space-y-2">
                <h4 className="text-sm font-medium">Recording</h4>
                <AudioPlayer audioSrc={selectedCall.recording_url} />
              </div>
            )}

            {/* Transcript with Keyword Highlighting */}
            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <h4 className="text-sm font-medium">Transcript</h4>
              </div>
              <TranscriptViewer 
                transcript={callTranscript || selectedCall.transcript}
                showLegend={true}
              />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
