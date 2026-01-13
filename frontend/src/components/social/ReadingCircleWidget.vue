<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { socialService } from '@/services/socialService'
import FollowButton from './FollowButton.vue'
import { Users, Sparkles, ArrowRight } from 'lucide-vue-next'

const router = useRouter()

const suggestedUsers = ref([])
const followingCount = ref(12)
const followersCount = ref(8)
const loading = ref(true)

onMounted(async () => {
  await loadSuggestions()
})

const loadSuggestions = async () => {
  loading.value = true
  try {
    const suggestions = await socialService.getSuggestedUsers(3)
    suggestedUsers.value = suggestions
  } catch (error) {
    console.error('Error loading suggestions:', error)
  } finally {
    loading.value = false
  }
}

const handleFollow = async (userId) => {
  try {
    await socialService.followUser(userId)
    // Update user state
    const user = suggestedUsers.value.find(u => u.id === userId)
    if (user) {
      user.is_following = true
      followingCount.value++
    }
  } catch (error) {
    console.error('Error following user:', error)
  }
}

const handleUnfollow = async (userId) => {
  try {
    await socialService.unfollowUser(userId)
    // Update user state
    const user = suggestedUsers.value.find(u => u.id === userId)
    if (user) {
      user.is_following = false
      followingCount.value--
    }
  } catch (error) {
    console.error('Error unfollowing user:', error)
  }
}

const goToCircles = () => {
  router.push('/circles')
}

const goToUserProfile = (userId) => {
  router.push(`/users/${userId}`)
}
</script>

<template>
  <div class="p-6 rounded-[2rem] glass border-slate-800 bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Users :size="20" class="text-indigo-400" />
        </div>
        <div>
          <h3 class="text-sm font-black text-white uppercase tracking-wider">Reading Circle</h3>
          <p class="text-[10px] text-slate-500 font-bold uppercase tracking-widest">
            {{ followingCount }} Following • {{ followersCount }} Followers
          </p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <div v-for="i in 3" :key="i" class="h-16 rounded-2xl bg-white/5 animate-pulse" />
    </div>

    <!-- Suggested Users -->
    <div v-else class="space-y-4">
      <div class="flex items-center gap-2 mb-4">
        <Sparkles :size="14" class="text-indigo-400" />
        <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Suggested for you</span>
      </div>

      <div
        v-for="user in suggestedUsers"
        :key="user.id"
        class="group relative"
      >
        <div class="p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] hover:border-indigo-500/30 transition-all cursor-pointer">
          <div class="flex items-center gap-3 mb-3">
            <div
              @click="goToUserProfile(user.id)"
              class="w-10 h-10 rounded-full overflow-hidden ring-2 ring-white/10 group-hover:ring-indigo-500/30 transition-all flex-shrink-0"
            >
              <img :src="user.avatar" class="w-full h-full object-cover" />
            </div>
            <div class="flex-1 min-w-0">
              <h4
                @click="goToUserProfile(user.id)"
                class="text-sm font-bold text-white truncate hover:text-indigo-400 transition-colors"
              >
                {{ user.first_name }} {{ user.last_name }}
              </h4>
              <div class="flex items-center gap-2 text-[9px] text-slate-500 font-black uppercase tracking-widest">
                <span class="text-indigo-400">{{ user.match_score }}% match</span>
                <span>•</span>
                <span>{{ user.shared_books_count }} shared</span>
              </div>
            </div>
          </div>

          <!-- Top Genres -->
          <div class="flex flex-wrap gap-1.5 mb-3">
            <span
              v-for="genre in user.top_genres.slice(0, 2)"
              :key="genre"
              class="px-2 py-0.5 rounded-lg bg-indigo-500/10 text-[9px] font-black text-indigo-400 uppercase tracking-wider"
            >
              {{ genre }}
            </span>
          </div>

          <!-- Follow Button -->
          <FollowButton
            :userId="user.id"
            :initialState="user.is_following ? 'following' : 'not_following'"
            size="small"
            @follow="handleFollow"
            @unfollow="handleUnfollow"
            class="w-full"
          />
        </div>
      </div>

      <!-- View All Button -->
      <button
        @click="goToCircles"
        class="w-full px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-xs uppercase tracking-widest hover:bg-white/10 hover:border-indigo-500/30 transition-all flex items-center justify-center gap-2 group"
      >
        View All Suggestions
        <ArrowRight :size="14" class="group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Light mode adjustments */
body.light .text-white {
  color: #0f172a !important;
}

body.light .text-slate-500 {
  color: #64748b !important;
}

body.light .bg-white\/\[0\.02\],
body.light .bg-white\/5 {
  background-color: rgba(0, 0, 0, 0.03) !important;
}

body.light .border-white\/5,
body.light .border-white\/10 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}
</style>
