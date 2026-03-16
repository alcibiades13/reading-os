<script setup>
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'

const router = useRouter()

const goHome = () => {
  router.push('/home')
}

const refresh = () => {
  window.location.reload()
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center space-y-6">
      <h1 class="text-9xl font-bold text-primary">500</h1>
      <h2 class="text-3xl font-semibold">Something Went Wrong</h2>
      <p class="text-muted-foreground max-w-md mx-auto">
        We're having trouble processing your request. Please try refreshing the page or come back later.
      </p>
      <div class="flex gap-3 justify-center">
        <Button @click="refresh" variant="outline" size="lg">
          Refresh Page
        </Button>
        <Button @click="goHome" size="lg">
          Go Home
        </Button>
      </div>
    </div>
  </div>
</template>
