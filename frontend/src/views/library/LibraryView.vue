<script setup>
import { ref, computed, onMounted, watch, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useAuthStore } from '@/stores/authStore'
import { useChallengesStore } from '@/stores/challengesStore'
import { useToast } from '@/composables/useToast'
import YearlyChallengeWidget from '@/components/YearlyChallengeWidget.vue'
import YearlyChallengeModal from '@/components/YearlyChallengeModal.vue'
import ReadingCircleWidget from '@/components/social/ReadingCircleWidget.vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { booksAPI } from '@/services/api'
import {
  BookOpen, Heart, Plus, Search, TrendingUp, Zap,
  CheckCircle, Bookmark, BrainCircuit, Lightbulb,
  Quote, ArrowUpRight, Upload, FileUp
} from 'lucide-vue-next'

const router = useRouter()
const booksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const authStore = useAuthStore()
const challengesStore = useChallengesStore()
const { addToast } = useToast()

const searchQuery = ref('')
const selectedTab = ref('all')
const loading = ref(true)
const isQuoteExpanded = ref(false)
const showChallengeModal = ref(false)
const editingChallenge = ref(null)

// Import state
const showImportDialog = ref(false)
const importing = ref(false)
const importProgress = ref(null)
const selectedFile = ref(null)
const fileInputRef = ref(null)

// Pagination state
const itemsPerPage = 24 // Show 24 books per load (4 rows of 6)
const currentPage = ref(1)

// Fetch books on mount
onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      booksStore.fetchBooks(),
      quotesStore.fetchQuotes()
    ])
  } catch (error) {
    console.error('Error loading library data:', error)
  } finally {
    loading.value = false
  }
})

// Reset pagination when search query changes
watch(searchQuery, () => {
  resetPagination()
})

// Books to display based on selected tab
const displayedBooks = computed(() => {
  if (selectedTab.value === 'all') {
    return booksStore.filteredBooks
  } else if (selectedTab.value === 'favorites') {
    booksStore.setFilter('favorite', true)
    return booksStore.filteredBooks
  } else {
    booksStore.setFilter('favorite', null)
    booksStore.setFilter('status', selectedTab.value)
    return booksStore.filteredBooks
  }
})

// Handle search
const handleSearch = (value) => {
  booksStore.setFilter('search', value)
}

// Tab change
const handleTabChange = (value) => {
  selectedTab.value = value
  resetPagination() // Reset pagination when changing tabs
  booksStore.resetFilters()
  if (value === 'favorites') {
    booksStore.setFilter('favorite', true)
  } else if (value !== 'all') {
    booksStore.setFilter('status', value)
  }
}

// Book actions
const handleViewBook = (book) => {
  router.push(`/books/${book.book.id}`)
}

const handleEditBook = (book) => {
  // TODO: Open edit dialog
  console.log('Edit book:', book)
}

const handleDeleteBook = async (book) => {
  if (confirm(`Remove "${book.book.title}" from your library?`)) {
    const result = await booksStore.removeBook(book.id)
    if (result.success) {
      console.log('Book removed')
    }
  }
}

const handleToggleFavorite = async (book) => {
  await booksStore.updateBook(book.id, {
    is_favorite: !book.is_favorite,
  })
}

// Goodreads Import functions
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.name.endsWith('.csv')) {
    selectedFile.value = file
  } else {
    addToast({
      title: 'Invalid File',
      description: 'Please select a CSV file',
      variant: 'destructive'
    })
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    addToast({
      title: 'No File Selected',
      description: 'Please select a Goodreads CSV file',
      variant: 'destructive'
    })
    return
  }

  importing.value = true
  importProgress.value = { current: 0, total: 0, status: 'Uploading...' }

  try {
    const response = await booksAPI.importGoodreadsCSV(selectedFile.value)

    importProgress.value = {
      current: response.data.imported,
      total: response.data.imported + response.data.skipped,
      status: 'Completed'
    }

    addToast({
      title: 'Import Successful!',
      description: `Imported ${response.data.imported} books, ${response.data.created_books} new books created`,
      variant: 'default'
    })

    // Refresh library
    await booksStore.fetchBooks()

    // Close dialog after a delay
    setTimeout(() => {
      showImportDialog.value = false
      selectedFile.value = null
      importProgress.value = null
    }, 2000)

  } catch (error) {
    console.error('Import error:', error)
    addToast({
      title: 'Import Failed',
      description: error.response?.data?.error || 'Failed to import CSV file',
      variant: 'destructive'
    })
    importProgress.value = null
  } finally {
    importing.value = false
  }
}

