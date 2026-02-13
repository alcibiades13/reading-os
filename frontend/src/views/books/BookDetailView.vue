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
import BookDNASurvey from '@/components/recommendations/BookDNASurvey.vue'
import CommunityActivity from '@/components/books/CommunityActivity.vue'
import { recommendationsService } from '@/services/recommendationsService'
import { booksAPI } from '@/services/api'
import { getBookUrl, getBookUrlWithSuffix } from '@/utils/bookUrl'
import { getAuthorUrl } from '@/utils/authorUrl'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  ArrowLeft, ArrowRight, BookOpen, Calendar, Globe, Hash, Building2,
  Heart, Share2, Plus, Users, Sparkles, Bookmark, SquarePen, Eye, CheckCircle, Edit3, Copy, Brain, AlignLeft, Lock, Star, Dna, Search, Loader2, X, MoreHorizontal, ChevronDown
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const authStore = useAuthStore()
const { addToast } = useToast()

// Route params - extract numeric ID from slug format (e.g., "14-orkanski-visovi" -> "14")
const bookId = computed(() => {
  const param = route.params.id
  // If it contains a dash, extract just the numeric prefix
  if (param && param.includes('-')) {
    return param.split('-')[0]
  }
  return param
})

// State
const showFullDesc = ref(false)
const isQuoteModalOpen = ref(false)
const isEditModalOpen = ref(false)
const showDNASurvey = ref(false)
const isSwitchEditionModalOpen = ref(false)
const editionToSwitchTo = ref(null)
const hasVotedForBook = ref(false)
const existingVote = ref(null)
const isLinkEditionModalOpen = ref(false)
const editionSearchQuery = ref('')
const editionSearchResults = ref([])
const isSearchingEditions = ref(false)
const currentPageInput = ref(0)
const reviewInput = ref('')
const coverLoaded = ref(false)
const currentCoverUrl = ref('')
const showMobileSidebar = ref(false)

// Sidebar state
const similarBooks = ref([])
const bookDNA = ref(null)
const potentialEditions = ref([])
const loadingSimilar = ref(true)
const loadingDNA = ref(true)
const loadingPotentialEditions = ref(false)
const showPotentialEditions = ref(false)

