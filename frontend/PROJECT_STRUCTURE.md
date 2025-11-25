# Easy Finance - Project Structure Document

## Project Overview
**Name:** Easy Finance
**Type:** Frontend Application (Next.js + TypeScript + Tailwind CSS)
**Purpose:** Call center/telephony management system with AI agents, CRM, billing, and call tracking

---

## Tech Stack
- **Framework:** Next.js 16.0.1
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4 (custom styling)
- **UI Components:** Radix UI Primitives (unstyled, accessible components)
- **Theme:** Dark/Light mode with next-themes
- **Icons:** lucide-react
- **UI Library:** React 19.2.0
- **Future Integration:** Python Backend APIs

### Radix UI Primitives to be Used
We'll use unstyled Radix primitives and style them with Tailwind:
- `@radix-ui/react-dropdown-menu` - Navigation dropdowns, user menu
- `@radix-ui/react-dialog` - Modals and dialogs
- `@radix-ui/react-select` - Dropdowns and selects
- `@radix-ui/react-tabs` - Tab navigation
- `@radix-ui/react-switch` - Toggle switches (theme switcher)
- `@radix-ui/react-slider` - Audio player controls
- `@radix-ui/react-tooltip` - Tooltips
- `@radix-ui/react-popover` - Popovers
- `@radix-ui/react-separator` - Visual separators
- `@radix-ui/react-scroll-area` - Scrollable areas
- `@radix-ui/react-avatar` - User avatar

---

## Global Layout Patterns

### Navigation Structure
```
Top Navigation Bar:
├── Logo (LX/UX brand) - Top left
├── Main Navigation Menu (Horizontal)
│   ├── Dashboard
│   ├── Phone Numbers
│   ├── AI Agents
│   ├── CRM
│   └── Billing
└── Right Section
    ├── Notification Bell Icon
    └── User Profile Dropdown (Eyal)
```

### Color Scheme & Theme System

**Theme Support:** Light and Dark mode with automatic system preference detection

