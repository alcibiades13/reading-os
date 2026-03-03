import { defineStore } from 'pinia'
import { authAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

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
    isAdmin: (state) => state.user?.is_staff === true,
  },

  actions: {
    async initAuth() {
      const token = localStorage.getItem('access_token')
      const user = localStorage.getItem('user')

      if (token && user) {
        this.accessToken = token
        this.refreshToken = localStorage.getItem('refresh_token')
        this.user = JSON.parse(user)
        this.isAuthenticated = true

        await this.fetchUser()
      }
    },

    async login(credentials) {
      return withLoading(this, async () => {
        const response = await authAPI.login(credentials)
        const { user, tokens } = response.data

        this.user = user
        this.accessToken = tokens.access
        this.refreshToken = tokens.refresh
        this.isAuthenticated = true

        localStorage.setItem('access_token', tokens.access)
        localStorage.setItem('refresh_token', tokens.refresh)
        localStorage.setItem('user', JSON.stringify(user))
      }, 'Login failed')
    },

    async register(userData) {
      return withLoading(this, async () => {
        const response = await authAPI.register(userData)
        const { user, tokens } = response.data

        this.user = user
        this.accessToken = tokens.access
        this.refreshToken = tokens.refresh
        this.isAuthenticated = true

        localStorage.setItem('access_token', tokens.access)
        localStorage.setItem('refresh_token', tokens.refresh)
        localStorage.setItem('user', JSON.stringify(user))
      }, 'Registration failed')
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.isAuthenticated = false

      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },

    async fetchUser() {
      return tryCatch(async () => {
        const response = await authAPI.getMe()
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      })
    },

    async updateProfile(data) {
      return withLoading(this, async () => {
        const response = await authAPI.updateProfile(data)
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      }, 'Update failed')
    },
  },
})
