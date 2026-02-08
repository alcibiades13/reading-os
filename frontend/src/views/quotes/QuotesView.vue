<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuotesStore } from '@/stores/quotesStore'
import { userBooksAPI } from '@/services/api'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Plus, BookOpen, Edit, Trash2, Star, Copy, Bookmark, MoreHorizontal, Sparkles, Type, Search, AlignLeft, Hash, Globe, Lock, Save, ExternalLink, X, Filter } from 'lucide-vue-next'

const router = useRouter()
const quotesStore = useQuotesStore()

const searchQuery = ref('')
const selectedTag = ref(null)
const showFavorites = ref(false)
const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)
const editingQuote = ref(null)
const showMobileFilters = ref(false)

// Book autocomplete (for create)
const bookSearchQuery = ref('')
const bookSearchResults = ref([])
const showBookDropdown = ref(false)
const isSearchingBooks = ref(false)

// Book autocomplete (for edit)
const editBookSearchQuery = ref('')
const editBookSearchResults = ref([])
const showEditBookDropdown = ref(false)
const isSearchingEditBooks = ref(false)

// New quote form
const newQuote = ref({
  text: '',
  note: '',
  book_title: '',
  book_author: '',
  page_number: null,
  chapter: '',
  tags_input: '',
  book: null,
  user_book: null,
  tag_ids: [],
  is_favorite: false,
  is_public: true,
})

// Edit quote form
const editQuote = ref({
  text: '',
  note: '',
  book_title: '',
  book_author: '',
  book: null,
  user_book: null,
  page_number: null,
  chapter: '',
  tags_input: '',
  tag_ids: [],
  is_favorite: false,
  is_public: true,
})

onMounted(async () => {
  await quotesStore.fetchQuotes()
  await quotesStore.fetchTags()
})

const displayedQuotes = computed(() => quotesStore.filteredQuotes)

const stats = computed(() => ({
  total: quotesStore.filteredQuotes?.length || 0,
  favorites: quotesStore.filteredQuotes?.filter(q => q.is_favorite)?.length || 0,
  books: new Set(quotesStore.filteredQuotes?.map(q => q.book_title)).size || 0
}))

const handleSearch = (e) => {
  quotesStore.setFilter('search', e.target.value)
}

const filterByTag = (tagId) => {
  selectedTag.value = tagId
  quotesStore.setFilter('tag', tagId)
}

const toggleFavorites = () => {
  showFavorites.value = !showFavorites.value
  quotesStore.setFilter('favorite', showFavorites.value ? true : null)
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedTag.value = null
  showFavorites.value = false
  quotesStore.resetFilters()
}

const handleCreateQuote = async () => {
  try {
    // Validate that book title is provided
    if (!newQuote.value.book_title) {
      alert('Book title is required')
      return
    }

    // Parse tags from comma-separated string
    const tagNames = newQuote.value.tags_input
      ? newQuote.value.tags_input.split(',').map(t => t.trim()).filter(t => t !== '')
      : []

    // Prepare payload for API - NO BOOK CREATION
    const payload = {
      text: newQuote.value.text,
      note: newQuote.value.note,
      book_title: newQuote.value.book_title,
      book_author: newQuote.value.book_author,
      book: newQuote.value.book || null,
      user_book: newQuote.value.user_book || null,
      page_number: newQuote.value.page_number || null,
      chapter: newQuote.value.chapter || '',
      is_favorite: newQuote.value.is_favorite,
      is_public: newQuote.value.is_public,
    }

    // Handle tags - fetch latest, then create only if doesn't exist
    if (tagNames.length > 0) {
      // Refresh tags from backend first
      await quotesStore.fetchTags()

      const tagIds = []
      for (const tagName of tagNames) {
        // Check if tag already exists in store
        const existingTag = quotesStore.tags.find(t =>
          t.name.toLowerCase() === tagName.toLowerCase()
        )

        if (existingTag) {
          tagIds.push(existingTag.id)
        } else {
          // Create new tag only if it doesn't exist
          const result = await quotesStore.createTag({ name: tagName })
          if (result.success) {
            tagIds.push(result.data.id)
          } else {
            console.error('Failed to create tag:', result.error)
          }
        }
      }
      payload.tag_ids = tagIds
    }

    const result = await quotesStore.createQuote(payload)

    if (result.success) {
      isCreateDialogOpen.value = false
      resetForm()
      // Refresh quotes to show the new one
      await quotesStore.fetchQuotes()
    } else {
      console.error('Quote creation failed:', result.error)
      alert(`Failed to create quote: ${JSON.stringify(result.error)}`)
    }
  } catch (error) {
    console.error('Error creating quote:', error)
    alert(`Error: ${error.message}`)
  }
}

