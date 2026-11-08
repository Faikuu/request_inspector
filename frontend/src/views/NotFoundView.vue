<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { buttonVariants } from '@/components/ui/button'
</script>

<template>
  <div class="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 sm:py-24">
    <div class="max-w-md">
      <h1 class="text-3xl font-extrabold tracking-tight sm:text-[36px]">This page doesn't exist.</h1>
      <p class="mt-4 text-[15px] leading-relaxed text-ink-soft">
        The link may be out of date, or the address may have a typo.
      </p>
      <div class="mt-8">
        <RouterLink to="/" :class="buttonVariants({ variant: 'outline' })">Go to the home page</RouterLink>
      </div>
    </div>
  </div>
</template>
