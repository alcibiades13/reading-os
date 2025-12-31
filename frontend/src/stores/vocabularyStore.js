import { defineStore } from 'pinia'

const STORAGE_KEY = 'reading_os_vocabulary'

const INITIAL_WORDS = [
  {
    id: 'v-1',
    word: 'Ethereal',
    bookTitle: 'The Midnight Library',
    bookAuthor: 'Matt Haig',
    context: 'The library felt ethereal, as if it were made of starlight and old paper.',
    pageNumber: 12,
    definition: 'Extremely delicate and light in a way that seems too perfect for this world.',
    mastery: 'learning',
    tags: ['poetic', 'beautiful'],
    isFavorite: true,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 5
  },
  {
    id: 'v-2',
    word: 'Mellifluous',
    bookTitle: 'Atomic Habits',
    bookAuthor: 'James Clear',
    context: 'A mellifluous voice can often persuade even the most stubborn of minds.',
    pageNumber: 85,
    definition: 'Sweet or musical; pleasant to hear.',
    mastery: 'new',
    tags: ['phonaesthetics'],
    isFavorite: false,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 1
  },
  {
    id: 'v-3',
    word: 'Ephemeral',
    bookTitle: 'Meditations',
    bookAuthor: 'Marcus Aurelius',
    context: 'All things are ephemeral—both the one who remembers and the one remembered.',
    pageNumber: 42,
    definition: 'Lasting for a very short time.',
    mastery: 'mastered',
    tags: ['philosophy', 'time'],
    isFavorite: true,
    isPublic: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    reviewCount: 12
  }
]

export const useVocabularyStore = defineStore('vocabulary', {
  state: () => ({
    words: [],
    tags: [],
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
        const book = w.bookTitle || 'Manual Entry'
        byBook[book] = (byBook[book] || 0) + 1
      })
      return byBook
    },

    stats: (state) => {
      return {
        total: state.words.length,
        new: state.words.filter(w => w.mastery === 'new').length,
        learning: state.words.filter(w => w.mastery === 'learning').length,
        mastered: state.words.filter(w => w.mastery === 'mastered').length,
        favorites: state.words.filter(w => w.isFavorite).length
      }
    },

    practiceWords: (state) => {
      return state.words
        .filter(w => w.mastery !== 'mastered')
        .sort((a, b) => b.reviewCount - a.reviewCount)
    },

    searchWords: (state) => (query) => {
      if (!query) return state.words
      const q = query.toLowerCase()
      return state.words.filter(w =>
        w.word.toLowerCase().includes(q) ||
        w.context?.toLowerCase().includes(q) ||
        w.bookTitle?.toLowerCase().includes(q) ||
        w.definition?.toLowerCase().includes(q)
      )
    }
  },

  actions: {
    loadWords() {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (!stored) {
        this.words = INITIAL_WORDS
        localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_WORDS))
      } else {
        this.words = JSON.parse(stored)
      }
    },

    saveWord(wordData) {
      const now = new Date().toISOString()

      if (wordData.id) {
        // Update existing
        const index = this.words.findIndex(w => w.id === wordData.id)
        if (index !== -1) {
          const updated = { ...this.words[index], ...wordData, updatedAt: now }
          this.words[index] = updated
          localStorage.setItem(STORAGE_KEY, JSON.stringify(this.words))
          return updated
        }
      }

      // Create new
      const newWord = {
        ...wordData,
        id: 'word-' + Math.random().toString(36).substr(2, 9),
        mastery: wordData.mastery || 'new',
        tags: wordData.tags || [],
        isFavorite: wordData.isFavorite || false,
        isPublic: wordData.isPublic !== undefined ? wordData.isPublic : true,
        createdAt: now,
        updatedAt: now,
        reviewCount: 0
      }

      this.words.unshift(newWord)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.words))
      return newWord
    },

    deleteWord(id) {
      this.words = this.words.filter(w => w.id !== id)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.words))
    },

    updateMastery(id, level) {
      const index = this.words.findIndex(w => w.id === id)
      if (index !== -1) {
        this.words[index].mastery = level
        this.words[index].reviewCount += 1
        this.words[index].lastReviewedAt = new Date().toISOString()
        this.words[index].updatedAt = new Date().toISOString()
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.words))
        return this.words[index]
      }
      return null
    },

    toggleFavorite(id) {
      const index = this.words.findIndex(w => w.id === id)
      if (index !== -1) {
        this.words[index].isFavorite = !this.words[index].isFavorite
        this.words[index].updatedAt = new Date().toISOString()
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.words))
        return this.words[index]
      }
      return null
    }
  }
})
