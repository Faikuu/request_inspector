<template>
  <div v-if="!resource" class="flex flex-col items-center p-6 bg-white rounded-lg shadow-md">
    <h1 class="text-2xl font-semibold text-gray-800 mb-4">Resource {{ uuid }}</h1>
    
    <form @submit.prevent="submitForm" class="w-full max-w-sm space-y-4">
      <div>
        <label for="password" class="block text-sm font-medium text-gray-700">Password:</label>
        <Input
          type="password"
          v-model="password"
          required
          class="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>
      <Button type="submit" class="w-full py-2 px-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-md">Submit</Button>
    </form>

    <p v-if="errorMessage" class="mt-4 text-sm text-red-500">{{ errorMessage }}</p>
  </div>
  <div v-else>
    <div class="flex flex-col justify-center items-center mb-4 text-3xl font-bold bg-gradient-to-r from-white to-indigo-300 text-transparent bg-clip-text drop-shadow-md">
      <span>
        To send request, use
      </span>
      <div class="bg-gray-700 rounded-lg mt-4 p-4 flex items-center w-full">
        <span class="text-white text-lg break-all">
          curl -X POST http://localhost:5173/api/resources/log \
-H "Authorization: Bearer {{ access_token }}" \
-H "Content-Type: application/json" \
-d '{"content":"Your message"}'
        </span>
      </div>
    </div>
    <div>
      <h1 class="flex flex-col justify-center items-center mb-4 text-3xl font-bold bg-gradient-to-r from-white to-indigo-300 text-transparent bg-clip-text drop-shadow-md">
        <span>
          Inspector 
        </span>
        <span>
          {{ uuid }}
        </span>
      </h1>

      <Tabs defaultValue="realtime" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="realtime">Realtime</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        <TabsContent value="realtime">
          <div class="flex flex-col-reverse">
            <div v-if="realTimeContent.length > 0" class="bg-gray-700 rounded-lg mt-4 p-4" v-for="child in realTimeContent" :key="child.id">
              {{ child.content }}
            </div>
            <div v-else class="bg-gray-700 rounded-lg mt-4 p-4 flex items-center">
              <svg class="mr-2 animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Waiting for requests...
            </div>
          </div>
        </TabsContent>
        <TabsContent value="history">
          <div class="flex flex-col-reverse">
            <div v-if="historyContent.length > 0" class="bg-gray-700 rounded-lg mt-4 p-4" v-for="child in historyContent" :key="child.id">
              {{ child.content }}
            </div>
            <div v-else class="bg-gray-700 rounded-lg mt-4 p-4 flex items-center">
              <svg class="mr-2 animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Waiting for history...
            </div>
          </div>
        </TabsContent>
        <TabsContent value="settings">
          <div class="bg-gray-700 rounded-lg mt-6 p-4 flex items-center">
            <svg class="mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <path class="opacity-75" fill="currentColor" d="M14 2H6c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 3h-2v2h2V5zm0 4h-2v2h2v-2zm0 4h-2v2h2v-2zM4 12h2v2H4v-2zm0 4h2v2H4v-2zM4 18h2v2H4v-2zM16 20h2v2h-2v-2zM16 6h2v2h-2V6zm0 10h2v2h-2v-2zM16 2h2v2h-2V2z"></path>
            </svg>
            Settings placeholder
          </div>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>

<script setup>
import Button from '@/components/ui/button/Button.vue';
import Input from '@/components/ui/input/Input.vue';
import axios from 'axios'
import { Tabs, TabsContent, TabsTrigger } from '@/components/ui/tabs'
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import TabsList from '@/components/ui/tabs/TabsList.vue';

const route = useRoute()
const router = useRouter()
const uuid = route.params.uuid

const password = ref('')
const errorMessage = ref('')
const resource = ref('')
const realTimeContent = ref([])
const historyContent = ref([])

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

    const historyResponse = await axios.get(`/api/resources/history/${uuid}`)
    const historyData = await historyResponse.data
    if (!historyData) {
      return
    }
    historyContent.value = historyData
    // console.log(historyContent.value);

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
      realTimeContent.value = [...realTimeContent.value, { id: realTimeContent.value.length + 1, content: event.data }]
    }
    socket.onclose = () => {
      console.log('WebSocket connection closed')
    }
  } catch (error) {
    console.error('Failed to fetch resource:', error)
  }
})
</script>
