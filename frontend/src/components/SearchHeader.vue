<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Search, Hash, Filter } from 'lucide-vue-next'

const props = defineProps({
  onSearch: {
    type: Function,
    required: true
  }
})

const emit = defineEmits(['search'])

const query = ref('')
const tab = ref('general') // 'general' | 'isbn' | 'advanced'
const isFocused = ref(false)
const inputRef = ref(null)

watch([query, tab], () => {
  if (tab.value === 'advanced' || !query.value) return
  
  const timeout = setTimeout(() => {
    emit('search', query.value, tab.value === 'isbn' ? 'isbn' : 'general')
    if (props.onSearch) {
      props.onSearch(query.value, tab.value === 'isbn' ? 'isbn' : 'general')
    }
  }, 500)
  
  return () => clearTimeout(timeout)
})

const handleKeyDown = (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    inputRef.value?.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class="w-full mb-12">
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-4xl font-black text-white tracking-tight mb-2">
          Discover <span class="text-indigo-500">Volume</span>
        </h1>
        <p class="text-slate-500 text-sm font-medium">
          Search millions of titles across the Google Books API
        </p>
      </div>

      <div class="flex items-center gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
        <button
          @click="tab = 'general'"
          :class="[
            'relative flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-200',
            tab === 'general'
              ? 'bg-indigo-500 text-white shadow-md'
              : 'text-slate-500 hover:text-white'
          ]"
        >
          <Search :size="14" />
          Search
        </button>
        <button
          @click="tab = 'isbn'"
          :class="[
            'relative flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-200',
            tab === 'isbn'
              ? 'bg-indigo-500 text-white shadow-md'
              : 'text-slate-500 hover:text-white'
          ]"
        >
          <Hash :size="14" />
          ISBN
        </button>
        <button
          @click="{}"
          :class="[
            'relative flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all duration-200',
            tab === 'advanced'
              ? 'bg-indigo-500 text-white shadow-md'
              : 'text-slate-500 hover:text-white'
          ]"
        >
          <Filter :size="14" />
          Advanced
          <span class="text-[8px] bg-white/10 text-slate-400 px-1.5 py-0.5 rounded ml-1">
            Soon
          </span>
        </button>
      </div>
    </div>

    <div :class="['relative group transition-all duration-300', isFocused ? 'scale-[1.005]' : '']">
      <div
        :class="[
          'absolute inset-0 bg-indigo-500/10 blur-2xl opacity-0 transition-opacity duration-300',
          isFocused ? 'opacity-100' : ''
        ]"
      />
      <div
        :class="[
          'relative flex items-center glass rounded-3xl overflow-hidden px-8 py-6 border-2 transition-all duration-300',
          isFocused
            ? 'border-indigo-500 shadow-2xl bg-slate-900/60'
            : 'border-white/5 bg-slate-900/40'
        ]"
      >
        <Search
          :class="[
            'mr-4 transition-colors duration-300',
            isFocused ? 'text-indigo-500' : 'text-slate-500'
          ]"
          :size="24"
        />
        <input
          ref="inputRef"
          v-model="query"
          type="text"
          @focus="isFocused = true"
          @blur="isFocused = false"
          :placeholder="tab === 'isbn' ? 'Enter 10 or 13 digit ISBN...' : 'Find your next intellectual obsession...'"
          class="flex-1 bg-transparent border-none outline-none text-2xl text-white placeholder-slate-700 font-serif italic"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
}
</style>
