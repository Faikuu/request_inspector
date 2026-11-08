const SHORT_DATE = new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' })
const SHORT_DATE_YEAR = new Intl.DateTimeFormat(undefined, {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

/** Parse an ISO string. Timestamps without an offset are UTC, as the backend sends them. */
function toDate(input: string | Date): Date {
  if (input instanceof Date) return input
  const hasOffset = /(Z|[+-]\d{2}:?\d{2})$/i.test(input)
  return new Date(hasOffset ? input : `${input}Z`)
}

/** Decimal units, as in the spec: 0 B, 512 B, 2.1 kB, 1.4 MB. */
export function formatBytes(n: number): string {
  if (!Number.isFinite(n) || n < 1000) return `${Math.max(0, Math.round(n || 0))} B`
  const units = ['kB', 'MB', 'GB', 'TB']
  let value = n / 1000
  let unit = 0
  while (value >= 1000 && unit < units.length - 1) {
    value /= 1000
    unit++
  }
  const text = value < 10 ? value.toFixed(1) : String(Math.round(value))
  return `${text} ${units[unit]}`
}

/** "just now", "12s ago", "4m ago", "3h ago", "2d ago", then a short date. */
export function relativeTime(input: string | Date, now: number = Date.now()): string {
  const date = toDate(input)
  const seconds = Math.floor((now - date.getTime()) / 1000)
  if (Number.isNaN(seconds) || seconds < 5) return 'just now'
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  const sameYear = date.getFullYear() === new Date(now).getFullYear()
  return (sameYear ? SHORT_DATE : SHORT_DATE_YEAR).format(date)
}

/** Local wall-clock time as HH:MM:SS. */
export function clockTime(iso: string): string {
  const d = toDate(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/** Long local date and time for tooltips and detail views. */
export function fullDate(iso: string): string {
  return toDate(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' })
}
