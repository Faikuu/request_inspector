<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Toaster from '@/components/ui/toast/Toaster.vue'
</script>

<template>
  <div class="px-4 bg-indigo-200">
    <header class="flex justify-center gap-4 transition-all duration-500 ease-in-out sm:w-[80%] md:w-[320px] md:hover:w-full my-0 mx-auto text-slate-700">
      <div class="max-w-[80%] w-full flex justify-start items-center h-16 my-4 px-8 py-1 bg-indigo-100 drop-shadow-sm rounded-full overflow-x-hidden">
        <a class="flex items-center cursor-pointer" href="/">
          <img class="h-10 w-10" src="@/assets/logo.svg" alt="Vite logo" />
          <h1 class="hidden md:block text-3xl font-bold">Inspector</h1>
        </a>
        <div class="flex items-center gap-2 ml-20">
          <div class="w-1 h-full bg-red-500 rounded-lg"></div>
          <a href="/inspector/new/">
            <span>New</span>
          </a>
          <a href="/inspector/">
            <span>Existing</span>
          </a>
        </div>
      </div>
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
