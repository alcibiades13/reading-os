import { defineStore } from 'pinia'
import { usersAPI } from '@/services/api'
import { withLoading } from '@/utils/storeHelpers'

export const useReadingStatsStore = defineStore('readingStats', {
  state: () => ({
    stats: null,
    loading: false,
    error: null,
    year: new Date().getFullYear(),
  }),

  getters: {
    overview: (state) => state.stats?.overview || null,
    monthly: (state) => state.stats?.monthly || [],
    genres: (state) => state.stats?.genres || [],
    ratings: (state) => state.stats?.ratings || [],
    pace: (state) => state.stats?.pace || null,
    engagement: (state) => state.stats?.engagement || [],
    authors: (state) => state.stats?.authors || null,
    quotes: (state) => state.stats?.quotes || null,
    yearComparison: (state) => state.stats?.year_comparison || null,
    heatmap: (state) => state.stats?.heatmap || [],
    vocabulary: (state) => state.stats?.vocabulary || null,
    hasData: (state) => state.stats?.overview?.total_books_read > 0,
  },

  actions: {
    async fetchStats(year) {
      if (year) this.year = year
      return withLoading(this, async () => {
        const response = await usersAPI.getReadingStats(this.year)
        this.stats = response.data
        return this.stats
      }, 'Failed to load reading stats')
    },
  },
})
