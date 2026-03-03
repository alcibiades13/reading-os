<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useBookImportStore } from '@/stores/bookImportStore'
import { Search, BookPlus, Command, Hash, Filter, Library, BookOpen, PenLine, X } from 'lucide-vue-next'

const showMobileFilters = ref(false)
import ImportBookCard from '@/components/import/ImportBookCard.vue'
import SkeletonCard from '@/components/import/SkeletonCard.vue'
import ManualEntryForm from '@/components/import/ManualEntryForm.vue'
import BookPreviewModal from '@/components/BookPreviewModal.vue'
import AccentText from '@/components/ui/AccentText.vue'
import { useToast } from '@/composables/useToast'

const importStore = useBookImportStore()
const { addToast } = useToast()

const searchInput = ref('')
const isbnInput = ref('')
const delfiUrlInput = ref('')
const tab = ref('general') // 'general', 'isbn', 'delfi', 'manual'
const showPreviewModal = ref(false)
const isFocused = ref(false)
const searchInputRef = ref(null)

// Debounced auto-search
let debounceTimeout = null
watch([searchInput, tab], () => {
  clearTimeout(debounceTimeout)

  if (tab.value === 'manual') return

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
    // Close modal and show error
    showPreviewModal.value = false
    addToast(result.error || 'Failed to import book', 'error')
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

// Handle manual entry form submit
const handleManualSubmit = (bookData) => {
  importStore.selectBook(bookData)
  showPreviewModal.value = true
}
</script>

<template>
  <div class="relative z-10 pb-20">
    <!-- Mobile Header (Sticky - minimal) -->
    <div class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 safe-area-top">
      <div class="flex items-center justify-between px-4 py-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <BookPlus :size="18" class="text-indigo-400" />
          </div>
          <div>
            <h1 class="text-base font-bold text-white">Import Books</h1>
            <p class="text-xs text-slate-500">Search & discover</p>
          </div>
        </div>
        <button
          @click="showMobileFilters = true"
          class="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-400 active:scale-95 transition-transform"
        >
          <Filter :size="18" />
        </button>
      </div>
    </div>

    <!-- Mobile Content Area (Not sticky) -->
    <div class="lg:hidden px-4 pt-4 space-y-3">
      <!-- Mobile Tabs -->
      <div class="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
        <button
          @click="tab = 'general'"
          :class="tab === 'general' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border transition-all"
        >
          <Search :size="14" />
          Search
        </button>
        <button
          @click="tab = 'isbn'"
          :class="tab === 'isbn' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border transition-all"
        >
          <Hash :size="14" />
          ISBN
        </button>
        <button
          @click="tab = 'delfi'"
          :class="tab === 'delfi' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border transition-all"
        >
          <BookOpen :size="14" />
          Delfi URL
        </button>
        <button
          @click="tab = 'manual'"
          :class="tab === 'manual' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold border transition-all"
        >
          <PenLine :size="14" />
          Manual
        </button>
      </div>

      <!-- Mobile: Manual Entry Form -->
      <div v-if="tab === 'manual'">
        <ManualEntryForm @submit="handleManualSubmit" />
      </div>

      <!-- Mobile Search Input -->
      <template v-else>
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
          <input
            v-if="tab === 'general'"
            v-model="searchInput"
            type="text"
            placeholder="Search books..."
            class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
          />
          <input
            v-else-if="tab === 'isbn'"
            v-model="isbnInput"
            type="text"
            placeholder="Enter ISBN..."
            class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
          />
          <input
            v-else-if="tab === 'delfi'"
            v-model="delfiUrlInput"
            type="text"
            @keyup.enter="handleDelfiUrlSubmit"
            placeholder="Paste Delfi.rs URL..."
            class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-12 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
          />
          <button
            v-if="tab === 'delfi' && delfiUrlInput"
            @click="handleDelfiUrlSubmit"
            class="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-indigo-500 text-white rounded-lg text-xs font-bold"
          >
            Find
          </button>
        </div>

        <!-- Active Source Indicator -->
        <div class="flex items-center gap-2">
          <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Source:</span>
          <span class="text-xs font-bold text-indigo-400">
            {{ importStore.importSource === 'google_books' ? 'Google Books' :
               importStore.importSource === 'open_library' ? 'Open Library' :
               importStore.importSource === 'hardcover' ? 'Hardcover' :
               importStore.importSource === 'both' ? 'All Sources' : 'Delfi.rs' }}
          </span>
        </div>
      </template>
    </div>

    <!-- Mobile Filter Panel -->
    <Teleport to="body">
      <Transition name="slide">
        <div
          v-if="showMobileFilters"
          class="fixed inset-0 z-50 lg:hidden"
        >
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/60 backdrop-blur-sm"
            @click="showMobileFilters = false"
          />

          <!-- Panel -->
          <div class="absolute right-0 top-0 bottom-0 w-[85%] max-w-sm bg-slate-900 border-l border-slate-800 overflow-y-auto safe-area-inset">
            <!-- Panel Header -->
            <div class="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 px-4 py-4">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-bold text-white">Search Source</h2>
                <button
                  @click="showMobileFilters = false"
                  class="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400"
                >
                  <X :size="20" />
                </button>
              </div>
            </div>

            <div class="p-4 space-y-6">
              <!-- Source Selection -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Choose Source</h3>
                <div class="space-y-2">
                  <button
                    @click="importStore.setImportSource('google_books'); showMobileFilters = false"
                    :class="importStore.importSource === 'google_books' ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Search :size="18" />
                    <span class="font-bold">Google Books</span>
                  </button>
                  <button
                    @click="importStore.setImportSource('open_library'); showMobileFilters = false"
                    :class="importStore.importSource === 'open_library' ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <BookOpen :size="18" />
                    <span class="font-bold">Open Library</span>
                  </button>
                  <button
                    @click="importStore.setImportSource('both'); showMobileFilters = false"
                    :class="importStore.importSource === 'both' ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Library :size="18" />
                    <span class="font-bold">Both Sources</span>
                  </button>
                  <button
                    @click="importStore.setImportSource('hardcover'); showMobileFilters = false"
                    :class="importStore.importSource === 'hardcover' ? 'border-purple-500 bg-purple-500/10 text-purple-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <BookOpen :size="18" />
                    <span class="font-bold">Hardcover</span>
                  </button>
                  <button
                    @click="importStore.setImportSource('delfi_rs'); showMobileFilters = false"
                    :class="importStore.importSource === 'delfi_rs' ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <BookOpen :size="18" />
                    <span class="font-bold">Delfi.rs 🇷🇸</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Header Section (Desktop) -->
    <div class="hidden lg:block w-full max-w-7xl mx-auto pt-12 pb-8 px-6">
      <header class="mb-12">
        <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
          Discover & <AccentText>Import</AccentText>
        </h1>
        <p class="text-slate-400 text-subtitle max-w-2xl leading-relaxed">
          Search millions of books from Google Books and Open Library, and build your digital library with our premium discovery engine.
        </p>
      </header>

      <!-- Source Selector -->
      <div v-if="tab !== 'manual'" class="mb-6">
        <div class="flex flex-col sm:flex-row sm:items-center gap-3">
          <span class="text-sm font-medium text-slate-400 shrink-0">Search Source:</span>
          <div class="flex flex-wrap gap-2">
            <button
              @click="importStore.setImportSource('google_books')"
              :class="importStore.importSource === 'google_books' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold border-2 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <Search :size="14" />
              Google Books
            </button>
            <button
              @click="importStore.setImportSource('open_library')"
              :class="importStore.importSource === 'open_library' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold border-2 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <BookOpen :size="14" />
              Open Library
            </button>
            <button
              @click="importStore.setImportSource('both')"
              :class="importStore.importSource === 'both' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold border-2 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <Library :size="14" />
              Both
            </button>
            <button
              @click="importStore.setImportSource('hardcover')"
              :class="importStore.importSource === 'hardcover' ? 'bg-purple-500 text-white border-purple-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-purple-500/50 hover:text-purple-400'"
              class="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold border-2 transition-all flex items-center gap-2 whitespace-nowrap"
            >
              <BookOpen :size="14" />
              Hardcover
            </button>
            <button
              @click="importStore.setImportSource('delfi_rs')"
              :class="importStore.importSource === 'delfi_rs' ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-transparent border-slate-700 text-slate-400 hover:border-indigo-500/50 hover:text-indigo-400'"
              class="px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-semibold border-2 transition-all flex items-center gap-2 whitespace-nowrap"
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
          @click="tab = 'manual'"
          :class="tab === 'manual' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'"
          class="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200"
        >
          <PenLine :size="16" />
          Manual Entry
        </button>
      </div>

      <!-- Search Input -->
      <div v-if="tab !== 'manual'" :class="isFocused ? 'scale-[1.01]' : ''" class="relative group transition-all duration-300">
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

      <!-- Manual Entry Form (Desktop) -->
      <ManualEntryForm v-if="tab === 'manual'" @submit="handleManualSubmit" />
    </div>

    <!-- Results Section -->
    <div v-if="tab !== 'manual'" class="max-w-7xl mx-auto px-6">
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

<style scoped>
/* Slide transition for mobile filter panel */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-active > div:last-child,
.slide-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from > div:last-child,
.slide-leave-to > div:last-child {
  transform: translateX(100%);
}

/* Hide scrollbar for horizontal scroll */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Safe area support */
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}

.safe-area-inset {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

/* Touch feedback */
button {
  -webkit-tap-highlight-color: transparent;
}
</style>
