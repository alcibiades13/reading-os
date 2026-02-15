<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { socialAPI } from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { getMediaUrl } from '@/utils/mediaUrl'
import { Users, ArrowRight } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const friends = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await socialAPI.myFriends()
    const currentUserId = authStore.user?.id
    const seen = new Set()
    const normalized = []
    for (const f of (res.data || [])) {
      const friend = f.from_user?.id === currentUserId ? f.to_user : f.from_user
      if (!friend || seen.has(friend.id)) continue
      seen.add(friend.id)
      normalized.push(friend)
    }
    friends.value = normalized
  } catch (e) {
    console.error('Error loading friends:', e)
  } finally {
    loading.value = false
  }
})

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
</script>

<template>
  <div class="p-5 rounded-[2rem] glass border-slate-800">
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Users :size="16" class="text-indigo-400" />
        </div>
        <div>
          <h3 class="text-sm font-black text-white uppercase tracking-wider">Friends</h3>
          <p class="text-[10px] text-slate-500 font-bold">
            {{ friends.length }} connected
          </p>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="h-11 rounded-xl bg-white/5 animate-pulse" />
    </div>

    <!-- No friends -->
    <div v-else-if="friends.length === 0" class="text-center py-4">
      <p class="text-xs text-slate-600 mb-3">No friends yet. Discover readers who share your taste.</p>
      <button
        @click="router.push('/friends')"
        class="px-4 py-2 rounded-xl bg-indigo-500 text-white text-[10px] font-black uppercase tracking-wider hover:bg-indigo-400 transition-all"
      >
        Discover
      </button>
    </div>

    <!-- Friends list -->
    <div v-else class="space-y-2">
      <div
        v-for="friend in friends.slice(0, 5)"
        :key="friend.id"
        @click="router.push(`/users/${friend.id}`)"
        class="flex items-center gap-3 p-2.5 -mx-1 rounded-xl hover:bg-white/[0.04] transition-all cursor-pointer group"
      >
        <!-- Circular avatar -->
        <div class="w-9 h-9 rounded-full overflow-hidden bg-gradient-to-br from-indigo-500 to-blue-600 flex items-center justify-center shrink-0 ring-2 ring-transparent group-hover:ring-indigo-500/30 transition-all">
          <img v-if="friend.avatar" :src="getMediaUrl(friend.avatar)" class="w-full h-full object-cover" @error="friend.avatar = null" />
          <span v-else class="text-white text-[10px] font-black">{{ getInitials(friend) }}</span>
        </div>
        <div class="flex-1 min-w-0">
          <h4 class="text-xs font-bold text-white truncate group-hover:text-indigo-400 transition-colors">
            {{ getDisplayName(friend) }}
          </h4>
          <p class="text-[10px] text-slate-600 truncate">
            {{ friend.books_count || 0 }} books
          </p>
        </div>
      </div>

      <!-- View all -->
      <button
        @click="router.push('/friends')"
        class="w-full mt-2 px-4 py-2.5 rounded-xl bg-white/[0.03] border border-white/5 text-white font-bold text-[10px] uppercase tracking-widest hover:bg-white/[0.06] hover:border-indigo-500/20 transition-all flex items-center justify-center gap-2 group"
      >
        View All Friends
        <ArrowRight :size="12" class="group-hover:translate-x-1 transition-transform" />
      </button>
    </div>
  </div>
</template>
