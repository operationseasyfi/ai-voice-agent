"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { CreditCard, Clock, Phone, TrendingUp, Building, Mail, User } from "lucide-react"
import { getBillingUsage, getBillingProfile, getBillingHistory, type BillingUsage, type BillingProfile, type Invoice } from "@/lib/api"

export default function BillingPage() {
  const [usage, setUsage] = useState<BillingUsage | null>(null)
  const [profile, setProfile] = useState<BillingProfile | null>(null)
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        const [usageData, profileData, historyData] = await Promise.all([
          getBillingUsage(),
          getBillingProfile(),
          getBillingHistory()
        ])
        setUsage(usageData)
        setProfile(profileData)
        setInvoices(historyData.invoices)
      } catch (err) {
        console.error("Error fetching billing data:", err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchData()
  }, [])

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Billing</h1>
          <p className="text-muted-foreground">Manage your billing and view usage</p>
        </div>
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <p className="text-muted-foreground">Loading billing information...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Billing</h1>
        <p className="text-muted-foreground">
          View your usage and billing information
        </p>
      </div>

      {/* Billing Profile */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="h-5 w-5" />
            Billing Profile
          </CardTitle>
          <CardDescription>Your company billing information</CardDescription>
        </CardHeader>
        <CardContent>
          {profile?.has_billing_profile ? (
            <div className="grid gap-6 md:grid-cols-2">
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Building className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Company Name</p>
                    <p className="font-medium">{profile.company_name}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Billing Email</p>
                    <p className="font-medium">{profile.billing_email || "Not set"}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Contact</p>
                    <p className="font-medium">{profile.contact_name || "Not set"}</p>
                    {profile.contact_phone && (
                      <p className="text-sm text-muted-foreground">{profile.contact_phone}</p>
                    )}
                  </div>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <CreditCard className="h-4 w-4 text-muted-foreground" />
                  <div>
                    <p className="text-sm text-muted-foreground">Payment Method</p>
                    <div className="flex items-center gap-2">
                      <Badge variant={profile.payment_method?.status === "configured" ? "success" : "secondary"}>
                        {profile.payment_method?.status === "configured" ? "Configured" : "Not Set Up"}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {profile.payment_method?.message}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div>
                    <p className="text-sm text-muted-foreground">Account Status</p>
                    <Badge variant={profile.is_active ? "success" : "destructive"}>
                      {profile.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-muted-foreground">No billing profile configured</p>
              <p className="text-sm text-muted-foreground mt-2">Contact support to set up billing</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Current Period Usage */}
      <Card>
        <CardHeader>
          <CardTitle>Current Period Usage</CardTitle>
          <CardDescription>
            {usage?.period.from_date} to {usage?.period.to_date}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Total Calls</span>
              </div>
              <p className="text-2xl font-bold">{usage?.summary.total_calls.toLocaleString()}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Total Minutes</span>
              </div>
              <p className="text-2xl font-bold">{usage?.summary.total_minutes.toLocaleString()}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Transfers</span>
              </div>
              <p className="text-2xl font-bold">{usage?.summary.total_transfers.toLocaleString()}</p>
            </div>
            <div className="p-4 border rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Avg Duration</span>
              </div>
              <p className="text-2xl font-bold">{Math.round(usage?.summary.avg_call_duration_seconds || 0)}s</p>
            </div>
          </div>

          {/* Breakdown by Agent */}
          {usage?.breakdown_by_agent && usage.breakdown_by_agent.length > 0 && (
            <div className="mt-6">
              <h4 className="font-medium mb-4">Usage by Agent</h4>
              <div className="space-y-3">
                {usage.breakdown_by_agent.map(agent => (
                  <div key={agent.agent_id} className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="font-medium">{agent.agent_name}</span>
                    <div className="flex items-center gap-6 text-sm">
                      <span><span className="text-muted-foreground">Calls:</span> {agent.total_calls}</span>
                      <span><span className="text-muted-foreground">Minutes:</span> {agent.total_minutes}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <p className="text-sm text-muted-foreground mt-6 p-3 bg-muted/50 rounded-lg">
            {usage?.billing_note}
          </p>
        </CardContent>
      </Card>

      {/* Invoice History */}
      <Card>
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
          <CardDescription>Past billing periods</CardDescription>
        </CardHeader>
        <CardContent>
          {invoices.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No invoices yet</p>
          ) : (
            <div className="space-y-3">
              {invoices.map(invoice => (
                <div key={invoice.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div>
                    <p className="font-medium">
                      {invoice.period.from_date} - {invoice.period.to_date}
                    </p>
                    <p className="text-sm text-muted-foreground">{invoice.notes}</p>
                  </div>
                  <div className="flex items-center gap-4">
                    <Badge variant={invoice.status === "paid" ? "success" : "secondary"}>
                      {invoice.status}
                    </Badge>
                    <Button variant="outline" size="sm" disabled>
                      View
                    </Button>
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
