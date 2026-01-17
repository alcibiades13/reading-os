// Social Service - Follow, Suggestions, Discovery
import api, { socialAPI } from './api'

// Mock data for development
const MOCK_USERS = [
  {
    id: 2,
    username: 'elena_rodriguez',
    first_name: 'Elena',
    last_name: 'Rodriguez',
    email: 'elena@example.com',
    avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
    bio: 'Philosophy enthusiast. Stoic practitioner. Always learning.',
    following_count: 45,
    followers_count: 128,
    books_read_count: 87,
    quotes_count: 342,
    top_genres: ['Philosophy', 'Stoicism', 'Biography'],
    is_following: false,
    is_follower: false,
    match_score: 87,
    shared_books_count: 12
  },
  {
    id: 3,
    username: 'marcus_chen',
    first_name: 'Marcus',
    last_name: 'Chen',
    email: 'marcus@example.com',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
    bio: 'Sci-Fi lover. Code by day, read by night.',
    following_count: 32,
    followers_count: 89,
    books_read_count: 62,
    quotes_count: 189,
    top_genres: ['Sci-Fi', 'Philosophy', 'Technology'],
    is_following: true,
    is_follower: true,
    match_score: 82,
    shared_books_count: 9
  },
  {
    id: 4,
    username: 'sofia_martinez',
    first_name: 'Sofia',
    last_name: 'Martinez',
    email: 'sofia@example.com',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop',
    bio: 'Literature professor. Classic novels aficionado.',
    following_count: 67,
    followers_count: 234,
    books_read_count: 143,
    quotes_count: 891,
    top_genres: ['Classic Literature', 'Philosophy', 'Poetry'],
    is_following: false,
    is_follower: false,
    match_score: 79,
    shared_books_count: 15
  },
  {
    id: 5,
    username: 'alex_kim',
    first_name: 'Alex',
    last_name: 'Kim',
    email: 'alex@example.com',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop',
    bio: 'Psychology meets philosophy. Understanding the human mind.',
    following_count: 28,
    followers_count: 56,
    books_read_count: 45,
    quotes_count: 234,
    top_genres: ['Psychology', 'Philosophy', 'Neuroscience'],
    is_following: false,
    is_follower: false,
    match_score: 76,
    shared_books_count: 7
  },
  {
    id: 6,
    username: 'isabella_wright',
    first_name: 'Isabella',
    last_name: 'Wright',
    email: 'isabella@example.com',
    avatar: 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=100&h=100&fit=crop',
    bio: 'Historical fiction and biographies. Learning from the past.',
    following_count: 52,
    followers_count: 98,
    books_read_count: 78,
    quotes_count: 445,
    top_genres: ['Historical Fiction', 'Biography', 'History'],
    is_following: false,
    is_follower: true,
    match_score: 71,
    shared_books_count: 11
  }
]

