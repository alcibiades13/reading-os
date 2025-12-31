<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useAuthStore } from '@/stores/authStore'
import {
  BookOpen, Heart, Plus, Search, TrendingUp, Zap,
  CheckCircle, Bookmark, BrainCircuit, Lightbulb,
  Quote, ArrowUpRight
} from 'lucide-vue-next'

const router = useRouter()
const booksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const selectedTab = ref('all')
const loading = ref(true)

// Fetch books on mount
onMounted(async () => {
  await Promise.all([
    booksStore.fetchBooks(),
    quotesStore.fetchQuotes()
  ])
  loading.value = false
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

// Daily quote
const dailyQuote = computed(() => {
  const favorites = quotesStore.favoriteQuotes
  if (favorites.length > 0) {
    return favorites[Math.floor(Math.random() * favorites.length)]
  }
  if (quotesStore.quotes.length > 0) {
    return quotesStore.quotes[0]
  }
  return null
})

// Filtered library
const filteredLibrary = computed(() => {
  let books = booksStore.books
  if (selectedTab.value !== 'all') {
    if (selectedTab.value === 'favorites') {
      books = books.filter(b => b.is_favorite)
    } else {
      books = books.filter(b => b.status === selectedTab.value)
    }
  }
  if (searchQuery.value) {
    const search = searchQuery.value.toLowerCase()
    books = books.filter(b =>
      b.book?.title?.toLowerCase().includes(search) ||
      b.book?.authors?.some(a => a.name.toLowerCase().includes(search))
    )
  }
  return books
})

// Helper functions
const handleBookClick = (userBook) => {
  router.push(`/books/${userBook.book.id}`)
}

const getProgress = (userBook) => {
  if (!userBook.current_page || !userBook.book?.pages) return 0
  return Math.round((userBook.current_page / userBook.book.pages) * 100)
}

const getCoverUrl = (book) => {
  if (!book) return 'https://via.placeholder.com/300x450/1E293B/64748B?text=Book'
  return book.cover_image || 'https://via.placeholder.com/300x450/1E293B/64748B'
}

// Year stats
const finishedThisYear = computed(() => {
  const currentYear = new Date().getFullYear()
  return booksStore.books.filter(b => {
    if (b.status !== 'read' || !b.finished_at) return false
    return new Date(b.finished_at).getFullYear() === currentYear
  }).length
})

const yearGoal = 50
const yearProgress = computed(() => Math.round((finishedThisYear.value / yearGoal) * 100))
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
      <div class="lg:col-span-7 space-y-8">
        <div class="flex items-center gap-2 text-indigo-400 font-bold text-[10px] uppercase tracking-[0.4em]">
          <BrainCircuit :size="14" class="fill-current" />
          Reading OS / V2.5
        </div>
        <h1 class="text-6xl font-black text-white tracking-tighter">
          Hello, <span class="text-indigo-500">{{ userName }}</span>.
        </h1>
        <p class="text-slate-400 text-xl leading-relaxed max-w-xl">
          Your personal archive of knowledge and wonder. Revisit your insights, track your growth, and find your next great exploration.
        </p>

        <div class="flex flex-wrap items-center gap-4 pt-2">
          <div class="px-5 py-3 rounded-2xl glass border-slate-800 flex items-center gap-4">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">{{ stats.total }} entries in vault</span>
          </div>
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
        <div v-if="dailyQuote" class="relative p-7 rounded-[2rem] glass border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/5 overflow-hidden shadow-2xl">
          <span class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black uppercase text-indigo-400 mb-5 tracking-widest">
            <Lightbulb :size="12" /> Spotlight
          </span>
          <p class="text-lg md:text-xl font-serif italic text-slate-200 leading-relaxed mb-5 line-clamp-4">
            "{{ dailyQuote.text }}"
          </p>
          <div>
            <p class="text-indigo-400 font-bold text-xs">— {{ dailyQuote.book_author }}</p>
            <p class="text-slate-500 text-[10px] font-medium uppercase tracking-wider">{{ dailyQuote.book_title }}</p>
          </div>
        </div>
      </div>
    </div>
