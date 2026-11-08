<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import Input from '@/components/ui/input/Input.vue'
import RecentInboxes from '@/components/RecentInboxes.vue'

const router = useRouter()

const raw = ref('')
const submitAttempted = ref(false)

// Inbox IDs are UUIDs. Accepts a bare ID or a link such as https://host/i/<id>.
const ID_PATTERN = /^[A-Za-z0-9-]{8,64}$/

function parseInboxId(input: string): string | null {
  const text = input.trim()
  if (!text) return null
  const fromPath = text.match(/\/(?:i|inspector)\/([^/?#\s]+)/)
  const candidate = fromPath ? fromPath[1] : text
  return ID_PATTERN.test(candidate) ? candidate : null
}

const parsed = computed(() => parseInboxId(raw.value))
const error = computed(() => {
  if (!submitAttempted.value || parsed.value) return ''
  return raw.value.trim() ? "That doesn't look like an inbox ID. Paste the ID or the inbox link." : 'Enter an inbox ID or paste its link.'
})

function onSubmit(): void {
  submitAttempted.value = true
  if (!parsed.value) {
    document.getElementById('inbox-id')?.focus()
    return
  }
  router.push(`/i/${parsed.value}`)
}
</script>

<template>
  <div class="mx-auto w-full max-w-6xl px-4 sm:px-6">
    <section class="max-w-md py-10 sm:py-16">
      <h1 class="text-2xl font-bold tracking-tight sm:text-4xl">Open an inbox</h1>
      <p class="mt-3 text-[15px] leading-relaxed text-ink-soft">
        Paste the inbox ID or its link. You'll be asked for the password next.
      </p>

      <form class="mt-8 space-y-6" novalidate @submit.prevent="onSubmit">
        <div>
          <label for="inbox-id" class="block text-sm font-semibold">Inbox ID</label>
          <Input
            id="inbox-id"
            v-model="raw"
            class="mt-1.5 font-mono"
            type="text"
            autocomplete="off"
            autocapitalize="off"
            spellcheck="false"
            placeholder="ID or link to the inbox"
            :aria-invalid="error ? 'true' : undefined"
            :aria-describedby="error ? 'inbox-id-error' : undefined"
          />
          <p v-if="error" id="inbox-id-error" class="mt-1.5 text-sm text-airmail-red">{{ error }}</p>
        </div>

        <div class="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Button type="submit" class="w-full sm:w-auto">Open inbox</Button>
          <RouterLink to="/new" class="text-sm font-semibold text-airmail-blue underline-offset-4 hover:underline">
            Create a new inbox instead
          </RouterLink>
        </div>
      </form>
    </section>

    <RecentInboxes />
  </div>
</template>
