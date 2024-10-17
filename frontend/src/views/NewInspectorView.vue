<template>
  <div>
    <h1>New Resource {{ id }}</h1>
    
    <form @submit.prevent="submitForm">
      <label for="password">Password:</label>
      <Input
        type="password"
        v-model="password"
        required
      />
      <Button type="submit">Submit</Button>
    </form>

    <p v-if="errorMessage">{{ errorMessage }}</p>
  </div>
</template>

<script setup>
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const id = route.params.id

// Define reactive state variables
const password = ref('')
const errorMessage = ref('')

// Form submission logic
const submitForm = async () => {
  try {
    // const response = await fetch(`/api/resources/${id}`, {
    const response = await fetch(`/api/resources/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ "resource_id": id, "password": password.value })
    })

    if (!response.ok) {
      throw new Error('Failed to submit. Please try again.')
    }

    const data = await response.json()
    // Handle the response (e.g., show a success message or navigate elsewhere)
    console.log('Response data:', data)
  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>
