<template>
  <div class="flex flex-col items-center p-6 bg-white rounded-lg shadow-md">
    <h1 class="text-2xl font-semibold text-gray-800 mb-4">Search Inspector</h1>
    
    <form @submit.prevent="submitForm" class="space-y-4">
      <div class="flex flex-col">
        <label for="inspector-id" class="text-sm font-medium text-gray-700">Inspector ID:</label>
        <Input
          type="text"
          v-model="inspectorId"
          required
          class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <Button type="submit" class="w-full px-4 py-2 bg-indigo-600 border border-transparent rounded-md shadow-sm text-white font-bold hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">Search</Button>
    </form>

    <p v-if="errorMessage" class="mt-4 text-sm text-red-500">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const inspectorId = ref('')
const errorMessage = ref('')

const submitForm = async () => {
  try {
    router.push(`/inspector/${inspectorId.value}`)

  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>

