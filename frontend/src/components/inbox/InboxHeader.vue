<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { Download, Ellipsis, Eraser, Lock, Pause, Pencil, Play, RotateCw, Trash2 } from 'lucide-vue-next'
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from 'radix-vue'
import type { Inbox } from '@/api/types'
import { Button } from '@/components/ui/button'
import ConfirmDialog from '@/components/inbox/ConfirmDialog.vue'
import type { StreamStatus } from '@/composables/useInboxStream'
import { fullDate } from '@/lib/format'

const props = defineProps<{
  inbox: Inbox
  status: StreamStatus
  paused: boolean
  pendingCount: number
}>()

const emit = defineEmits<{
  rename: [name: string | null]
  exportJson: []
  togglePause: []
  showPending: []
  lock: []
  rotateKey: []
  clearRequests: []
  deleteInbox: []
}>()

const STATUS_LABEL: Record<StreamStatus, string> = {
  connecting: 'Connecting…',
  live: 'Live',
  reconnecting: 'Reconnecting…',
  offline: 'Offline',
}
const statusLabel = computed(() => STATUS_LABEL[props.status])
const pendingLabel = computed(() =>
  props.pendingCount === 1 ? 'Show 1 new request' : `Show ${props.pendingCount} new requests`,
)

// Inline rename: Enter or blur saves, Escape cancels.
const editing = ref(false)
const draft = ref('')
const nameField = ref<HTMLInputElement | null>(null)

function startEdit(): void {
  draft.value = props.inbox.name ?? ''
  editing.value = true
  void nextTick(() => {
    nameField.value?.focus()
    nameField.value?.select()
  })
}

function commit(): void {
  if (!editing.value) return
  editing.value = false
  const next = draft.value.trim() || null
  if (next !== (props.inbox.name || null)) emit('rename', next)
}

function cancel(): void {
  editing.value = false
}

// Confirmations for destructive actions.
type ConfirmAction = 'rotateKey' | 'clearRequests' | 'deleteInbox'
const CONFIRMS: Record<ConfirmAction, { title: string; description: string; confirmLabel: string; destructive: boolean }> = {
  rotateKey: {
    title: 'Rotate the capture URL?',
    description: 'The current capture URL stops accepting requests straight away. Update anything that sends to it.',
    confirmLabel: 'Rotate URL',
    destructive: false,
  },
  clearRequests: {
    title: 'Clear all requests?',
    description: 'Every captured request in this inbox is deleted. This can’t be undone.',
    confirmLabel: 'Clear all requests',
    destructive: true,
  },
  deleteInbox: {
    title: 'Delete this inbox?',
    description: 'The inbox, its capture URL and all of its requests are deleted permanently.',
    confirmLabel: 'Delete inbox',
    destructive: true,
  },
}
const confirmOpen = ref(false)
const confirmAction = ref<ConfirmAction>('rotateKey')
const confirmCopy = computed(() => CONFIRMS[confirmAction.value])

function askFor(action: ConfirmAction): void {
  confirmAction.value = action
  confirmOpen.value = true
}

function runConfirmed(): void {
  switch (confirmAction.value) {
    case 'rotateKey':
      emit('rotateKey')
      break
    case 'clearRequests':
      emit('clearRequests')
      break
    case 'deleteInbox':
      emit('deleteInbox')
      break
  }
}
</script>