// Quote form state
const newQuote = ref({
  text: '',
  note: '',
  page_number: null,
  chapter: '',
  tags_input: '',
  is_favorite: false,
  is_public: true,
})

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

  // First, try to find UserBook for this specific book
  let foundUserBook = userBooksStore.books.find(ub => ub.book?.id === numericBookId)

  // If not found and this book is in a group, look for UserBook from other editions in the same group
  if (!foundUserBook && book.value?.book_group_id) {
    foundUserBook = userBooksStore.books.find(ub =>
      ub.book?.book_group_id === book.value.book_group_id &&
      ub.book?.id !== numericBookId
    )
  }

  return foundUserBook
})
const bookQuotes = computed(() => {
  if (!Array.isArray(quotesStore.quotes)) return []

  // If user has an edition in this group, show quotes from THEIR edition
  // Otherwise show quotes from the currently viewed book
  const quoteBookId = userBook.value ? userBook.value.book.id : parseInt(bookId.value)

  return quotesStore.quotes.filter(q => {
    // book is just the ID (number), not an object
    return q.book === quoteBookId
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
  if (!book.value?.description) return 'No description available.'
  // Convert plain text newlines to HTML with proper formatting
  const text = book.value.description
  // Replace ALL newlines with <br> to preserve exact formatting from textarea
  return text.replace(/\n/g, '<br>')
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
    booksStore.fetchBook(bookId.value)
  ]

  // Only fetch user books if store is empty
  if (userBooksStore.books.length === 0) {
    promises.push(userBooksStore.fetchBooks())
  }

  await Promise.all(promises)

  // After loading book and user books, fetch quotes for the user's edition (if they have one in this group)
  await nextTick()

  if (userBook.value) {
    // User has an edition in this group - fetch quotes for THEIR edition
    await quotesStore.fetchQuotes({ book: userBook.value.book.id })

    // Initialize inputs from user's edition data
    currentPageInput.value = userBook.value.current_page || 0
    reviewInput.value = userBook.value.review || ''
  } else {
    // User doesn't have any edition - fetch quotes for current book
    await quotesStore.fetchQuotes({ book: bookId.value })
  }

  // Check if user has already voted for this book's DNA
  await checkDNAVoteStatus()

  // Fetch sidebar data (similar books, book DNA)
  fetchSidebarData()

  // Fetch potential editions (for linking suggestions)
  await nextTick()
  fetchPotentialEditions()

  window.scrollTo(0, 0)
})

// Check DNA vote status and fetch existing vote
const checkDNAVoteStatus = async () => {
  if (!bookId.value) return

  try {
    const result = await recommendationsService.hasVotedForBook(bookId.value)
    console.log('[DNA Check] Book ID:', bookId.value, '| hasVoted:', result)
    hasVotedForBook.value = result
    if (result) {
      existingVote.value = await recommendationsService.getVoteForBook(bookId.value)
    }
  } catch (error) {
    console.error('[DNA Check] Error:', error)
    hasVotedForBook.value = false
  }
}

// Fetch sidebar data (similar books + book DNA)
const fetchSidebarData = async () => {
  if (!bookId.value) return

  loadingSimilar.value = true
  loadingDNA.value = true

  // Fetch in parallel
  const [similar, dna] = await Promise.all([
    recommendationsService.getSimilarBooks(bookId.value, 5),
    recommendationsService.getBookDNA(bookId.value)
  ])

  similarBooks.value = similar || []
  bookDNA.value = dna
  loadingSimilar.value = false
  loadingDNA.value = false
}

// Fetch potential editions (only if book doesn't already have other editions)
const fetchPotentialEditions = async () => {
  if (!bookId.value || !book.value) return

  // Skip if book already has other editions
  if (book.value.has_other_editions) {
    potentialEditions.value = []
    return
  }

  loadingPotentialEditions.value = true
  try {
    const response = await booksAPI.potentialEditions(bookId.value)
    potentialEditions.value = response.data || []
  } catch (error) {
    console.error('Failed to fetch potential editions:', error)
    potentialEditions.value = []
  } finally {
    loadingPotentialEditions.value = false
  }
}

// Open DNA survey manually
const openDNASurvey = () => {
  showDNASurvey.value = true
}

// Handle survey submitted
const handleSurveySubmitted = async () => {
  hasVotedForBook.value = true
  addToast('Thanks for rating! Your profile has been updated.', 'success')
  // Refresh existing vote data for future updates
  existingVote.value = await recommendationsService.getVoteForBook(bookId.value)
}

// Reset cover loaded state when bookId or coverUrl changes
watch(bookId, async (newId, oldId) => {
  // IMMEDIATELY clear the current book to prevent showing old data
  booksStore.currentBook = null
  coverLoaded.value = false
  hasVotedForBook.value = false
  existingVote.value = null
  similarBooks.value = []
  bookDNA.value = null
  await nextTick()

  await booksStore.fetchBook(newId)

  // After loading the new book, fetch quotes for user's edition if they have one
  await nextTick()

  if (userBook.value) {
    // User has an edition in this group - fetch quotes for THEIR edition
    await quotesStore.fetchQuotes({ book: userBook.value.book.id })
  } else {
    // User doesn't have any edition - fetch quotes for current book
    await quotesStore.fetchQuotes({ book: newId })
  }

  await checkDNAVoteStatus()
  fetchSidebarData()
  // Fetch potential editions after book data is loaded
  await nextTick()
  fetchPotentialEditions()
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
  const wasNotRead = currentStatus.value !== 'read'

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

  // Show DNA survey when marking as read for the first time
  if (newStatus === 'read' && wasNotRead) {
    // Check if user has already voted for this book
    const hasVoted = await recommendationsService.hasVotedForBook(bookId.value)
    if (!hasVoted) {
      // Show survey after a short delay
      setTimeout(() => {
        showDNASurvey.value = true
      }, 500)
    }
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
}

const handleCreateQuote = async () => {
  try {
    if (!newQuote.value.text) {
      addToast('Quote text is required', 'error')
      return
    }

    // Parse tags from comma-separated string
    const tagNames = newQuote.value.tags_input
      ? newQuote.value.tags_input.split(',').map(t => t.trim()).filter(t => t !== '')
      : []

    // Prepare payload - use user's edition if they have one
    const quoteBook = userBook.value ? userBook.value.book : book.value

    const payload = {
      text: newQuote.value.text,
      note: newQuote.value.note,
      book: quoteBook.id,
      book_title: quoteBook.title,
      book_author: quoteBook.authors?.[0]?.name || '',
      user_book: userBook.value?.id || null,
      page_number: newQuote.value.page_number || null,
      chapter: newQuote.value.chapter || '',
      is_favorite: newQuote.value.is_favorite,
      is_public: newQuote.value.is_public,
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
    }

    const result = await quotesStore.createQuote(payload)

    if (result.success) {
      addToast('Quote added successfully!', 'success')
      isQuoteModalOpen.value = false
      // Reset form
      newQuote.value = {
        text: '',
        note: '',
        page_number: null,
        chapter: '',
        tags_input: '',
        is_favorite: false,
        is_public: true,
      }
      // Refresh quotes for this book
      await quotesStore.fetchQuotes({ book: bookId.value })
    } else {
      addToast('Failed to create quote', 'error')
    }
  } catch (error) {
    console.error('Error creating quote:', error)
    addToast('Error creating quote', 'error')
  }
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
    path: getBookUrlWithSuffix(book.value, 'study'),
    query: { title: book.value?.title || 'Study Session' }
  })
}

const switchToEdition = async (newBookId) => {
  // Store the edition ID and open confirmation modal
  editionToSwitchTo.value = newBookId
  isSwitchEditionModalOpen.value = true
}

const confirmSwitchEdition = async () => {
  try {
    const newBookId = editionToSwitchTo.value
    if (!newBookId || !userBook.value) return

    // Get the book ID of the edition the user currently has
    // This might be different from the book they're viewing
    const currentUserBookId = userBook.value.book.id

    // Call the switch_edition API endpoint with the user's actual edition
    const response = await booksStore.switchEdition(currentUserBookId, newBookId)

    if (response.success) {
      // Close modal
      isSwitchEditionModalOpen.value = false

      // Navigate to new edition (find edition in other_editions for slug)
      const edition = book.value?.other_editions?.find(e => e.id === newBookId)
      router.push(edition ? getBookUrl(edition) : `/books/${newBookId}`)

      // Show success message
      addToast(
        `Switched to new edition! ${response.transferred_quotes} quote${response.transferred_quotes !== 1 ? 's' : ''} transferred.`,
        'success'
      )

      // Refresh user books
      await userBooksStore.fetchBooks()
    }
  } catch (error) {
    console.error('Failed to switch edition:', error)
    addToast(error.response?.data?.error || 'Failed to switch edition', 'error')
  }
}

// Link a potential edition
const linkPotentialEdition = async (editionId) => {
  try {
    const response = await booksAPI.linkEdition(bookId.value, editionId)

    if (response.data.success) {
      addToast('Edition linked successfully!', 'success')

      // Refresh book data to show new editions
      await booksStore.fetchBook(bookId.value)
      await nextTick()

      // Clear potential editions and fetch again
      potentialEditions.value = []
      fetchPotentialEditions()
    }
  } catch (error) {
    console.error('Failed to link edition:', error)
    addToast(error.response?.data?.error || 'Failed to link edition', 'error')
  }
}

// Manual edition search
let searchDebounceTimeout = null
watch(editionSearchQuery, (newQuery) => {
  clearTimeout(searchDebounceTimeout)

  if (!newQuery || newQuery.trim().length < 2) {
    editionSearchResults.value = []
    return
  }

  searchDebounceTimeout = setTimeout(async () => {
    await searchEditions(newQuery.trim())
  }, 300)
})

const searchEditions = async (query) => {
  isSearchingEditions.value = true
  try {
    const response = await booksAPI.list({ search: query })
    const results = response.data?.results || response.data || []

    // Filter out current book and any books already in the same group
    editionSearchResults.value = results.filter(b => {
      if (b.id === parseInt(bookId.value)) return false
      if (book.value.book_group_id && b.book_group_id === book.value.book_group_id) return false
      return true
    }).slice(0, 10)
  } catch (error) {
    console.error('Failed to search editions:', error)
    editionSearchResults.value = []
  } finally {
    isSearchingEditions.value = false
  }
}

const openLinkEditionModal = () => {
  editionSearchQuery.value = ''
  editionSearchResults.value = []
  isLinkEditionModalOpen.value = true
}

const linkManualEdition = async (editionId) => {
  try {
    const response = await booksAPI.linkEdition(bookId.value, editionId)

    if (response.data.success) {
      // Close modal
      isLinkEditionModalOpen.value = false
      editionSearchQuery.value = ''
      editionSearchResults.value = []

      addToast('Edition linked successfully!', 'success')

      // Refresh book data
      await booksStore.fetchBook(bookId.value)
      await nextTick()
      fetchPotentialEditions()
    }
  } catch (error) {
    console.error('Failed to link edition:', error)
    addToast(error.response?.data?.error || 'Failed to link edition', 'error')
  }
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
  <div v-if="book" class="w-full max-w-[1600px] mx-auto lg:px-6 lg:py-12 animate-in fade-in slide-in-from-bottom-4 duration-700">

    <!-- MOBILE HEADER -->
    <header class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-white/5">
      <div class="flex items-center justify-between px-4 py-3">
        <button
          @click="handleBack"
          class="p-2 -ml-2 rounded-xl text-slate-400 active:bg-slate-800"
        >
          <ArrowLeft :size="22" />
        </button>
        <div class="flex-1 min-w-0 mx-3">
          <h1 class="text-sm font-bold text-white truncate">{{ book.title }}</h1>
          <p class="text-[10px] text-slate-500 truncate">{{ authorsString }}</p>
        </div>
        <div class="flex items-center gap-1">
          <button
            @click="handleToggleFavorite"
            :class="[
              'p-2 rounded-xl transition-colors',
              isFavorite ? 'text-rose-400' : 'text-slate-400'
            ]"
          >
            <Heart :size="20" :fill="isFavorite ? 'currentColor' : 'none'" />
          </button>
          <button
            @click="showMobileSidebar = true"
            class="p-2 rounded-xl text-slate-400 active:bg-slate-800"
          >
            <MoreHorizontal :size="20" />
          </button>
        </div>
      </div>
    </header>

    <!-- Desktop Back Button -->
    <button
      @click="handleBack"
      class="hidden lg:flex items-center gap-2 text-slate-400 hover:text-indigo-400 mb-10 transition-colors font-bold group"
    >
      <ArrowLeft :size="20" class="group-hover:-translate-x-1 transition-transform" />
      Back to Results
    </button>

    <!-- MOBILE HERO - Cover + Quick Info -->
    <div class="lg:hidden">
      <!-- Cover Section -->
      <div class="relative px-4 pt-4 pb-6">
        <div class="flex gap-4">
          <!-- Cover -->
          <div class="relative shrink-0 w-28 aspect-[2/3] rounded-xl overflow-hidden shadow-2xl ring-1 ring-white/10">
            <div v-if="!coverLoaded" class="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-slate-800 animate-pulse" />
            <img
              :key="coverUrl"
              :src="coverUrl"
              :alt="book.title"
              @load="handleCoverLoad"
              v-show="coverLoaded"
              class="w-full h-full object-cover"
            />
          </div>

          <!-- Quick Info -->
          <div class="flex-1 min-w-0 py-1">
            <div v-if="book.genres?.length > 0" class="flex flex-wrap gap-1 mb-2">
              <span
                v-for="genre in book.genres.slice(0, 2)"
                :key="genre.id"
                class="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold"
              >
                {{ genre.name }}
              </span>
            </div>
            <h1 class="text-lg font-black text-white leading-tight mb-1 line-clamp-2">{{ book.title }}</h1>
            <p class="text-sm text-slate-400 mb-2">
              by <span v-for="(author, idx) in (book.authors || [])" :key="author.id"><router-link :to="getAuthorUrl(author)" class="text-indigo-400 hover:underline">{{ author.name }}</router-link><span v-if="idx < book.authors.length - 1">, </span></span><span v-if="!book.authors?.length">Unknown Author</span>
            </p>

            <!-- Rating -->
            <div class="flex items-center gap-2 mb-3">
              <StarRating :model-value="averageRating" :readonly="true" :size="12" :show-value="true" />
            </div>

            <!-- Quick Stats 2x2 Grid -->
            <div class="grid grid-cols-2 gap-1.5">
              <div class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <BookOpen :size="12" class="text-slate-400" />
                <span class="text-[11px] font-bold text-white">{{ book.pages || '---' }}</span>
                <span class="text-[9px] text-slate-500">pg</span>
              </div>
              <div class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <Globe :size="12" class="text-slate-400" />
                <span class="text-[11px] font-bold text-white">{{ book.language?.toUpperCase() || '---' }}</span>
              </div>
              <div class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <Calendar :size="12" class="text-slate-400" />
                <span class="text-[11px] font-bold text-white">{{ publishedYear }}</span>
              </div>
              <div class="flex items-center gap-1.5 px-2 py-1.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
                <Bookmark :size="12" class="text-indigo-400" />
                <span class="text-[11px] font-bold text-white">{{ bookQuotes.length }}</span>
                <span class="text-[9px] text-slate-500">quotes</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Mobile Status Button -->
      <div class="px-4 pb-4">
        <div v-if="!isInLibrary">
          <button
            @click="handleAddToLibrary"
            class="w-full py-3.5 rounded-xl bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-500/20 active:scale-[0.98] transition-transform flex items-center justify-center gap-2"
          >
            <Plus :size="18" />
            Add to Library
          </button>
        </div>
        <div v-else class="flex gap-2">
          <div class="flex-1 relative">
            <div
              :class="[
                'absolute left-0 top-0 bottom-0 w-1 rounded-l-xl z-10',
                currentStatus === 'read' ? 'bg-emerald-500' :
                currentStatus === 'currently_reading' ? 'bg-sky-500' :
                currentStatus === 'abandoned' ? 'bg-red-500' : 'bg-slate-600'
              ]"
            />
            <Select :model-value="currentStatus" @update:model-value="handleStatusChange">
              <SelectTrigger class="w-full bg-slate-800 border-slate-700 rounded-xl pl-4 pr-3 py-3 h-auto text-sm font-bold text-slate-200">
                <SelectValue placeholder="Select status" />
              </SelectTrigger>
              <SelectContent class="bg-slate-800 border-slate-700">
                <SelectItem value="want_to_read" class="text-slate-200 focus:bg-slate-700 focus:text-white">Want to Read</SelectItem>
                <SelectItem value="currently_reading" class="text-slate-200 focus:bg-slate-700 focus:text-white">Currently Reading</SelectItem>
                <SelectItem value="read" class="text-slate-200 focus:bg-slate-700 focus:text-white">Finished</SelectItem>
                <SelectItem value="abandoned" class="text-slate-200 focus:bg-slate-700 focus:text-white">Abandoned</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <button
            @click="handleStudyMode"
            class="px-4 py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 font-bold active:scale-[0.98] transition-transform"
          >
            <Brain :size="18" />
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-12">

      <!-- Left Column - Cover & Main Info (Desktop only) -->
      <div class="hidden lg:block lg:col-span-3 min-w-0 space-y-8">
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

      <!-- Middle Column - Interaction & Content -->
      <div class="lg:col-span-6 min-w-0 space-y-6 lg:space-y-12 px-4 lg:px-0">

        <!-- Header Info (Desktop only) -->
        <section class="hidden lg:block">
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
            by <span v-for="(author, idx) in (book.authors || [])" :key="author.id"><router-link :to="getAuthorUrl(author)" class="text-indigo-400 hover:underline">{{ author.name }}</router-link><span v-if="idx < book.authors.length - 1">, </span></span><span v-if="!book.authors?.length">Unknown Author</span>
          </p>

          <div class="flex items-center gap-4 mt-6">
            <StarRating :model-value="averageRating" :readonly="true" :size="24" :show-value="true" />
            <span class="text-slate-500 text-sm">({{ ratingsCount }} ratings on Google Books)</span>
          </div>
        </section>

        <!-- Description -->
        <section class="space-y-4">
          <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">About the Book</h2>
          <div :class="['text-slate-300 text-sm lg:text-base leading-relaxed space-y-4 relative', !showFullDesc ? 'max-h-48 overflow-hidden' : '']">
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
        <section class="p-4 sm:p-6 lg:p-8 rounded-2xl lg:rounded-3xl glass border-indigo-500/20 bg-indigo-500/5 relative overflow-hidden">
          <div class="absolute top-0 right-0 p-4 lg:p-8 opacity-10">
            <Sparkles :size="80" class="lg:w-[120px] lg:h-[120px] text-indigo-500" />
          </div>

          <div class="relative z-10 space-y-4 lg:space-y-6">
            <!-- Header (Desktop shows full, mobile shows compact) -->
            <div class="hidden lg:flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 class="text-xl font-bold text-white mb-1">My Reading</h2>
                <p class="text-slate-400 text-sm">Track your progress and thoughts</p>
              </div>

              <!-- Status Control -->
              <div class="flex items-center gap-2">
                <button
                  v-if="!isInLibrary"
                  @click="handleAddToLibrary"
                  class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-2"
                >
                  <Plus :size="18" />
                  Add to Library
                </button>

                <!-- Status Dropdown with colored indicator -->
                <div v-else class="relative">
                  <div
                    :class="[
                      'absolute left-0 top-0 bottom-0 w-1 rounded-l-lg',
                      currentStatus === 'read' ? 'bg-emerald-500' :
                      currentStatus === 'currently_reading' ? 'bg-sky-500' :
                      currentStatus === 'abandoned' ? 'bg-red-500' : 'bg-slate-600'
                    ]"
                  />
                  <select
                    :value="currentStatus"
                    @change="handleStatusChange($event.target.value)"
                    class="bg-slate-900 border border-slate-700 rounded-lg pl-4 pr-8 py-2.5 text-sm font-bold text-slate-200 outline-none focus:border-indigo-500 transition-all cursor-pointer appearance-none"
                    style="background-image: url('data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2214%22%20height%3D%2214%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22%2394a3b8%22%20stroke-width%3D%222%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpolyline%20points%3D%226%209%2012%2015%2018%209%22%3E%3C%2Fpolyline%3E%3C%2Fsvg%3E'); background-repeat: no-repeat; background-position: right 0.5rem center;"
                  >
                    <option value="want_to_read">Want to Read</option>
                    <option value="currently_reading">Currently Reading</option>
                    <option value="read">Finished</option>
                    <option value="abandoned">Abandoned</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Mobile Header -->
            <div class="lg:hidden flex items-center justify-between">
              <h2 class="text-base font-bold text-white">My Reading</h2>
              <span :class="['px-2 py-1 rounded-lg text-[10px] font-bold border', getStatusBadgeClass(currentStatus)]">
                {{ getStatusLabel(currentStatus) }}
              </span>
            </div>

            <!-- Content for In-Library books -->
            <div v-if="isInLibrary" :key="`library-${userBook?.id || 'new'}`" class="pt-6 border-t border-slate-800/50 space-y-6">

              <!-- Rating Section (for finished/abandoned) -->
              <div v-if="currentStatus === 'read' || currentStatus === 'abandoned'" class="space-y-6">
                <!-- Rating -->
                <div>
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-3">My Rating</label>
                  <div class="flex flex-wrap items-center gap-4">
                    <StarRating
                      v-if="userBook"
                      :key="`rating-${userBook.id}`"
                      v-model="personalRating"
                      :readonly="false"
                      :size="18"
                      :show-value="true"
                    />
                  </div>
                  <p class="text-[10px] text-slate-500 mt-2">Click once for full star, double-click for half star</p>
                </div>

                <!-- Reading Dates -->
                <div v-if="formattedStartedAt || formattedFinishedAt" class="p-3 lg:p-4 rounded-xl bg-slate-950/50 border border-slate-800 flex flex-col sm:flex-row sm:inline-flex items-start sm:items-center gap-3 sm:gap-6">
                  <div class="flex items-center gap-2">
                    <Calendar :size="14" class="text-slate-500" />
                    <span class="text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-widest">Reading Journey</span>
                  </div>

                  <div class="flex flex-wrap items-center gap-3 sm:gap-6">
                    <div v-if="formattedStartedAt" class="flex items-center gap-2">
                      <span class="text-[10px] sm:text-xs text-slate-500">Started</span>
                      <span class="text-xs sm:text-sm font-semibold text-slate-300">{{ formattedStartedAt }}</span>
                    </div>

                    <div v-if="formattedFinishedAt" class="flex items-center gap-2">
                      <span class="text-[10px] sm:text-xs text-slate-500">Finished</span>
                      <span class="text-xs sm:text-sm font-semibold text-emerald-400">{{ formattedFinishedAt }}</span>
                    </div>
                  </div>
                </div>

                <!-- Action Buttons Row -->
                <div class="flex flex-wrap gap-3">
                  <button
                    @click="router.push(getBookUrlWithSuffix(book, 'review'))"
                    class="px-4 py-2.5 rounded-lg border border-slate-700 text-slate-400 text-xs font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center gap-2 group/btn"
                  >
                    <SquarePen :size="14" class="transition-colors group-hover/btn:text-indigo-400" />
                    <span class="transition-colors group-hover/btn:text-indigo-400">Edit My Activity</span>
                  </button>

                  <button
                    v-if="!hasVotedForBook"
                    @click="openDNASurvey"
                    class="px-4 py-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-bold hover:bg-indigo-500/20 hover:border-indigo-500/50 transition-all flex items-center gap-2"
                  >
                    <Sparkles :size="14" />
                    <span>Rate Book DNA</span>
                  </button>
                  <button
                    v-else
                    @click="openDNASurvey"
                    class="px-4 py-2.5 rounded-lg border border-slate-700 text-slate-500 text-xs font-bold hover:border-indigo-500/30 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center gap-2 group/btn"
                  >
                    <Sparkles :size="14" class="transition-colors group-hover/btn:text-indigo-400" />
                    <span class="transition-colors group-hover/btn:text-indigo-400">Update DNA</span>
                  </button>
                </div>
              </div>

              <!-- Progress Tracking (for currently_reading) -->
              <div v-if="currentStatus === 'currently_reading'" class="p-6 rounded-2xl bg-slate-950/50 border border-slate-800 space-y-4">
                <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block">Reading Progress</label>

                <div class="flex flex-wrap items-center gap-3">
                  <input
                    type="number"
                    v-model.number="currentPageInput"
                    @keyup.enter="handleProgressUpdate"
                    :min="0"
                    :max="totalPages"
                    class="w-24 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-center font-bold text-indigo-400 outline-none focus:border-indigo-500 transition-colors"
                  />
                  <span class="text-slate-500 text-sm">/ {{ totalPages }} pages</span>
                  <button
                    @click="handleProgressUpdate"
                    class="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold rounded-lg transition-colors"
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

                <div class="flex flex-wrap items-center justify-between gap-4">
                  <button
                    @click="handleStatusChange('read')"
                    class="px-4 py-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold hover:bg-emerald-500/20 transition-all flex items-center gap-2"
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
                <div class="flex gap-2 sm:gap-3">
                  <button
                    @click="router.push(getBookUrlWithSuffix(book, 'review-view'))"
                    class="flex-1 py-2 sm:py-3 rounded-lg sm:rounded-xl bg-indigo-600 text-white text-xs sm:text-sm font-bold hover:bg-indigo-500 transition-all flex items-center justify-center gap-1.5 sm:gap-2"
                  >
                    <Eye :size="14" class="sm:hidden" /><Eye :size="16" class="hidden sm:block" />
                    <span class="whitespace-nowrap">Full Review</span>
                  </button>
                  <button
                    @click="router.push(getBookUrlWithSuffix(book, 'review'))"
                    class="flex-1 py-2 sm:py-3 rounded-lg sm:rounded-xl border border-slate-700 text-slate-400 text-xs sm:text-sm font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center justify-center gap-1.5 sm:gap-2"
                  >
                    <SquarePen :size="14" class="sm:hidden" /><SquarePen :size="16" class="hidden sm:block" />
                    <span class="whitespace-nowrap">Edit Review</span>
                  </button>
                </div>
              </div>

              <!-- Show write button if no review -->
              <button
                v-else
                @click="router.push(getBookUrlWithSuffix(book, 'review'))"
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
          <div class="flex items-center justify-between gap-2">
            <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em]">My Quotes</h2>
            <div class="flex items-center gap-2 sm:gap-3">
              <button
                @click="handleStudyMode"
                class="flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-xs sm:text-sm hover:bg-indigo-500/20 transition-all"
              >
                <Brain :size="14" /> <span class="hidden sm:inline">Study Mode</span><span class="sm:hidden">Study</span>
              </button>
              <button
                @click="handleAddQuote"
                class="flex items-center gap-1.5 sm:gap-2 text-indigo-400 font-bold text-xs sm:text-sm hover:text-indigo-300 transition-colors"
              >
                <Plus :size="14" class="sm:hidden" /><Plus :size="16" class="hidden sm:block" /> <span class="hidden sm:inline">Add Quote</span><span class="sm:hidden">Add</span>
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

        <!-- Community Activity -->
        <CommunityActivity
          :book-id="bookId"
          :book-title="book.title"
        />

        <!-- Mobile Similar Books -->
        <section v-if="similarBooks.length > 0" class="lg:hidden">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.15em] flex items-center gap-2">
              <Sparkles :size="14" class="text-indigo-400" />
              Similar Books
            </h2>
            <button
              @click="showMobileSidebar = true"
              class="text-xs font-bold text-indigo-400"
            >
              See All
            </button>
          </div>

          <div class="flex gap-3 overflow-x-auto hide-scrollbar -mx-4 px-4 pb-2">
            <router-link
              v-for="simBook in similarBooks"
              :key="simBook.id"
              :to="getBookUrl(simBook)"
              class="shrink-0 w-24 group"
            >
              <div class="aspect-[2/3] rounded-lg overflow-hidden bg-slate-800 shadow-lg mb-2">
                <img
                  v-if="simBook.cover_image"
                  :src="simBook.cover_image"
                  :alt="simBook.title"
                  class="w-full h-full object-cover group-active:scale-105 transition-transform"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <BookOpen :size="20" class="text-slate-600" />
                </div>
              </div>
              <h4 class="text-xs font-bold text-white line-clamp-2 leading-tight">{{ simBook.title }}</h4>
              <p class="text-[10px] text-slate-500 truncate">{{ simBook.authors?.map(a => a.name).join(', ') }}</p>
              <span v-if="simBook.similarity_score" class="text-[10px] font-bold text-indigo-400">
                {{ Math.round(simBook.similarity_score) }}% match
              </span>
            </router-link>
          </div>
        </section>

        <!-- Mobile bottom padding -->
        <div class="lg:hidden h-8"></div>
      </div>

      <!-- Right Column - Sidebar (Desktop only) -->
      <div class="hidden lg:block lg:col-span-3 min-w-0 space-y-6">

        <!-- Similar Books -->
        <div class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Sparkles :size="16" class="text-indigo-400" />
              </div>
              <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Similar Books</h3>
            </div>
          </div>

          <!-- Loading State -->
          <div v-if="loadingSimilar" class="space-y-4">
            <div v-for="n in 3" :key="n" class="flex items-center gap-3 animate-pulse">
              <div class="w-12 h-16 rounded-lg bg-slate-800" />
              <div class="flex-1 space-y-2">
                <div class="h-3 bg-slate-800 rounded w-3/4" />
                <div class="h-2 bg-slate-800 rounded w-1/2" />
              </div>
            </div>
          </div>

          <!-- Similar Books List -->
          <div v-else-if="similarBooks.length > 0" class="space-y-1">
            <router-link
              v-for="simBook in similarBooks"
              :key="simBook.id"
              :to="getBookUrl(simBook)"
              class="group flex items-center gap-3 p-2 -mx-1 rounded-xl hover:bg-white/5 transition-all"
            >
              <div class="shrink-0 w-14 h-20 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                <img
                  v-if="simBook.cover_image"
                  :src="simBook.cover_image"
                  :alt="simBook.title"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <BookOpen v-else :size="18" class="text-slate-600" />
              </div>
              <div class="flex-1 min-w-0 py-0.5">
                <h4 class="font-bold text-white text-sm leading-snug line-clamp-2 group-hover:text-indigo-400 transition-colors">
                  {{ simBook.title }}
                </h4>
                <p class="text-slate-400 text-xs truncate mt-0.5">
                  {{ simBook.authors?.map(a => a.name).join(', ') || 'Unknown' }}
                </p>
                <div class="flex items-center gap-1.5 mt-1.5">
                  <span v-if="simBook.similarity_score" class="text-xs font-bold text-indigo-400">
                    {{ Math.round(simBook.similarity_score) }}% similar
                  </span>
                </div>
              </div>
            </router-link>
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-6">
            <div class="w-12 h-12 mx-auto rounded-full bg-slate-800/50 flex items-center justify-center mb-3">
              <BookOpen :size="20" class="text-slate-600" />
            </div>
            <p class="text-slate-500 text-xs">
              Rate this book to discover similar reads
            </p>
          </div>
        </div>

        <!-- Book DNA -->
        <div v-if="bookDNA" class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Dna :size="16" class="text-indigo-400" />
            </div>
            <div>
              <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Book DNA</h3>
              <p class="text-slate-600 text-[9px]">{{ bookDNA.vote_count || 0 }} reader{{ bookDNA.vote_count !== 1 ? 's' : '' }} rated</p>
            </div>
          </div>

          <!-- DNA Attributes -->
          <div class="space-y-3">
            <div v-if="bookDNA.pace !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Pace</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.pace > 0.5 ? 'Fast' : 'Slow' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-indigo-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.pace * 100}%` }"
                />
              </div>
            </div>
            <div v-if="bookDNA.complexity !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Complexity</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.complexity > 0.5 ? 'Dense' : 'Light' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-purple-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.complexity * 100}%` }"
                />
              </div>
            </div>
            <div v-if="bookDNA.emotional_intensity !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Emotion</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.emotional_intensity > 0.5 ? 'Intense' : 'Calm' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-rose-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.emotional_intensity * 100}%` }"
                />
              </div>
            </div>
            <div v-if="bookDNA.darkness !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Tone</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.darkness > 0.5 ? 'Dark' : 'Light' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-slate-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.darkness * 100}%` }"
                />
              </div>
            </div>
            <div v-if="bookDNA.character_focus !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Focus</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.character_focus > 0.5 ? 'Characters' : 'Plot' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-amber-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.character_focus * 100}%` }"
                />
              </div>
            </div>
            <div v-if="bookDNA.introspection !== undefined">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[9px] font-bold text-slate-500 uppercase">Style</span>
                <span class="text-[9px] text-slate-600">{{ bookDNA.introspection > 0.5 ? 'Reflective' : 'Action' }}</span>
              </div>
              <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  class="h-full bg-cyan-500 rounded-full transition-all"
                  :style="{ width: `${bookDNA.introspection * 100}%` }"
                />
              </div>
            </div>
          </div>

          <!-- Themes -->
          <div v-if="bookDNA.themes?.length > 0" class="mt-5 pt-4 border-t border-slate-800">
            <span class="text-[9px] font-bold text-slate-500 uppercase block mb-2">Themes</span>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="theme in bookDNA.themes.slice(0, 4)"
                :key="theme"
                class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400"
              >
                {{ theme }}
              </span>
            </div>
          </div>
        </div>

        <!-- Potential Editions Section (only show if no existing editions) -->
        <div v-if="!book.has_other_editions && potentialEditions.length > 0" class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40 border-amber-500/20">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
              <BookOpen :size="16" class="text-amber-400" />
            </div>
            <div>
              <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Potential Editions</h3>
              <p class="text-slate-600 text-[9px]">{{ potentialEditions.length }} potential match{{ potentialEditions.length !== 1 ? 'es' : '' }} found</p>
            </div>
          </div>

          <div class="mb-4 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
            <p class="text-xs text-amber-200/70">
              We found books with similar titles and authors. Link them to group different editions together.
            </p>
          </div>

          <!-- Potential Editions List -->
          <div class="space-y-4">
            <div
              v-for="edition in potentialEditions"
              :key="edition.id"
              class="p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-amber-500/30 transition-all space-y-3"
            >
              <!-- Edition info -->
              <div class="flex gap-3">
                <div class="shrink-0 w-12 h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                  <img
                    v-if="edition.cover_image"
                    :src="edition.cover_image"
                    :alt="edition.title"
                    class="w-full h-full object-cover"
                    @error="(e) => e.target.style.display = 'none'"
                  />
                  <BookOpen v-else :size="16" class="text-slate-600" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-start gap-2 mb-1">
                    <h4 class="flex-1 font-semibold text-slate-100 text-sm line-clamp-2">{{ edition.title }}</h4>
                    <span class="shrink-0 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[9px] font-bold">
                      {{ Math.round(edition.similarity * 100) }}% match
                    </span>
                  </div>
                  <div class="space-y-1">
                    <div v-if="edition.authors?.length > 0" class="text-[10px] text-slate-500 truncate">
                      {{ edition.authors.map(a => a.name).join(', ') }}
                    </div>
                    <div class="flex items-center gap-2 text-[10px]">
                      <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                        {{ edition.language?.toUpperCase() || 'N/A' }}
                      </span>
                      <span class="text-slate-500">•</span>
                      <span class="text-slate-500">{{ edition.pages || 'N/A' }} pages</span>
                    </div>
                    <div v-if="edition.publisher" class="text-[10px] text-slate-500 truncate">
                      {{ edition.publisher }}
                    </div>
                    <div v-if="edition.isbn" class="text-[10px] text-slate-600">
                      ISBN: {{ edition.isbn }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="pt-3 border-t border-slate-800/50 flex gap-2">
                <button
                  @click="linkPotentialEdition(edition.id)"
                  class="flex-1 px-3 py-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-bold transition-all"
                >
                  Link as edition
                </button>
                <router-link
                  :to="getBookUrl(edition)"
                  class="px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs font-bold transition-all"
                >
                  View
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Editions Section -->
        <div v-if="book.has_other_editions && book.other_editions?.length > 0" class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
          <div class="flex items-center gap-3 mb-5">
            <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <BookOpen :size="16" class="text-indigo-400" />
            </div>
            <div>
              <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Other Editions</h3>
              <p class="text-slate-600 text-[9px]">{{ book.other_editions.length }} edition{{ book.other_editions.length !== 1 ? 's' : '' }}</p>
            </div>
          </div>

          <!-- Editions List -->
          <div class="space-y-4">
            <div
              v-for="edition in book.other_editions"
              :key="edition.id"
              class="p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-indigo-500/30 transition-all space-y-3"
            >
              <!-- Edition info - Clickable to navigate -->
              <router-link :to="getBookUrl(edition)" class="flex gap-3 cursor-pointer group/card">
                <div class="shrink-0 w-12 h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                  <img
                    v-if="edition.cover_image"
                    :src="edition.cover_image"
                    :alt="edition.title"
                    class="w-full h-full object-cover"
                    @error="(e) => e.target.style.display = 'none'"
                  />
                  <BookOpen v-else :size="16" class="text-slate-600" />
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1">
                    <h4 class="font-semibold text-slate-100 text-sm line-clamp-2 group-hover/card:text-indigo-400 transition-colors">{{ edition.title }}</h4>
                    <span
                      v-if="userBook?.book?.id === edition.id"
                      class="shrink-0 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-black uppercase tracking-wider"
                    >
                      Your Edition
                    </span>
                  </div>
                  <div class="space-y-1">
                    <div class="flex items-center gap-2 text-[10px]">
                      <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                        {{ edition.language?.toUpperCase() || 'N/A' }}
                      </span>
                      <span class="text-slate-500">•</span>
                      <span class="text-slate-500">{{ edition.pages }} pages</span>
                    </div>
                    <div v-if="edition.publisher" class="text-[10px] text-slate-500 truncate">
                      {{ edition.publisher }}
                    </div>
                    <div v-if="edition.published_date" class="text-[10px] text-slate-600">
                      {{ edition.published_date.split('-')[0] }}
                    </div>
                  </div>
                </div>
              </router-link>

              <!-- Actions -->
              <div class="pt-3 border-t border-slate-800/50">
                <!-- Current edition indicator -->
                <router-link
                  v-if="userBook?.book?.id === edition.id"
                  :to="getBookUrl(edition)"
                  class="block w-full px-3 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-xs font-bold transition-all text-center"
                >
                  View Your Edition
                </router-link>

                <!-- Switch button (if user has a different edition in library) -->
                <button
                  v-else-if="isInLibrary"
                  @click="switchToEdition(edition.id)"
                  class="w-full px-3 py-2 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-bold transition-all flex items-center justify-center gap-2 group"
                >
                  <ArrowRight :size="14" class="group-hover:translate-x-0.5 transition-transform" />
                  Switch to this edition
                </button>

                <!-- View button (if user doesn't have any edition) -->
                <router-link
                  v-else
                  :to="getBookUrl(edition)"
                  class="block w-full px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs font-bold transition-all text-center"
                >
                  View edition
                </router-link>
              </div>
            </div>
          </div>
        </div>

        <!-- Manual Link Edition Button -->
        <div class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40 border-dashed">
          <button
            @click="openLinkEditionModal"
            class="w-full px-4 py-3 rounded-xl bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 hover:border-emerald-500/50 text-emerald-400 text-sm font-bold transition-all flex items-center justify-center gap-2 group"
          >
            <Plus :size="16" class="group-hover:rotate-90 transition-transform" />
            Link another edition
          </button>
          <p class="text-[10px] text-slate-500 text-center mt-2">
            Manually link different language versions or editions
          </p>
        </div>

      </div>
    </div>
  </div>

  <!-- Loading State -->
  <div v-else class="w-full max-w-[1600px] mx-auto px-6 py-12">
    <div class="animate-pulse space-y-8">
      <div class="h-8 bg-slate-800 rounded w-48"></div>
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div class="lg:col-span-3">
          <div class="aspect-[2/3] bg-slate-800 rounded-3xl"></div>
        </div>
        <div class="lg:col-span-6 space-y-6">
          <div class="h-12 bg-slate-800 rounded w-3/4"></div>
          <div class="h-6 bg-slate-800 rounded w-1/2"></div>
          <div class="h-32 bg-slate-800 rounded"></div>
        </div>
        <div class="lg:col-span-3 space-y-6">
          <div class="h-64 bg-slate-800 rounded-[2rem]"></div>
          <div class="h-48 bg-slate-800 rounded-[2rem]"></div>
        </div>
      </div>
    </div>
  </div>

  <!-- Add Quote Modal -->
  <Dialog v-model:open="isQuoteModalOpen">
    <DialogContent class="max-w-2xl glass border-slate-700 max-h-[85vh] overflow-y-auto">
      <DialogHeader class="border-b border-slate-800 pb-3 mb-4">
        <DialogTitle class="text-lg font-bold flex items-center gap-2">
          <Sparkles :size="20" class="text-indigo-400" />
          Capture a Quote from {{ book?.title }}
        </DialogTitle>
      </DialogHeader>

      <form @submit.prevent="handleCreateQuote" class="space-y-5">
        <!-- Quote Text -->
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

        <!-- Metadata Grid -->
        <div class="grid grid-cols-2 gap-4">
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
              placeholder="Chapter name/number"
              class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
            />
          </div>
        </div>

        <!-- Personal Note -->
        <div class="space-y-2">
          <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
            <component :is="Brain" :size="12" /> Personal Note (Optional)
          </label>
          <Textarea
            v-model="newQuote.note"
            placeholder="What does this mean to you? Why does it resonate?"
            rows="3"
            class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-xl p-3 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 transition-all resize-none"
          />
        </div>

        <!-- Tags -->
        <div class="space-y-2">
          <label class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1.5">
            <component :is="Hash" :size="12" /> Tags (comma-separated)
          </label>
          <Input
            v-model="newQuote.tags_input"
            placeholder="philosophy, wisdom, inspiration..."
            class="w-full bg-slate-800/30 border-2 border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 transition-all"
          />
        </div>

        <!-- Toggles -->
        <div class="flex items-center gap-6 pt-3 border-t border-slate-800">
          <label class="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              v-model="newQuote.is_favorite"
              class="w-4 h-4 rounded border-2 border-slate-700 bg-slate-800/50 checked:bg-amber-500 checked:border-amber-500 focus:ring-2 focus:ring-amber-500/20 transition-all cursor-pointer"
            />
            <Star :size="16" class="text-amber-400" />
            <span class="text-sm text-slate-300 group-hover:text-white transition-colors">Add to Favorites</span>
          </label>
          <label class="flex items-center gap-2 cursor-pointer group">
            <input
              type="checkbox"
              v-model="newQuote.is_public"
              class="w-4 h-4 rounded border-2 border-slate-700 bg-slate-800/50 checked:bg-indigo-500 checked:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 transition-all cursor-pointer"
            />
            <Globe v-if="newQuote.is_public" :size="16" class="text-indigo-400" />
            <Lock v-else :size="16" class="text-slate-500" />
            <span class="text-sm text-slate-300 group-hover:text-white transition-colors">
              {{ newQuote.is_public ? 'Public' : 'Private' }}
            </span>
          </label>
        </div>

        <!-- Actions -->
        <div class="flex gap-3 pt-4 border-t border-slate-800">
          <button
            type="button"
            @click="isQuoteModalOpen = false"
            class="flex-1 px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="flex-1 px-4 py-3 rounded-xl text-sm font-bold bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20"
          >
            Save Quote
          </button>
        </div>
      </form>
    </DialogContent>
  </Dialog>

  <!-- Book Edit Modal -->
  <BookEditModal
    v-if="isEditModalOpen && book"
    :book="book"
    :open="isEditModalOpen"
    @close="isEditModalOpen = false"
    @save="handleSaveBook"
  />

  <!-- Book DNA Survey Modal -->
  <BookDNASurvey
    v-if="book"
    :open="showDNASurvey"
    :book="book"
    :user-book-id="userBook?.id"
    :existing-vote="existingVote"
    @close="showDNASurvey = false"
    @submitted="handleSurveySubmitted"
  />

  <!-- Switch Edition Confirmation Modal -->
  <Dialog :open="isSwitchEditionModalOpen" @update:open="isSwitchEditionModalOpen = $event">
    <DialogContent class="max-w-md glass border-slate-700">
      <DialogHeader class="border-b border-slate-800 pb-4 mb-4">
        <DialogTitle class="text-lg font-bold flex items-center gap-2 text-white">
          <BookOpen :size="20" class="text-indigo-400" />
          Switch to Different Edition?
        </DialogTitle>
      </DialogHeader>

      <div class="space-y-4">
        <p class="text-sm text-slate-300 leading-relaxed">
          Your reading progress, quotes, and review will be transferred to the new edition.
        </p>

        <div class="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/20 space-y-2">
          <div class="flex items-start gap-2">
            <ArrowRight :size="16" class="text-indigo-400 mt-0.5 flex-shrink-0" />
            <p class="text-xs text-slate-300">Page numbers will be adjusted proportionally based on the new edition's length</p>
          </div>
          <div class="flex items-start gap-2">
            <ArrowRight :size="16" class="text-indigo-400 mt-0.5 flex-shrink-0" />
            <p class="text-xs text-slate-300">Your original edition data will be preserved in your reading history</p>
          </div>
        </div>

        <div class="flex gap-3 pt-4">
          <button
            @click="isSwitchEditionModalOpen = false"
            class="flex-1 px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all border border-slate-700 hover:border-slate-600"
          >
            Cancel
          </button>
          <button
            @click="confirmSwitchEdition"
            class="flex-1 px-4 py-3 rounded-xl text-sm font-bold bg-indigo-500 text-white hover:bg-indigo-400 transition-all shadow-lg shadow-indigo-500/20 flex items-center justify-center gap-2"
          >
            <ArrowRight :size="16" />
            Switch Edition
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>

  <!-- Mobile Sidebar Slide-out -->
  <Teleport to="body">
    <Transition name="slide">
      <div
        v-if="showMobileSidebar"
        class="lg:hidden fixed inset-0 z-50"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/60 backdrop-blur-sm"
          @click="showMobileSidebar = false"
        />

        <!-- Panel -->
        <div class="absolute right-0 top-0 bottom-0 w-[85%] max-w-sm bg-slate-900 border-l border-slate-800 overflow-y-auto">
          <!-- Header -->
          <div class="sticky top-0 z-10 flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900">
            <h2 class="text-lg font-bold text-white">More Info</h2>
            <button
              @click="showMobileSidebar = false"
              class="p-2 rounded-xl bg-slate-800 text-slate-400"
            >
              <X :size="18" />
            </button>
          </div>

          <!-- Content -->
          <div class="p-4 space-y-4">
            <!-- Similar Books -->
            <div v-if="similarBooks.length > 0" class="p-4 rounded-2xl glass border-slate-800 bg-slate-900/40">
              <div class="flex items-center gap-2 mb-4">
                <Sparkles :size="16" class="text-indigo-400" />
                <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Similar Books</h3>
              </div>
              <div class="space-y-3">
                <router-link
                  v-for="simBook in similarBooks"
                  :key="simBook.id"
                  :to="getBookUrl(simBook)"
                  @click="showMobileSidebar = false"
                  class="flex items-center gap-3 p-2 -mx-2 rounded-xl active:bg-white/5 transition-all"
                >
                  <div class="shrink-0 w-10 h-14 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                    <img
                      v-if="simBook.cover_image"
                      :src="simBook.cover_image"
                      :alt="simBook.title"
                      class="w-full h-full object-cover"
                    />
                    <BookOpen v-else :size="14" class="text-slate-600" />
                  </div>
                  <div class="flex-1 min-w-0">
                    <h4 class="font-bold text-white text-sm leading-snug line-clamp-1">{{ simBook.title }}</h4>
                    <p class="text-slate-400 text-[10px] truncate">{{ simBook.authors?.map(a => a.name).join(', ') }}</p>
                    <span v-if="simBook.similarity_score" class="text-[10px] font-bold text-indigo-400">
                      {{ Math.round(simBook.similarity_score) }}% match
                    </span>
                  </div>
                </router-link>
              </div>
            </div>

            <!-- Book DNA -->
            <div v-if="bookDNA" class="p-4 rounded-2xl glass border-slate-800 bg-slate-900/40">
              <div class="flex items-center gap-2 mb-4">
                <Dna :size="16" class="text-indigo-400" />
                <div>
                  <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Book DNA</h3>
                  <p class="text-slate-600 text-[9px]">{{ bookDNA.vote_count || 0 }} reader{{ bookDNA.vote_count !== 1 ? 's' : '' }} rated</p>
                </div>
              </div>

              <!-- DNA Attributes (compact) -->
              <div class="space-y-2">
                <div v-if="bookDNA.pace !== undefined" class="flex items-center gap-2">
                  <span class="text-[9px] font-bold text-slate-500 uppercase w-16">Pace</span>
                  <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full bg-indigo-500 rounded-full" :style="{ width: `${bookDNA.pace * 100}%` }" />
                  </div>
                  <span class="text-[9px] text-slate-600 w-12 text-right">{{ bookDNA.pace > 0.5 ? 'Fast' : 'Slow' }}</span>
                </div>
                <div v-if="bookDNA.complexity !== undefined" class="flex items-center gap-2">
                  <span class="text-[9px] font-bold text-slate-500 uppercase w-16">Complexity</span>
                  <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full bg-purple-500 rounded-full" :style="{ width: `${bookDNA.complexity * 100}%` }" />
                  </div>
                  <span class="text-[9px] text-slate-600 w-12 text-right">{{ bookDNA.complexity > 0.5 ? 'Dense' : 'Light' }}</span>
                </div>
                <div v-if="bookDNA.emotional_intensity !== undefined" class="flex items-center gap-2">
                  <span class="text-[9px] font-bold text-slate-500 uppercase w-16">Emotion</span>
                  <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full bg-rose-500 rounded-full" :style="{ width: `${bookDNA.emotional_intensity * 100}%` }" />
                  </div>
                  <span class="text-[9px] text-slate-600 w-12 text-right">{{ bookDNA.emotional_intensity > 0.5 ? 'Intense' : 'Calm' }}</span>
                </div>
              </div>

              <!-- Themes -->
              <div v-if="bookDNA.themes?.length > 0" class="mt-3 pt-3 border-t border-slate-800">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="theme in bookDNA.themes.slice(0, 4)"
                    :key="theme"
                    class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400"
                  >
                    {{ theme }}
                  </span>
                </div>
              </div>
            </div>

            <!-- Other Editions -->
            <div v-if="book.has_other_editions && book.other_editions?.length > 0" class="p-4 rounded-2xl glass border-slate-800 bg-slate-900/40">
              <div class="flex items-center gap-2 mb-4">
                <BookOpen :size="16" class="text-indigo-400" />
                <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Other Editions</h3>
              </div>
              <div class="space-y-3">
                <div
                  v-for="edition in book.other_editions"
                  :key="edition.id"
                  class="p-3 rounded-xl bg-slate-950/50 border border-slate-800"
                >
                  <router-link :to="getBookUrl(edition)" @click="showMobileSidebar = false" class="flex gap-3">
                    <div class="shrink-0 w-10 h-14 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                      <img v-if="edition.cover_image" :src="edition.cover_image" :alt="edition.title" class="w-full h-full object-cover" />
                      <BookOpen v-else :size="14" class="text-slate-600" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <h4 class="font-semibold text-slate-100 text-sm line-clamp-1">{{ edition.title }}</h4>
                      <div class="flex items-center gap-2 text-[10px] mt-1">
                        <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">{{ edition.language?.toUpperCase() || 'N/A' }}</span>
                        <span class="text-slate-500">{{ edition.pages }} pages</span>
                      </div>
                    </div>
                  </router-link>
                  <button
                    v-if="isInLibrary && userBook?.book?.id !== edition.id"
                    @click="switchToEdition(edition.id); showMobileSidebar = false"
                    class="w-full mt-2 px-3 py-2 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold"
                  >
                    Switch to this edition
                  </button>
                </div>
              </div>
            </div>

            <!-- Publisher Info -->
            <div class="p-4 rounded-2xl glass border-slate-800 bg-slate-900/40 space-y-3">
              <div class="flex items-center gap-2">
                <Building2 :size="16" class="text-slate-400" />
                <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Publisher</h3>
              </div>
              <p class="text-slate-100 font-semibold text-sm">{{ book.publisher?.name || 'Unknown Publisher' }}</p>
              <div class="pt-3 border-t border-slate-800/50">
                <span class="text-[10px] text-slate-500 font-bold uppercase block mb-1">ISBN-13</span>
                <code class="text-xs text-indigo-400">{{ book.isbn || 'N/A' }}</code>
              </div>
            </div>

            <!-- Edit Book Button -->
            <button
              @click="handleEditBook(); showMobileSidebar = false"
              class="w-full p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold text-sm flex items-center justify-center gap-2"
            >
              <Edit3 :size="16" />
              Edit Book Details
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Link Edition Modal -->
  <Dialog :open="isLinkEditionModalOpen" @update:open="isLinkEditionModalOpen = $event">
    <DialogContent class="max-w-2xl glass border-slate-700 max-h-[80vh] flex flex-col">
      <DialogHeader class="border-b border-slate-800 pb-4">
        <DialogTitle class="text-lg font-bold flex items-center gap-2 text-white">
          <Plus :size="20" class="text-emerald-400" />
          Link Another Edition
        </DialogTitle>
      </DialogHeader>

      <div class="flex-1 overflow-hidden flex flex-col space-y-4 py-4">
        <p class="text-sm text-slate-300">
          Search for another edition of "{{ book.title }}" to link. This is useful for different language versions or publisher editions.
        </p>

        <!-- Search Input -->
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="18" />
          <input
            v-model="editionSearchQuery"
            type="text"
            placeholder="Search by title, author, or ISBN..."
            class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-50 outline-none focus:border-emerald-500 transition-all placeholder-slate-600"
            autofocus
          />
        </div>

        <!-- Loading State -->
        <div v-if="isSearchingEditions" class="flex items-center justify-center py-8">
          <Loader2 :size="24" class="text-emerald-400 animate-spin" />
        </div>

        <!-- Search Results -->
        <div v-else-if="editionSearchResults.length > 0" class="flex-1 overflow-y-auto space-y-3">
          <div
            v-for="result in editionSearchResults"
            :key="result.id"
            class="p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-emerald-500/30 transition-all cursor-pointer"
            @click="linkManualEdition(result.id)"
          >
            <div class="flex gap-3">
              <div class="shrink-0 w-12 h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                <img
                  v-if="result.cover_image"
                  :src="result.cover_image"
                  :alt="result.title"
                  class="w-full h-full object-cover"
                />
                <BookOpen v-else :size="16" class="text-slate-600" />
              </div>
              <div class="flex-1 min-w-0">
                <h4 class="font-semibold text-slate-100 text-sm line-clamp-2 mb-1">{{ result.title }}</h4>
                <div class="space-y-1">
                  <div v-if="result.authors?.length > 0" class="text-[11px] text-slate-500 truncate">
                    {{ result.authors.map(a => a.name).join(', ') }}
                  </div>
                  <div class="flex items-center gap-2 text-[11px]">
                    <span v-if="result.language" class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                      {{ result.language }}
                    </span>
                    <span v-if="result.pages" class="text-slate-500">{{ result.pages }} pages</span>
                    <span v-if="result.isbn" class="text-slate-600">ISBN: {{ result.isbn }}</span>
                  </div>
                  <div v-if="result.publisher?.name" class="text-[11px] text-slate-500 truncate">
                    {{ result.publisher.name }}
                  </div>
                </div>
              </div>
              <div class="shrink-0 flex items-center">
                <div class="px-3 py-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 text-xs font-bold">
                  Link
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="editionSearchQuery.trim().length >= 2" class="flex-1 flex flex-col items-center justify-center py-8 text-center">
          <div class="w-16 h-16 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center mb-4">
            <Search :size="24" class="text-slate-600" />
          </div>
          <p class="text-sm font-semibold text-slate-400 mb-1">No books found</p>
          <p class="text-xs text-slate-500">Try a different search term</p>
        </div>

        <!-- Initial State -->
        <div v-else class="flex-1 flex flex-col items-center justify-center py-8 text-center">
          <div class="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
            <BookOpen :size="24" class="text-emerald-400" />
          </div>
          <p class="text-sm font-semibold text-slate-300 mb-1">Search for editions</p>
          <p class="text-xs text-slate-500">Start typing to find books in the database</p>
        </div>

        <!-- Footer -->
        <div class="pt-4 border-t border-slate-800">
          <button
            @click="isLinkEditionModalOpen = false"
            class="w-full px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all border border-slate-700 hover:border-slate-600"
          >
            Cancel
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>

<style>
/* Mobile utilities */
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* Slide transition for mobile sidebar */
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

/* Touch feedback for mobile */
@media (max-width: 1023px) {
  button, a {
    -webkit-tap-highlight-color: transparent;
  }
}

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
