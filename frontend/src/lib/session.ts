// Viewer tokens live in sessionStorage (per tab, cleared when the tab closes)
// rather than in a year-long JS cookie. Nothing secret goes to localStorage.

const key = (inboxId: string) => `ri:token:${inboxId}`

interface Stored {
  token: string
  expiresAt: number // epoch ms
}

function safe<T>(fn: () => T, fallback: T): T {
  try {
    return fn()
  } catch {
    return fallback
  }
}

export function saveToken(inboxId: string, token: string, expiresInSeconds: number): void {
  const value: Stored = { token, expiresAt: Date.now() + expiresInSeconds * 1000 }
  safe(() => sessionStorage.setItem(key(inboxId), JSON.stringify(value)), undefined)
}

export function getToken(inboxId: string): string | null {
  const raw = safe(() => sessionStorage.getItem(key(inboxId)), null)
  if (!raw) return null
  const parsed = safe(() => JSON.parse(raw) as Stored, null)
  if (!parsed || parsed.expiresAt <= Date.now()) {
    clearToken(inboxId)
    return null
  }
  return parsed.token
}

export function clearToken(inboxId: string): void {
  safe(() => sessionStorage.removeItem(key(inboxId)), undefined)
}
