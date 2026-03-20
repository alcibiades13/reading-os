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
import FriendsWidget from '@/components/social/FriendsWidget.vue'
import ConsistencyWidget from '@/components/ConsistencyWidget.vue'
import DailyQuote from '@/components/DailyQuote.vue'
import GoodreadsImportDialog from '@/components/GoodreadsImportDialog.vue'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { recommendationsService } from '@/services/recommendationsService'
import ReadingTaste from '@/components/recommendations/ReadingTaste.vue'
import { getBookUrl, getBookUrlWithSuffix } from '@/utils/bookUrl'
import {
  BookOpen, Heart, Plus, Search, TrendingUp, Zap,
  CheckCircle, Bookmark, BrainCircuit,
  ArrowUpRight, Upload, LayoutGrid, List, Star,
  MoreVertical, Trash2, X, ChevronRight, Home
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
const showChallengeModal = ref(false)
const editingChallenge = ref(null)
const viewMode = ref('grid') // 'grid' or 'list'
const showMobileWidgets = ref(false)

// Import dialog
const showImportDialog = ref(false)

// Pagination state
const itemsPerPage = 24 // Show 24 books per load (4 rows of 6)
const currentPage = ref(1)

// Reading taste state
const readingTaste = ref(null)

// Fetch books on mount
onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      booksStore.fetchBooks(),
      quotesStore.fetchQuotes()
    ])
    // Fetch reading taste separately (non-blocking)
    recommendationsService.getReadingTaste('all').then(taste => {
      readingTaste.value = taste
    })
  } catch (error) {
    // Library data load failed
  } finally {
    loading.value = false
  }

  // Find the scrollable main container
  const mainContainer = document.querySelector('main.overflow-y-auto')
  if (mainContainer) {
    mainContainer.addEventListener('scroll', handleScroll, { passive: true })
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
  router.push(getBookUrl(book.book))
}

const handleEditBook = (book) => {
  // TODO: Open edit dialog
}

const handleDeleteBook = async (book) => {
  if (confirm(`Remove "${book.book.title}" from your library?`)) {
    await booksStore.removeBook(book.id)
  }
}

const handleToggleFavorite = async (book) => {
  await booksStore.updateBook(book.id, {
    is_favorite: !book.is_favorite,
  })
}

