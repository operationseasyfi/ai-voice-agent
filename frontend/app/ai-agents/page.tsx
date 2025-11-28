"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Phone, TrendingUp, Clock, PhoneCall, ArrowUpRight, Users } from "lucide-react"
import { getAgents, type Agent } from "@/lib/api"

export default function AIAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchAgents() {
      try {
        const data = await getAgents()
        setAgents(data.agents || [])
      } catch (err) {
        console.error("Error fetching agents:", err)
        // Use mock data if API fails
        setAgents([
          {
            id: "1",
            name: "Jessica - Loan Specialist",
            description: "Primary inbound agent for loan inquiries",
            voice_config: {},
            routing_config: {},
            is_active: true,
            created_at: new Date().toISOString()
          }
        ])
      } finally {
        setIsLoading(false)
      }
    }
    fetchAgents()
  }, [])

  // Stats cards data
  const statsCards = [
    { label: "Total Agents", value: agents.length, icon: Bot, color: "purple" },
    { label: "Active Agents", value: agents.filter(a => a.is_active).length, icon: Users, color: "emerald" },
    { label: "Calls Today", value: "0", icon: PhoneCall, color: "blue" },
    { label: "Avg. Success Rate", value: "0%", icon: TrendingUp, color: "amber" },
  ]

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
        <p className="text-muted-foreground mt-1">
          View your AI voice agents and their performance metrics
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statsCards.map((stat, i) => (
          <Card key={i} className="relative overflow-hidden">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold mt-1">{stat.value}</p>
                </div>
                <div className={`h-12 w-12 rounded-xl bg-${stat.color}-500/10 flex items-center justify-center`}>
                  <stat.icon className={`h-6 w-6 text-${stat.color}-500`} />
                </div>
              </div>
            </CardContent>
            <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-${stat.color}-500 to-${stat.color}-400`} />
          </Card>
        ))}
      </div>

      {/* Agents Grid */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Your AI Agents</h2>
        
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-6 bg-muted rounded w-3/4 mb-4" />
                  <div className="h-4 bg-muted rounded w-1/2 mb-6" />
                  <div className="space-y-3">
                    <div className="h-3 bg-muted rounded" />
                    <div className="h-3 bg-muted rounded" />
                    <div className="h-3 bg-muted rounded" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : agents.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <Bot className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Agents Configured</h3>
              <p className="text-muted-foreground">
                Contact your account manager to set up AI agents for your account.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {agents.map((agent) => (
              <Card key={agent.id} className="group hover:shadow-lg transition-all duration-300 hover:border-purple-500/30">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white shadow-lg shadow-purple-500/20">
                        <Bot className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{agent.name}</CardTitle>
                        <CardDescription className="text-xs mt-0.5">
                          {agent.description || "Voice AI Agent"}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge
                      variant={agent.is_active ? "success" : "secondary"}
                      className={agent.is_active ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : ""}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full mr-1.5 ${agent.is_active ? "bg-emerald-500" : "bg-gray-400"}`} />
                      {agent.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Stats Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <PhoneCall className="h-3.5 w-3.5" />
                        <span className="text-xs">Calls Today</span>
                      </div>
                      <p className="text-lg font-semibold">0</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <TrendingUp className="h-3.5 w-3.5" />
                        <span className="text-xs">Success Rate</span>
                      </div>
                      <p className="text-lg font-semibold">0%</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <Clock className="h-3.5 w-3.5" />
                        <span className="text-xs">Avg Duration</span>
                      </div>
                      <p className="text-lg font-semibold">0:00</p>
                    </div>
                    <div className="p-3 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-2 text-muted-foreground mb-1">
                        <ArrowUpRight className="h-3.5 w-3.5" />
                        <span className="text-xs">Transfers</span>
                      </div>
                      <p className="text-lg font-semibold">0</p>
                    </div>
                  </div>

                  {/* Agent Info */}
                  <div className="pt-3 border-t border-border/50 space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground flex items-center gap-2">
                        <Phone className="h-3.5 w-3.5" />
                        Assigned Number
                      </span>
                      <span className="font-medium text-xs bg-muted px-2 py-0.5 rounded">
                        Contact Support
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Created</span>
                      <span className="text-xs">
                        {new Date(agent.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Info Card */}
      <Card className="bg-gradient-to-br from-purple-500/5 via-transparent to-pink-500/5 border-purple-500/20">
        <CardContent className="py-6">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center flex-shrink-0">
              <Bot className="h-5 w-5 text-purple-500" />
            </div>
            <div>
              <h3 className="font-semibold mb-1">Need to modify your AI agents?</h3>
              <p className="text-sm text-muted-foreground">
                Agent configuration, voice settings, and routing rules are managed by your EasyFinance account team. 
                Contact your account manager to request changes to your AI agent setup.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
