import { defineStore } from 'pinia'
import { challengesAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

export const useChallengesStore = defineStore('challenges', {
  state: () => ({
    challenges: [],
    loading: false,
    error: null,
    filters: {
      active: null,
      completed: null,
      year: null,
    },
  }),

  getters: {
    activeChallenges: (state) => {
      if (!Array.isArray(state.challenges)) return []
      return state.challenges.filter(c => c.is_active)
    },

    completedChallenges: (state) => {
      if (!Array.isArray(state.challenges)) return []
      return state.challenges.filter(c => c.is_completed)
    },

    currentYearChallenge: (state) => {
      if (!Array.isArray(state.challenges)) return null
      const currentYear = new Date().getFullYear()
      return state.challenges.find(c =>
        c.is_active && new Date(c.start_date).getFullYear() === currentYear
      )
    },

    challengesByYear: (state) => {
      if (!Array.isArray(state.challenges)) return {}
      const grouped = {}
      state.challenges.forEach(challenge => {
        const year = new Date(challenge.start_date).getFullYear()
        if (!grouped[year]) grouped[year] = []
        grouped[year].push(challenge)
      })
      return grouped
    },

    filteredChallenges: (state) => {
      if (!Array.isArray(state.challenges)) return []
      let filtered = [...state.challenges]

      if (state.filters.active !== null) {
        filtered = filtered.filter(c => c.is_active === state.filters.active)
      }

      if (state.filters.completed !== null) {
        filtered = filtered.filter(c => c.is_completed === state.filters.completed)
      }

      if (state.filters.year) {
        filtered = filtered.filter(c =>
          new Date(c.start_date).getFullYear() === state.filters.year
        )
      }

      return filtered.sort((a, b) =>
        new Date(b.start_date) - new Date(a.start_date)
      )
    },
  },

  actions: {
    async fetchChallenges(params = {}) {
      return withLoading(this, async () => {
        const response = await challengesAPI.list(params)
        const data = response.data.results || response.data
        this.challenges = Array.isArray(data) ? data : []
      }, 'Failed to fetch challenges')
    },

    async fetchCurrentChallenges() {
      return withLoading(this, async () => {
        const response = await challengesAPI.current()
        this.challenges = Array.isArray(response.data) ? response.data : []
        return response.data
      }, 'Failed to fetch current challenges')
    },

    async createChallenge(challengeData) {
      return withLoading(this, async () => {
        const response = await challengesAPI.create(challengeData)
        this.challenges.unshift(response.data)
        return response.data
      }, 'Failed to create challenge')
    },

    async updateChallenge(id, challengeData) {
      return withLoading(this, async () => {
        const response = await challengesAPI.update(id, challengeData)
        const index = this.challenges.findIndex(c => c.id === id)
        if (index !== -1) {
          this.challenges[index] = response.data
        }
        return response.data
      }, 'Failed to update challenge')
    },

    async deleteChallenge(id) {
      return withLoading(this, async () => {
        await challengesAPI.delete(id)
        this.challenges = this.challenges.filter(c => c.id !== id)
      }, 'Failed to delete challenge')
    },

    async updateProgress(id) {
      return tryCatch(async () => {
        const response = await challengesAPI.updateProgress(id)
        const index = this.challenges.findIndex(c => c.id === id)
        if (index !== -1) {
          this.challenges[index] = response.data
        }
      })
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    resetFilters() {
      this.filters = {
        active: null,
        completed: null,
        year: null,
      }
    },

    clear() {
      this.challenges = []
      this.error = null
      this.resetFilters()
    },
  },
})
