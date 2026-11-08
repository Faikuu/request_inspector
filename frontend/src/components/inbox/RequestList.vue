<script setup lang="ts">
import { computed, nextTick, onScopeDispose, ref, watch } from 'vue'
import { useNow } from '@vueuse/core'
import { Search } from 'lucide-vue-next'
import type { CapturedRequest } from '@/api/types'
import MethodStamp from '@/components/MethodStamp.vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import CodeBlock from '@/components/inbox/CodeBlock.vue'
import { formatBytes, fullDate, relativeTime } from '@/lib/format'
import { sendSnippets } from '@/lib/snippets'

const props = defineProps<{
  items: CapturedRequest[]
  selectedId: number | null
  hasMore: boolean
  loading: boolean
  /** Current server-side filters, owned by the parent. */
  q: string
  method: string
  captureUrl: string
}>()

const emit = defineEmits<{
  select: [id: number]
  loadMore: []
  filter: [filters: { q: string; method: string }]
}>()

const METHOD_OPTIONS = [
  { value: '', label: 'All methods' },
  { value: 'GET', label: 'GET' },
  { value: 'POST', label: 'POST' },
  { value: 'PUT', label: 'PUT' },
  { value: 'PATCH', label: 'PATCH' },
  { value: 'DELETE', label: 'DELETE' },
  { value: 'OTHER', label: 'Other' },
]

const SEARCH_DEBOUNCE_MS = 300

const now = useNow({ interval: 15_000 })
const filtered = computed(() => Boolean(props.q || props.method))
const curlSnippet = computed(() => sendSnippets(props.captureUrl).find((s) => s.id === 'curl')?.code ?? '')

// Search text is local until the debounce fires, so typing does not refetch on every key.
const qInput = ref(props.q)
watch(
  () => props.q,
  (value) => {
    if (value !== qInput.value.trim()) qInput.value = value
  },
)

let debounceTimer: ReturnType<typeof setTimeout> | undefined
onScopeDispose(() => clearTimeout(debounceTimer))

function onSearchInput(): void {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    emit('filter', { q: qInput.value.trim(), method: props.method })
  }, SEARCH_DEBOUNCE_MS)
}

function onMethodChange(event: Event): void {
  clearTimeout(debounceTimer)
  emit('filter', { q: qInput.value.trim(), method: (event.target as HTMLSelectElement).value })
}

function clearFilters(): void {
  clearTimeout(debounceTimer)
  qInput.value = ''
  emit('filter', { q: '', method: '' })
}

// Roving focus: arrow keys move the selection and focus together.
const rowEls = new Map<number, HTMLElement>()

function setRow(id: number, el: unknown): void {
  if (el instanceof HTMLElement) rowEls.set(id, el)
  else rowEls.delete(id)
}

function onRowKeydown(event: KeyboardEvent, index: number): void {
  const step = event.key === 'ArrowDown' ? 1 : event.key === 'ArrowUp' ? -1 : 0
  if (!step || !props.items.length) return
  event.preventDefault()
  const next = props.items[Math.min(props.items.length - 1, Math.max(0, index + step))]
  emit('select', next.id)
  void nextTick(() => rowEls.get(next.id)?.focus())
}

function tabIndexFor(index: number, id: number): number {
  const isStop = props.selectedId === id || (props.selectedId === null && index === 0)
  return isStop ? 0 : -1
}
</script>

<template>
  <section
    class="flex min-w-0 flex-col rounded-lg lg:h-[calc(100vh-12rem)] lg:overflow-hidden"
    aria-label="Captured requests"
  >
    <div class="flex shrink-0 gap-2 pb-3">
      <div class="relative min-w-0 flex-1">
        <Search class="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-ink-soft" aria-hidden="true" />
        <Input
          v-model="qInput"
          type="search"
          placeholder="Search path, headers, body"
          aria-label="Search requests"
          class="h-10 bg-sheet pl-9 text-[15px]"
          @update:model-value="onSearchInput"
        />
      </div>
      <select
        :value="method"
        aria-label="Filter by method"
        class="h-10 shrink-0 rounded-md border border-rule bg-sheet px-2 text-[15px] text-ink"
        @change="onMethodChange"
      >
        <option v-for="o in METHOD_OPTIONS" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
    </div>

    <div class="min-h-0 flex-1 overflow-y-auto">
      <div v-if="!items.length && loading" role="status" class="space-y-3 p-3">
        <span class="sr-only">Loading requests</span>
        <div v-for="n in 4" :key="n" class="h-14 rounded-md bg-rule/40" />
      </div>

      <div v-else-if="!items.length && filtered" class="p-6">
        <p class="text-[18px] font-bold tracking-tight">No requests match these filters.</p>
        <Button variant="outline" size="sm" class="mt-3" @click="clearFilters">Clear filters</Button>
      </div>

      <div v-else-if="!items.length" class="p-6">
        <p class="text-[18px] font-bold tracking-tight">Nothing here yet.</p>
        <p class="mt-1 text-[15px] text-ink-soft">
          Send a request to the capture URL above and it will show up instantly.
        </p>
        <div class="mt-4">
          <CodeBlock :text="curlSnippet" kind="text" />
        </div>
      </div>

      <TransitionGroup v-else tag="ul" name="arrive" class="divide-y divide-rule">
        <li v-for="(r, i) in items" :key="r.id">
          <button
            :ref="(el) => setRow(r.id, el)"
            type="button"
            class="flex w-full min-w-0 items-center gap-3 border-l-2 px-3 py-2.5 text-left transition-colors"
            :class="selectedId === r.id ? 'border-airmail-blue bg-sheet' : 'border-transparent hover:bg-sheet/60'"
            :tabindex="tabIndexFor(i, r.id)"
            :aria-current="selectedId === r.id ? 'true' : undefined"
            @click="emit('select', r.id)"
            @keydown="onRowKeydown($event, i)"
          >
            <MethodStamp :method="r.method" size="sm" class="shrink-0" />
            <span class="min-w-0 flex-1">
              <span class="block truncate font-mono text-[13px] text-ink">{{ r.path }}</span>
              <span class="block text-[13px] text-ink-soft">{{ formatBytes(r.size) }}</span>
            </span>
            <time
              class="shrink-0 self-start text-[13px] text-ink-soft"
              :datetime="r.created_at"
              :title="fullDate(r.created_at)"
            >{{ relativeTime(r.created_at, now.getTime()) }}</time>
          </button>
        </li>
      </TransitionGroup>

      <div v-if="hasMore" class="border-t border-rule p-3">
        <Button variant="outline" size="sm" class="w-full" :disabled="loading" @click="emit('loadMore')">
          Load older requests
        </Button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.arrive-enter-active {
  transition:
    opacity 180ms ease-out,
    transform 180ms ease-out;
}
.arrive-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
