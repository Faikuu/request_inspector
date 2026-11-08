<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from '@/components/AppHeader.vue'
import Toaster from '@/components/ui/toast/Toaster.vue'
</script>

<template>
  <div class="flex min-h-dvh flex-col bg-paper text-ink">
    <AppHeader />
    <main class="flex min-w-0 flex-1 flex-col">
      <RouterView />
    </main>
    <Toaster />
  </div>
</template>