const resetForm = () => {
  newQuote.value = {
    text: '',
    note: '',
    book_title: '',
    book_author: '',
    page_number: null,
    chapter: '',
    tags_input: '',
    book: null,
    user_book: null,
    tag_ids: [],
    is_favorite: false,
    is_public: false,
  }
}

const toggleFavorite = async (quote) => {
  try {
    console.log('Toggling favorite for quote:', quote.id, 'Current value:', quote.is_favorite)
    const result = await quotesStore.updateQuote(quote.id, {
      is_favorite: !quote.is_favorite,
    })
    if (!result.success) {
      console.error('Failed to toggle favorite:', result.error)
      console.error('Full error details:', JSON.stringify(result.error, null, 2))
      alert(`Failed to update favorite status: ${JSON.stringify(result.error)}`)
    } else {
      console.log('Successfully toggled favorite')
    }
  } catch (error) {
    console.error('Error toggling favorite:', error)
    console.error('Error response:', error.response)
    alert('Error updating favorite status')
  }
}

const deleteQuote = async (quote) => {
  if (confirm('Delete this quote?')) {
    await quotesStore.deleteQuote(quote.id)
  }
}

const copyQuote = (quote) => {
  const text = `"${quote.text}" — ${quote.book_title} by ${quote.book_author || 'Unknown Author'}`
  navigator.clipboard.writeText(text)
}

// Track expanded notes
const expandedNotes = ref(new Set())
const toggleNotes = (quoteId) => {
  if (expandedNotes.value.has(quoteId)) {
    expandedNotes.value.delete(quoteId)
  } else {
    expandedNotes.value.add(quoteId)
  }
}

const handleBookClick = (quote) => {
  // If quote has book ID, navigate to book detail page
  if (quote.book) {
    router.push(`/books/${quote.book}`)
  }
}

// Book search autocomplete
const searchBooks = async (query) => {
  if (!query || query.length < 2) {
    bookSearchResults.value = []
    showBookDropdown.value = false
    return
  }

  isSearchingBooks.value = true
  try {
    const response = await userBooksAPI.list({ search: query })
    bookSearchResults.value = response.data.results || response.data || []
    showBookDropdown.value = bookSearchResults.value.length > 0
  } catch (error) {
    console.error('Error searching books:', error)
    bookSearchResults.value = []
  } finally {
    isSearchingBooks.value = false
  }
}

const selectBook = (userBook) => {
  newQuote.value.book = userBook.book.id
  newQuote.value.user_book = userBook.id
  newQuote.value.book_title = userBook.book.title
  newQuote.value.book_author = userBook.book.authors?.[0]?.name || ''
  bookSearchQuery.value = userBook.book.title
  showBookDropdown.value = false
}

const handleBookInputChange = async (e) => {
  bookSearchQuery.value = e.target.value
  newQuote.value.book_title = e.target.value
  await searchBooks(e.target.value)
}

// Edit book search functions
const searchEditBooks = async (query) => {
  if (!query || query.length < 2) {
    editBookSearchResults.value = []
    showEditBookDropdown.value = false
    return
  }

  isSearchingEditBooks.value = true
  try {
    const response = await userBooksAPI.list({ search: query })
    editBookSearchResults.value = response.data.results || response.data || []
    showEditBookDropdown.value = editBookSearchResults.value.length > 0
  } catch (error) {
    console.error('Error searching books:', error)
    editBookSearchResults.value = []
  } finally {
    isSearchingEditBooks.value = false
  }
}

const selectEditBook = (userBook) => {
  console.log('Selected edit book:', userBook)
  editQuote.value.book = userBook.book.id
  editQuote.value.user_book = userBook.id
  editQuote.value.book_title = userBook.book.title
  editQuote.value.book_author = userBook.book.authors?.[0]?.name || ''
  editBookSearchQuery.value = userBook.book.title
  showEditBookDropdown.value = false
  console.log('Updated editQuote:', editQuote.value)
}

const handleEditBookInputChange = async (e) => {
  editBookSearchQuery.value = e.target.value
  editQuote.value.book_title = e.target.value
  await searchEditBooks(e.target.value)
}

