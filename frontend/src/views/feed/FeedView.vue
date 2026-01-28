<script setup>
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import FeedPostCard from '@/components/feed/FeedPostCard.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import DiscoverTab from '@/components/social/DiscoverTab.vue'
import { Users, TrendingUp, Sparkles, Filter, ChevronDown, CheckCircle, BookOpen, Bookmark, Quote as QuoteIcon, MessageSquare, Star, MessageCircle, Compass, ArrowRight, Dna, Heart } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { recommendationsService, CONTEXT_CONFIG } from '@/services/recommendationsService'
import api from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()
const quotesStore = useQuotesStore()
const userBooksStore = useUserBooksStore()

const posts = ref([])
const activeTab = ref('all')
const loading = ref(true)

// Recommendations state
const recommendedBooks = ref([])
const tasteProfile = ref(null)
const loadingRecommendations = ref(true)
const showFilters = ref(false)
const selectedActivityTypes = ref(['all'])
const userBooks = ref([])

// Helper function to format timestamps
const formatTimestamp = (dateString) => {
  if (!dateString) return 'Recently'

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 60) return `${diffMins} minutes ago`
  if (diffHours < 24) return `${diffHours} hours ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString()
}

// Combine real data from stores
const realFeedPosts = computed(() => {
  const feedItems = []

  // Add quotes from quotesStore
  quotesStore.quotes.forEach(quote => {
    feedItems.push({
      id: `quote-${quote.id}`,
      user: { name: authStore.user?.username || 'You', avatar: null },
      type: 'quote',
      timestamp: formatTimestamp(quote.created_at),
      rawTimestamp: quote.created_at,
      book: {
        title: quote.book_title || quote.book?.title || 'Unknown',
        author: quote.book_author || quote.book?.authors?.[0]?.name || 'Unknown',
        cover: quote.book?.cover_image || null
      },
      content: {
        quote: quote.text,
        note: quote.note || null
      },
      stats: { likes: 0, comments: 0, hasLiked: false }
    })
  })

  // Add progress updates from userBooksStore (books currently being read with progress)
  userBooksStore.books.forEach(userBook => {
    if (userBook.current_page && userBook.current_page > 0 && userBook.status === 'currently_reading') {
      const totalPages = userBook.book?.pages || 0
      const progress = totalPages > 0 ? Math.round((userBook.current_page / totalPages) * 100) : 0

      feedItems.push({
        id: `progress-${userBook.id}`,
        user: { name: authStore.user?.username || 'You', avatar: null },
        type: 'progress',
        timestamp: formatTimestamp(userBook.updated_at),
        rawTimestamp: userBook.updated_at,
        bookId: userBook.book?.id,
        book: {
          title: userBook.book?.title || 'Unknown',
          author: userBook.book?.authors?.[0]?.name || 'Unknown',
          cover: userBook.book?.cover_image || null
        },
        content: {
          progress,
          note: `Reading: ${userBook.current_page}${totalPages > 0 ? `/${totalPages}` : ''} pages`
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      })
    }
  })

  // Add reviews from userBooksStore (only books with reviews)
  userBooksStore.books.forEach(userBook => {
    if (userBook.review && userBook.review.trim()) {
      // Strip HTML tags for preview
      const div = document.createElement('div')
      div.innerHTML = userBook.review
      const reviewText = div.textContent || div.innerText || ''

      feedItems.push({
        id: `review-${userBook.id}`,
        user: { name: authStore.user?.username || 'You', avatar: null },
        type: userBook.status === 'read' ? 'finished' : 'review',
        timestamp: formatTimestamp(userBook.updated_at),
        rawTimestamp: userBook.updated_at,
        bookId: userBook.book?.id,
        book: {
          title: userBook.book?.title || 'Unknown',
          author: userBook.book?.authors?.[0]?.name || 'Unknown',
          cover: userBook.book?.cover_image || null
        },
        content: {
          rating: userBook.rating ? parseFloat(userBook.rating) : null,
          review: reviewText.substring(0, 200) + (reviewText.length > 200 ? '...' : '')
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      })
    }
  })

  // Add "Want to Read" books
  userBooksStore.books.forEach(userBook => {
    if (userBook.status === 'want_to_read') {
      feedItems.push({
        id: `want-to-read-${userBook.id}`,
        user: { name: authStore.user?.username || 'You', avatar: null },
        type: 'want_to_read',
        timestamp: formatTimestamp(userBook.created_at || userBook.updated_at),
        rawTimestamp: userBook.created_at || userBook.updated_at,
        bookId: userBook.book?.id,
        book: {
          title: userBook.book?.title || 'Unknown',
          author: userBook.book?.authors?.[0]?.name || 'Unknown',
          cover: userBook.book?.cover_image || null
        },
        content: {
          note: null
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      })
    }
  })

  // Add "Currently Reading" books (started reading)
  userBooksStore.books.forEach(userBook => {
    if (userBook.status === 'currently_reading' && userBook.started_at) {
      feedItems.push({
        id: `started-reading-${userBook.id}`,
        user: { name: authStore.user?.username || 'You', avatar: null },
        type: 'started',
        timestamp: formatTimestamp(userBook.started_at),
        rawTimestamp: userBook.started_at,
        bookId: userBook.book?.id,
        book: {
          title: userBook.book?.title || 'Unknown',
          author: userBook.book?.authors?.[0]?.name || 'Unknown',
          cover: userBook.book?.cover_image || null
        },
        content: {
          note: null
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      })
    }
  })

  // Sort by rawTimestamp (newest first)
  return feedItems.sort((a, b) => new Date(b.rawTimestamp) - new Date(a.rawTimestamp))
})

// Placeholder feed data
const getFeedPosts = () => {
  return [
    {
      id: 'post-1',
      user: { name: 'Sarah Mitchell', avatar: null },
      type: 'finished',
      timestamp: '2 hours ago',
      book: {
        title: 'The Midnight Library',
        author: 'Matt Haig',
        cover: 'https://books.google.com/books/content?id=8L_SDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        rating: 5,
        review: "An absolute masterpiece about life choices and regret. Haig's writing is both philosophical and deeply emotional. Every page resonated with me."
      },
      stats: { likes: 12, comments: 3, hasLiked: false }
    },
    {
      id: 'post-2',
      user: { name: 'Marcus Chen', avatar: null },
      type: 'quote',
      timestamp: '5 hours ago',
      book: {
        title: 'Atomic Habits',
        author: 'James Clear',
        cover: 'https://books.google.com/books/content?id=f_S8DwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        quote: 'You do not rise to the level of your goals. You fall to the level of your systems.',
        note: 'This changed how I think about productivity.'
      },
      stats: { likes: 24, comments: 7, hasLiked: true }
    },
    {
      id: 'post-3',
      user: { name: 'Elena Rodriguez', avatar: null },
      type: 'started',
      timestamp: '8 hours ago',
      book: {
        title: 'Project Hail Mary',
        author: 'Andy Weir',
        cover: 'https://books.google.com/books/content?id=D_4yEAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        note: "Heard so many good things about this! Time to dive into some hard science fiction."
      },
      stats: { likes: 8, comments: 2, hasLiked: false }
    },
    {
      id: 'post-4',
      user: { name: 'David Wilson', avatar: null },
      type: 'progress',
      timestamp: '1 day ago',
      book: {
        title: 'Dune',
        author: 'Frank Herbert',
        cover: 'https://books.google.com/books/content?id=B1hGBAAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        progress: 75,
        note: "The world-building on Arrakis is unmatched. Paul is truly starting to understand his path."
      },
      stats: { likes: 15, comments: 4, hasLiked: false }
    },
    {
      id: 'post-5',
      user: { name: 'Reading OS Community', avatar: null },
      type: 'challenge',
      timestamp: '2 days ago',
      book: {
        title: 'Reading Odyssey 2024',
        author: 'Annual Challenge',
        cover: null
      },
      content: {
        challengeTitle: 'Halfway Point!',
        note: "Over 5,000 readers have reached their mid-year reading goals. Keep those pages turning!"
      },
      stats: { likes: 156, comments: 42, hasLiked: false }
    },
    {
      id: 'post-6',
      user: { name: 'Julian Thorne', avatar: null },
      type: 'list',
      timestamp: '2 days ago',
      book: {
        title: 'Modern Stoicism',
        author: 'Curated List',
        cover: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        listTitle: 'Essentials for the Modern Stoic',
        note: "A collection of 12 books to help navigate the chaos of the 21st century."
      },
      stats: { likes: 31, comments: 11, hasLiked: true }
    },
    {
      id: 'post-7',
      user: { name: 'Sophie Banks', avatar: null },
      type: 'review',
      timestamp: '3 days ago',
      book: {
        title: 'Deep Work',
        author: 'Cal Newport',
        cover: 'https://books.google.com/books/content?id=XmYpCgAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api'
      },
      content: {
        rating: 4,
        review: "Practical and convicting. Newport makes a compelling case for intense concentration in an age of distraction. I've already started scheduling my deep work blocks."
      },
      stats: { likes: 19, comments: 5, hasLiked: false }
    }
  ]
}

// Activity type filter options
const activityTypes = [
  { value: 'all', label: 'All Types', icon: Sparkles },
  { value: 'finished', label: 'Finished Books', icon: CheckCircle },
  { value: 'started', label: 'Started Reading', icon: BookOpen },
  { value: 'want_to_read', label: 'Want to Read', icon: Bookmark },
  { value: 'quote', label: 'Quotes', icon: QuoteIcon },
  { value: 'review', label: 'Reviews', icon: MessageSquare },
  { value: 'progress', label: 'Reading Progress', icon: TrendingUp },
  { value: 'challenge', label: 'Challenges', icon: Star },
  { value: 'list', label: 'Lists', icon: MessageCircle }
]

const toggleActivityType = (type) => {
  if (type === 'all') {
    selectedActivityTypes.value = ['all']
  } else {
    // Remove 'all' if selecting specific type
    const allIndex = selectedActivityTypes.value.indexOf('all')
    if (allIndex > -1) {
      selectedActivityTypes.value.splice(allIndex, 1)
    }

    const index = selectedActivityTypes.value.indexOf(type)
    if (index > -1) {
      selectedActivityTypes.value.splice(index, 1)
      // If nothing selected, select 'all'
      if (selectedActivityTypes.value.length === 0) {
        selectedActivityTypes.value = ['all']
      }
    } else {
      selectedActivityTypes.value.push(type)
    }
  }
}

const isActivityTypeSelected = (type) => {
  return selectedActivityTypes.value.includes(type) || selectedActivityTypes.value.includes('all')
}

// Generate real user feed posts from quotes and user books
const generateUserFeedPosts = () => {
  const feedPosts = []
  const currentUser = authStore.user

  // Add quotes as feed posts
  if (quotesStore.quotes && Array.isArray(quotesStore.quotes)) {
    quotesStore.quotes.forEach(quote => {
      feedPosts.push({
        id: `quote-${quote.id}`,
        user: {
          name: currentUser?.full_name || currentUser?.email || 'You',
          avatar: null
        },
        type: 'quote',
        timestamp: formatTimestamp(quote.created_at),
        book: {
          title: quote.book_title || quote.book?.title || 'Unknown Book',
          author: quote.book_author || quote.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author',
          cover: quote.book?.cover_image || null
        },
        content: {
          quote: quote.text,
          note: quote.note || null
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      })
    })
  }

  // Add user books activity
  if (userBooksStore.books && Array.isArray(userBooksStore.books)) {
    userBooksStore.books.forEach(userBook => {
      // Finished books
      if (userBook.status === 'read' && userBook.finished_at) {
        feedPosts.push({
          id: `finished-${userBook.id}`,
          user: {
            name: currentUser?.full_name || currentUser?.email || 'You',
            avatar: null
          },
          type: 'finished',
          timestamp: formatTimestamp(userBook.finished_at),
          book: {
            title: userBook.book?.title || 'Unknown Book',
            author: userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author',
            cover: userBook.book?.cover_image || null
          },
          content: {
            rating: userBook.rating,
            review: userBook.review
          },
          stats: { likes: 0, comments: 0, hasLiked: false }
        })
      }

      // Started reading
      if (userBook.status === 'currently_reading' && userBook.started_at) {
        feedPosts.push({
          id: `started-${userBook.id}`,
          user: {
            name: currentUser?.full_name || currentUser?.email || 'You',
            avatar: null
          },
          type: 'started',
          timestamp: formatTimestamp(userBook.started_at),
          book: {
            title: userBook.book?.title || 'Unknown Book',
            author: userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author',
            cover: userBook.book?.cover_image || null
          },
          content: {
            note: null
          },
          stats: { likes: 0, comments: 0, hasLiked: false }
        })
      }

      // Reading progress
      if (userBook.status === 'currently_reading' && userBook.current_page && userBook.book?.pages) {
        const progress = Math.round((userBook.current_page / userBook.book.pages) * 100)
        if (progress >= 25) { // Only show significant progress
          feedPosts.push({
            id: `progress-${userBook.id}`,
            user: {
              name: currentUser?.full_name || currentUser?.email || 'You',
              avatar: null
            },
            type: 'progress',
            timestamp: formatTimestamp(userBook.updated_at),
            book: {
              title: userBook.book?.title || 'Unknown Book',
              author: userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author',
              cover: userBook.book?.cover_image || null
            },
            content: {
              progress: progress,
              note: `Currently on page ${userBook.current_page} of ${userBook.book.pages}`
            },
            stats: { likes: 0, comments: 0, hasLiked: false }
          })
        }
      }
    })
  }

  // Sort by timestamp (newest first)
  feedPosts.sort((a, b) => {
    const dateA = parseTimestamp(a.timestamp)
    const dateB = parseTimestamp(b.timestamp)
    return dateB - dateA
  })

  return feedPosts
}

// Helper to parse timestamp for sorting
const parseTimestamp = (timestamp) => {
  const match = timestamp.match(/(\d+)\s+(minute|hour|day|week)s?\s+ago/)
  if (match) {
    const num = parseInt(match[1])
    const unit = match[2]
    const now = Date.now()
    if (unit === 'minute') return now - (num * 60000)
    if (unit === 'hour') return now - (num * 3600000)
    if (unit === 'day') return now - (num * 86400000)
    if (unit === 'week') return now - (num * 604800000)
  }
  if (timestamp === 'Yesterday') return Date.now() - 86400000
  return new Date(timestamp).getTime()
}

// Computed filtered posts
const filteredPosts = computed(() => {
  let filtered = posts.value

  // Filter by tab
  const currentUserId = authStore.user?.id

  if (activeTab.value === 'books') {
    // Show only user's own posts (My Updates)
    filtered = filtered.filter(post => post.user.id === currentUserId)
  } else if (activeTab.value === 'following') {
    // Show only posts from other users (Following)
    filtered = filtered.filter(post => post.user.id !== currentUserId)
  }
  // 'all' shows everything

  // Filter by activity type
  if (!selectedActivityTypes.value.includes('all')) {
    filtered = filtered.filter(post => selectedActivityTypes.value.includes(post.type))
  }

  return filtered
})

// Close filters dropdown when clicking outside
const handleClickOutside = () => {
  if (showFilters.value) {
    showFilters.value = false
  }
}

onMounted(async () => {
  loading.value = true

  try {
    // Fetch userBooks and feed in parallel for faster loading
    const [feedResponse, userBooksResponse] = await Promise.all([
      api.get('/social/feed/'),
      api.get('/reading/user-books/')
    ])

    console.log('Feed API response:', feedResponse.data)

    // Store userBooks
    userBooks.value = userBooksResponse.data?.results || userBooksResponse.data || []

    // DRF returns paginated results
    const feedData = feedResponse.data?.results || feedResponse.data || []

    // Transform API data to match expected format
    const currentUserId = authStore.user?.id

    posts.value = feedData.map(item => {
      // Get book data from API
      const bookTitle = item.book_data?.title || 'Unknown'
      const bookAuthor = item.book_data?.authors?.map(a => a.name).join(', ') || 'Unknown Author'
      const bookCover = item.book_data?.cover_image || item.preview_image
      const bookId = item.book_data?.id || item.object_id

      // Parse rating and progress from preview_text
      let rating = null
      let progress = null

      if (item.feed_type === 'book_finished' && item.preview_text) {
        // Format: "finished reading BookTitle and rated it X/5"
        const match = item.preview_text.match(/rated it ([\d.]+)\/5/)
        if (match) {
          rating = parseFloat(match[1])
        }
      } else if (item.feed_type === 'progress_update' && item.preview_text) {
        // Format: "made X% progress on BookTitle"
        const match = item.preview_text.match(/made (\d+)% progress/)
        if (match) {
          progress = parseInt(match[1])
        }
      }

      return {
        id: item.id,
        user: {
          id: item.actor.id,
          name: item.actor.id === currentUserId ? 'You' : `${item.actor.first_name} ${item.actor.last_name}`,
          avatar: item.actor.avatar,
        },
        type: item.feed_type === 'book_finished' ? 'finished' :
              item.feed_type === 'quote_added' ? 'quote' :
              item.feed_type === 'progress_update' ? 'progress' :
              item.feed_type === 'book_started' ? 'started' : item.feed_type,
        timestamp: formatTimestamp(item.created_at),
        rawTimestamp: item.created_at,
        bookId: bookId,
        book: {
          title: bookTitle,
          author: bookAuthor,
          cover: bookCover,
        },
        content: item.feed_type === 'quote_added' ? {
          quote: item.preview_text.split(' - ')[0].replace(/^"|"$/g, ''),
          note: null
        } : item.feed_type === 'book_finished' ? {
          rating: rating,
          review: item.review_data || null
        } : item.feed_type === 'progress_update' ? {
          progress: progress,
          note: item.preview_text
        } : item.feed_type === 'book_started' || item.feed_type === 'want_to_read' ? {
          note: null
        } : {
          note: item.preview_text
        },
        stats: { likes: 0, comments: 0, hasLiked: false }
      }
    })

    loading.value = false
  } catch (err) {
    console.error('Feed error:', err)

    // Fallback to store data if API fails
    await Promise.all([
      quotesStore.fetchQuotes(),
      quotesStore.fetchTags(),
      userBooksStore.fetchBooks()
    ])
    posts.value = realFeedPosts.value
    loading.value = false
  }

  // Add click outside listener
  document.addEventListener('click', handleClickOutside)

  // Fetch recommendations in background
  fetchRecommendations()
})

// Fetch recommendations for sidebar
const fetchRecommendations = async () => {
  loadingRecommendations.value = true
  try {
    const [books, profile] = await Promise.all([
      recommendationsService.getForYouBooks(6),
      recommendationsService.getTasteProfile()
    ])
    recommendedBooks.value = books
    tasteProfile.value = profile
  } catch (error) {
    console.error('Error fetching recommendations:', error)
  } finally {
    loadingRecommendations.value = false
  }
}

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const handleBookAdded = (newUserBook) => {
  userBooks.value.push(newUserBook)
}

const handleBookUpdated = (updatedUserBook) => {
  const index = userBooks.value.findIndex(ub => ub.id === updatedUserBook.id)
  if (index !== -1) {
    userBooks.value[index] = updatedUserBook
  }
}
</script>

<template>
  <div class="animate-in fade-in duration-700">
    <!-- Page Container with max width -->
    <div class="w-full max-w-[1600px] mx-auto px-6 py-12">

      <!-- Page Header -->
      <header class="mb-12">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Users :size="24" class="text-indigo-400" />
          </div>
          <span class="text-page-meta font-bold text-indigo-400 uppercase tracking-[0.3em]">Activity Stream</span>
        </div>
        <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
          Reading OS <span class="text-indigo-500">Feed</span>
        </h1>
        <p class="text-page-subtitle text-slate-400 leading-relaxed max-w-2xl">
          See what your reading community is up to. Discover new books, insights, and reading milestones.
        </p>
      </header>

      <!-- Main Grid: Feed + Sidebar -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">

        <!-- LEFT COLUMN: Main Feed -->
        <div class="lg:col-span-8 min-w-0">

      <!-- Filter Tabs -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
        <div class="flex items-center gap-1 p-1 bg-slate-900/80 rounded-2xl border border-slate-800 overflow-x-auto">
          <button
            @click="activeTab = 'all'"
            :class="[
              'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
              activeTab === 'all' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'
            ]"
          >
            <Sparkles :size="14" />
            <span class="hidden sm:inline">All Activity</span>
            <span class="sm:hidden">All</span>
          </button>
          <button
            @click="activeTab = 'following'"
            :class="[
              'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
              activeTab === 'following' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'
            ]"
          >
            <Users :size="14" />
            <span class="hidden sm:inline">Following</span>
            <span class="sm:hidden">Follow</span>
          </button>
          <button
            @click="activeTab = 'books'"
            :class="[
              'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
              activeTab === 'books' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'
            ]"
          >
            <TrendingUp :size="14" />
            <span class="hidden sm:inline">My Updates</span>
            <span class="sm:hidden">Mine</span>
          </button>
          <button
            @click="activeTab = 'discover'"
            :class="[
              'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
              activeTab === 'discover' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20' : 'text-slate-500 hover:text-slate-300'
            ]"
          >
            <Compass :size="14" />
            <span class="hidden sm:inline">Discover</span>
            <span class="sm:hidden">Find</span>
          </button>
        </div>

        <button
          @click.stop="showFilters = !showFilters"
          class="flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-all text-xs sm:text-sm font-bold relative shrink-0"
        >
          <Filter :size="16" />
          <span class="hidden sm:inline">Filters</span>
          <ChevronDown :size="14" :class="{ 'rotate-180': showFilters }" class="transition-transform" />

          <!-- Filters Dropdown -->
          <div
            v-if="showFilters"
            @click.stop
            class="absolute right-0 top-12 w-80 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl z-[100]"
          >
            <div class="p-4">
              <h3 class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Activity Types</h3>
              <div class="space-y-2">
                <button
                  v-for="type in activityTypes"
                  :key="type.value"
                  @click="toggleActivityType(type.value)"
                  :class="[
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                    isActivityTypeSelected(type.value)
                      ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                      : 'text-slate-400 hover:bg-slate-800 border border-transparent'
                  ]"
                >
                  <component :is="type.icon" :size="16" />
                  {{ type.label }}
                  <CheckCircle
                    v-if="isActivityTypeSelected(type.value)"
                    :size="14"
                    class="ml-auto text-indigo-400"
                  />
                </button>
              </div>
            </div>

            <div class="p-4 pt-3 border-t border-slate-800 flex gap-2 bg-slate-900/50">
              <button
                @click="selectedActivityTypes = ['all']; showFilters = false"
                class="flex-1 px-4 py-2 rounded-lg bg-slate-800 text-slate-300 text-xs font-bold hover:bg-slate-700 transition-colors"
              >
                Reset
              </button>
              <button
                @click="showFilters = false"
                class="flex-1 px-4 py-2 rounded-lg bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-400 transition-colors"
              >
                Apply
              </button>
            </div>
          </div>
        </button>
      </div>

      <!-- Feed Stream -->
      <div v-if="activeTab === 'discover'">
        <DiscoverTab />
      </div>
      <div v-else class="space-y-8">
        <div v-if="loading" class="space-y-8">
          <div v-for="n in 3" :key="n" class="h-64 glass bg-slate-900/50 rounded-2xl animate-pulse flex items-center justify-center">
            <div class="w-12 h-12 rounded-full border-4 border-slate-800 border-t-indigo-500 animate-spin" />
          </div>
        </div>

        <template v-else>
          <FeedPostCard
            v-for="post in filteredPosts"
            :key="post.id"
            :post="post"
            :user-books="userBooks"
            @book-added="handleBookAdded"
            @book-updated="handleBookUpdated"
          />

          <div class="flex justify-center pt-8">
            <button class="px-8 py-4 rounded-2xl bg-slate-900 border border-slate-800 text-white font-bold hover:bg-slate-800 hover:border-slate-700 transition-all flex items-center gap-3 active:scale-95">
              <TrendingUp :size="20" class="text-indigo-400" />
              Load Older Activity
            </button>
          </div>
        </template>
      </div>
        </div>

        <!-- RIGHT COLUMN: Recommendations Sidebar -->
        <div class="lg:col-span-4 min-w-0 space-y-6">

          <!-- For You - Recommended Books -->
          <div class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <div class="flex items-center justify-between mb-5">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                  <Sparkles :size="16" class="text-indigo-400" />
                </div>
                <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">For You</h3>
              </div>
              <router-link
                to="/discover"
                class="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
              >
                See All <ArrowRight :size="12" />
              </router-link>
            </div>

            <!-- Loading State -->
            <div v-if="loadingRecommendations" class="space-y-4">
              <div v-for="n in 3" :key="n" class="flex items-center gap-3 animate-pulse">
                <div class="w-12 h-16 rounded-lg bg-slate-800" />
                <div class="flex-1 space-y-2">
                  <div class="h-3 bg-slate-800 rounded w-3/4" />
                  <div class="h-2 bg-slate-800 rounded w-1/2" />
                </div>
              </div>
            </div>

            <!-- Recommended Books List -->
            <div v-else-if="recommendedBooks.length > 0" class="space-y-1">
              <router-link
                v-for="book in recommendedBooks.slice(0, 5)"
                :key="book.id"
                :to="`/books/${book.id}`"
                class="group flex items-center gap-3 p-2 -mx-1 rounded-xl hover:bg-white/5 transition-all"
              >
                <div class="shrink-0 w-14 h-20 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center">
                  <img
                    v-if="book.cover_image"
                    :src="book.cover_image"
                    :alt="book.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    @error="(e) => e.target.style.display = 'none'"
                  />
                  <BookOpen v-else :size="18" class="text-slate-600" />
                </div>
                <div class="flex-1 min-w-0 py-0.5">
                  <h4 class="font-bold text-white text-sm leading-snug line-clamp-2 group-hover:text-indigo-400 transition-colors">
                    {{ book.title }}
                  </h4>
                  <p class="text-slate-400 text-xs truncate mt-0.5">
                    {{ book.authors?.map(a => a.name).join(', ') || 'Unknown' }}
                  </p>
                  <!-- Match info + Themes on same area -->
                  <div class="flex items-center gap-1.5 mt-1.5 flex-wrap">
                    <span v-if="book.match_score" class="text-xs font-bold text-indigo-400">
                      {{ Math.round(book.match_score) }}%
                    </span>
                    <span v-if="book.match_highlights?.length" class="text-xs text-slate-500">
                      · {{ book.match_highlights.join(', ') }}
                    </span>
                  </div>
                  <div v-if="book.themes?.length" class="flex gap-1.5 mt-1.5 flex-wrap">
                    <span
                      v-for="theme in book.themes.slice(0, 2)"
                      :key="theme"
                      class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-400"
                    >
                      {{ theme }}
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
                Rate more books to get personalized recommendations
              </p>
              <router-link
                to="/discover"
                class="inline-flex items-center gap-1 mt-3 text-xs text-indigo-400 hover:text-indigo-300 font-bold transition-colors"
              >
                Explore Books <ArrowRight :size="12" />
              </router-link>
            </div>
          </div>

          <!-- Your Reading DNA (mini version) -->
          <div v-if="tasteProfile && tasteProfile.vote_count > 0" class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <div class="flex items-center gap-3 mb-5">
              <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Dna :size="16" class="text-indigo-400" />
              </div>
              <div>
                <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Your DNA</h3>
                <p class="text-slate-600 text-[9px]">{{ tasteProfile.vote_count }} books rated</p>
              </div>
            </div>

            <!-- Mini DNA bars -->
            <div class="space-y-3">
              <div v-if="tasteProfile.pace_preference !== undefined">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-bold text-slate-500 uppercase">Pace</span>
                  <span class="text-[9px] text-slate-600">{{ tasteProfile.pace_preference > 0.5 ? 'Fast' : 'Slow' }}</span>
                </div>
                <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-indigo-500 rounded-full transition-all"
                    :style="{ width: `${tasteProfile.pace_preference * 100}%` }"
                  />
                </div>
              </div>
              <div v-if="tasteProfile.complexity_tolerance !== undefined">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-bold text-slate-500 uppercase">Complexity</span>
                  <span class="text-[9px] text-slate-600">{{ tasteProfile.complexity_tolerance > 0.5 ? 'Dense' : 'Light' }}</span>
                </div>
                <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-purple-500 rounded-full transition-all"
                    :style="{ width: `${tasteProfile.complexity_tolerance * 100}%` }"
                  />
                </div>
              </div>
              <div v-if="tasteProfile.darkness_tolerance !== undefined">
                <div class="flex items-center justify-between mb-1">
                  <span class="text-[9px] font-bold text-slate-500 uppercase">Tone</span>
                  <span class="text-[9px] text-slate-600">{{ tasteProfile.darkness_tolerance > 0.5 ? 'Dark' : 'Light' }}</span>
                </div>
                <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-rose-500 rounded-full transition-all"
                    :style="{ width: `${tasteProfile.darkness_tolerance * 100}%` }"
                  />
                </div>
              </div>
            </div>

            <router-link
              to="/discover"
              class="mt-4 block text-center text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              View Full Profile
            </router-link>
          </div>

          <!-- Quick Mood Picks -->
          <div class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px] mb-4">Quick Picks</h3>
            <div class="grid grid-cols-2 gap-2">
              <router-link
                to="/discover?mood=peaceful"
                class="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 transition-all text-center group"
              >
                <span class="text-lg block mb-1">🌿</span>
                <span class="text-[10px] font-bold text-emerald-400 group-hover:text-emerald-300">Peaceful</span>
              </router-link>
              <router-link
                to="/discover?mood=challenge"
                class="p-3 rounded-xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-all text-center group"
              >
                <span class="text-lg block mb-1">🧠</span>
                <span class="text-[10px] font-bold text-purple-400 group-hover:text-purple-300">Challenge</span>
              </router-link>
              <router-link
                to="/discover?mood=emotional"
                class="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-all text-center group"
              >
                <span class="text-lg block mb-1">💔</span>
                <span class="text-[10px] font-bold text-rose-400 group-hover:text-rose-300">Emotional</span>
              </router-link>
              <router-link
                to="/discover?mood=quick"
                class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 hover:bg-amber-500/20 transition-all text-center group"
              >
                <span class="text-lg block mb-1">⚡</span>
                <span class="text-[10px] font-bold text-amber-400 group-hover:text-amber-300">Quick Read</span>
              </router-link>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.5);
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
