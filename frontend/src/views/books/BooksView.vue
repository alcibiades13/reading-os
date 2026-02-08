<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import PageHeader from '@/components/ui/PageHeader.vue'
import SectionHeader from '@/components/ui/SectionHeader.vue'
import SearchBar from '@/components/ui/SearchBar.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { BookOpen, Plus, TrendingUp, Calendar, Trash2, Check, ChevronDown, Filter, Search, X } from 'lucide-vue-next'

const showMobileFilters = ref(false)

const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()

const searchQuery = ref('')
const selectedGenre = ref(null)
const popularBooks = ref([])
const recentBooks = ref([])
const trendingBooks = ref([])
const isAddDialogOpen = ref(false)
const selectedBook = ref(null)
const addBookStatus = ref('want_to_read')
const showGenreDropdown = ref(false)
const isSearching = ref(false)
const isInitialLoad = ref(true)

// All books combined (without trending duplicates)
const allBooksExceptTrending = computed(() => {
  const booksMap = new Map()
  const trendingIds = new Set(trendingBooks.value.map(b => b.id))

  // Add recent books
  recentBooks.value.forEach(book => {
    if (!trendingIds.has(book.id)) {
      booksMap.set(book.id, book)
    }
  })

  // Add popular books
  popularBooks.value.forEach(book => {
    if (!trendingIds.has(book.id) && !booksMap.has(book.id)) {
      booksMap.set(book.id, book)
    }
  })

  return Array.from(booksMap.values())
})

const selectedGenreLabel = computed(() => {
  if (!selectedGenre.value) return 'All Genres'
  const genre = booksStore.genres.find(g => g.id === selectedGenre.value)
  return genre?.name || 'All Genres'
})

// Handle immediate input (before debounce) to show loading state
const handleSearchInput = (value) => {
  // Set loading state immediately when user starts typing
  if (value && value.trim()) {
    isSearching.value = true
  }
}

const handleSearch = async (value) => {
  // Set loading state FIRST, synchronously, before ANY other state changes
  isSearching.value = true

  // Wait for next tick to ensure loading state is rendered before proceeding
  await nextTick()

  // Then update all other state
  selectedGenre.value = null
  booksStore.setFilter('genre', null)
  booksStore.setFilter('search', value)

  if (value && value.trim()) {
    await booksStore.fetchBooks()
  } else {
    booksStore.books = []
  }

  isSearching.value = false
}

const filterByGenre = async (genreId) => {
  selectedGenre.value = genreId
  showGenreDropdown.value = false
  searchQuery.value = '' // Clear search when filtering by genre
  booksStore.setFilter('search', '')
  booksStore.setFilter('genre', genreId)
  if (genreId) {
    await booksStore.fetchBooks()
  } else {
    // Clear filter - reset to default view
    booksStore.books = []
  }
}

const handleClickOutside = () => {
  if (showGenreDropdown.value) {
    showGenreDropdown.value = false
  }
}

