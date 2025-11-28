"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { AudioPlayer } from "@/components/ui/audio-player"
import { Phone, History, FileText, Users, TrendingUp, Clock, AlertTriangle, Activity, PhoneOff, DollarSign, ExternalLink } from "lucide-react"
import {
  getDashboardStats,
  getAgentsOverview,
  getCalls,
  getConcurrentCalls,
  getAgents,
  getLostTransfers,
  getPerformanceColor,
  getTierColor,
  getTierLabel,
  type DashboardStats,
  type AgentOverview,
  type CallRecord,
  type Agent,
  type LostTransfersResponse
} from "@/lib/api"

export default function DashboardPage() {
  const router = useRouter()
  
  // State
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [agentOverviews, setAgentOverviews] = useState<AgentOverview[]>([])
  const [recentCalls, setRecentCalls] = useState<CallRecord[]>([])
  const [agents, setAgents] = useState<Agent[]>([])
  const [concurrentCalls, setConcurrentCalls] = useState(0)
  const [lostTransfers, setLostTransfers] = useState<LostTransfersResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [selectedAgent, setSelectedAgent] = useState<string>("")
  const [fromDate, setFromDate] = useState<string>(new Date().toISOString().split('T')[0])
  const [toDate, setToDate] = useState<string>(new Date().toISOString().split('T')[0])

  // Navigation helper for drill-down
  const navigateToCallHistory = (filters: Record<string, string>) => {
    const params = new URLSearchParams({
      from_date: fromDate,
      to_date: toDate,
      ...filters
    })
    router.push(`/call-history?${params.toString()}`)
  }

  // Fetch data
  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        setError(null)

        const params = {
          from_date: fromDate,
          to_date: toDate,
          ...(selectedAgent && { agent_id: selectedAgent })
        }

        const [statsData, overviewData, callsData, agentsData, lostData] = await Promise.all([
          getDashboardStats(params),
          getAgentsOverview({ from_date: fromDate, to_date: toDate }),
          getCalls({ ...params, limit: 10 }),
          getAgents({ is_active: true }),
          getLostTransfers({ from_date: fromDate, to_date: toDate, limit: 5 }).catch(() => null)
        ])

        setStats(statsData)
        setAgentOverviews(overviewData.agents)
        setRecentCalls(callsData.calls)
        setAgents(agentsData.agents)
        setLostTransfers(lostData)

        // Get concurrent calls (non-blocking)
        getConcurrentCalls()
          .then(data => setConcurrentCalls(data.concurrent_calls))
          .catch(() => {})

      } catch (err) {
        console.error("Error fetching dashboard data:", err)
        setError(err instanceof Error ? err.message : "Failed to load dashboard")
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
    
    // Poll concurrent calls every 30 seconds
    const interval = setInterval(() => {
      getConcurrentCalls()
        .then(data => setConcurrentCalls(data.concurrent_calls))
        .catch(() => {})
    }, 30000)

    return () => clearInterval(interval)
  }, [fromDate, toDate, selectedAgent])

  if (error) {
    return (
      <div className="space-y-8">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 text-destructive">
              <AlertTriangle className="h-6 w-6" />
              <div>
                <p className="font-semibold">Error loading dashboard</p>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your call center metrics and recent activity
          </p>
        </div>
        
        {/* Filters */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">From:</label>
            <input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="h-9 rounded-md border bg-background px-3 text-sm"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-muted-foreground">To:</label>
            <input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="h-9 rounded-md border bg-background px-3 text-sm"
            />
          </div>
          {agents.length > 1 && (
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="h-9 rounded-md border bg-background px-3 text-sm"
            >
              <option value="">All Agents</option>
              {agents.map(agent => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Live Concurrent Calls */}
      {concurrentCalls > 0 && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-3 w-3 rounded-full bg-primary animate-pulse" />
                <span className="font-semibold">Live Concurrent Calls</span>
              </div>
              <span className="text-2xl font-bold text-primary">{concurrentCalls}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Links */}
      <div className="grid gap-4 md:grid-cols-3">
        <Link href="/phone-numbers" className="block">
          <Card className="hover:bg-muted/20 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Phone className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">Phone Numbers</p>
                  <p className="text-sm text-muted-foreground">Manage AI & transfer numbers</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/call-history" className="block">
          <Card className="hover:bg-muted/20 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <History className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">Call History</p>
                  <p className="text-sm text-muted-foreground">View recordings & transcripts</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link href="/dnc" className="block">
          <Card className="hover:bg-muted/20 transition-colors cursor-pointer">
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                  <FileText className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">DNC List</p>
                  <p className="text-sm text-muted-foreground">Manage do-not-call entries</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Stats Cards - Color coded and clickable for drill-down */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors group"
          onClick={() => navigateToCallHistory({})}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Calls</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats ? getPerformanceColor(stats.total_calls, { good: 50, warning: 20 }) : ''}`}>
              {isLoading ? "..." : stats?.total_calls.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              {fromDate === toDate ? "Today" : `${fromDate} to ${toDate}`}
            </p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors group"
          onClick={() => navigateToCallHistory({ disconnection_reason: 'transferred' })}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Successful Transfers</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats ? getPerformanceColor(stats.transfer_rate, { good: 30, warning: 15 }) : ''}`}>
              {isLoading ? "..." : stats?.successful_transfers.toLocaleString()}
            </div>
            <p className={`text-xs ${stats ? getPerformanceColor(stats.transfer_rate, { good: 30, warning: 15 }) : 'text-muted-foreground'}`}>
              {stats?.transfer_rate}% transfer rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Duration</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-primary">
              {isLoading ? "..." : `${stats?.total_duration_minutes.toLocaleString()} min`}
            </div>
            <p className="text-xs text-muted-foreground">
              Voice AI minutes
            </p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors group"
          onClick={() => navigateToCallHistory({})}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats ? getPerformanceColor(stats.avg_duration_seconds, { good: 120, warning: 60 }) : ''}`}>
              {isLoading ? "..." : stats?.avg_duration_formatted}
            </div>
            <p className="text-xs text-muted-foreground">
              Per call average
            </p>
          </CardContent>
        </Card>

        <Card 
          className="cursor-pointer hover:bg-muted/50 transition-colors group"
          onClick={() => navigateToCallHistory({ is_dnc: 'true' })}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">DNC Detected</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${stats && stats.dnc_count > 5 ? 'text-red-600 dark:text-red-400' : stats && stats.dnc_count > 0 ? 'text-amber-600 dark:text-amber-400' : 'text-green-600 dark:text-green-400'}`}>
              {isLoading ? "..." : stats?.dnc_count}
            </div>
            <p className="text-xs text-muted-foreground">
              Click to view DNC calls
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Lost Transfers Alert - High Priority */}
      {lostTransfers && lostTransfers.total_lost > 0 && (
        <Card className="border-red-500/50 bg-red-500/5">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <PhoneOff className="h-5 w-5 text-red-500" />
                <CardTitle className="text-red-600 dark:text-red-400">Lost Transfers Alert</CardTitle>
              </div>
              <Badge variant="destructive" className="text-lg px-3 py-1">
                {lostTransfers.total_lost} Lost
              </Badge>
            </div>
            <CardDescription>
              Qualified calls where no closer answered - missed revenue opportunities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div className="flex items-center justify-between p-3 rounded-lg bg-red-500/10">
                <div>
                  <p className="text-sm font-medium">Estimated Lost Revenue</p>
                  <p className="text-xs text-muted-foreground">Based on tier values</p>
                </div>
                <div className="flex items-center gap-1 text-red-600 dark:text-red-400">
                  <DollarSign className="h-5 w-5" />
                  <span className="text-2xl font-bold">{lostTransfers.estimated_lost_revenue.toLocaleString()}</span>
                </div>
              </div>
              <div className={`flex items-center justify-between p-3 rounded-lg border ${getTierColor('high')}`}>
                <div>
                  <p className="text-sm font-medium">High Tier</p>
                  <p className="text-xs text-muted-foreground">$35K+ debt</p>
                </div>
                <span className="text-2xl font-bold">{lostTransfers.by_tier.high}</span>
              </div>
              <div className={`flex items-center justify-between p-3 rounded-lg border ${getTierColor('mid')}`}>
                <div>
                  <p className="text-sm font-medium">Mid Tier</p>
                  <p className="text-xs text-muted-foreground">$10K-$35K debt</p>
                </div>
                <span className="text-2xl font-bold">{lostTransfers.by_tier.mid}</span>
              </div>
              <div className={`flex items-center justify-between p-3 rounded-lg border ${getTierColor('low')}`}>
                <div>
                  <p className="text-sm font-medium">Low Tier</p>
                  <p className="text-xs text-muted-foreground">&lt;$10K debt</p>
                </div>
                <span className="text-2xl font-bold">{lostTransfers.by_tier.low}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Transfer Tiers Breakdown - Color coded & clickable */}
      {stats && (stats.calls_by_tier.high > 0 || stats.calls_by_tier.mid > 0 || stats.calls_by_tier.low > 0) && (
        <Card>
          <CardHeader>
            <CardTitle>Transfers by Tier</CardTitle>
            <CardDescription>Click any tier to view those calls</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-3">
              <div 
                className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer hover:opacity-80 transition-opacity ${getTierColor('high')}`}
                onClick={() => navigateToCallHistory({ transfer_tier: 'high' })}
              >
                <div>
                  <p className="text-sm font-medium">High Tier ($35K+)</p>
                  <p className="text-xs opacity-75">Premium queue</p>
                </div>
                <span className="text-2xl font-bold">{stats.calls_by_tier.high}</span>
              </div>
              <div 
                className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer hover:opacity-80 transition-opacity ${getTierColor('mid')}`}
                onClick={() => navigateToCallHistory({ transfer_tier: 'mid' })}
              >
                <div>
                  <p className="text-sm font-medium">Mid Tier ($10K-$35K)</p>
                  <p className="text-xs opacity-75">Standard queue</p>
                </div>
                <span className="text-2xl font-bold">{stats.calls_by_tier.mid}</span>
              </div>
              <div 
                className={`flex items-center justify-between p-4 rounded-lg border cursor-pointer hover:opacity-80 transition-opacity ${getTierColor('low')}`}
                onClick={() => navigateToCallHistory({ transfer_tier: 'low' })}
              >
                <div>
                  <p className="text-sm font-medium">Low Tier (&lt;$10K)</p>
                  <p className="text-xs opacity-75">Entry queue</p>
                </div>
                <span className="text-2xl font-bold">{stats.calls_by_tier.low}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Agent Overview (if multiple agents) */}
      {agentOverviews.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle>AI Agents Overview</CardTitle>
            <CardDescription>Performance breakdown by agent</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {agentOverviews.map(agent => (
                <div key={agent.id} className="p-4 rounded-lg border">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`h-2 w-2 rounded-full ${agent.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
                      <span className="font-medium">{agent.name}</span>
                    </div>
                    <Badge variant={agent.is_active ? "success" : "secondary"} size="sm">
                      {agent.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Calls</span>
                      <span className="font-medium">{agent.stats.total_calls}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Transfers</span>
                      <span className="font-medium">{agent.stats.successful_transfers}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Transfer Rate</span>
                      <span className="font-medium">{agent.stats.transfer_rate}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Duration</span>
                      <span className="font-medium">{agent.stats.total_duration_minutes} min</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Calls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Calls</CardTitle>
              <CardDescription>Latest calls from your AI agents</CardDescription>
            </div>
            <Link href="/call-history">
              <Button variant="outline" size="sm">View All</Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-muted-foreground">Loading...</p>
            </div>
          ) : recentCalls.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-muted-foreground">No calls found for this period</p>
            </div>
          ) : (
            <div className="space-y-4">
              {recentCalls.map(call => (
                <div
                  key={call.id}
                  className="flex items-center justify-between pb-4 border-b last:border-0 last:pb-0"
                >
                  <div className="space-y-1">
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
                    <p className="text-sm text-muted-foreground">{call.from_number}</p>
                    <p className="text-xs text-muted-foreground">
                      {call.disconnection_reason === "transferred" ? "Transferred" : 
                       call.disconnection_reason === "caller_hangup" ? "Caller hung up" :
                       call.disconnection_reason === "dnc_detected" ? "DNC detected" :
                       call.disconnection_reason === "no_answer" ? "No answer" :
                       call.disconnection_reason}
                      {call.total_debt > 0 && ` • $${call.total_debt.toLocaleString()} debt`}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    {call.recording_url && (
                      <AudioPlayer audioSrc={call.recording_url} className="w-32" />
                    )}
                    <div className="text-right">
                      <p className="text-sm font-medium">{call.duration_formatted}</p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(call.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <Badge
                      variant={call.transfer_success ? "success" : call.is_dnc_flagged ? "destructive" : "secondary"}
                    >
                      {call.transfer_success ? "Transferred" : call.status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
