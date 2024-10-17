<template>
  <div>
    <h1>New Resource</h1>
    
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
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const id = route.params.id

const password = ref('')
const errorMessage = ref('')

const submitForm = async () => {
  try {
    const response = await axios.post(`/api/resources/create`, { password: password.value })
    if (response.data.access_token) {
      document.cookie = `access_token=${response.data.access_token}; SameSite=Strict; Path=/; Max-Age=31536000`
    }
    if (response.data.uuid) {
      router.push(`/inspector/${response.data.uuid}`)
    }
  } catch (error) {
    errorMessage.value = error.message
  }
}
</script>

