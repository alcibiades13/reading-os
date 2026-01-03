<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useAuthStore } from '@/stores/authStore'
import { useToast } from '@/composables/useToast'
import StarRating from '@/components/ui/StarRating.vue'
import BookEditModal from '@/components/BookEditModal.vue'
import {
  ArrowLeft, BookOpen, Calendar, Globe, Hash, Building2,
  Heart, Share2, Plus, Users, Sparkles, Bookmark, SquarePen, Eye, CheckCircle, Edit3, Copy, Brain
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const authStore = useAuthStore()
const { addToast } = useToast()

// Route params
const bookId = computed(() => route.params.id)

// State
const showFullDesc = ref(false)
const isQuoteModalOpen = ref(false)
const isEditModalOpen = ref(false)
const currentPageInput = ref(0)
const reviewInput = ref('')
const coverLoaded = ref(false)
const currentCoverUrl = ref('')

// Helper to strip HTML and get text preview
const getReviewPreview = (htmlContent, maxLength = 300) => {
  if (!htmlContent) return ''
  const div = document.createElement('div')
  div.innerHTML = htmlContent
  const text = div.textContent || div.innerText || ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// Computed - Book data
const book = computed(() => booksStore.currentBook)
const userBook = computed(() => {
  const numericBookId = parseInt(bookId.value)
  return userBooksStore.books.find(ub => ub.book?.id === numericBookId)
})
const bookQuotes = computed(() => {
  if (!Array.isArray(quotesStore.quotes)) return []
  const numericBookId = parseInt(bookId.value)
  // Backend already filters by book when we call fetchQuotes({ book: bookId })
  // But also filter locally in case quotes from other books are in store
  return quotesStore.quotes.filter(q => {
    // book is just the ID (number), not an object
    return q.book === numericBookId
  })
})

// Computed - Library status
const isInLibrary = computed(() => !!userBook.value)
const currentStatus = computed(() => userBook.value?.status || null)
const personalRating = computed({
  get: () => {
    const rating = userBook.value?.rating
    return rating ? parseFloat(rating) : 0
  },
  set: async (newRating) => {
    if (!userBook.value) return
    // Ensure rating is sent as string to preserve decimal precision
    await userBooksStore.updateBook(userBook.value.id, { rating: String(newRating) })
  }
})
const isFavorite = computed(() => userBook.value?.is_favorite || false)

// Computed - Progress
const totalPages = computed(() => {
  const pages = book.value?.pages
  // If pages is null/undefined/0, use a reasonable default
  return pages && pages > 0 ? pages : 300
})
const currentPage = computed(() => userBook.value?.current_page || 0)
const progressPercent = computed(() => {
  if (!totalPages.value) return 0
  return Math.min(100, Math.round((currentPage.value / totalPages.value) * 100))
})

// Computed - Book meta
const coverUrl = computed(() => {
  if (!book.value) return ''
  return book.value.cover_image ||
    `https://via.placeholder.com/600x900/1E293B/64748B?text=${encodeURIComponent(book.value.title || 'Book')}`
})

const authorsString = computed(() => {
  if (!book.value?.authors || book.value.authors.length === 0) return 'Unknown Author'
  return book.value.authors.map(a => a.name).join(', ')
})

const publishedYear = computed(() => {
  if (!book.value?.published_date) return '---'
  return book.value.published_date.split('-')[0]
})

const averageRating = computed(() => book.value?.average_rating || 0)
const ratingsCount = computed(() => book.value?.ratings_count || 0)

const descriptionHtml = computed(() => {
  return book.value?.description || 'No description available.'
})

const formattedStartedAt = computed(() => {
  if (!userBook.value?.started_at) return null
  const date = new Date(userBook.value.started_at)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const formattedFinishedAt = computed(() => {
  if (!userBook.value?.finished_at) return null
  const date = new Date(userBook.value.finished_at)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

// Lifecycle
onMounted(async () => {
  coverLoaded.value = false

  const promises = [
    booksStore.fetchBook(bookId.value),
    quotesStore.fetchQuotes({ book: bookId.value })
  ]

  // Only fetch user books if store is empty
  if (userBooksStore.books.length === 0) {
    promises.push(userBooksStore.fetchBooks())
  }

  await Promise.all(promises)

  // Initialize inputs
  if (userBook.value) {
    currentPageInput.value = userBook.value.current_page || 0
    reviewInput.value = userBook.value.review || ''
  }

  window.scrollTo(0, 0)
})

// Reset cover loaded state when bookId or coverUrl changes
watch(bookId, async (newId, oldId) => {
  // IMMEDIATELY clear the current book to prevent showing old data
  booksStore.currentBook = null
  coverLoaded.value = false
  await nextTick()

  await booksStore.fetchBook(newId)
  quotesStore.fetchQuotes({ book: newId })
}, { flush: 'sync' })

watch(coverUrl, async (newUrl, oldUrl) => {
  if (newUrl !== oldUrl && newUrl !== currentCoverUrl.value) {
    coverLoaded.value = false
    currentCoverUrl.value = newUrl
    await nextTick()
  }
})

// Watch for userBook changes to update inputs
watch(userBook, (newVal, oldVal) => {
  if (newVal) {
    // Only update if current_page actually changed from the backend
    // This prevents resetting the input while user is typing
    if (!oldVal || newVal.current_page !== oldVal.current_page) {
      currentPageInput.value = newVal.current_page ?? 0
    }
    reviewInput.value = newVal.review || ''
  }
}, { deep: true })

// Handlers
const handleCoverLoad = () => {
  console.log('Image @load fired, setting coverLoaded to true')
  coverLoaded.value = true
}

const handleBack = () => {
  router.back()
}

const handleAddToLibrary = async () => {
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  await userBooksStore.addBook({
    book: bookId.value,
    status: 'want_to_read'
  })

  // Refresh to get the newly added book
  await userBooksStore.fetchBooks()
}

const handleStatusChange = async (newStatus) => {
  if (!userBook.value) {
    // Add to library with this status
    await userBooksStore.addBook({
      book: bookId.value,
      status: newStatus
    })
  } else {
    // Update existing
    await userBooksStore.updateBook(userBook.value.id, {
      status: newStatus
    })
  }
}

const handleReviewUpdate = async () => {
  if (!userBook.value) return

  await userBooksStore.updateBook(userBook.value.id, {
    review: reviewInput.value
  })
}

const handleProgressUpdate = async () => {
  if (!userBook.value) return

  // Validate and clamp the input value
  let validatedPage = Math.max(0, Math.min(currentPageInput.value, totalPages.value))
  currentPageInput.value = validatedPage

  // Calculate percentage locally before the update
  const percent = totalPages.value ? Math.min(100, Math.round((validatedPage / totalPages.value) * 100)) : 0

  const result = await userBooksStore.updateBook(userBook.value.id, {
    current_page: validatedPage
  })

  if (result.success) {
    // Show success toast
    addToast(`Progress updated: ${validatedPage}/${totalPages.value} pages (${percent}%)`, 'success')
  }
}

const handleToggleFavorite = async () => {
  if (!userBook.value) return

  await userBooksStore.updateBook(userBook.value.id, {
    is_favorite: !isFavorite.value
  })
}

const handleAddQuote = () => {
  isQuoteModalOpen.value = true
  // TODO: Implement quote modal
  // For now, navigate to quotes page
  router.push(`/quotes/new?book=${bookId.value}`)
}

const handleShareProgress = () => {
  // TODO: Implement share functionality
  alert('Share functionality coming soon!')
}

const getStatusBadgeClass = (status) => {
  if (status === 'read') return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
  if (status === 'currently_reading') return 'bg-sky-500/10 text-sky-400 border-sky-500/20'
  return 'bg-slate-800 text-slate-400 border-slate-700'
}

const getStatusLabel = (status) => {
  const labels = {
    'want_to_read': 'Want to Read',
    'currently_reading': 'Currently Reading',
    'read': 'Finished',
    'abandoned': 'Abandoned'
  }
  return labels[status] || status
}

const handleEditBook = () => {
  isEditModalOpen.value = true
}

const handleSaveBook = async (updatedData) => {
  try {
    await booksStore.updateBook(bookId.value, updatedData)
    isEditModalOpen.value = false
    addToast('Book updated successfully!', 'success')

    // Refresh book data
    await booksStore.fetchBook(bookId.value)
  } catch (error) {
    addToast('Failed to update book', 'error')
  }
}

const handleStudyMode = () => {
  router.push({
    path: `/books/${bookId.value}/study`,
    query: { title: book.value?.title || 'Study Session' }
  })
}
</script>

<script>
// Inline helper components
import { defineComponent, h } from 'vue'
import { Star, Bookmark, Heart, Copy } from 'lucide-vue-next'

export const MetaBox = defineComponent({
  props: {
    icon: [Object, Function],
    label: String,
    value: String
  },
  setup(props) {
    return () => h('div', { class: 'p-4 rounded-2xl glass border-slate-800/50' }, [
      h('div', { class: 'flex items-center gap-2 text-slate-500 mb-1' }, [
        h(props.icon, { size: 18 }),
        h('span', { class: 'text-[10px] font-bold uppercase tracking-widest' }, props.label)
      ]),
      h('p', { class: 'text-slate-100 font-bold truncate' }, props.value)
    ])
  }
})

export const FriendActivity = defineComponent({
  props: {
    user: String,
    status: String,
    rating: Number,
    review: String
  },
  setup(props) {
    const initials = props.user.split(' ').map(n => n[0]).join('')
    return () => h('div', { class: 'flex gap-4 p-4 rounded-2xl hover:bg-slate-900/50 transition-colors border border-transparent hover:border-slate-800' }, [
      h('div', { class: 'w-10 h-10 rounded-full bg-slate-800 flex-shrink-0 border border-slate-700 flex items-center justify-center font-bold text-slate-400 text-xs' }, initials),
      h('div', { class: 'flex-1 min-w-0' }, [
        h('div', { class: 'flex items-center justify-between mb-1' }, [
          h('span', { class: 'font-bold text-white text-sm' }, props.user),
          h('span', { class: 'text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-500 font-bold uppercase' }, props.status)
        ]),
        props.rating > 0 ? h('div', { class: 'flex items-center gap-1 mb-2' }, [
          h(Star, { size: 10, class: 'text-amber-400 fill-current' }),
          h('span', { class: 'text-[10px] font-bold text-amber-400' }, props.rating.toFixed(1))
        ]) : null,
        h('p', { class: 'text-xs text-slate-400 line-clamp-2 italic' }, `"${props.review}"`)
      ])
    ])
  }
})

export const QuoteCard = defineComponent({
  props: {
    quote: Object,
    bookTitle: String,
    bookAuthors: String
  },
  setup(props) {
    const handleCopy = () => {
      const text = `"${props.quote.text}" — ${props.bookTitle} by ${props.bookAuthors}`
      navigator.clipboard.writeText(text)
    }

    return () => h('div', { class: 'p-6 rounded-2xl glass border-slate-800/50 hover:border-indigo-500/30 transition-all space-y-4' }, [
      h('blockquote', { class: 'text-quote font-serif text-slate-200 italic leading-relaxed border-l-4 border-indigo-500 pl-4' }, `"${props.quote.text}"`),
      props.quote.note ? h('div', { class: 'text-sm text-slate-400 pl-4' }, [
        h('span', { class: 'font-bold text-slate-500' }, 'Note:'),
        ` ${props.quote.note}`
      ]) : null,
      h('div', { class: 'flex items-center justify-between pt-4 border-t border-slate-800/50' }, [
        h('div', { class: 'flex items-center gap-2' }, [
          h(Bookmark, { size: 14, class: 'text-slate-500' }),
          h('span', { class: 'text-xs text-slate-500' }, `Page ${props.quote.page_number || 'N/A'}`)
        ]),
        h('div', { class: 'flex gap-2' }, [
          h('button', {
            class: `p-2 rounded-lg hover:bg-slate-800 transition-colors ${props.quote.is_favorite ? 'text-rose-400' : 'text-slate-500'}`
          }, [
            h(Heart, { size: 16, fill: props.quote.is_favorite ? 'currentColor' : 'none' })
          ]),
          h('button', {
            class: 'p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-500 hover:text-indigo-400',
            onClick: handleCopy
          }, [
            h(Copy, { size: 16 })
          ])
        ])
      ])
    ])
  }
})
</script>

<template>
  <div v-if="book" class="max-w-7xl mx-auto px-6 py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">

    <!-- Back Button -->
    <button
      @click="handleBack"
      class="flex items-center gap-2 text-slate-400 hover:text-indigo-400 mb-10 transition-colors font-bold group"
    >
      <ArrowLeft :size="20" class="group-hover:-translate-x-1 transition-transform" />
      Back to Results
    </button>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">

      <!-- Left Column - Cover & Main Info -->
      <div class="lg:col-span-4 space-y-8">
        <div class="relative aspect-[2/3] w-full max-w-[200px] sm:max-w-xs mx-auto lg:max-w-none rounded-3xl overflow-hidden shadow-2xl ring-1 ring-white/10 group">
          <!-- Skeleton loader -->
          <div v-if="!coverLoaded" class="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-slate-800 animate-pulse z-10" />

          <img
            :key="coverUrl"
            :src="coverUrl"
            :alt="book.title"
            @load="handleCoverLoad"
            v-show="coverLoaded"
            class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950/10 to-transparent pointer-events-none" />

          <button
            @click="handleToggleFavorite"
            :class="[
              'absolute top-4 right-4 sm:top-6 sm:right-6 p-3 sm:p-4 rounded-full glass transition-all',
              isFavorite
                ? 'text-rose-500 bg-rose-500/10 border-rose-500/30'
                : 'text-white hover:text-rose-400'
            ]"
          >
            <Heart :size="20" class="sm:w-6 sm:h-6" :fill="isFavorite ? 'currentColor' : 'none'" />
          </button>
        </div>

        <!-- Quick Meta Grid -->
        <div class="grid grid-cols-2 gap-4">
          <MetaBox :icon="BookOpen" label="Pages" :value="book.pages?.toString() || '---'" />
          <MetaBox :icon="Globe" label="Language" :value="book.language?.toUpperCase() || '---'" />
          <MetaBox :icon="Calendar" label="Published" :value="publishedYear" />
          <MetaBox :icon="Hash" label="Format" value="Paperback" />
        </div>

        <!-- Publisher Info -->
        <div class="p-6 rounded-2xl glass border-slate-800/50 space-y-4">
          <div class="flex items-center gap-3 text-slate-400">
            <Building2 :size="18" />
            <span class="text-xs font-bold uppercase tracking-widest">Publisher</span>
          </div>
          <p class="text-slate-100 font-semibold">{{ book.publisher?.name || 'Unknown Publisher' }}</p>
          <div class="pt-4 border-t border-slate-800/50">
            <span class="text-[10px] text-slate-500 font-bold uppercase block mb-1">ISBN-13</span>
            <code class="text-xs text-indigo-400">{{ book.isbn || 'N/A' }}</code>
          </div>
        </div>

        <!-- Edit Book Button -->
        <button
          @click="handleEditBook"
          class="w-full p-4 rounded-2xl bg-indigo-500/10 border-2 border-indigo-500/20 hover:border-indigo-500/40 hover:bg-indigo-500/20 transition-all flex items-center justify-center gap-2 text-indigo-400 font-bold text-sm group"
        >
          <Edit3 :size="18" class="group-hover:rotate-12 transition-transform" />
          Edit Book Details
        </button>
      </div>

      <!-- Right Column - Interaction & Content -->
      <div class="lg:col-span-8 space-y-12">

        <!-- Header Info -->
        <section>
          <div v-if="book.genres?.length > 0" class="flex flex-wrap gap-2 mb-6">
            <span
              v-for="genre in book.genres"
              :key="genre.id"
              class="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold"
            >
              {{ genre.name }}
            </span>
          </div>
          <h1 class="text-2xl sm:text-3xl lg:text-4xl font-black text-white leading-tight mb-4">{{ book.title }}</h1>
          <p class="text-base sm:text-lg lg:text-xl text-slate-400 font-medium">
            by <span class="text-indigo-400 hover:underline cursor-pointer">{{ authorsString }}</span>
          </p>

          <div class="flex items-center gap-4 mt-6">
            <StarRating :model-value="averageRating" :readonly="true" :size="24" :show-value="true" />
            <span class="text-slate-500 text-sm">({{ ratingsCount }} ratings on Google Books)</span>
          </div>
        </section>

        <!-- Description -->
        <section class="space-y-4">
          <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">About the Book</h2>
          <div :class="['text-slate-300 leading-relaxed space-y-4 relative', !showFullDesc ? 'max-h-48 overflow-hidden' : '']">
            <div v-html="descriptionHtml" />
            <div v-if="!showFullDesc && descriptionHtml.length > 300" class="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-slate-950 to-transparent" />
          </div>
          <button
            v-if="descriptionHtml.length > 300"
            @click="showFullDesc = !showFullDesc"
            class="text-indigo-400 font-bold text-sm hover:text-indigo-300 transition-colors"
          >
            {{ showFullDesc ? 'Show Less' : 'Read More' }}
          </button>
        </section>

        <!-- My Reading - Interaction Hub -->
        <section class="p-8 rounded-3xl glass border-indigo-500/20 bg-indigo-500/5 relative overflow-hidden">
          <div class="absolute top-0 right-0 p-8 opacity-10">
            <Sparkles :size="120" class="text-indigo-500" />
          </div>

          <div class="relative z-10 space-y-8">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <h2 class="text-xl font-bold text-white mb-1">My Reading</h2>
                <p class="text-slate-400 text-sm">Track your progress and thoughts</p>
              </div>

              <div class="flex items-center gap-3">
                <button
                  v-if="!isInLibrary"
                  @click="handleAddToLibrary"
                  class="px-8 py-4 rounded-xl bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-3"
                >
                  <Plus :size="20" />
                  Add to Library
                </button>

                <div v-else class="flex items-center gap-3">
                  <div
                    :class="[
                      'px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider border',
                      getStatusBadgeClass(currentStatus)
                    ]"
                  >
                    {{ getStatusLabel(currentStatus) }}
                  </div>
                  <select
                    :value="currentStatus"
                    @change="handleStatusChange($event.target.value)"
                    class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs font-bold text-slate-300 outline-none focus:border-indigo-500"
                  >
                    <option value="want_to_read">Want to Read</option>
                    <option value="currently_reading">Currently Reading</option>
                    <option value="read">Finished</option>
                    <option value="abandoned">Abandoned</option>
                  </select>
                </div>
              </div>
            </div>

            <div v-if="isInLibrary" :key="`library-${userBook?.id || 'new'}`" class="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-slate-800/50">
              <!-- Rating (only for finished/abandoned) -->
              <div v-if="currentStatus === 'read' || currentStatus === 'abandoned'" class="space-y-6">
                <div>
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">My Rating</label>
                  <StarRating
                    v-if="userBook"
                    :key="`rating-${userBook.id}`"
                    v-model="personalRating"
                    :readonly="false"
                    :size="28"
                    :show-value="true"
                  />
                  <p class="text-[10px] text-slate-500 mt-2">Click once for full star, double-click for half star</p>
                </div>

                <!-- Reading Dates -->
                <div v-if="formattedStartedAt || formattedFinishedAt" class="p-4 rounded-xl bg-slate-950/50 border border-slate-800 space-y-3">
                  <div class="flex items-center gap-2 mb-2">
                    <Calendar :size="14" class="text-slate-500" />
                    <span class="text-xs font-bold text-slate-500 uppercase tracking-widest">Reading Journey</span>
                  </div>

                  <div v-if="formattedStartedAt" class="flex items-center justify-between">
                    <span class="text-xs text-slate-500">Started</span>
                    <span class="text-sm font-semibold text-slate-300">{{ formattedStartedAt }}</span>
                  </div>

                  <div v-if="formattedFinishedAt" class="flex items-center justify-between">
                    <span class="text-xs text-slate-500">Finished</span>
                    <span class="text-sm font-semibold text-emerald-400">{{ formattedFinishedAt }}</span>
                  </div>
                </div>

                <!-- Edit My Activity Button (Mobile) -->
                <button
                  @click="router.push(`/books/${bookId}/review`)"
                  class="md:hidden w-full py-3 rounded-lg border border-slate-700 text-slate-400 text-xs font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center justify-center gap-2 group/btn"
                >
                  <SquarePen :size="14" class="transition-colors group-hover/btn:text-indigo-400" />
                  <span class="transition-colors group-hover/btn:text-indigo-400">Edit My Activity</span>
                </button>
              </div>

              <!-- Right Column: Edit Button (Desktop) / Progress Tracking -->
              <div class="space-y-6">
                <!-- Edit My Activity Button (Desktop, only for finished/abandoned) -->
                <button
                  v-if="currentStatus === 'read' || currentStatus === 'abandoned'"
                  @click="router.push(`/books/${bookId}/review`)"
                  class="hidden md:flex w-full py-3 rounded-lg border border-slate-700 text-slate-400 text-xs font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all items-center justify-center gap-2 group/btn"
                >
                  <SquarePen :size="14" class="transition-colors group-hover/btn:text-indigo-400" />
                  <span class="transition-colors group-hover/btn:text-indigo-400">Edit My Activity</span>
                </button>
                <div v-if="currentStatus === 'currently_reading'" class="p-6 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-4">
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block">Reading Progress</label>

                  <div class="flex items-center gap-2">
                    <input
                      type="number"
                      v-model.number="currentPageInput"
                      @keyup.enter="handleProgressUpdate"
                      :min="0"
                      :max="totalPages"
                      class="w-20 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1 text-center font-bold text-indigo-400 outline-none focus:border-indigo-500 transition-colors"
                    />
                    <span class="text-slate-500 text-sm">/ {{ totalPages }} pages</span>
                    <button
                      @click="handleProgressUpdate"
                      class="px-3 py-1 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold rounded-lg transition-colors"
                    >
                      Save
                    </button>
                  </div>

                  <div class="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-indigo-500 rounded-full shadow-[0_0_10px_rgba(99,102,241,0.5)] transition-all duration-1000"
                      :style="{ width: `${progressPercent}%` }"
                    />
                  </div>

                  <div class="flex items-center justify-between">
                    <button
                      @click="handleStatusChange('read')"
                      class="px-4 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold hover:bg-emerald-500/20 transition-all flex items-center gap-2"
                    >
                      <CheckCircle :size="14" />
                      Mark as Completed
                    </button>
                    <div class="text-right">
                      <span class="text-indigo-400 font-black text-xl">{{ progressPercent }}%</span>
                      <p class="text-[10px] text-slate-500 font-medium">{{ currentPage }} / {{ totalPages }} pages</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- My Review Section (full width, only for finished/abandoned) -->
            <div v-if="isInLibrary && (currentStatus === 'read' || currentStatus === 'abandoned')" class="pt-8 border-t border-slate-800/50">
              <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-4">My Review</label>

              <!-- Show review preview if it exists -->
              <div v-if="reviewInput" class="space-y-4">
                <div class="p-6 rounded-2xl bg-slate-950/50 border border-slate-800">
                  <p class="text-sm text-slate-300 leading-relaxed italic">
                    "{{ getReviewPreview(reviewInput, 300) }}"
                  </p>
                </div>
                <div class="flex gap-3">
                  <button
                    @click="router.push(`/books/${bookId}/review-view`)"
                    class="flex-1 py-3 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-all flex items-center justify-center gap-2"
                  >
                    <Eye :size="16" />
                    Read Full Review
                  </button>
                  <button
                    @click="router.push(`/books/${bookId}/review`)"
                    class="flex-1 py-3 rounded-xl border border-slate-700 text-slate-400 font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center justify-center gap-2"
                  >
                    <SquarePen :size="16" />
                    Edit Review
                  </button>
                </div>
              </div>

              <!-- Show write button if no review -->
              <button
                v-else
                @click="router.push(`/books/${bookId}/review`)"
                class="w-full py-4 rounded-xl border-2 border-dashed border-slate-700 text-slate-400 font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center justify-center gap-3"
              >
                <SquarePen :size="18" />
                Write a Review
              </button>
            </div>
          </div>
        </section>

        <!-- Quotes Section -->
        <section class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">My Quotes</h2>
            <div class="flex items-center gap-3">
              <button
                @click="handleStudyMode"
                class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-sm hover:bg-indigo-500/20 transition-all"
              >
                <Brain :size="16" /> Study Mode
              </button>
              <button
                @click="handleAddQuote"
                class="flex items-center gap-2 text-indigo-400 font-bold text-sm hover:text-indigo-300 transition-colors"
              >
                <Plus :size="16" /> Add Quote
              </button>
            </div>
          </div>

          <div v-if="bookQuotes.length > 0" class="grid grid-cols-1 gap-6">
            <QuoteCard
              v-for="quote in bookQuotes.slice(0, 3)"
              :key="quote.id"
              :quote="quote"
              :book-title="book.title"
              :book-authors="authorsString"
            />
            <button
              v-if="bookQuotes.length > 3"
              class="w-full py-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 font-bold hover:text-white hover:bg-slate-800 transition-all"
            >
              View all {{ bookQuotes.length }} quotes from this book
            </button>
          </div>

          <div v-else class="p-12 rounded-3xl border-2 border-dashed border-slate-800 flex flex-col items-center text-center">
            <div class="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center mb-4 text-slate-600">
              <Bookmark :size="24" />
            </div>
            <p class="text-slate-500 text-sm italic">You haven't saved any quotes from this book yet.</p>
          </div>
        </section>

        <!-- Social - Community -->
        <section class="space-y-6 pt-12 border-t border-slate-900">
          <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] flex items-center gap-3">
            <Users :size="16" /> Community Activity
          </h2>

          <div class="flex flex-col gap-4">
            <FriendActivity
              user="Ana Kostić"
              status="Finished"
              :rating="9.0"
              review="This book changed my perspective on the world!"
            />
            <FriendActivity
              user="Marko Jovanović"
              status="Currently Reading"
              :rating="0"
              review="Just started, but looks promising..."
            />

            <div class="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/50 flex items-center justify-between">
              <p class="text-slate-400 text-sm">Be the first of your friends to recommend this book!</p>
              <button class="text-indigo-400 font-bold text-sm hover:underline">Invite Friends</button>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>

  <!-- Loading State -->
  <div v-else class="max-w-7xl mx-auto px-6 py-12">
    <div class="animate-pulse space-y-8">
      <div class="h-8 bg-slate-800 rounded w-48"></div>
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div class="lg:col-span-4">
          <div class="aspect-[2/3] bg-slate-800 rounded-3xl"></div>
        </div>
        <div class="lg:col-span-8 space-y-6">
          <div class="h-12 bg-slate-800 rounded w-3/4"></div>
          <div class="h-6 bg-slate-800 rounded w-1/2"></div>
          <div class="h-32 bg-slate-800 rounded"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Book Edit Modal -->
  <BookEditModal
    v-if="isEditModalOpen && book"
    :book="book"
    :open="isEditModalOpen"
    @close="isEditModalOpen = false"
    @save="handleSaveBook"
  />
</template>

<style>
.review-content {
  font-size: 14px !important;
}

.review-content * {
  font-size: 14px !important;
}

.review-content p {
  margin: 0.5em 0;
}

.review-content h1 {
  font-size: 1.3em !important;
  font-weight: bold;
  margin: 1em 0 0.5em;
}

.review-content h2 {
  font-size: 1.15em !important;
  font-weight: bold;
  margin: 1em 0 0.5em;
}

.review-content blockquote {
  border-left: 3px solid rgb(99 102 241);
  padding-left: 1em;
  padding-right: 0.8em;
  padding-top: 0.4em;
  padding-bottom: 0.4em;
  margin: 1em 0;
  font-style: italic;
  color: rgb(226 232 240);
  background: rgba(99, 102, 241, 0.05);
  border-radius: 0 6px 6px 0;
  font-family: 'Georgia', 'Garamond', 'Times New Roman', serif;
  position: relative;
}

.review-content blockquote::before {
  content: '"';
  font-size: 1.5em;
  color: rgb(99 102 241);
  position: absolute;
  left: 0.15em;
  top: -0.05em;
  font-family: Georgia, serif;
}

.review-content blockquote::after {
  content: '"';
  font-size: 1.5em;
  color: rgb(99 102 241);
  font-family: Georgia, serif;
}

.review-content ul {
  list-style-type: disc;
  margin-left: 1.5em;
  margin: 0.8em 0;
}

.review-content li {
  font-size: 14px !important;
}

.review-content a {
  color: rgb(99 102 241);
  text-decoration: underline;
}
</style>
