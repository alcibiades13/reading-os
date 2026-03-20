<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const success = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    await api.post('/users/verify-email/', { token: route.params.token })
    success.value = true
  } catch (err) {
    const data = err.response?.data
    if (data?.detail) {
      error.value = data.detail
    } else {
      error.value = 'Invalid or expired verification link.'
    }
  } finally {
    loading.value = false
  }
})

const goToLogin = () => {
  router.push('/login')
}

const goToLibrary = () => {
  router.push('/library')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
    <Card class="w-full max-w-md shadow-xl">
      <CardHeader class="space-y-1">
        <CardTitle class="text-3xl font-bold text-center">Reading OS</CardTitle>
        <CardDescription class="text-center">
          Email Verification
        </CardDescription>
      </CardHeader>

      <CardContent class="space-y-4">
        <div v-if="loading" class="text-center py-8">
          <p class="text-muted-foreground">Verifying your email...</p>
        </div>

        <div v-else-if="success" class="space-y-4">
          <div class="p-3 bg-green-500/10 text-green-700 text-sm rounded-md">
            Your email has been verified successfully.
          </div>
          <div class="flex gap-3">
            <Button @click="goToLogin" variant="outline" class="flex-1">
              Sign In
            </Button>
            <Button @click="goToLibrary" class="flex-1">
              Go to Library
            </Button>
          </div>
        </div>

        <div v-else class="space-y-4">
          <div class="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            {{ error }}
          </div>
          <Button @click="goToLogin" class="w-full">
            Go to Sign In
          </Button>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
