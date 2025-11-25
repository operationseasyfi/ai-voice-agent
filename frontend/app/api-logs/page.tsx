import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { JsonViewer } from "@/components/ui/json-viewer"

export default function CRMAPILogsPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">CRM API Logs</h1>
          <p className="text-muted-foreground">
            Monitor API requests and responses from your CRM integration
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">Refresh</Button>
          <Button variant="outline">Export Logs</Button>
        </div>
      </div>

       {/* Statistics */}
      <div className="grid gap-6 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">98.5%</div>
            <p className="text-xs text-muted-foreground">1,216 successful</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Errors</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">18</div>
            <p className="text-xs text-muted-foreground">Requires attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">142ms</div>
            <p className="text-xs text-muted-foreground">-12ms from yesterday</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Status</label>
              <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                All
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Method</label>
              <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                All
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Time Range</label>
              <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                Last 24 hours
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Search</label>
              <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                Search logs...
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* API Logs List with Inline Request/Response */}
      <div className="space-y-6">
        {[
          {
            id: 14858,
            status: 201,
            url: "https://crm.easyfinance.ai/api/v1/do_not_calls",
            timestamp: "Oct 28, 2025 13:15:17",
            request: {
              do_not_call: {
                phone_number: "+12103169152"
              }
            },
            response: {
              message: "Phone number status updated to do not call"
            }
          },
          {
            id: 14857,
            status: 201,
            url: "https://crm.easyfinance.ai/api/v1/leads",
            timestamp: "Oct 28, 2025 13:14:31",
            request: {
              lead: {
                email: "N/A",
                address: "63101",
                call_id: "call_84bf3c87df5145311b3722ed77",
                data_one: "1969-06-13",
                data_two: "6803",
                last_name: "Miller",
                first_name: "Brian",
                total_debt: "56086",
                car_payment: "0",
                other_debts: "14000",
                phone_number: "+15738817229",
                loan_requested: "32000",
                monthly_income: "4000",
                personal_loans: "32000",
                housing_expense: "500",
                groceries_expense: "150",
                utilities_expense: "125",
                credit_card_debt_assumption: "42000"
              },
              campaign: {
                name: "Gozuvo"
              }
            },
            response: {
              id: 3274299
            }
          },
          {
            id: 14856,
            status: 200,
            url: "https://crm.easyfinance.ai/api/v1/contacts",
            timestamp: "Oct 28, 2025 13:12:45",
            request: {
              contact: {
                name: "John Doe",
                email: "john@example.com",
                phone: "+15551234567"
              }
            },
            response: {
              id: 3274298,
              status: "active",
              created_at: "2025-10-28T13:12:45Z"
            }
          }
        ].map((log) => (
          <Card key={log.id}>
            <CardContent className="pt-6">
              {/* Log Header */}
              <div className="flex items-center justify-between mb-4 pb-3 border-b">
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      log.status >= 200 && log.status < 300
                        ? "success"
                        : log.status >= 400 && log.status < 500
                        ? "warning"
                        : "destructive"
                    }
                    size="lg"
                    dot
                  >
                    {log.status}
                  </Badge>
                  <div>
                    <p className="font-mono text-sm">{log.url}</p>
                    <p className="text-xs text-muted-foreground mt-1">{log.timestamp}</p>
                  </div>
                </div>
                <Badge variant="outline" size="sm">
                  ID: {log.id}
                </Badge>
              </div>

              {/* Request and Response */}
              <div className="grid gap-6 md:grid-cols-2">
                {/* Request Payload */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-current" />
                    <h4 className="font-semibold">Request Payload</h4>
                  </div>
                  <JsonViewer data={log.request} />
                </div>

                {/* Response Data */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="h-4 w-4 rounded-full border-2 border-current" />
                    <h4 className="font-semibold">Response Data</h4>
                  </div>
                  <JsonViewer data={log.response} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

    </div>
  )
}
