<script setup>
import { Sparkles, CheckCircle, AlertCircle, Info } from 'lucide-vue-next'

const props = defineProps({
  message: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'success',
  },
  action: {
    type: Object,
    default: null, // { label: 'Undo', callback: fn }
  }
})

const emit = defineEmits(['dismiss'])

const handleAction = () => {
  props.action?.callback()
  emit('dismiss')
}
</script>

<template>
  <div class="pointer-events-auto bg-zinc-900 border border-zinc-800 rounded-xl px-5 py-4 shadow-2xl flex items-center gap-3 animate-in slide-in-from-right-full duration-300">
    <!-- Icon -->
    <div
      :class="{
        'bg-emerald-500/20': type === 'success',
        'bg-red-500/20': type === 'error',
        'bg-sky-500/20': type === 'info'
      }"
      class="w-6 h-6 rounded-full flex items-center justify-center shrink-0"
    >
      <Sparkles v-if="type === 'success'" :size="14" class="text-emerald-500" />
      <AlertCircle v-else-if="type === 'error'" :size="14" class="text-red-500" />
      <Info v-else :size="14" class="text-sky-500" />
    </div>

    <!-- Message -->
    <p class="text-sm font-medium text-zinc-200 flex-1">{{ message }}</p>

    <!-- Action button (e.g. Undo) -->
    <button
      v-if="action"
      @click="handleAction"
      class="text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors shrink-0 ml-2"
    >
      {{ action.label }}
    </button>
  </div>
</template>
