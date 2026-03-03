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
  yearComparison: { type: Object, default: null },
})

const themeStore = useThemeStore()
const { elementRef, isVisible } = useScrollReveal()

const isDark = computed(() => themeStore.theme !== 'light')

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const chartData = computed(() => ({
  labels: monthLabels,
  datasets: [{
    data: props.data.map(m => m.books),
    backgroundColor: isDark.value ? 'rgba(99, 102, 241, 0.6)' : 'rgba(99, 102, 241, 0.8)',
    borderRadius: 6,
    borderSkipped: false,
    maxBarThickness: 32,
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

const totalBooks = computed(() => props.data.reduce((sum, m) => sum + m.books, 0))
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider">Your Reading Year</h3>
        <span class="text-xs text-slate-500">
          <b class="text-slate-300">{{ totalBooks }}</b> books
        </span>
      </div>

      <div v-if="totalBooks === 0" class="text-center py-10 text-sm text-slate-500">
        Finish a book to see your monthly rhythm.
      </div>

      <div v-else class="h-[200px] sm:h-[240px]">
        <Bar :key="themeStore.theme" :data="chartData" :options="chartOptions" />
      </div>
    </div>
  </div>
</template>
