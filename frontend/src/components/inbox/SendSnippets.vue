<script setup lang="ts">
import { computed } from 'vue'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import CodeBlock from '@/components/inbox/CodeBlock.vue'
import { sendSnippets } from '@/lib/snippets'

const props = defineProps<{ url: string }>()

const snippets = computed(() => sendSnippets(props.url))
</script>

<template>
  <Tabs default-value="curl">
    <TabsList class="flex h-auto w-full flex-wrap justify-start gap-1 bg-transparent p-0">
      <TabsTrigger
        v-for="s in snippets"
        :key="s.id"
        :value="s.id"
        class="rounded-md border border-transparent px-3 py-1.5 text-[13px] text-ink-soft data-[state=active]:border-rule data-[state=active]:bg-paper data-[state=active]:text-ink data-[state=active]:shadow-none"
      >
        {{ s.label }}
      </TabsTrigger>
    </TabsList>
    <TabsContent v-for="s in snippets" :key="s.id" :value="s.id" class="mt-3">
      <CodeBlock :text="s.code" kind="text" />
    </TabsContent>
  </Tabs>
</template>
