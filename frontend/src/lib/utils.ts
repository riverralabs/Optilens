import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

/**
 * Returns the CSS variable name for a CRO score band color.
 * 80-100: optimized (green), 60-79: needs work (amber),
 * 40-59: high risk (orange), 0-39: critical (red)
 */
export function getScoreColor(score: number): string {
  if (score >= 80) return 'hsl(var(--score-optimized))'
  if (score >= 60) return 'hsl(var(--score-needs-work))'
  if (score >= 40) return 'hsl(var(--score-high-risk))'
  return 'hsl(var(--score-critical))'
}

export function getScoreLabel(score: number): string {
  if (score >= 80) return 'Optimized'
  if (score >= 60) return 'Needs Work'
  if (score >= 40) return 'High Risk'
  return 'Critical'
}

/**
 * Format a number as currency (USD).
 */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(amount)
}

/**
 * Format a date relative to now (e.g., "2 hours ago").
 */
export function formatRelativeDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMins = Math.floor(diffMs / 60_000)
  const diffHours = Math.floor(diffMs / 3_600_000)
  const diffDays = Math.floor(diffMs / 86_400_000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 30) return `${diffDays}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

/**
 * Validate a URL string.
 */
export function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}
