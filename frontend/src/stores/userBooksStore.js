import { defineStore } from 'pinia'
import { userBooksAPI } from '@/services/api'

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
    // All user books
    userBooks: (state) => state.books,

    // Filter and sort books based on current filters
    filteredBooks: (state) => {
      let filtered = [...state.books]

      // Filter by status
      if (state.filters.status) {
        filtered = filtered.filter((book) => book.status === state.filters.status)
      }

      // Filter by favorite
      if (state.filters.favorite !== null) {
        filtered = filtered.filter((book) => book.is_favorite === state.filters.favorite)
      }

      // Search in book title and authors
      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter((book) => {
          const title = book.book?.title?.toLowerCase() || ''
          const authors = book.book?.authors?.map((a) => a.name.toLowerCase()).join(' ') || ''
          return title.includes(search) || authors.includes(search)
        })
      }

      // Sort
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

    // Books grouped by status
    booksByStatus: (state) => {
      return {
        want_to_read: state.books.filter((b) => b.status === 'want_to_read'),
        currently_reading: state.books.filter((b) => b.status === 'currently_reading'),
        read: state.books.filter((b) => b.status === 'read'),
        abandoned: state.books.filter((b) => b.status === 'abandoned'),
      }
    },

    // Currently reading books
    currentlyReading: (state) => {
      return state.books.filter((b) => b.status === 'currently_reading')
    },

    // Favorite books
    favoriteBooks: (state) => {
      return state.books.filter((b) => b.is_favorite)
    },

    // Owned books (home library)
    ownedBooks: (state) => {
      return state.books.filter((b) => b.is_owned)
    },

    // Wishlisted books
    wishlistedBooks: (state) => {
      return state.books.filter((b) => b.is_wishlisted)
    },
  },

  actions: {
    // Fetch user's books
    async fetchBooks(params = {}) {
      this.loading = true
      this.error = null

      try {
        const response = await userBooksAPI.list(params)
        // Handle both paginated and non-paginated responses
        this.books = Array.isArray(response.data) ? response.data : (response.data.results || [])

        // Calculate stats
        this.calculateStats()

        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch books'
        console.error('Failed to fetch books:', error)
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    // Add book to library
    async addBook(bookData) {
      this.loading = true
      this.error = null

      try {
        console.log('userBooksStore.addBook called with:', bookData)
        const response = await userBooksAPI.create(bookData)
        console.log('userBooksAPI.create response:', response)
        this.books.unshift(response.data)
        this.calculateStats()
        return { success: true, data: response.data }
      } catch (error) {
        console.error('userBooksStore.addBook error:', error)
        console.error('Error response:', error.response)
        const errorMessage = error.response?.data?.detail
          || error.response?.data?.error
          || JSON.stringify(error.response?.data)
          || error.message
          || 'Failed to add book'
        this.error = errorMessage
        return { success: false, error: errorMessage }
      } finally {
        this.loading = false
      }
    },

    // Update book
    async updateBook(id, bookData) {
      this.loading = true
      this.error = null

      try {
        const response = await userBooksAPI.update(id, bookData)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        this.calculateStats()
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to update book'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    // Remove book from library
    async removeBook(id) {
      this.loading = true
      this.error = null

      try {
        await userBooksAPI.delete(id)
        this.books = this.books.filter((b) => b.id !== id)
        this.calculateStats()
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to remove book'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    // Update reading progress
    async updateProgress(id, currentPage) {
      try {
        const response = await userBooksAPI.updateProgress(id, currentPage)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    // Mark book as finished
    async markFinished(id, finishedAt = null) {
      try {
        const response = await userBooksAPI.markFinished(id, { finished_at: finishedAt })
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        this.calculateStats()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    // Toggle ownership
    async toggleOwned(id) {
      try {
        const response = await userBooksAPI.toggleOwned(id)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    // Toggle wishlist
    async toggleWishlisted(id) {
      try {
        const response = await userBooksAPI.toggleWishlisted(id)
        const index = this.books.findIndex((b) => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    // Bulk toggle ownership
    async bulkToggleOwned(ids, isOwned = true) {
      try {
        const response = await userBooksAPI.bulkToggleOwned(ids, isOwned)
        // Update local state
        ids.forEach((id) => {
          const index = this.books.findIndex((b) => b.id === id)
          if (index !== -1) {
            this.books[index].is_owned = isOwned
          }
        })
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    // Calculate statistics
    calculateStats() {
      this.stats.total = this.books.length
      this.stats.want_to_read = this.books.filter((b) => b.status === 'want_to_read').length
      this.stats.currently_reading = this.books.filter((b) => b.status === 'currently_reading').length
      this.stats.read = this.books.filter((b) => b.status === 'read').length
      this.stats.abandoned = this.books.filter((b) => b.status === 'abandoned').length
    },

    // Update filters
    setFilter(key, value) {
      this.filters[key] = value
    },

    // Reset filters
    resetFilters() {
      this.filters = {
        status: null,
        search: '',
        sortBy: 'updated_at',
        sortOrder: 'desc',
        favorite: null,
      }
    },

    // Clear store
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