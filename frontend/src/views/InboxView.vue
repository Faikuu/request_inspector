<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { useMediaQuery } from '@vueuse/core'
import { Eye, EyeOff } from 'lucide-vue-next'
import { api, ApiError, AuthError, captureUrl } from '@/api/client'
import type { CapturedRequest, Inbox, StreamEvent } from '@/api/types'
import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/toast'
import InboxHeader from '@/components/inbox/InboxHeader.vue'
import CaptureUrlCard from '@/components/inbox/CaptureUrlCard.vue'
import RequestList from '@/components/inbox/RequestList.vue'
import RequestDetail from '@/components/inbox/RequestDetail.vue'
import { useInboxStream } from '@/composables/useInboxStream'
import { forgetInbox, rememberInbox } from '@/lib/recent'

type Phase = 'loading' | 'locked' | 'notfound' | 'error' | 'ready'

const PAGE_SIZE = 50
const STANDARD_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
const DEFAULT_TITLE = 'Request Inspector'

const route = useRoute()
const router = useRouter()
const { toast } = useToast()
const isDesktop = useMediaQuery('(min-width: 1024px)')

const inboxId = computed(() => String(route.params.id ?? ''))

const phase = ref<Phase>('loading')
const errorMessage = ref('')
const inbox = ref<Inbox | null>(null)
const items = ref<CapturedRequest[]>([])
const pending = ref<CapturedRequest[]>([])
const hasMore = ref(false)
const listLoading = ref(false)
const selectedId = ref<number | null>(null)
/** Mobile only: whether the detail pane is showing instead of the list. */
const showDetail = ref(false)
const filters = reactive({ q: '', method: '' })

const password = ref('')
const showPassword = ref(false)
const gateError = ref('')
const unlocking = ref(false)

let loadSeq = 0
let listSeq = 0
/** Set once the inbox is deleted, so the self-initiated and stream-initiated paths do not both navigate. */
let leaving = false

const streamId = computed(() => (phase.value === 'ready' ? inboxId.value : ''))
const { status, paused } = useInboxStream(streamId, {
  onEvent: handleEvent,
  onAuthFailed: () => lockInbox('Your session has ended. Enter the password to continue.'),
})

const selectedRequest = computed(() => items.value.find((i) => i.id === selectedId.value) ?? null)
const captureHref = computed(() => (inbox.value ? captureUrl(inbox.value) : ''))
const titleSource = computed(() => (inbox.value ? inbox.value.name || 'Untitled inbox' : null))

watch(titleSource, (name) => {
  if (name) document.title = `${name} — ${DEFAULT_TITLE}`
})

onBeforeUnmount(() => {
  document.title = DEFAULT_TITLE
})

function errMsg(e: unknown): string {
  return e instanceof Error ? e.message : 'Something went wrong.'
}

function unlockMessage(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 401) return "That password doesn't match this inbox."
    if (e.status === 429) return 'Too many attempts. Wait a minute and try again.'
  }
  return errMsg(e)
}

/** Runs an action, turning auth failures into the locked state and other failures into a toast. */
async function run<T>(action: () => Promise<T>, failTitle: string): Promise<T | undefined> {
  try {
    return await action()
  } catch (e) {
    if (e instanceof AuthError) {
      lockInbox(e.message)
      return undefined
    }
    toast({ title: failTitle, description: errMsg(e), variant: 'destructive' })
    return undefined
  }
}

function matchesMethod(r: CapturedRequest): boolean {
  if (!filters.method) return true
  if (filters.method === 'OTHER') return !STANDARD_METHODS.includes(r.method)
  return r.method === filters.method
}

/** The API filters by exact method, so "Other" is applied on the client, fetching further pages if needed. */
async function fetchPage(before?: number): Promise<{ items: CapturedRequest[]; hasMore: boolean }> {
  const wantOther = filters.method === 'OTHER'
  const serverMethod = filters.method && !wantOther ? filters.method : undefined
  let cursor = before
  let collected: CapturedRequest[] = []
  let more = true
  for (let round = 0; round < 6; round++) {
    const page = await api.listRequests(inboxId.value, {
      limit: PAGE_SIZE,
      before_id: cursor,
      method: serverMethod,
      q: filters.q || undefined,
    })
    collected = collected.concat(page.items.filter(matchesMethod))
    more = page.has_more
    if (!page.items.length) break
    cursor = page.items[page.items.length - 1].id
    if (!wantOther || !more || collected.length >= PAGE_SIZE / 2) break
  }
  return { items: collected, hasMore: more }
}

