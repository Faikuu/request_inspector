// Recently opened inboxes, kept in this browser only. Holds no secrets.

export type RecentInbox = {
  id: string
  name: string | null
  openedAt: number // epoch ms
}

const KEY = 'ri:recent'
const MAX = 8

function isRecent(value: unknown): value is RecentInbox {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return (
    typeof v.id === 'string' &&
    (typeof v.name === 'string' || v.name === null) &&
    typeof v.openedAt === 'number'
  )
}

export function getRecent(): RecentInbox[] {
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.filter(isRecent).slice(0, MAX) : []
  } catch {
    return []
  }
}

function write(list: RecentInbox[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(list))
  } catch {
    // Storage unavailable: the list simply is not remembered.
  }
}

/**
 * Put an inbox at the top of the list. Omitting `name` keeps the stored name,
 * so opening an inbox by ID does not erase what was learned at creation.
 */
export function rememberInbox({ id, name }: { id: string; name?: string | null }): void {
  const existing = getRecent()
  const previous = existing.find((r) => r.id === id)
  const resolvedName = name === undefined ? (previous?.name ?? null) : name?.trim() || null
  const entry: RecentInbox = { id, name: resolvedName, openedAt: Date.now() }
  write([entry, ...existing.filter((r) => r.id !== id)].slice(0, MAX))
}

export function forgetInbox(id: string): void {
  write(getRecent().filter((r) => r.id !== id))
}
