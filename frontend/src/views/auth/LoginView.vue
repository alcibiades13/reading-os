<!-- Paste LoginView.vue content here -->
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

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const handleLogin = async () => {
  error.value = ''
  
  // Validation
  if (!email.value || !password.value) {
    error.value = 'Please fill in all fields'
    return
  }

  loading.value = true

  const result = await authStore.login({
    email: email.value,
    password: password.value,
  })

  loading.value = false

  if (result.success) {
    // Redirect to home or saved redirect path
    const redirect = router.currentRoute.value.query.redirect || '/home'
    router.push(redirect)
  } else {
    error.value = result.error || 'Login failed. Please check your credentials.'
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
    <Card class="w-full max-w-md shadow-xl">
      <CardHeader class="space-y-1">
        <CardTitle class="text-3xl font-bold text-center">Reading OS</CardTitle>
        <CardDescription class="text-center">
          Sign in to your account to continue
        </CardDescription>
      </CardHeader>
      
      <CardContent class="space-y-4">
        <!-- Error message -->
        <div v-if="error" class="p-3 bg-destructive/10 text-destructive text-sm rounded-md">
          {{ error }}
        </div>

        <!-- Login form -->
        <form @submit.prevent="handleLogin" class="space-y-4">
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

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="password"
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
            <span v-if="loading">Signing in...</span>
            <span v-else>Sign In</span>
          </Button>
        </form>
      </CardContent>

      <CardFooter class="flex flex-col space-y-4">
        <div class="text-sm text-center text-muted-foreground">
          Don't have an account?
          <button
            @click="goToRegister"
            class="text-primary hover:underline font-medium ml-1"
            type="button"
          >
            Sign up
          </button>
        </div>
      </CardFooter>
    </Card>
  </div>
</template>