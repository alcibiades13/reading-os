import { defineStore } from 'pinia'
import { listsAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

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
      return withLoading(this, async () => {
        const response = await listsAPI.list(params)
        this.lists = response.data
      }, 'Failed to fetch lists')
    },

    async fetchList(id) {
      return withLoading(this, async () => {
        const response = await listsAPI.get(id)
        this.currentList = response.data
        return response.data
      }, 'Failed to fetch list')
    },

    async createList(listData) {
      return withLoading(this, async () => {
        const response = await listsAPI.create(listData)
        this.lists.unshift(response.data)
        return response.data
      }, 'Failed to create list')
    },

    async updateList(id, listData) {
      return withLoading(this, async () => {
        const response = await listsAPI.update(id, listData)
        const index = this.lists.findIndex(l => l.id === id)
        if (index !== -1) {
          this.lists[index] = response.data
        }
        if (this.currentList?.id === id) {
          this.currentList = response.data
        }
        return response.data
      }, 'Failed to update list')
    },

    async deleteList(id) {
      return withLoading(this, async () => {
        await listsAPI.delete(id)
        this.lists = this.lists.filter(l => l.id !== id)
        if (this.currentList?.id === id) {
          this.currentList = null
        }
      }, 'Failed to delete list')
    },

    async addBookToList(listId, bookId, note = '') {
      return tryCatch(async () => {
        await listsAPI.addBook(listId, bookId, note)
        await this.fetchList(listId)
      })
    },

    async removeBookFromList(listId, bookId) {
      return tryCatch(async () => {
        await listsAPI.removeBook(listId, bookId)
        await this.fetchList(listId)
      })
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
