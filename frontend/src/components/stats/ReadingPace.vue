<script setup>
import { useScrollReveal } from '@/composables/useScrollReveal'
import { Clock, Zap, Hourglass } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Object, default: null },
})

const { elementRef, isVisible } = useScrollReveal()
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6">
      <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">Reading Pace</h3>

      <div v-if="!data || data.total_tracked === 0" class="text-center py-6 text-sm text-slate-500">
        Add start and finish dates to your books to see pace stats.
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <!-- Average -->
        <div class="rounded-xl bg-slate-800/30 border border-slate-700/30 p-4 text-center">
          <div class="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mx-auto mb-2.5">
            <Clock :size="16" class="text-sky-400" />
          </div>
          <p class="text-2xl font-black text-white">{{ data.avg_days_per_book }}</p>
          <p class="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Avg days/book</p>
        </div>

        <!-- Fastest -->
        <div v-if="data.fastest" class="rounded-xl bg-slate-800/30 border border-slate-700/30 p-4 text-center">
          <div class="w-9 h-9 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-2.5">
            <Zap :size="16" class="text-emerald-400" />
          </div>
          <p class="text-2xl font-black text-white">{{ data.fastest.days }}<span class="text-sm font-medium text-slate-400"> days</span></p>
          <p class="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Fastest read</p>
          <p class="text-xs text-slate-400 truncate">{{ data.fastest.title }}</p>
        </div>

        <!-- Slowest -->
        <div v-if="data.slowest" class="rounded-xl bg-slate-800/30 border border-slate-700/30 p-4 text-center">
          <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-2.5">
            <Hourglass :size="16" class="text-amber-400" />
          </div>
          <p class="text-2xl font-black text-white">{{ data.slowest.days }}<span class="text-sm font-medium text-slate-400"> days</span></p>
          <p class="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-1">Most savored</p>
          <p class="text-xs text-slate-400 truncate">{{ data.slowest.title }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
