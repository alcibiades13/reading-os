<script setup>
defineProps({
  icon: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-20 text-center opacity-60">
    <div class="p-6 rounded-full bg-zinc-900/50 border border-zinc-800 mb-6">
      <component :is="icon" :size="48" class="text-zinc-600" />
    </div>
    <h2 class="text-xl font-bold text-white mb-2">{{ title }}</h2>
    <p v-if="description" class="max-w-md text-zinc-400 text-sm">{{ description }}</p>
    <slot name="action" />
  </div>
</template>