const openEditDialog = (quote) => {
  editingQuote.value = quote
  editQuote.value = {
    text: quote.text,
    note: quote.note || '',
    book_title: quote.book_title,
    book_author: quote.book_author,
    book: quote.book || null,
    user_book: quote.user_book || null,
    page_number: quote.page_number,
    chapter: quote.chapter || '',
    tags_input: quote.tags?.map(t => t.name).join(', ') || '',
    tag_ids: quote.tags?.map(t => t.id) || [],
    is_favorite: quote.is_favorite,
    is_public: quote.is_public,
  }
  // Reset edit book search
  editBookSearchQuery.value = quote.book_title || ''
  editBookSearchResults.value = []
  showEditBookDropdown.value = false
  isEditDialogOpen.value = true
}

const handleEditQuote = async () => {
  try {
    // Parse tags from comma-separated string
    const tagNames = editQuote.value.tags_input
      ? editQuote.value.tags_input.split(',').map(t => t.trim()).filter(t => t !== '')
      : []

    // Prepare payload
    const payload = {
      text: editQuote.value.text,
      note: editQuote.value.note,
      book_title: editQuote.value.book_title,
      book_author: editQuote.value.book_author,
      book: editQuote.value.book || null,
      user_book: editQuote.value.user_book || null,
      page_number: editQuote.value.page_number || null,
      chapter: editQuote.value.chapter || '',
      is_favorite: editQuote.value.is_favorite,
      is_public: editQuote.value.is_public,
    }

    // Handle tags
    if (tagNames.length > 0) {
      await quotesStore.fetchTags()
      const tagIds = []

      for (const tagName of tagNames) {
        const existingTag = quotesStore.tags.find(t =>
          t.name.toLowerCase() === tagName.toLowerCase()
        )

        if (existingTag) {
          tagIds.push(existingTag.id)
        } else {
          const result = await quotesStore.createTag({ name: tagName })
          if (result.success) {
            tagIds.push(result.data.id)
          }
        }
      }
      payload.tag_ids = tagIds
    } else {
      payload.tag_ids = []
    }

    console.log('Edit Quote Payload:', payload)
    const result = await quotesStore.updateQuote(editingQuote.value.id, payload)

    if (result.success) {
      console.log('Quote updated successfully:', result)
      isEditDialogOpen.value = false
      editingQuote.value = null
      await quotesStore.fetchQuotes()
    } else {
      console.error('Quote update failed:', result.error)
      alert(`Failed to update quote: ${JSON.stringify(result.error)}`)
    }
  } catch (error) {
    console.error('Error updating quote:', error)
    alert(`Error: ${error.message}`)
  }
}
</script>

