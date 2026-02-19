import axios from 'axios'

// Base URL za Django backend
// U development: koristi Vite proxy (/api)
// U production: koristi environment varijablu (VITE_API_URL)
const API_URL = import.meta.env.VITE_API_URL || '/api'

// Kreiraj axios instancu
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - dodaje JWT token u svaki request
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // If data is FormData, remove Content-Type header (browser will set it with boundary)
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handleuje token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Ako je 401 i nismo već pokušali refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/token/refresh/`, {
            refresh: refreshToken,
          })

          const { access } = response.data
          localStorage.setItem('access_token', access)

          // Pokušaj ponovo sa novim tokenom
          originalRequest.headers.Authorization = `Bearer ${access}`
          return api(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed - logout user
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api

// API endpoints
export const authAPI = {
  login: (credentials) => api.post('/users/login/', credentials),
  register: (data) => api.post('/users/', data),
  getMe: () => api.get('/users/me/'),
  updateProfile: (data) => api.patch('/users/update_profile/', data),
}

export const booksAPI = {
  list: (params) => api.get('/books/', { params }),
  get: (id) => api.get(`/books/${id}/`),
  create: (data) => api.post('/books/', data),
  importBook: (data) => api.post('/books/import_book/', data),
  importGoodreadsCSV: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/books/import_goodreads_csv/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },
  update: (id, data) => api.put(`/books/${id}/`, data),
  delete: (id) => api.delete(`/books/${id}/`),
  popular: () => api.get('/books/popular/'),
  recent: () => api.get('/books/recent/'),
  trending: () => api.get('/books/trending/'),
  featured: () => api.get('/books/featured/'),
  switchEdition: (oldBookId, newBookId) =>
    api.post(`/books/${oldBookId}/switch_edition/`, { new_book_id: newBookId }),
  linkEdition: (book1Id, book2Id) =>
    api.post(`/books/${book1Id}/link_edition/`, { book_id: book2Id }),
  potentialEditions: (bookId) =>
    api.get(`/books/${bookId}/potential_editions/`),
  // Community activity
  communityActivity: (bookId) =>
    api.get(`/books/${bookId}/community_activity/`),
  userReview: (bookId, userId) =>
    api.get(`/books/${bookId}/review/${userId}/`),
}

export const authorsAPI = {
  list: (params) => api.get('/books/authors/', { params }),
  get: (id) => api.get(`/books/authors/${id}/`),
  books: (id) => api.get(`/books/authors/${id}/books/`),
}

export const genresAPI = {
  list: (params) => api.get('/books/genres/', { params }),
}

export const userBooksAPI = {
  list: (params) => api.get('/reading/user-books/', { params }),
  get: (id) => api.get(`/reading/user-books/${id}/`),
  create: (data) => api.post('/reading/user-books/', data),
  update: (id, data) => api.put(`/reading/user-books/${id}/`, data),
  delete: (id) => api.delete(`/reading/user-books/${id}/`),
  updateProgress: (id, currentPage) =>
    api.post(`/reading/user-books/${id}/update_progress/`, { current_page: currentPage }),
  markFinished: (id, data) =>
    api.post(`/reading/user-books/${id}/mark_finished/`, data),
  bookKnowledge: (bookId) =>
    api.get('/reading/user-books/book_knowledge/', { params: { book: bookId } }),
}

export const quotesAPI = {
  list: (params) => api.get('/reading/quotes/', { params }),
  get: (id) => api.get(`/reading/quotes/${id}/`),
  create: (data) => api.post('/reading/quotes/', data),
  update: (id, data) => api.put(`/reading/quotes/${id}/`, data),
  patch: (id, data) => api.patch(`/reading/quotes/${id}/`, data),
  delete: (id) => api.delete(`/reading/quotes/${id}/`),
  myFavorites: () => api.get('/reading/quotes/my_favorites/'),
  searchSemantic: (query) => api.get('/reading/quotes/search_semantic/', { params: { q: query } }),
  export: (format = 'json') => api.get('/reading/quotes/export/', { params: { format }, responseType: 'blob' }),
}

export const quoteTagsAPI = {
  list: () => api.get('/reading/quote-tags/'),
  create: (data) => api.post('/reading/quote-tags/', data),
  update: (id, data) => api.put(`/reading/quote-tags/${id}/`, data),
  delete: (id) => api.delete(`/reading/quote-tags/${id}/`),
}

export const studyNotesAPI = {
  list: (params) => api.get('/reading/study-notes/', { params }),
  get: (id) => api.get(`/reading/study-notes/${id}/`),
  create: (data) => api.post('/reading/study-notes/', data),
  update: (id, data) => api.patch(`/reading/study-notes/${id}/`, data),
  delete: (id) => api.delete(`/reading/study-notes/${id}/`),
  references: (bookId) => api.get('/reading/study-notes/references/', { params: { book: bookId } }),
  promoteToQuote: (id) => api.post(`/reading/study-notes/${id}/promote_to_quote/`),
  booksWithNotes: () => api.get('/reading/study-notes/books_with_notes/'),
  export: (params) => api.get('/reading/study-notes/export/', { params, responseType: 'blob' }),
}

export const listsAPI = {
  list: (params) => api.get('/lists/', { params }),
  get: (id) => api.get(`/lists/${id}/`),
  create: (data) => api.post('/lists/', data),
  update: (id, data) => api.put(`/lists/${id}/`, data),
  delete: (id) => api.delete(`/lists/${id}/`),
  addBook: (id, bookId, note) => 
    api.post(`/lists/${id}/add_book/`, { book_id: bookId, note }),
  removeBook: (id, bookId) => 
    api.delete(`/lists/${id}/remove_book/`, { data: { book_id: bookId } }),
}

export const challengesAPI = {
  list: (params) => api.get('/challenges/', { params }),
  get: (id) => api.get(`/challenges/${id}/`),
  create: (data) => api.post('/challenges/', data),
  update: (id, data) => api.put(`/challenges/${id}/`, data),
  delete: (id) => api.delete(`/challenges/${id}/`),
  current: () => api.get('/challenges/current/'),
  updateProgress: (id) => api.post(`/challenges/${id}/update_progress/`),
}

export const socialAPI = {
  // Friendships
  friendships: () => api.get('/social/friendships/'),
  myFriends: () => api.get('/social/friendships/my_friends/'),
  pendingRequests: () => api.get('/social/friendships/pending/'),
  sendFriendRequest: (userId) => api.post('/social/friendships/', { to_user: userId }),
  acceptFriend: (id) => api.post(`/social/friendships/${id}/accept/`),
  declineFriend: (id) => api.post(`/social/friendships/${id}/decline/`),
  removeFriend: (id) => api.delete(`/social/friendships/${id}/`),

  // Circles
  circles: () => api.get('/social/circles/'),
  getCircle: (id) => api.get(`/social/circles/${id}/`),
  createCircle: (data) => api.post('/social/circles/', data),

  // Circle Posts
  circlePosts: (params) => api.get('/social/circle-posts/', { params }),
  createPost: (data) => api.post('/social/circle-posts/', data),

  // Feed
  feed: () => api.get('/social/feed/'),
  markFeedRead: (id) => api.post(`/social/feed/${id}/mark_read/`),

  // Review Comments & Likes
  reviewComments: (userBookId) => api.get('/social/review-comments/', { params: { user_book: userBookId } }),
  addReviewComment: (userBookId, content) => api.post('/social/review-comments/', { user_book_id: userBookId, content }),
  deleteReviewComment: (commentId) => api.delete(`/social/review-comments/${commentId}/`),
  toggleReviewLike: (userBookId) => api.post('/social/review-likes/toggle/', { user_book_id: userBookId }),
  reviewLikeStatus: (userBookId) => api.get('/social/review-likes/toggle/', { params: { user_book_id: userBookId } }),

  // User Discovery & Profiles
  suggestedUsers: (params) => api.get('/social/suggested-users/', { params }),
  searchUsers: (query) => api.get('/users/search/', { params: { q: query } }),
  getUserProfile: (userId) => api.get(`/users/${userId}/profile/`),
  getUserBooks: (userId, params) => api.get(`/users/${userId}/books/`, { params }),
  getUserStats: (userId) => api.get(`/users/${userId}/stats/`),
}

export const vocabularyAPI = {
  list: (params) => api.get('/reading/vocabulary/', { params }),
  get: (id) => api.get(`/reading/vocabulary/${id}/`),
  create: (data) => api.post('/reading/vocabulary/', data),
  update: (id, data) => api.put(`/reading/vocabulary/${id}/`, data),
  delete: (id) => api.delete(`/reading/vocabulary/${id}/`),
  updateMastery: (id, mastery) => api.post(`/reading/vocabulary/${id}/update_mastery/`, { mastery }),
  toggleFavorite: (id) => api.post(`/reading/vocabulary/${id}/toggle_favorite/`),
  export: (format = 'json') => api.get('/reading/vocabulary/export/', { params: { format }, responseType: 'blob' }),
}

export const usersAPI = {
  exportAllData: () => api.get('/users/export_all_data/', { responseType: 'blob' }),
  getConsistency: () => api.get('/users/consistency/'),
}

export const recommendationsAPI = {
  // Main recommendations
  getRecommendations: (params) => api.get('/recommendations/', { params }),
  getContextual: (context, limit = 10) =>
    api.get('/recommendations/contextual/', { params: { context, limit } }),
  getSimilar: (bookId, limit = 6) =>
    api.get(`/recommendations/similar/${bookId}/`, { params: { limit } }),

  // Survey
  submitSurvey: (data) => api.post('/recommendations/survey/', data),
  checkSurvey: (bookId) => api.get(`/recommendations/survey/check/${bookId}/`),
  getSurveyConfig: () => api.get('/recommendations/survey/config/'),

  // User profile
  getTasteProfile: () => api.get('/recommendations/taste-profile/'),

  // Book DNA
  getBookDNA: (bookId) => api.get(`/recommendations/book-dna/${bookId}/`),
}

export const conversationsAPI = {
  // Conversations
  list: () => api.get('/social/conversations/'),
  get: (id) => api.get(`/social/conversations/${id}/`),
  start: (recipientId) => api.post('/social/conversations/start/', { recipient_id: recipientId }),
  markRead: (id) => api.post(`/social/conversations/${id}/mark_read/`),

  // Messages
  listMessages: (params) => api.get('/social/messages/', { params }),
  sendMessage: (data) => api.post('/social/messages/', data),
  getMessage: (id) => api.get(`/social/messages/${id}/`),
}