const openImportDialog = () => {
  showImportDialog.value = true
  selectedFile.value = null
  importProgress.value = null
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

// Stats
const stats = computed(() => booksStore.stats)

// User name
const userName = computed(() => authStore.user?.username || 'Reader')

// Currently reading books
const currentlyReading = computed(() => {
  return booksStore.books
    .filter(b => b.status === 'currently_reading')
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
})

// Last read books
const lastReadBooks = computed(() => {
  return booksStore.books
    .filter(b => b.status === 'read')
    .sort((a, b) => {
      // Sort by finished_at if both have it, otherwise by updated_at
      const dateA = b.finished_at ? new Date(b.finished_at) : new Date(b.updated_at)
      const dateB = a.finished_at ? new Date(a.finished_at) : new Date(a.updated_at)
      return dateA - dateB
    })
})

// Active expeditions - combine currently reading and last read to always show 3 cards
const activeExpeditions = computed(() => {
  const expeditions = []
  const maxCards = 3

  // Add currently reading books (max 2)
  const reading = currentlyReading.value.slice(0, 2)
  expeditions.push(...reading)

  // Fill remaining slots with last read books
  const remainingSlots = maxCards - expeditions.length
  if (remainingSlots > 0 && lastReadBooks.value.length > 0) {
    const lastReads = lastReadBooks.value.slice(0, remainingSlots).map(book => ({
      ...book,
      isLastRead: true
    }))
    expeditions.push(...lastReads)
  }

  return expeditions
})

// Daily quote - generates once per day without repeating
const dailyQuote = computed(() => {
  const allQuotes = quotesStore.quotes
  if (allQuotes.length === 0) return null

  // Get today's date string (YYYY-MM-DD)
  const today = new Date().toISOString().split('T')[0]

  // Get shown quotes history from localStorage
  const shownQuotesKey = 'dailyQuotesHistory'
  const lastDateKey = 'lastQuoteDate'
  const storedDate = localStorage.getItem(lastDateKey)

  let shownQuoteIds = []
  try {
    const stored = localStorage.getItem(shownQuotesKey)
    shownQuoteIds = stored ? JSON.parse(stored) : []
  } catch (e) {
    shownQuoteIds = []
  }

  // If it's a new day, potentially reset history if we've shown all quotes
  if (storedDate !== today) {
    // Get available quotes that haven't been shown
    const availableQuotes = allQuotes.filter(q => !shownQuoteIds.includes(q.id))

    // If we've shown all quotes, reset the history
    if (availableQuotes.length === 0) {
      shownQuoteIds = []
      localStorage.setItem(shownQuotesKey, JSON.stringify([]))
    }

    // Pick a new quote for today
    const quotesToChooseFrom = availableQuotes.length > 0 ? availableQuotes : allQuotes
    const randomIndex = Math.floor(Math.random() * quotesToChooseFrom.length)
    const selectedQuote = quotesToChooseFrom[randomIndex]

    // Save the selected quote ID and today's date
    shownQuoteIds.push(selectedQuote.id)
    localStorage.setItem(shownQuotesKey, JSON.stringify(shownQuoteIds))
    localStorage.setItem(lastDateKey, today)
    localStorage.setItem('todayQuoteId', selectedQuote.id.toString())

    return selectedQuote
  }

  // Same day - return the quote selected for today
  const todayQuoteId = localStorage.getItem('todayQuoteId')
  if (todayQuoteId) {
    const quote = allQuotes.find(q => q.id.toString() === todayQuoteId)
    if (quote) return quote
  }

  // Fallback
  return allQuotes[0]
})

// Check if quote is longer than 600 characters
const isQuoteLong = computed(() => {
  return dailyQuote.value && dailyQuote.value.text && dailyQuote.value.text.length > 600
})

// Filtered library with proper date sorting
const filteredLibrary = computed(() => {
  let books = booksStore.books

  // Filter by tab
  if (selectedTab.value !== 'all') {
    if (selectedTab.value === 'favorites') {
      books = books.filter(b => b.is_favorite)
    } else {
      books = books.filter(b => b.status === selectedTab.value)
    }
  }

  // Filter by search
  if (searchQuery.value) {
    const search = searchQuery.value.toLowerCase()
    books = books.filter(b =>
      b.book?.title?.toLowerCase().includes(search) ||
      b.book?.authors?.some(a => a.name.toLowerCase().includes(search))
    )
  }

  // Sort by relevant date (NEWEST FIRST - most recent at top)
  books = [...books].sort((a, b) => {
    // Helper function to get the most relevant date for a book based on its status
    const getRelevantDate = (book) => {
      if (book.status === 'read') {
        // For read books: finished_at is most important
        return book.finished_at ? new Date(book.finished_at) : new Date(book.updated_at || book.created_at)
      } else if (book.status === 'currently_reading') {
        // For currently reading: started_at is most important
        return book.started_at ? new Date(book.started_at) : new Date(book.updated_at || book.created_at)
      } else if (book.status === 'want_to_read') {
        // For want to read: when added to library (created_at)
        return new Date(book.created_at || book.updated_at)
      } else {
        // Fallback
        return new Date(book.updated_at || book.created_at)
      }
    }

    const dateA = getRelevantDate(a)
    const dateB = getRelevantDate(b)

    // Return DESCENDING order (newest first) - newer dates are LARGER numbers
    return dateB.getTime() - dateA.getTime()
  })

  return books
})

// Paginated library - show only items up to current page
const paginatedLibrary = computed(() => {
  const maxItems = currentPage.value * itemsPerPage
  return filteredLibrary.value.slice(0, maxItems)
})

// Check if there are more items to load
const hasMoreItems = computed(() => {
  return paginatedLibrary.value.length < filteredLibrary.value.length
})

// Load more function
const loadMore = () => {
  currentPage.value++
}

// Reset pagination when filters change
const resetPagination = () => {
  currentPage.value = 1
}

// Infinite scroll handler
const handleScroll = () => {
  const scrollThreshold = 300 // pixels from bottom
  const scrollPosition = window.innerHeight + window.scrollY
  const pageHeight = document.documentElement.scrollHeight

  if (pageHeight - scrollPosition < scrollThreshold && hasMoreItems.value && !loading.value) {
    loadMore()
  }
}

// Add scroll listener after books are loaded
watch(() => booksStore.books, () => {
  nextTick(() => {
    window.addEventListener('scroll', handleScroll, { passive: true })
  })
}, { once: true })

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})

