<script setup>
import { ref, watch } from 'vue'
import { Search, Command } from 'lucide-vue-next'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search...'
  },
  showShortcut: {
    type: Boolean,
    default: true
  },
  debounce: {
    type: Number,
    default: 500
  }
})

const emit = defineEmits(['update:modelValue', 'search'])

const isFocused = ref(false)
const inputRef = ref(null)
let debounceTimeout = null

const handleInput = (e) => {
  const value = e.target.value
  emit('update:modelValue', value)

  clearTimeout(debounceTimeout)
  debounceTimeout = setTimeout(() => {
    emit('search', value)
  }, props.debounce)
}

// Expose focus method for parent components
defineExpose({
  focus: () => inputRef.value?.focus()
})
</script>

<template>
  <div :class="isFocused ? 'scale-[1.01]' : ''" class="relative group transition-all duration-300">
    <div :class="isFocused ? 'opacity-100' : 'opacity-0'" class="absolute inset-0 bg-indigo-500/10 blur-xl transition-opacity duration-300" />
    <div :class="isFocused ? 'border-indigo-500 shadow-2xl' : 'border-slate-800'" class="relative flex items-center glass rounded-2xl overflow-hidden px-6 py-4 border-2 transition-all duration-300">
      <Search :class="isFocused ? 'text-indigo-500' : 'text-slate-500'" class="mr-4 transition-colors duration-300" :size="20" />
      <input
        ref="inputRef"
        :value="modelValue"
        type="text"
        @input="handleInput"
        @focus="isFocused = true"
        @blur="isFocused = false"
        :placeholder="placeholder"
        class="flex-1 bg-transparent border-none outline-none text-lg text-white placeholder-slate-600 font-medium"
      />
      <div v-if="showShortcut" class="hidden sm:flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-500 text-xs font-bold">
        <Command :size="12" />
        <span>K</span>
      </div>
    </div>
  </div>
</template>
