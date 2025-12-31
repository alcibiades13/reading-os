<script setup>
import { Sparkles, CheckCircle, AlertCircle, Info } from 'lucide-vue-next'

defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'success', // 'success', 'error', 'info'
  }
})
</script>

<template>
  <div class="pointer-events-auto bg-slate-900 border border-slate-800 rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full duration-300">
    <!-- Icon based on type -->
    <div
      :class="{
        'bg-emerald-500/20': type === 'success',
        'bg-red-500/20': type === 'error',
        'bg-sky-500/20': type === 'info'
      }"
      class="w-6 h-6 rounded-full flex items-center justify-center shrink-0"
    >
      <Sparkles
        v-if="type === 'success'"
        :size="14"
        class="text-emerald-500"
      />
      <AlertCircle
        v-else-if="type === 'error'"
        :size="14"
        class="text-red-500"
      />
      <Info
        v-else
        :size="14"
        class="text-sky-500"
      />
    </div>

    <!-- Message -->
    <p class="text-sm font-medium text-slate-200">{{ message }}</p>
  </div>
</template>