// Helper functions
const handleBookClick = (userBook, event) => {
  // Support middle-click to open in new tab
  if (event && (event.button === 1 || event.ctrlKey || event.metaKey)) {
    const route = router.resolve(`/books/${userBook.book.id}`)
    window.open(route.href, '_blank')
  } else {
    router.push(`/books/${userBook.book.id}`)
  }
}

const getProgress = (userBook) => {
  if (!userBook.current_page || !userBook.book?.pages) return 0
  return Math.round((userBook.current_page / userBook.book.pages) * 100)
}

const getCoverUrl = (book) => {
  if (!book) return null
  return book.cover_image || null
}

// Year stats
const finishedThisYear = computed(() => {
  const currentYear = new Date().getFullYear()
  return booksStore.books.filter(b => {
    if (b.status !== 'read') return false

    // If has finished_at, check if it's this year
    if (b.finished_at) {
      return new Date(b.finished_at).getFullYear() === currentYear
    }

    // Fallback: if no finished_at but status is 'read', check updated_at or created_at
    const fallbackDate = b.updated_at || b.created_at
    if (fallbackDate) {
      return new Date(fallbackDate).getFullYear() === currentYear
    }

    return false
  }).length
})

const yearGoal = 50
const yearProgress = computed(() => Math.round((finishedThisYear.value / yearGoal) * 100))

