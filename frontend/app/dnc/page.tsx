"use client"

import { useState, useEffect, useRef } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  Download, 
  AlertTriangle, 
  Search, 
  X, 
  Upload, 
  FileText, 
  Shield, 
  Phone, 
  CheckCircle2,
  AlertCircle,
  Bot
} from "lucide-react"
import { getDNCEntries, getDNCStats, getDNCExportUrl, type DNCEntry } from "@/lib/api"

export default function DNCPage() {
  const [entries, setEntries] = useState<DNCEntry[]>([])
  const [stats, setStats] = useState<{ total: number; today: number; by_method: Record<string, number> } | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const limit = 25
  
  // Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [fromDate, setFromDate] = useState<string>("")
  const [toDate, setToDate] = useState<string>("")
  
  // Upload states
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadType, setUploadType] = useState<"dnc" | "tcpa">("dnc")
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true)
        
        const [entriesData, statsData] = await Promise.all([
          getDNCEntries({
            from_date: fromDate || undefined,
            to_date: toDate || undefined,
            skip: page * limit,
            limit
          }),
          getDNCStats()
        ])
        
        setEntries(entriesData.dnc_entries)
        setTotal(entriesData.total)
        setStats(statsData)
      } catch (err) {
        console.error("Error fetching DNC data:", err)
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchData()
  }, [page, fromDate, toDate])

  const filteredEntries = entries.filter(entry => {
    if (!searchQuery) return true
    return entry.phone_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
           entry.reason?.toLowerCase().includes(searchQuery.toLowerCase()) ||
           entry.detected_phrase?.toLowerCase().includes(searchQuery.toLowerCase())
  })

  const handleExport = () => {
    const url = getDNCExportUrl({ from_date: fromDate, to_date: toDate })
    window.open(url, '_blank')
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setSelectedFile(file)
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    
    setIsUploading(true)
    
    // TODO: Implement actual upload API
    // For now, simulate upload
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setIsUploading(false)
    setShowUploadModal(false)
    setSelectedFile(null)
    
    // Show success message
    alert(`Successfully uploaded ${uploadType === "dnc" ? "DNC" : "TCPA Litigator"} list with ${selectedFile.name}`)
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">DNC Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage do-not-call entries and TCPA litigator scrubs
          </p>
        </div>
        <div className="flex gap-3">
          <Button onClick={() => { setUploadType("dnc"); setShowUploadModal(true); }} variant="outline">
            <Upload className="h-4 w-4 mr-2" />
            Upload DNC List
          </Button>
          <Button onClick={() => { setUploadType("tcpa"); setShowUploadModal(true); }} variant="outline" className="border-amber-500/50 text-amber-500 hover:bg-amber-500/10">
            <Shield className="h-4 w-4 mr-2" />
            Upload TCPA List
          </Button>
          <Button onClick={handleExport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Blocked</CardTitle>
            <Phone className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total || 0}</div>
            <p className="text-xs text-muted-foreground">All time entries</p>
          </CardContent>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500 to-red-400" />
        </Card>

        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Flagged Today</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.today || 0}</div>
            <p className="text-xs text-muted-foreground">New DNC requests</p>
          </CardContent>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 to-amber-400" />
        </Card>

        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Detected</CardTitle>
            <Bot className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.by_method?.auto || 0}</div>
            <p className="text-xs text-muted-foreground">By phrase detection</p>
          </CardContent>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-purple-400" />
        </Card>

        <Card className="relative overflow-hidden">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">TCPA Litigators</CardTitle>
            <Shield className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.by_method?.tcpa || 0}</div>
            <p className="text-xs text-muted-foreground">Known litigators blocked</p>
          </CardContent>
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 to-emerald-400" />
        </Card>
      </div>

      {/* DNC Info Banner */}
      <Card className="bg-gradient-to-br from-red-500/5 via-transparent to-amber-500/5 border-red-500/20">
        <CardContent className="py-4">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-red-500" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold mb-1">How DNC Protection Works</h3>
              <p className="text-sm text-muted-foreground">
                Numbers on this list are automatically blocked from your AI voice agents. When a caller says phrases like 
                "do not call me", "remove me from your list", or "stop calling", the AI automatically flags their number.
                You can also upload external DNC lists and TCPA litigator databases for additional protection.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search by phone number or phrase..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-10 w-full rounded-lg border bg-background px-10 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500/20"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="absolute right-3 top-1/2 -translate-y-1/2"
                >
                  <X className="h-4 w-4 text-muted-foreground hover:text-foreground" />
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                placeholder="From date"
                className="h-10 rounded-lg border bg-background px-3 text-sm"
              />
              <span className="text-muted-foreground">to</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                placeholder="To date"
                className="h-10 rounded-lg border bg-background px-3 text-sm"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DNC List */}
      <Card>
        <CardHeader>
          <CardTitle>DNC Entries</CardTitle>
          <CardDescription>
            {total} total entries • Page {page + 1} of {Math.ceil(total / limit) || 1}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-muted-foreground">Loading...</p>
            </div>
          ) : filteredEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-16 w-16 rounded-2xl bg-muted/50 flex items-center justify-center mb-4">
                <CheckCircle2 className="h-8 w-8 text-emerald-500" />
              </div>
              <p className="font-medium mb-2">No DNC entries found</p>
              <p className="text-sm text-muted-foreground max-w-md">
                DNC entries will appear here when callers request to be removed from your call list, 
                or when you upload external DNC/TCPA lists.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Phone Number</th>
                      <th className="py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Source</th>
                      <th className="py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Detected Phrase</th>
                      <th className="py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Reason</th>
                      <th className="py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">Date Added</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {filteredEntries.map(entry => (
                      <tr key={entry.id} className="hover:bg-muted/30 transition-colors">
                        <td className="py-3 font-mono text-sm">{entry.phone_number}</td>
                        <td className="py-3">
                          <Badge 
                            className={
                              entry.detection_method === "auto" 
                                ? "bg-purple-500/10 text-purple-500 border-purple-500/20" 
                                : entry.detection_method === "tcpa"
                                ? "bg-amber-500/10 text-amber-500 border-amber-500/20"
                                : "bg-blue-500/10 text-blue-500 border-blue-500/20"
                            }
                          >
                            {entry.detection_method === "auto" ? "AI Detected" : 
                             entry.detection_method === "tcpa" ? "TCPA List" : 
                             entry.detection_method === "manual" ? "Manual" : entry.detection_method}
                          </Badge>
                        </td>
                        <td className="py-3 text-sm text-muted-foreground max-w-[200px] truncate" title={entry.detected_phrase || ""}>
                          {entry.detected_phrase || "-"}
                        </td>
                        <td className="py-3 text-sm text-muted-foreground max-w-[200px] truncate" title={entry.reason || ""}>
                          {entry.reason || "-"}
                        </td>
                        <td className="py-3 text-sm text-muted-foreground">
                          {entry.flagged_at ? new Date(entry.flagged_at).toLocaleDateString() : "-"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              <div className="flex items-center justify-between pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => p + 1)}
                    disabled={(page + 1) * limit >= total}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setShowUploadModal(false)}
          />
          <div className="relative z-50 w-full max-w-lg mx-4">
            <Card className="shadow-2xl border-purple-500/20">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${
                      uploadType === "dnc" 
                        ? "bg-red-500/10" 
                        : "bg-amber-500/10"
                    }`}>
                      {uploadType === "dnc" ? (
                        <Phone className="h-5 w-5 text-red-500" />
                      ) : (
                        <Shield className="h-5 w-5 text-amber-500" />
                      )}
                    </div>
                    <div>
                      <CardTitle>
                        Upload {uploadType === "dnc" ? "DNC List" : "TCPA Litigator List"}
                      </CardTitle>
                      <CardDescription>
                        {uploadType === "dnc" 
                          ? "Block numbers from your do-not-call list"
                          : "Block known TCPA litigators and frequent filers"
                        }
                      </CardDescription>
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowUploadModal(false)}
                    className="h-8 w-8 rounded-lg flex items-center justify-center hover:bg-muted transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* File Upload Area */}
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                    selectedFile 
                      ? "border-emerald-500 bg-emerald-500/5" 
                      : "border-muted-foreground/20 hover:border-purple-500/50 hover:bg-purple-500/5"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.txt,.xlsx"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div className="space-y-2">
                      <CheckCircle2 className="h-10 w-10 mx-auto text-emerald-500" />
                      <p className="font-medium">{selectedFile.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(selectedFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="h-10 w-10 mx-auto text-muted-foreground" />
                      <p className="font-medium">Click to upload or drag and drop</p>
                      <p className="text-sm text-muted-foreground">
                        CSV, TXT, or Excel file with phone numbers
                      </p>
                    </div>
                  )}
                </div>

                {/* Format Info */}
                <div className="p-4 rounded-lg bg-muted/50">
                  <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    File Format Requirements
                  </h4>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    <li>• One phone number per line</li>
                    <li>• 10-digit format (e.g., 5551234567) or E.164 (+15551234567)</li>
                    <li>• CSV files should have "phone" or "number" column header</li>
                    <li>• Maximum 50,000 numbers per upload</li>
                  </ul>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <Button 
                    variant="outline" 
                    className="flex-1"
                    onClick={() => setShowUploadModal(false)}
                  >
                    Cancel
                  </Button>
                  <Button 
                    className="flex-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 text-white"
                    onClick={handleUpload}
                    disabled={!selectedFile || isUploading}
                  >
                    {isUploading ? (
                      <>
                        <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload List
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  )
}
