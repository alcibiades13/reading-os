<script setup>
import { ref, watch, onMounted } from 'vue'
import { Search, Download, BookOpen, Loader2, Globe } from 'lucide-vue-next'
import { ebooksAPI } from '@/services/api'

const emit = defineEmits(['imported', 'open'])

// Gutenberg language codes
const LANGUAGES = [
  { code: '', label: 'All languages' },
  { code: 'sr', label: 'Serbian' },
  { code: 'hr', label: 'Croatian' },
  { code: 'en', label: 'English' },
  { code: 'de', label: 'German' },
  { code: 'fr', label: 'French' },
  { code: 'ru', label: 'Russian' },
  { code: 'it', label: 'Italian' },
  { code: 'es', label: 'Spanish' },
  { code: 'la', label: 'Latin' },
  { code: 'el', label: 'Greek' },
]

const query = ref('')
const language = ref('')
const results = ref([])
const page = ref(1)
const hasNext = ref(false)
const loading = ref(false)
const error = ref('')
const importing = ref({}) // gutenberg id -> true
let searchTimer = null
let requestId = 0

const load = async (append = false) => {
  const current = ++requestId
  loading.value = true
  error.value = ''
  try {
    const { data } = await ebooksAPI.publicDomainSearch({
      q: query.value.trim() || undefined,
      language: language.value || undefined,
      page: page.value,
    })
    if (current !== requestId) return
    results.value = append ? [...results.value, ...data.results] : data.results
    hasNext.value = data.has_next
  } catch (err) {
    if (current !== requestId) return
    error.value = err?.response?.data?.detail || 'Could not reach the catalog. Try again in a moment.'
    if (!append) results.value = []
  } finally {
    if (current === requestId) loading.value = false
  }
}

const reload = () => {
  page.value = 1
  load()
}

const loadMore = () => {
  page.value++
  load(true)
}

watch(query, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(reload, 450)
})
watch(language, reload)
onMounted(load)

const importBook = async (book) => {
  if (book.ebook_id) {
    emit('open', book.ebook_id)
    return
  }
  importing.value = { ...importing.value, [book.id]: true }
  try {
    const { data } = await ebooksAPI.publicDomainImport(book.id)
    book.ebook_id = data.id
    emit('imported', data)
  } catch (err) {
    error.value = err?.response?.data?.detail || 'Download failed. Try again in a moment.'
  } finally {
    importing.value = { ...importing.value, [book.id]: false }
  }
}

const hideBrokenCover = (e) => {
  e.target.style.display = 'none'
}
</script>

<template>
  <div>
    <p class="text-sm text-zinc-500 mb-5 max-w-2xl">
      Classics whose copyright has expired, from <span class="text-zinc-300">Project Gutenberg</span>. Free to read and keep -
      adding one puts a copy in your e-books, with the same reader, progress tracking and notes.
    </p>

    <div class="flex flex-col sm:flex-row gap-3 mb-6">
      <div class="relative flex-1 max-w-md">
        <Search :size="16" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" />
        <input
          v-model="query"
          placeholder="Search title or author… (e.g. Dostoevsky, Nušić)"
          class="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 outline-none transition-all"
        />
      </div>
      <div class="relative">
        <Globe :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
        <select
          v-model="language"
          class="appearance-none bg-zinc-900/50 border border-zinc-800 rounded-xl pl-9 pr-8 py-2.5 text-sm text-white focus:border-indigo-500 outline-none cursor-pointer"
        >
          <option v-for="lang in LANGUAGES" :key="lang.code" :value="lang.code">{{ lang.label }}</option>
        </select>
      </div>
    </div>

    <p v-if="error" class="text-sm text-amber-400 mb-4">{{ error }}</p>

    <div v-if="loading && !results.length" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 lg:gap-6">
      <div v-for="i in 12" :key="i" class="aspect-[2/3] rounded-xl bg-zinc-900/60 animate-pulse" />
    </div>

    <p v-else-if="!results.length && !error" class="text-center text-sm text-zinc-500 py-16">
      No free e-books found{{ query ? ` for "${query}"` : '' }}. Books still under copyright aren't in this catalog.
    </p>

    <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-4 gap-y-6 lg:gap-x-6 lg:gap-y-8">
      <div v-for="book in results" :key="book.id" class="flex flex-col">
        <div class="relative aspect-[2/3] rounded-xl overflow-hidden shadow-lg ring-1 ring-white/5 bg-gradient-to-br from-indigo-950 via-zinc-900 to-zinc-950">
          <div class="absolute inset-0 flex flex-col items-center justify-center gap-2 p-3 text-center">
            <BookOpen :size="18" class="text-indigo-400/50" />
            <p class="text-[11px] font-serif font-bold text-zinc-400 line-clamp-4">{{ book.title }}</p>
          </div>
          <img :src="book.cover_url" :alt="book.title" loading="lazy" class="relative w-full h-full object-cover" @error="hideBrokenCover" />
        </div>
        <p class="mt-2.5 text-sm font-bold text-white leading-snug line-clamp-2">{{ book.title }}</p>
        <p class="text-xs text-zinc-500 truncate mt-0.5">{{ book.authors.join(', ') || 'Unknown author' }}</p>
        <button
          class="mt-2 flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-bold transition-all disabled:opacity-60"
          :class="book.ebook_id ? 'bg-zinc-800 text-zinc-200 hover:bg-zinc-700' : 'bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500 hover:text-white'"
          :disabled="importing[book.id]"
          @click="importBook(book)"
        >
          <Loader2 v-if="importing[book.id]" :size="13" class="animate-spin" />
          <BookOpen v-else-if="book.ebook_id" :size="13" />
          <Download v-else :size="13" />
          {{ importing[book.id] ? 'Adding…' : book.ebook_id ? 'Read' : 'Add to e-books' }}
        </button>
      </div>
    </div>

    <div v-if="hasNext && results.length" class="flex justify-center mt-8">
      <button
        class="px-5 py-2.5 rounded-xl border border-zinc-700 text-sm font-bold text-zinc-300 hover:text-white hover:border-zinc-500 transition-all flex items-center gap-2 disabled:opacity-50"
        :disabled="loading"
        @click="loadMore"
      >
        <Loader2 v-if="loading" :size="14" class="animate-spin" />
        Load more
      </button>
    </div>
  </div>
</template>
