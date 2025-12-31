import { defineStore } from 'pinia'
import { quotesAPI, quoteTagsAPI, booksAPI, userBooksAPI } from '@/services/api'

export const useQuotesStore = defineStore('quotes', {
  state: () => ({
    quotes: [],
    tags: [],
    loading: false,
    error: null,
    filters: {
      book: null,
      tag: null,
      favorite: null,
      search: '',
    },
  }),

  getters: {
    filteredQuotes: (state) => {
      if (!Array.isArray(state.quotes)) return []
      let filtered = [...state.quotes]

      if (state.filters.book) {
        filtered = filtered.filter(q => q.book?.id === state.filters.book)
      }

      if (state.filters.tag) {
        filtered = filtered.filter(q =>
          q.tags?.some(t => t.id === state.filters.tag)
        )
      }

      if (state.filters.favorite !== null) {
        filtered = filtered.filter(q => q.is_favorite === state.filters.favorite)
      }

      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(q =>
          q.text.toLowerCase().includes(search) ||
          q.note?.toLowerCase().includes(search)
        )
      }

      return filtered
    },

    favoriteQuotes: (state) => {
      if (!Array.isArray(state.quotes)) return []
      return state.quotes.filter(q => q.is_favorite)
    },

    quotesByTag: (state) => {
      const grouped = {}
      if (!Array.isArray(state.quotes)) return grouped
      state.tags.forEach(tag => {
        grouped[tag.id] = state.quotes.filter(q =>
          q.tags?.some(t => t.id === tag.id)
        )
      })
      return grouped
    },
  },

  actions: {
    async fetchQuotes(params = {}) {
      this.loading = true
      this.error = null

      try {
        const response = await quotesAPI.list(params)
        // Backend returns paginated response: {count, next, previous, results}
        this.quotes = Array.isArray(response.data?.results)
          ? response.data.results
          : (Array.isArray(response.data) ? response.data : [])
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch quotes'
        this.quotes = []
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchTags() {
      try {
        const response = await quoteTagsAPI.list()
        this.tags = Array.isArray(response.data) ? response.data : []
        return { success: true }
      } catch (error) {
        console.error('Failed to fetch tags:', error)
        this.tags = []
        return { success: false }
      }
    },

    async createQuote(quoteData) {
      this.loading = true
      this.error = null

      try {
        const response = await quotesAPI.create(quoteData)
        // Ensure quotes is an array before unshift
        if (!Array.isArray(this.quotes)) {
          this.quotes = []
        }
        this.quotes.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to create quote'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateQuote(id, quoteData) {
      this.loading = true
      this.error = null

      try {
        const response = await quotesAPI.update(id, quoteData)
        const index = this.quotes.findIndex(q => q.id === id)
        if (index !== -1) {
          this.quotes[index] = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to update quote'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteQuote(id) {
      this.loading = true
      this.error = null

      try {
        await quotesAPI.delete(id)
        this.quotes = this.quotes.filter(q => q.id !== id)
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to delete quote'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async createTag(tagData) {
      try {
        const response = await quoteTagsAPI.create(tagData)
        this.tags.push(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    async deleteTag(id) {
      try {
        await quoteTagsAPI.delete(id)
        this.tags = this.tags.filter(t => t.id !== id)
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    async importBook(bookData) {
      try {
        const response = await booksAPI.importBook(bookData)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data || 'Failed to import book' }
      }
    },

    async createUserBook(userBookData) {
      try {
        const response = await userBooksAPI.create(userBookData)
        return { success: true, data: response.data }
      } catch (error) {
        return { success: false, error: error.response?.data || 'Failed to create user book' }
      }
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    resetFilters() {
      this.filters = {
        book: null,
        tag: null,
        favorite: null,
        search: '',
      }
    },

    clear() {
      this.quotes = []
      this.tags = []
      this.error = null
      this.resetFilters()
    },
  },
})