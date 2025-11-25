# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Easy Finance** is a modern call center/telephony management system with AI agents, CRM, billing, and call tracking capabilities. This is currently a **frontend-only** application built with Next.js, designed to be integrated with a Python backend in the future.

## Tech Stack

- **Framework:** Next.js 16.0.1 (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS v4 (using new `@import` syntax)
- **UI Components:** Radix UI Primitives (unstyled/headless) with custom Tailwind styling
- **Theme System:** next-themes with CSS custom properties
- **Icons:** lucide-react
- **React:** 19.2.0

## Development Commands

```bash
# Install dependencies
npm install

# Run development server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

## Architecture & Design Patterns

### 1. Theme System Architecture

The application uses a sophisticated theme system with CSS custom properties (HSL color space) for seamless light/dark mode switching:

- **Theme Provider:** `components/providers/theme-provider.tsx` wraps the entire app in `app/layout.tsx`
- **CSS Variables:** Defined in `app/globals.css` using HSL format (`--background: 0 0% 0%`)
- **Theme Toggle:** `components/layout/theme-toggle.tsx` - handles theme switching with proper hydration
- **Dark Mode:** Pure black background (`0 0% 0%`) for a clean, modern aesthetic
- **Light Mode:** White background with subtle shadows

**Important:** Always use theme-aware Tailwind classes (`bg-background`, `text-foreground`, `border-border`) instead of hardcoded colors.

### 2. Component Architecture

#### Radix UI + Custom Styling Pattern

Components follow a two-tier approach:

1. **Base UI Components** (`components/ui/`): Styled Radix UI primitives
   - Use Radix UI primitives for structure and accessibility
   - Style with Tailwind CSS using the `cn()` utility
   - Support variants using conditional classes
   - Example: `button.tsx`, `card.tsx`, `badge.tsx`

2. **Feature Components** (`components/[page]/`): Page-specific components
   - Build on top of base UI components
   - Contain business logic and data handling
   - Example: `components/dashboard/MetricsRow.tsx`

#### Component Styling Conventions

```tsx
import { cn } from "@/lib/utils"

// Always use forwardRef for UI components
const Component = React.forwardRef<HTMLElement, Props>(
  ({ className, variant = "default", ...props }, ref) => (
    <element
      ref={ref}
      className={cn(
        "base-classes",
        {
          "variant-classes": variant === "variant",
        },
        className // Allow overrides
      )}
      {...props}
    />
  )
)
```

#### Card Component Pattern

Cards use **transparent backgrounds** with borders for separation (modern, flat design):
- `bg-transparent` - matches page background
- `border` - defines card boundaries
- `shadow-sm` - subtle depth
- Works in both light and dark themes

### 3. Utility Functions

Located in `lib/utils.ts`:

- **`cn(...inputs)`** - Merge Tailwind classes with proper precedence (clsx + tailwind-merge)
- **`formatPhoneNumber(phone)`** - Convert to (XXX) XXX-XXXX format
- **`formatCurrency(amount)`** - USD formatting with commas
- **`formatDate(date)`** - Readable date format
- **`formatDuration(seconds)`** - Convert to MM:SS or HH:MM:SS

### 4. Layout Structure

The app uses a persistent layout defined in `app/layout.tsx`:

```
RootLayout
└── ThemeProvider
    ├── Navigation (sticky top nav)
    └── Main Container
        └── Page Content
```

**Navigation** (`components/layout/navigation.tsx`):
- Sticky top navigation with glass morphism effect
- Active route detection using `usePathname()`
- Theme toggle button
- User profile section (currently placeholder)

### 5. Path Aliases

TypeScript paths are configured in `tsconfig.json`:
- `@/*` maps to root directory
- Use for all imports: `import { cn } from "@/lib/utils"`

### 6. Tailwind v4 Configuration

Using the new Tailwind v4 architecture:
- No `tailwind.config.js` file
- Styles imported via `@import "tailwindcss"` in `globals.css`
- CSS custom properties defined in `:root` and `.dark`
- Theme colors registered in `@theme inline` block

## Page Structure

Planned pages (some not yet implemented):

1. **Dashboard** (`/`) - Call metrics, transferred calls list
2. **AI Agents** (`/ai-agents`) - Agent management and configuration
3. **Phone Numbers** (`/phone-numbers`) - AI and transfer number management
4. **CRM** (`/crm`) - Customer relationship management
5. **CRM API Logs** (`/crm/api-logs`) - API transaction logs with JSON viewer
6. **Billing** (`/billing`) - Stripe integration, billing profile
7. **Call History** (`/call-history`) - Call records with filters and audio player

## Key Files Reference

- **`PROJECT_STRUCTURE.md`** - Comprehensive architecture documentation with data structures for all pages
- **`app/globals.css`** - Theme variables and Tailwind v4 configuration
- **`lib/utils.ts`** - Shared utility functions
- **`components/ui/`** - Reusable styled Radix primitives
- **`components/layout/`** - App shell components (nav, theme toggle)

## Backend Integration (Future)

The frontend is designed to connect to a Python backend via REST APIs:
- API client will be in `lib/api.ts`
- Mock data for development in `lib/mock-data.ts`
- All data structures documented in `PROJECT_STRUCTURE.md`

API endpoints are planned for:
- Dashboard metrics
- AI agents CRUD
- Phone numbers management
- CRM operations
- Billing/Stripe integration
- Call history with filtering

## Color System

Semantic color tokens (use these, not raw colors):

- `bg-background` / `text-foreground` - Main background and text
- `bg-card` / `text-card-foreground` - Card surfaces
- `bg-primary` / `text-primary-foreground` - Primary actions
- `bg-success` / `text-success-foreground` - Success states (green)
- `bg-warning` / `text-warning-foreground` - Warning states (amber)
- `bg-destructive` / `text-destructive-foreground` - Destructive actions (red)
- `bg-muted` / `text-muted-foreground` - Subtle/disabled content
- `border-border` - All borders

## Important Conventions

1. **Always use `"use client"`** for components using hooks (useState, useTheme, etc.)
2. **Server components by default** - Only add `"use client"` when necessary
3. **Hydration-safe theme toggle** - Check `mounted` state before rendering theme-dependent UI
4. **Custom 404 page** - Uses theme system (`app/not-found.tsx`)
5. **Component exports** - Use named exports with displayName for better debugging
6. **Responsive design** - Mobile-first with `md:` and `lg:` breakpoints

## Design Philosophy

- **Modern & Minimal** - Flat design with subtle shadows
- **Transparent cards** - Border-separated, not background-separated
- **Dark mode first** - Pure black background (#000000)
- **Accessibility** - Radix UI handles ARIA, focus management, keyboard navigation
- **Type safety** - Strict TypeScript throughout