<template>
  <div class="animate-in fade-in duration-700 pb-20">
    <!-- Mobile Header (Sticky - minimal) -->
    <div class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 safe-area-top">
      <div class="flex items-center justify-between px-4 py-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Type :size="18" class="text-indigo-400" />
          </div>
          <div>
            <h1 class="text-base font-bold text-white">Quotes & Insights</h1>
            <p class="text-xs text-slate-500">{{ stats.total }} collected</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="showMobileFilters = true"
            class="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-400 active:scale-95 transition-transform"
          >
            <Filter :size="18" />
          </button>
          <button
            @click="isCreateDialogOpen = true"
            class="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20 active:scale-95 transition-transform"
          >
            <Plus :size="20" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Content Area (Not sticky) -->
    <div class="lg:hidden px-4 pt-4 space-y-3">
      <!-- Mobile Stats Row -->
      <div class="flex gap-2 overflow-x-auto scrollbar-hide pb-1">
        <div class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
          <Sparkles :size="12" class="text-indigo-400" />
          <span class="text-[11px] font-bold text-white">{{ stats.total }}</span>
          <span class="text-[11px] text-indigo-400/70">insights</span>
        </div>
        <div class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
          <Star :size="12" class="text-amber-400" />
          <span class="text-[11px] font-bold text-white">{{ stats.favorites }}</span>
          <span class="text-[11px] text-amber-400/70">favorites</span>
        </div>
        <div class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-sky-500/10 border border-sky-500/20">
          <BookOpen :size="12" class="text-sky-400" />
          <span class="text-[11px] font-bold text-white">{{ stats.books }}</span>
          <span class="text-[11px] text-sky-400/70">sources</span>
        </div>
      </div>

      <!-- Active Filters -->
      <div v-if="selectedTag || showFavorites || searchQuery" class="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex-shrink-0">Active:</span>
        <button
          v-if="searchQuery"
          @click="searchQuery = ''; handleSearch()"
          class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-700/50 border border-slate-600 text-slate-300 text-xs font-bold"
        >
          <Search :size="12" />
          "{{ searchQuery.length > 12 ? searchQuery.slice(0, 12) + '...' : searchQuery }}"
          <X :size="12" />
        </button>
        <button
          v-if="showFavorites"
          @click="toggleFavorites"
          class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-400 text-xs font-bold"
        >
          <Star :size="12" fill="currentColor" />
          Favorites
          <X :size="12" />
        </button>
        <button
          v-if="selectedTag"
          @click="selectedTag = null; quotesStore.setFilter('tag', null)"
          class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 text-xs font-bold"
        >
          #{{ quotesStore.tags?.find(t => t.id === selectedTag)?.name || selectedTag }}
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
                <h2 class="text-lg font-bold text-white">Filters & Tags</h2>
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
                    @input="handleSearch"
                    placeholder="Search quotes..."
                    class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <!-- Quick Filters -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Quick Filters</h3>
                <div class="space-y-2">
                  <button
                    @click="toggleFavorites(); showMobileFilters = false"
                    :class="showFavorites ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Star :size="18" :fill="showFavorites ? 'currentColor' : 'none'" />
                    <span class="font-bold">Favorites Only</span>
                  </button>
                </div>
              </div>

              <!-- Tags -->
              <div v-if="quotesStore.tags?.length > 0">
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Tags</h3>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="tag in quotesStore.tags"
                    :key="tag.id"
                    @click="filterByTag(tag.id); showMobileFilters = false"
                    :class="selectedTag === tag.id
                      ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400'
                      : 'border-slate-700 text-slate-400 hover:border-slate-600'"
                    class="px-3 py-2 rounded-xl border text-sm font-semibold transition-all"
                  >
                    #{{ tag.name }}
                  </button>
                </div>
              </div>

              <!-- Clear Filters -->
              <button
                v-if="selectedTag || showFavorites || searchQuery"
                @click="clearFilters(); showMobileFilters = false"
                class="w-full px-4 py-3 rounded-xl border border-red-500/30 text-red-400 font-bold text-sm hover:bg-red-500/10 transition-all"
              >
                Clear All Filters
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Page Header (Desktop) -->
    <div class="hidden lg:block max-w-7xl mx-auto pt-12 pb-8 px-6">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
        <header>
          <div class="flex items-center gap-2 sm:gap-3 mb-4">
            <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Type :size="18" class="sm:w-6 sm:h-6 text-indigo-400" />
            </div>
            <span class="text-page-meta font-bold text-indigo-400 uppercase tracking-[0.2em] sm:tracking-[0.3em]">Insights & Quotes</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
            The <span class="text-indigo-500">Collected</span> Mind
          </h1>
          <p class="text-page-subtitle text-slate-400 max-w-2xl leading-relaxed">
            Your digital commonplace book. Revisit the ideas that shaped your perspective and preserve the beauty of language.
          </p>
        </header>

        <Dialog v-model:open="isCreateDialogOpen">
          <DialogTrigger as-child>
            <button class="group flex items-center gap-2 sm:gap-3 px-5 sm:px-8 py-3 sm:py-5 rounded-2xl bg-indigo-500 text-white text-sm sm:text-base font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all">
              <Plus :size="18" class="sm:w-6 sm:h-6 group-hover:rotate-90 transition-transform duration-300" />
              <span class="hidden sm:inline">Add New Insight</span>
              <span class="sm:hidden">Add Quote</span>
            </button>
          </DialogTrigger>
          <DialogContent class="max-w-2xl glass border-slate-700 max-h-[85vh] overflow-y-auto">
            <DialogHeader class="border-b border-slate-800 pb-3 mb-4">
              <DialogTitle class="text-lg font-bold flex items-center gap-2">
                <div class="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                  <Type :size="16" class="text-white" />
                </div>
                Capture New Insight
              </DialogTitle>
              <DialogDescription class="sr-only">
                Add a new quote from a book to your library
              </DialogDescription>
            </DialogHeader>

            <form @submit.prevent="handleCreateQuote" class="space-y-5">
              <!-- Quote Content -->
              <div class="space-y-2">
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                  <component :is="AlignLeft" :size="12" /> The Quote
                </label>
                <Textarea
                  v-model="newQuote.text"
                  placeholder="Paste the brilliant words here..."
                  rows="4"
                  required
                  class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 transition-all resize-none"
                />
              </div>

              <!-- Book Info Grid -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="space-y-2 relative">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                    <component :is="Bookmark" :size="12" /> Book Title
                  </label>
                  <input
                    :value="bookSearchQuery || newQuote.book_title"
                    @input="handleBookInputChange"
                    @focus="showBookDropdown = bookSearchResults.length > 0"
                    placeholder="Start typing to search your books..."
                    required
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all outline-none"
                    autocomplete="off"
                  />
                  <!-- Autocomplete Dropdown -->
                  <div
                    v-if="showBookDropdown && bookSearchResults.length > 0"
                    class="absolute z-50 w-full mt-1 bg-slate-800 border-2 border-slate-700 rounded-xl shadow-2xl max-h-64 overflow-y-auto"
                  >
                    <button
                      v-for="userBook in bookSearchResults"
                      :key="userBook.id"
                      type="button"
                      @click="selectBook(userBook)"
                      class="w-full flex items-start gap-3 p-3 hover:bg-slate-700 transition-colors text-left border-b border-slate-700/50 last:border-0"
                    >
                      <div class="w-8 h-12 rounded overflow-hidden flex-shrink-0 bg-slate-700 flex items-center justify-center">
                        <img
                          v-if="userBook.book.cover_image"
                          :src="userBook.book.cover_image"
                          :alt="userBook.book.title"
                          class="w-full h-full object-cover"
                        />
                        <BookOpen v-else :size="14" class="text-slate-500" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-bold text-white truncate">{{ userBook.book.title }}</p>
                        <p class="text-xs text-slate-400 truncate">{{ userBook.book.authors?.[0]?.name || 'Unknown Author' }}</p>
                      </div>
                    </button>
                  </div>
                  <p v-if="isSearchingBooks" class="text-xs text-slate-500 mt-1">Searching...</p>
                </div>
                <div class="space-y-2">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                    <component :is="Hash" :size="12" /> Author
                  </label>
                  <Input
                    v-model="newQuote.book_author"
                    placeholder="The creative mind..."
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
                  />
                </div>
              </div>

              <!-- Metadata Grid -->
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div class="space-y-2">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Page</label>
                  <Input
                    v-model.number="newQuote.page_number"
                    type="number"
                    placeholder="e.g. 142"
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
                  />
                </div>
                <div class="space-y-2">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Chapter</label>
                  <Input
                    v-model="newQuote.chapter"
                    placeholder="e.g. Chapter IV"
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
                  />
                </div>
                <div class="space-y-2 md:col-span-1 col-span-2">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Tags</label>
                  <Input
                    v-model="newQuote.tags_input"
                    placeholder="philosophy, life, love"
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
                  />
                </div>
              </div>

              <!-- Personal Notes -->
              <div class="space-y-2">
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Personal Notes</label>
                <Textarea
                  v-model="newQuote.note"
                  placeholder="Why did this resonate with you?"
                  rows="2"
                  class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-600 focus:border-indigo-500 transition-all resize-none"
                />
              </div>

              <!-- Toggles -->
              <div class="flex flex-wrap gap-3 pt-2">
                <button
                  type="button"
                  @click="newQuote.is_favorite = !newQuote.is_favorite"
                  :class="newQuote.is_favorite ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-500'"
                  class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all text-sm"
                >
                  <component :is="Star" :size="16" :fill="newQuote.is_favorite ? 'currentColor' : 'none'" />
                  <span class="font-semibold">Favorite</span>
                </button>
                <button
                  type="button"
                  @click="newQuote.is_public = !newQuote.is_public"
                  :class="newQuote.is_public ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-700 text-slate-500'"
                  class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all text-sm"
                >
                  <component :is="newQuote.is_public ? Globe : Lock" :size="16" />
                  <span class="font-semibold">{{ newQuote.is_public ? 'Public' : 'Private' }}</span>
                </button>
              </div>

              <!-- Footer Buttons -->
              <div class="flex gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  @click="isCreateDialogOpen = false"
                  class="flex-1 px-4 py-3 rounded-lg border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-all"
                >
                  Discard
                </button>
                <button
                  type="submit"
                  class="flex-[2] px-4 py-3 rounded-lg bg-indigo-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
                >
                  <component :is="Save" :size="18" />
                  Save to Library
                </button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <!-- Stats Grid (Desktop) -->
      <div class="hidden lg:grid grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mb-12">
        <div class="p-4 sm:p-6 rounded-2xl sm:rounded-3xl border-2 text-indigo-400 bg-indigo-500/10 border-indigo-500/20 shadow-xl shadow-indigo-500/5 transition-all duration-500 hover:scale-[1.02]">
          <div class="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-4 opacity-70">
            <Sparkles :size="16" class="sm:w-5 sm:h-5" />
            <span class="text-[10px] sm:text-xs font-bold uppercase tracking-wider sm:tracking-widest">Total Insights</span>
          </div>
          <p class="text-2xl sm:text-4xl font-black text-white">{{ stats.total }}</p>
        </div>

        <div class="p-4 sm:p-6 rounded-2xl sm:rounded-3xl border-2 text-amber-400 bg-amber-500/10 border-amber-500/20 shadow-xl shadow-amber-500/5 transition-all duration-500 hover:scale-[1.02]">
          <div class="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-4 opacity-70">
            <Star :size="16" class="sm:w-5 sm:h-5" />
            <span class="text-[10px] sm:text-xs font-bold uppercase tracking-wider sm:tracking-widest">Favorite Gems</span>
          </div>
          <p class="text-2xl sm:text-4xl font-black text-white">{{ stats.favorites }}</p>
        </div>

        <div class="p-4 sm:p-6 rounded-2xl sm:rounded-3xl border-2 text-sky-400 bg-sky-500/10 border-sky-500/20 shadow-xl shadow-sky-500/5 transition-all duration-500 hover:scale-[1.02] col-span-2 md:col-span-1">
          <div class="flex items-center gap-2 sm:gap-3 mb-2 sm:mb-4 opacity-70">
            <BookOpen :size="16" class="sm:w-5 sm:h-5" />
            <span class="text-[10px] sm:text-xs font-bold uppercase tracking-wider sm:tracking-widest">Sources Quoted</span>
          </div>
          <p class="text-2xl sm:text-4xl font-black text-white">{{ stats.books }}</p>
        </div>
      </div>

      <!-- Filter Bar (Desktop) -->
      <div class="hidden lg:block space-y-6">
        <div class="flex flex-col lg:flex-row gap-4">
          <div class="flex-1 relative group">
            <Search class="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" :size="20" />
            <input
              type="text"
              v-model="searchQuery"
              @input="handleSearch"
              placeholder="Search across content, books, or authors..."
              class="w-full bg-slate-900/50 border-2 border-slate-800 rounded-2xl px-14 py-4 text-white focus:border-indigo-500 transition-all outline-none"
            />
          </div>

          <div class="flex gap-4">
            <button
              @click="toggleFavorites"
              :class="showFavorites ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-800 text-slate-400 hover:border-slate-700'"
              class="flex items-center gap-3 px-6 py-4 rounded-2xl border-2 transition-all"
            >
              <Star :size="18" :fill="showFavorites ? 'currentColor' : 'none'" />
              <span class="font-bold">Favorites</span>
            </button>
          </div>
        </div>

        <div v-if="selectedTag" class="flex items-center gap-2">
          <span class="text-xs font-bold text-slate-500 uppercase tracking-widest mr-2">Filtered by:</span>
          <button
            @click="selectedTag = null"
            class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-400 text-sm font-bold"
          >
            #{{ selectedTag }}
            <Plus class="rotate-45" :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="max-w-7xl mx-auto px-6">
      <!-- Loading State -->
      <div v-if="quotesStore.loading" class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div v-for="i in 6" :key="i" class="space-y-3">
          <Skeleton class="h-64 rounded-3xl" />
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="displayedQuotes.length === 0" class="flex flex-col items-center justify-center py-40 text-center animate-in fade-in duration-500">
        <div class="w-20 h-20 rounded-full bg-slate-900/50 border border-slate-800 flex items-center justify-center mb-6">
          <Sparkles :size="32" class="text-slate-700" />
        </div>
        <h3 class="text-2xl font-bold text-white mb-2">No insights found</h3>
        <p class="text-slate-500 max-w-sm">
          Adjust your filters or capture your first quote to start building your collection.
        </p>
        <button
          v-if="searchQuery || selectedTag || showFavorites"
          @click="clearFilters"
          class="mt-6 text-indigo-400 font-bold hover:text-indigo-300 transition-colors"
        >
          Clear all filters
        </button>
      </div>

      <!-- Quotes Grid -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div
          v-for="quote in displayedQuotes"
          :key="quote.id"
          class="group relative glass bg-slate-900/40 rounded-2xl sm:rounded-3xl p-5 sm:p-8 border border-slate-800/50 hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/5"
        >
          <!-- Quote Mark -->
          <div class="absolute -top-4 -left-2 text-7xl text-indigo-500/10 font-serif pointer-events-none select-none">"</div>

          <div class="relative space-y-6">
            <!-- Quote Content -->
            <p class="text-quote font-medium text-slate-100 leading-relaxed italic font-serif whitespace-pre-wrap">
              {{ quote.text }}
            </p>

            <!-- Book Info -->
            <div class="flex items-start gap-2 sm:gap-3 pt-3 border-t border-slate-800/50">
              <!-- Book Cover or Placeholder -->
              <div
                v-if="quote.book_cover"
                @click="handleBookClick(quote)"
                :class="quote.book ? 'cursor-pointer hover:scale-105 transition-transform' : ''"
                class="w-8 h-12 sm:w-9 sm:h-13 rounded-md shadow-lg overflow-hidden flex-shrink-0"
              >
                <img :src="quote.book_cover" :alt="quote.book_title" class="w-full h-full object-cover" />
              </div>
              <div
                v-else
                @click="handleBookClick(quote)"
                :class="quote.book ? 'cursor-pointer hover:bg-slate-700 transition-colors' : ''"
                class="w-8 h-12 sm:w-9 sm:h-13 bg-slate-800 rounded-md flex items-center justify-center flex-shrink-0"
              >
                <Bookmark :size="14" class="text-slate-600" />
              </div>
              <div class="flex-1 min-w-0 space-y-1.5">
                <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2 min-w-0">
                  <h4
                    @click="handleBookClick(quote)"
                    :class="quote.book ? 'cursor-pointer hover:text-indigo-400 transition-colors' : ''"
                    class="text-white font-bold text-sm flex items-center gap-1.5 group/title"
                  >
                    <span class="truncate">{{ quote.book_title || 'Unknown Book' }}</span>
                    <ExternalLink v-if="quote.book" :size="12" class="opacity-0 group-hover/title:opacity-100 transition-opacity flex-shrink-0" />
                  </h4>
                  <span class="text-slate-600 hidden sm:inline flex-shrink-0">·</span>
                  <p class="text-indigo-400 font-medium text-sm truncate">{{ quote.book_author || 'Unknown Author' }}</p>
                </div>
                <div class="flex flex-wrap items-center gap-2 text-xs">
                  <!-- Chapter and Page -->
                  <template v-if="quote.chapter || quote.page_number">
                    <span v-if="quote.chapter" class="flex items-center gap-1 text-slate-500 font-bold uppercase tracking-wider">
                      <span class="text-slate-600">Ch.</span> {{ quote.chapter }}
                    </span>
                    <span v-if="quote.page_number" class="flex items-center gap-1 text-slate-500 font-bold uppercase tracking-wider">
                      <span class="text-slate-600">Pg.</span> {{ quote.page_number }}
                    </span>
                  </template>

                  <!-- Tags inline -->
                  <template v-if="quote.tags && quote.tags.length > 0">
                    <span v-if="quote.chapter || quote.page_number" class="text-slate-700">|</span>
                    <button
                      v-for="(tag, i) in quote.tags"
                      :key="i"
                      @click="filterByTag(tag.id)"
                      class="px-2 py-0.5 rounded-full bg-slate-800/50 border border-slate-700 text-xs font-semibold text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all"
                    >
                      #{{ tag.name }}
                    </button>
                  </template>
                </div>
              </div>
            </div>

            <!-- Notes Toggle -->
            <div v-if="quote.note" class="pt-2">
              <button
                @click="toggleNotes(quote.id)"
                class="text-xs font-bold text-slate-500 flex items-center gap-1.5 hover:text-slate-300 transition-colors"
              >
                <MoreHorizontal :size="14" />
                {{ expandedNotes.has(quote.id) ? 'Hide personal notes' : 'Read personal notes' }}
              </button>
              <p
                v-if="expandedNotes.has(quote.id)"
                class="mt-3 p-4 rounded-xl bg-slate-950/50 border border-slate-800 text-slate-400 text-sm leading-relaxed animate-in slide-in-from-top-2"
              >
                {{ quote.note }}
              </p>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-between pt-4">
              <div class="flex items-center gap-1">
                <button
                  @click="toggleFavorite(quote)"
                  :class="quote.is_favorite ? 'text-amber-400 bg-amber-400/10' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'"
                  class="p-2 rounded-full transition-all"
                >
                  <Star :size="20" :fill="quote.is_favorite ? 'currentColor' : 'none'" />
                </button>
                <button
                  @click="copyQuote(quote)"
                  class="p-2 rounded-full text-slate-500 hover:text-indigo-400 hover:bg-slate-800 transition-all"
                >
                  <Copy :size="20" />
                </button>
              </div>

              <div class="flex items-center gap-2">
                <button
                  @click="openEditDialog(quote)"
                  class="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all flex items-center gap-2"
                >
                  <Edit :size="14" /> Edit
                </button>
                <button
                  @click="deleteQuote(quote)"
                  class="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-all flex items-center gap-2"
                >
                  <Trash2 :size="14" /> Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Quote Dialog -->
    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent class="max-w-2xl glass border-slate-700 max-h-[85vh] overflow-y-auto">
        <DialogHeader class="border-b border-slate-800 pb-3 mb-4">
          <DialogTitle class="text-lg font-bold flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Edit :size="16" class="text-white" />
            </div>
            Edit Quote
          </DialogTitle>
          <DialogDescription class="sr-only">
            Edit this quote from your library
          </DialogDescription>
        </DialogHeader>

        <form @submit.prevent="handleEditQuote" class="space-y-5">
          <!-- Quote Content -->
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
              <component :is="AlignLeft" :size="12" /> The Quote
            </label>
            <Textarea
              v-model="editQuote.text"
              placeholder="Paste the brilliant words here..."
              rows="4"
              required
              class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 transition-all resize-none"
            />
          </div>

          <!-- Book Info Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-2 relative">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                <component :is="Bookmark" :size="12" /> Book Title
              </label>
              <input
                :value="editBookSearchQuery || editQuote.book_title"
                @input="handleEditBookInputChange"
                @focus="showEditBookDropdown = editBookSearchResults.length > 0"
                placeholder="Start typing to search your books..."
                required
                class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all outline-none"
                autocomplete="off"
              />
              <!-- Autocomplete Dropdown -->
              <div
                v-if="showEditBookDropdown && editBookSearchResults.length > 0"
                class="absolute z-50 w-full mt-1 bg-slate-800 border-2 border-slate-700 rounded-xl shadow-2xl max-h-64 overflow-y-auto"
              >
                <button
                  v-for="userBook in editBookSearchResults"
                  :key="userBook.id"
                  type="button"
                  @click="selectEditBook(userBook)"
                  class="w-full flex items-start gap-3 p-3 hover:bg-slate-700 transition-colors text-left border-b border-slate-700/50 last:border-0"
                >
                  <div class="w-8 h-12 rounded overflow-hidden flex-shrink-0 bg-slate-700 flex items-center justify-center">
                    <img
                      v-if="userBook.book.cover_image"
                      :src="userBook.book.cover_image"
                      :alt="userBook.book.title"
                      class="w-full h-full object-cover"
                    />
                    <BookOpen v-else :size="14" class="text-slate-500" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-bold text-white truncate">{{ userBook.book.title }}</p>
                    <p class="text-xs text-slate-400 truncate">{{ userBook.book.authors?.[0]?.name || 'Unknown Author' }}</p>
                  </div>
                </button>
              </div>
              <p v-if="isSearchingEditBooks" class="text-xs text-slate-500 mt-1">Searching...</p>
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                <component :is="Hash" :size="12" /> Author
              </label>
              <Input
                v-model="editQuote.book_author"
                placeholder="The creative mind..."
                class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <!-- Metadata Grid -->
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Page</label>
              <Input
                v-model.number="editQuote.page_number"
                type="number"
                placeholder="e.g. 142"
                class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
              />
            </div>
            <div class="space-y-2">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Chapter</label>
              <Input
                v-model="editQuote.chapter"
                placeholder="e.g. Chapter IV"
                class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
              />
            </div>
            <div class="space-y-2 md:col-span-1 col-span-2">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Tags</label>
              <Input
                v-model="editQuote.tags_input"
                placeholder="philosophy, life, love"
                class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
              />
            </div>
          </div>

          <!-- Personal Notes -->
          <div class="space-y-2">
            <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Personal Notes</label>
            <Textarea
              v-model="editQuote.note"
              placeholder="Why did this resonate with you?"
              rows="2"
              class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-600 focus:border-indigo-500 transition-all resize-none"
            />
          </div>

          <!-- Toggles -->
          <div class="flex flex-wrap gap-3 pt-2">
            <button
              type="button"
              @click="editQuote.is_favorite = !editQuote.is_favorite"
              :class="editQuote.is_favorite ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-500'"
              class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all text-sm"
            >
              <component :is="Star" :size="16" :fill="editQuote.is_favorite ? 'currentColor' : 'none'" />
              <span class="font-semibold">Favorite</span>
            </button>
            <button
              type="button"
              @click="editQuote.is_public = !editQuote.is_public"
              :class="editQuote.is_public ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-700 text-slate-500'"
              class="flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all text-sm"
            >
              <component :is="editQuote.is_public ? Globe : Lock" :size="16" />
              <span class="font-semibold">{{ editQuote.is_public ? 'Public' : 'Private' }}</span>
            </button>
          </div>

          <!-- Footer Buttons -->
          <div class="flex gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              @click="isEditDialogOpen = false"
              class="flex-1 px-4 py-3 rounded-lg border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="flex-[2] px-4 py-3 rounded-lg bg-indigo-500 text-white text-sm font-semibold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
            >
              <component :is="Save" :size="18" />
              Save Changes
            </button>
          </div>
        </form>
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
