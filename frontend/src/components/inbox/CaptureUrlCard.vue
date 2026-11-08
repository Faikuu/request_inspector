<script setup lang="ts">
import { ref } from 'vue'
import { Check, Copy } from 'lucide-vue-next'
import { useClipboard } from '@vueuse/core'
import { Button } from '@/components/ui/button'
import SendSnippets from '@/components/inbox/SendSnippets.vue'

defineProps<{ url: string }>()

const { copy, copied } = useClipboard({ copiedDuring: 1500 })
const showSnippets = ref(false)
const snippetsId = 'capture-url-snippets'
</script>

<template>
  <section class="relative overflow-hidden rounded-lg border border-rule bg-sheet" aria-labelledby="capture-url-label">
    <!-- The airmail edge: the one bold element on the page. -->
    <div class="absolute inset-y-0 left-0 w-1.5 bg-airmail" aria-hidden="true" />
    <div class="p-4 pl-6 sm:p-5 sm:pl-7">
      <p id="capture-url-label" class="text-[13px] font-medium text-ink-soft">Capture URL</p>
      <p class="mt-1.5 break-all font-mono text-[15px] text-ink">{{ url }}</p>
      <p class="mt-2 text-[13px] text-ink-soft">
        Any method and path works — append /anything to the URL to tag requests.
      </p>
      <div class="mt-4 flex flex-wrap gap-2">
        <Button size="sm" @click="copy(url)">
          <Check v-if="copied" class="size-4" aria-hidden="true" />
          <Copy v-else class="size-4" aria-hidden="true" />
          {{ copied ? 'Copied' : 'Copy URL' }}
        </Button>
        <Button
          variant="outline"
          size="sm"
          :aria-expanded="showSnippets"
          :aria-controls="snippetsId"
          @click="showSnippets = !showSnippets"
        >
          {{ showSnippets ? 'Hide snippets' : 'Show snippets' }}
        </Button>
      </div>
      <div v-if="showSnippets" :id="snippetsId" class="mt-4">
        <SendSnippets :url="url" />
      </div>
    </div>
  </section>
</template>