onMounted(async () => {
  await booksStore.fetchGenres()
  await userBooksStore.fetchBooks()

  // Fetch all discovery endpoints in parallel
  const [popular, recent, trending] = await Promise.all([
    booksStore.fetchPopularBooks(),
    booksStore.fetchRecentBooks(),
    booksStore.fetchTrendingBooks()
  ])

  if (popular.success) popularBooks.value = popular.data
  if (recent.success) recentBooks.value = recent.data
  if (trending.success) trendingBooks.value = trending.data

  // Mark initial load as complete
  isInitialLoad.value = false

  // Add click outside listener
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const openAddDialog = (book) => {
  selectedBook.value = book
  isAddDialogOpen.value = true
}

const addToLibrary = async () => {
  if (!selectedBook.value) return

  console.log('Adding book to library:', {
    book: selectedBook.value.id,
    status: addBookStatus.value
  })

  const result = await userBooksStore.addBook({
    book: selectedBook.value.id,
    status: addBookStatus.value,
  })

  console.log('Add book result:', result)

  if (result.success) {
    isAddDialogOpen.value = false
    selectedBook.value = null
    // Refresh books list to show the newly added book
    await userBooksStore.fetchBooks()
  } else {
    console.error('Failed to add book:', result.error)
    alert(`Failed to add book: ${result.error || 'Unknown error'}`)
  }
}

const viewBook = (book) => {
  router.push(`/books/${book.id}`)
}

const getAuthorsString = (book) => {
  return book.authors?.map(a => a.name).join(', ') || 'Unknown Author'
}

const deleteBook = async (book) => {
  if (!confirm(`Are you sure you want to delete "${book.title}"? This action cannot be undone.`)) {
    return
  }

  const result = await booksStore.deleteBook(book.id)

  if (result.success) {
    // Refresh the lists
    const popular = await booksStore.fetchPopularBooks()
    if (popular.success) popularBooks.value = popular.data

    const recent = await booksStore.fetchRecentBooks()
    if (recent.success) recentBooks.value = recent.data
  } else {
    alert('Failed to delete book: ' + JSON.stringify(result.error))
  }
}

const isBookInLibrary = (book) => {
  return userBooksStore.books.some(ub => ub.book?.id === book.id)
}
</script>

<template>
  <div class="relative z-10 pb-20">
    <!-- Mobile Header (Sticky - minimal) -->
    <div class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 safe-area-top">
      <div class="flex items-center justify-between px-4 py-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <BookOpen :size="18" class="text-indigo-400" />
          </div>
          <div>
            <h1 class="text-base font-bold text-white">Browse Books</h1>
            <p class="text-xs text-slate-500">Discover new reads</p>
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
      <!-- Active Filter Indicator -->
      <div v-if="selectedGenre || searchQuery" class="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex-shrink-0">Active:</span>
        <button
          v-if="searchQuery"
          @click="searchQuery = ''; handleSearch('')"
          class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-700/50 border border-slate-600 text-slate-300 text-xs font-bold"
        >
          <Search :size="12" />
          "{{ searchQuery.length > 12 ? searchQuery.slice(0, 12) + '...' : searchQuery }}"
          <X :size="12" />
        </button>
        <button
          v-if="selectedGenre"
          @click="filterByGenre(null)"
          class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 text-xs font-bold"
        >
          {{ selectedGenreLabel }}
          <X :size="12" />
        </button>
      </div>
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
                <h2 class="text-lg font-bold text-white">Search & Filter</h2>
                <button
                  @click="showMobileFilters = false"
                  class="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400"
                >
                  <X :size="20" />
                </button>
              </div>
            </div>

            <div class="p-4 space-y-6">
              <!-- Search -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Search</h3>
                <div class="relative">
                  <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
                  <input
                    type="text"
                    v-model="searchQuery"
                    @input="handleSearchInput(searchQuery)"
                    @change="handleSearch(searchQuery)"
                    placeholder="Title, author, ISBN..."
                    class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <!-- Genre Filter -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Genre</h3>
                <div class="space-y-2">
                  <button
                    @click="filterByGenre(null); showMobileFilters = false"
                    :class="!selectedGenre ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <span class="font-bold">All Genres</span>
                    <Check v-if="!selectedGenre" :size="16" class="ml-auto" />
                  </button>
                  <button
                    v-for="genre in (booksStore.genres || []).filter(g => g?.id)"
                    :key="genre.id"
                    @click="filterByGenre(genre.id); showMobileFilters = false"
                    :class="selectedGenre === genre.id ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <span class="font-bold">{{ genre.name }}</span>
                    <Check v-if="selectedGenre === genre.id" :size="16" class="ml-auto" />
                  </button>
                </div>
              </div>

              <!-- Clear Filters -->
              <button
                v-if="selectedGenre || searchQuery"
                @click="filterByGenre(null); searchQuery = ''; handleSearch(''); showMobileFilters = false"
                class="w-full px-4 py-3 rounded-xl border border-red-500/30 text-red-400 font-bold text-sm hover:bg-red-500/10 transition-all"
              >
                Clear All Filters
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Header Section (Desktop) -->
    <div class="hidden lg:block w-full max-w-7xl mx-auto pt-12 pb-8 px-6">
      <PageHeader
        title="Browse Books"
        subtitle="Discover your next great read from the curated collection"
        accentWord="Browse"
      />

      <!-- Genre Filter -->
      <div class="mb-6 flex items-center gap-3">
        <span class="text-sm font-medium text-slate-400">Filter by Genre:</span>
        <button
          @click.stop="showGenreDropdown = !showGenreDropdown"
          class="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-all text-sm font-bold relative bg-slate-900/80"
        >
          <Filter :size="16" />
          {{ selectedGenreLabel }}
          <ChevronDown :size="14" :class="{ 'rotate-180': showGenreDropdown }" class="transition-transform" />

          <!-- Dropdown -->
          <div
            v-if="showGenreDropdown"
            @click.stop
            class="absolute left-0 top-12 w-64 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl z-[100]"
          >
            <div class="p-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Select Genre</h3>
              <div class="space-y-2">
                <button
                  @click="filterByGenre(null)"
                  :class="[
                    'w-full flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                    !selectedGenre
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:bg-slate-800 border border-transparent'
                  ]"
                >
                  All Genres
                  <Check
                    v-if="!selectedGenre"
                    :size="14"
                    class="ml-auto text-indigo-400"
                  />
                </button>
                <button
                  v-for="genre in (booksStore.genres || []).filter(g => g?.id)"
                  :key="genre.id"
                  @click="filterByGenre(genre.id)"
                  :class="[
                    'w-full flex items-center gap-3 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                    selectedGenre === genre.id
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:bg-slate-800 border border-transparent'
                  ]"
                >
                  {{ genre.name }}
                  <Check
                    v-if="selectedGenre === genre.id"
                    :size="14"
                    class="ml-auto text-indigo-400"
                  />
                </button>
              </div>
            </div>
          </div>
        </button>
      </div>

      <!-- Search Input -->
      <SearchBar
        v-model="searchQuery"
        placeholder="Search by title, author, or ISBN..."
        @update:modelValue="handleSearchInput"
        @search="handleSearch"
      />
    </div>

    <!-- Content Section -->
    <div class="max-w-7xl mx-auto px-6 space-y-16">
      <!-- Trending Books Section -->
      <section v-if="!searchQuery && !selectedGenre && trendingBooks.length > 0">
        <div class="flex items-center gap-2 mb-6">
          <TrendingUp :size="18" class="text-indigo-400 flex-shrink-0 mt-0.5" />
          <SectionHeader title="Trending This Week" />
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div
            v-for="book in trendingBooks"
            :key="book.id"
            class="group cursor-pointer"
          >
            <div @click="viewBook(book)" class="relative aspect-[2/3] bg-slate-900 rounded-xl overflow-hidden mb-4 shadow-2xl border border-slate-700/50 group-hover:border-indigo-500/50 transition-all duration-300">
              <!-- Cover Image or Placeholder -->
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />

              <!-- Beautiful placeholder for missing covers -->
              <div v-else class="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
                <div class="w-20 h-20 rounded-full bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center mb-4">
                  <BookOpen :size="32" class="text-indigo-500/40" />
                </div>
                <h3 class="text-slate-400 text-sm font-bold text-center line-clamp-3 leading-tight">
                  {{ book.title }}
                </h3>
                <p class="text-slate-600 text-xs mt-2 text-center">
                  No cover available
                </p>
              </div>

              <!-- Hover Overlay -->
              <div class="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <button class="px-5 py-2 glass rounded-full text-white text-sm font-medium hover:bg-white/20 transition-colors">
                  View Details
                </button>
              </div>

              <!-- Delete Button -->
              <button
                @click.stop="deleteBook(book)"
                class="absolute top-2 right-2 p-2 rounded-lg bg-red-500/80 backdrop-blur-sm border border-red-400/50 text-white opacity-0 group-hover:opacity-100 hover:bg-red-600 transition-all duration-300 shadow-lg z-10"
                title="Delete book"
              >
                <Trash2 :size="16" />
              </button>
            </div>
            <h3 class="font-semibold text-sm line-clamp-2 text-white mb-1 group-hover:text-indigo-400 transition-colors">
              {{ book.title }}
            </h3>
            <p class="text-xs text-slate-400 line-clamp-1 mb-3">
              {{ getAuthorsString(book) }}
            </p>
            <button
              v-if="!isBookInLibrary(book)"
              @click.stop="openAddDialog(book)"
              class="w-full px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold hover:bg-indigo-500 hover:text-white transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Plus :size="14" />
              Add to Library
            </button>
            <button
              v-else
              disabled
              class="w-full px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center justify-center gap-2 cursor-default"
            >
              <Check :size="14" />
              In Library
            </button>
          </div>
        </div>
      </section>

      <!-- All Books Section -->
      <section v-if="!searchQuery && !selectedGenre && allBooksExceptTrending.length > 0">
        <div class="flex items-center gap-2 mb-6">
          <BookOpen :size="18" class="text-indigo-400 flex-shrink-0 mt-0.5" />
          <SectionHeader title="All Books" />
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div
            v-for="book in allBooksExceptTrending"
            :key="book.id"
            class="group cursor-pointer"
          >
            <div @click="viewBook(book)" class="relative aspect-[2/3] bg-slate-900 rounded-xl overflow-hidden mb-4 shadow-2xl border border-slate-700/50 group-hover:border-indigo-500/50 transition-all duration-300">
              <!-- Cover Image or Placeholder -->
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />

              <!-- Beautiful placeholder for missing covers -->
              <div v-else class="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
                <div class="w-20 h-20 rounded-full bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center mb-4">
                  <BookOpen :size="32" class="text-indigo-500/40" />
                </div>
                <h3 class="text-slate-400 text-sm font-bold text-center line-clamp-3 leading-tight">
                  {{ book.title }}
                </h3>
                <p class="text-slate-600 text-xs mt-2 text-center">
                  No cover available
                </p>
              </div>

              <!-- Hover Overlay -->
              <div class="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <button class="px-5 py-2 glass rounded-full text-white text-sm font-medium hover:bg-white/20 transition-colors">
                  View Details
                </button>
              </div>

              <!-- Delete Button -->
              <button
                @click.stop="deleteBook(book)"
                class="absolute top-2 right-2 p-2 rounded-lg bg-red-500/80 backdrop-blur-sm border border-red-400/50 text-white opacity-0 group-hover:opacity-100 hover:bg-red-600 transition-all duration-300 shadow-lg z-10"
                title="Delete book"
              >
                <Trash2 :size="16" />
              </button>
            </div>
            <h3 class="font-semibold text-sm line-clamp-2 text-white mb-1 group-hover:text-indigo-400 transition-colors">
              {{ book.title }}
            </h3>
            <p class="text-xs text-slate-400 line-clamp-1 mb-3">
              {{ getAuthorsString(book) }}
            </p>
            <button
              v-if="!isBookInLibrary(book)"
              @click.stop="openAddDialog(book)"
              class="w-full px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold hover:bg-indigo-500 hover:text-white transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Plus :size="14" />
              Add to Library
            </button>
            <button
              v-else
              disabled
              class="w-full px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center justify-center gap-2 cursor-default"
            >
              <Check :size="14" />
              In Library
            </button>
          </div>
        </div>
      </section>

      <!-- Loading Skeletons for Initial Load, Search, or Filter -->
      <section v-if="(booksStore.loading || isSearching || isInitialLoad)">
        <SectionHeader title="Loading..." class="mb-6" />
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12">
          <div v-for="n in 10" :key="n" class="space-y-3">
            <Skeleton class="w-full aspect-[2/3] rounded-xl" />
            <Skeleton class="h-4 w-3/4" />
            <Skeleton class="h-3 w-1/2" />
          </div>
        </div>
      </section>

      <!-- Search Results -->
      <section v-else-if="(searchQuery || selectedGenre) && booksStore.books.length > 0">
        <SectionHeader title="Search Results" class="mb-6" />

        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-x-8 gap-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div
            v-for="book in booksStore.books"
            :key="book.id"
            class="group cursor-pointer"
          >
            <div @click="viewBook(book)" class="relative aspect-[2/3] bg-slate-900 rounded-xl overflow-hidden mb-4 shadow-2xl border border-slate-700/50 group-hover:border-indigo-500/50 transition-all duration-300">
              <!-- Cover Image or Placeholder -->
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />

              <!-- Beautiful placeholder for missing covers -->
              <div v-else class="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
                <div class="w-20 h-20 rounded-full bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center mb-4">
                  <BookOpen :size="32" class="text-indigo-500/40" />
                </div>
                <h3 class="text-slate-400 text-sm font-bold text-center line-clamp-3 leading-tight">
                  {{ book.title }}
                </h3>
                <p class="text-slate-600 text-xs mt-2 text-center">
                  No cover available
                </p>
              </div>

              <!-- Hover Overlay -->
              <div class="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                <button class="px-5 py-2 glass rounded-full text-white text-sm font-medium hover:bg-white/20 transition-colors">
                  View Details
                </button>
              </div>

              <!-- Delete Button -->
              <button
                @click.stop="deleteBook(book)"
                class="absolute top-2 right-2 p-2 rounded-lg bg-red-500/80 backdrop-blur-sm border border-red-400/50 text-white opacity-0 group-hover:opacity-100 hover:bg-red-600 transition-all duration-300 shadow-lg z-10"
                title="Delete book"
              >
                <Trash2 :size="16" />
              </button>
            </div>
            <h3 class="font-semibold text-sm line-clamp-2 text-white mb-1 group-hover:text-indigo-400 transition-colors">
              {{ book.title }}
            </h3>
            <p class="text-xs text-slate-400 line-clamp-1 mb-3">
              {{ getAuthorsString(book) }}
            </p>
            <button
              v-if="!isBookInLibrary(book)"
              @click.stop="openAddDialog(book)"
              class="w-full px-4 py-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold hover:bg-indigo-500 hover:text-white transition-all duration-300 flex items-center justify-center gap-2"
            >
              <Plus :size="14" />
              Add to Library
            </button>
            <button
              v-else
              disabled
              class="w-full px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold flex items-center justify-center gap-2 cursor-default"
            >
              <Check :size="14" />
              In Library
            </button>
          </div>
        </div>
      </section>

      <!-- Empty State for Search/Filter with no results -->
      <EmptyState
        v-else-if="(searchQuery || selectedGenre) && booksStore.books.length === 0"
        :icon="BookOpen"
        title="No books found"
        description="Try adjusting your search or filter criteria"
      />

      <!-- Empty State for no books at all -->
      <EmptyState
        v-else-if="!searchQuery && !selectedGenre && trendingBooks.length === 0 && allBooksExceptTrending.length === 0"
        :icon="BookOpen"
        title="No books available"
        description="Check back later for new additions to our collection"
      />
    </div>

    <!-- Add to Library Dialog -->
    <Dialog v-model:open="isAddDialogOpen">
      <DialogContent class="glass border-slate-700">
        <DialogHeader>
          <DialogTitle class="text-xl">Add to Library</DialogTitle>
        </DialogHeader>
        <div v-if="selectedBook" class="space-y-4">
          <div class="flex gap-4">
            <div class="w-24 h-36 bg-slate-900 rounded-lg overflow-hidden flex-shrink-0 border border-slate-700/50">
              <img
                v-if="selectedBook.cover_image"
                :src="selectedBook.cover_image"
                :alt="selectedBook.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex flex-col items-center justify-center p-3 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
                <div class="w-10 h-10 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-2">
                  <BookOpen :size="16" class="text-indigo-500/40" />
                </div>
                <p class="text-slate-600 text-[10px] text-center">
                  No cover
                </p>
              </div>
            </div>
            <div>
              <h3 class="font-semibold mb-1 text-white">{{ selectedBook.title }}</h3>
              <p class="text-sm text-slate-400">
                {{ getAuthorsString(selectedBook) }}
              </p>
            </div>
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium text-slate-300">Status</label>
            <select
              v-model="addBookStatus"
              class="w-full px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-700 text-white text-sm font-medium focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="want_to_read">Want to Read</option>
              <option value="currently_reading">Currently Reading</option>
              <option value="read">Read</option>
            </select>
          </div>

          <div class="flex justify-end gap-2 pt-4">
            <button
              @click="isAddDialogOpen = false"
              class="px-5 py-3 rounded-xl border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-colors"
            >
              Cancel
            </button>
            <button
              @click="addToLibrary"
              class="px-5 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors"
            >
              Add to Library
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
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
