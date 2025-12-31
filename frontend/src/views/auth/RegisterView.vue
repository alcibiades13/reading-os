<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

const router = useRouter()
const authStore = useAuthStore()

const formData = ref({
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  password_confirm: '',
})

const errors = ref({})
const loading = ref(false)

const validateForm = () => {
  errors.value = {}

  if (!formData.value.email) {
    errors.value.email = 'Email is required'
  } else if (!/\S+@\S+\.\S+/.test(formData.value.email)) {
    errors.value.email = 'Email is invalid'
  }

  if (!formData.value.first_name) {
    errors.value.first_name = 'First name is required'
  }

  if (!formData.value.last_name) {
    errors.value.last_name = 'Last name is required'
  }

  if (!formData.value.password) {
    errors.value.password = 'Password is required'
  } else if (formData.value.password.length < 8) {
    errors.value.password = 'Password must be at least 8 characters'
  }

  if (formData.value.password !== formData.value.password_confirm) {
    errors.value.password_confirm = 'Passwords do not match'
  }

  return Object.keys(errors.value).length === 0
}

const handleRegister = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true

  const result = await authStore.register(formData.value)

  loading.value = false

  if (result.success) {
    // Redirect to home
    router.push('/home')
  } else {
    // Display errors from backend
    if (typeof result.error === 'object') {
      errors.value = result.error
    } else {
      errors.value.general = result.error || 'Registration failed'
    }
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
        <CardTitle class="text-3xl font-bold text-center">Create Account</CardTitle>
        <CardDescription class="text-center">
          Start your reading journey today
        </CardDescription>
      </CardHeader>
      
      <CardContent class="space-y-4">
        <!-- General error message -->
        <div v-if="errors.general" class="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
          {{ errors.general }}
        </div>

        <!-- Register form -->
        <form @submit.prevent="handleRegister" class="space-y-4">
          <!-- Email -->
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="formData.email"
              type="email"
              placeholder="your@email.com"
              :disabled="loading"
              :class="{ 'border-destructive': errors.email }"
            />
            <p v-if="errors.email" class="text-sm text-destructive">{{ errors.email }}</p>
          </div>

          <!-- First Name -->
          <div class="space-y-2">
            <Label for="first_name">First Name</Label>
            <Input
              id="first_name"
              v-model="formData.first_name"
              type="text"
              placeholder="John"
              :disabled="loading"
              :class="{ 'border-destructive': errors.first_name }"
            />
            <p v-if="errors.first_name" class="text-sm text-destructive">{{ errors.first_name }}</p>
          </div>

          <!-- Last Name -->
          <div class="space-y-2">
            <Label for="last_name">Last Name</Label>
            <Input
              id="last_name"
              v-model="formData.last_name"
              type="text"
              placeholder="Doe"
              :disabled="loading"
              :class="{ 'border-destructive': errors.last_name }"
            />
            <p v-if="errors.last_name" class="text-sm text-destructive">{{ errors.last_name }}</p>
          </div>

          <!-- Password -->
          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="formData.password"
              type="password"
              placeholder="••••••••"
              :disabled="loading"
              :class="{ 'border-destructive': errors.password }"
            />
            <p v-if="errors.password" class="text-sm text-destructive">{{ errors.password }}</p>
          </div>

          <!-- Confirm Password -->
          <div class="space-y-2">
            <Label for="password_confirm">Confirm Password</Label>
            <Input
              id="password_confirm"
              v-model="formData.password_confirm"
              type="password"
              placeholder="••••••••"
              :disabled="loading"
              :class="{ 'border-destructive': errors.password_confirm }"
            />
            <p v-if="errors.password_confirm" class="text-sm text-destructive">{{ errors.password_confirm }}</p>
          </div>

          <Button 
            type="submit" 
            class="w-full" 
            :disabled="loading"
          >
            <span v-if="loading">Creating account...</span>
            <span v-else>Create Account</span>
          </Button>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col space-y-4">
        <div class="text-sm text-center text-muted-foreground">
          Already have an account?
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