function ensureSelection(): void {
  if (selectedId.value !== null && items.value.some((i) => i.id === selectedId.value)) return
  if (isDesktop.value) {
    selectedId.value = items.value[0]?.id ?? null
  } else {
    selectedId.value = null
    showDetail.value = false
  }
}

function lockInbox(message = ''): void {
  api.lock(inboxId.value)
  phase.value = 'locked'
  inbox.value = null
  items.value = []
  pending.value = []
  hasMore.value = false
  selectedId.value = null
  showDetail.value = false
  password.value = ''
  gateError.value = message
}

async function loadInbox(): Promise<void> {
  const seq = ++loadSeq
  phase.value = 'loading'
  leaving = false
  try {
    const [loaded, page] = await Promise.all([api.getInbox(inboxId.value), fetchPage()])
    if (seq !== loadSeq) return
    inbox.value = loaded
    items.value = page.items
    hasMore.value = page.hasMore
    pending.value = []
    ensureSelection()
    rememberInbox({ id: loaded.id, name: loaded.name })
    phase.value = 'ready'
  } catch (e) {
    if (seq !== loadSeq) return
    if (e instanceof AuthError) {
      lockInbox(e.message)
    } else if (e instanceof ApiError && e.status === 404) {
      forgetInbox(inboxId.value)
      phase.value = 'notfound'
    } else {
      errorMessage.value = errMsg(e)
      phase.value = 'error'
    }
  }
}

async function start(): Promise<void> {
  inbox.value = null
  items.value = []
  pending.value = []
  hasMore.value = false
  selectedId.value = null
  showDetail.value = false
  filters.q = ''
  filters.method = ''
  gateError.value = ''
  password.value = ''
  if (!api.hasSession(inboxId.value)) {
    phase.value = 'locked'
    return
  }
  await loadInbox()
}

async function unlock(): Promise<void> {
  if (!password.value || unlocking.value) return
  unlocking.value = true
  gateError.value = ''
  try {
    await api.unlock(inboxId.value, password.value)
    password.value = ''
    await loadInbox()
  } catch (e) {
    gateError.value = unlockMessage(e)
  } finally {
    unlocking.value = false
  }
}

async function refreshList(): Promise<void> {
  const seq = ++listSeq
  listLoading.value = true
  const page = await run(() => fetchPage(), 'Could not load requests')
  if (seq !== listSeq) return
  listLoading.value = false
  if (!page) return
  items.value = page.items
  hasMore.value = page.hasMore
  ensureSelection()
}

function applyFilters(next: { q: string; method: string }): void {
  filters.q = next.q
  filters.method = next.method
  void refreshList()
}

async function loadMore(): Promise<void> {
  const last = items.value[items.value.length - 1]
  if (!last || listLoading.value) return
  const seq = listSeq
  listLoading.value = true
  const page = await run(() => fetchPage(last.id), 'Could not load older requests')
  if (seq !== listSeq) return
  listLoading.value = false
  if (!page) return
  const seen = new Set(items.value.map((i) => i.id))
  items.value = [...items.value, ...page.items.filter((i) => !seen.has(i.id))]
  hasMore.value = page.hasMore
}

function selectRequest(id: number): void {
  selectedId.value = id
  showDetail.value = true
}

/** Removes a request from the list and moves the selection to a neighbour. Returns false if it was not loaded. */
function removeItem(rid: number): void {
  pending.value = pending.value.filter((i) => i.id !== rid)
  const idx = items.value.findIndex((i) => i.id === rid)
  if (idx === -1) return
  const neighbour = items.value[idx + 1] ?? items.value[idx - 1] ?? null
  items.value = items.value.filter((i) => i.id !== rid)
  if (inbox.value) {
    inbox.value = { ...inbox.value, request_count: Math.max(0, inbox.value.request_count - 1) }
  }
  if (selectedId.value === rid) {
    if (isDesktop.value) {
      selectedId.value = neighbour?.id ?? null
    } else {
      selectedId.value = null
      showDetail.value = false
    }
  }
}

