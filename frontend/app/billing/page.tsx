"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CreditCard, ExternalLink, Phone, Download } from "lucide-react"
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

  // Mock data for demonstration
  const voiceMinutes = usage?.summary?.total_minutes || 1240
  const includedMinutes = 2000
  const usagePercentage = Math.min((voiceMinutes / includedMinutes) * 100, 100)
  const estimatedCost = (voiceMinutes * 0.068).toFixed(2)

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Billing & Usage</h1>
          <p className="page-description">Manage your subscription, payment methods, and invoices.</p>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <ExternalLink className="h-4 w-4" />
          Stripe Customer Portal
        </button>
      </div>

      {/* Usage and Payment Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Current Usage */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium text-primary">Current Usage</CardTitle>
            <p className="text-sm text-muted-foreground">Billing cycle ends in 12 days</p>
          </CardHeader>
          <CardContent className="p-4 pt-0 space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-sm">
                  <Phone className="h-4 w-4 text-muted-foreground" />
                  <span>Voice Minutes</span>
                </div>
                <span className="text-sm font-medium">{voiceMinutes.toLocaleString()} / {includedMinutes.toLocaleString()}</span>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${usagePercentage}%` }}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                You have used {usagePercentage.toFixed(0)}% of your included minutes.
              </p>
            </div>
            <div className="pt-4 border-t border-border">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted-foreground">Estimated cost this month:</span>
                <span className="font-semibold">${estimatedCost}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Payment Method */}
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Payment Method</CardTitle>
            <p className="text-sm text-muted-foreground">Secured by Stripe</p>
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="flex items-center gap-4 p-4 bg-secondary/50 border border-border mb-4">
              <div className="h-10 w-14 bg-background border border-border flex items-center justify-center">
                <CreditCard className="h-5 w-5 text-muted-foreground" />
              </div>
              <div className="flex-1">
                <div className="font-medium">Visa ending in 4242</div>
                <div className="text-xs text-muted-foreground">Expires 12/24</div>
              </div>
              <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Default
              </span>
            </div>
            <div className="flex gap-2">
              <button className="flex-1 btn-secondary text-sm">Update Card</button>
              <button className="flex-1 btn-secondary text-sm">Billing Details</button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Invoice History */}
      <Card>
        <CardHeader className="p-4 pb-2">
          <CardTitle className="text-base font-medium">Invoice History</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table>
            <thead>
              <tr>
                <th>Invoice ID</th>
                <th>Date</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Download</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-muted-foreground">
                    Loading invoices...
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <>
                  {/* Mock invoices for demonstration */}
                  <tr>
                    <td className="font-medium">INV-2023-10</td>
                    <td className="text-muted-foreground">Oct 01, 2023</td>
                    <td className="text-primary font-medium">$124.50</td>
                    <td>
                      <span className="text-xs px-2 py-1 badge-completed flex items-center gap-1 w-fit">
                        Paid
                      </span>
                    </td>
                    <td>
                      <button className="p-1 text-muted-foreground hover:text-foreground">
                        <Download className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td className="font-medium">INV-2023-09</td>
                    <td className="text-muted-foreground">Sep 01, 2023</td>
                    <td className="text-primary font-medium">$98.20</td>
                    <td>
                      <span className="text-xs px-2 py-1 badge-completed flex items-center gap-1 w-fit">
                        Paid
                      </span>
                    </td>
                    <td>
                      <button className="p-1 text-muted-foreground hover:text-foreground">
                        <Download className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td className="font-medium">INV-2023-08</td>
                    <td className="text-muted-foreground">Aug 01, 2023</td>
                    <td className="text-primary font-medium">$112.00</td>
                    <td>
                      <span className="text-xs px-2 py-1 badge-completed flex items-center gap-1 w-fit">
                        Paid
                      </span>
                    </td>
                    <td>
                      <button className="p-1 text-muted-foreground hover:text-foreground">
                        <Download className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                </>
              ) : (
                invoices.map((invoice) => (
                  <tr key={invoice.id}>
                    <td className="font-medium">{invoice.id}</td>
                    <td className="text-muted-foreground">
                      {new Date(invoice.period.from_date).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' })}
                    </td>
                    <td className="text-primary font-medium">${invoice.amount?.toFixed(2) || "—"}</td>
                    <td>
                      <span className={`text-xs px-2 py-1 ${
                        invoice.status === 'paid' ? 'badge-completed' : 'badge-flagged'
                      } flex items-center gap-1 w-fit`}>
                        {invoice.status === 'paid' ? 'Paid' : invoice.status}
                      </span>
                    </td>
                    <td>
                      <button className="p-1 text-muted-foreground hover:text-foreground">
                        <Download className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
