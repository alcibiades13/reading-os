<script setup>
import { computed } from 'vue'
import { bookClubService } from '@/services/bookClubService'
import { BookOpen, Lock, BarChart3 } from 'lucide-vue-next'

const props = defineProps({
  poll: { type: Object, required: true },
})

const emit = defineEmits(['vote'])

const maxVotes = computed(() => {
  if (!props.poll?.options) return 1
  return Math.max(...props.poll.options.map(o => o.vote_count || 0), 1)
})

function getVotePercentage(option) {
  if (!props.poll.total_votes) return 0
  return Math.round(((option.vote_count || 0) / props.poll.total_votes) * 100)
}
</script>

<template>
  <div v-if="poll" class="p-6 rounded-2xl bg-white/5 border border-white/10 space-y-4">
    <div class="flex items-center gap-2">
      <BarChart3 :size="16" class="text-amber-400" />
      <h4 class="text-sm font-black text-white">{{ poll.question }}</h4>
      <span
        v-if="poll.is_closed"
        class="px-2 py-0.5 rounded-full bg-slate-500/20 text-slate-400 text-[9px] font-black uppercase"
      >
        Closed
      </span>
    </div>

    <div class="space-y-2">
      <button
        v-for="option in poll.options"
        :key="option.id"
        @click="!poll.is_closed && $emit('vote', poll.id, option.id)"
        :disabled="poll.is_closed"
        :class="[
          'w-full text-left p-3 rounded-xl border transition-all relative overflow-hidden',
          option.user_voted
            ? 'border-indigo-500/40 bg-indigo-500/10'
            : 'border-white/5 bg-white/[0.02] hover:bg-white/5',
          poll.is_closed ? 'cursor-default' : 'cursor-pointer'
        ]"
      >
        <!-- Progress bar background -->
        <div
          class="absolute inset-0 rounded-xl transition-all duration-500"
          :class="option.user_voted ? 'bg-indigo-500/10' : 'bg-white/5'"
          :style="{ width: `${getVotePercentage(option)}%` }"
        />

        <div class="relative z-10 flex items-center gap-3">
          <!-- Book cover (for book_vote) -->
          <div v-if="option.book_data" class="w-8 h-12 rounded-md overflow-hidden shrink-0 shadow">
            <img v-if="option.book_data.cover_image" :src="option.book_data.cover_image" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="10" class="text-slate-600" /></div>
          </div>

          <div class="flex-1 min-w-0">
            <p :class="['text-sm font-bold truncate', option.user_voted ? 'text-white' : 'text-slate-300']">
              {{ option.text }}
            </p>
            <p v-if="option.book_data" class="text-[10px] text-slate-500 truncate">
              {{ option.book_data.authors?.map(a => a.name).join(', ') }}
            </p>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <span class="text-xs font-black text-slate-400">{{ option.vote_count || 0 }}</span>
            <span class="text-[10px] text-slate-600">{{ getVotePercentage(option) }}%</span>
          </div>
        </div>
      </button>
    </div>

    <div class="flex items-center justify-between text-[10px] text-slate-600">
      <span>{{ poll.total_votes }} vote{{ poll.total_votes !== 1 ? 's' : '' }}</span>
      <span v-if="poll.allows_multiple">Multiple selections allowed</span>
    </div>
  </div>
</template>
