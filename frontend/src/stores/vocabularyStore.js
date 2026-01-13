import { defineStore } from 'pinia'
import { vocabularyAPI } from '@/services/api'

export const useVocabularyStore = defineStore('vocabulary', {
  state: () => ({
    words: [],
    loading: false,
    error: null
  }),

  getters: {
    vocabularyWords: (state) => state.words,

    wordsByMastery: (state) => (level) => {
      if (level === 'all') return state.words
      return state.words.filter(w => w.mastery === level)
    },

    wordsByBook: (state) => {
      const byBook = {}
      state.words.forEach(w => {
        const book = w.book_title || 'Manual Entry'
        byBook[book] = (byBook[book] || 0) + 1
      })
      return byBook
    },

    practiceWords: (state) => {
      return state.words.filter(w => w.mastery !== 'mastered')
    },

    stats: (state) => ({
      total: state.words.length,
      new: state.words.filter(w => w.mastery === 'new').length,
      learning: state.words.filter(w => w.mastery === 'learning').length,
      mastered: state.words.filter(w => w.mastery === 'mastered').length,
      favorites: state.words.filter(w => w.is_favorite).length
    }),

    searchWords: (state) => (query) => {
      if (!query) return state.words
      const q = query.toLowerCase()
      return state.words.filter(w =>
        w.word.toLowerCase().includes(q) ||
        w.context?.toLowerCase().includes(q) ||
        w.book_title?.toLowerCase().includes(q) ||
        w.definition?.toLowerCase().includes(q)
      )
    }
  },

  actions: {
    // Transform backend snake_case fields to frontend camelCase
    _transformWord(backendWord) {
      return {
        id: backendWord.id,
        word: backendWord.word,
        definition: backendWord.definition,
        context: backendWord.context,
        book: backendWord.book,
        bookTitle: backendWord.book_title,
        bookAuthor: backendWord.book_author,
        pageNumber: backendWord.page_number,
        mastery: backendWord.mastery,
        reviewCount: backendWord.review_count,
        lastReviewedAt: backendWord.last_reviewed_at,
        tags: backendWord.tags,
        isFavorite: backendWord.is_favorite,
        isPublic: backendWord.is_public,
        createdAt: backendWord.created_at,
        updatedAt: backendWord.updated_at,
      }
    },

    async loadWords() {
      this.loading = true
      this.error = null
      try {
        const response = await vocabularyAPI.list()
        // Handle paginated response (DRF returns {results: [], count: N})
        const words = response.data.results || response.data
        // Transform snake_case to camelCase
        this.words = words.map(word => this._transformWord(word))
      } catch (error) {
        this.error = error.response?.data || 'Failed to load vocabulary'
        console.error('Failed to load vocabulary:', error)
      } finally {
        this.loading = false
      }
    },

    async saveWord(wordData) {
      this.loading = true
      this.error = null
      try {
        // Map frontend field names to backend field names
        const payload = {
          word: wordData.word,
          definition: wordData.definition,
          context: wordData.context || '',
          book: wordData.bookId || null,
          book_title: wordData.bookTitle || '',
          book_author: wordData.bookAuthor || '',
          page_number: wordData.pageNumber || null,
          mastery: wordData.mastery || 'new',
          tags: wordData.tags || [],
          is_favorite: wordData.isFavorite || false,
          is_public: wordData.isPublic !== undefined ? wordData.isPublic : true,
        }

        if (wordData.id) {
          // Update existing
          const response = await vocabularyAPI.update(wordData.id, payload)
          const transformedWord = this._transformWord(response.data)
          const index = this.words.findIndex(w => w.id === wordData.id)
          if (index !== -1) {
            this.words[index] = transformedWord
          }
          return transformedWord
        } else {
          // Create new
          const response = await vocabularyAPI.create(payload)
          const transformedWord = this._transformWord(response.data)
          this.words.unshift(transformedWord)
          return transformedWord
        }
      } catch (error) {
        this.error = error.response?.data || 'Failed to save word'
        console.error('Failed to save word:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async deleteWord(id) {
      this.loading = true
      this.error = null
      try {
        await vocabularyAPI.delete(id)
        this.words = this.words.filter(w => w.id !== id)
      } catch (error) {
        this.error = error.response?.data || 'Failed to delete word'
        console.error('Failed to delete word:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async updateMastery(id, level) {
      this.loading = true
      this.error = null
      try {
        const response = await vocabularyAPI.updateMastery(id, level)
        const transformedWord = this._transformWord(response.data)
        const index = this.words.findIndex(w => w.id === id)
        if (index !== -1) {
          this.words[index] = transformedWord
        }
        return transformedWord
      } catch (error) {
        this.error = error.response?.data || 'Failed to update mastery'
        console.error('Failed to update mastery:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    async toggleFavorite(id) {
      this.loading = true
      this.error = null
      try {
        const response = await vocabularyAPI.toggleFavorite(id)
        const transformedWord = this._transformWord(response.data)
        const index = this.words.findIndex(w => w.id === id)
        if (index !== -1) {
          this.words[index] = transformedWord
        }
        return transformedWord
      } catch (error) {
        this.error = error.response?.data || 'Failed to toggle favorite'
        console.error('Failed to toggle favorite:', error)
        throw error
      } finally {
        this.loading = false
      }
    }
  }
})
