<script setup lang="ts">
import { ref } from 'vue'
import { Check, Copy } from 'lucide-vue-next'
import { useClipboard } from '@vueuse/core'
import { Button } from '@/components/ui/button'

defineProps<{
  rows: { key: string; value: string }[]
  emptyLabel: string
}>()

const { copy } = useClipboard()
const copiedIndex = ref<number | null>(null)

async function copyRow(index: number, value: string): Promise<void> {
  await copy(value)
  copiedIndex.value = index
  setTimeout(() => {
    if (copiedIndex.value === index) copiedIndex.value = null
  }, 1500)
}
</script>

<template>
  <p v-if="!rows.length" class="py-6 text-[15px] text-ink-soft">{{ emptyLabel }}</p>
  <div v-else class="overflow-x-auto rounded-lg border border-rule">
    <table class="w-full border-collapse text-left text-[13px]">
      <caption class="sr-only">Captured entries</caption>
      <tbody class="divide-y divide-rule">
        <tr v-for="(row, i) in rows" :key="i" class="align-top">
          <th scope="row" class="w-[35%] break-all px-3 py-2 font-mono font-normal text-ink-soft">{{ row.key }}</th>
          <td class="break-all px-3 py-2 font-mono text-ink">{{ row.value }}</td>
          <td class="w-12 px-1 py-1.5 text-right">
            <Button
              variant="ghost"
              size="icon"
              class="h-8 w-8"
              :aria-label="`Copy value of ${row.key}`"
              @click="copyRow(i, row.value)"
            >
              <Check v-if="copiedIndex === i" class="size-4" aria-hidden="true" />
              <Copy v-else class="size-4" aria-hidden="true" />
            </Button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
