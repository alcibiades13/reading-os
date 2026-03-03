<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { socialService } from '@/services/socialService'
import { useAuthStore } from '@/stores/authStore'
import FollowButton from '@/components/social/FollowButton.vue'
import BookCard from '@/components/BookCard.vue'
import TasteProfile from '@/components/recommendations/TasteProfile.vue'
import api, { contributionsAPI } from '@/services/api'
import {
  BookOpen, Quote, Users, TrendingUp, Heart,
  ArrowLeft, Sparkles, Bookmark, ExternalLink, Copy, Star,
  LayoutGrid, List, ArrowUpRight, Gift, Shield
} from 'lucide-vue-next'
import { getBookUrl } from '@/utils/bookUrl'
import { getTier } from '@/config/tiers'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const userId = computed(() => route.params.id)
const isOwnProfile = computed(() => String(userId.value) === String(authStore.user?.id))
const userProfile = ref(null)
const userBooks = ref([])
const userStats = ref(null)
const sharedBooks = ref([])
const matchScore = ref(0)
const readingDna = ref(null)
const loading = ref(true)
const activeTab = ref('books') // 'books', 'quotes', 'wishlist', 'followers', 'following'
const userWishlist = ref([])
const booksSubTab = ref('all') // 'all', 'reading', 'finished', 'want_to_read'
const viewMode = ref('list') // 'grid' or 'list' - default to list for UserProfileView
const userQuotes = ref([])
const followers = ref([])
const following = ref([])
const quotesLoading = ref(false)
const userReputation = ref(null)
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
    readingDna.value = null
    userQuotes.value = []
    userWishlist.value = []
    followers.value = []
    following.value = []
    activeTab.value = 'books'
    booksPage.value = 1
    hasMoreBooks.value = false

    userReputation.value = null

    // Load new user's data
    await Promise.all([
      loadUserProfile(),
      loadUserBooks(),
      loadUserStats(),
      contributionsAPI.userReputation(newId).then(r => userReputation.value = r.data).catch(() => {}),
    ])

    // Use data from backend profile response
    if (userProfile.value) {
      sharedBooks.value = userProfile.value.shared_books || []
      matchScore.value = userProfile.value.match_score || 0
      readingDna.value = userProfile.value.reading_dna || null
    }

    loading.value = false
  }
})

onMounted(async () => {
  // Load the viewed user's data
  await Promise.all([
    loadUserProfile(),
    loadUserBooks(),
    loadUserStats(),
    contributionsAPI.userReputation(userId.value).then(r => userReputation.value = r.data).catch(() => {}),
  ])

  // Use data from backend profile response
  if (userProfile.value) {
    sharedBooks.value = userProfile.value.shared_books || []
    matchScore.value = userProfile.value.match_score || 0
    readingDna.value = userProfile.value.reading_dna || null
  }

  loading.value = false
})

const userTier = computed(() => getTier(userReputation.value?.tier))

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

const loadUserWishlist = async () => {
  try {
    const { userBooksAPI } = await import('@/services/api')
    const response = await userBooksAPI.wishlist(userId.value)
    userWishlist.value = response.data
  } catch (error) {
    console.error('Error loading user wishlist:', error)
  }
}

