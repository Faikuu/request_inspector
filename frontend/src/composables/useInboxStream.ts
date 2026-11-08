import { onScopeDispose, ref, unref, watch, type Ref } from 'vue'
import { api, streamUrl } from '@/api/client'
import type { StreamEvent } from '@/api/types'

export type StreamStatus = 'connecting' | 'live' | 'reconnecting' | 'offline'

export interface InboxStreamHandlers {
  /** Every server event except `ready`. A close with code 4404 is reported as a synthetic `inbox.deleted`. */
  onEvent(event: StreamEvent): void
  /** Auth was refused (close 4401/4403) or no token is stored. The stream stays stopped until the inbox id changes. */
  onAuthFailed(): void
}

const MAX_BACKOFF_MS = 30_000
/** After this many failed attempts the status reads 'offline' while retries continue. */
const OFFLINE_AFTER_ATTEMPTS = 3

/**
 * Live request stream for one inbox. The viewer token is sent as the first WebSocket message,
 * never in the URL. Passing an empty id closes the socket. `paused` is a plain flag owned by
 * the caller: every event is still delivered, and the caller decides what to insert while paused.
 */
export function useInboxStream(inboxId: Ref<string> | string, handlers: InboxStreamHandlers) {
  const status = ref<StreamStatus>('connecting')
  const paused = ref(false)

  let socket: WebSocket | null = null
  let timer: ReturnType<typeof setTimeout> | undefined
  let attempt = 0
  let currentId = ''
  let halted = false
  let disposed = false

  function clearTimer(): void {
    if (timer !== undefined) {
      clearTimeout(timer)
      timer = undefined
    }
  }

  function closeSocket(): void {
    clearTimer()
    const ws = socket
    socket = null
    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onclose = null
      ws.onerror = null
      ws.close(1000)
    }
  }

  function halt(): void {
    halted = true
    clearTimer()
    status.value = 'offline'
  }

  function scheduleReconnect(): void {
    clearTimer()
    attempt += 1
    status.value = attempt > OFFLINE_AFTER_ATTEMPTS ? 'offline' : 'reconnecting'
    // While the browser reports no network, wait for the window 'online' event instead of polling.
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return
    const delay = Math.min(1000 * 2 ** (attempt - 1), MAX_BACKOFF_MS)
    timer = setTimeout(() => {
      timer = undefined
      connect()
    }, delay)
  }

  function connect(): void {
    if (disposed || halted || !currentId || socket) return
    const id = currentId
    const ws = new WebSocket(streamUrl(id))
    socket = ws

    ws.onopen = () => {
      // An empty token makes the server close with 4401, which lands in onclose below.
      ws.send(JSON.stringify({ type: 'auth', token: api.token(id) ?? '' }))
    }

    ws.onmessage = (ev: MessageEvent) => {
      if (socket !== ws) return
      let msg: StreamEvent
      try {
        msg = JSON.parse(String(ev.data)) as StreamEvent
      } catch {
        return
      }
      if (msg.type === 'ready') {
        attempt = 0
        status.value = 'live'
        return
      }
      handlers.onEvent(msg)
    }

    ws.onclose = (ev: CloseEvent) => {
      if (socket !== ws) return
      socket = null
      if (disposed) return
      if (ev.code === 4401 || ev.code === 4403) {
        halt()
        handlers.onAuthFailed()
        return
      }
      if (ev.code === 4404) {
        halt()
        handlers.onEvent({ type: 'inbox.deleted' })
        return
      }
      scheduleReconnect()
    }

    // Errors are always followed by a close event, which decides whether to retry.
    ws.onerror = () => {}
  }

  function setInbox(id: string): void {
    closeSocket()
    currentId = id
    halted = false
    attempt = 0
    status.value = id ? 'connecting' : 'offline'
    if (id) connect()
  }

  function onOnline(): void {
    if (disposed || halted || socket || !currentId) return
    clearTimer()
    status.value = 'reconnecting'
    connect()
  }

  watch(() => unref(inboxId), setInbox, { immediate: true })

  if (typeof window !== 'undefined') window.addEventListener('online', onOnline)

  onScopeDispose(() => {
    disposed = true
    closeSocket()
    if (typeof window !== 'undefined') window.removeEventListener('online', onOnline)
  }, true)

  return { status, paused }
}