async function deleteRequest(rid: number): Promise<void> {
  const ok = await run(async () => {
    await api.deleteRequest(inboxId.value, rid)
    return true
  }, 'Could not delete request')
  if (ok) removeItem(rid)
}

function applyCleared(): void {
  items.value = []
  pending.value = []
  hasMore.value = false
  selectedId.value = null
  showDetail.value = false
  if (inbox.value) inbox.value = { ...inbox.value, request_count: 0 }
}

async function clearRequests(): Promise<void> {
  const ok = await run(async () => {
    await api.clearRequests(inboxId.value)
    return true
  }, 'Could not clear requests')
  if (ok) {
    applyCleared()
    toast({ title: 'All requests cleared' })
  }
}

async function rotateKey(): Promise<void> {
  const updated = await run(() => api.rotateKey(inboxId.value), 'Could not rotate the capture URL')
  if (updated) {
    inbox.value = updated
    toast({ title: 'Capture URL rotated', description: 'The old URL no longer accepts requests.' })
  }
}

async function renameInbox(name: string | null): Promise<void> {
  const updated = await run(() => api.renameInbox(inboxId.value, name), 'Could not rename the inbox')
  if (updated) {
    inbox.value = updated
    rememberInbox({ id: updated.id, name: updated.name })
  }
}

