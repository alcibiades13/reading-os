<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { socialService } from '@/services/socialService'
import { socialAPI } from '@/services/api'
import { getMediaUrl } from '@/utils/mediaUrl'
import PageHeader from '@/components/ui/PageHeader.vue'
import {
  Users, Search, UserPlus, UserCheck, UserX, MessageCircle,
  Sparkles, Clock, Library, Network, Loader2, BookMarked
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref(null)
const friends = ref([])
const pendingRequests = ref([])
const suggestedUsers = ref([])
const searchQuery = ref('')
const activeTab = ref('friends') // 'friends' | 'pending' | 'discover'

// ── Data Loading ─────────────────────────────────────
onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  loading.value = true
  error.value = null
  try {
    const [friendsRes, pendingRes, suggestedRes] = await Promise.allSettled([
      socialAPI.myFriends(),
      socialAPI.pendingRequests(),
      socialService.getSuggestedUsers(10),
    ])

    if (friendsRes.status === 'fulfilled') {
      friends.value = normalizeFriendships(friendsRes.value.data || [])
    }
    if (pendingRes.status === 'fulfilled') {
      pendingRequests.value = pendingRes.value.data || []
    }
    if (suggestedRes.status === 'fulfilled') {
      suggestedUsers.value = suggestedRes.value || []
    }

    // If all requests failed, show error
    if (friendsRes.status === 'rejected' && pendingRes.status === 'rejected' && suggestedRes.status === 'rejected') {
      error.value = 'Failed to load friends data. Please try again.'
    }
  } catch (e) {
    error.value = 'Failed to load friends data. Please try again.'
  } finally {
    loading.value = false
  }
}

// Normalize friendship objects to get the "other" user — deduplicate by user ID
const normalizeFriendships = (friendships) => {
  const currentUserId = authStore.user?.id
  const seen = new Set()
  const result = []
  for (const f of friendships) {
    const friend = f.from_user?.id === currentUserId ? f.to_user : f.from_user
    if (!friend || seen.has(friend.id)) continue
    seen.add(friend.id)
    result.push({
      ...friend,
      friendshipId: f.id,
      friendshipStatus: f.status,
      friendSince: f.created_at,
    })
  }
  return result
}

// ── Computed ──────────────────────────────────────────
const filteredFriends = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return friends.value
  return friends.value.filter(f =>
    (f.full_name || `${f.first_name} ${f.last_name}`).toLowerCase().includes(q) ||
    f.username?.toLowerCase().includes(q) ||
    f.bio?.toLowerCase().includes(q)
  )
})

const filteredSuggested = computed(() => {
  const q = searchQuery.value.toLowerCase()
  if (!q) return suggestedUsers.value
  return suggestedUsers.value.filter(u =>
    (u.full_name || `${u.first_name} ${u.last_name}`).toLowerCase().includes(q) ||
    u.username?.toLowerCase().includes(q) ||
    u.top_genres?.some(g => g.toLowerCase().includes(q))
  )
})

const pendingCount = computed(() => pendingRequests.value.length)

// ── Actions ──────────────────────────────────────────
const acceptingIds = ref(new Set())
const decliningIds = ref(new Set())
const followingIds = ref(new Set())

const acceptRequest = async (friendship) => {
  acceptingIds.value.add(friendship.id)
  try {
    await socialAPI.acceptFriend(friendship.id)
    pendingRequests.value = pendingRequests.value.filter(r => r.id !== friendship.id)
    await loadData()
  } catch (e) {
    // Accept request failed
  } finally {
    acceptingIds.value.delete(friendship.id)
  }
}

const declineRequest = async (friendship) => {
  decliningIds.value.add(friendship.id)
  try {
    await socialAPI.declineFriend(friendship.id)
    pendingRequests.value = pendingRequests.value.filter(r => r.id !== friendship.id)
  } catch (e) {
    // Decline request failed
  } finally {
    decliningIds.value.delete(friendship.id)
  }
}

const followUser = async (user) => {
  followingIds.value.add(user.id)
  try {
    await socialService.followUser(user.id)
    suggestedUsers.value = suggestedUsers.value.filter(u => u.id !== user.id)
  } catch (e) {
    // Follow user failed
  } finally {
    followingIds.value.delete(user.id)
  }
}

const openProfile = (user) => {
  router.push(`/users/${user.id}`)
}

const openMessage = (user) => {
  router.push('/correspondence')
}

