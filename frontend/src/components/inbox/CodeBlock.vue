<script setup lang="ts">
import { computed, ref } from 'vue'
import { Check, Copy, WrapText } from 'lucide-vue-next'
import { useClipboard } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import { type BodyKind, type JsonTokenType, tokenizeJson } from '@/lib/highlight'

const props = withDefaults(
  defineProps<{
    text: string
    kind?: BodyKind
  }>(),
  { kind: 'text' },
)

// The block always renders with the dark palette (the `dark` class below), so token colours
// stay readable on the navy code background in both themes.
const TOKEN_CLASS: Record<JsonTokenType, string> = {
  key: 'text-method-get',
  string: 'text-method-post',
  number: 'text-method-put',
  boolean: 'text-method-patch',
  null: 'text-method-patch',
  punct: 'text-code-ink/60',
  ws: '',
}

/** Very large payloads are shown as plain text to keep rendering cheap. */
const MAX_HIGHLIGHT_CHARS = 200_000

const wrap = ref(false)
const { copy, copied } = useClipboard({ copiedDuring: 1500 })

const tokens = computed(() =>
  props.kind === 'json' && props.text.length <= MAX_HIGHLIGHT_CHARS ? tokenizeJson(props.text) : null,
)
</script>

<template>
  <div class="dark overflow-hidden rounded-lg bg-code text-code-ink">
    <div class="flex items-center justify-end gap-1 border-b border-code-ink/10 px-2 py-1">
      <Button
        variant="ghost"
        size="sm"
        class="h-8 text-code-ink hover:bg-code-ink/10"
        :aria-pressed="wrap"
        @click="wrap = !wrap"
      >
        <WrapText class="size-4" aria-hidden="true" />
        Wrap lines
      </Button>
      <Button variant="ghost" size="sm" class="h-8 text-code-ink hover:bg-code-ink/10" @click="copy(text)">
        <Check v-if="copied" class="size-4" aria-hidden="true" />
        <Copy v-else class="size-4" aria-hidden="true" />
        {{ copied ? 'Copied' : 'Copy' }}
      </Button>
    </div>
    <pre
      tabindex="0"
      class="max-h-[60vh] overflow-auto p-4 font-mono text-[13px] leading-relaxed"
      :class="wrap ? 'whitespace-pre-wrap break-words' : 'whitespace-pre'"
    ><code v-if="tokens" class="font-mono"><span v-for="(tok, i) in tokens" :key="i" :class="TOKEN_CLASS[tok.t]">{{ tok.v }}</span></code><code v-else class="font-mono">{{ text }}</code></pre>
  </div>
</template>
