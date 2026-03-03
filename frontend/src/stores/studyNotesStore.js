import { defineStore } from 'pinia'
import { studyNotesAPI } from '@/services/api'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

export const useStudyNotesStore = defineStore('studyNotes', {
  state: () => ({
    notes: [],
    loading: false,
    error: null,
    filters: {
      book: null,
      type: null,
      reference: null,
      tag: null,
      search: '',
    },
  }),

  getters: {
    filteredNotes: (state) => {
      if (!Array.isArray(state.notes)) return []
      let filtered = [...state.notes]

      if (state.filters.book) {
        filtered = filtered.filter(n => n.book === state.filters.book)
      }

      if (state.filters.type) {
        filtered = filtered.filter(n => n.note_type === state.filters.type)
      }

      if (state.filters.reference) {
        filtered = filtered.filter(n => n.reference === state.filters.reference)
      }

      if (state.filters.tag) {
        filtered = filtered.filter(n =>
          n.tags?.some(t => t.id === state.filters.tag)
        )
      }

      if (state.filters.search) {
        const search = state.filters.search.toLowerCase()
        filtered = filtered.filter(n =>
          n.content.toLowerCase().includes(search) ||
          n.reference?.toLowerCase().includes(search)
        )
      }

      return filtered
    },

    notesByReference: (state) => {
      const grouped = {}
      if (!Array.isArray(state.notes)) return grouped

      state.notes.forEach(note => {
        const ref = note.reference || 'General'
        if (!grouped[ref]) {
          grouped[ref] = []
        }
        grouped[ref].push(note)
      })

      return grouped
    },

    notesByType: (state) => {
      const grouped = {
        note: [],
        quote: [],
        question: [],
        insight: []
      }
      if (!Array.isArray(state.notes)) return grouped

      state.notes.forEach(note => {
        if (grouped[note.note_type]) {
          grouped[note.note_type].push(note)
        }
      })

      return grouped
    },

    references: (state) => {
      if (!Array.isArray(state.notes)) return []
      const refs = new Set(state.notes.map(n => n.reference || 'General'))
      return Array.from(refs).sort()
    },
  },

  actions: {
    async fetchNotes(params = {}) {
      return withLoading(this, async () => {
        const response = await studyNotesAPI.list(params)
        this.notes = Array.isArray(response.data?.results)
          ? response.data.results
          : (Array.isArray(response.data) ? response.data : [])
      }, 'Failed to fetch study notes')
    },

    async createNote(noteData) {
      return withLoading(this, async () => {
        const response = await studyNotesAPI.create(noteData)
        if (!Array.isArray(this.notes)) {
          this.notes = []
        }
        this.notes.unshift(response.data)
        return response.data
      }, 'Failed to create note')
    },

    async updateNote(id, noteData) {
      return withLoading(this, async () => {
        const response = await studyNotesAPI.update(id, noteData)
        const index = this.notes.findIndex(n => n.id === id)
        if (index !== -1) {
          Object.assign(this.notes[index], response.data)
        }
        return response.data
      }, 'Failed to update note')
    },

    async deleteNote(id) {
      return withLoading(this, async () => {
        await studyNotesAPI.delete(id)
        this.notes = this.notes.filter(n => n.id !== id)
      }, 'Failed to delete note')
    },

    async promoteToQuote(noteId) {
      return withLoading(this, async () => {
        const response = await studyNotesAPI.promoteToQuote(noteId)
        const index = this.notes.findIndex(n => n.id === noteId)
        if (index !== -1) {
          this.notes[index].is_promoted_to_quote = true
          this.notes[index].promoted_quote = response.data.quote_id
        }
        return response.data
      }, 'Failed to promote note')
    },

    async fetchReferences(bookId) {
      return tryCatch(async () => {
        const response = await studyNotesAPI.references(bookId)
        return response.data
      })
    },

    setFilter(key, value) {
      this.filters[key] = value
    },

    resetFilters() {
      this.filters = {
        book: null,
        type: null,
        reference: null,
        tag: null,
        search: '',
      }
    },

    clear() {
      this.notes = []
      this.error = null
      this.resetFilters()
    },
  },
})