export const socialService = {
  /**
   * Follow a user (send friend request)
   */
  async followUser(userId) {
    try {
      const response = await socialAPI.sendFriendRequest(userId)
      return { success: true, is_following: true, data: response.data }
    } catch (error) {
      console.error('Error following user:', error)
      // Fallback to mock for development
      if (error.response?.status === 404) {
        await new Promise(resolve => setTimeout(resolve, 500))
        return { success: true, is_following: true }
      }
      throw error
    }
  },

  /**
   * Unfollow a user (remove friend)
   */
  async unfollowUser(friendshipId) {
    try {
      await socialAPI.removeFriend(friendshipId)
      return { success: true, is_following: false }
    } catch (error) {
      console.error('Error unfollowing user:', error)
      // Fallback to mock for development
      if (error.response?.status === 404) {
        await new Promise(resolve => setTimeout(resolve, 500))
        return { success: true, is_following: false }
      }
      throw error
    }
  },

  /**
   * Get suggested users based on reading similarity
   */
  async getSuggestedUsers(limit = 10) {
    try {
      const response = await socialAPI.suggestedUsers({ limit })
      return response.data
    } catch (error) {
      console.error('Error getting suggested users:', error)
      // Fallback to mock data if backend not ready
      if (error.response?.status === 404) {
        const suggestions = MOCK_USERS
          .filter(user => !user.is_following)
          .sort((a, b) => b.match_score - a.match_score)
          .slice(0, limit)
        return suggestions
      }
      return []
    }
  },

  /**
   * Get users with similar reading taste (Kindred Spirits)
   */
  async getKindredSpirits(limit = 5) {
    try {
      // TODO: Replace with actual API call implementing the full algorithm
      // const response = await api.get('/api/social/kindred-spirits/', { params: { limit } })
      // return response.data

      // Mock implementation
      return this.getSuggestedUsers(limit)
    } catch (error) {
      console.error('Error getting kindred spirits:', error)
      return []
    }
  },

  /**
   * Get user's followers
   */
  async getUserFollowers(userId) {
    try {
      const response = await api.get(`/users/${userId}/followers/`)
      return response.data
    } catch (error) {
      console.error('Error getting followers:', error)
      return []
    }
  },

  /**
   * Get user's following
   */
  async getUserFollowing(userId) {
    try {
      const response = await api.get(`/users/${userId}/following/`)
      return response.data
    } catch (error) {
      console.error('Error getting following:', error)
      return []
    }
  },

  /**
   * Get users reading a specific book
   */
  async getBookReaders(bookId, limit = 10) {
    try {
      // TODO: Replace with actual API call
      // const response = await api.get(`/api/books/${bookId}/readers/`, { params: { limit } })
      // return response.data

      // Mock implementation
      return MOCK_USERS.slice(0, limit)
    } catch (error) {
      console.error('Error getting book readers:', error)
      return []
    }
  },

  /**
   * Search users
   */
  async searchUsers(query) {
    try {
      const response = await socialAPI.searchUsers(query)
      return response.data
    } catch (error) {
      console.error('Error searching users:', error)
      // Fallback to mock data
      if (error.response?.status === 404) {
        const lowerQuery = query.toLowerCase()
        return MOCK_USERS.filter(user =>
          user.username.toLowerCase().includes(lowerQuery) ||
          user.first_name.toLowerCase().includes(lowerQuery) ||
          user.last_name.toLowerCase().includes(lowerQuery)
        )
      }
      return []
    }
  },

  /**
   * Get user profile by ID
   */
  async getUserProfile(userId) {
    try {
      const response = await socialAPI.getUserProfile(userId)
      return response.data
    } catch (error) {
      console.error('Error getting user profile:', error)
      // Fallback to mock data
      if (error.response?.status === 404) {
        return MOCK_USERS.find(u => u.id === parseInt(userId)) || null
      }
      throw error
    }
  },

  /**
   * Get user's books (paginated)
   */
  async getUserBooks(userId, params = {}) {
    try {
      // Default to first page with 20 items if not specified
      const queryParams = {
        page: 1,
        page_size: 20,
        ...params
      }
      const response = await socialAPI.getUserBooks(userId, queryParams)
      return response.data.results || response.data
    } catch (error) {
      console.error('Error getting user books:', error)
      return []
    }
  },

  /**
   * Get user stats
   */
  async getUserStats(userId) {
    try {
      const response = await socialAPI.getUserStats(userId)
      return response.data
    } catch (error) {
      console.error('Error getting user stats:', error)
      return null
    }
  },

  /**
   * Calculate match score between current user and another user
   * (Client-side approximation - real calculation should be on backend)
   */
  calculateMatchScore(currentUserBooks, otherUserBooks, currentUserGenres, otherUserGenres) {
    let score = 0

    // Book overlap (max 40 points)
    const sharedBooks = currentUserBooks.filter(book =>
      otherUserBooks.some(otherBook => otherBook.id === book.id)
    )
    score += Math.min(sharedBooks.length * 4, 40)

    // Genre overlap (max 30 points)
    const sharedGenres = currentUserGenres.filter(genre =>
      otherUserGenres.includes(genre)
    )
    score += Math.min(sharedGenres.length * 10, 30)

    // Normalize to 0-100
    return Math.min(score, 100)
  }
}
