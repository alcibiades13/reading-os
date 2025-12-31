<script setup>
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'

const router = useRouter()

const goHome = () => {
  router.push('/home')
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background">
    <div class="text-center space-y-6">
      <h1 class="text-9xl font-bold text-primary">404</h1>
      <h2 class="text-3xl font-semibold">Page Not Found</h2>
      <p class="text-muted-foreground max-w-md mx-auto">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button @click="goHome" size="lg">
        Go Home
      </Button>
    </div>
  </div>
</template>