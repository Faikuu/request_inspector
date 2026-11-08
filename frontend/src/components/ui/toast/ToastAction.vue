<script setup lang="ts">
import { type HTMLAttributes, computed } from 'vue'
import { ToastAction, type ToastActionProps } from 'radix-vue'
import { cn } from '@/lib/utils'

const props = defineProps<ToastActionProps & { class?: HTMLAttributes['class'] }>()

const delegatedProps = computed(() => {
  const { class: _, ...delegated } = props

  return delegated
})
</script>

<template>
  <ToastAction v-bind="delegatedProps" :class="cn('inline-flex h-8 shrink-0 items-center justify-center rounded-md border border-rule bg-transparent px-3 text-sm font-medium text-ink transition-colors hover:bg-paper focus:outline-none focus:ring-2 focus:ring-airmail-blue focus:ring-offset-2 focus:ring-offset-sheet disabled:pointer-events-none disabled:opacity-50 group-[.destructive]:border-airmail-red group-[.destructive]:text-airmail-red group-[.destructive]:hover:bg-airmail-red group-[.destructive]:hover:text-paper', props.class)">
    <slot />
  </ToastAction>
</template>
