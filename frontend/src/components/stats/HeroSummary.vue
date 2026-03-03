<script setup>
import { computed } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { BookOpen, FileText, Quote, Brain, Flame, TrendingUp, TrendingDown } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Object, default: null },
  yearComparison: { type: Object, default: null },
})

const { elementRef, isVisible } = useScrollReveal()

const delta = computed(() => props.yearComparison?.delta || 0)
const deltaText = computed(() => {
  if (!props.yearComparison || delta.value === 0) return null
  const abs = Math.abs(delta.value)
  return delta.value > 0
    ? `${abs} more than last year`
    : `${abs} fewer than last year`
})

const stats = computed(() => {
  if (!props.data) return []
  return [
    { label: 'Books Read', value: props.data.books_read, icon: BookOpen, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20' },
    { label: 'Pages Turned', value: props.data.pages_read?.toLocaleString(), icon: FileText, color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
    { label: 'Quotes Saved', value: props.data.total_quotes, icon: Quote, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
    { label: 'Words Learned', value: props.data.words_learned, icon: Brain, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  ]
})
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <!-- Stat Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      <div
        v-for="(stat, i) in stats"
        :key="stat.label"
        class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-4 sm:p-5 text-center"
        :style="{ transitionDelay: `${i * 80}ms` }"
      >
        <div :class="['w-10 h-10 rounded-xl border flex items-center justify-center mx-auto mb-3', stat.color]">
          <component :is="stat.icon" :size="18" />
        </div>
        <p class="text-2xl sm:text-3xl font-black text-white mb-1">{{ stat.value || 0 }}</p>
        <p class="text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider">{{ stat.label }}</p>
      </div>
    </div>

    <!-- Secondary stats row -->
    <div class="flex flex-wrap items-center justify-center gap-4 sm:gap-6 mt-4 text-xs text-slate-400">
      <div v-if="data?.current_streak > 0" class="flex items-center gap-1.5">
        <Flame :size="14" class="text-orange-400" />
        <span><b class="text-white">{{ data.current_streak }}</b> day streak</span>
      </div>
      <div v-if="data?.avg_rating" class="flex items-center gap-1.5">
        <span class="text-amber-400">★</span>
        <span>Avg rating: <b class="text-white">{{ data.avg_rating }}</b></span>
      </div>
      <div v-if="deltaText" class="flex items-center gap-1.5">
        <TrendingUp v-if="delta > 0" :size="14" class="text-emerald-400" />
        <TrendingDown v-else :size="14" class="text-rose-400" />
        <span>{{ deltaText }}</span>
      </div>
    </div>
  </div>
</template>
