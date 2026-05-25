import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatConfidence(value: number): string {
  return `${Math.round(value * 100)}%`
}

export function truncate(str: string, max: number): string {
  return str.length > max ? str.slice(0, max) + '…' : str
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Europe/Vienna',
  }).format(date)
}

export function userFacingSourceError(value: string | null | undefined): string {
  if (!value) return 'The source could not be processed. Check the file and try again.'

  const internalPatterns = [
    'Expected node',
    'Traceback',
    'KeyError',
    'ValueError',
    'RuntimeError',
    'Exception',
    'langgraph',
  ]

  if (internalPatterns.some(pattern => value.toLowerCase().includes(pattern.toLowerCase()))) {
    return 'The source could not be processed. Check the file and try again.'
  }

  return value
}
