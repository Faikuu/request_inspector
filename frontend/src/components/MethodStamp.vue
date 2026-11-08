<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    method: string
    size?: 'sm' | 'md'
  }>(),
  { size: 'md' },
)

const TONE: Record<string, string> = {
  GET: 'text-method-get border-method-get',
  POST: 'text-method-post border-method-post',
  PUT: 'text-method-put border-method-put',
  PATCH: 'text-method-patch border-method-patch',
  DELETE: 'text-method-delete border-method-delete',
}

const label = computed(() => props.method.toUpperCase())
const tone = computed(() => TONE[label.value] ?? 'text-method-other border-method-other')
const sizeClass = computed(() =>
  props.size === 'sm' ? 'min-w-[3.75rem] px-1.5 py-1 text-[11px]' : 'min-w-[4.5rem] px-2 py-1.5 text-xs',
)
</script>

<template>
  <span
    :class="[
      'inline-flex shrink-0 items-center justify-center rounded-sm border-2 font-sans font-bold uppercase leading-none tracking-wide',
      sizeClass,
      tone,
    ]"
  >{{ label }}</span>
</template>
