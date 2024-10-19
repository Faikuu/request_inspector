<template>
  <div v-if="!resource">
    <h1>Resource {{ uuid }}</h1>
    
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
  <div v-else>
    <div>
      <h1>Resource {{ uuid }}</h1>

      <div>
        <div v-for="child in resourceContent" :key="child.id">
          {{ child.name }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import axios from 'axios'
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const uuid = route.params.uuid

const password = ref('')
const errorMessage = ref('')
const resource = ref('')
// const resourceContent = ref('')
const resourceContent = ref([{ id: 1, name: 'Foo' }, { id: 2, name: 'Bar' }])

const submitForm = async () => {
  try {
    const response = await axios.post(`/api/resources/token`, {
      resource_uuid: uuid,
      password: password.value
    })

    if (response.data.access_token) {
      document.cookie = `access_token=${response.data.access_token}; SameSite=Strict; Path=/; Max-Age=31536000`
      
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`
    }

    const data = await response.data
    if (response.data.uuid) {
      router.go(0)
    }
    console.log('Response data:', data)
  } catch (error) {
    errorMessage.value = error.message
  }
}

onMounted(async () => {
  const token = document.cookie.match(/access_token=([^;]+)/)?.[1]
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await axios.get(`/api/resources/${uuid}`)
    const data = await response.data
    if (!data.content) {
      return
    }
    resource.value = data.content

    const token = document.cookie.match(/access_token=([^;]+)/)?.[1]
    var socket = new WebSocket(`ws://localhost:5173/api/ws/?access_token=${token}`)
    socket.onopen = () => {
      console.log('WebSocket connection established')
    }
    socket.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    socket.onmessage = (event) => {
      console.log('WebSocket message received:', event.data)
    }
    socket.onclose = () => {
      console.log('WebSocket connection closed')
    }
  } catch (error) {
    console.error('Failed to fetch resource:', error)
  }
})
</script>
