import { defineStore } from 'pinia'
import { quotesAPI, quoteTagsAPI, booksAPI, userBooksAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

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
        filtered = filtered.filter(q => {
          const bookId = typeof q.book === 'object' ? q.book?.id : q.book
          return bookId === state.filters.book
        })
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
      return withLoading(this, async () => {
        const response = await quotesAPI.list(params)
        this.quotes = Array.isArray(response.data?.results)
          ? response.data.results
          : (Array.isArray(response.data) ? response.data : [])
      }, 'Failed to fetch quotes')
    },

    async fetchTags() {
      return tryCatch(async () => {
        const response = await quoteTagsAPI.list()
        this.tags = Array.isArray(response.data) ? response.data : []
      })
    },

    async createQuote(quoteData) {
      return withLoading(this, async () => {
        const response = await quotesAPI.create(quoteData)
        if (!Array.isArray(this.quotes)) {
          this.quotes = []
        }
        this.quotes.unshift(response.data)
        return response.data
      }, 'Failed to create quote')
    },

    async updateQuote(id, quoteData) {
      return withLoading(this, async () => {
        const response = await quotesAPI.patch(id, quoteData)
        const index = this.quotes.findIndex(q => q.id === id)
        if (index !== -1) {
          this.quotes[index] = response.data
        }
        return response.data
      }, 'Failed to update quote')
    },

    async deleteQuote(id) {
      return withLoading(this, async () => {
        await quotesAPI.delete(id)
        this.quotes = this.quotes.filter(q => q.id !== id)
      }, 'Failed to delete quote')
    },

    async createTag(tagData) {
      return tryCatch(async () => {
        const response = await quoteTagsAPI.create(tagData)
        this.tags.push(response.data)
        return response.data
      })
    },

    async deleteTag(id) {
      return tryCatch(async () => {
        await quoteTagsAPI.delete(id)
        this.tags = this.tags.filter(t => t.id !== id)
      })
    },

    async importBook(bookData) {
      return tryCatch(async () => {
        const response = await booksAPI.importBook(bookData)
        return response.data
      })
    },

    async createUserBook(userBookData) {
      return tryCatch(async () => {
        const response = await userBooksAPI.create(userBookData)
        return response.data
      })
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