// ── Helpers ──────────────────────────────────────────
const getInitials = (user) => {
  const first = user.first_name?.[0] || user.username?.[0] || '?'
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase()
}

const getDisplayName = (user) => {
  if (user.full_name) return user.full_name
  if (user.first_name) return `${user.first_name} ${user.last_name || ''}`.trim()
  return user.username || 'Unknown'
}

const getMatchColor = (score) => {
  if (score >= 90) return 'from-indigo-500 to-purple-600'
  if (score >= 80) return 'from-indigo-500 to-blue-600'
  if (score >= 70) return 'from-blue-500 to-cyan-600'
  return 'from-slate-600 to-slate-700'
}

const getMatchBadgeClasses = (score) => {
  if (score >= 80) return 'bg-indigo-500/15 text-indigo-400 border-indigo-500/20'
  if (score >= 60) return 'bg-blue-500/15 text-blue-400 border-blue-500/20'
  return 'bg-slate-500/15 text-slate-400 border-slate-500/20'
}

const getStatusLabel = (user) => {
  if (user.currently_reading) return 'READING'
  if (user.books_read_count > 100) return 'ARCHIVIST'
  return 'ONLINE'
}

const getStatusColor = (user) => {
  if (user.currently_reading) return 'bg-emerald-500'
  return 'bg-slate-500'
}
</script>

