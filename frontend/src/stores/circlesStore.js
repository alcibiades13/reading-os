import { defineStore } from 'pinia'
import { bookClubService } from '@/services/bookClubService'
import { useAuthStore } from '@/stores/authStore'

export const useCirclesStore = defineStore('circles', {
  state: () => ({
    circles: [],
    activeCircleId: null,
    activeTopicId: null,
    messages: [],
    pendingInvitations: [],
    clubReadings: [],
    memberProgress: [],
    unreadCounts: {},
    discoverCircles: [],
    circleEvents: [],
    loading: false,
    error: null,
    // Polling
    pollTimer: null,
    lastMessageTimestamp: null,
    // UI state
    activeTab: 'topics', // 'topics' | 'bookshelf'
    mobileView: 'topics', // 'topics' | 'chat'
  }),

  getters: {
    activeCircle(state) {
      return state.circles.find(c => c.id === state.activeCircleId) || null
    },

    activeTopic() {
      if (!this.activeCircle?.topics) return null
      return this.activeCircle.topics.find(t => t.id === this.activeTopicId) || null
    },

    isCircleAdmin() {
      const authStore = useAuthStore()
      if (!this.activeCircle) return false
      return (
        this.activeCircle.creator?.id === authStore.user?.id ||
        this.activeCircle.memberships?.some(
          m => m.user?.id === authStore.user?.id && m.role === 'admin'
        )
      )
    },

    currentReading(state) {
      return state.clubReadings.find(r => r.status === 'current') || null
    },

    upcomingReadings(state) {
      return state.clubReadings.filter(r => r.status === 'upcoming')
    },

    completedReadings(state) {
      return state.clubReadings.filter(r => r.status === 'completed')
    },

    totalUnreadCount(state) {
      return Object.values(state.unreadCounts).reduce((sum, count) => sum + count, 0)
    },

    circleUnreadCounts(state) {
      // Group unread counts by circle
      const counts = {}
      if (!state.circles.length) return counts
      for (const circle of state.circles) {
        const topics = circle.topics || []
        let total = 0
        for (const topic of topics) {
          total += (state.unreadCounts[topic.id] || 0)
        }
        if (total > 0) counts[circle.id] = total
      }
      return counts
    },
  },

  actions: {
    // ===== LOADING =====

    async fetchCircles() {
      this.loading = true
      this.error = null
      try {
        const data = await bookClubService.getCircles()
        this.circles = data.results || data || []
        if (this.circles.length > 0 && !this.activeCircleId) {
          this.activeCircleId = this.circles[0].id
        }
        return { success: true }
      } catch (error) {
        this.error = error.response?.data || 'Failed to fetch circles'
        console.error('Error loading circles:', error)
        return { success: false, error: this.error }
      } finally {
        this.loading = false
      }
    },

    async fetchCircleDetail(circleId) {
      try {
        const detail = await bookClubService.getCircle(circleId)
        const idx = this.circles.findIndex(c => c.id === circleId)
        if (idx !== -1) {
          this.circles[idx] = { ...this.circles[idx], ...detail }
        }
        return { success: true, data: detail }
      } catch (error) {
        console.error('Error loading circle detail:', error)
        return { success: false, error }
      }
    },

    async fetchPendingInvitations() {
      try {
        const data = await bookClubService.getInvitations()
        this.pendingInvitations = (data.results || data || []).filter(
          inv => inv.status === 'pending'
        )
        return { success: true }
      } catch (error) {
        console.error('Error loading invitations:', error)
        return { success: false, error }
      }
    },

    async fetchTopicMessages(topicId) {
      try {
        const data = await bookClubService.getTopicMessages(topicId)
        this.messages = data.results || data || []
        if (this.messages.length > 0) {
          this.lastMessageTimestamp = this.messages[this.messages.length - 1].created_at
        }
        return { success: true }
      } catch (error) {
        console.error('Error loading messages:', error)
        return { success: false, error }
      }
    },

    async fetchNewMessages(topicId) {
      if (!this.lastMessageTimestamp) return
      try {
        const data = await bookClubService.getTopicMessages(topicId, {
          after: this.lastMessageTimestamp
        })
        const newMessages = data.results || data || []
        if (newMessages.length > 0) {
          // Avoid duplicates
          const existingIds = new Set(this.messages.map(m => m.id))
          const unique = newMessages.filter(m => !existingIds.has(m.id))
          if (unique.length > 0) {
            this.messages.push(...unique)
            this.lastMessageTimestamp = unique[unique.length - 1].created_at
          }
        }
      } catch (error) {
        console.error('Error polling messages:', error)
      }
    },

    // ===== POLLING =====

    startPolling(topicId) {
      this.stopPolling()
      this.pollTimer = setInterval(() => {
        this.fetchNewMessages(topicId)
      }, 7000)
    },

    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
    },

    // ===== CIRCLE ACTIONS =====

    async createCircle(formData) {
      try {
        const newCircle = await bookClubService.createCircle(formData)
        this.circles.unshift(newCircle)
        this.setActiveCircle(newCircle.id)
        return { success: true, data: newCircle }
      } catch (error) {
        console.error('Error creating circle:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async updateCircle(circleId, data) {
      try {
        const updated = await bookClubService.updateCircle(circleId, data)
        const idx = this.circles.findIndex(c => c.id === updated.id)
        if (idx !== -1) {
          this.circles[idx] = { ...this.circles[idx], ...updated }
        }
        return { success: true, data: updated }
      } catch (error) {
        console.error('Error updating circle:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async deleteCircle(circleId) {
      try {
        await bookClubService.deleteCircle(circleId)
        this.circles = this.circles.filter(c => c.id !== circleId)
        this.activeCircleId = this.circles[0]?.id || null
        return { success: true }
      } catch (error) {
        console.error('Error deleting circle:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async leaveCircle(circleId) {
      try {
        await bookClubService.leaveCircle(circleId)
        this.circles = this.circles.filter(c => c.id !== circleId)
        this.activeCircleId = this.circles[0]?.id || null
        return { success: true }
      } catch (error) {
        console.error('Error leaving circle:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async promoteMember(circleId, userId) {
      try {
        await bookClubService.promoteMember(circleId, userId)
        await this.fetchCircleDetail(circleId)
        return { success: true }
      } catch (error) {
        console.error('Error promoting member:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== INVITATIONS =====

    async acceptInvitation(invitationId) {
      try {
        await bookClubService.acceptInvitation(invitationId)
        this.pendingInvitations = this.pendingInvitations.filter(
          inv => inv.id !== invitationId
        )
        await this.fetchCircles()
        return { success: true }
      } catch (error) {
        console.error('Error accepting invitation:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async declineInvitation(invitationId) {
      try {
        await bookClubService.declineInvitation(invitationId)
        this.pendingInvitations = this.pendingInvitations.filter(
          inv => inv.id !== invitationId
        )
        return { success: true }
      } catch (error) {
        console.error('Error declining invitation:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== TOPICS =====

    async createTopic(data) {
      try {
        const newTopic = await bookClubService.createTopic(data)
        await this.fetchCircleDetail(this.activeCircleId)
        this.activeTopicId = newTopic.id
        return { success: true, data: newTopic }
      } catch (error) {
        console.error('Error creating topic:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async deleteTopic(topicId) {
      try {
        await bookClubService.deleteTopic(topicId)
        if (this.activeTopicId === topicId) {
          this.activeTopicId = null
          this.messages = []
        }
        await this.fetchCircleDetail(this.activeCircleId)
        return { success: true }
      } catch (error) {
        console.error('Error deleting topic:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async togglePinTopic(topicId) {
      try {
        const result = await bookClubService.togglePinTopic(topicId)
        await this.fetchCircleDetail(this.activeCircleId)
        return { success: true, data: result }
      } catch (error) {
        console.error('Error pinning topic:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== MESSAGES =====

    async sendMessage(data) {
      const authStore = useAuthStore()
      try {
        const newMessage = await bookClubService.sendTopicMessage(data)
        // Ensure author data is present
        if (!newMessage.author || !newMessage.author.first_name) {
          newMessage.author = {
            id: authStore.user?.id,
            first_name: authStore.user?.first_name,
            last_name: authStore.user?.last_name,
            email: authStore.user?.email,
            avatar: authStore.user?.avatar,
          }
        }
        this.messages.push(newMessage)
        this.lastMessageTimestamp = newMessage.created_at
        return { success: true, data: newMessage }
      } catch (error) {
        console.error('Error sending message:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async toggleMessageLike(messageId) {
      try {
        const result = await bookClubService.toggleMessageLike(messageId)
        const msg = this.messages.find(m => m.id === messageId)
        if (msg) {
          msg.is_liked = result.liked
          msg.likes_count = result.likes_count
        }
        return { success: true, data: result }
      } catch (error) {
        console.error('Error toggling like:', error)
        return { success: false, error }
      }
    },

    async deleteMessage(messageId) {
      try {
        await bookClubService.deleteTopicMessage(messageId)
        this.messages = this.messages.filter(m => m.id !== messageId)
        return { success: true }
      } catch (error) {
        console.error('Error deleting message:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== BOOK CLUB READINGS =====

    async fetchClubReadings(circleId) {
      try {
        const data = await bookClubService.getClubReadings(circleId)
        this.clubReadings = data.results || data || []
        return { success: true }
      } catch (error) {
        console.error('Error loading club readings:', error)
        return { success: false, error }
      }
    },

    async addClubReading(data) {
      try {
        const reading = await bookClubService.addClubReading(data)
        this.clubReadings.unshift(reading)
        return { success: true, data: reading }
      } catch (error) {
        console.error('Error adding club reading:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async setCurrentReading(readingId) {
      try {
        const result = await bookClubService.setCurrentReading(readingId)
        // Refresh readings and circle detail
        await Promise.all([
          this.fetchClubReadings(this.activeCircleId),
          this.fetchCircleDetail(this.activeCircleId),
        ])
        return { success: true, data: result }
      } catch (error) {
        console.error('Error setting current reading:', error)
        return { success: false, error: error.response?.data }
      }
    },

    async deleteClubReading(readingId) {
      try {
        await bookClubService.deleteClubReading(readingId)
        this.clubReadings = this.clubReadings.filter(r => r.id !== readingId)
        return { success: true }
      } catch (error) {
        console.error('Error deleting club reading:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== MEMBER PROGRESS =====

    async fetchMemberProgress(circleId) {
      try {
        const data = await bookClubService.getMemberProgress(circleId)
        this.memberProgress = data || []
        return { success: true }
      } catch (error) {
        console.error('Error loading member progress:', error)
        return { success: false, error }
      }
    },

    // ===== UNREAD TRACKING =====

    async fetchUnreadCounts(circleId) {
      try {
        const data = await bookClubService.getUnreadCounts(circleId)
        this.unreadCounts = { ...this.unreadCounts, ...data }
        return { success: true }
      } catch (error) {
        console.error('Error loading unread counts:', error)
        return { success: false, error }
      }
    },

    async markTopicRead(topicId) {
      try {
        await bookClubService.markTopicRead(topicId)
        delete this.unreadCounts[topicId]
        return { success: true }
      } catch (error) {
        console.error('Error marking topic read:', error)
        return { success: false, error }
      }
    },

    // ===== NAVIGATION =====

    setActiveCircle(circleId) {
      this.activeCircleId = circleId
      this.activeTopicId = null
      this.messages = []
      this.clubReadings = []
      this.memberProgress = []
      this.stopPolling()
    },

    setActiveTopic(topicId) {
      this.activeTopicId = topicId
      this.stopPolling()
    },

    openMobileChat(topicId) {
      this.activeTopicId = topicId
      this.mobileView = 'chat'
    },

    closeMobileChat() {
      this.mobileView = 'topics'
      this.activeTopicId = null
      this.stopPolling()
    },

    // ===== DISCOVERY =====

    async fetchDiscoverCircles() {
      try {
        const data = await bookClubService.discoverCircles()
        this.discoverCircles = data || []
        return { success: true }
      } catch (error) {
        console.error('Error loading discover circles:', error)
        return { success: false, error }
      }
    },

    async joinPublicCircle(circleId) {
      try {
        await bookClubService.joinCircle(circleId)
        this.discoverCircles = this.discoverCircles.filter(c => c.id !== circleId)
        await this.fetchCircles()
        this.activeCircleId = circleId
        return { success: true }
      } catch (error) {
        console.error('Error joining circle:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== EVENTS =====

    async fetchCircleEvents(circleId) {
      try {
        const data = await bookClubService.getCircleEvents(circleId)
        this.circleEvents = data || []
        return { success: true }
      } catch (error) {
        console.error('Error loading events:', error)
        return { success: false, error }
      }
    },

    async createCircleEvent(circleId, data) {
      try {
        const event = await bookClubService.createCircleEvent(circleId, data)
        this.circleEvents.push(event)
        return { success: true, data: event }
      } catch (error) {
        console.error('Error creating event:', error)
        return { success: false, error: error.response?.data }
      }
    },

    // ===== CLEANUP =====

    clear() {
      this.stopPolling()
      this.circles = []
      this.activeCircleId = null
      this.activeTopicId = null
      this.messages = []
      this.pendingInvitations = []
      this.clubReadings = []
      this.memberProgress = []
      this.unreadCounts = {}
      this.discoverCircles = []
      this.circleEvents = []
      this.error = null
      this.activeTab = 'topics'
      this.mobileView = 'topics'
    },
  },
})
