"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Phone, Plus } from "lucide-react"
import { getPhoneNumbers, type PhoneNumber } from "@/lib/api"

export default function PhoneNumbersPage() {
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([])
  const [grouped, setGrouped] = useState<Record<string, PhoneNumber[]>>({})
  const [counts, setCounts] = useState<Record<string, number>>({})
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const data = await getPhoneNumbers()
        setPhoneNumbers(data.phone_numbers)
        setGrouped(data.grouped)
        setCounts(data.counts)
      } catch (err) {
        console.error("Error fetching phone numbers:", err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  const categories = [
    { key: "ai_inbound", label: "AI Inbound", color: "text-cyan-400", dot: "bg-cyan-500" },
    { key: "transfer_high", label: "Transfer ($35K+)", color: "text-emerald-400", dot: "bg-emerald-500" },
    { key: "transfer_mid", label: "Transfer ($10K-$35K)", color: "text-amber-400", dot: "bg-amber-500" },
    { key: "transfer_low", label: "Transfer (<$10K)", color: "text-orange-400", dot: "bg-orange-500" },
    { key: "outbound", label: "Outbound", color: "text-purple-400", dot: "bg-purple-500" },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="page-title">Phone Numbers</h1>
        <p className="page-description">Manage your AI inbound and transfer destination numbers</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        {categories.map((cat) => (
          <Card key={cat.key}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm text-muted-foreground">{cat.label}</span>
                <span className={`h-2 w-2 rounded-full ${cat.dot}`}></span>
              </div>
              <div className="text-3xl font-semibold">
                {isLoading ? "..." : counts[cat.key] || 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">numbers</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* AI Inbound Numbers Section */}
      <Card>
        <CardHeader className="p-4 pb-2">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-cyan-500"></span>
            <CardTitle className="text-base font-medium">AI Inbound Numbers</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">Numbers that connect to your AI voice agents</p>
        </CardHeader>
        <CardContent className="p-4 pt-0">
          {isLoading ? (
            <p className="text-sm text-muted-foreground py-8 text-center">Loading...</p>
          ) : (grouped.ai_inbound?.length || 0) === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">No AI inbound numbers configured</p>
          ) : (
            <div className="space-y-2">
              {grouped.ai_inbound?.map((num) => (
                <div key={num.id} className="flex items-center justify-between p-3 bg-secondary/30 border border-border">
                  <div className="flex items-center gap-3">
                    <Phone className="h-4 w-4 text-primary" />
                    <div>
                      <div className="font-medium">{num.formatted_number || num.number}</div>
                      <div className="text-xs text-muted-foreground">{num.friendly_name || "No label"}</div>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {num.total_calls} calls
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Transfer Destination Numbers Section */}
      <Card>
        <CardHeader className="p-4 pb-2">
          <CardTitle className="text-base font-medium">Transfer Destination Numbers</CardTitle>
          <p className="text-sm text-muted-foreground">Queue numbers where calls are transferred based on debt tier</p>
        </CardHeader>
        <CardContent className="p-4 pt-0 space-y-6">
          {/* High Tier */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span className="font-medium">High Tier ($35,000+)</span>
              <span className="tier-high text-xs px-2 py-0.5">Premium Queue</span>
            </div>
            {(grouped.transfer_high?.length || 0) === 0 ? (
              <p className="text-sm text-muted-foreground pl-4">No numbers configured for this tier</p>
            ) : (
              <div className="space-y-2 pl-4">
                {grouped.transfer_high?.map((num) => (
                  <div key={num.id} className="flex items-center justify-between p-3 bg-secondary/30 border border-border">
                    <div className="font-medium">{num.formatted_number || num.number}</div>
                    <div className="text-sm text-muted-foreground">{num.total_calls} calls</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Mid Tier */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="h-2 w-2 rounded-full bg-amber-500"></span>
              <span className="font-medium">Mid Tier ($10,000 - $34,999)</span>
              <span className="tier-mid text-xs px-2 py-0.5">Standard Queue</span>
            </div>
            {(grouped.transfer_mid?.length || 0) === 0 ? (
              <p className="text-sm text-muted-foreground pl-4">No numbers configured for this tier</p>
            ) : (
              <div className="space-y-2 pl-4">
                {grouped.transfer_mid?.map((num) => (
                  <div key={num.id} className="flex items-center justify-between p-3 bg-secondary/30 border border-border">
                    <div className="font-medium">{num.formatted_number || num.number}</div>
                    <div className="text-sm text-muted-foreground">{num.total_calls} calls</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Low Tier */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="h-2 w-2 rounded-full bg-orange-500"></span>
              <span className="font-medium">Low Tier (Under $10,000)</span>
              <span className="tier-low text-xs px-2 py-0.5">Entry Queue</span>
            </div>
            {(grouped.transfer_low?.length || 0) === 0 ? (
              <p className="text-sm text-muted-foreground pl-4">No numbers configured for this tier</p>
            ) : (
              <div className="space-y-2 pl-4">
                {grouped.transfer_low?.map((num) => (
                  <div key={num.id} className="flex items-center justify-between p-3 bg-secondary/30 border border-border">
                    <div className="font-medium">{num.formatted_number || num.number}</div>
                    <div className="text-sm text-muted-foreground">{num.total_calls} calls</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
