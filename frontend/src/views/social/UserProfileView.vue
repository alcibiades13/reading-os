<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { socialService } from '@/services/socialService'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useAuthStore } from '@/stores/authStore'
import FollowButton from '@/components/social/FollowButton.vue'
import BookCard from '@/components/BookCard.vue'
import api from '@/services/api'
import {
  BookOpen, Quote, Users, TrendingUp, Heart,
  ArrowLeft, Sparkles, Bookmark, ExternalLink, Copy, Star,
  LayoutGrid, List, ArrowUpRight
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useUserBooksStore()
const authStore = useAuthStore()

const userId = computed(() => route.params.id)
const userProfile = ref(null)
const userBooks = ref([])
const userStats = ref(null)
const sharedBooks = ref([])
const matchScore = ref(0)
const loading = ref(true)
const activeTab = ref('books') // 'books', 'quotes', 'followers', 'following'
const booksSubTab = ref('all') // 'all', 'reading', 'finished', 'want_to_read'
const viewMode = ref('list') // 'grid' or 'list' - default to list for UserProfileView
const userQuotes = ref([])
const followers = ref([])
const following = ref([])
const quotesLoading = ref(false)
const booksPage = ref(1)
const hasMoreBooks = ref(false)
const loadingMoreBooks = ref(false)

// Watch for route parameter changes to reload profile
watch(() => route.params.id, async (newId, oldId) => {
  if (newId && newId !== oldId) {
    console.log('Route changed from user', oldId, 'to user', newId)
    loading.value = true

    // Reset data
    userProfile.value = null
    userBooks.value = []
    userStats.value = null
    sharedBooks.value = []
    matchScore.value = 0
    userQuotes.value = []
    followers.value = []
    following.value = []
    activeTab.value = 'books'
    booksPage.value = 1
    hasMoreBooks.value = false

    // Load new user's data
    await Promise.all([
      loadUserProfile(),
      loadUserBooks(),
      loadUserStats(),
    ])

    // Load current user's books for comparison (only if viewing someone else)
    if (newId != authStore.user?.id) {
      await booksStore.fetchBooks()
    }

    calculateMatchAndSharedBooks()
    loading.value = false
  }
})

onMounted(async () => {
  // Load the viewed user's data
  await Promise.all([
    loadUserProfile(),
    loadUserBooks(),
    loadUserStats(),
  ])

  // Load current user's books for comparison (only if viewing someone else)
  if (userId.value != authStore.user?.id) {
    await booksStore.fetchBooks()
  }

  calculateMatchAndSharedBooks()
  loading.value = false
})

const loadUserProfile = async () => {
  try {
    userProfile.value = await socialService.getUserProfile(userId.value)
    console.log('Loaded user profile:', userProfile.value)
    console.log('Friendship ID:', userProfile.value?.friendship_id)
    console.log('Is following:', userProfile.value?.is_following)
  } catch (error) {
    console.error('Error loading user profile:', error)
  }
}

const loadUserBooks = async (append = false) => {
  try {
    const response = await api.get(`/users/${userId.value}/books/`, {
      params: {
        page: booksPage.value,
        page_size: 100 // Load 100 at a time
      }
    })

    const newBooks = response.data.results || response.data

    if (append) {
      userBooks.value = [...userBooks.value, ...newBooks]
    } else {
      userBooks.value = newBooks
    }

    // Check if there are more books
    hasMoreBooks.value = response.data.next !== null
  } catch (error) {
    console.error('Error loading user books:', error)
  }
}

const loadMoreBooks = async () => {
  if (!hasMoreBooks.value || loadingMoreBooks.value) return

  loadingMoreBooks.value = true
  booksPage.value += 1
  await loadUserBooks(true)
  loadingMoreBooks.value = false
}

const loadUserStats = async () => {
  try {
    userStats.value = await socialService.getUserStats(userId.value)
  } catch (error) {
    console.error('Error loading user stats:', error)
  }
}

const loadFollowers = async () => {
  try {
    followers.value = await socialService.getUserFollowers(userId.value)
  } catch (error) {
    console.error('Error loading followers:', error)
  }
}

const loadFollowing = async () => {
  try {
    following.value = await socialService.getUserFollowing(userId.value)
  } catch (error) {
    console.error('Error loading following:', error)
  }
}

const loadUserQuotes = async () => {
  quotesLoading.value = true
  try {
    const response = await api.get('/reading/quotes/', {
      params: { user: userId.value }
    })
    // Handle paginated response
    userQuotes.value = response.data.results || response.data
    console.log('Loaded quotes:', userQuotes.value)
  } catch (error) {
    console.error('Error loading user quotes:', error)
  } finally {
    quotesLoading.value = false
  }
}

const switchTab = async (tab) => {
  activeTab.value = tab

  // Load data on demand
  if (tab === 'quotes' && userQuotes.value.length === 0) {
    await loadUserQuotes()
  } else if (tab === 'followers' && followers.value.length === 0) {
    await loadFollowers()
  } else if (tab === 'following' && following.value.length === 0) {
    await loadFollowing()
  }
}

const calculateMatchAndSharedBooks = () => {
  const currentUserBooks = booksStore.books.map(ub => ub.book)
  const otherUserBooks = userBooks.value.map(ub => ub.book)

  // Find shared books
  const shared = userBooks.value.filter(userBook =>
    booksStore.books.some(myBook => myBook.book.id === userBook.book.id)
  )
  sharedBooks.value = shared

  // Calculate match score
  const currentUserGenres = [...new Set(currentUserBooks.flatMap(b => b.genres?.map(g => g.name) || []))]
  const otherUserGenres = [...new Set(otherUserBooks.flatMap(b => b.genres?.map(g => g.name) || []))]

  matchScore.value = socialService.calculateMatchScore(
    currentUserBooks,
    otherUserBooks,
    currentUserGenres,
    otherUserGenres
  )
}

const filteredBooks = computed(() => {
  if (booksSubTab.value === 'all') return userBooks.value
  return userBooks.value.filter(ub => ub.status === booksSubTab.value)
})

const handleFollow = async (userId) => {
  try {
    console.log('Attempting to follow user:', userId)
    const result = await socialService.followUser(userId)
    console.log('Follow result:', result)
    console.log('Follow result data:', result.data)

    if (userProfile.value && result.data?.id) {
      // Update local state with the friendship data
      userProfile.value.is_following = true
      userProfile.value.followers_count++
      userProfile.value.friendship_id = result.data.id
      console.log('Updated profile - is_following:', userProfile.value.is_following)
      console.log('Updated profile - friendship_id:', userProfile.value.friendship_id)
    } else {
      console.error('No friendship_id in response:', result)
    }
  } catch (error) {
    console.error('Error following user:', error)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
  }
}

const handleUnfollow = async () => {
  try {
    console.log('Attempting to unfollow, friendship_id:', userProfile.value?.friendship_id)
    // Use friendship_id for unfollow
    if (userProfile.value?.friendship_id) {
      const result = await socialService.unfollowUser(userProfile.value.friendship_id)
      console.log('Unfollow result:', result)
      if (userProfile.value) {
        userProfile.value.is_following = false
        userProfile.value.followers_count--
        userProfile.value.friendship_id = null
      }
    } else {
      console.error('No friendship_id available for unfollow')
    }
  } catch (error) {
    console.error('Error unfollowing user:', error)
    console.error('Error response:', error.response?.data)
    console.error('Error status:', error.response?.status)
  }
}

const goBack = () => {
  router.back()
}

const copyQuote = async (quote) => {
  try {
    await navigator.clipboard.writeText(quote.text)
    // TODO: Add toast notification
    console.log('Quote copied to clipboard!')
  } catch (error) {
    console.error('Failed to copy quote:', error)
  }
}

// Helper functions for list view
const getCoverUrl = (book) => {
  if (!book) return null
  return book.cover_image || null
}

const getStatusBadge = (status) => {
  const badges = {
    'currently_reading': {
      text: 'Reading',
      class: 'bg-indigo-500 text-white'
    },
    'reading': {
      text: 'Reading',
      class: 'bg-indigo-500 text-white'
    },
    'read': {
      text: 'Finished',
      class: 'bg-emerald-500/90 text-white'
    },
    'finished': {
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
</script>

<template>
  <div class="min-h-screen bg-slate-950 pb-16">
    <div class="max-w-7xl mx-auto px-6 pt-8">
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-32">
        <div class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Profile Content -->
      <div v-else-if="userProfile" class="animate-in fade-in duration-700">
        <!-- Back Button -->
        <button
          @click="goBack"
          class="mb-8 flex items-center gap-2 text-slate-400 hover:text-white transition-colors group"
        >
          <ArrowLeft :size="18" class="group-hover:-translate-x-1 transition-transform" />
          <span class="text-xs font-bold uppercase tracking-widest">Back</span>
        </button>

        <!-- Profile Header -->
        <div class="p-8 rounded-[2rem] glass border-slate-800 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10 mb-8">
          <div class="flex flex-col md:flex-row items-start gap-8">
            <!-- Avatar -->
            <div class="relative flex-shrink-0">
              <div class="w-32 h-32 rounded-3xl overflow-hidden ring-4 ring-indigo-500/20 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                <img
                  v-if="userProfile.avatar"
                  :src="userProfile.avatar"
                  :alt="userProfile.username"
                  class="w-full h-full object-cover"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <span v-if="!userProfile.avatar" class="text-5xl font-black text-white">
                  {{ userProfile.first_name?.[0]?.toUpperCase() || '?' }}
                </span>
              </div>
              <div class="absolute -bottom-2 -right-2 w-8 h-8 rounded-full bg-emerald-500 border-4 border-slate-950 flex items-center justify-center">
                <div class="w-2 h-2 rounded-full bg-white" />
              </div>
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-4">
                <div>
                  <h1 class="text-3xl font-black text-white mb-2">
                    {{ userProfile.first_name }} {{ userProfile.last_name }}
                  </h1>
                  <p class="text-sm text-slate-400 font-medium mb-1">@{{ userProfile.username }}</p>
                  <p class="text-sm text-slate-300 max-w-2xl">{{ userProfile.bio || 'No bio yet.' }}</p>
                </div>

                <!-- Follow Button (only show if not viewing own profile) -->
                <FollowButton
                  v-if="userId != authStore.user?.id"
                  :userId="userProfile.id"
                  :initialState="userProfile.is_following ? 'following' : 'not_following'"
                  :isFollower="userProfile.is_follower"
                  size="large"
                  @follow="handleFollow"
                  @unfollow="handleUnfollow"
                />
              </div>

              <!-- Stats Row - Clickable -->
              <div class="flex flex-wrap gap-3">
                <button
                  @click="switchTab('books')"
                  :class="[
                    'flex items-center gap-2 px-4 py-3 rounded-2xl transition-all group',
                    activeTab === 'books'
                      ? 'bg-indigo-500 shadow-lg shadow-indigo-500/20'
                      : 'bg-white/5 hover:bg-white/10'
                  ]"
                >
                  <BookOpen :size="18" :class="activeTab === 'books' ? 'text-white' : 'text-indigo-400'" />
                  <span class="text-xl font-black text-white">{{ userProfile.books_read_count || 0 }}</span>
                  <span :class="['text-xs font-black uppercase tracking-widest', activeTab === 'books' ? 'text-white/80' : 'text-slate-400 group-hover:text-indigo-400']">Books</span>
                </button>
                <button
                  @click="switchTab('quotes')"
                  :class="[
                    'flex items-center gap-2 px-4 py-3 rounded-2xl transition-all group',
                    activeTab === 'quotes'
                      ? 'bg-purple-500 shadow-lg shadow-purple-500/20'
                      : 'bg-white/5 hover:bg-white/10'
                  ]"
                >
                  <Quote :size="18" :class="activeTab === 'quotes' ? 'text-white' : 'text-purple-400'" />
                  <span class="text-xl font-black text-white">{{ userProfile.quotes_count || 0 }}</span>
                  <span :class="['text-xs font-black uppercase tracking-widest', activeTab === 'quotes' ? 'text-white/80' : 'text-slate-400 group-hover:text-purple-400']">Quotes</span>
                </button>
                <button
                  @click="switchTab('followers')"
                  :class="[
                    'flex items-center gap-2 px-4 py-3 rounded-2xl transition-all group',
                    activeTab === 'followers'
                      ? 'bg-emerald-500 shadow-lg shadow-emerald-500/20'
                      : 'bg-white/5 hover:bg-white/10'
                  ]"
                >
                  <Users :size="18" :class="activeTab === 'followers' ? 'text-white' : 'text-emerald-400'" />
                  <span class="text-xl font-black text-white">{{ userProfile.followers_count || 0 }}</span>
                  <span :class="['text-xs font-black uppercase tracking-widest', activeTab === 'followers' ? 'text-white/80' : 'text-slate-400 group-hover:text-emerald-400']">Followers</span>
                </button>
                <button
                  @click="switchTab('following')"
                  :class="[
                    'flex items-center gap-2 px-4 py-3 rounded-2xl transition-all group',
                    activeTab === 'following'
                      ? 'bg-amber-500 shadow-lg shadow-amber-500/20'
                      : 'bg-white/5 hover:bg-white/10'
                  ]"
                >
                  <TrendingUp :size="18" :class="activeTab === 'following' ? 'text-white' : 'text-amber-400'" />
                  <span class="text-xl font-black text-white">{{ userProfile.following_count || 0 }}</span>
                  <span :class="['text-xs font-black uppercase tracking-widest', activeTab === 'following' ? 'text-white/80' : 'text-slate-400 group-hover:text-amber-400']">Following</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Layout Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <!-- Main Content -->
          <div class="lg:col-span-8 space-y-8">
            <!-- BOOKS TAB -->
            <div v-if="activeTab === 'books'">
              <!-- Books Sub-Tab Navigation and View Toggle -->
              <div class="flex flex-wrap items-center justify-between gap-4 mb-6">
                <div class="flex items-center gap-2 overflow-x-auto pb-2">
                  <button
                    v-for="tab in [
                      { id: 'all', label: 'All Books', icon: BookOpen },
                      { id: 'reading', label: 'Reading', icon: BookOpen },
                      { id: 'finished', label: 'Finished', icon: BookOpen },
                      { id: 'want_to_read', label: 'Want to Read', icon: Heart }
                    ]"
                    :key="tab.id"
                    @click="booksSubTab = tab.id"
                    :class="[
                      'flex items-center gap-2 px-6 py-3 rounded-2xl font-black text-xs uppercase tracking-widest transition-all flex-shrink-0',
                      booksSubTab === tab.id
                        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                        : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
                    ]"
                  >
                    <component :is="tab.icon" :size="14" />
                    <span>{{ tab.label }}</span>
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

              <!-- Books Grid View -->
              <div v-if="viewMode === 'grid' && filteredBooks.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6">
                <BookCard
                  v-for="userBook in filteredBooks"
                  :key="userBook.id"
                  :book="userBook"
                  :status="userBook.status"
                  :progress="userBook.current_page"
                  :readonly="true"
                />
              </div>

              <!-- Books List/Table View -->
              <div v-else-if="viewMode === 'list' && filteredBooks.length > 0" class="space-y-3">
                <!-- Table Header -->
                <div class="flex items-center gap-4 px-4 py-2 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">
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
                  v-for="userBook in filteredBooks"
                  :key="userBook.id"
                  :to="`/books/${userBook.book.id}`"
                  class="group flex items-center gap-4 p-4 rounded-2xl glass border-slate-800 hover:border-indigo-500/30 transition-all duration-300"
                >
                  <!-- Cover -->
                  <div class="shrink-0 w-12 h-16 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-lg flex items-center justify-center">
                    <img
                      v-if="getCoverUrl(userBook.book)"
                      :src="getCoverUrl(userBook.book)"
                      :alt="userBook.book?.title"
                      class="w-full h-full object-cover"
                      @error="(e) => e.target.style.display = 'none'"
                    />
                    <BookOpen v-else :size="20" class="text-slate-600" />
                  </div>

                  <!-- Title & Author -->
                  <div class="flex-1 min-w-0">
                    <h3 class="font-bold text-white text-sm truncate group-hover:text-indigo-400 transition-colors">
                      {{ userBook.book?.title }}
                    </h3>
                    <p class="text-slate-400 text-xs truncate">
                      {{ userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author' }}
                    </p>
                  </div>

                  <!-- Star Rating (10-point scale) -->
                  <div class="hidden sm:flex flex-col items-center gap-1 w-32">
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

                  <!-- Date Read -->
                  <div class="hidden md:block text-xs text-slate-500 w-24 text-center">
                    {{ userBook.finished_at ? new Date(userBook.finished_at).toLocaleDateString() : '—' }}
                  </div>

                  <!-- Date Added -->
                  <div class="hidden lg:block text-xs text-slate-500 w-24 text-center">
                    {{ userBook.created_at ? new Date(userBook.created_at).toLocaleDateString() : '—' }}
                  </div>

                  <!-- Status Badge -->
                  <div class="hidden xl:flex w-28 justify-center">
                    <span
                      v-if="getStatusBadge(userBook.status)"
                      :class="['px-2 py-1 rounded-lg text-[9px] font-bold whitespace-nowrap', getStatusBadge(userBook.status).class]"
                    >
                      {{ getStatusBadge(userBook.status).text }}
                    </span>
                  </div>

                  <!-- Actions -->
                  <div class="flex items-center gap-2 w-16 justify-end">
                    <button
                      v-if="userBook.is_favorite"
                      @click.stop
                      class="p-2 rounded-lg"
                    >
                      <Heart :size="16" class="text-red-400 fill-current" />
                    </button>
                    <div class="text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowUpRight :size="18" />
                    </div>
                  </div>
                </router-link>
              </div>

              <!-- Load More Button -->
              <div v-if="hasMoreBooks && filteredBooks.length > 0" class="flex justify-center pt-8">
                <button
                  @click="loadMoreBooks"
                  :disabled="loadingMoreBooks"
                  class="px-6 py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-bold hover:bg-indigo-500 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <span v-if="loadingMoreBooks">Loading...</span>
                  <span v-else>Load More Books</span>
                </button>
              </div>

              <!-- Empty State -->
              <div v-else-if="filteredBooks.length === 0" class="p-16 rounded-3xl glass text-center opacity-40">
                <BookOpen :size="48" class="mx-auto mb-4 text-slate-600" />
                <p class="text-slate-400 font-medium">No books in this category yet.</p>
              </div>
            </div>

            <!-- QUOTES TAB -->
            <div v-if="activeTab === 'quotes'">
              <!-- Loading State -->
              <div v-if="quotesLoading" class="flex items-center justify-center py-32">
                <div class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              </div>

              <!-- Quotes List -->
              <div v-else-if="userQuotes.length > 0" class="space-y-6">
                <div
                  v-for="quote in userQuotes"
                  :key="quote.id"
                  class="group relative glass bg-slate-900/40 rounded-3xl p-8 border border-slate-800/50 hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/5"
                >
                  <!-- Quote Mark -->
                  <div class="absolute -top-4 -left-2 text-7xl text-indigo-500/10 font-serif pointer-events-none select-none">"</div>

                  <div class="relative space-y-6">
                    <!-- Quote Content -->
                    <p class="text-lg font-medium text-slate-100 leading-relaxed italic font-serif">
                      {{ quote.text }}
                    </p>

                    <!-- Book Info and Actions -->
                    <div class="flex items-center justify-between gap-4 pt-3 border-t border-slate-800/50">
                      <div class="flex-1 min-w-0 space-y-1.5">
                        <div class="flex items-center gap-2 min-w-0">
                          <h4
                            @click="quote.book ? router.push(`/books/${quote.book}`) : null"
                            :class="quote.book ? 'cursor-pointer hover:text-indigo-400 transition-colors' : ''"
                            class="text-white font-bold text-sm truncate"
                          >
                            {{ quote.book_title || 'Unknown Book' }}
                          </h4>
                          <span class="text-slate-600 hidden sm:inline flex-shrink-0">·</span>
                          <p class="text-indigo-400 font-medium text-sm truncate">{{ quote.book_author || 'Unknown Author' }}</p>
                        </div>
                        <div class="flex items-center gap-3 text-xs text-slate-500 font-bold uppercase tracking-wider">
                          <span v-if="quote.chapter" class="flex items-center gap-1">
                            <span class="text-slate-600">Ch.</span> {{ quote.chapter }}
                          </span>
                          <span v-if="quote.page_number" class="flex items-center gap-1">
                            <span class="text-slate-600">Pg.</span> {{ quote.page_number }}
                          </span>
                        </div>
                      </div>

                      <!-- Actions on the right -->
                      <div class="flex items-center gap-1 flex-shrink-0">
                        <button
                          @click="copyQuote(quote)"
                          class="p-2 rounded-full text-slate-500 hover:text-indigo-400 hover:bg-slate-800 transition-all"
                        >
                          <Copy :size="20" />
                        </button>
                        <button
                          class="p-2 rounded-full text-slate-500 hover:text-amber-400 hover:bg-slate-800 transition-all"
                        >
                          <Bookmark :size="20" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="p-16 rounded-3xl glass text-center opacity-40">
                <Quote :size="48" class="mx-auto mb-4 text-slate-600" />
                <p class="text-slate-400 font-medium">No quotes yet.</p>
              </div>
            </div>

            <!-- FOLLOWERS TAB -->
            <div v-if="activeTab === 'followers'">
              <div v-if="followers.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div
                  v-for="follower in followers"
                  :key="follower.id"
                  class="p-6 rounded-3xl glass border-white/5 hover:border-indigo-500/30 transition-all group cursor-pointer"
                  @click="router.push(`/users/${follower.id}`)"
                >
                  <div class="flex items-start gap-4">
                    <div class="w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <img
                        v-if="follower.avatar"
                        :src="follower.avatar"
                        class="w-full h-full object-cover"
                        @error="(e) => e.target.style.display = 'none'"
                      />
                      <span v-if="!follower.avatar" class="text-2xl font-black text-white">
                        {{ follower.first_name?.[0]?.toUpperCase() || '?' }}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-lg font-black text-white truncate group-hover:text-indigo-400 transition-colors">
                        {{ follower.first_name }} {{ follower.last_name }}
                      </h3>
                      <p class="text-xs text-slate-400 mb-2">@{{ follower.username }}</p>
                      <div class="flex gap-4 text-xs text-slate-500">
                        <span>{{ follower.books_read_count }} books</span>
                        <span>{{ follower.followers_count }} followers</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="p-16 rounded-3xl glass text-center opacity-40">
                <Users :size="48" class="mx-auto mb-4 text-slate-600" />
                <p class="text-slate-400 font-medium">No followers yet.</p>
              </div>
            </div>

            <!-- FOLLOWING TAB -->
            <div v-if="activeTab === 'following'">
              <div v-if="following.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div
                  v-for="followedUser in following"
                  :key="followedUser.id"
                  class="p-6 rounded-3xl glass border-white/5 hover:border-indigo-500/30 transition-all group cursor-pointer"
                  @click="router.push(`/users/${followedUser.id}`)"
                >
                  <div class="flex items-start gap-4">
                    <div class="w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <img
                        v-if="followedUser.avatar"
                        :src="followedUser.avatar"
                        class="w-full h-full object-cover"
                        @error="(e) => e.target.style.display = 'none'"
                      />
                      <span v-if="!followedUser.avatar" class="text-2xl font-black text-white">
                        {{ followedUser.first_name?.[0]?.toUpperCase() || '?' }}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-lg font-black text-white truncate group-hover:text-indigo-400 transition-colors">
                        {{ followedUser.first_name }} {{ followedUser.last_name }}
                      </h3>
                      <p class="text-xs text-slate-400 mb-2">@{{ followedUser.username }}</p>
                      <div class="flex gap-4 text-xs text-slate-500">
                        <span>{{ followedUser.books_read_count }} books</span>
                        <span>{{ followedUser.followers_count }} followers</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="p-16 rounded-3xl glass text-center opacity-40">
                <TrendingUp :size="48" class="mx-auto mb-4 text-slate-600" />
                <p class="text-slate-400 font-medium">Not following anyone yet.</p>
              </div>
            </div>
          </div>

          <!-- Sidebar -->
          <div class="lg:col-span-4 space-y-8">
            <!-- Match Score Widget -->
            <div class="p-6 rounded-[2rem] glass border-slate-800 bg-gradient-to-br from-emerald-500/5 via-transparent to-indigo-500/5">
              <div class="flex items-center gap-3 mb-6">
                <div class="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <Sparkles :size="20" class="text-emerald-400" />
                </div>
                <div>
                  <h3 class="text-sm font-black text-white uppercase tracking-wider">Reading Compatibility</h3>
                  <p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">Kindred Spirit Score</p>
                </div>
              </div>

              <!-- Match Score Circle -->
              <div class="flex items-center justify-center mb-6">
                <div class="relative w-32 h-32">
                  <svg class="w-32 h-32 transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      stroke-width="8"
                      fill="none"
                      class="text-white/5"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="currentColor"
                      stroke-width="8"
                      fill="none"
                      :stroke-dasharray="`${matchScore * 3.51} 351.86`"
                      class="text-emerald-500 transition-all duration-1000"
                    />
                  </svg>
                  <div class="absolute inset-0 flex items-center justify-center">
                    <span class="text-4xl font-black text-white">{{ matchScore }}%</span>
                  </div>
                </div>
              </div>

              <!-- Match Details -->
              <div class="space-y-3">
                <div class="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <span class="text-xs text-slate-400 font-bold uppercase tracking-wider">Shared Books</span>
                  <span class="text-lg font-black text-white">{{ sharedBooks.length }}</span>
                </div>
                <div class="flex items-center justify-between p-3 rounded-xl bg-white/[0.02] border border-white/5">
                  <span class="text-xs text-slate-400 font-bold uppercase tracking-wider">Similar Genres</span>
                  <span class="text-lg font-black text-white">{{ userProfile.top_genres?.length || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Shared Books Widget -->
            <div v-if="sharedBooks.length > 0" class="p-6 rounded-[2rem] glass border-slate-800">
              <h3 class="text-sm font-black text-white uppercase tracking-wider mb-6">Books in Common</h3>
              <div class="space-y-4">
                <div
                  v-for="userBook in sharedBooks.slice(0, 5)"
                  :key="userBook.id"
                  class="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all cursor-pointer group"
                >
                  <div class="w-10 h-14 rounded-lg overflow-hidden flex-shrink-0 bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                    <img
                      v-if="userBook.book.cover_image"
                      :src="userBook.book.cover_image"
                      :alt="userBook.book.title"
                      class="w-full h-full object-cover"
                      @error="(e) => e.target.style.display = 'none'"
                    />
                    <BookOpen v-if="!userBook.book.cover_image" :size="16" class="text-slate-600" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-xs font-bold text-white truncate group-hover:text-indigo-400 transition-colors">
                      {{ userBook.book.title }}
                    </p>
                    <p class="text-[9px] text-slate-500 font-black uppercase tracking-widest truncate">
                      {{ userBook.book.authors?.[0]?.name || 'Unknown' }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Genres Widget -->
            <div v-if="userProfile.top_genres?.length" class="p-6 rounded-[2rem] glass border-slate-800">
              <h3 class="text-sm font-black text-white uppercase tracking-wider mb-6">Favorite Genres</h3>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="genre in userProfile.top_genres"
                  :key="genre"
                  class="px-3 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs font-black text-indigo-400 uppercase tracking-wider"
                >
                  {{ genre }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else class="flex flex-col items-center justify-center py-32 opacity-40">
        <Users :size="64" class="text-slate-700 mb-4" />
        <p class="text-slate-400 font-medium">User not found</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.animate-in {
  animation: fadeIn 0.7s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Light mode adjustments */
body.light .bg-slate-950 {
  background-color: #f8fafc !important;
}

body.light .text-white {
  color: #0f172a !important;
}

body.light .text-slate-300,
body.light .text-slate-400 {
  color: #64748b !important;
}

body.light .text-slate-500 {
  color: #94a3b8 !important;
}

body.light .border-slate-800 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}

body.light .bg-white\/5,
body.light .bg-white\/\[0\.02\] {
  background-color: rgba(0, 0, 0, 0.03) !important;
}

body.light .border-white\/5,
body.light .border-white\/10 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}
</style>
