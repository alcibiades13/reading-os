<script setup>
import { computed } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { useThemeStore } from '@/stores/themeStore'
import { Brain } from 'lucide-vue-next'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

const props = defineProps({
  data: { type: Object, default: null },
})

const themeStore = useThemeStore()
const { elementRef, isVisible } = useScrollReveal()

const isDark = computed(() => themeStore.theme !== 'light')

const monthLabels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Cumulative growth
const cumulativeData = computed(() => {
  if (!props.data?.monthly) return []
  let sum = 0
  return props.data.monthly.map(m => {
    sum += m.count
    return sum
  })
})

const chartData = computed(() => ({
  labels: monthLabels,
  datasets: [{
    data: cumulativeData.value,
    borderColor: 'rgba(16, 185, 129, 0.8)',
    backgroundColor: isDark.value ? 'rgba(16, 185, 129, 0.08)' : 'rgba(16, 185, 129, 0.12)',
    fill: true,
    tension: 0.4,
    pointRadius: 3,
    pointHoverRadius: 6,
    pointBackgroundColor: 'rgba(16, 185, 129, 0.8)',
    pointBorderColor: isDark.value ? '#0f172a' : '#ffffff',
    pointBorderWidth: 2,
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
        label: (ctx) => `${ctx.parsed.y} word${ctx.parsed.y !== 1 ? 's' : ''} total`,
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
        font: { size: 11 },
      },
      border: { display: false },
    },
  },
}))

const masteryCards = computed(() => {
  if (!props.data) return []
  return [
    { label: 'New', count: props.data.new || 0, color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
    { label: 'Learning', count: props.data.learning || 0, color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
    { label: 'Mastered', count: props.data.mastered || 0, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  ]
})
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6">
      <div class="flex items-center gap-2 mb-4">
        <Brain :size="15" class="text-emerald-400" />
        <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider">Vocabulary Growth</h3>
      </div>

      <div v-if="!data || data.total === 0" class="text-center py-8 text-sm text-slate-500">
        Save vocabulary words from your reading to track growth.
      </div>

      <template v-else>
        <!-- Mastery cards -->
        <div class="grid grid-cols-3 gap-3 mb-5">
          <div
            v-for="card in masteryCards"
            :key="card.label"
            class="rounded-xl bg-slate-800/30 border border-slate-700/30 p-3 text-center"
          >
            <p class="text-xl font-black text-white">{{ card.count }}</p>
            <p :class="['text-[10px] font-bold uppercase tracking-wider', card.color.split(' ')[0]]">{{ card.label }}</p>
          </div>
        </div>

        <!-- Growth chart -->
        <div v-if="cumulativeData.some(v => v > 0)" class="h-[160px]">
          <Line :key="themeStore.theme" :data="chartData" :options="chartOptions" />
        </div>
      </template>
    </div>
  </div>
</template>
