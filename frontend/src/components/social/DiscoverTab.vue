<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { socialService } from '@/services/socialService'
import FollowButton from './FollowButton.vue'
import { Sparkles, Users, BookOpen, TrendingUp, Search } from 'lucide-vue-next'

const router = useRouter()

const kindredSpirits = ref([])
const searchResults = ref([])
const searchQuery = ref('')
const loading = ref(true)
const searching = ref(false)
const activeView = ref('suggested') // 'suggested' | 'search'

onMounted(async () => {
  await loadKindredSpirits()
})

const loadKindredSpirits = async () => {
  loading.value = true
  try {
    const spirits = await socialService.getKindredSpirits(6)
    kindredSpirits.value = spirits
  } catch (error) {
    console.error('Error loading kindred spirits:', error)
  } finally {
    loading.value = false
  }
}

// Watch search query and trigger search
let searchTimeout = null
watch(searchQuery, (newQuery) => {
  if (searchTimeout) clearTimeout(searchTimeout)

  if (!newQuery || newQuery.trim().length < 2) {
    activeView.value = 'suggested'
    searchResults.value = []
    return
  }

  searchTimeout = setTimeout(async () => {
    await handleSearch(newQuery)
  }, 500)
})

const handleSearch = async (query) => {
  searching.value = true
  activeView.value = 'search'
  try {
    const results = await socialService.searchUsers(query)
    searchResults.value = results
  } catch (error) {
    console.error('Error searching users:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

const displayedUsers = computed(() => {
  return activeView.value === 'search' ? searchResults.value : kindredSpirits.value
})

const handleFollow = async (userId) => {
  try {
    await socialService.followUser(userId)
    const user = kindredSpirits.value.find(u => u.id === userId)
    if (user) {
      user.is_following = true
    }
  } catch (error) {
    console.error('Error following user:', error)
  }
}

const handleUnfollow = async (userId) => {
  try {
    await socialService.unfollowUser(userId)
    const user = kindredSpirits.value.find(u => u.id === userId)
    if (user) {
      user.is_following = false
    }
  } catch (error) {
    console.error('Error unfollowing user:', error)
  }
}

const goToUserProfile = (userId) => {
  router.push(`/users/${userId}`)
}
</script>

<template>
  <div class="max-w-5xl mx-auto space-y-12 py-8">

    <!-- Header -->
    <div class="text-center space-y-4">
      <div class="flex items-center justify-center gap-3">
        <div class="w-12 h-12 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Sparkles :size="24" class="text-indigo-400" />
        </div>
      </div>
      <h1 class="text-4xl font-black text-white tracking-tighter">Discover <span class="text-indigo-500">Kindred Spirits</span></h1>
      <p class="text-slate-400 font-medium max-w-md mx-auto">
        Connect with readers who share your literary taste and intellectual curiosity
      </p>

      <!-- Search Bar -->
      <div class="max-w-md mx-auto mt-6 relative group">
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-500 transition-colors" :size="18" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search readers by name or username..."
          class="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-4 py-3 text-sm text-white outline-none focus:border-indigo-500 transition-all"
        />
        <div v-if="searching" class="absolute right-4 top-1/2 -translate-y-1/2">
          <div class="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="i in 6" :key="i" class="h-64 rounded-3xl bg-white/5 animate-pulse" />
    </div>

    <!-- User Results -->
    <div v-else>
      <div class="flex items-center gap-3 mb-8">
        <Users :size="20" class="text-indigo-400" />
        <h2 class="text-xl font-black text-white uppercase tracking-wider">
          {{ activeView === 'search' ? `Search Results (${displayedUsers.length})` : 'Readers Like You' }}
        </h2>
        <div class="flex-1 h-px bg-slate-800" />
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div
          v-for="user in displayedUsers"
          :key="user.id"
          class="group p-8 rounded-3xl glass border-white/5 hover:border-indigo-500/30 bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5 transition-all duration-500"
        >
          <!-- User Header -->
          <div class="flex items-start gap-4 mb-6">
            <div
              @click="goToUserProfile(user.id)"
              class="w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all cursor-pointer flex-shrink-0 bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center"
            >
              <img
                v-if="user.avatar"
                :src="user.avatar"
                class="w-full h-full object-cover"
                @error="(e) => e.target.style.display = 'none'"
              />
              <span v-if="!user.avatar" class="text-2xl font-black text-white">
                {{ user.first_name?.[0]?.toUpperCase() || '?' }}
              </span>
            </div>
            <div class="flex-1 min-w-0">
              <h3
                @click="goToUserProfile(user.id)"
                class="text-lg font-black text-white truncate cursor-pointer hover:text-indigo-400 transition-colors"
              >
                {{ user.first_name }} {{ user.last_name }}
              </h3>
              <p class="text-xs text-slate-500 font-bold">@{{ user.username }}</p>
              <div class="flex items-center gap-3 mt-2">
                <div class="flex items-center gap-1.5">
                  <BookOpen :size="12" class="text-indigo-400" />
                  <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    {{ user.books_read_count }} books
                  </span>
                </div>
                <div class="flex items-center gap-1.5">
                  <Users :size="12" class="text-purple-400" />
                  <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                    {{ user.followers_count }} followers
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Bio -->
          <p v-if="user.bio" class="text-sm text-slate-400 mb-6 line-clamp-2">
            {{ user.bio }}
          </p>

          <!-- Match Score -->
          <div class="mb-6 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Compatibility</span>
              <span class="text-2xl font-black text-indigo-400">{{ user.match_score }}%</span>
            </div>
            <div class="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000"
                :style="{ width: `${user.match_score}%` }"
              />
            </div>
            <div class="mt-3 flex items-center gap-2 text-[10px] text-slate-500 font-bold">
              <span>📚 {{ user.shared_books_count }} books in common</span>
            </div>
          </div>

          <!-- Top Genres -->
          <div class="mb-6">
            <span class="text-[9px] font-black text-slate-600 uppercase tracking-widest block mb-3">Top Interests</span>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="genre in user.top_genres"
                :key="genre"
                class="px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-black text-indigo-400 uppercase tracking-wider"
              >
                {{ genre }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-3">
            <FollowButton
              :userId="user.id"
              :initialState="user.is_following ? 'following' : 'not_following'"
              size="default"
              @follow="handleFollow"
              @unfollow="handleUnfollow"
              class="flex-1"
            />
            <button
              @click="goToUserProfile(user.id)"
              class="px-6 py-2.5 rounded-xl bg-white/5 border border-white/10 text-white font-bold text-xs uppercase tracking-widest hover:bg-white/10 transition-all"
            >
              View Profile
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!loading && displayedUsers.length === 0" class="text-center py-20">
      <div class="w-20 h-20 rounded-full bg-white/5 border border-white/10 flex items-center justify-center mx-auto mb-6">
        <Users :size="40" class="text-slate-700" />
      </div>
      <h3 class="text-2xl font-black text-white mb-2 uppercase tracking-wider">
        {{ activeView === 'search' ? 'No Users Found' : 'No Suggestions Yet' }}
      </h3>
      <p class="text-slate-500 font-medium max-w-sm mx-auto">
        {{ activeView === 'search' ? 'Try a different search term' : 'Add more books to your library to get personalized reader recommendations' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
/* Light mode adjustments */
body.light .text-white {
  color: #0f172a !important;
}

body.light .text-slate-400,
body.light .text-slate-500 {
  color: #64748b !important;
}

body.light .bg-white\/5 {
  background-color: rgba(0, 0, 0, 0.03) !important;
}

body.light .border-white\/5,
body.light .border-white\/10 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}
</style>
