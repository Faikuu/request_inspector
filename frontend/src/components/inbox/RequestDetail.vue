<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, Check, Copy, Trash2 } from 'lucide-vue-next'
import { useClipboard } from '@vueuse/core'
import type { CapturedRequest } from '@/api/types'
import MethodStamp from '@/components/MethodStamp.vue'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import CodeBlock from '@/components/inbox/CodeBlock.vue'
import KeyValueTable from '@/components/inbox/KeyValueTable.vue'
import { clockTime, formatBytes, fullDate } from '@/lib/format'
import { prettyBody } from '@/lib/highlight'
import { pathWithQuery, toCurl } from '@/lib/snippets'

const props = defineProps<{
  request: CapturedRequest | null
  captureUrl: string
}>()

const emit = defineEmits<{
  delete: []
  back: []
}>()

const tab = ref('body')
const { copy: copyCurl, copied: curlCopied } = useClipboard({ copiedDuring: 1500 })
const { copy: copyBody, copied: bodyCopied } = useClipboard({ copiedDuring: 1500 })

const pretty = computed(() =>
  props.request ? prettyBody(props.request) : { kind: 'empty' as const, text: '' },
)

const headerRows = computed(() =>
  Object.entries(props.request?.headers ?? {}).map(([key, value]) => ({ key, value })),
)

const queryRows = computed(() => {
  const rows: { key: string; value: string }[] = []
  for (const [key, values] of Object.entries(props.request?.query ?? {})) {
    for (const value of values) rows.push({ key, value })
  }
  return rows
})

/** The body exactly as received (base64 for binary payloads). */
const rawBody = computed(() => props.request?.body ?? props.request?.body_base64 ?? '')

const rawMessage = computed(() => {
  const r = props.request
  if (!r) return ''
  const head = [`${r.method} ${pathWithQuery(r)} HTTP/1.1`]
  for (const [name, value] of Object.entries(r.headers)) head.push(`${name}: ${value}`)
  const body = r.body ?? (r.body_base64 ? `[binary body, base64] ${r.body_base64}` : '')
  return `${head.join('\n')}\n\n${body}`
})
</script>

<template>
  <section v-if="request" class="min-w-0" aria-label="Request details">
    <div class="mb-3 lg:hidden">
      <Button variant="ghost" size="sm" @click="emit('back')">
        <ArrowLeft class="size-4" aria-hidden="true" />
        Back to requests
      </Button>
    </div>

    <div class="flex min-w-0 items-start gap-3">
      <MethodStamp :method="request.method" size="md" class="mt-0.5 shrink-0" />
      <h2 class="min-w-0 break-all font-mono text-[15px] font-medium text-ink">{{ pathWithQuery(request) }}</h2>
    </div>

    <dl class="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-[13px]">
      <div class="flex gap-1.5">
        <dt class="text-ink-soft">Size</dt>
        <dd class="text-ink">{{ formatBytes(request.size) }}</dd>
      </div>
      <div class="flex min-w-0 gap-1.5">
        <dt class="text-ink-soft">Content type</dt>
        <dd class="min-w-0 break-all font-mono text-ink">{{ request.content_type ?? 'Not set' }}</dd>
      </div>
      <div class="flex gap-1.5">
        <dt class="text-ink-soft">Remote address</dt>
        <dd class="font-mono text-ink">{{ request.remote_addr ?? 'Unknown' }}</dd>
      </div>
      <div class="flex gap-1.5">
        <dt class="text-ink-soft">Received</dt>
        <dd class="text-ink">
          <time :datetime="request.created_at" :title="fullDate(request.created_at)">{{
            clockTime(request.created_at)
          }}</time>
        </dd>
      </div>
    </dl>

    <div class="mt-4 flex flex-wrap items-center gap-2">
      <Button variant="outline" size="sm" @click="copyCurl(toCurl(request, captureUrl))">
        <Check v-if="curlCopied" class="size-4" aria-hidden="true" />
        <Copy v-else class="size-4" aria-hidden="true" />
        {{ curlCopied ? 'Copied' : 'Copy as cURL' }}
      </Button>
      <Button variant="outline" size="sm" :disabled="!rawBody" @click="copyBody(rawBody)">
        <Check v-if="bodyCopied" class="size-4" aria-hidden="true" />
        <Copy v-else class="size-4" aria-hidden="true" />
        {{ bodyCopied ? 'Copied' : 'Copy body' }}
      </Button>
      <Button variant="ghost" size="sm" class="text-airmail-red hover:text-airmail-red" @click="emit('delete')">
        <Trash2 class="size-4" aria-hidden="true" />
        Delete request
      </Button>
    </div>

    <Tabs v-model="tab" class="mt-5">
      <TabsList class="flex h-auto w-full justify-start gap-1 overflow-x-auto bg-transparent p-0">
        <TabsTrigger
          value="body"
          class="rounded-md border border-transparent px-3 py-1.5 text-ink-soft data-[state=active]:border-rule data-[state=active]:bg-sheet data-[state=active]:text-ink data-[state=active]:shadow-none"
        >
          Body
        </TabsTrigger>
        <TabsTrigger
          value="headers"
          class="rounded-md border border-transparent px-3 py-1.5 text-ink-soft data-[state=active]:border-rule data-[state=active]:bg-sheet data-[state=active]:text-ink data-[state=active]:shadow-none"
        >
          Headers ({{ headerRows.length }})
        </TabsTrigger>
        <TabsTrigger
          value="query"
          class="rounded-md border border-transparent px-3 py-1.5 text-ink-soft data-[state=active]:border-rule data-[state=active]:bg-sheet data-[state=active]:text-ink data-[state=active]:shadow-none"
        >
          Query ({{ queryRows.length }})
        </TabsTrigger>
        <TabsTrigger
          value="raw"
          class="rounded-md border border-transparent px-3 py-1.5 text-ink-soft data-[state=active]:border-rule data-[state=active]:bg-sheet data-[state=active]:text-ink data-[state=active]:shadow-none"
        >
          Raw
        </TabsTrigger>
      </TabsList>

      <TabsContent value="body" class="mt-3">
        <CodeBlock v-if="pretty.kind !== 'empty'" :text="pretty.text" :kind="pretty.kind" />
        <p v-else class="py-6 text-[15px] text-ink-soft">This request has no body.</p>
      </TabsContent>
      <TabsContent value="headers" class="mt-3">
        <KeyValueTable :rows="headerRows" empty-label="No headers were captured." />
      </TabsContent>
      <TabsContent value="query" class="mt-3">
        <KeyValueTable :rows="queryRows" empty-label="No query parameters." />
      </TabsContent>
      <TabsContent value="raw" class="mt-3">
        <CodeBlock :text="rawMessage" kind="text" />
      </TabsContent>
    </Tabs>
  </section>

  <div
    v-else
    class="flex min-h-[240px] items-center justify-center rounded-lg border border-dashed border-rule p-6 text-center text-[15px] text-ink-soft"
  >
    Select a request to see its details.
  </div>
</template>
