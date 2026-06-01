<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { searchAPI } from '@/services/api'
import { Search, BookOpen, Quote, BookMarked, Loader2, X, Brain, Star } from 'lucide-vue-next'

const router = useRouter()

const query = ref('')
const results = ref(null)
const isLoading = ref(false)
const error = ref(null)

let debounceTimer = null

const hasResults = computed(() => {
  if (!results.value) return false
  return (
    results.value.quotes.length > 0 ||
    results.value.study_notes.length > 0 ||
    results.value.vocabulary.length > 0
  )
})

const totalResults = computed(() => {
  if (!results.value) return 0
  return results.value.quotes.length + results.value.study_notes.length + results.value.vocabulary.length
})

watch(query, (val) => {
  clearTimeout(debounceTimer)
  if (!val || val.trim().length < 2) {
    results.value = null
    return
  }
  debounceTimer = setTimeout(() => performSearch(val.trim()), 350)
})

const performSearch = async (q) => {
  isLoading.value = true
  error.value = null
  try {
    const res = await searchAPI.unified(q, 8)
    results.value = res.data
  } catch (e) {
    error.value = 'Search failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const clearSearch = () => {
  query.value = ''
  results.value = null
}

const highlight = (text, q) => {
  if (!text || !q) return text
  const escaped = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp(`(${escaped})`, 'gi'), '<mark class="bg-indigo-500/30 text-indigo-200 rounded px-0.5">$1</mark>')
}

const goToBook = (bookId) => {
  if (bookId) router.push(`/books/${bookId}`)
}

const goToQuotes = (result) => {
  router.push({ path: '/quotes', query: { book: result.book_id } })
}

const masteryColor = {
  new: 'text-slate-400 bg-slate-800',
  learning: 'text-amber-400 bg-amber-500/10',
  mastered: 'text-emerald-400 bg-emerald-500/10',
}
</script>

