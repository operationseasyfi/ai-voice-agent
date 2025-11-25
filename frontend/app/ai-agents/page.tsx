import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export default function AIAgentsPage() {
  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
          <p className="text-muted-foreground">
            Manage and configure your AI voice agents
          </p>
        </div>
        <Button>Create New Agent</Button>
      </div>

      {/* Agents Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <Card key={i}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle>Agent {i}</CardTitle>
                  <CardDescription>Sales Assistant</CardDescription>
                </div>
                <Badge
                  variant={i % 2 === 0 ? "success" : "secondary"}
                  dot={i % 2 === 0}
                >
                  {i % 2 === 0 ? "Active" : "Inactive"}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Phone:</span>
                  <span className="font-medium">(555) 100-000{i}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Calls Today:</span>
                  <span className="font-medium">{i * 15}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Success Rate:</span>
                  <span className="font-medium">{90 + i}%</span>
                </div>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1">
                  Edit
                </Button>
                <Button variant="outline" size="sm" className="flex-1">
                  Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Agent Configuration Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Agent Configuration</CardTitle>
          <CardDescription>
            Selected agent details and settings will be shown here
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Agent Name</label>
                <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                  Agent 1
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Voice Model</label>
                <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                  GPT-4 Voice
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Language</label>
                <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                  English (US)
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Assigned Phone</label>
                <div className="h-10 rounded-md border bg-muted/20 px-3 flex items-center text-sm text-muted-foreground">
                  (555) 100-0001
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">System Prompt</label>
              <div className="min-h-[120px] rounded-md border bg-muted/20 p-3 text-sm text-muted-foreground">
                System prompt and instructions for the AI agent will be displayed here...
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
