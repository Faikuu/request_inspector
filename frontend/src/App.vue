<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Toaster from '@/components/ui/toast/Toaster.vue'
</script>

<template>
  <div class="px-4 bg-indigo-200">
    <header>
      <div class="w-full h-16 mt-4 bg-white rounded-full">

      </div>
      <!-- <font-awesome-icon :icon="['fas', 'chevron-up']" /> -->
    </header>
    
    <div class="flex min-h-screen justify-center py-2 items-center fade-in">
      <div class="min-w-[320px] max-w-[80%] p-4 bg-gradient-to-b from-slate-500 to-indigo-300 shadow-md rounded-lg">
        <RouterView />
      </div>
    </div>
    
    <Toaster />
    <footer>

    </footer>
  </div>
</template>

<style scoped>
.fade-in {
  opacity: 0;
  animation: fadeIn 0.5s ease-in-out forwards;
}

@keyframes fadeIn {
  to {
    opacity: 1;
  }
}

header {
  line-height: 1.5;
  max-height: 100vh;
}

.logo {
  display: block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  text-align: center;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  .logo {
    margin: 0 2rem 0 0;
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }

  nav {
    text-align: left;
    margin-left: -1rem;
    font-size: 1rem;

    padding: 1rem 0;
    margin-top: 1rem;
  }
}
</style>
