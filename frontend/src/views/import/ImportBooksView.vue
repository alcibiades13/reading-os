<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useBookImportStore } from '@/stores/bookImportStore'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Search, BookPlus, Command, Hash, Filter, Library, BookOpen } from 'lucide-vue-next'
import ImportBookCard from '@/components/import/ImportBookCard.vue'
import SkeletonCard from '@/components/import/SkeletonCard.vue'
import BookPreviewModal from '@/components/BookPreviewModal.vue'
import AccentText from '@/components/ui/AccentText.vue'
import { useToast } from '@/composables/useToast'

const importStore = useBookImportStore()
const { addToast } = useToast()

const searchInput = ref('')
const isbnInput = ref('')
const delfiUrlInput = ref('')
const tab = ref('general') // 'general', 'isbn', 'delfi', 'advanced'
const showPreviewModal = ref(false)
const isFocused = ref(false)
const searchInputRef = ref(null)

// Debounced auto-search
let debounceTimeout = null
watch([searchInput, tab], () => {
  clearTimeout(debounceTimeout)

  if (tab.value === 'advanced') return

  debounceTimeout = setTimeout(() => {
    const query = tab.value === 'isbn' ? isbnInput.value : searchInput.value

    if (query && query.trim()) {
      if (tab.value === 'isbn') {
        importStore.searchByISBN(query.trim())
      } else {
        importStore.searchBooks(query.trim())
      }
    } else {
      importStore.clearResults()
    }
  }, 500)
})

