<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  icon: {
    type: Object,
    default: null
  },
  valueColor: {
    type: String,
    default: 'text-indigo-400'
  }
})
</script>

<template>
  <div class="glass rounded-xl p-4 border border-zinc-700/50 hover:border-indigo-500/30 transition-all duration-300">
    <div class="flex items-center justify-between">
      <div>
        <p class="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-1">{{ label }}</p>
        <p class="text-2xl font-bold" :class="valueColor">{{ value }}</p>
      </div>
      <component
        v-if="icon"
        :is="icon"
        :size="32"
        class="text-zinc-600"
      />
    </div>
  </div>
</template>
