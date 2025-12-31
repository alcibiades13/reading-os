<script setup>
import { ref, onMounted } from 'vue'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Users } from 'lucide-vue-next'

const circles = ref([])
const loading = ref(true)

onMounted(async () => {
  // TODO: Fetch circles from API
  loading.value = false
})
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <Users class="w-8 h-8 text-primary" />
        <h1 class="text-3xl font-bold">Reading Circles</h1>
      </div>
      <Button>Create Circle</Button>
    </div>

    <Card v-if="circles.length === 0">
      <CardContent class="p-12 text-center">
        <Users class="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
        <h3 class="text-lg font-semibold mb-2">No circles yet</h3>
        <p class="text-muted-foreground mb-4">
          Create or join a reading circle to discuss books with others
        </p>
        <Button>Create Your First Circle</Button>
      </CardContent>
    </Card>
  </div>
</template>
