"use client"

import { useState, useEffect } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { Wifi, Activity, Phone, Volume2, StopCircle } from "lucide-react"
import { getConcurrentCalls } from "@/lib/api"

interface ActiveCall {
  id: string
  name: string
  phone: string
  status: "GREETING" | "INTAKE" | "TRANSFERRING" | "ON_HOLD"
  duration: number
  estimatedDebt: number | null
  transcript: Array<{ role: "ai" | "caller"; text: string }>
}

// Mock data for demonstration
const mockCalls: ActiveCall[] = [
  {
    id: "1",
    name: "Sarah Williams",
    phone: "+1 (555) 123-4567",
    status: "INTAKE",
    duration: 134,
    estimatedDebt: 42500,
    transcript: [
      { role: "ai", text: "Thank you for calling EasyFinance. Could you please state your total unsecured debt amount?" },
      { role: "caller", text: "I think it's around forty two thousand dollars." },
      { role: "ai", text: "Understood. And are you currently" }
    ]
  },
  {
    id: "2",
    name: "Mike Ross",
    phone: "+1 (555) 987-6543",
    status: "TRANSFERRING",
    duration: 272,
    estimatedDebt: 12000,
    transcript: [
      { role: "ai", text: "Great, I'm connecting you to a specialist now." },
    ]
  },
  {
    id: "3",
    name: "Unknown Caller",
    phone: "+1 (555) 444-3333",
    status: "GREETING",
    duration: 12,
    estimatedDebt: null,
    transcript: [
      { role: "ai", text: "Hello! You've reached EasyFinance. Who am I speaking with?" },
    ]
  }
]

export default function LiveMonitorPage() {
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>(mockCalls)
  const [latency, setLatency] = useState(24)

  // Format duration as mm:ss
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }

  // Simulate duration updates
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCalls(calls => 
        calls.map(call => ({ ...call, duration: call.duration + 1 }))
      )
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "GREETING": return "bg-slate-500/20 text-slate-400 border border-slate-500/30"
      case "INTAKE": return "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30"
      case "TRANSFERRING": return "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
      case "ON_HOLD": return "bg-amber-500/20 text-amber-400 border border-amber-500/30"
      default: return "bg-slate-500/20 text-slate-400 border border-slate-500/30"
    }
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="page-title">Live Monitor</h1>
          <span className="status-dot online"></span>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary border border-border text-sm">
            <Wifi className="h-4 w-4 text-primary" />
            <span className="text-muted-foreground">SignalWire:</span>
            <span className="text-foreground">{latency}ms</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 bg-secondary border border-border text-sm">
            <Activity className="h-4 w-4 text-primary" />
            <span className="text-foreground">{activeCalls.length} Active Calls</span>
          </div>
        </div>
      </div>

      <p className="text-sm text-muted-foreground -mt-4">
        Monitor active calls, sentiment, and transfers in real-time.
      </p>

      {/* Active Calls Grid */}
      <div className="grid grid-cols-3 gap-4">
        {activeCalls.map((call) => (
          <Card key={call.id} className="flex flex-col">
            <CardContent className="p-4 flex-1 flex flex-col">
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-secondary flex items-center justify-center text-sm font-medium text-primary">
                    {call.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
                  </div>
                  <div>
                    <div className="font-medium">{call.name}</div>
                    <div className="text-xs text-muted-foreground">{call.phone}</div>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 ${getStatusBadge(call.status)}`}>
                  {call.status}
                </span>
              </div>

              {/* Stats Row */}
              <div className="flex items-center justify-between text-sm mb-4">
                <div className="flex items-center gap-1 text-primary">
                  <Activity className="h-3 w-3" />
                  <span>{formatDuration(call.duration)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Est. Debt:</span>
                  <span className={`ml-1 font-medium ${call.estimatedDebt ? 'text-primary' : 'text-amber-400'}`}>
                    {call.estimatedDebt ? `$${call.estimatedDebt.toLocaleString()}` : 'Pending...'}
                  </span>
                </div>
              </div>

              {/* Transcript */}
              <div className="flex-1 bg-background border border-border p-3 space-y-2 min-h-[120px] max-h-[180px] overflow-y-auto">
                {call.transcript.map((msg, i) => (
                  <div key={i} className={msg.role === 'ai' ? 'chat-ai' : 'chat-caller'}>
                    {msg.text}
                  </div>
                ))}
                {call.status === "TRANSFERRING" && (
                  <div className="text-center py-2">
                    <span className="text-xs px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      Initiating SIP Transfer to Queue B...
                    </span>
                  </div>
                )}
                {call.status !== "TRANSFERRING" && (
                  <div className="text-center">
                    <span className="text-xs text-primary">AI is listening...</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 mt-4">
                <button className="flex-1 flex items-center justify-center gap-2 py-2 bg-secondary border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/80 transition-colors">
                  <Volume2 className="h-4 w-4" />
                  Listen
                </button>
                <button className="flex-1 flex items-center justify-center gap-2 py-2 bg-secondary border border-border text-sm text-muted-foreground hover:text-foreground hover:bg-secondary/80 transition-colors">
                  <StopCircle className="h-4 w-4" />
                  End
                </button>
              </div>
            </CardContent>
          </Card>
        ))}

        {/* Empty Slot */}
        <Card className="border-dashed">
          <CardContent className="p-4 h-full flex flex-col items-center justify-center min-h-[300px]">
            <Phone className="h-8 w-8 text-muted-foreground/50 mb-3" />
            <p className="text-sm text-muted-foreground">Waiting for inbound calls...</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

