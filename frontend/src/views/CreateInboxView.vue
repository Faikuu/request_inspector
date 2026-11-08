<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff, Loader2 } from 'lucide-vue-next'
import { api, ApiError } from '@/api/client'
import { Button } from '@/components/ui/button'
import Input from '@/components/ui/input/Input.vue'
import { rememberInbox } from '@/lib/recent'

const router = useRouter()

const name = ref('')
const password = ref('')
const confirm = ref('')
const showPassword = ref(false)
const submitting = ref(false)
const serverError = ref('')
const submitAttempted = ref(false)
const touched = reactive({ name: false, password: false, confirm: false })

type Field = 'name' | 'password' | 'confirm'

const errors = computed<Partial<Record<Field, string>>>(() => {
  const e: Partial<Record<Field, string>> = {}
  if (name.value.length > 80) e.name = 'Keep the name to 80 characters or fewer.'
  if (!password.value) e.password = 'Enter a password.'
  else if (password.value.length < 8) e.password = 'Use at least 8 characters.'
  else if (password.value.length > 128) e.password = 'Use 128 characters or fewer.'
  if (!confirm.value) e.confirm = 'Type the password again.'
  else if (confirm.value !== password.value) e.confirm = "Passwords don't match."
  return e
})

const hasErrors = computed(() => Object.keys(errors.value).length > 0)

function shownError(field: Field): string | undefined {
  return submitAttempted.value || touched[field] ? errors.value[field] : undefined
}

function describedBy(field: Field, help?: string): string | undefined {
  const ids = [help, shownError(field) ? `${field}-error` : undefined].filter(Boolean)
  return ids.length ? ids.join(' ') : undefined
}

async function onSubmit(): Promise<void> {
  submitAttempted.value = true
  serverError.value = ''
  if (hasErrors.value) {
    const first = (['name', 'password', 'confirm'] as Field[]).find((f) => errors.value[f])
    if (first) document.getElementById(first)?.focus()
    return
  }

  submitting.value = true
  try {
    const session = await api.createInbox(password.value, name.value)
    rememberInbox({ id: session.inbox.id, name: session.inbox.name })
    await router.push(`/i/${session.inbox.id}`)
  } catch (err) {
    serverError.value =
      err instanceof ApiError ? err.message : 'Could not create the inbox. Try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="mx-auto w-full max-w-6xl px-4 py-10 sm:px-6 sm:py-16">
    <div class="max-w-md">
      <h1 class="text-2xl font-bold tracking-tight sm:text-4xl">Create an inbox</h1>
      <p class="mt-3 text-[15px] leading-relaxed text-ink-soft">
        Requests sent to the capture URL are stored here. Only someone with the password can read them.
      </p>

      <form class="mt-8 space-y-6" novalidate @submit.prevent="onSubmit">
        <div>
          <label for="name" class="block text-sm font-semibold">
            Name <span class="font-normal text-ink-soft">(optional)</span>
          </label>
          <Input
            id="name"
            v-model="name"
            class="mt-1.5"
            type="text"
            maxlength="80"
            autocomplete="off"
            placeholder="Stripe webhooks"
            :aria-invalid="shownError('name') ? 'true' : undefined"
            :aria-describedby="describedBy('name')"
            @blur="touched.name = true"
          />
          <p v-if="shownError('name')" id="name-error" class="mt-1.5 text-sm text-airmail-red">
            {{ shownError('name') }}
          </p>
        </div>

        <div>
          <label for="password" class="block text-sm font-semibold">Password</label>
          <div class="relative mt-1.5">
            <Input
              id="password"
              v-model="password"
              class="pr-11"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="new-password"
              required
              :aria-invalid="shownError('password') ? 'true' : undefined"
              :aria-describedby="describedBy('password', 'password-help')"
              @blur="touched.password = true"
            />
            <button
              type="button"
              class="absolute right-1 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-ink-soft transition-colors hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-airmail-blue"
              aria-label="Show password"
              :aria-pressed="showPassword"
              @click="showPassword = !showPassword"
            >
              <EyeOff v-if="showPassword" :size="18" aria-hidden="true" />
              <Eye v-else :size="18" aria-hidden="true" />
            </button>
          </div>
          <p v-if="shownError('password')" id="password-error" class="mt-1.5 text-sm text-airmail-red">
            {{ shownError('password') }}
          </p>
          <p id="password-help" class="mt-1.5 text-sm text-ink-soft">
            You'll need this to open the inbox from another browser. It can't be recovered.
          </p>
        </div>

        <div>
          <label for="confirm" class="block text-sm font-semibold">Confirm password</label>
          <Input
            id="confirm"
            v-model="confirm"
            class="mt-1.5"
            type="password"
            autocomplete="new-password"
            required
            :aria-invalid="shownError('confirm') ? 'true' : undefined"
            :aria-describedby="describedBy('confirm')"
            @blur="touched.confirm = true"
          />
          <p v-if="shownError('confirm')" id="confirm-error" class="mt-1.5 text-sm text-airmail-red">
            {{ shownError('confirm') }}
          </p>
        </div>

        <div
          v-if="serverError"
          role="alert"
          class="rounded-md border border-airmail-red px-4 py-3 text-sm text-airmail-red"
        >
          {{ serverError }}
        </div>

        <Button type="submit" class="w-full sm:w-auto" :disabled="submitting" :aria-busy="submitting">
          <Loader2 v-if="submitting" class="animate-spin" :size="16" aria-hidden="true" />
          Create inbox
        </Button>
      </form>
    </div>
  </div>
</template>
