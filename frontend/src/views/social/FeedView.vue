<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Badge } from '@/components/ui/badge'
import api from '@/services/api'
import {
  Heart,
  MessageCircle,
  Share2,
  BookOpen,
  Quote,
  Star,
  Target,
  List,
  Users,
  TrendingUp,
  Sparkles,
  RefreshCw,
  Filter,
  ChevronDown,
  X
} from 'lucide-vue-next'
import { getBookUrl } from '@/utils/bookUrl'

const router = useRouter()

const activities = ref([])
const loading = ref(true)
const refreshing = ref(false)
const error = ref(null)
const userBooks = ref([])

// Filter state
const activeFilter = ref('all')
const showFilterMenu = ref(false)

const filterOptions = [
  { value: 'all', label: 'All Activity', icon: Sparkles },
  { value: 'book_finished', label: 'Finished Books', icon: Star },
  { value: 'book_started', label: 'Started Reading', icon: BookOpen },
  { value: 'quote_added', label: 'Quotes', icon: Quote },
  { value: 'progress_update', label: 'Progress Updates', icon: TrendingUp },
]

onMounted(async () => {
  await loadFeed()
  await loadUserBooks()
})

const loadUserBooks = async () => {
  try {
    const response = await api.get('/reading/user-books/')
    userBooks.value = response.data?.results || response.data || []
  } catch (err) {
    console.error('Failed to load user books:', err)
  }
}

const loadFeed = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await api.get('/social/feed/')
    const feedData = response.data?.results || response.data || []

    activities.value = feedData.map(item => ({
      id: item.id,
      type: item.feed_type,
      user: {
        id: item.actor.id,
        full_name: `${item.actor.first_name} ${item.actor.last_name}`,
        avatar: item.actor.avatar,
      },
      book: item.book_data || null,
      quote: item.feed_type === 'quote_added' ? {
        text: item.preview_text,
        page_number: null,
      } : null,
      rating: null,
      review: item.review_data || null,
      timestamp: item.created_at,
      likes_count: item.likes_count || 0,
      comments_count: item.comments_count || 0,
      is_liked: item.is_liked || false,
      preview_text: item.preview_text,
      preview_image: item.preview_image,
    }))

    loading.value = false
  } catch (err) {
    console.error('Feed error:', err)
    error.value = 'Failed to load activity feed'
    loading.value = false
  }
}

const handleRefresh = async () => {
  refreshing.value = true
  await loadFeed()
  refreshing.value = false
}

const filteredActivities = computed(() => {
  if (activeFilter.value === 'all') return activities.value
  return activities.value.filter(a => a.type === activeFilter.value)
})

const getActivityIcon = (type) => {
  const icons = {
    book_finished: Star,
    quote_added: Quote,
    challenge_completed: Target,
    list_created: List,
    reading_session: BookOpen,
    progress_update: TrendingUp,
    book_started: BookOpen,
    want_to_read: Heart,
    joined_circle: Users,
  }
  return icons[type] || Sparkles
}

const getActivityColor = (type) => {
  const colors = {
    book_finished: 'text-yellow-500',
    quote_added: 'text-purple-500',
    challenge_completed: 'text-green-500',
    list_created: 'text-blue-500',
    reading_session: 'text-orange-500',
    progress_update: 'text-amber-500',
    book_started: 'text-indigo-500',
    want_to_read: 'text-rose-500',
    joined_circle: 'text-pink-500',
  }
  return colors[type] || 'text-primary'
}

const getActivityBgColor = (type) => {
  const colors = {
    book_finished: 'bg-yellow-500/10',
    quote_added: 'bg-purple-500/10',
    challenge_completed: 'bg-green-500/10',
    list_created: 'bg-blue-500/10',
    reading_session: 'bg-orange-500/10',
    progress_update: 'bg-amber-500/10',
    book_started: 'bg-indigo-500/10',
    want_to_read: 'bg-rose-500/10',
    joined_circle: 'bg-pink-500/10',
  }
  return colors[type] || 'bg-primary/10'
}