// Keyboard shortcut Cmd+K / Ctrl+K
const handleKeyDown = (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault()
    searchInputRef.value?.focus()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

// Handle book selection for preview
const handleSelectBook = (book) => {
  importStore.selectBook(book)
  showPreviewModal.value = true
}

// Handle book import
const handleImportBook = async (payload) => {
  const result = await importStore.importBookToDatabase(payload)

  if (result.success) {
    showPreviewModal.value = false
    const message = payload.addToLibrary
      ? `Successfully imported "${payload.book.title}" to your library!`
      : `Successfully imported "${payload.book.title}" to database!`
    addToast(message, 'success')
  } else {
    addToast(`Failed to import: ${result.error}`, 'error')
  }
}

// Close preview modal
const closePreviewModal = () => {
  showPreviewModal.value = false
  importStore.clearSelectedBook()
}

// Suggestion chips for empty state
const suggestions = [
  'Atomic Habits',
  'Project Hail Mary',
  'The Midnight Library',
  'Dune'
]

const handleSuggestionClick = (query) => {
  searchInput.value = query
  tab.value = 'general'
}

// Handle Delfi URL scraping
const handleDelfiUrlSubmit = async () => {
  if (!delfiUrlInput.value || !delfiUrlInput.value.trim()) {
    addToast('Please enter a Delfi.rs URL', 'error')
    return
  }

  await importStore.scrapeDelfiBook(delfiUrlInput.value.trim())
}
</script>

<template>
  <div class="relative z-10 pb-20">
    <!-- Header Section -->
    <div class="w-full max-w-7xl mx-auto pt-12 pb-8 px-6">
      <header class="mb-12">
        <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
          Discover & <AccentText>Import</AccentText>
        </h1>
        <p class="text-slate-400 text-subtitle max-w-2xl leading-relaxed">
          Search millions of books from Google Books and Open Library, and build your digital library with our premium discovery engine.
        </p>
      </header>

      <!-- Source Selector -->
      <div class="mb-6">
        <div class="flex items-center gap-3">
          <span class="text-sm font-medium text-slate-400">Search Source:</span>
          <div class="flex gap-2">
            <button
              @click="importStore.setImportSource('google_books')"
              :class="importStore.importSource === 'google_books' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all flex items-center gap-2"
            >
              <Search :size="14" />
              Google Books
            </button>
            <button
              @click="importStore.setImportSource('open_library')"
              :class="importStore.importSource === 'open_library' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all flex items-center gap-2"
            >
              <BookOpen :size="14" />
              Open Library
            </button>
            <button
              @click="importStore.setImportSource('both')"
              :class="importStore.importSource === 'both' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all flex items-center gap-2"
            >
              <Library :size="14" />
              Both Sources
            </button>
            <button
              @click="importStore.setImportSource('delfi_rs')"
              :class="importStore.importSource === 'delfi_rs' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-4 py-2 rounded-lg text-sm font-semibold border-2 transition-all flex items-center gap-2"
            >
              <BookOpen :size="14" />
              Delfi.rs 🇷🇸
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex items-center gap-1 p-1 bg-slate-900/80 rounded-xl mb-6 w-fit border border-slate-800">
        <button
          @click="tab = 'general'"
          :class="tab === 'general' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'"
          class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
        >
          <Search :size="16" />
          Quick Search
        </button>
        <button
          @click="tab = 'isbn'"
          :class="tab === 'isbn' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'"
          class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
        >
          <Hash :size="16" />
          ISBN Lookup
        </button>
        <button
          @click="tab = 'delfi'"
          :class="tab === 'delfi' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'"
          class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
        >
          <BookOpen :size="16" />
          Delfi.rs URL
        </button>
        <button
          @click="tab = 'advanced'"
          :class="tab === 'advanced' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'"
          class="relative flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
        >
          <Filter :size="16" />
          Advanced
          <span class="text-[9px] bg-amber-500/20 text-amber-500 px-1.5 py-0.5 rounded uppercase tracking-tighter ml-1">
            Coming Soon
          </span>
        </button>
      </div>

      <!-- Search Input -->
      <div :class="isFocused ? 'scale-[1.01]' : ''" class="relative group transition-all duration-300">
        <div :class="isFocused ? 'opacity-100' : 'opacity-0'" class="absolute inset-0 bg-indigo-500/10 blur-xl transition-opacity duration-300" />
        <div :class="isFocused ? 'border-indigo-500 shadow-2xl' : 'border-slate-800'" class="relative flex items-center glass rounded-2xl overflow-hidden px-6 py-5 border-2 transition-all duration-300">
          <Search :class="isFocused ? 'text-indigo-500' : 'text-slate-500'" class="mr-4 transition-colors duration-300" :size="24" />
          <input
            v-if="tab === 'general'"
            ref="searchInputRef"
            v-model="searchInput"
            type="text"
            @focus="isFocused = true"
            @blur="isFocused = false"
            placeholder="Search by title, author, or keywords..."
            class="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder-slate-600 font-medium"
          />
          <input
            v-else-if="tab === 'isbn'"
            v-model="isbnInput"
            type="text"
            @focus="isFocused = true"
            @blur="isFocused = false"
            placeholder="Enter 10 or 13 digit ISBN..."
            class="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder-slate-600 font-medium"
          />
          <input
            v-else-if="tab === 'delfi'"
            v-model="delfiUrlInput"
            type="text"
            @focus="isFocused = true"
            @blur="isFocused = false"
            @keyup.enter="handleDelfiUrlSubmit"
            placeholder="Paste Delfi.rs book URL (e.g., https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html)"
            class="flex-1 bg-transparent border-none outline-none text-xl text-white placeholder-slate-600 font-medium"
          />
          <button
            v-if="tab === 'delfi' && delfiUrlInput"
            @click="handleDelfiUrlSubmit"
            class="ml-4 px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg font-semibold transition-colors"
          >
            Find
          </button>
          <div v-else class="hidden sm:flex items-center gap-1 px-3 py-1 rounded-lg bg-slate-800/80 border border-slate-700 text-slate-500 text-xs font-bold">
            <Command :size="12" />
            <span>K</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div class="max-w-7xl mx-auto px-6">
      <!-- Error Message -->
      <div
        v-if="importStore.error"
        class="mb-8 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-center"
      >
        {{ importStore.error }}
      </div>

      <!-- Empty State -->
      <div
        v-if="!importStore.loading && !importStore.hasResults && !importStore.error"
        class="flex flex-col items-center justify-center py-32 text-center opacity-50"
      >
        <div class="p-6 rounded-full bg-slate-900/50 border border-slate-800 mb-6">
          <Search :size="48" class="text-slate-600" />
        </div>
        <h2 class="text-2xl font-bold text-white mb-2">Search millions of books</h2>
        <p class="max-w-md text-slate-400">Enter a title, author, or ISBN to start exploring. Try searching for "The Midnight Library".</p>

        <div class="mt-12 flex flex-wrap justify-center gap-3">
          <span class="text-xs font-bold uppercase tracking-widest text-slate-600 w-full mb-2">Popular suggestions</span>
          <button
            v-for="suggestion in suggestions"
            :key="suggestion"
            @click="handleSuggestionClick(suggestion)"
            class="px-4 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-400 hover:text-white hover:border-slate-600 transition-all"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>

      <!-- Loading Skeletons -->
      <div
        v-if="importStore.loading"
        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700"
      >
        <SkeletonCard v-for="i in 10" :key="i" />
      </div>

      <!-- Results Grid -->
      <div
        v-else-if="importStore.hasResults"
        class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700"
      >
        <ImportBookCard
          v-for="(book, index) in importStore.searchResults"
          :key="book.google_books_id || book.open_library_id || `book-${index}`"
          :book="book"
          @click="handleSelectBook"
        />
      </div>
    </div>

    <!-- Book Preview Modal -->
    <BookPreviewModal
      v-if="showPreviewModal && importStore.selectedBook"
      :book="importStore.selectedBook"
      :open="showPreviewModal"
      @close="closePreviewModal"
      @import="handleImportBook"
    />
  </div>
</template>
