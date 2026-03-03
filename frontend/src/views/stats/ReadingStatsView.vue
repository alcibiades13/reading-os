<script setup>
import { onMounted, computed } from 'vue'
import { useReadingStatsStore } from '@/stores/readingStatsStore'
import { BarChart3, BookOpen } from 'lucide-vue-next'
import HeroSummary from '@/components/stats/HeroSummary.vue'
import MonthlyChart from '@/components/stats/MonthlyChart.vue'
import GenreLandscape from '@/components/stats/GenreLandscape.vue'
import RatingPattern from '@/components/stats/RatingPattern.vue'
import ReadingPace from '@/components/stats/ReadingPace.vue'
import EngagementDepth from '@/components/stats/EngagementDepth.vue'
import ActivityHeatmap from '@/components/stats/ActivityHeatmap.vue'
import VocabularyGrowth from '@/components/stats/VocabularyGrowth.vue'

const statsStore = useReadingStatsStore()

const loading = computed(() => statsStore.loading)
const hasData = computed(() => statsStore.hasData)

onMounted(() => {
  statsStore.fetchStats()
})
</script>

<template>
  <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

    <!-- Page Header -->
    <div class="mb-8 sm:mb-10">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-9 h-9 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <BarChart3 :size="18" class="text-indigo-400" />
        </div>
        <h1 class="text-2xl sm:text-3xl font-black tracking-tight">Reading Life</h1>
      </div>
      <p class="text-sm text-slate-400 ml-12">Your reading journey, reflected back to you.</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-6">
      <div v-for="n in 4" :key="n" class="rounded-2xl border border-slate-800/50 bg-slate-900/40 p-6">
        <div class="animate-pulse space-y-4">
          <div class="h-4 bg-slate-800 rounded w-1/3"></div>
          <div class="h-32 bg-slate-800/50 rounded-xl"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasData && !loading" class="text-center py-20">
      <div class="w-16 h-16 rounded-2xl bg-slate-800/50 border border-slate-700/50 flex items-center justify-center mx-auto mb-4">
        <BookOpen :size="28" class="text-slate-600" />
      </div>
      <h3 class="text-lg font-bold text-slate-300 mb-2">Your story starts here</h3>
      <p class="text-sm text-slate-500 max-w-sm mx-auto">
        Start reading and tracking books to see your reading life unfold. Every book you finish adds to your story.
      </p>
    </div>

    <!-- Stats Sections -->
    <div v-else class="space-y-6 sm:space-y-8">
      <HeroSummary
        :data="statsStore.overview"
        :year-comparison="statsStore.yearComparison"
      />

      <MonthlyChart
        :data="statsStore.monthly"
        :year-comparison="statsStore.yearComparison"
      />

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GenreLandscape :data="statsStore.genres" />
        <RatingPattern :data="statsStore.ratings" />
      </div>

      <ReadingPace :data="statsStore.pace" />

      <EngagementDepth :data="statsStore.engagement" />

      <ActivityHeatmap :data="statsStore.heatmap" />

      <VocabularyGrowth :data="statsStore.vocabulary" />
    </div>
  </div>
</template>
