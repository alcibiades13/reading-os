import api from './api'

/**
 * Book Club / Circles Service
 * Handles all book club related API calls including circles, topics, and discussions
 */
export const bookClubService = {
  // ===== CIRCLES (Book Clubs) =====

  /**
   * Get all circles the user is a member of
   */
  async getCircles() {
    const response = await api.get('/social/circles/')
    return response.data
  },

  /**
   * Get a single circle by ID with full details
   */
  async getCircle(id) {
    const response = await api.get(`/social/circles/${id}/`)
    return response.data
  },

  /**
   * Create a new circle/book club
   */
  async createCircle(data) {
    const response = await api.post('/social/circles/', data)
    return response.data
  },

  /**
   * Update a circle
   */
  async updateCircle(id, data) {
    const response = await api.patch(`/social/circles/${id}/`, data)
    return response.data
  },

  /**
   * Delete a circle
   */
  async deleteCircle(id) {
    await api.delete(`/social/circles/${id}/`)
  },

  /**
   * Leave a circle
   */
  async leaveCircle(id) {
    const response = await api.post(`/social/circles/${id}/leave/`)
    return response.data
  },

  /**
   * Promote a member to admin
   */
  async promoteMember(circleId, userId) {
    const response = await api.post(`/social/circles/${circleId}/promote_member/`, {
      user_id: userId
    })
    return response.data
  },

  // ===== CIRCLE INVITATIONS =====

  /**
   * Get pending invitations for the current user
   */
  async getInvitations() {
    const response = await api.get('/social/circle-invitations/')
    return response.data
  },

  /**
   * Send an invitation to join a circle
   */
  async sendInvitation(circleId, userId, message = '') {
    const response = await api.post('/social/circle-invitations/', {
      circle: circleId,
      to_user: userId,
      message
    })
    return response.data
  },

  /**
   * Accept a circle invitation
   */
  async acceptInvitation(id) {
    const response = await api.post(`/social/circle-invitations/${id}/accept/`)
    return response.data
  },

  /**
   * Decline a circle invitation
   */
  async declineInvitation(id) {
    const response = await api.post(`/social/circle-invitations/${id}/decline/`)
    return response.data
  },

  // ===== DISCUSSION TOPICS =====

  /**
   * Get topics for a circle
   */
  async getTopics(circleId, options = {}) {
    const params = new URLSearchParams()
    if (circleId) params.append('circle', circleId)
    if (options.category) params.append('category', options.category)

    const response = await api.get(`/social/topics/?${params.toString()}`)
    return response.data
  },

  /**
   * Get a single topic with messages
   */
  async getTopic(id) {
    const response = await api.get(`/social/topics/${id}/`)
    return response.data
  },

  /**
   * Create a new discussion topic
   */
  async createTopic(data) {
    const response = await api.post('/social/topics/', data)
    return response.data
  },

  /**
   * Update a topic
   */
  async updateTopic(id, data) {
    const response = await api.patch(`/social/topics/${id}/`, data)
    return response.data
  },

  /**
   * Delete a topic
   */
  async deleteTopic(id) {
    await api.delete(`/social/topics/${id}/`)
  },

  // ===== TOPIC MESSAGES =====

  /**
   * Get messages for a topic, optionally filtered by timestamp
   */
  async getTopicMessages(topicId, options = {}) {
    const params = new URLSearchParams()
    params.append('topic', topicId)
    if (options.after) params.append('after', options.after)

    const response = await api.get(`/social/topic-messages/?${params.toString()}`)
    return response.data
  },

  /**
   * Send a message to a topic
   */
  async sendTopicMessage(data) {
    const response = await api.post('/social/topic-messages/', data)
    return response.data
  },

  /**
   * Toggle like on a topic message
   */
  async toggleMessageLike(messageId) {
    const response = await api.post(`/social/topic-messages/${messageId}/toggle_like/`)
    return response.data
  },

  /**
   * Delete a topic message
   */
  async deleteTopicMessage(id) {
    await api.delete(`/social/topic-messages/${id}/`)
  },

  // ===== BOOK CLUB READINGS =====

  /**
   * Get reading history/schedule for a circle
   */
  async getClubReadings(circleId, status = null) {
    const params = new URLSearchParams()
    if (circleId) params.append('circle', circleId)
    if (status) params.append('status', status)

    const response = await api.get(`/social/club-readings/?${params.toString()}`)
    return response.data
  },

  /**
   * Add a book to club reading list
   */
  async addClubReading(data) {
    const response = await api.post('/social/club-readings/', data)
    return response.data
  },

  /**
   * Update a club reading
   */
  async updateClubReading(id, data) {
    const response = await api.patch(`/social/club-readings/${id}/`, data)
    return response.data
  },

  /**
   * Set a book as the current reading for the club
   */
  async setCurrentReading(id) {
    const response = await api.post(`/social/club-readings/${id}/set_as_current/`)
    return response.data
  },

  /**
   * Delete a club reading
   */
  async deleteClubReading(id) {
    await api.delete(`/social/club-readings/${id}/`)
  },

  // ===== MEMBER PROGRESS =====

  /**
   * Get member progress on circle's current book
   */
  async getMemberProgress(circleId) {
    const response = await api.get(`/social/circles/${circleId}/member_progress/`)
    return response.data
  },

  // ===== UNREAD TRACKING =====

  /**
   * Get unread counts for topics in a circle
   */
  async getUnreadCounts(circleId) {
    const response = await api.get(`/social/circles/${circleId}/unread_counts/`)
    return response.data
  },

  /**
   * Mark a topic as read
   */
  async markTopicRead(topicId) {
    const response = await api.post(`/social/topics/${topicId}/mark_read/`)
    return response.data
  },

  // ===== TOPIC ACTIONS =====

  /**
   * Toggle pin on a topic (admin only)
   */
  async togglePinTopic(topicId) {
    const response = await api.post(`/social/topics/${topicId}/toggle_pin/`)
    return response.data
  },

  // ===== MESSAGE SEARCH =====

  /**
   * Search messages within a circle
   */
  async searchMessages(circleId, query) {
    const response = await api.get(`/social/topic-messages/search/?circle=${circleId}&q=${encodeURIComponent(query)}`)
    return response.data
  },

  // ===== REACTIONS =====

  /**
   * Toggle a reaction on a message
   */
  async toggleReaction(messageId, emoji) {
    const response = await api.post(`/social/topic-messages/${messageId}/toggle_reaction/`, { emoji })
    return response.data
  },

  // ===== POLLS =====

  /**
   * Create a poll
   */
  async createPoll(data) {
    const response = await api.post('/social/polls/', data)
    return response.data
  },

  /**
   * Vote on a poll
   */
  async votePoll(pollId, optionId) {
    const response = await api.post(`/social/polls/${pollId}/vote/`, { option_id: optionId })
    return response.data
  },

  /**
   * Close a poll (admin only)
   */
  async closePoll(pollId) {
    const response = await api.post(`/social/polls/${pollId}/close/`)
    return response.data
  },

  // ===== HELPERS =====

  /**
   * Get category display info
   */
  getCategoryInfo(category) {
    const categories = {
      general: { label: 'General', color: 'bg-indigo-500/20 text-indigo-400' },
      spoilers: { label: 'Spoilers', color: 'bg-rose-500/20 text-rose-400' },
      theories: { label: 'Theories', color: 'bg-amber-500/20 text-amber-400' },
      characters: { label: 'Characters', color: 'bg-emerald-500/20 text-emerald-400' },
      themes: { label: 'Themes', color: 'bg-purple-500/20 text-purple-400' },
      quotes: { label: 'Quotes', color: 'bg-cyan-500/20 text-cyan-400' },
    }
    return categories[category] || categories.general
  },

  /**
   * Format time ago string
   */
  formatTimeAgo(dateString) {
    if (!dateString) return 'Never'

    const date = new Date(dateString)
    const now = new Date()
    const seconds = Math.floor((now - date) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
    return `${Math.floor(seconds / 604800)}w ago`
  },

  // ===== CIRCLE DISCOVERY =====

  async discoverCircles() {
    const response = await api.get('/social/circles/discover/')
    return response.data
  },

  async joinCircle(circleId) {
    const response = await api.post(`/social/circles/${circleId}/join/`)
    return response.data
  },

  // ===== CIRCLE EVENTS =====

  async getCircleEvents(circleId) {
    const response = await api.get(`/social/circles/${circleId}/events/`)
    return response.data
  },

  async createCircleEvent(circleId, data) {
    const response = await api.post(`/social/circles/${circleId}/events/`, data)
    return response.data
  },
}

export default bookClubService
