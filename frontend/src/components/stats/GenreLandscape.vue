<script setup>
import { computed } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { useThemeStore } from '@/stores/themeStore'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip)

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const themeStore = useThemeStore()
const { elementRef, isVisible } = useScrollReveal()

const isDark = computed(() => themeStore.theme !== 'light')

const colors = [
  'rgba(99, 102, 241, 0.8)',   // indigo
  'rgba(168, 85, 247, 0.8)',   // purple
  'rgba(14, 165, 233, 0.8)',   // sky
  'rgba(16, 185, 129, 0.8)',   // emerald
  'rgba(245, 158, 11, 0.8)',   // amber
  'rgba(244, 63, 94, 0.8)',    // rose
  'rgba(6, 182, 212, 0.8)',    // cyan
  'rgba(236, 72, 153, 0.8)',   // pink
  'rgba(132, 204, 22, 0.8)',   // lime
  'rgba(251, 146, 60, 0.8)',   // orange
]

const chartData = computed(() => ({
  labels: props.data.map(g => g.name),
  datasets: [{
    data: props.data.map(g => g.count),
    backgroundColor: props.data.map((_, i) => colors[i % colors.length]),
    borderWidth: 0,
    hoverOffset: 8,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  cutout: '65%',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: isDark.value ? '#1e293b' : '#ffffff',
      titleColor: isDark.value ? '#f8fafc' : '#0f172a',
      bodyColor: isDark.value ? '#94a3b8' : '#475569',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      borderWidth: 1,
      padding: 10,
      cornerRadius: 8,
      callbacks: {
        label: (ctx) => ` ${ctx.parsed} book${ctx.parsed !== 1 ? 's' : ''}`,
      },
    },
  },
}))

const maxCount = computed(() => Math.max(...props.data.map(g => g.count), 1))
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6 h-full">
      <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">Genre Landscape</h3>

      <div v-if="!data.length" class="text-center py-10 text-sm text-slate-500">
        Read some books to see your genre landscape.
      </div>

      <template v-else>
        <!-- Doughnut -->
        <div class="h-[160px] mb-4">
          <Doughnut :key="themeStore.theme" :data="chartData" :options="chartOptions" />
        </div>

        <!-- Genre list -->
        <div class="space-y-2">
          <div v-for="(genre, i) in data" :key="genre.name" class="flex items-center gap-2.5">
            <div class="w-2.5 h-2.5 rounded-full flex-shrink-0" :style="{ backgroundColor: colors[i % colors.length] }" />
            <span class="text-xs text-slate-300 flex-1 truncate">{{ genre.name }}</span>
            <div class="w-16 h-1 bg-slate-800 rounded-full overflow-hidden flex-shrink-0">
              <div class="h-full rounded-full" :style="{ width: `${(genre.count / maxCount) * 100}%`, backgroundColor: colors[i % colors.length] }" />
            </div>
            <span class="text-[10px] text-slate-500 font-bold w-6 text-right flex-shrink-0">{{ genre.count }}</span>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
