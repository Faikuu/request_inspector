<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { X } from 'lucide-vue-next'
import { forgetInbox, getRecent, type RecentInbox } from '@/lib/recent'
import { relativeTime } from '@/lib/format'

const items = ref<RecentInbox[]>(getRecent())

function remove(id: string): void {
  forgetInbox(id)
  items.value = getRecent()
}
</script>

<template>
  <section v-if="items.length" aria-labelledby="recent-inboxes-heading" class="py-10 sm:py-12">
    <h2 id="recent-inboxes-heading" class="text-2xl font-bold tracking-tight">Recent inboxes</h2>
    <ul class="mt-4 divide-y divide-rule border-y border-rule">
      <li v-for="item in items" :key="item.id" class="flex items-center gap-3 py-3">
        <RouterLink
          :to="`/i/${item.id}`"
          class="group min-w-0 flex-1 rounded-sm text-ink"
        >
          <span class="block truncate font-semibold group-hover:underline">{{ item.name || 'Untitled inbox' }}</span>
          <span class="block truncate font-mono text-xs text-ink-soft">{{ item.id }}</span>
          <span class="block text-xs text-ink-soft">opened {{ relativeTime(new Date(item.openedAt)) }}</span>
        </RouterLink>
        <button
          type="button"
          class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md text-ink-soft transition-colors hover:bg-sheet hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-airmail-blue focus-visible:ring-offset-2 focus-visible:ring-offset-paper"
          :aria-label="`Remove ${item.name || 'untitled inbox'} from this list`"
          title="Remove from list"
          @click="remove(item.id)"
        >
          <X :size="16" aria-hidden="true" />
        </button>
      </li>
    </ul>
  </section>
</template>