#### Light Mode Colors
- **Primary Brand:** Purple/Blue (#5B5FED or similar)
- **Success/Active:** Green (#4ADE80 or similar)
- **Warning/Alert:** Orange/Amber (#F59E0B)
- **Neutral:** Gray scales for text and backgrounds
- **Background:** Light gray (#F9FAFB)
- **Card Background:** White (#FFFFFF)
- **Text Primary:** Dark gray (#111827)
- **Text Secondary:** Medium gray (#6B7280)

#### Dark Mode Colors
- **Primary Brand:** Lighter Purple/Blue (#7C7FFA or similar)
- **Success/Active:** Green (#34D399)
- **Warning/Alert:** Orange/Amber (#FBBF24)
- **Neutral:** Gray scales for text and backgrounds
- **Background:** Dark gray (#111827)
- **Card Background:** Darker gray (#1F2937)
- **Text Primary:** White (#F9FAFB)
- **Text Secondary:** Light gray (#D1D5DB)

#### CSS Custom Properties (will be defined)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;
  --primary: 240 73% 62%;
  --primary-foreground: 210 40% 98%;
  --success: 142 76% 36%;
  --warning: 38 92% 50%;
  --border: 214.3 31.8% 91.4%;
  /* ... more variables */
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
  --card: 222.2 84% 10%;
  --card-foreground: 210 40% 98%;
  /* ... dark mode overrides */
}
```

### Common UI Components Identified

#### 1. Stat Cards
```
Structure:
├── Icon Container (Circular, colored background)
├── Label (Small text)
├── Value (Large number/text)
└── Optional: Additional info (e.g., "Avg: 9 | Highest: 36")

Variants:
- Simple (icon + label + value)
- With metadata (includes additional stats)
```

#### 2. Data Tables
```
Features:
├── Column Headers
├── Sortable columns (implied)
├── Pagination (implied)
├── Row hover states
├── Action buttons (Edit, Delete)
├── Status badges
└── Inline content (audio players, JSON viewers)

Common Columns Patterns:
- ID/Name column
- Status badges
- Date/Time stamps
- Action buttons
- Numeric values
- Phone numbers (with formatting)
```

#### 3. Badges/Pills
```
Types:
├── Status badges (Active, Published, etc.)
│   └── Green background, green text
├── Transfer status
│   └── Orange/amber background
├── Direction indicators (Inbound)
│   └── Blue background
└── Yes/No indicators
    └── Blue for Yes, Gray for No
```

#### 4. Section Containers
```
Structure:
├── White background card
├── Padding: p-6 to p-8
├── Rounded corners: rounded-lg
├── Shadow: subtle shadow
└── Optional: Header with title
```

#### 5. Audio Player
```
Components:
├── Volume/Mute icon
├── Play/Pause button
├── Time display (0:00 / X:XX)
├── Progress bar/slider
├── Volume control
└── More options menu (three dots)
```

---

## Page-by-Page Breakdown

### 1. Dashboard Page
**Route:** `/` or `/dashboard`

**Layout Structure:**
```
├── Page Header
│   └── Title: "Easy Finance"
│
├── Metrics Row (3 Stat Cards)
│   ├── Today's Calls (1250) - Purple icon
│   ├── Today's Transfers (322) - Orange icon
│   └── Concurrent Calls (10) - Green icon with avg/highest
│
└── Today's Transferred Calls Section
    ├── Section Header
    │   ├── Title: "Today's Transferred Calls"
    │   └── Action Links
    │       ├── View API Log
    │       ├── DNC Today
    │       └── All DNC
    │
    └── Calls List (Card-based)
        └── Each Call Card Contains:
            ├── Transfer icon (circular orange bg)
            ├── Call ID
            ├── Time stamp
            ├── From/To numbers
            ├── Audio player
            ├── Duration
            └── Status badge (Transferred)
```

**Data Structure:**
```typescript
interface CallMetrics {
  todayCalls: number;
  todayTransfers: number;
  concurrentCalls: {
    current: number;
    average: number;
    highest: number;
  };
}

interface TransferredCall {
  callId: string;
  time: string;
  from: string;
  to: string;
  duration: string;
  audioUrl: string;
  status: 'Transferred';
}
```

---

### 2. AI Agents Page
**Route:** `/ai-agents`

**Layout Structure:**
```
├── Page Header
│   └── Title: "AI Agents - Easy Finance"
│
├── AI Agents Section
│   ├── Info Text: "Toll Free numbers have a $0.05 per minute..."
│   ├── Count: "Total AI Agents: 4"
│   └── Table
│       └── Columns:
│           ├── Agent Name
│           ├── Phones (multiple numbers shown)
│           ├── Channel
│           ├── Voice ID
│           ├── Language
│           ├── Published (Yes/No badge)
│           ├── Max (duration)
│           └── Created
│
└── Detailed Agent Information Section
    └── Agent Cards (Grid Layout)
        └── Each Card Contains:
            ├── Agent Icon
            ├── Agent Name + ID
            ├── Version
            ├── Voice Speed
            ├── Volume
            ├── Responsiveness
            ├── Silence Timeout
            └── Webhook endpoint
```

**Data Structure:**
```typescript
interface AIAgent {
  id: string;
  name: string;
  phones: string[];
  channel: 'Voice';
  voiceId: string;
  language: string;
  published: boolean;
  maxDuration: string;
  created: string;
  version?: number;
  voiceSpeed?: number;
  volume?: number;
  responsiveness?: number;
  silenceTimeout?: string;
  webhook?: string;
}
```

---

### 3. Billing Page
**Route:** `/billing`

**Layout Structure:**
```
├── Page Header
│   └── Title: "Billing & Payments"
│
├── Stripe Integration Status Section
│   ├── Title: "Stripe Integration Status"
│   ├── Subtitle: "System-wide Stripe configuration"
│   └── Status Message
│       ├── Green check icon
│       └── "Stripe is configured and ready"
│       └── Description text
│
├── Current Billing Profile Section
│   ├── Title: "Current Billing Profile"
│   ├── Subtitle: "Your account's billing information"
│   │
│   ├── Two-Column Layout
│   │   ├── Left: Account Information
│   │   │   ├── Account Name: "Easy Finance"
│   │   │   ├── Billing Email: "operations@easyfinance.ai"
│   │   │   ├── Subscription Status: Active (badge)
│   │   │   ├── Current Balance: $1,018.89
│   │   │   ├── Auto Pay: On
│   │   │   ├── Auto Charge Threshold: $0.00
│   │   │   ├── Pause Threshold: $-300.00
│   │   │   └── Price per Minute: $0.35
│   │   │
│   │   └── Right: Stripe Connection
│   │       ├── Status: "Connected to Stripe" (green dot)
│   │       ├── Customer ID
│   │       └── Description text
│   │
│   └── Footer Note: "Toll Free numbers have a $0.05 per minute..."
│
└── Payment Methods Section
    ├── Title: "Payment Methods"
    ├── Subtitle: "Manage your payment options"
    └── Content: "Your Payment Methods" (expandable)
```

**Data Structure:**
```typescript
interface BillingProfile {
  accountName: string;
  billingEmail: string;
  subscriptionStatus: 'Active' | 'Inactive' | 'Paused';
  currentBalance: number;
  autoPay: boolean;
  autoChargeThreshold: number;
  pauseThreshold: number;
  pricePerMinute: number;
  stripeCustomerId: string;
  stripeConnected: boolean;
}
```

---

### 4. Phone Numbers Page
**Route:** `/phone-numbers`

**Layout Structure:**
```
├── Page Header
│   └── Title: "Phone Numbers - Easy Finance"
│
├── AI Phone Numbers Section
│   ├── Info Text: "Toll Free numbers have a $0.05 per minute..."
│   ├── Count: "Total AI Phone Numbers: 5"
│   └── Table
│       └── Columns:
│           ├── Phone Number
│           ├── Pretty Format
│           ├── Agent ID
│           ├── Area Code
│           ├── Toll Free (Yes/No badge)
│           └── SMS Enabled (Yes/No)
│
└── Transfer Numbers Section
    ├── Count: "Total Transfer Numbers: 5"
    └── Table
        └── Columns:
            ├── Phone Number
            ├── Description
            ├── Type (badge)
            ├── Status (Active badge)
            ├── Created
            └── Actions (Edit, Delete)
```

**Data Structure:**
```typescript
interface AIPhoneNumber {
  phoneNumber: string;
  prettyFormat: string;
  agentId: string;
  areaCode: string;
  tollFree: boolean;
  smsEnabled: boolean;
}

interface TransferNumber {
  phoneNumber: string;
  description: string;
  type: 'Transfer To Did';
  status: 'Active';
  created: string;
}
```

---

### 5. CRM Page
**Route:** `/crm`

**Layout Structure:**
```
├── Page Header
│   └── Title: "CRM - Easy Finance"
│
└── Customer Relationship Management Section
    └── Info Card
        ├── Two-Column Layout
        │   ├── Left Column
        │   │   ├── Label: "CRM System"
        │   │   ├── Value: "CRM Easy Finance"
        │   │   ├── Label: "Type"
        │   │   └── Value: "custom"
        │   │
        │   └── Right Column
        │       ├── Label: "Status"
        │       ├── Value: "Active" (green badge)
        │       ├── Label: "Created"
        │       └── Value: "Aug 13, 2025"
```

**Data Structure:**
```typescript
interface CRMSystem {
  name: string;
  type: 'custom' | 'salesforce' | 'hubspot' | 'other';
  status: 'Active' | 'Inactive';
  created: string;
}
```

---

### 6. CRM API Logs Page
**Route:** `/crm/api-logs`

**Layout Structure:**
```
├── Page Header
│   └── Title: "CRM API Log"
│
└── API Transaction Log Section
    ├── Header: "Showing 1 to 100 of 14104 records"
    └── Log Entries (List)
        └── Each Entry Contains:
            ├── Status Code Badge (201)
            ├── Endpoint URL
            ├── Timestamp
            ├── Record ID
            ├── Two-Column Layout
            │   ├── Request Payload (JSON viewer)
            │   └── Response Data (JSON viewer)
```

**Data Structure:**
```typescript
interface APILogEntry {
  id: number;
  statusCode: number;
  endpoint: string;
  timestamp: string;
  requestPayload: object;
  responseData: object;
}
```

---

### 7. Call History Page
**Route:** `/call-history`

**Layout Structure:**
```
├── Page Header
│   ├── Title: "Call History - Easy Finance"
│   └── Action: "Back to Dashboard" button
│
├── Metrics Row (4 Stat Cards)
│   ├── Total Calls (Today): 1,257
│   ├── Transfers (Today): 325
│   ├── Total Duration (Today): 3722:01
│   └── Avg Duration (Today): 2:57
│
├── AI Agents Activity Section
│   ├── Title: "AI Agents Activity (Today)"
│   └── Agent Cards (Grid)
│       └── Each Card Contains:
│           ├── Agent icon
│           ├── Agent name + ID
│           ├── Phone numbers
│           ├── Call count (large)
│           ├── Transfers count
│           └── Transfer percentage
│
├── Filters Section
│   ├── Label: "Filters"
│   ├── Toggle: "Showing Today's Calls" / "Show All Calls"
│   └── Filter Inputs
│       ├── AI Agent (dropdown)
│       ├── Direction (dropdown)
│       ├── From Date (date picker)
│       ├── To Date (date picker)
│       └── Apply Filters button
│
└── Call History Table
    └── Columns:
        ├── Call Start
        ├── Disconnection Reason
        ├── Duration
        ├── Direction (badge)
        ├── From
        ├── Transferred To
        └── Recording (audio player)
```

**Data Structure:**
```typescript
interface CallHistoryMetrics {
  totalCalls: number;
  transfers: number;
  totalDuration: string;
  avgDuration: string;
}

interface AgentActivity {
  agentId: string;
  agentName: string;
  phoneNumbers: string[];
  callCount: number;
  transferCount: number;
  transferPercentage: number;
}

interface CallRecord {
  callStart: string;
  disconnectionReason: string;
  duration: string;
  direction: 'Inbound' | 'Outbound';
  from: string;
  transferredTo: string;
  recordingUrl: string;
}
```

---

## Component Library Structure

### Recommended Folder Structure
```
/
├── app/
│   ├── layout.tsx (Root layout with ThemeProvider & navigation)
│   ├── page.tsx (Dashboard)
│   ├── globals.css (Global styles + CSS custom properties)
│   ├── ai-agents/
│   │   └── page.tsx
│   ├── billing/
│   │   └── page.tsx
│   ├── phone-numbers/
│   │   └── page.tsx
│   ├── crm/
│   │   ├── page.tsx
│   │   └── api-logs/
│   │       └── page.tsx
│   └── call-history/
│       └── page.tsx
│
├── components/
│   ├── providers/
│   │   └── theme-provider.tsx (next-themes provider wrapper)
│   │
│   ├── layout/
│   │   ├── Navigation.tsx
│   │   ├── Header.tsx
│   │   ├── UserMenu.tsx (Custom styled Radix DropdownMenu)
│   │   └── ThemeToggle.tsx (Dark/Light mode toggle)
│   │
│   ├── ui/ (Custom styled Radix primitives - reusable)
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── select.tsx
│   │   ├── dialog.tsx
│   │   ├── switch.tsx
│   │   ├── slider.tsx
│   │   ├── tooltip.tsx
│   │   ├── popover.tsx
│   │   ├── tabs.tsx
│   │   ├── separator.tsx
│   │   ├── scroll-area.tsx
│   │   ├── table.tsx
│   │   ├── avatar.tsx
│   │   ├── audio-player.tsx
│   │   └── json-viewer.tsx
│   │
│   ├── dashboard/
│   │   ├── MetricsRow.tsx
│   │   ├── StatCard.tsx
│   │   └── TransferredCallCard.tsx
│   │
│   ├── ai-agents/
│   │   ├── AgentTable.tsx
│   │   └── AgentDetailCard.tsx
│   │
│   ├── billing/
│   │   ├── StripeStatus.tsx
│   │   ├── BillingProfile.tsx
│   │   └── PaymentMethods.tsx
│   │
│   ├── phone-numbers/
│   │   ├── PhoneNumbersTable.tsx
│   │   └── TransferNumbersTable.tsx
│   │
│   ├── crm/
│   │   ├── CRMInfo.tsx
│   │   └── APILogEntry.tsx
│   │
│   └── call-history/
│       ├── CallMetrics.tsx
│       ├── AgentActivityCard.tsx
│       ├── CallFilters.tsx
│       └── CallHistoryTable.tsx
│
├── types/
│   ├── dashboard.ts
│   ├── agents.ts
│   ├── billing.ts
│   ├── phoneNumbers.ts
│   ├── crm.ts
│   └── callHistory.ts
│
├── lib/
│   ├── api.ts (API client for future backend integration)
│   ├── utils.ts (cn() utility, formatters)
│   └── mock-data.ts (Mock data for development)
│
└── hooks/
    ├── use-call-history.ts
    ├── use-agents.ts
    └── use-billing.ts
```

---

## Styling Guidelines

### Approach
- **Radix UI Primitives** for component structure and accessibility
- **Tailwind CSS** for styling with theme-aware custom properties
- **CSS Custom Properties** for theme values (support dark/light modes)
- **Class Variance Authority (CVA)** for component variants (optional)

### Tailwind Configuration with Theme Support
```javascript
// Common spacing
padding: p-6, p-8
margin: mb-4, mb-6
gap: gap-4, gap-6

// Typography (theme-aware)
heading: text-2xl font-semibold text-foreground
subheading: text-sm text-muted-foreground
value: text-3xl font-bold text-foreground

// Colors (using CSS custom properties)
background: bg-background
foreground: text-foreground
card: bg-card text-card-foreground
primary: bg-primary text-primary-foreground
success: bg-success text-success-foreground
warning: bg-warning text-warning-foreground
muted: bg-muted text-muted-foreground
border: border-border

// Components (theme-aware)
card: bg-card text-card-foreground rounded-lg shadow-sm border border-border
badge: px-3 py-1 rounded-full text-xs font-medium
button: bg-primary text-primary-foreground hover:bg-primary/90 rounded-md px-4 py-2

// Dark mode classes (automatic with custom properties)
.dark classes are handled by CSS variables, no need for dark: prefix in most cases
```

### Radix UI Component Styling Pattern
```tsx
// Example: Button component with Radix-like API
import * as React from 'react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'md', ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center rounded-md font-medium transition-colors',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
          'disabled:pointer-events-none disabled:opacity-50',
          // Variants
          {
            'bg-primary text-primary-foreground hover:bg-primary/90': variant === 'default',
            'border border-border bg-background hover:bg-muted': variant === 'outline',
            'hover:bg-muted': variant === 'ghost',
          },
          // Sizes
          {
            'h-9 px-3 text-sm': size === 'sm',
            'h-10 px-4': size === 'md',
            'h-11 px-8': size === 'lg',
          },
          className
        )}
        {...props}
      />
    )
  }
)
```

### Theme Toggle Component Location
- Located in the top right of navigation bar
- Uses Radix UI Switch or Button with icons (Sun/Moon)
- Smooth transition between themes

---

## API Integration Plan

### API Endpoints (To be implemented in Python backend)
```
Dashboard:
- GET /api/dashboard/metrics
- GET /api/dashboard/transferred-calls

AI Agents:
- GET /api/agents
- GET /api/agents/:id
- POST /api/agents
- PUT /api/agents/:id
- DELETE /api/agents/:id

Billing:
- GET /api/billing/profile
- GET /api/billing/stripe-status
- POST /api/billing/payment-methods

Phone Numbers:
- GET /api/phone-numbers
- GET /api/transfer-numbers
- POST /api/phone-numbers
- DELETE /api/phone-numbers/:id

CRM:
- GET /api/crm
- GET /api/crm/api-logs
- POST /api/crm/leads

Call History:
- GET /api/call-history
- GET /api/call-history/metrics
- GET /api/call-history/agent-activity
```

---

## Implementation Checklist

### Phase 1: Foundation & Setup
- [ ] Install required dependencies
  - [ ] Radix UI Primitives (all individual packages)
  - [ ] next-themes (theme management)
  - [ ] clsx & tailwind-merge (for cn() utility)
  - [ ] lucide-react (icons)
- [ ] Configure theme system
  - [ ] Set up CSS custom properties in globals.css (colors, etc.)
  - [ ] Create ThemeProvider component wrapper
  - [ ] Configure next-themes in root layout
  - [ ] Create ThemeToggle component
- [ ] Set up utility functions
  - [ ] Create cn() utility (classname merger with clsx + tailwind-merge)
  - [ ] Create formatters (date, phone, currency)
- [ ] Create base styled Radix UI components in components/ui/
  - [ ] Button (styled with Tailwind)
  - [ ] Card (styled with Tailwind)
  - [ ] Badge (styled with Tailwind)
  - [ ] Dropdown Menu (styled with Tailwind)
  - [ ] Select (styled with Tailwind)
  - [ ] Dialog (styled with Tailwind)
  - [ ] Switch (styled with Tailwind)
  - [ ] Table (styled with Tailwind)
- [ ] Set up base layout with navigation
- [ ] Set up TypeScript types/interfaces

### Phase 2: Page Development
- [ ] Dashboard page
  - [ ] Metrics cards
  - [ ] Transferred calls list
  - [ ] Audio player integration
- [ ] AI Agents page
  - [ ] Agents table
  - [ ] Agent detail cards
- [ ] Billing page
  - [ ] Stripe status section
  - [ ] Billing profile
  - [ ] Payment methods
- [ ] Phone Numbers page
  - [ ] AI phone numbers table
  - [ ] Transfer numbers table
- [ ] CRM page
  - [ ] CRM info card
- [ ] CRM API Logs page
  - [ ] API log entries
  - [ ] JSON viewer
- [ ] Call History page
  - [ ] Metrics row
  - [ ] Agent activity cards
  - [ ] Filters section
  - [ ] Call history table

### Phase 3: Integration Ready
- [ ] Create API client utility
- [ ] Add mock data for development
- [ ] Implement loading states (Radix Spinner)
- [ ] Implement error handling
- [ ] Add form validation
- [ ] Test all components in both themes

### Phase 4: Polish
- [ ] Responsive design testing (mobile, tablet, desktop)
- [ ] Accessibility improvements (ARIA labels, keyboard navigation)
- [ ] Performance optimization
- [ ] Cross-browser testing
- [ ] Dark mode polish (ensure all components look good)
- [ ] Add animations and transitions

---

## Required NPM Packages

### Radix UI Primitives (Individual packages)
```bash
npm install @radix-ui/react-dropdown-menu @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-switch @radix-ui/react-slider @radix-ui/react-tooltip @radix-ui/react-popover @radix-ui/react-separator @radix-ui/react-scroll-area @radix-ui/react-avatar
```

### Theme & Utilities
```bash
npm install next-themes           # Dark/light mode management
npm install clsx tailwind-merge   # Classname utilities
npm install lucide-react          # Icons
```

### Optional (for enhanced functionality)
```bash
npm install class-variance-authority  # For component variants (CVA)
npm install date-fns                  # For date formatting
npm install react-syntax-highlighter  # For JSON viewer
```

### Installation Command (All at once)
```bash
npm install @radix-ui/react-dropdown-menu @radix-ui/react-dialog @radix-ui/react-select @radix-ui/react-tabs @radix-ui/react-switch @radix-ui/react-slider @radix-ui/react-tooltip @radix-ui/react-popover @radix-ui/react-separator @radix-ui/react-scroll-area @radix-ui/react-avatar next-themes clsx tailwind-merge lucide-react
```

---

## Notes
- All dates should be formatted consistently (e.g., "Oct 28, 2025 13:15:45")
- Phone numbers should support multiple formats (e.g., "+1234567890", "(123) 456-7890")
- Audio players need to support multiple audio formats
- Tables should support sorting and filtering (client-side for now)
- All monetary values should be formatted with proper currency symbols
- Status badges should have consistent color coding across all pages
- Theme transitions should be smooth (transition-colors on theme-aware elements)
- All Radix components should be properly styled for both light and dark themes
- Ensure ARIA attributes are properly set for accessibility
- Use semantic HTML elements where possible
