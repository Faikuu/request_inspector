<script setup lang="ts">
import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogOverlay,
  AlertDialogPortal,
  AlertDialogRoot,
  AlertDialogTitle,
} from 'radix-vue'
import { buttonVariants } from '@/components/ui/button'

defineProps<{
  open: boolean
  title: string
  description: string
  confirmLabel: string
  destructive?: boolean
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  confirm: []
}>()
</script>

<template>
  <AlertDialogRoot :open="open" @update:open="emit('update:open', $event)">
    <AlertDialogPortal>
      <AlertDialogOverlay class="fixed inset-0 z-50 bg-ink/40" />
      <AlertDialogContent
        class="fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border border-rule bg-sheet p-6 text-ink shadow-sm focus:outline-none"
      >
        <AlertDialogTitle class="text-[18px] font-bold tracking-tight">{{ title }}</AlertDialogTitle>
        <AlertDialogDescription class="mt-2 text-[15px] text-ink-soft">{{ description }}</AlertDialogDescription>
        <div class="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <AlertDialogCancel :class="buttonVariants({ variant: 'outline' })">Cancel</AlertDialogCancel>
          <AlertDialogAction
            :class="buttonVariants({ variant: destructive ? 'destructive' : 'default' })"
            @click="emit('confirm')"
          >
            {{ confirmLabel }}
          </AlertDialogAction>
        </div>
      </AlertDialogContent>
    </AlertDialogPortal>
  </AlertDialogRoot>
</template>
