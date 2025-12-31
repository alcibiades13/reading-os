import { defineStore } from 'pinia'
import { challengesAPI } from '@/services/api'

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
      return state.challenges.filter(c => c.is_active)
    },

    completedChallenges: (state) => {
      return state.challenges.filter(c => c.is_completed)
    },

    challengesByYear: (state) => {
      const grouped = {}
      state.challenges.forEach(challenge => {
        const year = new Date(challenge.start_date).getFullYear()
        if (!grouped[year]) grouped[year] = []
        grouped[year].push(challenge)
      })
      return grouped
    },

    filteredChallenges: (state) => {
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
      this.loading = true
      this.error = null

      try {
        const response = await challengesAPI.list(params)
        this.challenges = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch challenges'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async createChallenge(challengeData) {
      this.loading = true
      this.error = null

      try {
        const response = await challengesAPI.create(challengeData)
        this.challenges.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to create challenge'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateChallenge(id, challengeData) {
      this.loading = true
      this.error = null

      try {
        const response = await challengesAPI.update(id, challengeData)
        const index = this.challenges.findIndex(c => c.id === id)
        if (index !== -1) {
          this.challenges[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to update challenge'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteChallenge(id) {
      this.loading = true
      this.error = null

      try {
        await challengesAPI.delete(id)
        this.challenges = this.challenges.filter(c => c.id !== id)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to delete challenge'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateProgress(id) {
      try {
        const response = await challengesAPI.updateProgress(id)
        const index = this.challenges.findIndex(c => c.id === id)
        if (index !== -1) {
          this.challenges[index] = response.data
        }
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
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