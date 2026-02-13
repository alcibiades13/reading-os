import { recommendationsAPI } from './api'

/**
 * Context labels and icons for contextual recommendations
 */
export const CONTEXT_CONFIG = {
  peaceful: {
    id: 'peaceful',
    label: 'For Peaceful Days',
    description: 'Light, bright, optimistic books',
    icon: 'leaf',
    color: 'emerald',
  },
  challenge: {
    id: 'challenge',
    label: 'Challenge Yourself',
    description: 'Complex, demanding books',
    icon: 'brain',
    color: 'purple',
  },
  emotional: {
    id: 'emotional',
    label: 'Emotional Journey',
    description: 'Intense, touching books',
    icon: 'heart',
    color: 'rose',
  },
  quick: {
    id: 'quick',
    label: 'Quick Reads',
    description: 'Fast-paced, dynamic books',
    icon: 'zap',
    color: 'amber',
  },
  light: {
    id: 'light',
    label: 'Something Light',
    description: 'Simple, relaxing books',
    icon: 'sun',
    color: 'yellow',
  },
  deep: {
    id: 'deep',
    label: 'Deep Thinking',
    description: 'Philosophical, introspective books',
    icon: 'sparkles',
    color: 'indigo',
  },
}

/**
 * Recommendations service with helper functions
 */
export const recommendationsService = {
  /**
   * Get personalized book recommendations
   */
  async getForYouBooks(limit = 20) {
    try {
      const response = await recommendationsAPI.getRecommendations({ limit })
      return response.data
    } catch (error) {
      console.error('Error fetching recommendations:', error)
      return []
    }
  },

  /**
   * Get contextual recommendations
   */
  async getContextualBooks(context, limit = 10) {
    try {
      const response = await recommendationsAPI.getContextual(context, limit)
      return {
        ...CONTEXT_CONFIG[context],
        books: response.data.books || [],
      }
    } catch (error) {
      console.error('Error fetching contextual recommendations:', error)
      return {
        ...CONTEXT_CONFIG[context],
        books: [],
      }
    }
  },

  /**
   * Get similar books to a given book
   */
  async getSimilarBooks(bookId, limit = 6) {
    try {
      const response = await recommendationsAPI.getSimilar(bookId, limit)
      return response.data
    } catch (error) {
      console.error('Error fetching similar books:', error)
      return []
    }
  },

  /**
   * Check if user has voted for a book
   */
  async hasVotedForBook(bookId) {
    try {
      const response = await recommendationsAPI.checkSurvey(bookId)
      console.log('[API] checkSurvey response for book', bookId, ':', response.data)
      return response.data.has_voted
    } catch (error) {
      console.error('[API] checkSurvey error:', error.response?.status, error.message)
      return false
    }
  },

  /**
   * Get existing vote for a book
   */
  async getVoteForBook(bookId) {
    try {
      const response = await recommendationsAPI.checkSurvey(bookId)
      return response.data.vote
    } catch (error) {
      console.error('Error getting vote:', error)
      return null
    }
  },

  /**
   * Submit book DNA survey
   */
  async submitSurvey(bookId, userBookId, responses, themes, primaryThemes = [], genreTags = [], primaryGenreTag = null) {
    try {
      const response = await recommendationsAPI.submitSurvey({
        book_id: bookId,
        user_book_id: userBookId,
        responses,
        themes,
        primary_themes: primaryThemes,
        genre_tags: genreTags,
        primary_genre_tag: primaryGenreTag,
      })
      return response.data
    } catch (error) {
      console.error('Error submitting survey:', error)
      throw error
    }
  },

  /**
   * Get survey configuration (questions and themes)
   */
  async getSurveyConfig() {
    try {
      const response = await recommendationsAPI.getSurveyConfig()
      return response.data
    } catch (error) {
      console.error('Error getting survey config:', error)
      // Return default config if API fails
      return {
        questions: [
          { id: 'pace', question: 'What was the pacing like?', left_label: 'Slow', right_label: 'Fast' },
          { id: 'emotional_intensity', question: 'Emotional intensity?', left_label: 'Light', right_label: 'Intense' },
          { id: 'complexity', question: 'How complex was it?', left_label: 'Simple', right_label: 'Complex' },
          { id: 'character_focus', question: 'Story focus?', left_label: 'Plot', right_label: 'Characters' },
          { id: 'darkness', question: 'Overall tone?', left_label: 'Light', right_label: 'Dark' },
          { id: 'introspection', question: 'What drives the narrative?', left_label: 'Action', right_label: 'Reflection' },
        ],
        theme_options: [],
        theme_categories: [],
        genre_tag_options: [],
        theme_popularity: {},
      }
    }
  },

  /**
   * Get user's taste profile
   */
  async getTasteProfile() {
    try {
      const response = await recommendationsAPI.getTasteProfile()
      return response.data
    } catch (error) {
      console.error('Error getting taste profile:', error)
      return null
    }
  },

  /**
   * Get book's DNA
   */
  async getBookDNA(bookId) {
    try {
      const response = await recommendationsAPI.getBookDNA(bookId)
      return response.data
    } catch (error) {
      console.error('Error getting book DNA:', error)
      return null
    }
  },
}

export default recommendationsService
