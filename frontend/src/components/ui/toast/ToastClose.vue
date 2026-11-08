<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { ToastClose, type ToastCloseProps } from 'radix-vue'
import { X } from 'lucide-vue-next'
import { cn } from '@/lib/utils'

const props = defineProps<ToastCloseProps & {
  class?: HTMLAttributes['class']
}>()

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props

  return delegated
})
</script>

<template>
  <ToastClose v-bind="delegatedProps" :class="cn('absolute right-2 top-2 rounded-md p-1 text-ink-soft opacity-0 transition-opacity hover:text-ink focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-airmail-blue group-hover:opacity-100 group-[.destructive]:text-airmail-red group-[.destructive]:hover:text-airmail-red', props.class)">
    <X class="h-4 w-4" />
  </ToastClose>
</template>
