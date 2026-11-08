<script setup lang="ts">
import { RouterLink } from 'vue-router'
import MethodStamp from '@/components/MethodStamp.vue'
import RecentInboxes from '@/components/RecentInboxes.vue'
import { buttonVariants } from '@/components/ui/button'
import { formatBytes, relativeTime } from '@/lib/format'

const CAPTURE_URL = 'https://example.com/api/hook/k7Qz2mVpX4rT9aLw'

// Sample rows for the preview. `ago` is milliseconds before the page loaded.
const loadedAt = Date.now()
const samples = [
  { method: 'POST', path: '/orders/42', bytes: 2100, ago: 12_000 },
  { method: 'GET', path: '/health', bytes: 0, ago: 41_000 },
  { method: 'PUT', path: '/users/7/settings', bytes: 512, ago: 4 * 60_000 },
  { method: 'DELETE', path: '/sessions/a91f', bytes: 0, ago: 3 * 3_600_000 },
]
</script>

<template>
  <div class="mx-auto w-full max-w-6xl px-4 sm:px-6">
    <section class="grid gap-12 pt-12 pb-10 sm:pt-20 lg:grid-cols-2 lg:items-center lg:gap-16">
      <div>
        <h1 class="text-4xl font-extrabold leading-[1.05] tracking-tight text-ink sm:text-[56px]">
          See exactly what your app sends.
        </h1>
        <p class="mt-6 max-w-[60ch] text-[18px] leading-relaxed text-ink-soft">
          Create an inbox and point a webhook or your code at its capture URL. Every request that
          arrives shows up live, with its method, headers, query string and body.
        </p>
        <div class="mt-8 flex flex-col gap-3 sm:flex-row">
          <RouterLink to="/new" :class="buttonVariants({ size: 'lg' })">Create inbox</RouterLink>
          <RouterLink to="/open" :class="buttonVariants({ variant: 'outline', size: 'lg' })">
            Open an existing inbox
          </RouterLink>
        </div>
      </div>

      <div
        class="relative overflow-hidden rounded-lg border border-rule bg-sheet"
        aria-hidden="true"
      >
        <div class="bg-airmail absolute inset-y-0 left-0 w-1.5" />
        <div class="py-5 pl-6 pr-4 sm:pl-7 sm:pr-5">
          <p class="text-xs text-ink-soft">Capture URL</p>
          <p class="mt-1 break-all font-mono text-sm text-ink">{{ CAPTURE_URL }}</p>
          <ul class="mt-4 divide-y divide-rule border-t border-rule">
            <li
              v-for="(s, i) in samples"
              :key="s.path"
              class="capture-row flex items-center gap-2.5 py-3 sm:gap-3"
              :style="{ '--i': i }"
            >
              <MethodStamp :method="s.method" size="sm" />
              <span class="min-w-0 flex-1 truncate font-mono text-sm text-ink">{{ s.path }}</span>
              <span class="shrink-0 text-xs tabular-nums text-ink-soft">{{ formatBytes(s.bytes) }}</span>
              <span class="w-[4.5rem] shrink-0 text-right text-xs text-ink-soft">
                {{ relativeTime(new Date(loadedAt - s.ago), loadedAt) }}
              </span>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <RecentInboxes />

    <section aria-labelledby="how-it-works" class="border-t border-rule py-12 sm:py-16">
      <h2 id="how-it-works" class="text-2xl font-bold tracking-tight">How it works</h2>
      <ol class="mt-6 max-w-[60ch] list-decimal space-y-4 pl-5 text-[15px] leading-relaxed text-ink marker:font-semibold marker:text-ink-soft">
        <li><span class="font-semibold">Create an inbox</span> with a password.</li>
        <li>
          <span class="font-semibold">Send requests</span> to its capture URL from anything: curl,
          a webhook, your app.
        </li>
        <li>
          <span class="font-semibold">Inspect</span> bodies, headers and query strings live, then
          export or clear them.
        </li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
/* The one orchestrated motion on the site: sample rows arrive one after another. */
.capture-row {
  opacity: 0;
  animation: capture-in 180ms ease-out forwards;
  animation-delay: calc(300ms + var(--i) * 250ms);
}

@keyframes capture-in {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .capture-row {
    opacity: 1;
    animation: none;
  }
}
</style>
