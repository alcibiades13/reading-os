<script setup>
import { computed } from 'vue'
import { Dna, Sparkles, ArrowRight } from 'lucide-vue-next'

const props = defineProps({
  profile: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
})

const attributes = [
  { key: 'pace_preference', label: 'Pace', left: 'Slow', right: 'Fast' },
  { key: 'complexity_tolerance', label: 'Complexity', left: 'Simple', right: 'Complex' },
  { key: 'emotional_preference', label: 'Emotion', left: 'Light', right: 'Intense' },
  { key: 'darkness_tolerance', label: 'Tone', left: 'Light', right: 'Dark' },
  { key: 'character_focus_preference', label: 'Focus', left: 'Plot', right: 'Characters' },
  { key: 'introspection_preference', label: 'Depth', left: 'Action', right: 'Introspective' },
]

const hasThemes = computed(() => {
  return props.profile?.themes_affinity?.length > 0
})

const getProgressWidth = (value) => {
  return `${(value || 0.5) * 100}%`
}
</script>

<template>
  <div class="p-6 rounded-3xl bg-gradient-to-br from-indigo-500/5 via-transparent to-purple-500/5 border border-white/5">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Dna :size="20" class="text-indigo-400" />
        </div>
        <div>
          <h3 class="text-lg font-black text-white">Your Reading DNA</h3>
          <p class="text-xs text-slate-500">Based on {{ profile.vote_count || 0 }} rated books</p>
        </div>
      </div>
      <router-link
        to="/discover"
        class="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
      >
        View Full Profile <ArrowRight :size="12" />
      </router-link>
    </div>

    <!-- Attributes Grid -->
    <div :class="['grid gap-4 mb-6', compact ? 'grid-cols-1' : 'grid-cols-1 xl:grid-cols-2']">
      <div v-for="attr in attributes" :key="attr.key" class="space-y-1.5">
        <div class="flex justify-between text-[10px] text-slate-500 uppercase tracking-wider font-bold">
          <span>{{ attr.left }}</span>
          <span class="text-slate-400">{{ attr.label }}</span>
          <span>{{ attr.right }}</span>
        </div>
        <div class="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
            :style="{ width: getProgressWidth(profile[attr.key]) }"
          />
        </div>
      </div>
    </div>

    <!-- Themes -->
    <div v-if="hasThemes">
      <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest block mb-3">
        Favorite Themes
      </span>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="theme in profile.themes_affinity"
          :key="theme"
          class="px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-black text-indigo-400 uppercase tracking-wider"
        >
          {{ theme }}
        </span>
      </div>
    </div>

    <!-- Stats -->
    <div class="flex items-center gap-6 mt-6 pt-6 border-t border-white/5">
      <div>
        <span class="text-2xl font-black text-white">{{ profile.books_completed || 0 }}</span>
        <span class="text-[10px] text-slate-500 uppercase tracking-wider ml-1">books read</span>
      </div>
      <div>
        <span class="text-2xl font-black text-white">{{ Math.round((profile.completion_rate || 1) * 100) }}%</span>
        <span class="text-[10px] text-slate-500 uppercase tracking-wider ml-1">completion rate</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Light mode */
:global(body.light) .text-white {
  color: #0f172a !important;
}

:global(body.light) .bg-slate-800 {
  background-color: #e2e8f0 !important;
}
</style>
