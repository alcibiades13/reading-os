<script setup>
import { onMounted } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { Users, BookOpen, Globe, UserPlus } from 'lucide-vue-next'

const circlesStore = useCirclesStore()

onMounted(() => {
  circlesStore.fetchDiscoverCircles()
})

async function handleJoin(circleId) {
  await circlesStore.joinPublicCircle(circleId)
}
</script>

<template>
  <div class="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-6">
    <div class="flex items-center gap-3 mb-6">
      <Globe :size="20" class="text-indigo-400" />
      <h2 class="text-lg font-black text-white">Discover Circles</h2>
    </div>

    <div v-if="circlesStore.discoverCircles.length === 0" class="text-center py-16">
      <Globe :size="48" class="text-slate-700 mx-auto mb-4" />
      <h3 class="text-lg font-black text-slate-400 mb-2">No Public Circles</h3>
      <p class="text-sm text-slate-600">No public circles available to join right now.</p>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="circle in circlesStore.discoverCircles"
        :key="circle.id"
        class="p-5 rounded-2xl bg-white/5 border border-white/10 hover:border-indigo-500/30 transition-all"
      >
        <div class="flex items-start gap-4">
          <div
            class="w-14 h-14 rounded-2xl shrink-0 flex items-center justify-center text-white font-black text-lg shadow-lg"
            :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}dd, #000000)` }"
          >
            {{ circle.name?.charAt(0) }}
          </div>
          <div class="flex-1 min-w-0">
            <h3 class="text-base font-bold text-white truncate">{{ circle.name }}</h3>
            <p v-if="circle.description" class="text-xs text-slate-500 line-clamp-2 mt-1">{{ circle.description }}</p>
            <div class="flex items-center gap-3 mt-2 text-[10px] text-slate-600 font-bold uppercase">
              <span class="flex items-center gap-1"><Users :size="10" /> {{ circle.members_count }} members</span>
              <span v-if="circle.creator" class="truncate">by {{ circle.creator.first_name }}</span>
            </div>

            <!-- Current book -->
            <div v-if="circle.current_book_data" class="mt-3 flex items-center gap-2 p-2 rounded-lg bg-white/5">
              <div class="w-6 h-8 rounded overflow-hidden shrink-0">
                <img v-if="circle.current_book_data.cover_image" :src="circle.current_book_data.cover_image" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="8" class="text-slate-600" /></div>
              </div>
              <p class="text-[10px] text-slate-400 truncate">Reading: {{ circle.current_book_data.title }}</p>
            </div>
          </div>
        </div>

        <button
          @click="handleJoin(circle.id)"
          class="w-full mt-4 px-4 py-2.5 rounded-xl bg-indigo-500/20 text-indigo-400 font-bold text-sm hover:bg-indigo-500/30 transition-colors flex items-center justify-center gap-2"
        >
          <UserPlus :size="16" />
          Join Circle
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }
</style>
