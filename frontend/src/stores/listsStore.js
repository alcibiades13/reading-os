import { defineStore } from 'pinia'
import { listsAPI } from '@/services/api'

export const useListsStore = defineStore('lists', {
  state: () => ({
    lists: [],
    currentList: null,
    loading: false,
    error: null,
    filters: {
      public: null,
      smart: null,
      search: '',
    },
  }),

  getters: {
    filteredLists: (state) => {
      let filtered = [...state.lists]

      if (state.filters.public !== null) {
        filtered = filtered.filter(l => l.is_public === state.filters.public)
      }

      if (state.filters.smart !== null) {
        filtered = filtered.filter(l => l.is_smart === state.filters.smart)
      }

      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(l =>
          l.title.toLowerCase().includes(search) ||
          l.description?.toLowerCase().includes(search)
        )
      }

      return filtered.sort((a, b) => 
        new Date(b.updated_at) - new Date(a.updated_at)
      )
    },

    publicLists: (state) => {
      return state.lists.filter(l => l.is_public)
    },

    privateLists: (state) => {
      return state.lists.filter(l => !l.is_public)
    },
  },

  actions: {
    async fetchLists(params = {}) {
      this.loading = true
      this.error = null

      try {
        const response = await listsAPI.list(params)
        this.lists = response.data
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch lists'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchList(id) {
      this.loading = true
      this.error = null

      try {
        const response = await listsAPI.get(id)
        this.currentList = response.data
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch list'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async createList(listData) {
      this.loading = true
      this.error = null

      try {
        const response = await listsAPI.create(listData)
        this.lists.unshift(response.data)
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to create list'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async updateList(id, listData) {
      this.loading = true
      this.error = null

      try {
        const response = await listsAPI.update(id, listData)
        const index = this.lists.findIndex(l => l.id === id)
        if (index !== -1) {
          this.lists[index] = response.data
        }
        if (this.currentList?.id === id) {
          this.currentList = response.data
        }
        return { success: true, data: response.data }
      } catch (error) {
        this.error = error.response?.data || 'Failed to update list'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async deleteList(id) {
      this.loading = true
      this.error = null

      try {
        await listsAPI.delete(id)
        this.lists = this.lists.filter(l => l.id !== id)
        if (this.currentList?.id === id) {
          this.currentList = null
        }
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to delete list'
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async addBookToList(listId, bookId, note = '') {
      try {
        await listsAPI.addBook(listId, bookId, note)
        // Refresh list to get updated items
        await this.fetchList(listId)
        return { success: true }
      } catch (error) {
        return { success: false, error: error.response?.data }
      }
    },

    async removeBookFromList(listId, bookId) {
      try {
        await listsAPI.removeBook(listId, bookId)
        // Refresh list
        await this.fetchList(listId)
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
        public: null,
        smart: null,
        search: '',
      }
    },

    clear() {
      this.lists = []
      this.currentList = null
      this.error = null
      this.resetFilters()
    },
  },
})