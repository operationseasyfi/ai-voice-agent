"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Phone, Edit2, Check, X } from "lucide-react"
import { getPhoneNumbers, updatePhoneNumber, type PhoneNumber } from "@/lib/api"

export default function PhoneNumbersPage() {
  const [phoneNumbers, setPhoneNumbers] = useState<PhoneNumber[]>([])
  const [grouped, setGrouped] = useState<Record<string, PhoneNumber[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editDescription, setEditDescription] = useState("")

  useEffect(() => {
    fetchPhoneNumbers()
  }, [])

  async function fetchPhoneNumbers() {
    try {
      setIsLoading(true)
      const data = await getPhoneNumbers()
      setPhoneNumbers(data.phone_numbers)
      setGrouped(data.grouped)
    } catch (err) {
      console.error("Error fetching phone numbers:", err)
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSaveDescription(numberId: string) {
    try {
      await updatePhoneNumber(numberId, { description: editDescription })
      setEditingId(null)
      fetchPhoneNumbers()
    } catch (err) {
      console.error("Error updating phone number:", err)
    }
  }

  const typeColors: Record<string, string> = {
    ai_inbound: "bg-blue-500",
    transfer_high: "bg-green-500",
    transfer_mid: "bg-amber-500",
    transfer_low: "bg-orange-500",
    outbound: "bg-purple-500"
  }

  const typeLabels: Record<string, string> = {
    ai_inbound: "AI Inbound",
    transfer_high: "Transfer ($35K+)",
    transfer_mid: "Transfer ($10K-$35K)",
    transfer_low: "Transfer (<$10K)",
    outbound: "Outbound"
  }

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Phone Numbers</h1>
        <p className="text-muted-foreground">
          Manage your AI inbound and transfer destination numbers
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        {Object.entries(typeLabels).map(([type, label]) => (
          <Card key={type}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{label}</CardTitle>
              <div className={`h-3 w-3 rounded-full ${typeColors[type]}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {grouped[type]?.length || 0}
              </div>
              <p className="text-xs text-muted-foreground">numbers</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Phone Numbers by Type */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12">
            <div className="flex items-center justify-center">
              <p className="text-muted-foreground">Loading phone numbers...</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* AI Inbound Numbers */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className={`h-4 w-4 rounded-full ${typeColors.ai_inbound}`} />
                <div>
                  <CardTitle>AI Inbound Numbers</CardTitle>
                  <CardDescription>Numbers that connect to your AI voice agents</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {grouped.ai_inbound?.length > 0 ? (
                <div className="space-y-4">
                  {grouped.ai_inbound.map(number => (
                    <PhoneNumberRow
                      key={number.id}
                      number={number}
                      isEditing={editingId === number.id}
                      editDescription={editDescription}
                      onEdit={() => {
                        setEditingId(number.id)
                        setEditDescription(number.description || "")
                      }}
                      onCancel={() => setEditingId(null)}
                      onSave={() => handleSaveDescription(number.id)}
                      onDescriptionChange={setEditDescription}
                    />
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-center py-4">No AI inbound numbers configured</p>
              )}
            </CardContent>
          </Card>

          {/* Transfer Numbers */}
          <Card>
            <CardHeader>
              <CardTitle>Transfer Destination Numbers</CardTitle>
              <CardDescription>Queue numbers where calls are transferred based on debt tier</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* High Tier */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className={`h-3 w-3 rounded-full ${typeColors.transfer_high}`} />
                    <span className="font-medium">High Tier ($35,000+)</span>
                    <Badge variant="success" size="sm">Premium Queue</Badge>
                  </div>
                  {grouped.transfer_high?.length > 0 ? (
                    <div className="space-y-2 pl-5">
                      {grouped.transfer_high.map(number => (
                        <PhoneNumberRow
                          key={number.id}
                          number={number}
                          isEditing={editingId === number.id}
                          editDescription={editDescription}
                          onEdit={() => {
                            setEditingId(number.id)
                            setEditDescription(number.description || "")
                          }}
                          onCancel={() => setEditingId(null)}
                          onSave={() => handleSaveDescription(number.id)}
                          onDescriptionChange={setEditDescription}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm pl-5">No numbers configured for this tier</p>
                  )}
                </div>

                {/* Mid Tier */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className={`h-3 w-3 rounded-full ${typeColors.transfer_mid}`} />
                    <span className="font-medium">Mid Tier ($10,000 - $34,999)</span>
                    <Badge variant="secondary" size="sm">Standard Queue</Badge>
                  </div>
                  {grouped.transfer_mid?.length > 0 ? (
                    <div className="space-y-2 pl-5">
                      {grouped.transfer_mid.map(number => (
                        <PhoneNumberRow
                          key={number.id}
                          number={number}
                          isEditing={editingId === number.id}
                          editDescription={editDescription}
                          onEdit={() => {
                            setEditingId(number.id)
                            setEditDescription(number.description || "")
                          }}
                          onCancel={() => setEditingId(null)}
                          onSave={() => handleSaveDescription(number.id)}
                          onDescriptionChange={setEditDescription}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm pl-5">No numbers configured for this tier</p>
                  )}
                </div>

                {/* Low Tier */}
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <div className={`h-3 w-3 rounded-full ${typeColors.transfer_low}`} />
                    <span className="font-medium">Low Tier (Under $10,000)</span>
                    <Badge variant="outline" size="sm">Entry Queue</Badge>
                  </div>
                  {grouped.transfer_low?.length > 0 ? (
                    <div className="space-y-2 pl-5">
                      {grouped.transfer_low.map(number => (
                        <PhoneNumberRow
                          key={number.id}
                          number={number}
                          isEditing={editingId === number.id}
                          editDescription={editDescription}
                          onEdit={() => {
                            setEditingId(number.id)
                            setEditDescription(number.description || "")
                          }}
                          onCancel={() => setEditingId(null)}
                          onSave={() => handleSaveDescription(number.id)}
                          onDescriptionChange={setEditDescription}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm pl-5">No numbers configured for this tier</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

// Phone Number Row Component
function PhoneNumberRow({
  number,
  isEditing,
  editDescription,
  onEdit,
  onCancel,
  onSave,
  onDescriptionChange
}: {
  number: PhoneNumber
  isEditing: boolean
  editDescription: string
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  onDescriptionChange: (value: string) => void
}) {
  return (
    <div className="flex items-center justify-between p-3 border rounded-lg">
      <div className="flex items-center gap-4">
        <Phone className="h-4 w-4 text-muted-foreground" />
        <div>
          <p className="font-mono font-medium">{number.formatted_number}</p>
          {isEditing ? (
            <input
              type="text"
              value={editDescription}
              onChange={(e) => onDescriptionChange(e.target.value)}
              placeholder="Add description..."
              className="text-sm text-muted-foreground bg-transparent border-b border-primary focus:outline-none mt-1"
              autoFocus
            />
          ) : (
            <p className="text-sm text-muted-foreground">
              {number.description || number.friendly_name || "No description"}
            </p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-2">
        {number.last_used_at && (
          <span className="text-xs text-muted-foreground">
            Last used: {new Date(number.last_used_at).toLocaleDateString()}
          </span>
        )}
        <Badge variant={number.is_active ? "success" : "secondary"} size="sm">
          {number.is_active ? "Active" : "Inactive"}
        </Badge>
        {isEditing ? (
          <>
            <Button variant="ghost" size="sm" onClick={onSave}>
              <Check className="h-4 w-4 text-green-500" />
            </Button>
            <Button variant="ghost" size="sm" onClick={onCancel}>
              <X className="h-4 w-4 text-red-500" />
            </Button>
          </>
        ) : (
          <Button variant="ghost" size="sm" onClick={onEdit}>
            <Edit2 className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
