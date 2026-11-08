import type { CapturedRequest, Inbox, ListRequestsParams, RequestPage, Session } from './types'
import { clearToken, getToken, saveToken } from '@/lib/session'

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/** Raised for 401/403 on an authenticated call; the stored token has already been cleared. */
export class AuthError extends ApiError {}

const BASE = '/api'

async function request<T>(
  path: string,
  init: RequestInit & { inboxId?: string } = {},
): Promise<T> {
  const { inboxId, headers, ...rest } = init
  const h = new Headers(headers)
  if (rest.body && !h.has('Content-Type')) h.set('Content-Type', 'application/json')
  if (inboxId) {
    const token = getToken(inboxId)
    if (!token) throw new AuthError(401, 'Your session has ended. Enter the password to continue.')
    h.set('Authorization', `Bearer ${token}`)
  }

  let res: Response
  try {
    res = await fetch(BASE + path, { ...rest, headers: h })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check that the backend is running.')
  }

  if (res.status === 204) return undefined as T
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const detail = typeof data?.detail === 'string' ? data.detail : res.statusText || 'Request failed'
    if (inboxId && (res.status === 401 || res.status === 403)) {
      clearToken(inboxId)
      throw new AuthError(res.status, detail)
    }
    throw new ApiError(res.status, detail)
  }
  return data as T
}

function remember(session: Session): Session {
  saveToken(session.inbox.id, session.access_token, session.expires_in)
  return session
}

export const api = {
  /** Create an inbox; stores the returned token. */
  async createInbox(password: string, name?: string): Promise<Session> {
    const body = JSON.stringify({ password, name: name?.trim() || null })
    return remember(await request<Session>('/inboxes', { method: 'POST', body }))
  },

  /** Exchange the inbox password for a viewer token; stores it. 401 = wrong id/password, 429 = rate limited. */
  async unlock(inboxId: string, password: string): Promise<Session> {
    const body = JSON.stringify({ password })
    return remember(
      await request<Session>(`/inboxes/${encodeURIComponent(inboxId)}/session`, { method: 'POST', body }),
    )
  },

  hasSession(inboxId: string): boolean {
    return getToken(inboxId) !== null
  },

  lock(inboxId: string): void {
    clearToken(inboxId)
  },

  /** Short-lived token for authenticating the WebSocket (sent as the first message). */
  token(inboxId: string): string | null {
    return getToken(inboxId)
  },

  getInbox(inboxId: string): Promise<Inbox> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}`, { inboxId })
  },

  renameInbox(inboxId: string, name: string | null): Promise<Inbox> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}`, {
      method: 'PATCH',
      body: JSON.stringify({ name }),
      inboxId,
    })
  },

  /** Issue a new ingest key; the old capture URL stops working. */
  rotateKey(inboxId: string): Promise<Inbox> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}/rotate-key`, { method: 'POST', inboxId })
  },

  async deleteInbox(inboxId: string): Promise<void> {
    await request(`/inboxes/${encodeURIComponent(inboxId)}`, { method: 'DELETE', inboxId })
    clearToken(inboxId)
  },

  listRequests(inboxId: string, params: ListRequestsParams = {}): Promise<RequestPage> {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') qs.set(k, String(v))
    }
    const suffix = qs.toString() ? `?${qs}` : ''
    return request(`/inboxes/${encodeURIComponent(inboxId)}/requests${suffix}`, { inboxId })
  },

  getRequest(inboxId: string, requestId: number): Promise<CapturedRequest> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}/requests/${requestId}`, { inboxId })
  },

  deleteRequest(inboxId: string, requestId: number): Promise<void> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}/requests/${requestId}`, {
      method: 'DELETE',
      inboxId,
    })
  },

  clearRequests(inboxId: string): Promise<void> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}/requests`, { method: 'DELETE', inboxId })
  },

  /** All captured requests as a JSON array (newest first). */
  exportRequests(inboxId: string): Promise<CapturedRequest[]> {
    return request(`/inboxes/${encodeURIComponent(inboxId)}/export`, { inboxId })
  },
}

/** Public capture URL for an inbox, e.g. https://host/api/hook/<ingest_key> */
export function captureUrl(inbox: Pick<Inbox, 'ingest_key'>): string {
  return `${window.location.origin}${BASE}/hook/${inbox.ingest_key}`
}

/** WebSocket URL for the live stream (wss on https). Auth is sent as the first message. */
export function streamUrl(inboxId: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}${BASE}/inboxes/${encodeURIComponent(inboxId)}/stream`
}