async function exportJson(): Promise<void> {
  const rows = await run(() => api.exportRequests(inboxId.value), 'Could not export requests')
  if (!rows) return
  const blob = new Blob([JSON.stringify(rows, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `inbox-${inboxId.value}.json`
  document.body.appendChild(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

/** Leaves the page once the inbox is gone; the stream and the delete action can both report it. */
function inboxGone(): void {
  if (leaving) return
  leaving = true
  forgetInbox(inboxId.value)
  api.lock(inboxId.value)
  toast({ title: 'Inbox deleted' })
  void router.push('/')
}

async function deleteInbox(): Promise<void> {
  const ok = await run(async () => {
    await api.deleteInbox(inboxId.value)
    return true
  }, 'Could not delete the inbox')
  if (ok) inboxGone()
}

function lockNow(): void {
  lockInbox('')
}

function flushPending(): void {
  if (!pending.value.length) return
  const seen = new Set(items.value.map((i) => i.id))
  items.value = [...pending.value.filter((i) => !seen.has(i.id)), ...items.value]
  pending.value = []
  ensureSelection()
}

function togglePause(): void {
  if (paused.value) {
    paused.value = false
    flushPending()
  } else {
    paused.value = true
  }
}

function onCreated(r: CapturedRequest): void {
  if (items.value.some((i) => i.id === r.id) || pending.value.some((i) => i.id === r.id)) return
  if (inbox.value) inbox.value = { ...inbox.value, request_count: inbox.value.request_count + 1 }
  if (!matchesMethod(r)) return
  if (paused.value) {
    pending.value = [r, ...pending.value]
    return
  }
  items.value = [r, ...items.value]
  ensureSelection()
}

function handleEvent(e: StreamEvent): void {
  switch (e.type) {
    case 'ready':
      return
    case 'request.created':
      onCreated(e.data)
      return
    case 'request.deleted':
      removeItem(e.id)
      return
    case 'requests.cleared':
      applyCleared()
      return
    case 'inbox.updated':
      inbox.value = e.data
      return
    case 'inbox.deleted':
      inboxGone()
      return
  }
}

watch(inboxId, () => {
  void start()
}, { immediate: true })
</script>

<template>
  <div class="mx-auto w-full max-w-[1400px] px-4 py-6 lg:px-8 lg:py-8">
    <!-- Loading -->
    <div v-if="phase === 'loading'" role="status" class="space-y-4">
      <span class="sr-only">Loading inbox</span>
      <div class="h-9 w-2/5 max-w-sm rounded-md bg-rule/40" />
      <div class="h-4 w-1/4 rounded bg-rule/40" />
      <div class="h-24 rounded-lg bg-rule/40" />
      <div class="grid gap-6 lg:grid-cols-[minmax(300px,380px)_1fr]">
        <div class="space-y-3">
          <div v-for="n in 5" :key="n" class="h-12 rounded-md bg-rule/40" />
        </div>
        <div class="h-96 rounded-lg bg-rule/40" />
      </div>
    </div>

    <!-- Locked: password gate -->
    <section v-else-if="phase === 'locked'" class="mx-auto mt-12 max-w-sm sm:mt-20" aria-labelledby="unlock-heading">
      <h1 id="unlock-heading" class="text-[24px] font-bold tracking-tight">Unlock inbox</h1>
      <p class="mt-2 text-[15px] text-ink-soft">Enter the inbox password to see its requests.</p>
      <p class="mt-3 break-all font-mono text-[13px] text-ink">{{ inboxId }}</p>

      <form class="mt-6 space-y-4" @submit.prevent="unlock">
        <div class="space-y-1.5">
          <label for="inbox-password" class="text-[13px] font-medium text-ink">Password</label>
          <div class="relative">
            <Input
              id="inbox-password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
              class="h-10 bg-sheet pr-11"
              :aria-invalid="gateError ? 'true' : undefined"
              :aria-describedby="gateError ? 'gate-error' : undefined"
            />
            <button
              type="button"
              class="absolute right-1 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-ink-soft hover:text-ink"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" class="size-4" aria-hidden="true" />
              <Eye v-else class="size-4" aria-hidden="true" />
            </button>
          </div>
        </div>
        <p v-if="gateError" id="gate-error" role="alert" class="text-[13px] text-airmail-red">{{ gateError }}</p>
        <Button type="submit" class="w-full" :disabled="unlocking">Unlock</Button>
      </form>
    </section>

    <!-- Not found -->
    <section v-else-if="phase === 'notfound'" class="mx-auto mt-12 max-w-md sm:mt-20">
      <h1 class="text-[24px] font-bold tracking-tight">Inbox not found</h1>
      <p class="mt-2 text-[15px] text-ink-soft">This inbox doesn't exist or was deleted.</p>
      <div class="mt-6">
        <RouterLink to="/new" :class="buttonVariants()">Create a new inbox</RouterLink>
      </div>
    </section>

    <!-- Error -->
    <section v-else-if="phase === 'error'" class="mx-auto mt-12 max-w-md sm:mt-20">
      <h1 class="text-[24px] font-bold tracking-tight">Could not load this inbox</h1>
      <p class="mt-2 text-[15px] text-ink-soft">{{ errorMessage }}</p>
      <Button variant="outline" class="mt-6" @click="loadInbox()">Try again</Button>
    </section>

    <!-- Ready -->
    <div v-else-if="inbox" class="space-y-5">
      <InboxHeader
        :inbox="inbox"
        :status="status"
        :paused="paused"
        :pending-count="pending.length"
        @rename="renameInbox"
        @export-json="exportJson"
        @toggle-pause="togglePause"
        @show-pending="flushPending"
        @lock="lockNow"
        @rotate-key="rotateKey"
        @clear-requests="clearRequests"
        @delete-inbox="deleteInbox"
      />

      <CaptureUrlCard :url="captureHref" />

      <div class="grid gap-6 lg:grid-cols-[minmax(300px,380px)_1fr]">
        <div class="min-w-0" :class="{ 'hidden lg:block': showDetail }">
          <RequestList
            :items="items"
            :selected-id="selectedId"
            :has-more="hasMore"
            :loading="listLoading"
            :q="filters.q"
            :method="filters.method"
            :capture-url="captureHref"
            @select="selectRequest"
            @load-more="loadMore"
            @filter="applyFilters"
          />
        </div>
        <div class="min-w-0 lg:h-[calc(100vh-12rem)] lg:overflow-y-auto" :class="{ 'hidden lg:block': !showDetail }">
          <RequestDetail
            :request="selectedRequest"
            :capture-url="captureHref"
            @delete="selectedRequest && deleteRequest(selectedRequest.id)"
            @back="showDetail = false"
          />
        </div>
      </div>
    </div>
  </div>
</template>