<template>
  <div class="p-4 sm:p-6 lg:p-8 max-w-[1400px] mx-auto">

    <!-- Header -->
    <PageHeader
      title="Kindred Minds"
      accentWord="Kindred"
      subtitle="Connect with readers who share your intellectual frequency. Explore archives, exchange insights, and grow together."
    />

    <!-- Stats Bar -->
    <div class="flex flex-wrap items-center gap-2 sm:gap-6 mb-6 sm:mb-8">
      <div class="flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl sm:rounded-2xl bg-white/[0.03] border border-white/5">
        <Users :size="14" class="text-indigo-400 sm:w-4 sm:h-4" />
        <span class="text-xs sm:text-sm font-bold text-white">{{ friends.length }}</span>
        <span class="text-[10px] sm:text-xs text-slate-500">Friends</span>
      </div>
      <div v-if="pendingCount > 0" class="flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl sm:rounded-2xl bg-amber-500/5 border border-amber-500/10">
        <Clock :size="14" class="text-amber-400 sm:w-4 sm:h-4" />
        <span class="text-xs sm:text-sm font-bold text-amber-400">{{ pendingCount }}</span>
        <span class="text-[10px] sm:text-xs text-slate-500">Pending</span>
      </div>
      <div class="flex items-center gap-2 px-3 py-2 sm:px-4 sm:py-2.5 rounded-xl sm:rounded-2xl bg-white/[0.03] border border-white/5">
        <Sparkles :size="14" class="text-purple-400 sm:w-4 sm:h-4" />
        <span class="text-xs sm:text-sm font-bold text-white">{{ suggestedUsers.length }}</span>
        <span class="text-[10px] sm:text-xs text-slate-500">Suggested</span>
      </div>
    </div>

    <!-- Search + Tabs -->
    <div class="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-6 sm:mb-8">
      <div class="relative flex-1 group">
        <Search :size="16" class="absolute left-3.5 sm:left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-400 transition-colors" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search by name or interest..."
          class="w-full bg-white/[0.03] border border-white/5 rounded-xl sm:rounded-2xl pl-10 sm:pl-12 pr-4 py-2.5 sm:py-3 text-sm text-white outline-none focus:border-indigo-500/50 transition-all placeholder-slate-600"
        />
      </div>
      <div class="flex items-center gap-0.5 sm:gap-1 p-1 bg-slate-900/40 border border-white/5 rounded-xl sm:rounded-2xl shrink-0 self-start">
        <button
          @click="activeTab = 'friends'"
          :class="activeTab === 'friends' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'"
          class="flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-widest transition-all"
        >
          Friends
        </button>
        <button
          @click="activeTab = 'pending'"
          :class="activeTab === 'pending' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'"
          class="flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-widest transition-all relative"
        >
          Pending
          <span v-if="pendingCount > 0" class="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[8px] font-bold flex items-center justify-center">
            {{ pendingCount }}
          </span>
        </button>
        <button
          @click="activeTab = 'discover'"
          :class="activeTab === 'discover' ? 'bg-indigo-500 text-white shadow-lg' : 'text-slate-500 hover:text-white'"
          class="flex-1 sm:flex-none px-3 sm:px-4 py-2 rounded-lg sm:rounded-xl text-[9px] sm:text-[10px] font-black uppercase tracking-widest transition-all"
        >
          Discover
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
      <div v-for="i in 8" :key="i" class="h-[280px] sm:h-[420px] rounded-2xl sm:rounded-3xl bg-white/[0.03] animate-pulse" />
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="text-center py-12">
      <p class="text-red-400 mb-4">{{ error }}</p>
      <button @click="loadData" class="text-amber-500 hover:text-amber-400 font-bold text-sm">Try again</button>
    </div>

    <!-- ═══ TAB: Friends ═══ -->
    <template v-else-if="activeTab === 'friends'">
      <div v-if="filteredFriends.length > 0" class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
        <div
          v-for="friend in filteredFriends"
          :key="friend.id"
          class="group"
        >
          <div class="relative h-full rounded-2xl sm:rounded-3xl overflow-hidden bg-gradient-to-b from-slate-800/60 to-slate-900/80 border border-slate-700/30 hover:border-indigo-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 flex flex-col">

            <!-- Match badge -->
            <div v-if="friend.match_score" class="absolute top-2.5 sm:top-4 right-2.5 sm:right-4 z-10">
              <div :class="getMatchBadgeClasses(friend.match_score)" class="px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg border text-[8px] sm:text-[9px] font-black backdrop-blur-sm">
                {{ friend.match_score }}%
              </div>
            </div>

            <!-- Status label — hidden on mobile to save space -->
            <div class="absolute top-2.5 sm:top-4 left-2.5 sm:left-4 z-10 hidden sm:block">
              <div class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/30 backdrop-blur-sm">
                <div :class="getStatusColor(friend)" class="w-1.5 h-1.5 rounded-full animate-pulse" />
                <span class="text-[8px] font-black text-slate-400 uppercase tracking-widest">{{ getStatusLabel(friend) }}</span>
              </div>
            </div>

            <!-- Avatar Section -->
            <div class="pt-8 sm:pt-12 pb-2 sm:pb-4 flex flex-col items-center text-center px-3 sm:px-5">
              <!-- Circular avatar with gradient ring -->
              <div class="relative mb-2.5 sm:mb-4">
                <div :class="`bg-gradient-to-br ${getMatchColor(friend.match_score || 70)}`" class="w-14 h-14 sm:w-[76px] sm:h-[76px] rounded-full p-[2px] sm:p-[3px] group-hover:scale-105 transition-transform duration-300">
                  <div class="w-full h-full rounded-full bg-slate-900 p-[1.5px] sm:p-[2px]">
                    <div class="w-full h-full rounded-full overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                      <img v-if="friend.avatar" :src="getMediaUrl(friend.avatar)" class="w-full h-full object-cover" @error="friend.avatar = null" />
                      <span v-else class="text-white text-sm sm:text-lg font-black">{{ getInitials(friend) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Name -->
              <h3 class="text-xs sm:text-[15px] font-black text-white mb-0.5 group-hover:text-indigo-400 transition-colors line-clamp-1">
                {{ getDisplayName(friend) }}
              </h3>
              <p v-if="friend.username" class="text-[9px] sm:text-[10px] text-slate-600 mb-2 sm:mb-3">@{{ friend.username }}</p>

              <!-- Bio (italic quoted) — hidden on mobile -->
              <p v-if="friend.bio" class="hidden sm:block text-[11px] text-slate-500 italic line-clamp-2 leading-relaxed mb-4 px-2">
                "{{ friend.bio }}"
              </p>
            </div>

            <!-- Stats boxes: VAULT + SHARED -->
            <div class="px-2.5 sm:px-4 mb-2.5 sm:mb-4 grid grid-cols-2 gap-1.5 sm:gap-2">
              <div class="rounded-lg sm:rounded-xl bg-white/[0.03] border border-white/5 py-1.5 sm:py-2.5 px-2 sm:px-3 text-center">
                <div class="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-slate-600 mb-0.5 sm:mb-1">Vault</div>
                <div class="text-sm sm:text-base font-black text-white">{{ friend.books_read_count || friend.books_count || 0 }}</div>
              </div>
              <div class="rounded-lg sm:rounded-xl bg-white/[0.03] border border-white/5 py-1.5 sm:py-2.5 px-2 sm:px-3 text-center">
                <div class="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-slate-600 mb-0.5 sm:mb-1">Shared</div>
                <div class="text-sm sm:text-base font-black text-indigo-400">{{ friend.shared_books_count || 0 }}</div>
              </div>
            </div>

            <!-- Currently reading section — hidden on mobile -->
            <div v-if="friend.currently_reading" class="hidden sm:block px-4 mb-4">
              <div class="rounded-xl bg-indigo-500/5 border border-indigo-500/10 p-3">
                <div class="flex items-center gap-1.5 mb-2">
                  <BookMarked :size="10" class="text-indigo-400" />
                  <span class="text-[8px] font-black uppercase tracking-widest text-indigo-400">Devouring</span>
                </div>
                <p class="text-[11px] font-bold text-white line-clamp-1">{{ friend.currently_reading.title || friend.currently_reading }}</p>
                <div v-if="friend.currently_reading.progress" class="mt-2 w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" :style="{ width: friend.currently_reading.progress + '%' }" />
                </div>
              </div>
            </div>

            <!-- Top genres (if no currently reading) — hidden on mobile -->
            <div v-else-if="friend.top_genres?.length || friend.profile?.favorite_genres?.length" class="hidden sm:block px-4 mb-4">
              <div class="flex flex-wrap gap-1.5 justify-center">
                <span
                  v-for="genre in (friend.top_genres || friend.profile?.favorite_genres || []).slice(0, 3)"
                  :key="genre"
                  class="px-2.5 py-1 rounded-full bg-indigo-500/8 text-indigo-300/70 text-[9px] font-bold border border-indigo-500/10"
                >{{ genre }}</span>
              </div>
            </div>

            <!-- Spacer -->
            <div class="flex-1" />

            <!-- Actions -->
            <div class="px-2.5 sm:px-4 pb-3 sm:pb-4 flex gap-1.5 sm:gap-2">
              <button
                @click.stop="openProfile(friend)"
                class="flex-1 px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[8px] sm:text-[9px] font-black uppercase tracking-wider hover:bg-indigo-500/20 transition-all flex items-center justify-center gap-1"
              >
                <Library :size="11" class="sm:w-3 sm:h-3" /> <span class="hidden sm:inline">Explore </span>Vault
              </button>
              <button
                @click.stop="openMessage(friend)"
                class="w-8 h-8 sm:w-10 sm:h-10 rounded-lg sm:rounded-xl bg-slate-800/60 border border-slate-700/50 text-slate-400 hover:text-white hover:bg-slate-700/60 transition-all flex items-center justify-center shrink-0"
              >
                <MessageCircle :size="12" class="sm:w-3.5 sm:h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else class="py-24 text-center">
        <div class="w-16 h-16 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mx-auto mb-6 opacity-30">
          <Users :size="28" class="text-slate-500" />
        </div>
        <h3 v-if="searchQuery" class="text-lg font-black text-white/30 uppercase tracking-widest mb-2">No matches found</h3>
        <h3 v-else class="text-lg font-black text-white/30 uppercase tracking-widest mb-2">No friends yet</h3>
        <p class="text-sm text-slate-600 max-w-sm mx-auto mb-6">
          {{ searchQuery ? 'Try a different search term.' : 'Discover like-minded readers and send them a friend request.' }}
        </p>
        <button
          v-if="!searchQuery"
          @click="activeTab = 'discover'"
          class="px-6 py-2.5 rounded-xl bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-400 transition-all"
        >
          Discover Readers
        </button>
      </div>
    </template>

    <!-- ═══ TAB: Pending Requests ═══ -->
    <template v-else-if="activeTab === 'pending'">
      <div v-if="pendingRequests.length > 0" class="space-y-2 sm:space-y-3 max-w-2xl">
        <div
          v-for="request in pendingRequests"
          :key="request.id"
          class="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 rounded-xl sm:rounded-2xl bg-white/[0.03] border border-white/5 hover:border-amber-500/20 transition-all"
        >
          <!-- Avatar -->
          <div class="w-10 h-10 sm:w-12 sm:h-12 rounded-full bg-gradient-to-br from-amber-500 to-orange-600 p-[2px] shrink-0">
            <div class="w-full h-full rounded-full bg-slate-900 p-[1px]">
              <div class="w-full h-full rounded-full overflow-hidden bg-slate-800 flex items-center justify-center">
                <img v-if="request.from_user?.avatar" :src="getMediaUrl(request.from_user.avatar)" class="w-full h-full object-cover" />
                <span v-else class="text-white text-xs sm:text-sm font-black">{{ getInitials(request.from_user || {}) }}</span>
              </div>
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <h4 class="text-xs sm:text-sm font-bold text-white truncate">{{ getDisplayName(request.from_user || {}) }}</h4>
            <p class="text-[10px] sm:text-xs text-slate-500">wants to connect</p>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
            <button
              @click="acceptRequest(request)"
              :disabled="acceptingIds.has(request.id)"
              class="p-2 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl bg-indigo-500 text-white text-[10px] font-black uppercase tracking-wider hover:bg-indigo-400 transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              <Loader2 v-if="acceptingIds.has(request.id)" :size="12" class="animate-spin" />
              <UserCheck v-else :size="14" class="sm:w-3 sm:h-3" />
              <span class="hidden sm:inline">Accept</span>
            </button>
            <button
              @click="declineRequest(request)"
              :disabled="decliningIds.has(request.id)"
              class="p-2 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl bg-slate-800 text-slate-400 text-[10px] font-black uppercase tracking-wider hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              <Loader2 v-if="decliningIds.has(request.id)" :size="12" class="animate-spin" />
              <UserX v-else :size="14" class="sm:w-3 sm:h-3" />
              <span class="hidden sm:inline">Decline</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Empty pending -->
      <div v-else class="py-24 text-center">
        <div class="w-16 h-16 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mx-auto mb-6 opacity-30">
          <Clock :size="28" class="text-slate-500" />
        </div>
        <h3 class="text-lg font-black text-white/30 uppercase tracking-widest mb-2">No pending requests</h3>
        <p class="text-sm text-slate-600">When someone sends you a friend request, it will appear here.</p>
      </div>
    </template>

    <!-- ═══ TAB: Discover ═══ -->
    <template v-else-if="activeTab === 'discover'">
      <div v-if="filteredSuggested.length > 0" class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
        <div
          v-for="user in filteredSuggested"
          :key="user.id"
          class="group"
        >
          <div class="relative h-full rounded-2xl sm:rounded-3xl overflow-hidden bg-gradient-to-b from-slate-800/60 to-slate-900/80 border border-slate-700/30 hover:border-indigo-500/40 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 flex flex-col">

            <!-- Match badge -->
            <div v-if="user.match_score" class="absolute top-2.5 sm:top-4 right-2.5 sm:right-4 z-10">
              <div :class="getMatchBadgeClasses(user.match_score)" class="px-1.5 sm:px-2.5 py-0.5 sm:py-1 rounded-md sm:rounded-lg border text-[8px] sm:text-[9px] font-black backdrop-blur-sm">
                {{ user.match_score }}%
              </div>
            </div>

            <!-- Avatar Section -->
            <div class="pt-7 sm:pt-8 pb-2 sm:pb-4 flex flex-col items-center text-center px-3 sm:px-5">
              <!-- Circular avatar with gradient ring -->
              <div class="relative mb-2.5 sm:mb-4">
                <div :class="`bg-gradient-to-br ${getMatchColor(user.match_score || 50)}`" class="w-14 h-14 sm:w-[76px] sm:h-[76px] rounded-full p-[2px] sm:p-[3px] group-hover:scale-105 transition-transform duration-300">
                  <div class="w-full h-full rounded-full bg-slate-900 p-[1.5px] sm:p-[2px]">
                    <div class="w-full h-full rounded-full overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                      <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" @error="user.avatar = null" />
                      <span v-else class="text-white text-sm sm:text-lg font-black">{{ getInitials(user) }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Name -->
              <h3 class="text-xs sm:text-[15px] font-black text-white mb-0.5 group-hover:text-indigo-400 transition-colors line-clamp-1">
                {{ getDisplayName(user) }}
              </h3>
              <p class="text-[9px] sm:text-[10px] text-slate-600 mb-2 sm:mb-3">
                @{{ user.username || 'reader' }}
              </p>

              <!-- Bio — hidden on mobile -->
              <p v-if="user.bio" class="hidden sm:block text-[11px] text-slate-500 italic line-clamp-2 leading-relaxed mb-4 px-2">
                "{{ user.bio }}"
              </p>
            </div>

            <!-- Stats boxes: VAULT + SHARED -->
            <div class="px-2.5 sm:px-4 mb-2.5 sm:mb-4 grid grid-cols-2 gap-1.5 sm:gap-2">
              <div class="rounded-lg sm:rounded-xl bg-white/[0.03] border border-white/5 py-1.5 sm:py-2.5 px-2 sm:px-3 text-center">
                <div class="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-slate-600 mb-0.5 sm:mb-1">Vault</div>
                <div class="text-sm sm:text-base font-black text-white">{{ user.books_read_count || 0 }}</div>
              </div>
              <div class="rounded-lg sm:rounded-xl bg-white/[0.03] border border-white/5 py-1.5 sm:py-2.5 px-2 sm:px-3 text-center">
                <div class="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-slate-600 mb-0.5 sm:mb-1">Shared</div>
                <div class="text-sm sm:text-base font-black text-indigo-400">{{ user.shared_books_count || 0 }}</div>
              </div>
            </div>

            <!-- Genres — hidden on mobile -->
            <div v-if="user.top_genres?.length" class="hidden sm:block px-4 mb-4">
              <div class="flex flex-wrap gap-1.5 justify-center">
                <span
                  v-for="genre in user.top_genres.slice(0, 3)"
                  :key="genre"
                  class="px-2.5 py-1 rounded-full bg-indigo-500/8 text-indigo-300/70 text-[9px] font-bold border border-indigo-500/10"
                >{{ genre }}</span>
              </div>
            </div>

            <!-- Match bar -->
            <div v-if="user.match_score" class="px-2.5 sm:px-4 mb-2.5 sm:mb-4">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[7px] sm:text-[8px] font-black uppercase tracking-widest text-slate-600">Resonance</span>
                <span class="text-[9px] sm:text-[10px] font-black text-indigo-400">{{ user.match_score }}%</span>
              </div>
              <div class="w-full h-1 sm:h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  :class="`bg-gradient-to-r ${getMatchColor(user.match_score)}`"
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: user.match_score + '%' }"
                />
              </div>
            </div>

            <!-- Spacer -->
            <div class="flex-1" />

            <!-- Action -->
            <div class="px-2.5 sm:px-4 pb-3 sm:pb-4">
              <button
                @click.stop="followUser(user)"
                :disabled="followingIds.has(user.id)"
                class="w-full px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg sm:rounded-xl bg-indigo-500 text-white text-[8px] sm:text-[9px] font-black uppercase tracking-wider hover:bg-indigo-400 transition-all disabled:opacity-50 flex items-center justify-center gap-1 sm:gap-1.5"
              >
                <Loader2 v-if="followingIds.has(user.id)" :size="12" class="animate-spin" />
                <UserPlus v-else :size="11" class="sm:w-3 sm:h-3" />
                Add Friend
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty discover -->
      <div v-else class="py-24 text-center">
        <div class="w-16 h-16 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mx-auto mb-6 opacity-30">
          <Search :size="28" class="text-slate-500" />
        </div>
        <h3 class="text-lg font-black text-white/30 uppercase tracking-widest mb-2">No suggestions found</h3>
        <p class="text-sm text-slate-600 max-w-sm mx-auto">
          {{ searchQuery ? 'Try a different search term.' : 'Rate more books to improve suggestions based on your reading taste.' }}
        </p>
      </div>
    </template>

    <!-- Footer CTA -->
    <div v-if="!loading" class="mt-10 sm:mt-16 p-5 sm:p-10 rounded-2xl sm:rounded-3xl bg-indigo-500/5 border border-indigo-500/10 flex flex-col sm:flex-row items-center justify-between gap-4 sm:gap-6 overflow-hidden relative group">
      <div class="absolute top-0 right-0 p-10 sm:p-16 opacity-5 group-hover:scale-110 transition-transform duration-1000">
        <Network :size="80" class="sm:w-[100px] sm:h-[100px]" />
      </div>
      <div class="relative z-10 text-center sm:text-left">
        <h3 class="text-base sm:text-xl font-black text-white mb-1">Grow Your Reading Network</h3>
        <p class="text-xs sm:text-sm text-slate-500">Share your reading journey and connect with the most thoughtful readers.</p>
      </div>
      <button
        @click="activeTab = 'discover'"
        class="relative z-10 px-6 sm:px-8 py-3 sm:py-3.5 rounded-xl sm:rounded-2xl bg-indigo-500 text-white font-black text-[9px] sm:text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:scale-105 transition-all shrink-0"
      >
        Discover Readers
      </button>
    </div>
  </div>
</template>