const handleToggleOwned = async (book) => {
  await booksStore.toggleOwned(book.id)
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

  const today = new Date().toISOString().split('T')[0]
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

  if (storedDate !== today) {
    const availableQuotes = allQuotes.filter(q => !shownQuoteIds.includes(q.id))
    if (availableQuotes.length === 0) {
      shownQuoteIds = []
      localStorage.setItem(shownQuotesKey, JSON.stringify([]))
    }
    const quotesToChooseFrom = availableQuotes.length > 0 ? availableQuotes : allQuotes
    const randomIndex = Math.floor(Math.random() * quotesToChooseFrom.length)
    const selectedQuote = quotesToChooseFrom[randomIndex]
    shownQuoteIds.push(selectedQuote.id)
    localStorage.setItem(shownQuotesKey, JSON.stringify(shownQuoteIds))
    localStorage.setItem(lastDateKey, today)
    localStorage.setItem('todayQuoteId', selectedQuote.id.toString())
    return selectedQuote
  }

  const todayQuoteId = localStorage.getItem('todayQuoteId')
  if (todayQuoteId) {
    const quote = allQuotes.find(q => q.id.toString() === todayQuoteId)
    if (quote) return quote
  }
  return allQuotes[0]
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
const isLoadingMore = ref(false)
const handleScroll = (event) => {
  const element = event.target
  const scrollThreshold = 500
  const scrollPosition = element.scrollTop + element.clientHeight
  const scrollHeight = element.scrollHeight

  if (scrollHeight - scrollPosition < scrollThreshold && hasMoreItems.value && !loading.value && !isLoadingMore.value) {
    isLoadingMore.value = true
    loadMore()
    setTimeout(() => {
      isLoadingMore.value = false
    }, 500)
  }
}

onUnmounted(() => {
  const mainContainer = document.querySelector('main.overflow-y-auto')
  if (mainContainer) {
    mainContainer.removeEventListener('scroll', handleScroll)
  }
})

// Helper functions
const handleBookClick = (userBook, event) => {
  // Support middle-click to open in new tab
  if (event && (event.button === 1 || event.ctrlKey || event.metaKey)) {
    const route = router.resolve(getBookUrl(userBook.book))
    window.open(route.href, '_blank')
  } else {
    router.push(getBookUrl(userBook.book))
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
  <div v-if="loading" class="max-w-7xl mx-auto px-4 lg:px-6 py-12 lg:py-20 flex flex-col items-center justify-center space-y-4">
    <div class="w-10 h-10 lg:w-12 lg:h-12 border-4 border-slate-800 border-t-indigo-500 rounded-full animate-spin" />
    <p class="text-slate-500 font-bold uppercase tracking-widest text-[10px] lg:text-xs">Accessing Library...</p>
  </div>

  <!-- Main Content -->
  <div v-else class="w-full max-w-[1800px] mx-auto lg:px-8 lg:py-12">

    <!-- MOBILE HEADER -->
    <header class="lg:hidden relative border-b border-white/5 bg-slate-900">
      <div class="px-4 pt-4 pb-3">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <BookOpen :size="20" class="text-white" />
            </div>
            <div>
              <h1 class="text-lg font-bold text-white">Library</h1>
              <p class="text-xs text-slate-500">{{ stats.total }} books</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="showMobileWidgets = true"
              class="p-2.5 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <TrendingUp :size="18" />
            </button>
            <button
              @click="showImportDialog = true"
              class="p-2.5 rounded-xl bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <Upload :size="18" />
            </button>
            <button
              @click="router.push('/import')"
              class="p-2.5 rounded-xl bg-indigo-500 text-white"
            >
              <Plus :size="18" />
            </button>
          </div>
        </div>

        <!-- Mobile Stats Row -->
        <div class="flex items-center gap-3 overflow-x-auto hide-scrollbar -mx-4 px-4 pb-1">
          <div class="shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Zap :size="14" class="text-indigo-400" />
            <span class="text-xs font-bold text-white">{{ stats.currently_reading || 0 }}</span>
            <span class="text-[10px] text-slate-500">Reading</span>
          </div>
          <div class="shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <CheckCircle :size="14" class="text-emerald-400" />
            <span class="text-xs font-bold text-white">{{ stats.read || 0 }}</span>
            <span class="text-[10px] text-slate-500">Finished</span>
          </div>
          <div class="shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Bookmark :size="14" class="text-sky-400" />
            <span class="text-xs font-bold text-white">{{ stats.want_to_read || 0 }}</span>
            <span class="text-[10px] text-slate-500">To Read</span>
          </div>
          <div class="shrink-0 flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Heart :size="14" class="text-red-400 fill-current" />
            <span class="text-xs font-bold text-white">{{ booksStore.favoriteBooks.length }}</span>
            <span class="text-[10px] text-slate-500">Favorites</span>
          </div>
        </div>
      </div>
    </header>

    <!-- DESKTOP HERO SECTION -->
    <div class="hidden lg:grid grid-cols-1 lg:grid-cols-12 gap-8 mb-16 items-start">

      <!-- Welcome Briefing -->
      <div class="lg:col-span-7">
        <div class="flex items-center gap-2 text-indigo-400 font-bold text-page-meta uppercase tracking-[0.3em] sm:tracking-[0.4em] mb-4">
          <BrainCircuit :size="12" class="sm:w-3.5 sm:h-3.5 fill-current" />
          Reading OS / V2.5
        </div>
        <h1 class="text-page-heading font-black text-white tracking-tighter mb-3">
          Hello, <span class="text-indigo-500">{{ userName }}</span>.
        </h1>
        <p class="text-page-subtitle text-slate-400 leading-relaxed max-w-xl">
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
      <DailyQuote :quote="dailyQuote" />
    </div>

    <!-- MOBILE WISDOM SPOTLIGHT -->
    <DailyQuote :quote="dailyQuote" compact />

    <!-- ACTIVE EXPEDITIONS - Mobile -->
    <div v-if="activeExpeditions.length > 0" class="lg:hidden px-4 py-4">
      <div class="flex items-center justify-between mb-3">
        <h2 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] flex items-center gap-2">
          <BookOpen :size="12" class="text-indigo-500" />
          Active Expeditions
        </h2>
        <span class="text-[10px] font-bold text-slate-600">{{ currentlyReading.length }} reading</span>
      </div>

      <div class="flex gap-3 overflow-x-auto hide-scrollbar -mx-4 px-4 pb-2">
        <router-link
          v-for="expedition in activeExpeditions"
          :key="expedition.id"
          :to="getBookUrl(expedition.book)"
          class="shrink-0 w-[280px] relative p-3 rounded-xl glass border-slate-800 active:scale-[0.98] transition-transform"
        >
          <!-- Badge -->
          <div class="absolute top-2 right-2 z-10">
            <span
              :class="expedition.isLastRead ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400'"
              class="px-1.5 py-0.5 rounded-md border text-[8px] font-black uppercase tracking-wider"
            >
              {{ expedition.isLastRead ? 'Last Read' : 'Reading' }}
            </span>
          </div>

          <div class="flex gap-3">
            <div class="shrink-0 w-12 h-[72px] rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-lg flex items-center justify-center">
              <img
                v-if="getCoverUrl(expedition.book)"
                :src="getCoverUrl(expedition.book)"
                :alt="expedition.book?.title"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
              <BookOpen v-else :size="18" class="text-slate-600" />
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-bold text-white text-sm mb-0.5 line-clamp-1">
                {{ expedition.book?.title }}
              </h3>
              <p class="text-slate-500 text-[10px] mb-2 line-clamp-1">
                {{ expedition.book?.authors?.map(a => a.name).join(', ') }}
              </p>

              <!-- Progress bar for currently reading -->
              <div v-if="!expedition.isLastRead" class="space-y-1">
                <div class="flex items-center justify-between text-[10px]">
                  <span class="text-slate-400">{{ getProgress(expedition) }}%</span>
                  <span class="text-slate-600">{{ expedition.current_page || 0 }}/{{ expedition.book?.pages || 0 }}</span>
                </div>
                <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    :style="{ width: getProgress(expedition) + '%' }"
                    class="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                  />
                </div>
              </div>

              <!-- Rating for last read -->
              <div v-else class="flex items-center gap-2">
                <div v-if="expedition.rating" class="flex items-center gap-1">
                  <Heart :size="10" class="text-yellow-400 fill-current" />
                  <span class="text-yellow-400 font-bold text-xs">{{ expedition.rating }}/10</span>
                </div>
                <span v-else class="text-slate-600 text-[10px]">No rating</span>
              </div>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- ACTIVE EXPEDITIONS - Desktop -->
    <div v-if="activeExpeditions.length > 0" class="hidden lg:block mb-16">
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
          :to="getBookUrl(expedition.book)"
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
                  @click.stop="router.push(getBookUrlWithSuffix(expedition.book, 'review-view'))"
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
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12">

      <!-- LEFT COLUMN: SEARCH, TABS & BOOKS -->
      <div class="lg:col-span-8 space-y-4 lg:space-y-8 lg:pt-6 lg:border-t lg:border-slate-900">

        <!-- Mobile Search Bar -->
        <div class="lg:hidden px-4">
          <div class="relative">
            <Search :size="18" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search books..."
              class="w-full bg-slate-800/50 border border-slate-700 rounded-xl pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/40 focus:bg-slate-800 outline-none transition-all"
            />
          </div>
        </div>

        <!-- Desktop Search Bar with Import Button -->
        <div class="hidden lg:flex items-center gap-4">
          <div class="relative group flex-1">
            <div class="absolute inset-0 bg-indigo-500/5 blur-2xl opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none" />
            <Search :size="24" class="absolute left-6 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-500 transition-colors" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Query your personal archive by title, author, or keyword..."
              class="bg-slate-900/40 border border-slate-800 rounded-3xl pl-16 pr-8 py-4 text-lg text-white placeholder-slate-600 focus:border-indigo-500/40 focus:bg-slate-900 outline-none transition-all w-full shadow-lg"
            />
          </div>

          <!-- Import from Goodreads Button -->
          <button
            @click="showImportDialog = true"
            class="px-6 py-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold text-sm transition-all duration-300 shadow-lg shadow-emerald-500/20 hover:shadow-xl hover:shadow-emerald-500/30 flex items-center gap-2 shrink-0"
          >
            <Upload :size="18" />
            <span class="hidden sm:inline">Import from Goodreads</span>
          </button>
        </div>

        <!-- Mobile Tabs (Horizontal Scroll) -->
        <div class="lg:hidden">
          <div class="flex items-center gap-2 overflow-x-auto hide-scrollbar px-4 pb-2">
            <button
              @click="handleTabChange('all')"
              :class="selectedTab === 'all' ? 'bg-indigo-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
              class="shrink-0 px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2"
            >
              <BookOpen :size="14" />
              All
            </button>
            <button
              @click="handleTabChange('currently_reading')"
              :class="selectedTab === 'currently_reading' ? 'bg-indigo-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
              class="shrink-0 px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2"
            >
              <Zap :size="14" />
              Reading
            </button>
            <button
              @click="handleTabChange('read')"
              :class="selectedTab === 'read' ? 'bg-indigo-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
              class="shrink-0 px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2"
            >
              <CheckCircle :size="14" />
              Finished
            </button>
            <button
              @click="handleTabChange('want_to_read')"
              :class="selectedTab === 'want_to_read' ? 'bg-indigo-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
              class="shrink-0 px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2"
            >
              <Bookmark :size="14" />
              To Read
            </button>
            <button
              @click="handleTabChange('favorites')"
              :class="selectedTab === 'favorites' ? 'bg-indigo-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
              class="shrink-0 px-4 py-2 rounded-xl text-xs font-bold border transition-all flex items-center gap-2"
            >
              <Heart :size="14" :class="selectedTab === 'favorites' ? 'fill-current' : ''" />
              Favorites
            </button>
          </div>

          <!-- Mobile View Toggle -->
          <div class="flex items-center justify-between px-4 mt-2">
            <span class="text-xs text-slate-500">{{ filteredLibrary.length }} books</span>
            <div class="flex items-center gap-1 p-0.5 bg-slate-800/50 rounded-lg border border-slate-700">
              <button
                @click="viewMode = 'grid'"
                :class="[
                  'p-2 rounded-md transition-all',
                  viewMode === 'grid' ? 'bg-indigo-500 text-white' : 'text-slate-500'
                ]"
              >
                <LayoutGrid :size="16" />
              </button>
              <button
                @click="viewMode = 'list'"
                :class="[
                  'p-2 rounded-md transition-all',
                  viewMode === 'list' ? 'bg-indigo-500 text-white' : 'text-slate-500'
                ]"
              >
                <List :size="16" />
              </button>
            </div>
          </div>
        </div>

        <!-- Desktop Tabs and View Toggle -->
        <div class="hidden lg:flex flex-wrap items-center justify-between gap-4">
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

          <!-- View Toggle -->
          <div class="flex items-center gap-1 p-1 bg-slate-900/80 rounded-xl border border-slate-800">
            <button
              @click="viewMode = 'grid'"
              :class="[
                'p-2.5 rounded-lg transition-all',
                viewMode === 'grid' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'
              ]"
              title="Grid View"
            >
              <LayoutGrid :size="18" />
            </button>
            <button
              @click="viewMode = 'list'"
              :class="[
                'p-2.5 rounded-lg transition-all',
                viewMode === 'list' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'
              ]"
              title="List View"
            >
              <List :size="18" />
            </button>
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="filteredLibrary.length === 0" class="mx-4 lg:mx-0 py-12 lg:py-20 text-center glass border-slate-800 rounded-2xl lg:rounded-[2.5rem]">
          <p class="text-slate-600 font-bold uppercase tracking-widest text-xs">No entries found in archive</p>
        </div>

        <!-- Grid View -->
        <div v-else-if="viewMode === 'grid'" class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 lg:gap-x-6 lg:gap-y-10 px-4 lg:px-0">
          <router-link
            v-for="userBook in paginatedLibrary"
            :key="userBook.id"
            :to="getBookUrl(userBook.book)"
            class="group relative aspect-[2/3] rounded-lg lg:rounded-xl overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 cursor-pointer shadow-lg lg:hover:shadow-2xl lg:hover:shadow-indigo-500/10 transition-all duration-300 flex items-center justify-center active:scale-[0.98]"
          >
            <img
              v-if="getCoverUrl(userBook.book)"
              :src="getCoverUrl(userBook.book)"
              :alt="userBook.book?.title"
              class="w-full h-full object-cover lg:group-hover:scale-105 transition-transform duration-500"
              @error="(e) => e.target.style.display = 'none'"
            />
            <BookOpen v-if="!getCoverUrl(userBook.book)" :size="24" class="text-slate-600 lg:w-12 lg:h-12" />

            <!-- Hover Overlay (Desktop only) -->
            <div class="hidden lg:flex absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/80 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex-col justify-end p-4">
              <h3 class="font-bold text-white text-sm mb-1 line-clamp-2">{{ userBook.book?.title }}</h3>
              <p class="text-slate-400 text-xs line-clamp-1">{{ userBook.book?.authors?.map(a => a.name).join(', ') }}</p>
            </div>

            <!-- Status Badge -->
            <div v-if="getStatusBadge(userBook.status)" class="absolute top-1.5 left-1.5 lg:top-3 lg:left-3">
              <span
                :class="['px-1.5 py-0.5 lg:px-2 lg:py-1 rounded-md lg:rounded-lg text-[8px] lg:text-[10px] font-bold shadow-lg', getStatusBadge(userBook.status).class]"
              >
                {{ getStatusBadge(userBook.status).text }}
              </span>
            </div>

            <!-- Favorite Icon -->
            <button
              v-if="userBook.is_favorite"
              @click.stop="handleToggleFavorite(userBook)"
              class="absolute top-1.5 right-1.5 lg:top-3 lg:right-3 p-1 lg:p-1.5 rounded-md lg:rounded-lg bg-slate-950/80 backdrop-blur-sm"
            >
              <Heart :size="12" class="text-red-400 fill-current lg:w-3.5 lg:h-3.5" />
            </button>

            <!-- More Options (Grid View - Desktop only) -->
            <div class="hidden lg:block absolute bottom-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <button
                    @click.stop
                    class="p-2 rounded-lg bg-slate-950/80 backdrop-blur-sm hover:bg-slate-900 transition-colors text-slate-400 hover:text-white"
                  >
                    <MoreVertical :size="16" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="bg-slate-900 border-slate-800">
                  <DropdownMenuItem
                    @click.stop="handleToggleOwned(userBook)"
                    class="text-xs cursor-pointer hover:bg-slate-800 flex items-center gap-2"
                  >
                    <Home :size="14" />
                    {{ userBook.is_owned ? 'Remove from shelf' : 'I own this' }}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    @click.stop="handleDeleteBook(userBook)"
                    class="text-xs cursor-pointer hover:bg-slate-800 text-red-400 hover:text-red-300 flex items-center gap-2"
                  >
                    <Trash2 :size="14" />
                    Remove from Library
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            <!-- Progress Bar for currently reading -->
            <div v-if="userBook.status === 'currently_reading' && getProgress(userBook) > 0" class="absolute bottom-0 left-0 right-0 h-1 bg-slate-800">
              <div
                :style="{ width: getProgress(userBook) + '%' }"
                class="h-full bg-indigo-500"
              />
            </div>
          </router-link>
        </div>

        <!-- List/Table View -->
        <div v-else-if="viewMode === 'list'" class="space-y-2 lg:space-y-3 px-4 lg:px-0">
          <!-- Table Header (Desktop only) -->
          <div class="hidden lg:flex items-center gap-4 px-4 py-2 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">
            <!-- Cover -->
            <div class="shrink-0 w-12"></div>

            <!-- Title & Author -->
            <div class="flex-1 min-w-0">Book</div>

            <!-- Star Rating -->
            <div class="hidden sm:flex w-20 justify-center">Rating</div>

            <!-- Date Read -->
            <div class="hidden md:block w-24 text-center">Date Read</div>

            <!-- Date Added -->
            <div class="hidden lg:block w-24 text-center">Date Added</div>

            <!-- Status Badge -->
            <div class="hidden xl:flex w-28 justify-center">Status</div>

            <!-- Actions -->
            <div class="w-16"></div>
          </div>

          <!-- Table Rows -->
          <router-link
            v-for="userBook in paginatedLibrary"
            :key="userBook.id"
            :to="getBookUrl(userBook.book)"
            class="group flex items-center gap-3 lg:gap-4 p-3 lg:p-4 rounded-xl lg:rounded-2xl glass border-slate-800 lg:hover:border-indigo-500/30 transition-all duration-300 active:scale-[0.99]"
          >
            <!-- Cover -->
            <div class="shrink-0 w-10 h-14 lg:w-12 lg:h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-lg flex items-center justify-center">
              <img
                v-if="getCoverUrl(userBook.book)"
                :src="getCoverUrl(userBook.book)"
                :alt="userBook.book?.title"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
              <BookOpen v-else :size="16" class="text-slate-600 lg:w-5 lg:h-5" />
            </div>

            <!-- Title & Author -->
            <div class="flex-1 min-w-0">
              <h3 class="font-bold text-white text-sm truncate lg:group-hover:text-indigo-400 transition-colors">
                {{ userBook.book?.title }}
              </h3>
              <p class="text-slate-400 text-xs truncate">
                {{ userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author' }}
              </p>
              <!-- Mobile: Show rating and status inline -->
              <div class="lg:hidden flex items-center gap-2 mt-1">
                <span
                  v-if="getStatusBadge(userBook.status)"
                  :class="['px-1.5 py-0.5 rounded-md text-[8px] font-bold', getStatusBadge(userBook.status).class]"
                >
                  {{ getStatusBadge(userBook.status).text }}
                </span>
                <span v-if="userBook.rating" class="text-[10px] font-bold text-amber-400">{{ userBook.rating }}/10</span>
              </div>
            </div>

            <!-- Star Rating (10-point scale) - Desktop -->
            <div class="hidden lg:flex flex-col items-center gap-1 w-32">
              <span v-if="userBook.rating" class="text-xs font-bold text-amber-400">{{ userBook.rating }}</span>
              <div class="flex items-center gap-0.5">
                <Star
                  v-for="i in 10"
                  :key="i"
                  :size="12"
                  :class="i <= (userBook.rating || 0) ? 'text-amber-400 fill-current' : 'text-slate-700'"
                />
              </div>
            </div>

            <!-- Date Read - Desktop -->
            <div class="hidden lg:block text-xs text-slate-500 w-24 text-center">
              {{ userBook.finished_at ? new Date(userBook.finished_at).toLocaleDateString() : '—' }}
            </div>

            <!-- Date Added - Desktop -->
            <div class="hidden xl:block text-xs text-slate-500 w-24 text-center">
              {{ userBook.created_at ? new Date(userBook.created_at).toLocaleDateString() : '—' }}
            </div>

            <!-- Status Badge - Desktop -->
            <div class="hidden xl:flex w-28 justify-center">
              <span
                v-if="getStatusBadge(userBook.status)"
                :class="['px-2 py-1 rounded-lg text-[9px] font-bold whitespace-nowrap', getStatusBadge(userBook.status).class]"
              >
                {{ getStatusBadge(userBook.status).text }}
              </span>
            </div>

            <!-- Actions -->
            <div class="flex items-center gap-1 lg:gap-2 lg:w-16 justify-end">
              <button
                v-if="userBook.is_favorite"
                @click.stop="handleToggleFavorite(userBook)"
                class="p-1.5 lg:p-2 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <Heart :size="14" class="text-red-400 fill-current lg:w-4 lg:h-4" />
              </button>
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <button
                    @click.stop
                    class="p-1.5 lg:p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-500 hover:text-white"
                  >
                    <MoreVertical :size="16" class="lg:w-[18px] lg:h-[18px]" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="bg-slate-900 border-slate-800">
                  <DropdownMenuItem
                    @click.stop="handleToggleOwned(userBook)"
                    class="text-xs cursor-pointer hover:bg-slate-800 flex items-center gap-2"
                  >
                    <Home :size="14" />
                    {{ userBook.is_owned ? 'Remove from shelf' : 'I own this' }}
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    @click.stop="handleDeleteBook(userBook)"
                    class="text-xs cursor-pointer hover:bg-slate-800 text-red-400 hover:text-red-300 flex items-center gap-2"
                  >
                    <Trash2 :size="14" />
                    Remove from Library
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </router-link>
        </div>

        <!-- Infinite scroll loading indicator (for both grid and list views) -->
        <div v-if="hasMoreItems" class="flex justify-center mt-8 lg:mt-12 py-6 lg:py-8 px-4 lg:px-0">
          <div class="flex items-center gap-2 text-slate-500 text-sm">
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse"></div>
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" style="animation-delay: 0.2s"></div>
            <div class="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" style="animation-delay: 0.4s"></div>
          </div>
        </div>

        <!-- Mobile bottom padding for safe area -->
        <div class="lg:hidden h-8"></div>
      </div>

      <!-- RIGHT COLUMN: Analytics Sidebar (Desktop only) -->
      <div class="hidden lg:block lg:col-span-4 space-y-8">
        <!-- Friends Widget -->
        <FriendsWidget />

        <!-- Reading Circle Widget -->
        <ReadingCircleWidget />

        <!-- Yearly Reading Challenge Widget -->
        <YearlyChallengeWidget
          @edit="handleEditChallenge"
          @create="handleCreateChallenge"
        />

        <!-- Reading Taste -->
        <ReadingTaste v-if="readingTaste && readingTaste.books_count > 0" :taste="readingTaste" compact title="Your Reading Taste" />

        <!-- Taste Empty State -->
        <div v-else class="p-8 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <h3 class="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px] mb-6">Your Reading Taste</h3>
          <p class="text-sm text-slate-500">
            Add books to your library to discover your reading taste.
          </p>
        </div>

        <!-- Consistency Heatmap -->
        <ConsistencyWidget />
      </div>
    </div>

    <!-- Yearly Challenge Modal -->
    <YearlyChallengeModal
      :challenge="editingChallenge"
      :open="showChallengeModal"
      @close="handleCloseChallengeModal"
      @save="handleSaveChallenge"
    />

    <!-- Mobile Widgets Slide-out Panel -->
    <Teleport to="body">
      <Transition name="slide">
        <div
          v-if="showMobileWidgets"
          class="lg:hidden fixed inset-0 z-50"
        >
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/60 backdrop-blur-sm"
            @click="showMobileWidgets = false"
          />

          <!-- Panel -->
          <div class="absolute right-0 top-0 bottom-0 w-[85%] max-w-sm bg-slate-900 border-l border-slate-800 overflow-y-auto">
            <!-- Header -->
            <div class="sticky top-0 z-10 flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900">
              <h2 class="text-lg font-bold text-white">Insights</h2>
              <button
                @click="showMobileWidgets = false"
                class="p-2 rounded-xl bg-slate-800 text-slate-400"
              >
                <X :size="18" />
              </button>
            </div>

            <!-- Widgets -->
            <div class="p-4 space-y-4">
              <!-- Friends Widget -->
              <FriendsWidget />

              <!-- Reading Circle Widget -->
              <ReadingCircleWidget />

              <!-- Yearly Challenge Widget -->
              <YearlyChallengeWidget
                @edit="handleEditChallenge"
                @create="handleCreateChallenge"
              />

              <!-- Reading Taste -->
              <ReadingTaste v-if="readingTaste && readingTaste.books_count > 0" :taste="readingTaste" compact title="Your Reading Taste" />

              <!-- Consistency Heatmap -->
              <ConsistencyWidget compact />
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Import Dialog -->
    <GoodreadsImportDialog v-model:open="showImportDialog" />
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* Hide scrollbar for horizontal scroll areas */
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

/* Safe area support for notched phones */
@supports (padding-top: env(safe-area-inset-top)) {
  header {
    padding-top: calc(1rem + env(safe-area-inset-top));
  }
}

/* Touch feedback for mobile */
@media (max-width: 1023px) {
  button, a {
    -webkit-tap-highlight-color: transparent;
  }
}

/* Slide transition for mobile widgets panel */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-active > div:last-child,
.slide-leave-active > div:last-child {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from > div:last-child,
.slide-leave-to > div:last-child {
  transform: translateX(100%);
}
</style>
