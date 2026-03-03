import { defineStore } from 'pinia'
import { userBooksAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

export const useUserBooksStore = defineStore('userBooks', {
  state: () => ({
    books: [],
    loading: false,
    error: null,
    filters: {
      status: null, // 'want_to_read', 'currently_reading', 'read', 'abandoned'
      search: '',
      sortBy: 'updated_at', // 'title', 'rating', 'created_at', 'updated_at'
      sortOrder: 'desc', // 'asc', 'desc'
      favorite: null,
    },
    stats: {
      total: 0,
      want_to_read: 0,
      currently_reading: 0,
      read: 0,
      abandoned: 0,
    },
  }),

  getters: {
    userBooks: (state) => state.books,

    filteredBooks: (state) => {
      let filtered = [...state.books]

      if (state.filters.status) {
        filtered = filtered.filter((book) => book.status === state.filters.status)
      }

      if (state.filters.favorite !== null) {
        filtered = filtered.filter((book) => book.is_favorite === state.filters.favorite)
      }

      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter((book) => {
          const title = book.book?.title?.toLowerCase() || ''
          const authors = book.book?.authors?.map((a) => a.name.toLowerCase()).join(' ') || ''
          return title.includes(search) || authors.includes(search)
        })
      }

      filtered.sort((a, b) => {
        const sortBy = state.filters.sortBy
        const order = state.filters.sortOrder === 'asc' ? 1 : -1

        if (sortBy === 'title') {
          return (a.book?.title || '').localeCompare(b.book?.title || '') * order
        } else if (sortBy === 'rating') {
          return ((a.rating || 0) - (b.rating || 0)) * order
        } else if (sortBy === 'updated_at') {
          return (new Date(a.updated_at) - new Date(b.updated_at)) * order
        } else if (sortBy === 'created_at') {
          return (new Date(a.created_at) - new Date(b.created_at)) * order
        }
        return 0
      })

      return filtered
    },

    booksByStatus: (state) => {
      return {
        want_to_read: state.books.filter((b) => b.status === 'want_to_read'),
        currently_reading: state.books.filter((b) => b.status === 'currently_reading'),
        read: state.books.filter((b) => b.status === 'read'),
        abandoned: state.books.filter((b) => b.status === 'abandoned'),
      }
    },

    currentlyReading: (state) => {
      return state.books.filter((b) => b.status === 'currently_reading')
    },

    favoriteBooks: (state) => {
      return state.books.filter((b) => b.is_favorite)
    },

    ownedBooks: (state) => {
      return state.books.filter((b) => b.is_owned)
    },

    wishlistedBooks: (state) => {
      return state.books.filter((b) => b.is_wishlisted)
    },
  },

  actions: {
    async fetchBooks(params = {}) {
      return withLoading(this, async () => {
        const response = await userBooksAPI.list(params)
        this.books = Array.isArray(response.data) ? response.data : (response.data.results || [])
        this.calculateStats()
      }, 'Failed to fetch books')
    },

    async addBook(bookData) {
      return withLoading(this, async () => {
        const response = await userBooksAPI.create(bookData)
        this.books.unshift(response.data)
        this.calculateStats()
        return response.data
      }, 'Failed to add book')
    },

    async updateBook(id, bookData) {
      return withLoading(this, async () => {
        const response = await userBooksAPI.update(id, bookData)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        this.calculateStats()
        return response.data
      }, 'Failed to update book')
    },

    async removeBook(id) {
      return withLoading(this, async () => {
        await userBooksAPI.delete(id)
        this.books = this.books.filter((b) => b.id !== id)
        this.calculateStats()
      }, 'Failed to remove book')
    },

    async updateProgress(id, currentPage) {
      return tryCatch(async () => {
        const response = await userBooksAPI.updateProgress(id, currentPage)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return response.data
      })
    },

    async markFinished(id, finishedAt = null) {
      return tryCatch(async () => {
        const response = await userBooksAPI.markFinished(id, { finished_at: finishedAt })
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        this.calculateStats()
        return response.data
      })
    },

    async toggleOwned(id) {
      return tryCatch(async () => {
        const response = await userBooksAPI.toggleOwned(id)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return response.data
      })
    },

    async toggleWishlisted(id) {
      return tryCatch(async () => {
        const response = await userBooksAPI.toggleWishlisted(id)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return response.data
      })
    },

    async bulkToggleOwned(ids, isOwned = true) {
      return tryCatch(async () => {
        const response = await userBooksAPI.bulkToggleOwned(ids, isOwned)
        ids.forEach((id) => {
          const index = this.books.findIndex((b) => b.id === id)
          if (index !== -1) {
            this.books[index].is_owned = isOwned
          }
        })
        return response.data
      })
    },

    calculateStats() {
      this.stats.total = this.books.length
      this.stats.want_to_read = this.books.filter((b) => b.status === 'want_to_read').length
      this.stats.currently_reading = this.books.filter((b) => b.status === 'currently_reading').length
      this.stats.read = this.books.filter((b) => b.status === 'read').length
      this.stats.abandoned = this.books.filter((b) => b.status === 'abandoned').length
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    resetFilters() {
      this.filters = {
        status: null,
        search: '',
        sortBy: 'updated_at',
        sortOrder: 'desc',
        favorite: null,
      }
    },

    clear() {
      this.books = []
      this.error = null
      this.resetFilters()
      this.stats = {
        total: 0,
        want_to_read: 0,
        currently_reading: 0,
        read: 0,
        abandoned: 0,
      }
    },
  },
})