const getActivityTitle = (activity) => {
  const titles = {
    book_finished: 'finished reading',
    quote_added: 'saved a quote from',
    challenge_completed: 'completed a challenge',
    list_created: 'created a new list',
    reading_session: 'just read',
    progress_update: 'made progress on',
    book_started: 'started reading',
    want_to_read: 'wants to read',
    joined_circle: 'joined a circle',
  }
  return titles[activity.type] || 'posted'
}

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`

  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const handleLike = async (activity) => {
  // Optimistic update
  activity.is_liked = !activity.is_liked
  activity.likes_count += activity.is_liked ? 1 : -1
  try {
    const response = await api.post(`/social/feed/${activity.id}/toggle_like/`)
    activity.is_liked = response.data.liked
    activity.likes_count = response.data.likes_count
  } catch (err) {
    // Revert on error
    activity.is_liked = !activity.is_liked
    activity.likes_count += activity.is_liked ? 1 : -1
    console.error('Failed to toggle like:', err)
  }
}

const goToBook = (book) => {
  if (typeof book === 'object' && book) {
    router.push(getBookUrl(book))
  } else {
    router.push(`/books/${book}`)
  }
}

const goToProfile = (userId) => {
  router.push(`/users/${userId}`)
}

const initials = (name) => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

const getUserBookStatus = (bookId) => {
  if (!bookId) return null
  const userBook = userBooks.value.find(ub => ub.book?.id === bookId)
  return userBook?.status || null
}

const getStatusLabel = (status) => {
  const labels = {
    'currently_reading': 'Reading',
    'read': 'Finished',
    'want_to_read': 'Want to Read',
    'abandoned': 'Abandoned'
  }
  return labels[status] || status
}

const addToLibrary = async (bookId, status) => {
  if (!bookId) return

  try {
    const response = await api.post('/reading/user-books/', {
      book: bookId,
      status: status
    })

    if (response.data) {
      userBooks.value.push(response.data)
    }
  } catch (err) {
    console.error('Failed to add book to library:', err)
  }
}

const selectFilter = (value) => {
  activeFilter.value = value
  showFilterMenu.value = false
}
</script>

<template>
  <div class="h-full flex flex-col bg-slate-950 animate-in fade-in duration-500">

    <!-- ==================== MOBILE HEADER ==================== -->
    <header class="lg:hidden px-4 py-3 border-b border-white/5 bg-slate-900/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <TrendingUp :size="20" class="text-white" />
          </div>
          <div>
            <h1 class="text-lg font-black text-white">Activity</h1>
            <p class="text-[10px] text-slate-500 uppercase tracking-wider">{{ filteredActivities.length }} updates</p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <!-- Refresh Button -->
          <button
            @click="handleRefresh"
            :disabled="refreshing"
            class="p-2.5 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw :size="18" :class="refreshing ? 'animate-spin' : ''" />
          </button>

          <!-- Filter Button -->
          <button
            @click="showFilterMenu = !showFilterMenu"
            :class="[
              'p-2.5 rounded-xl transition-colors',
              activeFilter !== 'all' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/5 text-slate-400'
            ]"
          >
            <Filter :size="18" />
          </button>
        </div>
      </div>

      <!-- Filter Dropdown -->
      <div
        v-if="showFilterMenu"
        class="fixed inset-0 z-40"
        @click="showFilterMenu = false"
      />
      <div
        v-if="showFilterMenu"
        class="absolute right-4 top-full mt-2 w-56 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-50"
      >
        <div class="p-2 space-y-1">
          <button
            v-for="option in filterOptions"
            :key="option.value"
            @click="selectFilter(option.value)"
            :class="[
              'w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left',
              activeFilter === option.value ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-400 hover:bg-white/5'
            ]"
          >
            <component :is="option.icon" :size="16" />
            <span class="text-sm font-medium">{{ option.label }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- ==================== DESKTOP HEADER ==================== -->
    <header class="hidden lg:block border-b border-white/5 bg-slate-900/50">
      <div class="container mx-auto px-8 py-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <TrendingUp :size="24" class="text-white" />
            </div>
            <div>
              <h1 class="text-2xl font-black text-white">Activity Feed</h1>
              <p class="text-sm text-slate-500">See what your friends are reading</p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <!-- Filter Tabs -->
            <div class="flex items-center gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
              <button
                v-for="option in filterOptions"
                :key="option.value"
                @click="activeFilter = option.value"
                :class="[
                  'px-4 py-2 rounded-lg text-xs font-bold transition-all flex items-center gap-2',
                  activeFilter === option.value
                    ? 'bg-indigo-500 text-white shadow-lg'
                    : 'text-slate-400 hover:text-white'
                ]"
              >
                <component :is="option.icon" :size="14" />
                {{ option.label }}
              </button>
            </div>

            <button
              @click="handleRefresh"
              :disabled="refreshing"
              class="p-3 rounded-xl bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-colors disabled:opacity-50"
            >
              <RefreshCw :size="18" :class="refreshing ? 'animate-spin' : ''" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- ==================== CONTENT ==================== -->
    <div class="flex-1 overflow-y-auto custom-scrollbar">

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="flex flex-col items-center gap-4">
          <div class="w-10 h-10 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          <p class="text-sm text-slate-500">Loading activity...</p>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="flex flex-col items-center justify-center py-20 px-4 text-center">
        <div class="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mb-4">
          <TrendingUp :size="28" class="text-rose-400" />
        </div>
        <p class="text-lg font-bold text-white mb-2">Something went wrong</p>
        <p class="text-sm text-slate-500 mb-4">{{ error }}</p>
        <button
          @click="loadFeed"
          class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold text-sm"
        >
          Try Again
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredActivities.length === 0" class="flex flex-col items-center justify-center py-20 px-4 text-center">
        <div class="w-20 h-20 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mb-6">
          <Sparkles :size="36" class="text-slate-600" />
        </div>
        <h3 class="text-xl font-black text-white mb-2">No activity yet</h3>
        <p class="text-sm text-slate-500 max-w-xs">
          {{ activeFilter === 'all' ? 'Start following users to see their reading activity here!' : 'No activity of this type yet.' }}
        </p>
        <button
          v-if="activeFilter !== 'all'"
          @click="activeFilter = 'all'"
          class="mt-4 px-5 py-2.5 rounded-xl bg-white/5 text-slate-400 font-bold text-sm hover:bg-white/10 transition-colors"
        >
          Show All Activity
        </button>
      </div>

      <!-- Activity List -->
      <div v-else class="container mx-auto max-w-2xl px-4 lg:px-8 py-4 lg:py-8 space-y-4">
        <div
          v-for="activity in filteredActivities"
          :key="activity.id"
          class="bg-white/[0.03] border border-white/5 rounded-2xl lg:rounded-3xl overflow-hidden hover:bg-white/[0.05] transition-colors"
        >
          <!-- Activity Header -->
          <div class="p-4 lg:p-5">
            <div class="flex items-start gap-3">
              <!-- User Avatar -->
              <button
                @click="goToProfile(activity.user.id)"
                class="shrink-0 active:scale-95 transition-transform"
              >
                <div class="w-11 h-11 lg:w-12 lg:h-12 rounded-xl bg-indigo-500/20 border border-indigo-500/20 flex items-center justify-center overflow-hidden">
                  <img v-if="activity.user.avatar" :src="activity.user.avatar" class="w-full h-full object-cover" />
                  <span v-else class="text-indigo-400 font-bold text-sm">{{ initials(activity.user.full_name) }}</span>
                </div>
              </button>

              <!-- Activity Info -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center flex-wrap gap-x-2 gap-y-1">
                  <button
                    @click="goToProfile(activity.user.id)"
                    class="text-sm font-bold text-white hover:text-indigo-400 transition-colors"
                  >
                    {{ activity.user.full_name }}
                  </button>
                  <span class="text-sm text-slate-500">{{ getActivityTitle(activity) }}</span>
                </div>
                <div class="flex items-center gap-2 mt-1">
                  <div :class="['w-5 h-5 rounded-md flex items-center justify-center', getActivityBgColor(activity.type)]">
                    <component :is="getActivityIcon(activity.type)" :size="12" :class="getActivityColor(activity.type)" />
                  </div>
                  <span class="text-xs text-slate-600">{{ formatTimestamp(activity.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Activity Content -->
          <div class="px-4 lg:px-5 pb-4 lg:pb-5">
            <!-- Book Finished Activity -->
            <div v-if="activity.type === 'book_finished'" class="space-y-3">
              <button
                v-if="activity.book"
                @click="goToBook(activity.book)"
                class="w-full flex gap-4 p-3 rounded-xl bg-white/5 border border-white/5 active:scale-[0.99] transition-all text-left"
              >
                <div v-if="activity.preview_image" class="w-14 h-20 lg:w-16 lg:h-24 rounded-lg overflow-hidden shrink-0 shadow-lg">
                  <img :src="activity.preview_image" :alt="activity.book?.title" class="w-full h-full object-cover" />
                </div>
                <div class="flex-1 min-w-0">
                  <h3 class="font-bold text-white text-sm lg:text-base line-clamp-2">{{ activity.book.title }}</h3>
                  <p v-if="activity.book?.authors?.length" class="text-xs text-slate-500 mt-1">
                    {{ activity.book.authors.map(a => a.name).join(', ') }}
                  </p>
                  <div v-if="activity.rating" class="flex gap-0.5 mt-2">
                    <Star
                      v-for="i in 5"
                      :key="i"
                      :size="14"
                      :class="i <= activity.rating ? 'fill-yellow-400 text-yellow-400' : 'text-slate-700'"
                    />
                  </div>
                </div>
              </button>
              <p v-if="activity.review" class="text-sm text-slate-400 leading-relaxed">
                {{ activity.review }}
              </p>
            </div>

            <!-- Quote Activity -->
            <div v-if="activity.type === 'quote_added'" class="space-y-3">
              <div class="relative pl-4 border-l-2 border-purple-500/50">
                <Quote :size="14" class="absolute -left-[9px] top-0 text-purple-500 bg-slate-950" />
                <blockquote class="text-sm lg:text-base text-slate-300 italic leading-relaxed font-serif">
                  "{{ activity.quote?.text || activity.preview_text }}"
                </blockquote>
              </div>
              <button
                v-if="activity.book"
                @click="goToBook(activity.book)"
                class="text-xs text-purple-400 hover:text-purple-300 font-medium transition-colors"
              >
                — {{ activity.book.title }}
              </button>
            </div>

            <!-- Challenge Completed -->
            <div v-if="activity.type === 'challenge_completed'" class="space-y-2">
              <div class="p-4 rounded-xl bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/20">
                <div class="flex items-center gap-3 mb-2">
                  <div class="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
                    <Target :size="20" class="text-green-400" />
                  </div>
                  <div>
                    <h3 v-if="activity.challenge" class="font-bold text-white">{{ activity.challenge.title }}</h3>
                    <p class="text-xs text-green-400">Challenge Completed!</p>
                  </div>
                </div>
                <p v-if="activity.challenge" class="text-2xl font-black text-green-400">
                  {{ activity.challenge.completed_books }} / {{ activity.challenge.target_books }} books
                </p>
              </div>
            </div>

            <!-- Progress Update / Reading Session -->
            <div v-if="activity.type === 'reading_session' || activity.type === 'progress_update'" class="space-y-2">
              <div v-if="activity.preview_text" class="text-sm text-slate-400">
                {{ activity.preview_text }}
              </div>
              <button
                v-if="activity.book"
                @click="goToBook(activity.book)"
                class="text-sm text-indigo-400 hover:text-indigo-300 font-medium transition-colors"
              >
                {{ activity.book.title }}
              </button>
            </div>

            <!-- Book Started / Want to Read -->
            <div v-if="activity.type === 'book_started' || activity.type === 'want_to_read'">
              <button
                v-if="activity.book"
                @click="goToBook(activity.book)"
                class="w-full flex gap-4 p-3 rounded-xl bg-white/5 border border-white/5 active:scale-[0.99] transition-all text-left"
              >
                <div v-if="activity.preview_image" class="w-14 h-20 lg:w-16 lg:h-24 rounded-lg overflow-hidden shrink-0 shadow-lg">
                  <img :src="activity.preview_image" :alt="activity.book?.title" class="w-full h-full object-cover" />
                </div>
                <div class="flex-1 min-w-0 flex flex-col justify-between">
                  <div>
                    <h3 class="font-bold text-white text-sm lg:text-base line-clamp-2">{{ activity.book.title }}</h3>
                    <p v-if="activity.book?.authors?.length" class="text-xs text-slate-500 mt-1">
                      {{ activity.book.authors.map(a => a.name).join(', ') }}
                    </p>
                  </div>
                  <!-- Status Badge or Add Button -->
                  <div class="mt-2">
                    <Badge
                      v-if="getUserBookStatus(activity.book?.id)"
                      variant="secondary"
                      class="text-[10px]"
                    >
                      {{ getStatusLabel(getUserBookStatus(activity.book?.id)) }}
                    </Badge>
                    <button
                      v-else
                      @click.stop="addToLibrary(activity.book?.id, 'want_to_read')"
                      class="px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold hover:bg-indigo-500 hover:text-white transition-all"
                    >
                      + Want to Read
                    </button>
                  </div>
                </div>
              </button>
            </div>

            <!-- Generic preview text -->
            <div v-if="!['book_finished', 'quote_added', 'challenge_completed', 'reading_session', 'progress_update', 'book_started', 'want_to_read'].includes(activity.type) && activity.preview_text">
              <p class="text-sm text-slate-400">{{ activity.preview_text }}</p>
            </div>
          </div>

          <!-- Interaction Bar -->
          <div class="px-4 lg:px-5 py-3 border-t border-white/5 flex items-center gap-6">
            <button
              @click="handleLike(activity)"
              :class="[
                'flex items-center gap-2 text-sm transition-colors active:scale-95',
                activity.is_liked ? 'text-rose-400' : 'text-slate-500 hover:text-rose-400'
              ]"
            >
              <Heart :size="18" :class="activity.is_liked ? 'fill-current' : ''" />
              <span class="font-medium">{{ activity.likes_count || '' }}</span>
            </button>

            <button class="flex items-center gap-2 text-sm text-slate-500 hover:text-indigo-400 transition-colors">
              <MessageCircle :size="18" />
              <span class="font-medium">{{ activity.comments_count || '' }}</span>
            </button>

            <button class="flex items-center gap-2 text-sm text-slate-500 hover:text-emerald-400 transition-colors ml-auto">
              <Share2 :size="18" />
            </button>
          </div>
        </div>
      </div>

      <!-- Bottom Padding for Safe Area -->
      <div class="h-4 lg:h-8" />
    </div>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}

/* Safe area support for notched phones */
.safe-area-top {
  padding-top: max(0.75rem, env(safe-area-inset-top));
}

.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

/* Mobile touch feedback */
@media (max-width: 1023px) {
  button {
    -webkit-tap-highlight-color: transparent;
  }
}

/* Font for quotes */
.font-serif {
  font-family: 'Georgia', serif;
}
</style>
