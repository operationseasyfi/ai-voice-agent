"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { User, Building, Bell, Shield, Camera } from "lucide-react"

type Tab = "general" | "account" | "notifications" | "security"

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>("general")
  const [userName, setUserName] = useState({ first: "Admin", last: "User" })
  const [email, setEmail] = useState("admin@easyfinance.ai")
  const [workspaceName, setWorkspaceName] = useState("Main Workspace")

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user')
      if (user) {
        try {
          const parsed = JSON.parse(user)
          const names = (parsed.full_name || "Admin User").split(' ')
          setUserName({ first: names[0] || "Admin", last: names.slice(1).join(' ') || "User" })
          setEmail(parsed.email || "admin@easyfinance.ai")
        } catch {}
      }
    }
  }, [])

  const tabs = [
    { id: "general" as Tab, label: "General", icon: User },
    { id: "account" as Tab, label: "Account", icon: Building },
    { id: "notifications" as Tab, label: "Notifications", icon: Bell },
    { id: "security" as Tab, label: "Security", icon: Shield },
  ]

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="page-title">Settings</h1>
        <p className="page-description">Manage your account settings and preferences.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors relative ${
                activeTab === tab.id 
                  ? 'text-foreground' 
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
              {activeTab === tab.id && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
              )}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {activeTab === "general" && (
        <div className="space-y-6">
          {/* Profile Information */}
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-base font-medium">Profile Information</CardTitle>
              <p className="text-sm text-muted-foreground">Update your profile details and public information.</p>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-4">
              {/* Avatar */}
              <div className="flex items-center gap-4">
                <div className="h-20 w-20 bg-secondary border border-border flex items-center justify-center overflow-hidden">
                  <div className="h-full w-full bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center text-2xl font-bold text-white">
                    {userName.first[0]}{userName.last[0]}
                  </div>
                </div>
                <button className="btn-secondary text-sm">Change Avatar</button>
              </div>

              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">First name</label>
                  <input
                    type="text"
                    value={userName.first}
                    onChange={(e) => setUserName({ ...userName, first: e.target.value })}
                    className="w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Last name</label>
                  <input
                    type="text"
                    value={userName.last}
                    onChange={(e) => setUserName({ ...userName, last: e.target.value })}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Email */}
              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full"
                />
              </div>

              {/* Bio */}
              <div>
                <label className="block text-sm font-medium mb-2">Bio</label>
                <textarea
                  placeholder="Tell us about yourself"
                  rows={3}
                  className="w-full resize-none"
                />
              </div>
            </CardContent>
          </Card>

          {/* Workspace Settings */}
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-base font-medium">Workspace</CardTitle>
              <p className="text-sm text-muted-foreground">Manage workspace settings.</p>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <div>
                <label className="block text-sm font-medium mb-2">Workspace Name</label>
                <input
                  type="text"
                  value={workspaceName}
                  onChange={(e) => setWorkspaceName(e.target.value)}
                  className="w-full"
                />
              </div>
            </CardContent>
          </Card>

          {/* Save Button */}
          <div className="flex justify-end">
            <button className="btn-primary">Save Changes</button>
          </div>
        </div>
      )}

      {activeTab === "account" && (
        <Card>
          <CardContent className="p-6">
            <p className="text-muted-foreground">Account settings coming soon.</p>
          </CardContent>
        </Card>
      )}

      {activeTab === "notifications" && (
        <Card>
          <CardHeader className="p-4 pb-2">
            <CardTitle className="text-base font-medium">Notification Preferences</CardTitle>
            <p className="text-sm text-muted-foreground">Configure how you receive notifications.</p>
          </CardHeader>
          <CardContent className="p-4 pt-0 space-y-4">
            {[
              { label: "Email notifications for new transfers", enabled: true },
              { label: "Email notifications for DNC detections", enabled: true },
              { label: "Daily summary email", enabled: false },
              { label: "Weekly analytics report", enabled: true },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                <span className="text-sm">{item.label}</span>
                <button className={`h-6 w-11 rounded-full transition-colors ${
                  item.enabled ? 'bg-primary' : 'bg-secondary'
                }`}>
                  <div className={`h-5 w-5 rounded-full bg-white transition-transform ${
                    item.enabled ? 'translate-x-5' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {activeTab === "security" && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-base font-medium">Change Password</CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-0 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Current Password</label>
                <input type="password" className="w-full" placeholder="••••••••" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">New Password</label>
                <input type="password" className="w-full" placeholder="••••••••" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Confirm New Password</label>
                <input type="password" className="w-full" placeholder="••••••••" />
              </div>
              <button className="btn-primary">Update Password</button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="p-4 pb-2">
              <CardTitle className="text-base font-medium">Two-Factor Authentication</CardTitle>
              <p className="text-sm text-muted-foreground">Add an extra layer of security to your account.</p>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              <button className="btn-secondary">Enable 2FA</button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
