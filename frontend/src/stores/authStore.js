import { defineStore } from 'pinia'
import { authAPI } from '@/services/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    loading: false,
    error: null,
  }),

  getters: {
    currentUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated,
  },

  actions: {
    // Initialize auth state from localStorage
    async initAuth() {
      const token = localStorage.getItem('access_token')
      const user = localStorage.getItem('user')

      if (token && user) {
        this.accessToken = token
        this.refreshToken = localStorage.getItem('refresh_token')
        this.user = JSON.parse(user)
        this.isAuthenticated = true

        // Refresh user data to get latest avatar URL
        await this.fetchUser()
      }
    },

    // Login
    async login(credentials) {
      this.loading = true
      this.error = null

      try {
        const response = await authAPI.login(credentials)
        const { user, tokens } = response.data

        // Save to state
        this.user = user
        this.accessToken = tokens.access
        this.refreshToken = tokens.refresh
        this.isAuthenticated = true

        // Save to localStorage
        localStorage.setItem('access_token', tokens.access)
        localStorage.setItem('refresh_token', tokens.refresh)
        localStorage.setItem('user', JSON.stringify(user))

        return { success: true }
      } catch (error) {
        this.error = error.response?.data?.error || 'Login failed'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    // Register
    async register(userData) {
      this.loading = true
      this.error = null

      try {
        const response = await authAPI.register(userData)
        const { user, tokens } = response.data

        // Save to state
        this.user = user
        this.accessToken = tokens.access
        this.refreshToken = tokens.refresh
        this.isAuthenticated = true

        // Save to localStorage
        localStorage.setItem('access_token', tokens.access)
        localStorage.setItem('refresh_token', tokens.refresh)
        localStorage.setItem('user', JSON.stringify(user))

        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Registration failed'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    // Logout
    logout() {
      // Clear state
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.isAuthenticated = false

      // Clear localStorage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },

    // Fetch current user profile
    async fetchUser() {
      try {
        const response = await authAPI.getMe()
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
        return { success: true }
      } catch (error) {
        console.error('Failed to fetch user:', error)
        return { success: false }
      }
    },

    // Update profile
    async updateProfile(data) {
      this.loading = true
      this.error = null

      try {
        const response = await authAPI.updateProfile(data)
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Update failed'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },
  },
})