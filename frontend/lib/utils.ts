import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Merge Tailwind CSS classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format phone number to pretty format
 * Example: +12135551234 -> (213) 555-1234
 */
export function formatPhoneNumber(phone: string): string {
  const cleaned = phone.replace(/\D/g, '')

  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    const areaCode = cleaned.slice(1, 4)
    const prefix = cleaned.slice(4, 7)
    const line = cleaned.slice(7)
    return `(${areaCode}) ${prefix}-${line}`
  }

  if (cleaned.length === 10) {
    const areaCode = cleaned.slice(0, 3)
    const prefix = cleaned.slice(3, 6)
    const line = cleaned.slice(6)
    return `(${areaCode}) ${prefix}-${line}`
  }

  return phone
}

/**
 * Format currency to USD
 * Example: 1234.56 -> $1,234.56
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

/**
 * Format date to readable format
 * Example: 2025-01-15T10:30:00 -> Jan 15, 2025 10:30 AM
 */
export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(d)
}

/**
 * Format duration from seconds to MM:SS or HH:MM:SS
 * Example: 125 -> 2:05, 3665 -> 1:01:05
 */
export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
  }

  return `${minutes}:${String(secs).padStart(2, '0')}`
}

/**
 * Truncate text with ellipsis
 * Example: truncate("Hello World", 5) -> "Hello..."
 */
export function truncate(text: string, length: number): string {
  if (text.length <= length) return text
  return text.slice(0, length) + '...'
}
