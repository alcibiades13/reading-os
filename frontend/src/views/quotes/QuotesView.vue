<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuotesStore } from '@/stores/quotesStore'
import { Skeleton } from '@/components/ui/skeleton'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Plus, BookOpen, Edit, Trash2, Star, Copy, Bookmark, MoreHorizontal, Sparkles, Type, Search, AlignLeft, Hash, Globe, Lock, Save, ExternalLink } from 'lucide-vue-next'

const router = useRouter()
const quotesStore = useQuotesStore()

const searchQuery = ref('')
const selectedTag = ref(null)
const showFavorites = ref(false)
const isCreateDialogOpen = ref(false)

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
  is_public: false,
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
  await quotesStore.updateQuote(quote.id, {
    is_favorite: !quote.is_favorite,
  })
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
</script>

<template>
  <div class="animate-in fade-in duration-700 pb-20">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto pt-12 pb-8 px-6">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
        <header>
          <div class="flex items-center gap-2 sm:gap-3 mb-4">
            <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Type :size="18" class="sm:w-6 sm:h-6 text-indigo-400" />
            </div>
            <span class="text-[10px] sm:text-sm font-bold text-indigo-400 uppercase tracking-[0.2em] sm:tracking-[0.3em]">Insights & Quotes</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
            The <span class="text-indigo-500">Collected</span> Mind
          </h1>
          <p class="text-slate-400 text-subtitle max-w-2xl leading-relaxed">
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
                <div class="space-y-2">
                  <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
                    <component :is="Bookmark" :size="12" /> Book Title
                  </label>
                  <Input
                    v-model="newQuote.book_title"
                    placeholder="Which masterpiece is this from?"
                    required
                    class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
                  />
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

      <!-- Stats Grid -->
      <div class="grid grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6 mb-12">
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

      <!-- Filter Bar -->
      <div class="space-y-6">
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
            <p class="text-quote font-medium text-slate-100 leading-relaxed italic font-serif">
              {{ quote.text }}
            </p>

            <!-- Book Info -->
            <div class="flex flex-col sm:flex-row items-start gap-3 sm:gap-4 pt-4 border-t border-slate-800/50">
              <div
                v-if="quote.book_cover"
                @click="handleBookClick(quote)"
                :class="quote.book ? 'cursor-pointer hover:scale-105 transition-transform' : ''"
                class="w-10 h-15 sm:w-12 sm:h-18 rounded-lg shadow-lg overflow-hidden flex-shrink-0"
              >
                <img :src="quote.book_cover" :alt="quote.book_title" class="w-full h-full object-cover" />
              </div>
              <div
                v-else
                @click="handleBookClick(quote)"
                :class="quote.book ? 'cursor-pointer hover:bg-slate-700 transition-colors' : ''"
                class="w-10 h-15 sm:w-12 sm:h-18 bg-slate-800 rounded-lg flex items-center justify-center flex-shrink-0"
              >
                <Bookmark :size="18" class="sm:w-5 sm:h-5 text-slate-600" />
              </div>
              <div class="flex-1 min-w-0 space-y-2">
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
                <div class="flex flex-wrap gap-2 text-xs text-slate-500 font-bold uppercase tracking-wider">
                  <span v-if="quote.chapter" class="flex items-center gap-1">
                    <span class="text-slate-600">Ch.</span> {{ quote.chapter }}
                  </span>
                  <span v-if="quote.page_number" class="flex items-center gap-1">
                    <span class="text-slate-600">Pg.</span> {{ quote.page_number }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Tags -->
            <div v-if="quote.tags && quote.tags.length > 0" class="flex flex-wrap gap-2">
              <button
                v-for="(tag, i) in quote.tags"
                :key="i"
                @click="filterByTag(tag.id)"
                class="px-3 py-1 rounded-full bg-slate-800/50 border border-slate-700 text-xs font-semibold text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all"
              >
                #{{ tag.name }}
              </button>
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
                <button class="px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all flex items-center gap-2">
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
  </div>
</template>
