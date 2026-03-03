import { defineStore } from 'pinia'
import { bookClubService } from '@/services/bookClubService'
import { useAuthStore } from '@/stores/authStore'
import { withLoading, tryCatch } from '@/utils/storeHelpers'

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
    // Polling / sync
    pollTimer: null,
    lastSyncTimestamp: null,
    // Edit state
    editingMessageId: null,
    // Poll
    activePoll: null,
    // UI state
    activeTab: 'topics',
    mobileView: 'topics',
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
      return withLoading(this, async () => {
        const data = await bookClubService.getCircles()
        this.circles = data.results || data || []
        if (this.circles.length > 0 && !this.activeCircleId) {
          this.activeCircleId = this.circles[0].id
        }
      }, 'Failed to fetch circles')
    },

    async fetchCircleDetail(circleId) {
      return tryCatch(async () => {
        const detail = await bookClubService.getCircle(circleId)
        const idx = this.circles.findIndex(c => c.id === circleId)
        if (idx !== -1) {
          this.circles[idx] = { ...this.circles[idx], ...detail }
        }
        return detail
      })
    },

    async fetchPendingInvitations() {
      return tryCatch(async () => {
        const data = await bookClubService.getInvitations()
        this.pendingInvitations = (data.results || data || []).filter(
          inv => inv.status === 'pending'
        )
      })
    },

    async fetchTopicMessages(topicId) {
      return tryCatch(async () => {
        const data = await bookClubService.getTopicMessages(topicId)
        this.messages = data.results || data || []
        if (this.messages.length > 0) {
          const timestamps = this.messages.map(m => m.updated_at || m.created_at)
          this.lastSyncTimestamp = timestamps.sort().pop()
        } else {
          this.lastSyncTimestamp = new Date().toISOString()
        }
      })
    },

    async syncMessages(topicId) {
      if (!this.lastSyncTimestamp) return
      try {
        const data = await bookClubService.syncTopicMessages(topicId, this.lastSyncTimestamp)

        if (data.new?.length > 0) {
          const existingIds = new Set(this.messages.map(m => m.id))
          const unique = data.new.filter(m => !existingIds.has(m.id))
          if (unique.length > 0) {
            this.messages.push(...unique)
          }
        }

        if (data.edited?.length > 0) {
          for (const edited of data.edited) {
            const idx = this.messages.findIndex(m => m.id === edited.id)
            if (idx !== -1) {
              this.messages[idx] = { ...this.messages[idx], ...edited }
            }
          }
        }

        if (data.deleted?.length > 0) {
          const deletedSet = new Set(data.deleted)
          this.messages = this.messages.filter(m => !deletedSet.has(m.id))
        }

        if (data.server_time) {
          this.lastSyncTimestamp = data.server_time
        }
      } catch (error) {
        console.error('Error syncing messages:', error)
      }
    },

    // ===== POLLING =====

    startPolling(topicId) {
      this.stopPolling()
      const sync = () => {
        this.syncMessages(topicId)
        if (this.activePoll) {
          this.fetchTopicPoll(topicId)
        }
      }
      this.pollTimer = setInterval(sync, 3000)

      const handler = () => {
        if (document.hidden) {
          clearInterval(this.pollTimer)
          this.pollTimer = null
        } else {
          sync()
          this.pollTimer = setInterval(sync, 3000)
        }
      }
      this._visibilityHandler = handler
      document.addEventListener('visibilitychange', handler)
    },

    stopPolling() {
      if (this.pollTimer) {
        clearInterval(this.pollTimer)
        this.pollTimer = null
      }
      if (this._visibilityHandler) {
        document.removeEventListener('visibilitychange', this._visibilityHandler)
        this._visibilityHandler = null
      }
    },

    // ===== CIRCLE ACTIONS =====

    async createCircle(formData) {
      return tryCatch(async () => {
        const newCircle = await bookClubService.createCircle(formData)
        this.circles.unshift(newCircle)
        this.setActiveCircle(newCircle.id)
        return newCircle
      })
    },

    async updateCircle(circleId, data) {
      return tryCatch(async () => {
        const updated = await bookClubService.updateCircle(circleId, data)
        const idx = this.circles.findIndex(c => c.id === updated.id)
        if (idx !== -1) {
          this.circles[idx] = { ...this.circles[idx], ...updated }
        }
        return updated
      })
    },

    async deleteCircle(circleId) {
      return tryCatch(async () => {
        await bookClubService.deleteCircle(circleId)
        this.circles = this.circles.filter(c => c.id !== circleId)
        this.activeCircleId = this.circles[0]?.id || null
      })
    },

    async leaveCircle(circleId) {
      return tryCatch(async () => {
        await bookClubService.leaveCircle(circleId)
        this.circles = this.circles.filter(c => c.id !== circleId)
        this.activeCircleId = this.circles[0]?.id || null
      })
    },

    async promoteMember(circleId, userId) {
      return tryCatch(async () => {
        await bookClubService.promoteMember(circleId, userId)
        await this.fetchCircleDetail(circleId)
      })
    },

    // ===== INVITATIONS =====

    async acceptInvitation(invitationId) {
      return tryCatch(async () => {
        await bookClubService.acceptInvitation(invitationId)
        this.pendingInvitations = this.pendingInvitations.filter(
          inv => inv.id !== invitationId
        )
        await this.fetchCircles()
      })
    },

    async declineInvitation(invitationId) {
      return tryCatch(async () => {
        await bookClubService.declineInvitation(invitationId)
        this.pendingInvitations = this.pendingInvitations.filter(
          inv => inv.id !== invitationId
        )
      })
    },

    // ===== TOPICS =====

    async createTopic(data) {
      return tryCatch(async () => {
        const newTopic = await bookClubService.createTopic(data)
        await this.fetchCircleDetail(this.activeCircleId)
        this.activeTopicId = newTopic.id
        return newTopic
      })
    },

    async updateTopic(topicId, data) {
      return tryCatch(async () => {
        const updated = await bookClubService.updateTopic(topicId, data)
        await this.fetchCircleDetail(this.activeCircleId)
        return updated
      })
    },

    async deleteTopic(topicId) {
      return tryCatch(async () => {
        await bookClubService.deleteTopic(topicId)
        if (this.activeTopicId === topicId) {
          this.activeTopicId = null
          this.messages = []
          this.activePoll = null
        }
        await this.fetchCircleDetail(this.activeCircleId)
      })
    },

    async togglePinTopic(topicId) {
      return tryCatch(async () => {
        const result = await bookClubService.togglePinTopic(topicId)
        await this.fetchCircleDetail(this.activeCircleId)
        return result
      })
    },

    async togglePinMessage(messageId) {
      return tryCatch(async () => {
        const result = await bookClubService.togglePinMessage(messageId)
        const msg = this.messages.find(m => m.id === messageId)
        if (msg) {
          if (result.is_pinned) {
            this.messages.forEach(m => { if (m.id !== messageId) m.is_pinned = false })
          }
          msg.is_pinned = result.is_pinned
        }
        return result
      })
    },

    // ===== MESSAGES =====

    async sendMessage(data) {
      const authStore = useAuthStore()
      return tryCatch(async () => {
        const newMessage = await bookClubService.sendTopicMessage(data)
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
        return newMessage
      })
    },

    async toggleMessageLike(messageId) {
      return tryCatch(async () => {
        const result = await bookClubService.toggleMessageLike(messageId)
        const msg = this.messages.find(m => m.id === messageId)
        if (msg) {
          msg.is_liked = result.liked
          msg.likes_count = result.likes_count
        }
        return result
      })
    },

    async deleteMessage(messageId) {
      return tryCatch(async () => {
        await bookClubService.deleteTopicMessage(messageId)
        this.messages = this.messages.filter(m => m.id !== messageId)
      })
    },

    async editMessage(messageId, newContent) {
      const msg = this.messages.find(m => m.id === messageId)
      const oldContent = msg?.content
      // Optimistic update
      if (msg) {
        msg.content = newContent
        msg.is_edited = true
      }
      this.editingMessageId = null

      try {
        const updated = await bookClubService.editTopicMessage(messageId, newContent)
        if (msg) {
          Object.assign(msg, updated)
        }
        return { success: true }
      } catch (error) {
        // Rollback on failure
        if (msg) {
          msg.content = oldContent
          msg.is_edited = false
        }
        return { success: false, error: error.response?.data }
      }
    },

    startEditing(messageId) {
      this.editingMessageId = messageId
    },

    cancelEditing() {
      this.editingMessageId = null
    },

    // ===== POLLS =====

    async fetchTopicPoll(topicId) {
      return tryCatch(async () => {
        this.activePoll = await bookClubService.getPollByTopic(topicId)
      })
    },

    async createPoll(data) {
      return tryCatch(async () => {
        const poll = await bookClubService.createPoll(data)
        this.activePoll = poll
        return poll
      })
    },

    async votePoll(pollId, optionId) {
      return tryCatch(async () => {
        const updated = await bookClubService.votePoll(pollId, optionId)
        this.activePoll = updated
      })
    },

    async closePoll(pollId) {
      return tryCatch(async () => {
        const updated = await bookClubService.closePoll(pollId)
        this.activePoll = updated
      })
    },

    // ===== BOOK CLUB READINGS =====

    async fetchClubReadings(circleId) {
      return tryCatch(async () => {
        const data = await bookClubService.getClubReadings(circleId)
        this.clubReadings = data.results || data || []
      })
    },

    async addClubReading(data) {
      return tryCatch(async () => {
        const reading = await bookClubService.addClubReading(data)
        this.clubReadings.unshift(reading)
        return reading
      })
    },

    async setCurrentReading(readingId) {
      return tryCatch(async () => {
        const result = await bookClubService.setCurrentReading(readingId)
        await Promise.all([
          this.fetchClubReadings(this.activeCircleId),
          this.fetchCircleDetail(this.activeCircleId),
        ])
        return result
      })
    },

    async deleteClubReading(readingId) {
      return tryCatch(async () => {
        await bookClubService.deleteClubReading(readingId)
        this.clubReadings = this.clubReadings.filter(r => r.id !== readingId)
      })
    },

    // ===== MEMBER PROGRESS =====

    async fetchMemberProgress(circleId) {
      return tryCatch(async () => {
        const data = await bookClubService.getMemberProgress(circleId)
        this.memberProgress = data || []
      })
    },

    // ===== UNREAD TRACKING =====

    async fetchUnreadCounts(circleId) {
      return tryCatch(async () => {
        const data = await bookClubService.getUnreadCounts(circleId)
        this.unreadCounts = { ...this.unreadCounts, ...data }
      })
    },

    async markTopicRead(topicId) {
      return tryCatch(async () => {
        await bookClubService.markTopicRead(topicId)
        delete this.unreadCounts[topicId]
      })
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
      this.activePoll = null
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
      return tryCatch(async () => {
        const data = await bookClubService.discoverCircles()
        this.discoverCircles = data || []
      })
    },

    async joinPublicCircle(circleId) {
      return tryCatch(async () => {
        await bookClubService.joinCircle(circleId)
        this.discoverCircles = this.discoverCircles.filter(c => c.id !== circleId)
        await this.fetchCircles()
        this.activeCircleId = circleId
      })
    },

    // ===== EVENTS =====

    async fetchCircleEvents(circleId) {
      return tryCatch(async () => {
        const data = await bookClubService.getCircleEvents(circleId)
        this.circleEvents = data || []
      })
    },

    async createCircleEvent(circleId, data) {
      return tryCatch(async () => {
        const event = await bookClubService.createCircleEvent(circleId, data)
        this.circleEvents.push(event)
        return event
      })
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
      this.lastSyncTimestamp = null
      this.editingMessageId = null
      this.activePoll = null
      this.error = null
      this.activeTab = 'topics'
      this.mobileView = 'topics'
    },
  },
})
