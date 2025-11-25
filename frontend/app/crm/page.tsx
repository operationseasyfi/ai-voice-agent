import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function CRMPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">CRM</h1>
          <p className="text-muted-foreground">
            Customer relationship management and contact records
          </p>
        </div>
        <Button>Add Contact</Button>
      </div>
       {/* CRM Statistics */}
      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Total Contacts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">1,234</div>
            <p className="text-xs text-muted-foreground mt-1">
              +123 this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Active Customers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">892</div>
            <p className="text-xs text-muted-foreground mt-1">
              72% of total contacts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">API Syncs Today</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">456</div>
            <p className="text-xs text-muted-foreground mt-1">
              Last sync: 5 min ago
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                Search contacts...
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline">Filters</Button>
              <Button variant="outline">Sort</Button>
              <Button variant="outline">Export</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contacts List */}
      <Card>
        <CardHeader>
          <CardTitle>Contacts</CardTitle>
          <CardDescription>
            All customer contacts and interaction history
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { name: "John Doe", company: "Acme Corp", status: "active", lastContact: "2 hours ago" },
              { name: "Jane Smith", company: "Tech Solutions", status: "active", lastContact: "5 hours ago" },
              { name: "Bob Johnson", company: "Startup Inc", status: "inactive", lastContact: "2 days ago" },
              { name: "Alice Williams", company: "Enterprise LLC", status: "active", lastContact: "1 day ago" },
              { name: "Charlie Brown", company: "Small Biz", status: "active", lastContact: "3 hours ago" },
            ].map((contact, i) => (
              <div
                key={i}
                className="flex items-center justify-between border-b pb-4 last:border-0 last:pb-0"
              >
                <div className="flex-1 space-y-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{contact.name}</p>
                    <Badge variant={contact.status === "active" ? "success" : "secondary"}>
                      {contact.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{contact.company}</p>
                </div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm font-medium">(555) 123-{4560 + i}</p>
                    <p className="text-xs text-muted-foreground">
                      Last contact: {contact.lastContact}
                    </p>
                  </div>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
