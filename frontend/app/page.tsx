"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  Phone, 
  TrendingUp, 
  Clock, 
  DollarSign,
  ShieldAlert,
  ArrowUpRight,
  Download,
  PhoneIncoming,
  PhoneOutgoing,
  CheckCircle,
  VoicemailIcon,
  PhoneForwarded,
  Ban
} from "lucide-react"
import {
  getDashboardStats,
  getCalls,
  getConcurrentCalls,
  getLostTransfers,
  type DashboardStats,
  type CallRecord,
  type LostTransfersResponse
} from "@/lib/api"

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentCalls, setRecentCalls] = useState<CallRecord[]>([])
  const [lostTransfers, setLostTransfers] = useState<LostTransfersResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0])

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const [statsData, callsData, lostData] = await Promise.all([
          getDashboardStats({ from_date: selectedDate, to_date: selectedDate }),
          getCalls({ from_date: selectedDate, to_date: selectedDate, limit: 4 }),
          getLostTransfers({ from_date: selectedDate, to_date: selectedDate, limit: 4 }).catch(() => null)
        ])
        setStats(statsData)
        setRecentCalls(callsData.calls)
        setLostTransfers(lostData)
      } catch (err) {
        console.error("Error fetching dashboard data:", err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [selectedDate])

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', { 
      month: 'long', 
      day: 'numeric', 
      year: 'numeric' 
    })
  }

  const getStatusBadge = (call: CallRecord) => {
    if (call.transfer_success) return { text: "Completed", class: "badge-completed" }
    if (call.disconnection_reason === "transferred") return { text: "Transferred", class: "badge-transferring" }
    if (call.disconnection_reason === "no_answer") return { text: "Voicemail", class: "badge-voicemail" }
    if (call.is_dnc_flagged) return { text: "DNC Blocked", class: "badge-blocked" }
    return { text: call.status || "Completed", class: "badge-completed" }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Overview</h1>
          <p className="text-sm text-primary mt-1">
            Metrics for {formatDate(selectedDate)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="px-3 py-2 text-sm"
          />
          <button className="btn-secondary flex items-center gap-2">
            <Download className="h-4 w-4" />
            Download Report
          </button>
        </div>
      </div>

      {/* Main Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Total Calls</span>
              <Phone className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.total_calls.toLocaleString() || "0"}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-primary">
              <ArrowUpRight className="h-3 w-3" />
              <span>+20.1% from yesterday</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Successful Transfers</span>
              <CheckCircle className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.successful_transfers.toLocaleString() || "0"}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-primary">
              <ArrowUpRight className="h-3 w-3" />
              <span>{stats?.transfer_rate || 0}% conversion</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Total Duration</span>
              <Clock className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : `${Math.floor((stats?.total_duration_minutes || 0) / 60)}h ${(stats?.total_duration_minutes || 0) % 60}m`}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-primary">
              <ArrowUpRight className="h-3 w-3" />
              <span>+5.2% from yesterday</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Avg Duration</span>
              <Clock className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.avg_duration_formatted || "0:00"}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-primary">
              <ArrowUpRight className="h-3 w-3" />
              <span>+12s from yesterday</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Secondary Stats Row */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">DNC Detected</span>
              <ShieldAlert className="h-4 w-4 text-destructive" />
            </div>
            <div className="text-3xl font-semibold">
              {isLoading ? "..." : stats?.dnc_count || "0"}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {stats?.total_calls ? ((stats.dnc_count / stats.total_calls) * 100).toFixed(1) : "0"}% of total calls
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-muted-foreground">Total Debt Processed</span>
              <DollarSign className="h-4 w-4 text-primary" />
            </div>
            <div className="text-3xl font-semibold">
              ${isLoading ? "..." : (lostTransfers?.estimated_lost_revenue ? (lostTransfers.estimated_lost_revenue * 10).toLocaleString() : "0")}
            </div>
            <div className="flex items-center gap-1 mt-2 text-xs text-primary">
              <ArrowUpRight className="h-3 w-3" />
              <span>+18.2% from yesterday</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-2 gap-4">
        {/* Call Volume Chart */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Call Volume</CardTitle>
            <p className="text-sm text-muted-foreground">Inbound calls vs Transfers over time.</p>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="h-[200px] flex items-end justify-between gap-1 pt-4">
              {/* Placeholder chart bars */}
              {[15, 18, 22, 28, 35, 32, 38, 42, 45, 52, 48, 55].map((height, i) => (
                <div key={i} className="flex-1 flex flex-col gap-1">
                  <div 
                    className="bg-primary/30 transition-all" 
                    style={{ height: `${height * 1.5}px` }}
                  />
                  <div 
                    className="bg-cyan-500/50" 
                    style={{ height: `${height * 0.6}px` }}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-xs text-muted-foreground">
              <span>09:00</span>
              <span>10:00</span>
              <span>11:00</span>
              <span>12:00</span>
              <span>13:00</span>
              <span>14:00</span>
              <span>15:00</span>
            </div>
          </CardContent>
        </Card>

        {/* Queue Distribution */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Queue Distribution</CardTitle>
            <p className="text-sm text-muted-foreground">High Value vs Standard</p>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="space-y-4 pt-4">
              <div className="flex items-center gap-4">
                <span className="text-sm text-muted-foreground w-16">Queue A</span>
                <div className="flex-1 h-6 bg-secondary">
                  <div className="h-full bg-cyan-500" style={{ width: '60%' }} />
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-muted-foreground w-16">Queue B</span>
                <div className="flex-1 h-6 bg-secondary">
                  <div className="h-full bg-emerald-500" style={{ width: '40%' }} />
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-6 pt-4 border-t border-border">
              <div className="text-center">
                <div className="text-xs text-cyan-400 mb-1">Queue A</div>
                <div className="text-2xl font-semibold">{stats?.calls_by_tier?.high || 0}</div>
                <div className="text-xs text-muted-foreground">High Value (&gt;35k)</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-emerald-400 mb-1">Queue B</div>
                <div className="text-2xl font-semibold">{(stats?.calls_by_tier?.mid || 0) + (stats?.calls_by_tier?.low || 0)}</div>
                <div className="text-xs text-muted-foreground">Standard (&lt;35k)</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Section */}
      <div className="grid grid-cols-2 gap-4">
        {/* Recent Calls */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Recent Calls</CardTitle>
            <p className="text-sm text-muted-foreground">Latest inbound and outbound activity.</p>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="space-y-3">
              {isLoading ? (
                <div className="text-sm text-muted-foreground text-center py-8">Loading...</div>
              ) : recentCalls.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8">No calls today</div>
              ) : (
                recentCalls.map((call) => {
                  const badge = getStatusBadge(call)
                  return (
                    <div key={call.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 bg-secondary flex items-center justify-center">
                          <PhoneIncoming className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <div className="text-sm font-medium">{call.from_number}</div>
                          <div className="text-xs text-muted-foreground">
                            Inbound • {call.duration_formatted}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs px-2 py-1 ${badge.class}`}>
                          {badge.text}
                        </span>
                        <div className="text-xs text-muted-foreground mt-1">
                          {new Date(call.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Live Transfers */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Recent Live Transfers</CardTitle>
            <p className="text-sm text-muted-foreground">Latest successful transfers to 3CX queues.</p>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="space-y-3">
              {isLoading ? (
                <div className="text-sm text-muted-foreground text-center py-8">Loading...</div>
              ) : !lostTransfers || lostTransfers.calls.length === 0 ? (
                <div className="text-sm text-muted-foreground text-center py-8">No transfers today</div>
              ) : (
                recentCalls.filter(c => c.transfer_success).slice(0, 4).map((call, i) => (
                  <div key={call.id} className="flex items-center justify-between py-2 border-b border-border/50 last:border-0">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 bg-secondary flex items-center justify-center text-xs font-medium text-primary">
                        {(call.lead_name || "U")[0].toUpperCase()}
                      </div>
                      <div>
                        <div className="text-sm font-medium">{call.lead_name || "Unknown"}</div>
                        <div className="text-xs text-muted-foreground">
                          Income: ${(call.total_debt * 0.1).toLocaleString()}/mo • {new Date(call.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-semibold text-primary">${call.total_debt?.toLocaleString() || "0"}</div>
                      <span className={`text-xs px-2 py-0.5 ${call.transfer_tier === 'high' ? 'tier-high' : 'tier-mid'}`}>
                        Queue {call.transfer_tier === 'high' ? 'A' : 'B'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
