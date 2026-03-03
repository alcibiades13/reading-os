<script setup>
import { computed } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { useThemeStore } from '@/stores/themeStore'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip)

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const themeStore = useThemeStore()
const { elementRef, isVisible } = useScrollReveal()

const isDark = computed(() => themeStore.theme !== 'light')

const hasRatings = computed(() => props.data.some(r => r.count > 0))

const barColors = [
  'rgba(244, 63, 94, 0.7)',    // 1 - rose
  'rgba(251, 113, 133, 0.7)',  // 2
  'rgba(251, 146, 60, 0.7)',   // 3 - orange
  'rgba(245, 158, 11, 0.7)',   // 4 - amber
  'rgba(234, 179, 8, 0.7)',    // 5 - yellow
  'rgba(132, 204, 22, 0.7)',   // 6 - lime
  'rgba(34, 197, 94, 0.7)',    // 7 - green
  'rgba(16, 185, 129, 0.7)',   // 8 - emerald
  'rgba(6, 182, 212, 0.7)',    // 9 - cyan
  'rgba(99, 102, 241, 0.7)',   // 10 - indigo
]

const chartData = computed(() => ({
  labels: props.data.map(r => `${r.rating}`),
  datasets: [{
    data: props.data.map(r => r.count),
    backgroundColor: barColors,
    borderRadius: 4,
    borderSkipped: false,
    maxBarThickness: 28,
  }],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
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
        title: (items) => `Rating: ${items[0].label}/10`,
        label: (ctx) => `${ctx.parsed.y} book${ctx.parsed.y !== 1 ? 's' : ''}`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: {
        color: isDark.value ? '#64748b' : '#475569',
        font: { size: 11, weight: '600' },
      },
      border: { display: false },
    },
    y: {
      grid: { color: isDark.value ? 'rgba(51,65,85,0.3)' : 'rgba(0,0,0,0.06)' },
      ticks: {
        color: isDark.value ? '#64748b' : '#475569',
        stepSize: 1,
        font: { size: 11 },
      },
      border: { display: false },
    },
  },
}))
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6 h-full">
      <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">How You Rate</h3>

      <div v-if="!hasRatings" class="text-center py-10 text-sm text-slate-500">
        Rate your books to see your rating pattern.
      </div>

      <div v-else class="h-[200px] sm:h-[260px]">
        <Bar :key="themeStore.theme" :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