<template>
  <header class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
    <div class="min-w-0 flex-1">
      <form v-if="editing" class="max-w-xl" @submit.prevent="commit">
        <input
          ref="nameField"
          v-model="draft"
          type="text"
          maxlength="80"
          placeholder="Untitled inbox"
          aria-label="Inbox name"
          class="h-12 w-full rounded-md border border-rule bg-sheet px-3 text-[24px] font-bold tracking-tight text-ink placeholder:text-ink-soft"
          @keydown.esc.prevent="cancel"
          @blur="commit"
        />
      </form>
      <div v-else class="flex min-w-0 items-center gap-2">
        <h1
          class="min-w-0 break-words text-[24px] font-bold leading-tight tracking-tight sm:text-[36px]"
          :class="inbox.name ? 'text-ink' : 'text-ink-soft'"
        >
          {{ inbox.name || 'Untitled inbox' }}
        </h1>
        <Button variant="ghost" size="sm" class="shrink-0" @click="startEdit">
          <Pencil class="size-4" aria-hidden="true" />
          Rename
        </Button>
      </div>
      <p class="mt-1 text-[13px] text-ink-soft">
        Created <time :datetime="inbox.created_at">{{ fullDate(inbox.created_at) }}</time>
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-2">
      <span class="inline-flex items-center gap-2 px-1 text-[13px]" aria-live="polite">
        <span
          class="size-2 shrink-0 rounded-full"
          :class="status === 'live' ? 'bg-live' : 'bg-ink-soft'"
          aria-hidden="true"
        />
        <span :class="status === 'live' ? 'text-ink' : 'text-ink-soft'">{{ statusLabel }}</span>
      </span>

      <Button variant="outline" size="sm" @click="emit('togglePause')">
        <Play v-if="paused" class="size-4" aria-hidden="true" />
        <Pause v-else class="size-4" aria-hidden="true" />
        {{ paused ? 'Resume' : 'Pause' }}
      </Button>
      <Button v-if="paused && pendingCount > 0" variant="outline" size="sm" @click="emit('showPending')">
        {{ pendingLabel }}
      </Button>
      <span class="sr-only" aria-live="polite">
        {{ paused && pendingCount > 0 ? `${pendingCount} new requests held while paused.` : '' }}
      </span>

      <Button variant="outline" size="sm" @click="emit('exportJson')">
        <Download class="size-4" aria-hidden="true" />
        Export JSON
      </Button>

      <DropdownMenuRoot>
        <DropdownMenuTrigger as-child>
          <Button variant="outline" size="icon" aria-label="More actions">
            <Ellipsis class="size-4" aria-hidden="true" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuPortal>
          <DropdownMenuContent
            align="end"
            :side-offset="6"
            class="z-50 min-w-[220px] rounded-lg border border-rule bg-sheet p-1 text-[15px] text-ink shadow-sm"
            @close-auto-focus="(e: Event) => e.preventDefault()"
          >
            <DropdownMenuItem
              class="flex cursor-default select-none items-center gap-2 rounded-md px-2.5 py-2 outline-none data-[highlighted]:bg-paper"
              @select="emit('lock')"
            >
              <Lock class="size-4" aria-hidden="true" />
              Lock inbox
            </DropdownMenuItem>
            <DropdownMenuItem
              class="flex cursor-default select-none items-center gap-2 rounded-md px-2.5 py-2 outline-none data-[highlighted]:bg-paper"
              @select="askFor('rotateKey')"
            >
              <RotateCw class="size-4" aria-hidden="true" />
              Rotate capture URL
            </DropdownMenuItem>
            <DropdownMenuItem
              class="flex cursor-default select-none items-center gap-2 rounded-md px-2.5 py-2 outline-none data-[highlighted]:bg-paper"
              @select="askFor('clearRequests')"
            >
              <Eraser class="size-4" aria-hidden="true" />
              Clear all requests
            </DropdownMenuItem>
            <DropdownMenuSeparator class="my-1 h-px bg-rule" />
            <DropdownMenuItem
              class="flex cursor-default select-none items-center gap-2 rounded-md px-2.5 py-2 text-airmail-red outline-none data-[highlighted]:bg-paper"
              @select="askFor('deleteInbox')"
            >
              <Trash2 class="size-4" aria-hidden="true" />
              Delete inbox
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenuPortal>
      </DropdownMenuRoot>
    </div>

    <ConfirmDialog
      :open="confirmOpen"
      :title="confirmCopy.title"
      :description="confirmCopy.description"
      :confirm-label="confirmCopy.confirmLabel"
      :destructive="confirmCopy.destructive"
      @update:open="confirmOpen = $event"
      @confirm="runConfirmed"
    />
  </header>
</template>