// Get badge information for status
const getStatusBadge = (status) => {
  const badges = {
    'currently_reading': {
      text: 'Reading',
      class: 'bg-indigo-500 text-white'
    },
    'read': {
      text: 'Finished',
      class: 'bg-emerald-500/90 text-white'
    },
    'want_to_read': {
      text: 'Want to Read',
      class: 'bg-sky-500/90 text-white'
    },
    'abandoned': {
      text: 'Abandoned',
      class: 'bg-slate-600 text-slate-200'
    }
  }
  return badges[status] || null
}

// Challenge handlers
const handleEditChallenge = (challenge) => {
  editingChallenge.value = challenge
  showChallengeModal.value = true
}

const handleCreateChallenge = () => {
  editingChallenge.value = null
  showChallengeModal.value = true
}

const handleCloseChallengeModal = () => {
  showChallengeModal.value = false
  editingChallenge.value = null
}

const handleSaveChallenge = async (challengeData) => {
  let result

  if (editingChallenge.value) {
    // Update existing challenge
    result = await challengesStore.updateChallenge(editingChallenge.value.id, challengeData)
  } else {
    // Create new challenge
    result = await challengesStore.createChallenge(challengeData)
  }

  if (result.success) {
    addToast(
      editingChallenge.value ? 'Challenge updated successfully!' : 'Challenge created successfully!',
      'success'
    )
    showChallengeModal.value = false
    editingChallenge.value = null
  } else {
    addToast(result.error || 'Failed to save challenge', 'error')
  }
}
</script>

