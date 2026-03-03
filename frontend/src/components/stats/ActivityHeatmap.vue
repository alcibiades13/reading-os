<script setup>
import { computed, ref } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { format, parseISO } from 'date-fns'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const { elementRef, isVisible } = useScrollReveal()
const hoveredDay = ref(null)

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Build grid: 7 rows (Mon-Sun) x ~53 columns
const grid = computed(() => {
  if (!props.data.length) return []

  const firstDate = parseISO(props.data[0].date)
  const startDow = firstDate.getDay() // 0=Sun, 1=Mon...
  // Adjust to Mon=0
  const offset = startDow === 0 ? 6 : startDow - 1

  // Pad with empty cells at the start
  const cells = []
  for (let i = 0; i < offset; i++) {
    cells.push({ empty: true })
  }
  for (const day of props.data) {
    cells.push(day)
  }
  return cells
})

// Column count for CSS grid
const columns = computed(() => Math.ceil(grid.value.length / 7))

// Month labels positioned at correct columns
const monthLabels = computed(() => {
  if (!props.data.length) return []
  const labels = []
  let lastMonth = -1
  let col = 0

  for (let i = 0; i < grid.value.length; i++) {
    if (i % 7 === 0) col++
    const cell = grid.value[i]
    if (cell.empty || !cell.date) continue
    const d = parseISO(cell.date)
    const m = d.getMonth()
    if (m !== lastMonth) {
      lastMonth = m
      labels.push({ label: months[m], col })
    }
  }
  return labels
})

function getCellColor(total) {
  if (!total || total === 0) return 'bg-slate-800/50'
  if (total === 1) return 'bg-indigo-500/25'
  if (total <= 3) return 'bg-indigo-500/50'
  return 'bg-indigo-500'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return format(parseISO(dateStr), 'MMM d, yyyy')
}

function activeDays() {
  return props.data.filter(d => d.total > 0).length
}
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-5 sm:p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-bold text-slate-300 uppercase tracking-wider">Activity Rhythm</h3>
        <span v-if="data.length" class="text-xs text-slate-500">
          <b class="text-slate-300">{{ activeDays() }}</b> active days
        </span>
      </div>

      <div v-if="!data.length" class="text-center py-6 text-sm text-slate-500">
        No activity data yet.
      </div>

      <div v-else class="overflow-x-auto pb-2">
        <!-- Month labels -->
        <div class="stats-heatmap-months flex text-[9px] text-slate-500 font-medium mb-1 ml-6">
          <div
            v-for="ml in monthLabels"
            :key="ml.label + ml.col"
            class="absolute"
            :style="{ left: `${(ml.col - 1) * 13 + 24}px` }"
          >
            {{ ml.label }}
          </div>
        </div>

        <div class="relative mt-4">
          <!-- Day labels -->
          <div class="absolute left-0 top-0 flex flex-col gap-[2px] text-[9px] text-slate-600 font-medium">
            <div class="h-[11px] flex items-center">M</div>
            <div class="h-[11px]"></div>
            <div class="h-[11px] flex items-center">W</div>
            <div class="h-[11px]"></div>
            <div class="h-[11px] flex items-center">F</div>
            <div class="h-[11px]"></div>
            <div class="h-[11px] flex items-center">S</div>
          </div>

          <!-- Grid -->
          <div
            class="stats-heatmap ml-6"
            :style="{
              display: 'grid',
              gridTemplateRows: 'repeat(7, 11px)',
              gridTemplateColumns: `repeat(${columns}, 11px)`,
              gap: '2px',
              gridAutoFlow: 'column',
            }"
          >
            <div
              v-for="(cell, i) in grid"
              :key="i"
              :class="[
                'rounded-sm cursor-default transition-colors relative',
                cell.empty ? 'bg-transparent' : getCellColor(cell.total),
              ]"
              @mouseenter="hoveredDay = cell.empty ? null : cell"
              @mouseleave="hoveredDay = null"
            />
          </div>
        </div>

        <!-- Tooltip -->
        <Teleport to="body">
          <div
            v-if="hoveredDay"
            class="fixed z-[100] pointer-events-none px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 shadow-xl text-xs"
            :style="{
              left: '50%',
              bottom: '80px',
              transform: 'translateX(-50%)',
            }"
          >
            <p class="font-bold text-slate-200 mb-1">{{ formatDate(hoveredDay.date) }}</p>
            <div class="flex gap-3 text-slate-400">
              <span v-if="hoveredDay.books">{{ hoveredDay.books }} book{{ hoveredDay.books > 1 ? 's' : '' }}</span>
              <span v-if="hoveredDay.quotes">{{ hoveredDay.quotes }} quote{{ hoveredDay.quotes > 1 ? 's' : '' }}</span>
              <span v-if="hoveredDay.vocabulary">{{ hoveredDay.vocabulary }} word{{ hoveredDay.vocabulary > 1 ? 's' : '' }}</span>
              <span v-if="!hoveredDay.total">No activity</span>
            </div>
          </div>
        </Teleport>

        <!-- Legend -->
        <div class="flex items-center justify-end gap-2 mt-3 text-[9px] text-slate-500">
          <span>Less</span>
          <div class="w-[11px] h-[11px] rounded-sm bg-slate-800/50" />
          <div class="w-[11px] h-[11px] rounded-sm bg-indigo-500/25" />
          <div class="w-[11px] h-[11px] rounded-sm bg-indigo-500/50" />
          <div class="w-[11px] h-[11px] rounded-sm bg-indigo-500" />
          <span>More</span>
        </div>
      </div>
    </div>
  </div>
</template>
