<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import { Monitor, Moon, Sun } from 'lucide-vue-next'
import { type ThemeMode, useTheme } from '@/composables/useTheme'

const { theme, cycle } = useTheme()

const NEXT: Record<ThemeMode, ThemeMode> = { light: 'dark', dark: 'system', system: 'light' }
const ICON = { light: Sun, dark: Moon, system: Monitor }

const icon = computed(() => ICON[theme.value])
const description = computed(
  () => `Theme: ${theme.value}. Switch to ${NEXT[theme.value]} theme.`,
)
</script>

<template>
  <div class="bg-airmail h-1.5" aria-hidden="true" />
  <header class="border-b border-rule bg-paper">
    <div
      class="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-x-6 gap-y-1 px-4 py-2 sm:flex-nowrap sm:px-6 sm:py-0 sm:h-14"
    >
      <RouterLink to="/" class="flex min-w-0 items-center gap-2 text-ink">
        <img src="/ri_logo.png" alt="" width="28" height="28" class="h-7 w-7 shrink-0" />
        <span class="truncate text-base font-bold tracking-tight sm:text-lg">Request Inspector</span>
      </RouterLink>

      <button
        type="button"
        class="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-rule bg-sheet text-ink-soft transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-airmail-blue focus-visible:ring-offset-2 focus-visible:ring-offset-paper"
        :aria-label="description"
        :title="description"
        @click="cycle"
      >
        <component :is="icon" :size="18" aria-hidden="true" />
      </button>

      <nav aria-label="Primary" class="order-last flex w-full items-center gap-6 text-sm sm:order-none sm:mr-auto sm:ml-8 sm:w-auto">
        <RouterLink
          to="/new"
          class="inline-flex h-9 items-center border-b-2 border-transparent font-semibold text-ink-soft transition-colors hover:text-ink [&.router-link-active]:border-airmail-blue [&.router-link-active]:text-ink"
        >
          New inbox
        </RouterLink>
        <RouterLink
          to="/open"
          class="inline-flex h-9 items-center border-b-2 border-transparent font-semibold text-ink-soft transition-colors hover:text-ink [&.router-link-active]:border-airmail-blue [&.router-link-active]:text-ink"
        >
          Open inbox
        </RouterLink>
      </nav>
    </div>
  </header>
</template>
