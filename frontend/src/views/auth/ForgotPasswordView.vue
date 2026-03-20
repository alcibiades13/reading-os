<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()

const email = ref('')
const error = ref('')
const success = ref(false)
const loading = ref(false)

const handleSubmit = async () => {
  error.value = ''

  if (!email.value) {
    error.value = 'Please enter your email address'
    return
  }

  loading.value = true

  try {
    await api.post('/users/forgot-password/', { email: email.value })
    success.value = true
  } catch (err) {
    // Always show success to prevent email enumeration
    success.value = true
  } finally {
    loading.value = false
  }
}

const goToLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
    <Card class="w-full max-w-md shadow-xl">
      <CardHeader class="space-y-1">
        <CardTitle class="text-3xl font-bold text-center">Reading OS</CardTitle>
        <CardDescription class="text-center">
          Reset your password
        </CardDescription>
      </CardHeader>

      <CardContent class="space-y-4">
        <template v-if="success">
          <div class="p-3 bg-green-500/10 text-green-700 text-sm rounded-md">
            If an account exists with that email, we've sent a reset link.
          </div>
        </template>

        <template v-else>
          <div v-if="error" class="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
            {{ error }}
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="space-y-2">
              <Label for="email">Email</Label>
              <Input
                id="email"
                v-model="email"
                type="email"
                placeholder="your@email.com"
                required
                :disabled="loading"
              />
            </div>

            <Button
              type="submit"
              class="w-full"
              :disabled="loading"
            >
              <span v-if="loading">Sending...</span>
              <span v-else>Send Reset Link</span>
            </Button>
          </form>
        </template>
      </CardContent>

      <CardFooter class="flex flex-col space-y-4">
        <div class="text-sm text-center text-muted-foreground">
          Remember your password?
          <button
            @click="goToLogin"
            class="text-primary hover:underline font-medium ml-1"
            type="button"
          >
            Sign in
          </button>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>
