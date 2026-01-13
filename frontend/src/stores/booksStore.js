import { defineStore } from 'pinia'
import { booksAPI, authorsAPI, genresAPI } from '@/services/api'

export const useBooksStore = defineStore('books', {
  state: () => ({
    books: [],
    authors: [],
    genres: [],
    currentBook: null,
    loading: false,
    error: null,
    filters: {
      search: '',
      author: null,
      genre: null,
      language: null,
    },
    pagination: {
      page: 1,
      pageSize: 20,
      total: 0,
    },
  }),

  getters: {
    filteredBooks: (state) => {
      return state.books
    },
  },

  actions: {
    async fetchBooks(params = {}) {
      this.loading = true
      this.error = null

      try {
        const response = await booksAPI.list({
          ...params,
          ...this.filters,
        })
        // Handle paginated response (results) or direct array
        const data = response.data?.results || response.data
        // Ensure we always have a valid array
        this.books = Array.isArray(data) ? data : []
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch books'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchBook(id) {
      this.loading = true
      this.error = null

      try {
        const response = await booksAPI.get(id)
        this.currentBook = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch book'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchPopularBooks() {
      this.loading = true
      try {
        const response = await booksAPI.popular()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      } finally {
        this.loading = false
      }
    },

    async fetchRecentBooks() {
      this.loading = true
      try {
        const response = await booksAPI.recent()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      } finally {
        this.loading = false
      }
    },

    async fetchTrendingBooks() {
      this.loading = true
      try {
        const response = await booksAPI.trending()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      } finally {
        this.loading = false
      }
    },

    async fetchFeaturedBooks() {
      this.loading = true
      try {
        const response = await booksAPI.featured()
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      } finally {
        this.loading = false
      }
    },

    async fetchAuthors(params = {}) {
      try {
        const response = await authorsAPI.list(params)
        // Ensure we always have a valid array and filter out any null/undefined values
        this.authors = Array.isArray(response.data)
          ? response.data.filter(a => a && a.id)
          : []
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    async fetchGenres(params = {}) {
      try {
        const response = await genresAPI.list(params)
        // Handle paginated response (results) or direct array
        const data = response.data?.results || response.data
        // Ensure we always have a valid array and filter out any null/undefined values
        this.genres = Array.isArray(data)
          ? data.filter(g => g && g.id && g.name !== 'Knjiga') // Filter out 'Knjiga' as it's too generic
          : []
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    async updateBook(id, bookData) {
      this.loading = true
      this.error = null

      try {
        const response = await booksAPI.update(id, bookData)

        // Update in the books list if present
        const index = this.books.findIndex(b => b.id === id)
        if (index !== -1) {
          this.books[index] = response.data
        }

        // Update current book if it's the same
        if (this.currentBook && this.currentBook.id === id) {
          this.currentBook = response.data
        }

        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to update book'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteBook(id) {
      this.loading = true
      this.error = null

      try {
        await booksAPI.delete(id)
        this.books = this.books.filter(b => b.id !== id)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to delete book'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    resetFilters() {
      this.filters = {
        search: '',
        author: null,
        genre: null,
        language: null,
      }
    },

    clear() {
      this.books = []
      this.currentBook = null
      this.error = null
      this.resetFilters()
    },
  },
})