<template>
  <div class="animate-in fade-in duration-500 pb-20 min-h-screen">
    <!-- Mobile header -->
    <div class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 safe-area-top">
      <div class="flex items-center gap-3 px-4 py-3">
        <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Search :size="18" class="text-indigo-400" />
        </div>
        <div>
          <h1 class="text-base font-bold text-white">Search</h1>
          <p class="text-xs text-slate-500">Quotes, notes & vocabulary</p>
        </div>
      </div>
    </div>

    <!-- Desktop header -->
    <div class="hidden lg:block px-6 pt-6 pb-4">
      <h1 class="text-2xl font-bold text-white">Search your library</h1>
      <p class="text-slate-400 text-sm mt-1">Full-text search across quotes, study notes, and vocabulary</p>
    </div>

    <!-- Search input -->
    <div class="px-4 lg:px-6 pt-4 lg:pt-2">
      <div class="relative max-w-2xl">
        <Search :size="18" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
        <input
          v-model="query"
          type="text"
          placeholder="Search quotes, notes, vocabulary..."
          autofocus
          class="w-full bg-slate-800/80 border border-slate-700/60 rounded-xl pl-10 pr-10 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30 transition-all"
        />
        <button
          v-if="query"
          @click="clearSearch"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
        >
          <X :size="16" />
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center gap-2 px-4 lg:px-6 mt-6 text-slate-400 text-sm">
      <Loader2 :size="16" class="animate-spin" />
      <span>Searching...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="px-4 lg:px-6 mt-6">
      <p class="text-red-400 text-sm">{{ error }}</p>
    </div>

    <!-- Empty state (query too short or no query) -->
    <div v-else-if="!query || query.trim().length < 2" class="px-4 lg:px-6 mt-12 flex flex-col items-center text-center">
      <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
        <Search :size="28" class="text-indigo-400" />
      </div>
      <p class="text-slate-300 font-medium">Search your reading knowledge</p>
      <p class="text-slate-500 text-sm mt-1">Type at least 2 characters to search across all your collected wisdom</p>
    </div>

    <!-- No results -->
    <div v-else-if="results && !hasResults" class="px-4 lg:px-6 mt-12 flex flex-col items-center text-center">
      <p class="text-slate-300 font-medium">No results for "{{ query }}"</p>
      <p class="text-slate-500 text-sm mt-1">Try different keywords or shorter terms</p>
    </div>

    <!-- Results -->
    <div v-else-if="results && hasResults" class="px-4 lg:px-6 mt-5 space-y-6 max-w-2xl">
      <p class="text-xs text-slate-500 font-medium uppercase tracking-wider">{{ totalResults }} result{{ totalResults !== 1 ? 's' : '' }} for "{{ query }}"</p>

      <!-- Quotes -->
      <div v-if="results.quotes.length > 0">
        <div class="flex items-center gap-2 mb-2">
          <Quote :size="14" class="text-indigo-400" />
          <span class="text-xs font-bold text-indigo-400 uppercase tracking-wider">Quotes</span>
          <span class="text-xs text-slate-600">({{ results.quotes.length }})</span>
        </div>
        <div class="space-y-2">
          <button
            v-for="item in results.quotes"
            :key="item.id"
            @click="goToQuotes(item)"
            class="w-full text-left bg-slate-800/60 border border-slate-700/40 rounded-xl p-3.5 hover:border-indigo-500/30 hover:bg-slate-800 transition-all"
          >
            <div class="flex items-start gap-2">
              <div class="flex-1 min-w-0">
                <p class="text-sm text-slate-200 leading-relaxed line-clamp-2" v-html="highlight(item.text, query)" />
                <div class="flex items-center gap-2 mt-1.5">
                  <span v-if="item.book_title" class="text-xs text-slate-500 truncate">{{ item.book_title }}</span>
                  <span v-if="item.chapter" class="text-xs text-slate-600">· ch. {{ item.chapter }}</span>
                  <span v-if="item.page_number" class="text-xs text-slate-600">· p. {{ item.page_number }}</span>
                </div>
                <p v-if="item.note" class="text-xs text-slate-500 mt-1 italic line-clamp-1" v-html="highlight(item.note, query)" />
              </div>
              <Star v-if="item.is_favorite" :size="12" class="text-amber-400 flex-shrink-0 mt-1" />
            </div>
          </button>
        </div>
      </div>

      <!-- Study Notes -->
      <div v-if="results.study_notes.length > 0">
        <div class="flex items-center gap-2 mb-2">
          <BookMarked :size="14" class="text-sky-400" />
          <span class="text-xs font-bold text-sky-400 uppercase tracking-wider">Study Notes</span>
          <span class="text-xs text-slate-600">({{ results.study_notes.length }})</span>
        </div>
        <div class="space-y-2">
          <button
            v-for="item in results.study_notes"
            :key="item.id"
            @click="goToBook(item.book_id)"
            class="w-full text-left bg-slate-800/60 border border-slate-700/40 rounded-xl p-3.5 hover:border-sky-500/30 hover:bg-slate-800 transition-all"
          >
            <p class="text-sm text-slate-200 leading-relaxed line-clamp-2" v-html="highlight(item.text, query)" />
            <div class="flex items-center gap-2 mt-1.5">
              <span v-if="item.note_type" class="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400">{{ item.note_type }}</span>
              <span v-if="item.book_title" class="text-xs text-slate-500 truncate">{{ item.book_title }}</span>
              <span v-if="item.chapter" class="text-xs text-slate-600">· ch. {{ item.chapter }}</span>
            </div>
          </button>
        </div>
      </div>

      <!-- Vocabulary -->
      <div v-if="results.vocabulary.length > 0">
        <div class="flex items-center gap-2 mb-2">
          <Brain :size="14" class="text-emerald-400" />
          <span class="text-xs font-bold text-emerald-400 uppercase tracking-wider">Vocabulary</span>
          <span class="text-xs text-slate-600">({{ results.vocabulary.length }})</span>
        </div>
        <div class="space-y-2">
          <button
            v-for="item in results.vocabulary"
            :key="item.id"
            @click="router.push('/vocabulary')"
            class="w-full text-left bg-slate-800/60 border border-slate-700/40 rounded-xl p-3.5 hover:border-emerald-500/30 hover:bg-slate-800 transition-all"
          >
            <div class="flex items-start justify-between gap-2">
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-white" v-html="highlight(item.text, query)" />
                <p v-if="item.definition" class="text-xs text-slate-400 mt-0.5 line-clamp-1" v-html="highlight(item.definition, query)" />
                <span v-if="item.book_title" class="text-xs text-slate-500">{{ item.book_title }}</span>
              </div>
              <span :class="['text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded flex-shrink-0', masteryColor[item.mastery]]">
                {{ item.mastery }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