<template>
  <!-- Loading State -->
  <div v-if="loading" class="max-w-7xl mx-auto px-6 py-20 flex flex-col items-center justify-center space-y-4">
    <div class="w-12 h-12 border-4 border-slate-800 border-t-indigo-500 rounded-full animate-spin" />
    <p class="text-slate-500 font-bold uppercase tracking-widest text-xs">Accessing Command Center...</p>
  </div>

  <!-- Main Content -->
  <div v-else class="max-w-7xl mx-auto px-6 py-12">

    <!-- HERO SECTION -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-16 items-start">

      <!-- Welcome Briefing -->
      <div class="lg:col-span-7 space-y-4 sm:space-y-8">
        <div class="flex items-center gap-2 text-indigo-400 font-bold text-page-meta uppercase tracking-[0.3em] sm:tracking-[0.4em]">
          <BrainCircuit :size="12" class="sm:w-3.5 sm:h-3.5 fill-current" />
          Reading OS / V2.5
        </div>
        <h1 class="text-page-heading font-black text-white tracking-tighter">
          Hello, <span class="text-indigo-500">{{ userName }}</span>.
        </h1>
        <p class="text-page-subtitle text-slate-400 leading-relaxed max-w-xl -mt-2 sm:mt-0">
          Your personal archive of knowledge and wonder. Revisit your insights, track your growth, and find your next great exploration.
        </p>

        <div class="flex flex-wrap items-center gap-4 pt-2">
          <div class="px-6 py-3.5 rounded-2xl glass border-slate-800 flex items-center gap-4">
            <div class="flex -space-x-2">
              <img
                v-for="(book, i) in booksStore.books.slice(0, 3)"
                :key="i"
                :src="getCoverUrl(book.book)"
                class="w-6 h-6 rounded-full border-2 border-slate-950 object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
            </div>
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{{ stats.total }} entries in vault</span>
          </div>
          <button
            @click="router.push('/library/shelf')"
            class="px-6 py-3.5 rounded-2xl glass border-indigo-500/30 text-indigo-400 font-bold hover:bg-indigo-500/10 active:scale-95 transition-all flex items-center gap-2"
          >
            <BookOpen :size="20" />
            My Shelf
          </button>
          <button
            @click="router.push('/import')"
            class="px-6 py-3.5 rounded-2xl bg-indigo-500 text-white font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center gap-2"
          >
            <Plus :size="20" />
            Import New Book
          </button>
        </div>
      </div>

      <!-- Wisdom Spotlight -->
      <div class="lg:col-span-5">
        <div v-if="dailyQuote" class="relative p-5 sm:p-7 rounded-[2rem] glass border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/5 group overflow-hidden shadow-2xl">
          <div class="absolute top-0 right-0 p-6 opacity-[0.03] text-indigo-400 group-hover:scale-110 transition-transform duration-1000">
            <Quote :size="80" />
          </div>
          <div class="relative z-10">
            <span class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black uppercase text-indigo-400 mb-5 tracking-widest">
              <Lightbulb :size="12" /> Musing of the Day
            </span>
            <div class="mb-5">
              <p class="text-quote font-serif italic text-slate-200 leading-relaxed">
                "{{ isQuoteExpanded || !isQuoteLong ? dailyQuote.text : dailyQuote.text.substring(0, 600) + '...' }}"
              </p>
              <button
                v-if="isQuoteLong"
                @click="isQuoteExpanded = !isQuoteExpanded"
                class="text-xs text-indigo-400 hover:text-indigo-300 transition-colors mt-2 font-medium"
              >
                {{ isQuoteExpanded ? 'show less' : 'more...' }}
              </button>
            </div>
            <div>
              <p class="text-indigo-400 font-bold text-xs">— {{ dailyQuote.book_author }}</p>
              <p class="text-slate-500 text-[10px] font-medium uppercase tracking-wider">{{ dailyQuote.book_title }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ACTIVE EXPEDITIONS -->
    <div v-if="activeExpeditions.length > 0" class="mb-16">
      <div class="flex items-center justify-between mb-8">
        <h2 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em] flex items-center gap-3">
          <BookOpen :size="14" class="text-indigo-500" />
          Active Expeditions
        </h2>
        <div class="h-px flex-1 bg-slate-900 mx-6" />
        <span class="text-[10px] font-bold text-slate-600 uppercase tracking-widest">{{ currentlyReading.length }} currently</span>
      </div>

      <div class="grid md:grid-cols-3 gap-5">
        <router-link
          v-for="expedition in activeExpeditions"
          :key="expedition.id"
          :to="`/books/${expedition.book.id}`"
          class="group relative p-5 rounded-2xl glass border-slate-800 hover:border-indigo-500/30 transition-all duration-300 cursor-pointer overflow-hidden"
        >
          <!-- Badge: Currently Reading or Last Read -->
          <div class="absolute top-3 right-3 z-10">
            <span
              v-if="expedition.isLastRead"
              class="px-2 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[9px] font-black uppercase tracking-wider"
            >
              Last Read
            </span>
            <span
              v-else
              class="px-2 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-[9px] font-black uppercase tracking-wider"
            >
              Reading
            </span>
          </div>

          <div class="flex gap-4">
            <div class="shrink-0 w-16 h-24 rounded-xl overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-lg flex items-center justify-center">
              <img
                v-if="getCoverUrl(expedition.book)"
                :src="getCoverUrl(expedition.book)"
                :alt="expedition.book?.title"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
              <BookOpen v-if="!getCoverUrl(expedition.book)" :size="24" class="text-slate-600" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-bold text-white text-sm mb-1 line-clamp-2 group-hover:text-indigo-400 transition-colors">
                {{ expedition.book?.title }}
              </h3>
              <p class="text-slate-500 text-[11px] mb-3 line-clamp-1">
                {{ expedition.book?.authors?.map(a => a.name).join(', ') }}
              </p>

              <!-- Progress bar for currently reading -->
              <div v-if="!expedition.isLastRead" class="space-y-2">
                <div class="flex items-center justify-between text-xs">
                  <span class="text-slate-400">{{ getProgress(expedition) }}% complete</span>
                  <span class="text-slate-600">{{ expedition.current_page || 0 }} / {{ expedition.book?.pages || 0 }}</span>
                </div>
                <div class="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    :style="{ width: getProgress(expedition) + '%' }"
                    class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                  />
                </div>
              </div>

              <!-- Rating and Review link for last read -->
              <div v-else class="space-y-2">
                <div class="flex items-center gap-2">
                  <div v-if="expedition.rating" class="flex items-center gap-1">
                    <Heart :size="12" class="text-yellow-400 fill-current" />
                    <span class="text-yellow-400 font-bold text-sm">{{ expedition.rating }}/10</span>
                  </div>
                  <span v-else class="text-slate-600 text-xs">No rating</span>
                </div>
                <p class="text-xs text-slate-500">
                  <span class="text-emerald-400 font-bold">Completed</span>
                  <template v-if="expedition.finished_at">
                    <span class="mx-1">•</span>
                    {{ new Date(expedition.finished_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}
                  </template>
                </p>
                <button
                  v-if="expedition.review"
                  @click.stop="router.push(`/books/${expedition.book.id}/review-view`)"
                  class="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
                >
                  Read Review <ArrowUpRight :size="10" />
                </button>
              </div>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- MAIN GRID: LEFT CONTENT + RIGHT SIDEBAR -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">

      <!-- LEFT COLUMN: SEARCH, TABS & BOOKS -->
      <div class="lg:col-span-8 space-y-8 pt-6 border-t border-slate-900">

        <!-- Search Bar with Import Button -->
        <div class="flex items-center gap-4">
          <div class="relative group flex-1">
            <div class="absolute inset-0 bg-indigo-500/5 blur-2xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
            <Search :size="24" class="absolute left-6 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-500 transition-colors" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Query your personal archive by title, author, or keyword..."
              class="bg-slate-900/40 border border-slate-800 rounded-3xl pl-16 pr-8 py-6 text-lg text-white placeholder-slate-600 focus:border-indigo-500/40 focus:bg-slate-900 outline-none transition-all w-full shadow-lg"
            />
          </div>

          <!-- Import from Goodreads Button -->
          <button
            @click="openImportDialog"
            class="px-6 py-6 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-sm transition-all duration-300 shadow-lg shadow-emerald-500/20 hover:shadow-xl hover:shadow-emerald-500/30 flex items-center gap-2 shrink-0"
          >
            <Upload :size="18" />
            <span class="hidden sm:inline">Import from Goodreads</span>
          </button>
        </div>

        <!-- Tabs -->
        <div class="flex flex-wrap items-center gap-1.5 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 w-fit">
          <button
            @click="handleTabChange('all')"
            :class="selectedTab === 'all' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white bg-transparent'"
            class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-2"
          >
            <BookOpen :size="12" />
            All Vault
          </button>
          <button
            @click="handleTabChange('currently_reading')"
            :class="selectedTab === 'currently_reading' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white bg-transparent'"
            class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-2"
          >
            <Zap :size="12" />
            Reading
          </button>
          <button
            @click="handleTabChange('read')"
            :class="selectedTab === 'read' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white bg-transparent'"
            class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-2"
          >
            <CheckCircle :size="12" />
            Finished
          </button>
          <button
            @click="handleTabChange('want_to_read')"
            :class="selectedTab === 'want_to_read' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white bg-transparent'"
            class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-2"
          >
            <Bookmark :size="12" />
            Want to Read
          </button>
          <button
            @click="handleTabChange('favorites')"
            :class="selectedTab === 'favorites' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-white bg-transparent'"
            class="px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-2"
          >
            <Heart :size="12" :class="selectedTab === 'favorites' ? 'fill-current' : ''" />
            Favorites
          </button>
        </div>

        <!-- Books Grid -->
        <div v-if="filteredLibrary.length === 0" class="py-20 text-center glass border-slate-800 rounded-[2.5rem]">
          <p class="text-slate-600 font-bold uppercase tracking-widest text-xs">No entries found in archive</p>
        </div>

        <div v-else>
          <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-6 gap-y-10">
            <router-link
              v-for="userBook in paginatedLibrary"
              :key="userBook.id"
              :to="`/books/${userBook.book.id}`"
              class="group relative aspect-[2/3] rounded-xl overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 cursor-pointer shadow-lg hover:shadow-2xl hover:shadow-indigo-500/10 transition-all duration-300 flex items-center justify-center"
            >
            <img
              v-if="getCoverUrl(userBook.book)"
              :src="getCoverUrl(userBook.book)"
              :alt="userBook.book?.title"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              @error="(e) => e.target.style.display = 'none'"
            />
            <BookOpen v-if="!getCoverUrl(userBook.book)" :size="48" class="text-slate-600" />

            <!-- Hover Overlay -->
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
              <h3 class="font-bold text-white text-sm mb-1 line-clamp-2">{{ userBook.book?.title }}</h3>
              <p class="text-slate-400 text-xs line-clamp-1">{{ userBook.book?.authors?.map(a => a.name).join(', ') }}</p>
            </div>

            <!-- Status Badge -->
            <div v-if="getStatusBadge(userBook.status)" class="absolute top-3 left-3">
              <span
                :class="['px-2 py-1 rounded-lg text-[10px] font-bold shadow-lg', getStatusBadge(userBook.status).class]"
              >
                {{ getStatusBadge(userBook.status).text }}
              </span>
            </div>

            <!-- Favorite Icon -->
            <button
              v-if="userBook.is_favorite"
              @click.stop="handleToggleFavorite(userBook)"
              class="absolute top-3 right-3 p-1.5 rounded-lg bg-slate-950/80 backdrop-blur-sm"
            >
              <Heart :size="14" class="text-red-400 fill-current" />
            </button>

            <!-- Progress Bar for currently reading -->
            <div v-if="userBook.status === 'currently_reading' && getProgress(userBook) > 0" class="absolute bottom-0 left-0 right-0 h-1 bg-slate-800">
              <div
                :style="{ width: getProgress(userBook) + '%' }"
                class="h-full bg-indigo-500"
              />
            </div>
          </router-link>
        </div>

        <!-- Infinite scroll loading indicator -->
        <div v-if="hasMoreItems" class="flex justify-center mt-12 py-8">
          <div class="flex items-center gap-2 text-slate-500 text-sm">
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" style="animation-delay: 0.2s"></div>
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" style="animation-delay: 0.4s"></div>
          </div>
        </div>
      </div>
      </div>

      <!-- RIGHT COLUMN: Analytics Sidebar -->
      <div class="lg:col-span-4 space-y-8">
        <!-- Reading Circle Widget -->
        <ReadingCircleWidget />

        <!-- Yearly Reading Challenge Widget -->
        <YearlyChallengeWidget
          @edit="handleEditChallenge"
          @create="handleCreateChallenge"
        />

        <!-- Library DNA -->
        <div class="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <h3 class="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">Library DNA</h3>
          <div class="space-y-4">
            <!-- Sci-Fi -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Sci-Fi</span>
                <span class="text-xs font-bold text-slate-500">45%</span>
              </div>
              <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full bg-sky-400 rounded-full" style="width: 45%"></div>
              </div>
            </div>

            <!-- Non-Fiction -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Non-Fiction</span>
                <span class="text-xs font-bold text-slate-500">30%</span>
              </div>
              <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full bg-indigo-400 rounded-full" style="width: 30%"></div>
              </div>
            </div>

            <!-- Philosophy -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Philosophy</span>
                <span class="text-xs font-bold text-slate-500">15%</span>
              </div>
              <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div class="h-full bg-emerald-400 rounded-full" style="width: 15%"></div>
              </div>
            </div>
          </div>
          <button class="mt-6 text-[9px] font-black uppercase text-indigo-400 hover:text-white transition-colors flex items-center gap-2">
            Full Analysis <ArrowUpRight :size="12" />
          </button>
        </div>

        <!-- Consistency Heatmap -->
        <div class="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <h3 class="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">Consistency</h3>
          <div class="grid grid-cols-7 gap-1.5 mb-5">
            <div
              v-for="i in 28"
              :key="i"
              :class="i > 20 ? 'bg-indigo-500' : i > 10 ? 'bg-indigo-500/30' : 'bg-slate-800'"
              class="aspect-square rounded-[2px]"
            />
          </div>
          <div class="flex justify-between items-center">
            <div>
              <span class="text-xl font-black text-white block">12 Days</span>
              <span class="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Active Streak</span>
            </div>
            <div class="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
              <Zap :size="16" class="fill-current" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Yearly Challenge Modal -->
    <YearlyChallengeModal
      :challenge="editingChallenge"
      :open="showChallengeModal"
      @close="handleCloseChallengeModal"
      @save="handleSaveChallenge"
    />

    <!-- Import Dialog -->
    <Dialog v-model:open="showImportDialog">
      <DialogContent class="glass border-slate-700 sm:max-w-md">
        <DialogHeader>
          <DialogTitle class="text-2xl font-bold flex items-center gap-3">
            <FileUp :size="28" class="text-emerald-400" />
            Import from Goodreads
          </DialogTitle>
        </DialogHeader>

        <div class="space-y-6 py-4">
          <!-- Instructions -->
          <div class="space-y-3">
            <p class="text-sm text-slate-300 leading-relaxed">
              Import your reading history from Goodreads by uploading your library export CSV file.
            </p>
            <div class="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-3">
              <p class="text-xs text-indigo-300 font-medium">
                📚 How to export from Goodreads:
              </p>
              <ol class="text-xs text-slate-400 mt-2 space-y-1 list-decimal list-inside">
                <li>Go to Goodreads → My Books</li>
                <li>Click "Import and export"</li>
                <li>Download your library CSV</li>
              </ol>
            </div>
          </div>

          <!-- File Input -->
          <div class="space-y-3">
            <input
              ref="fileInputRef"
              type="file"
              accept=".csv"
              @change="handleFileSelect"
              class="hidden"
            />

            <button
              @click="triggerFileInput"
              :disabled="importing"
              class="w-full px-6 py-4 rounded-xl border-2 border-dashed border-slate-700 hover:border-indigo-500/50 bg-slate-900/50 hover:bg-slate-900 transition-all duration-300 text-slate-400 hover:text-white flex flex-col items-center justify-center gap-2"
            >
              <Upload :size="32" />
              <span class="text-sm font-medium">
                {{ selectedFile ? selectedFile.name : 'Click to select CSV file' }}
              </span>
            </button>
          </div>

          <!-- Progress -->
          <div v-if="importProgress" class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-slate-400">{{ importProgress.status }}</span>
              <span v-if="importProgress.total > 0" class="text-indigo-400 font-medium">
                {{ importProgress.current }} / {{ importProgress.total }}
              </span>
            </div>
            <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                v-if="importProgress.total > 0"
                class="bg-gradient-to-r from-emerald-500 to-teal-500 h-full transition-all duration-500 ease-out"
                :style="{ width: `${(importProgress.current / importProgress.total) * 100}%` }"
              />
              <div
                v-else
                class="bg-gradient-to-r from-emerald-500 to-teal-500 h-full animate-pulse"
                style="width: 100%"
              />
            </div>
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              @click="showImportDialog = false"
              :disabled="importing"
              class="px-5 py-3 rounded-xl border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              @click="handleImport"
              :disabled="!selectedFile || importing"
              class="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-bold hover:from-emerald-400 hover:to-teal-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Upload :size="16" />
              {{ importing ? 'Importing...' : 'Import Books' }}
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
</style>
