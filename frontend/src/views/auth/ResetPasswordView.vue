<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()
const route = useRoute()

const password = ref('')
const passwordConfirm = ref('')
const error = ref('')
const fieldErrors = ref({})
const loading = ref(false)

const handleSubmit = async () => {
  error.value = ''
  fieldErrors.value = {}

  if (!password.value || !passwordConfirm.value) {
    error.value = 'Please fill in all fields'
    return
  }

  if (password.value !== passwordConfirm.value) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true

  try {
    await api.post('/users/reset-password/', {
      token: route.params.token,
      password: password.value,
      password_confirm: passwordConfirm.value,
    })
    router.push({ path: '/login', query: { reset: 'success' } })
  } catch (err) {
    const data = err.response?.data
    if (data) {
      if (typeof data === 'string') {
        error.value = data
      } else if (data.detail) {
        error.value = data.detail
      } else if (data.non_field_errors) {
        error.value = Array.isArray(data.non_field_errors)
          ? data.non_field_errors.join(' ')
          : data.non_field_errors
      } else {
        // Field-level errors
        fieldErrors.value = data
        const firstKey = Object.keys(data)[0]
        if (firstKey) {
          const val = data[firstKey]
          error.value = Array.isArray(val) ? val.join(' ') : val
        }
      }
    } else {
      error.value = 'Something went wrong. Please try again.'
    }
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
          Set your new password
        </CardDescription>
      </CardHeader>

      <CardContent class="space-y-4">
        <div v-if="error" class="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
          {{ error }}
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="space-y-2">
            <Label for="password">New Password</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              placeholder="••••••••"
              required
              :disabled="loading"
            />
          </div>

          <div class="space-y-2">
            <Label for="password-confirm">Confirm Password</Label>
            <Input
              id="password-confirm"
              v-model="passwordConfirm"
              type="password"
              placeholder="••••••••"
              required
              :disabled="loading"
            />
          </div>

          <Button
            type="submit"
            class="w-full"
            :disabled="loading"
          >
            <span v-if="loading">Resetting...</span>
            <span v-else>Reset Password</span>
          </Button>
        </form>
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