const switchTab = async (tab) => {
  activeTab.value = tab

  // Load data on demand
  if (tab === 'quotes' && userQuotes.value.length === 0) {
    await loadUserQuotes()
  } else if (tab === 'wishlist' && userWishlist.value.length === 0) {
    await loadUserWishlist()
  } else if (tab === 'followers' && followers.value.length === 0) {
    await loadFollowers()
  } else if (tab === 'following' && following.value.length === 0) {
    await loadFollowing()
  }
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
  <div class="min-h-screen bg-slate-950 light:bg-slate-50 pb-20 lg:pb-16">
    <!-- Mobile Sticky Header -->
    <div class="lg:hidden sticky top-0 z-50 bg-slate-950/95 light:bg-white/95 backdrop-blur-xl border-b border-slate-800/50 light:border-slate-200 safe-area-top">
      <div class="flex items-center justify-between px-4 py-3">
        <button
          @click="goBack"
          class="p-2 -ml-2 rounded-xl text-slate-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-slate-800 light:hover:bg-slate-100 transition-all active:scale-95"
        >
          <ArrowLeft :size="20" />
        </button>

        <div v-if="userProfile" class="flex items-center gap-2 flex-1 min-w-0 px-3">
          <div class="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
            <img
              v-if="userProfile.avatar"
              :src="userProfile.avatar"
              :alt="userProfile.username"
              class="w-full h-full object-cover"
              @error="(e) => e.target.style.display = 'none'"
            />
            <span v-if="!userProfile.avatar" class="text-sm font-black text-white">
              {{ userProfile.first_name?.[0]?.toUpperCase() || '?' }}
            </span>
          </div>
          <span class="font-bold text-white light:text-slate-900 truncate">
            {{ userProfile.first_name }} {{ userProfile.last_name }}
          </span>
        </div>

        <FollowButton
          v-if="userProfile && userId != authStore.user?.id"
          :userId="userProfile.id"
          :initialState="userProfile.is_following ? 'following' : 'not_following'"
          :isFollower="userProfile.is_follower"
          size="small"
          @follow="handleFollow"
          @unfollow="handleUnfollow"
        />
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 lg:px-6 pt-4 lg:pt-8">
      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-32">
        <div class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <!-- Profile Content -->
      <div v-else-if="userProfile" class="animate-in fade-in duration-700">
        <!-- Back Button - Desktop Only -->
        <button
          @click="goBack"
          class="hidden lg:flex mb-4 items-center gap-2 text-slate-400 hover:text-white transition-colors group"
        >
          <ArrowLeft :size="18" class="group-hover:-translate-x-1 transition-transform" />
          <span class="text-xs font-bold uppercase tracking-widest">Back</span>
        </button>

        <!-- Profile Header -->
        <div class="p-4 lg:p-8 rounded-2xl lg:rounded-[2rem] glass border-slate-800 light:border-slate-200 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10 mb-6 lg:mb-8">
          <div class="flex flex-row items-start gap-3 lg:gap-8">
            <!-- Avatar -->
            <div class="relative flex-shrink-0">
              <div class="w-16 h-16 lg:w-32 lg:h-32 rounded-xl lg:rounded-3xl overflow-hidden ring-2 lg:ring-4 ring-indigo-500/20 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                <img
                  v-if="userProfile.avatar"
                  :src="userProfile.avatar"
                  :alt="userProfile.username"
                  class="w-full h-full object-cover"
                  @error="(e) => e.target.style.display = 'none'"
                />
                <span v-if="!userProfile.avatar" class="text-2xl lg:text-5xl font-black text-white">
                  {{ userProfile.first_name?.[0]?.toUpperCase() || '?' }}
                </span>
              </div>
              <div class="absolute -bottom-1 -right-1 lg:-bottom-2 lg:-right-2 w-5 h-5 lg:w-8 lg:h-8 rounded-full bg-emerald-500 border-2 lg:border-4 border-slate-950 light:border-white flex items-center justify-center">
                <div class="w-1 h-1 lg:w-2 lg:h-2 rounded-full bg-white" />
              </div>
            </div>

            <!-- Info -->
            <div class="flex-1 min-w-0">
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2 lg:gap-4 mb-3 lg:mb-4">
                <div class="min-w-0">
                  <h1 class="text-base lg:text-3xl font-black text-white light:text-slate-900 mb-0.5 lg:mb-2 truncate">
                    {{ userProfile.first_name }} {{ userProfile.last_name }}
                  </h1>
                  <div class="flex items-center gap-2 mb-0.5 lg:mb-1">
                    <p class="text-[10px] lg:text-sm text-slate-400 light:text-slate-500 font-medium">@{{ userProfile.username }}</p>
                    <span v-if="userReputation" :class="['inline-flex items-center gap-1 px-1.5 lg:px-2 py-0.5 rounded-full text-[9px] lg:text-xs font-bold border', userTier.bg, userTier.text, userTier.border]">
                      <Shield :size="10" />
                      {{ userTier.label }}
                    </span>
                    <span v-if="userReputation" class="text-[9px] lg:text-xs text-slate-500 font-medium">{{ userReputation.total_points }} pts</span>
                  </div>
                  <p class="text-[10px] lg:text-sm text-slate-300 light:text-slate-600 max-w-2xl line-clamp-2 lg:line-clamp-none">{{ userProfile.bio || 'No bio yet.' }}</p>
                </div>

                <!-- Follow Button - Desktop Only (mobile has it in header) -->
                <FollowButton
                  v-if="userId != authStore.user?.id"
                  :userId="userProfile.id"
                  :initialState="userProfile.is_following ? 'following' : 'not_following'"
                  :isFollower="userProfile.is_follower"
                  size="large"
                  class="hidden lg:flex"
                  @follow="handleFollow"
                  @unfollow="handleUnfollow"
                />
              </div>
            </div>
          </div>
              <!-- Stats Row - Horizontal Scrollable on Mobile -->
              <div class="flex gap-1.5 lg:gap-3 mt-4 overflow-x-auto pb-1 -mx-5 px-5 lg:mx-0 lg:px-0 lg:flex-wrap scrollbar-hide">
                <button
                  @click="switchTab('books')"
                  :class="[
                    'flex items-center gap-1 lg:gap-2 px-2 lg:px-4 py-1.5 lg:py-3 rounded-lg lg:rounded-2xl transition-all group flex-shrink-0',
                    activeTab === 'books'
                      ? 'bg-indigo-500 shadow-lg shadow-indigo-500/20'
                      : 'bg-white/5 light:bg-slate-100 hover:bg-white/10 light:hover:bg-slate-200'
                  ]"
                >
                  <BookOpen :size="14" class="lg:w-[18px] lg:h-[18px]" :class="activeTab === 'books' ? 'text-white' : 'text-indigo-400'" />
                  <span class="text-sm lg:text-xl font-black text-white light:text-slate-900">{{ userProfile.books_read_count || 0 }}</span>
                  <span :class="['text-[9px] lg:text-xs font-bold uppercase tracking-wide lg:tracking-widest', activeTab === 'books' ? 'text-white/80' : 'text-slate-400 light:text-slate-500 group-hover:text-indigo-400']">books</span>
                </button>
                <button
                  @click="switchTab('quotes')"
                  :class="[
                    'flex items-center gap-1 lg:gap-2 px-2 lg:px-4 py-1.5 lg:py-3 rounded-lg lg:rounded-2xl transition-all group flex-shrink-0',
                    activeTab === 'quotes'
                      ? 'bg-purple-500 shadow-lg shadow-purple-500/20'
                      : 'bg-white/5 light:bg-slate-100 hover:bg-white/10 light:hover:bg-slate-200'
                  ]"
                >
                  <Quote :size="14" class="lg:w-[18px] lg:h-[18px]" :class="activeTab === 'quotes' ? 'text-white' : 'text-purple-400'" />
                  <span class="text-sm lg:text-xl font-black text-white light:text-slate-900">{{ userProfile.quotes_count || 0 }}</span>
                  <span :class="['text-[9px] lg:text-xs font-bold uppercase tracking-wide lg:tracking-widest', activeTab === 'quotes' ? 'text-white/80' : 'text-slate-400 light:text-slate-500 group-hover:text-purple-400']">quotes</span>
                </button>
                <button
                  @click="switchTab('followers')"
                  :class="[
                    'flex items-center gap-1 lg:gap-2 px-2 lg:px-4 py-1.5 lg:py-3 rounded-lg lg:rounded-2xl transition-all group flex-shrink-0',
                    activeTab === 'followers'
                      ? 'bg-emerald-500 shadow-lg shadow-emerald-500/20'
                      : 'bg-white/5 light:bg-slate-100 hover:bg-white/10 light:hover:bg-slate-200'
                  ]"
                >
                  <Users :size="14" class="lg:w-[18px] lg:h-[18px]" :class="activeTab === 'followers' ? 'text-white' : 'text-emerald-400'" />
                  <span class="text-sm lg:text-xl font-black text-white light:text-slate-900">{{ userProfile.followers_count || 0 }}</span>
                  <span :class="['text-[9px] lg:text-xs font-bold uppercase tracking-wide lg:tracking-widest hidden sm:inline', activeTab === 'followers' ? 'text-white/80' : 'text-slate-400 light:text-slate-500 group-hover:text-emerald-400']">followers</span>
                </button>
                <button
                  @click="switchTab('following')"
                  :class="[
                    'flex items-center gap-1 lg:gap-2 px-2 lg:px-4 py-1.5 lg:py-3 rounded-lg lg:rounded-2xl transition-all group flex-shrink-0',
                    activeTab === 'following'
                      ? 'bg-amber-500 shadow-lg shadow-amber-500/20'
                      : 'bg-white/5 light:bg-slate-100 hover:bg-white/10 light:hover:bg-slate-200'
                  ]"
                >
                  <TrendingUp :size="14" class="lg:w-[18px] lg:h-[18px]" :class="activeTab === 'following' ? 'text-white' : 'text-amber-400'" />
                  <span class="text-sm lg:text-xl font-black text-white light:text-slate-900">{{ userProfile.following_count || 0 }}</span>
                  <span :class="['text-[9px] lg:text-xs font-bold uppercase tracking-wide lg:tracking-widest hidden sm:inline', activeTab === 'following' ? 'text-white/80' : 'text-slate-400 light:text-slate-500 group-hover:text-amber-400']">following</span>
                </button>
                <button
                  @click="switchTab('wishlist')"
                  :class="[
                    'flex items-center gap-1 lg:gap-2 px-2 lg:px-4 py-1.5 lg:py-3 rounded-lg lg:rounded-2xl transition-all group flex-shrink-0',
                    activeTab === 'wishlist'
                      ? 'bg-rose-500 shadow-lg shadow-rose-500/20'
                      : 'bg-white/5 light:bg-slate-100 hover:bg-white/10 light:hover:bg-slate-200'
                  ]"
                >
                  <Gift :size="14" class="lg:w-[18px] lg:h-[18px]" :class="activeTab === 'wishlist' ? 'text-white' : 'text-rose-400'" />
                  <span :class="['text-[9px] lg:text-xs font-bold uppercase tracking-wide lg:tracking-widest', activeTab === 'wishlist' ? 'text-white/80' : 'text-slate-400 light:text-slate-500 group-hover:text-rose-400']">wishlist</span>
                </button>
              </div>

              <!-- Badges Row -->
              <div v-if="userReputation?.badges?.length" class="flex flex-wrap gap-1.5 lg:gap-2 mt-3">
                <div v-for="ub in userReputation.badges.slice(0, 5)" :key="ub.id"
                  class="inline-flex items-center gap-1 px-2 py-1 rounded-full text-[9px] lg:text-xs font-bold border border-slate-700/50 bg-slate-800/50 light:bg-slate-100 light:border-slate-200"
                  :title="ub.badge.description">
                  <span :style="{ color: ub.badge.color }" class="text-[10px] lg:text-xs">{{ ub.badge.icon }}</span>
                  <span class="text-slate-300 light:text-slate-600">{{ ub.badge.name }}</span>
                </div>
              </div>
        </div>

        <!-- Layout Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8">
          <!-- Main Content -->
          <div class="lg:col-span-8 space-y-6 lg:space-y-8">
            <!-- BOOKS TAB -->
            <div v-if="activeTab === 'books'">
              <!-- Books Sub-Tab Navigation and View Toggle -->
              <div class="flex items-center justify-between gap-3 mb-4 lg:mb-6">
                <div class="flex items-center gap-2 overflow-x-auto pb-1 -mx-4 px-4 lg:mx-0 lg:px-0 scrollbar-hide flex-1">
                  <button
                    v-for="tab in [
                      { id: 'all', label: 'All', labelLg: 'All Books', icon: BookOpen },
                      { id: 'reading', label: 'Reading', labelLg: 'Reading', icon: BookOpen },
                      { id: 'finished', label: 'Read', labelLg: 'Finished', icon: BookOpen },
                      { id: 'want_to_read', label: 'TBR', labelLg: 'Want to Read', icon: Heart }
                    ]"
                    :key="tab.id"
                    @click="booksSubTab = tab.id"
                    :class="[
                      'flex items-center gap-1.5 lg:gap-2 px-3 lg:px-6 py-2 lg:py-3 rounded-xl lg:rounded-2xl font-black text-[10px] lg:text-xs uppercase tracking-wider lg:tracking-widest transition-all flex-shrink-0',
                      booksSubTab === tab.id
                        ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/20'
                        : 'bg-white/5 light:bg-slate-100 text-slate-400 light:text-slate-500 hover:bg-white/10 light:hover:bg-slate-200 hover:text-white light:hover:text-slate-900'
                    ]"
                  >
                    <component :is="tab.icon" :size="12" class="lg:w-3.5 lg:h-3.5" />
                    <span class="lg:hidden">{{ tab.label }}</span>
                    <span class="hidden lg:inline">{{ tab.labelLg }}</span>
                  </button>
                </div>

                <!-- View Toggle -->
                <div class="flex items-center gap-1 p-1 bg-slate-900/80 light:bg-slate-100 rounded-lg lg:rounded-xl border border-slate-800 light:border-slate-200 flex-shrink-0">
                  <button
                    @click="viewMode = 'grid'"
                    :class="[
                      'p-2 lg:p-2.5 rounded-md lg:rounded-lg transition-all',
                      viewMode === 'grid' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white light:hover:text-slate-900'
                    ]"
                    title="Grid View"
                  >
                    <LayoutGrid :size="16" class="lg:w-[18px] lg:h-[18px]" />
                  </button>
                  <button
                    @click="viewMode = 'list'"
                    :class="[
                      'p-2 lg:p-2.5 rounded-md lg:rounded-lg transition-all',
                      viewMode === 'list' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white light:hover:text-slate-900'
                    ]"
                    title="List View"
                  >
                    <List :size="16" class="lg:w-[18px] lg:h-[18px]" />
                  </button>
                </div>
              </div>

              <!-- Books Grid View -->
              <div v-if="viewMode === 'grid' && filteredBooks.length > 0" class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 gap-3 lg:gap-6">
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
              <div v-else-if="viewMode === 'list' && filteredBooks.length > 0" class="space-y-2 lg:space-y-3">
                <!-- Table Header - Desktop Only -->
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
                  v-for="userBook in filteredBooks"
                  :key="userBook.id"
                  :to="getBookUrl(userBook.book)"
                  class="group flex items-center gap-3 lg:gap-4 p-3 lg:p-4 rounded-xl lg:rounded-2xl glass border-slate-800 light:border-slate-200 hover:border-indigo-500/30 transition-all duration-300"
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
                    <BookOpen v-else :size="16" class="lg:w-5 lg:h-5 text-slate-600" />
                  </div>

                  <!-- Title & Author -->
                  <div class="flex-1 min-w-0">
                    <h3 class="font-bold text-white light:text-slate-900 text-xs lg:text-sm truncate group-hover:text-indigo-400 transition-colors">
                      {{ userBook.book?.title }}
                    </h3>
                    <p class="text-slate-400 light:text-slate-500 text-[10px] lg:text-xs truncate">
                      {{ userBook.book?.authors?.map(a => a.name).join(', ') || 'Unknown Author' }}
                    </p>
                    <!-- Mobile: Show rating inline -->
                    <div v-if="userBook.rating" class="lg:hidden flex items-center gap-1 mt-1">
                      <Star :size="10" class="text-amber-400 fill-current" />
                      <span class="text-[10px] font-bold text-amber-400">{{ userBook.rating }}</span>
                    </div>
                  </div>

                  <!-- Star Rating (10-point scale) - Desktop Only -->
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
                  <div class="flex items-center gap-1 lg:gap-2 lg:w-16 justify-end">
                    <button
                      v-if="userBook.is_favorite"
                      @click.stop
                      class="p-1.5 lg:p-2 rounded-lg"
                    >
                      <Heart :size="14" class="lg:w-4 lg:h-4 text-red-400 fill-current" />
                    </button>
                    <div class="hidden lg:block text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ArrowUpRight :size="18" />
                    </div>
                  </div>
                </router-link>
              </div>

              <!-- Load More Button -->
              <div v-if="hasMoreBooks && filteredBooks.length > 0" class="flex justify-center pt-6 lg:pt-8">
                <button
                  @click="loadMoreBooks"
                  :disabled="loadingMoreBooks"
                  class="px-5 lg:px-6 py-2.5 lg:py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs lg:text-sm font-bold hover:bg-indigo-500 hover:text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <span v-if="loadingMoreBooks">Loading...</span>
                  <span v-else>Load More Books</span>
                </button>
              </div>

              <!-- Empty State -->
              <div v-else-if="filteredBooks.length === 0" class="p-10 lg:p-16 rounded-2xl lg:rounded-3xl glass text-center opacity-40">
                <BookOpen :size="40" class="lg:w-12 lg:h-12 mx-auto mb-3 lg:mb-4 text-slate-600" />
                <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">No books in this category yet.</p>
              </div>
            </div>

            <!-- QUOTES TAB -->
            <div v-if="activeTab === 'quotes'">
              <!-- Loading State -->
              <div v-if="quotesLoading" class="flex items-center justify-center py-20 lg:py-32">
                <div class="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              </div>

              <!-- Quotes List -->
              <div v-else-if="userQuotes.length > 0" class="space-y-4 lg:space-y-6">
                <div
                  v-for="quote in userQuotes"
                  :key="quote.id"
                  class="group relative glass bg-slate-900/40 light:bg-white rounded-2xl lg:rounded-3xl p-5 lg:p-8 border border-slate-800/50 light:border-slate-200 hover:border-indigo-500/50 transition-all duration-500 hover:shadow-2xl hover:shadow-indigo-500/5"
                >
                  <!-- Quote Mark -->
                  <div class="absolute -top-3 -left-1 lg:-top-4 lg:-left-2 text-5xl lg:text-7xl text-indigo-500/10 font-serif pointer-events-none select-none">"</div>

                  <div class="relative space-y-4 lg:space-y-6">
                    <!-- Quote Content -->
                    <p class="text-sm lg:text-lg font-medium text-slate-100 light:text-slate-900 leading-relaxed italic font-serif">
                      {{ quote.text }}
                    </p>

                    <!-- Book Info and Actions -->
                    <div class="flex items-center justify-between gap-3 lg:gap-4 pt-3 border-t border-slate-800/50 light:border-slate-200">
                      <div class="flex-1 min-w-0 space-y-1">
                        <div class="flex flex-col lg:flex-row lg:items-center gap-0.5 lg:gap-2 min-w-0">
                          <h4
                            @click="quote.book ? router.push(getBookUrl({ id: quote.book, slug: quote.book_slug })) : null"
                            :class="quote.book ? 'cursor-pointer hover:text-indigo-400 transition-colors' : ''"
                            class="text-white light:text-slate-900 font-bold text-xs lg:text-sm truncate"
                          >
                            {{ quote.book_title || 'Unknown Book' }}
                          </h4>
                          <span class="text-slate-600 hidden lg:inline flex-shrink-0">·</span>
                          <p class="text-indigo-400 font-medium text-[11px] lg:text-sm truncate">{{ quote.book_author || 'Unknown Author' }}</p>
                        </div>
                        <div class="flex items-center gap-3 text-[10px] lg:text-xs text-slate-500 font-bold uppercase tracking-wider">
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
                          class="p-1.5 lg:p-2 rounded-full text-slate-500 hover:text-indigo-400 hover:bg-slate-800 light:hover:bg-slate-100 transition-all"
                        >
                          <Copy :size="16" class="lg:w-5 lg:h-5" />
                        </button>
                        <button
                          class="p-1.5 lg:p-2 rounded-full text-slate-500 hover:text-amber-400 hover:bg-slate-800 light:hover:bg-slate-100 transition-all"
                        >
                          <Bookmark :size="16" class="lg:w-5 lg:h-5" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty State -->
              <div v-else class="p-10 lg:p-16 rounded-2xl lg:rounded-3xl glass text-center opacity-40">
                <Quote :size="40" class="lg:w-12 lg:h-12 mx-auto mb-3 lg:mb-4 text-slate-600" />
                <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">No quotes yet.</p>
              </div>
            </div>

            <!-- FOLLOWERS TAB -->
            <div v-if="activeTab === 'followers'">
              <div v-if="followers.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3 lg:gap-6">
                <div
                  v-for="follower in followers"
                  :key="follower.id"
                  class="p-4 lg:p-6 rounded-2xl lg:rounded-3xl glass border-white/5 light:border-slate-200 hover:border-indigo-500/30 transition-all group cursor-pointer active:scale-[0.98]"
                  @click="router.push(`/users/${follower.id}`)"
                >
                  <div class="flex items-center lg:items-start gap-3 lg:gap-4">
                    <div class="w-12 h-12 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <img
                        v-if="follower.avatar"
                        :src="follower.avatar"
                        class="w-full h-full object-cover"
                        @error="(e) => e.target.style.display = 'none'"
                      />
                      <span v-if="!follower.avatar" class="text-lg lg:text-2xl font-black text-white">
                        {{ follower.first_name?.[0]?.toUpperCase() || '?' }}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm lg:text-lg font-black text-white light:text-slate-900 truncate group-hover:text-indigo-400 transition-colors">
                        {{ follower.first_name }} {{ follower.last_name }}
                      </h3>
                      <p class="text-[10px] lg:text-xs text-slate-400 light:text-slate-500 mb-1 lg:mb-2">@{{ follower.username }}</p>
                      <div class="flex gap-3 lg:gap-4 text-[10px] lg:text-xs text-slate-500">
                        <span>{{ follower.books_read_count }} books</span>
                        <span>{{ follower.followers_count }} followers</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="p-10 lg:p-16 rounded-2xl lg:rounded-3xl glass text-center opacity-40">
                <Users :size="40" class="lg:w-12 lg:h-12 mx-auto mb-3 lg:mb-4 text-slate-600" />
                <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">No followers yet.</p>
              </div>
            </div>

            <!-- FOLLOWING TAB -->
            <div v-if="activeTab === 'following'">
              <div v-if="following.length > 0" class="grid grid-cols-1 md:grid-cols-2 gap-3 lg:gap-6">
                <div
                  v-for="followedUser in following"
                  :key="followedUser.id"
                  class="p-4 lg:p-6 rounded-2xl lg:rounded-3xl glass border-white/5 light:border-slate-200 hover:border-indigo-500/30 transition-all group cursor-pointer active:scale-[0.98]"
                  @click="router.push(`/users/${followedUser.id}`)"
                >
                  <div class="flex items-center lg:items-start gap-3 lg:gap-4">
                    <div class="w-12 h-12 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center">
                      <img
                        v-if="followedUser.avatar"
                        :src="followedUser.avatar"
                        class="w-full h-full object-cover"
                        @error="(e) => e.target.style.display = 'none'"
                      />
                      <span v-if="!followedUser.avatar" class="text-lg lg:text-2xl font-black text-white">
                        {{ followedUser.first_name?.[0]?.toUpperCase() || '?' }}
                      </span>
                    </div>
                    <div class="flex-1 min-w-0">
                      <h3 class="text-sm lg:text-lg font-black text-white light:text-slate-900 truncate group-hover:text-indigo-400 transition-colors">
                        {{ followedUser.first_name }} {{ followedUser.last_name }}
                      </h3>
                      <p class="text-[10px] lg:text-xs text-slate-400 light:text-slate-500 mb-1 lg:mb-2">@{{ followedUser.username }}</p>
                      <div class="flex gap-3 lg:gap-4 text-[10px] lg:text-xs text-slate-500">
                        <span>{{ followedUser.books_read_count }} books</span>
                        <span>{{ followedUser.followers_count }} followers</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="p-10 lg:p-16 rounded-2xl lg:rounded-3xl glass text-center opacity-40">
                <TrendingUp :size="40" class="lg:w-12 lg:h-12 mx-auto mb-3 lg:mb-4 text-slate-600" />
                <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">Not following anyone yet.</p>
              </div>
            </div>

            <!-- WISHLIST TAB -->
            <div v-if="activeTab === 'wishlist'">
              <div class="flex items-center gap-2 mb-4 lg:mb-6">
                <Gift :size="18" class="text-rose-400" />
                <h2 class="text-sm lg:text-base font-black text-white light:text-slate-900 uppercase tracking-widest">
                  {{ isOwnProfile ? 'My Wishlist' : 'Their Wishlist' }}
                </h2>
                <p class="text-[10px] text-slate-500 font-bold ml-auto">
                  {{ userWishlist.length }} {{ userWishlist.length === 1 ? 'book' : 'books' }}
                </p>
              </div>
              <p v-if="!isOwnProfile" class="text-xs text-slate-500 mb-4 lg:mb-6">
                Books they'd love to own — perfect for gift ideas!
              </p>
              <div v-if="userWishlist.length > 0" class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3 sm:gap-4">
                <div
                  v-for="item in userWishlist"
                  :key="item.id"
                  @click="router.push(getBookUrl(item.book))"
                  class="group relative cursor-pointer"
                >
                  <div class="aspect-[2/3] rounded-lg overflow-hidden border-2 border-transparent group-hover:border-rose-500/30 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:shadow-black/40 transition-all duration-200">
                    <img
                      v-if="item.book?.cover_image"
                      :src="item.book.cover_image"
                      :alt="item.book?.title"
                      class="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div
                      v-else
                      class="w-full h-full bg-gradient-to-br from-rose-800 to-stone-900 flex items-center justify-center p-3"
                    >
                      <span class="text-[11px] font-bold text-white/80 text-center leading-tight line-clamp-4">
                        {{ item.book?.title || 'Unknown' }}
                      </span>
                    </div>
                    <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-2.5 pointer-events-none">
                      <p class="text-[11px] font-bold text-white leading-tight line-clamp-2">{{ item.book?.title }}</p>
                      <p class="text-[10px] text-white/70 line-clamp-1 mt-0.5">{{ item.book?.authors?.[0]?.name }}</p>
                    </div>
                  </div>
                  <div class="mt-1.5 sm:hidden">
                    <p class="text-[11px] font-semibold text-slate-200 line-clamp-2 leading-tight">{{ item.book?.title }}</p>
                  </div>
                </div>
              </div>
              <div v-else class="p-10 lg:p-16 rounded-2xl lg:rounded-3xl glass text-center opacity-40">
                <Gift :size="40" class="lg:w-12 lg:h-12 mx-auto mb-3 lg:mb-4 text-slate-600" />
                <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">
                  {{ isOwnProfile ? 'Your wishlist is empty. Browse books and add ones you\'d love to own!' : 'No items on their wishlist yet.' }}
                </p>
              </div>
            </div>
          </div>

          <!-- Sidebar - Shows below main content on mobile -->
          <div class="lg:col-span-4 space-y-4 lg:space-y-8">
            <!-- Reading DNA Widget -->
            <TasteProfile
              v-if="readingDna?.vote_count > 0"
              :profile="readingDna"
              :title="isOwnProfile ? 'Your Reading DNA' : 'Reading DNA'"
              compact
            />

            <!-- Match Score Widget -->
            <div v-if="userId != authStore.user?.id" class="p-5 lg:p-6 rounded-2xl lg:rounded-[2rem] glass border-slate-800 light:border-slate-200 bg-gradient-to-br from-emerald-500/5 via-transparent to-indigo-500/5">
              <div class="flex items-center gap-3 mb-4 lg:mb-6">
                <div class="w-9 h-9 lg:w-10 lg:h-10 rounded-xl lg:rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
                  <Sparkles :size="18" class="lg:w-5 lg:h-5 text-emerald-400" />
                </div>
                <div>
                  <h3 class="text-xs lg:text-sm font-black text-white light:text-slate-900 uppercase tracking-wider">Reading Compatibility</h3>
                  <p class="text-[9px] lg:text-[10px] text-slate-500 font-bold uppercase tracking-widest">Kindred Spirit Score</p>
                </div>
              </div>

              <!-- Match Score Circle -->
              <div class="flex items-center justify-center mb-4 lg:mb-6">
                <div class="relative w-24 h-24 lg:w-32 lg:h-32">
                  <!-- Mobile SVG -->
                  <svg class="w-24 h-24 transform -rotate-90 lg:hidden" viewBox="0 0 96 96">
                    <circle
                      cx="48"
                      cy="48"
                      r="42"
                      stroke="currentColor"
                      stroke-width="6"
                      fill="none"
                      class="text-white/5"
                    />
                    <circle
                      cx="48"
                      cy="48"
                      r="42"
                      stroke="currentColor"
                      stroke-width="6"
                      fill="none"
                      :stroke-dasharray="`${matchScore * 2.64} 263.89`"
                      class="text-emerald-500 transition-all duration-1000"
                    />
                  </svg>
                  <!-- Desktop SVG -->
                  <svg class="w-32 h-32 transform -rotate-90 hidden lg:block" viewBox="0 0 128 128">
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
                    <span class="text-2xl lg:text-4xl font-black text-white light:text-slate-900">{{ matchScore }}%</span>
                  </div>
                </div>
              </div>

              <!-- Match Details -->
              <div class="grid grid-cols-2 lg:grid-cols-1 gap-2 lg:gap-3">
                <div class="flex items-center justify-between p-2.5 lg:p-3 rounded-lg lg:rounded-xl bg-white/[0.02] light:bg-slate-100 border border-white/5 light:border-slate-200">
                  <span class="text-[10px] lg:text-xs text-slate-400 light:text-slate-500 font-bold uppercase tracking-wider">Shared Books</span>
                  <span class="text-base lg:text-lg font-black text-white light:text-slate-900">{{ sharedBooks.length }}</span>
                </div>
                <div class="flex items-center justify-between p-2.5 lg:p-3 rounded-lg lg:rounded-xl bg-white/[0.02] light:bg-slate-100 border border-white/5 light:border-slate-200">
                  <span class="text-[10px] lg:text-xs text-slate-400 light:text-slate-500 font-bold uppercase tracking-wider">Similar Genres</span>
                  <span class="text-base lg:text-lg font-black text-white light:text-slate-900">{{ userProfile.top_genres?.length || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- Shared Books Widget -->
            <div v-if="!isOwnProfile && sharedBooks.length > 0" class="p-5 lg:p-6 rounded-2xl lg:rounded-[2rem] glass border-slate-800 light:border-slate-200">
              <h3 class="text-xs lg:text-sm font-black text-white light:text-slate-900 uppercase tracking-wider mb-4 lg:mb-6">
                Books in Common
                <span class="text-slate-500 font-bold ml-1">({{ sharedBooks.length }})</span>
              </h3>
              <div class="grid grid-cols-2 lg:grid-cols-1 gap-2 lg:gap-4 max-h-[480px] overflow-y-auto shared-books-scroll pr-1">
                <div
                  v-for="userBook in sharedBooks"
                  :key="userBook.id"
                  class="flex items-center gap-2.5 lg:gap-3 p-2.5 lg:p-3 rounded-xl lg:rounded-2xl bg-white/[0.02] light:bg-slate-100 border border-white/5 light:border-slate-200 hover:bg-white/[0.04] light:hover:bg-slate-200 transition-all cursor-pointer group"
                >
                  <div class="w-8 h-11 lg:w-10 lg:h-14 rounded-md lg:rounded-lg overflow-hidden flex-shrink-0 bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                    <img
                      v-if="userBook.book.cover_image"
                      :src="userBook.book.cover_image"
                      :alt="userBook.book.title"
                      class="w-full h-full object-cover"
                      @error="(e) => e.target.style.display = 'none'"
                    />
                    <BookOpen v-if="!userBook.book.cover_image" :size="14" class="lg:w-4 lg:h-4 text-slate-600" />
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-[11px] lg:text-xs font-bold text-white light:text-slate-900 truncate group-hover:text-indigo-400 transition-colors">
                      {{ userBook.book.title }}
                    </p>
                    <p class="text-[8px] lg:text-[9px] text-slate-500 font-black uppercase tracking-widest truncate">
                      {{ userBook.book.authors?.[0]?.name || 'Unknown' }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Top Genres Widget -->
            <div v-if="userProfile.top_genres?.length" class="p-5 lg:p-6 rounded-2xl lg:rounded-[2rem] glass border-slate-800 light:border-slate-200">
              <h3 class="text-xs lg:text-sm font-black text-white light:text-slate-900 uppercase tracking-wider mb-4 lg:mb-6">Favorite Genres</h3>
              <div class="flex flex-wrap gap-1.5 lg:gap-2">
                <span
                  v-for="genre in userProfile.top_genres"
                  :key="genre"
                  class="px-2.5 lg:px-3 py-1.5 lg:py-2 rounded-lg lg:rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[10px] lg:text-xs font-black text-indigo-400 uppercase tracking-wider"
                >
                  {{ genre }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else class="flex flex-col items-center justify-center py-20 lg:py-32 opacity-40">
        <Users :size="48" class="lg:w-16 lg:h-16 text-slate-700 mb-3 lg:mb-4" />
        <p class="text-slate-400 light:text-slate-500 font-medium text-sm lg:text-base">User not found</p>
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

/* Hide scrollbar for horizontal scroll areas */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Thin scrollbar for shared books */
.shared-books-scroll::-webkit-scrollbar {
  width: 4px;
}
.shared-books-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.shared-books-scroll::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 2px;
}
.shared-books-scroll::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}
.shared-books-scroll {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.2) transparent;
}

/* Safe area for notched devices */
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}

/* Touch feedback optimization */
* {
  -webkit-tap-highlight-color: transparent;
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
