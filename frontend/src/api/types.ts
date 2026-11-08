// Wire types shared with the FastAPI backend (backend/app/schemas.py).

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'OPTIONS' | 'HEAD'

export interface Inbox {
  id: string
  name: string | null
  /** Secret part of the capture URL: `${origin}/api/hook/${ingest_key}` */
  ingest_key: string
  created_at: string // ISO 8601, UTC
  request_count: number
}

export interface Session {
  inbox: Inbox
  access_token: string
  token_type: 'bearer'
  expires_in: number // seconds
}

export interface CapturedRequest {
  id: number
  inbox_id: string
  method: string
  /** Sub-path after the ingest key, always starts with "/" (e.g. "/" or "/orders/42") */
  path: string
  query: Record<string, string[]>
  headers: Record<string, string>
  content_type: string | null
  /** UTF-8 text body, or null when the body is binary or empty */
  body: string | null
  /** Base64 body, set only when the body is not valid UTF-8 */
  body_base64: string | null
  size: number // bytes
  remote_addr: string | null
  created_at: string // ISO 8601, UTC
}

export interface RequestPage {
  items: CapturedRequest[] // newest first
  has_more: boolean
}

export interface ListRequestsParams {
  limit?: number // 1..200, default 50
  before_id?: number // cursor: return items with id < before_id
  method?: string
  q?: string // substring search across path, body, headers
}

/** Messages pushed over the WebSocket after auth succeeds. */
export type StreamEvent =
  | { type: 'ready' }
  | { type: 'request.created'; data: CapturedRequest }
  | { type: 'request.deleted'; id: number }
  | { type: 'requests.cleared' }
  | { type: 'inbox.updated'; data: Inbox }
  | { type: 'inbox.deleted' }
