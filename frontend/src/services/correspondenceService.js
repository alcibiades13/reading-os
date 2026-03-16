// Correspondence (Chat) Service
import { conversationsAPI, socialAPI } from './api'
import { getMediaUrl } from '@/utils/mediaUrl'

// Helper to ensure avatar URL is absolute
const getAvatarUrl = (avatar) => getMediaUrl(avatar)

export const correspondenceService = {
  /**
   * Get all conversations for current user
   */
  async getConversations() {
    try {
      const response = await conversationsAPI.list()
      // Handle paginated response or plain array
      const data = response.data
      if (Array.isArray(data)) {
        return data
      }
      // DRF paginated response
      return data.results || []
    } catch (error) {
      // Conversations fetch failed
      return []
    }
  },

  /**
   * Get a specific conversation with messages
   */
  async getConversation(conversationId) {
    try {
      const response = await conversationsAPI.get(conversationId)
      return response.data
    } catch (error) {
      // Conversation fetch failed
      return null
    }
  },

  /**
   * Get messages for a specific conversation
   */
  async getMessages(conversationId) {
    try {
      const response = await conversationsAPI.listMessages({ conversation: conversationId })
      // Handle paginated response or plain array
      const data = response.data
      if (Array.isArray(data)) {
        return data
      }
      return data.results || []
    } catch (error) {
      // Messages fetch failed
      return []
    }
  },

  /**
   * Send a new message in a conversation
   * @param {number|null} conversationId - Existing conversation ID (null if starting new)
   * @param {object} messageData - Message content and attachments
   * @param {number|null} recipientId - Recipient user ID (for new conversations)
   */
  async sendMessage(conversationId, messageData, recipientId = null) {
    try {
      const payload = {
        content: messageData.content || '',
        subject: messageData.subject || '',
        is_important: messageData.isImportant || false,
      }

      // Either conversation or recipient_id
      if (conversationId) {
        payload.conversation = conversationId
      } else if (recipientId) {
        payload.recipient_id = recipientId
      }

      // Handle attachments
      if (messageData.attachments?.length > 0) {
        for (const attachment of messageData.attachments) {
          if (attachment.type === 'book') {
            payload.attached_book_id = attachment.id
          } else if (attachment.type === 'quote') {
            payload.attached_quote_id = attachment.id
          } else if (attachment.type === 'note') {
            payload.attached_study_note_id = attachment.id
          }
        }
      }

      const response = await conversationsAPI.sendMessage(payload)
      return response.data
    } catch (error) {
      // Message send failed
      throw error
    }
  },

  /**
   * Start a new conversation with a user
   * @param {number} recipientId - The user ID to start conversation with
   */
  async startConversation(recipientId) {
    try {
      const response = await conversationsAPI.start(recipientId)
      return response.data
    } catch (error) {
      // Start conversation failed
      throw error
    }
  },

  /**
   * Mark all messages in a conversation as read
   */
  async markAsRead(conversationId) {
    try {
      await conversationsAPI.markRead(conversationId)
    } catch (error) {
      // Mark as read failed
    }
  },

  /**
   * Search for users to start a conversation with
   * @param {string} query - Search query
   */
  async searchUsers(query) {
    if (!query || query.trim().length < 2) {
      return []
    }

    try {
      const response = await socialAPI.searchUsers(query)
      // Handle paginated response or plain array
      const data = response.data
      if (Array.isArray(data)) {
        return data
      }
      return data.results || []
    } catch (error) {
      // User search failed
      return []
    }
  },

  /**
   * Search conversations by participant name or message content
   */
  async searchConversations(query) {
    try {
      const conversations = await this.getConversations()
      if (!query) return conversations

      const lowerQuery = query.toLowerCase()
      return conversations.filter(conv => {
        // Search in other participant's name
        const otherParticipant = conv.other_participant
        if (otherParticipant) {
          const fullName = `${otherParticipant.first_name || ''} ${otherParticipant.last_name || ''}`.toLowerCase()
          if (fullName.includes(lowerQuery)) return true
          if (otherParticipant.email?.toLowerCase().includes(lowerQuery)) return true
        }

        // Search in last message preview
        if (conv.last_message_preview?.toLowerCase().includes(lowerQuery)) return true

        return false
      })
    } catch (error) {
      // Conversation search failed
      return []
    }
  },

  /**
   * Transform API message to frontend format
   * Normalizes the message structure for the UI components
   */
  transformMessage(message) {
    const attachments = []

    if (message.attached_book) {
      attachments.push({
        type: 'book',
        id: message.attached_book.id,
        title: message.attached_book.title,
        subtitle: message.attached_book.authors?.map(a => a.name).join(', ') || '',
        image: message.attached_book.cover_image,
      })
    }

    if (message.attached_quote) {
      attachments.push({
        type: 'quote',
        id: message.attached_quote.id,
        content: message.attached_quote.text,
        title: message.attached_quote.book_title || 'Quote',
        subtitle: message.attached_quote.book_author || '',
      })
    }

    if (message.attached_study_note) {
      attachments.push({
        type: 'note',
        id: message.attached_study_note.id,
        content: message.attached_study_note.content,
        title: message.attached_study_note.book_title || 'Study Note',
        subtitle: message.attached_study_note.reference || '',
        noteType: message.attached_study_note.note_type,
      })
    }

    return {
      id: message.id,
      senderId: message.sender?.id,
      senderName: message.sender ? `${message.sender.first_name} ${message.sender.last_name}` : 'Unknown',
      timestamp: message.created_at,
      content: message.content,
      subject: message.subject,
      attachments,
      isImportant: message.is_important,
      status: message.read_at ? 'read' : 'sent',
      isOwn: message.is_own_message,
    }
  },

  /**
   * Transform API conversation to frontend format
   */
  transformConversation(conversation) {
    const lastMsg = conversation.last_message
    const other = conversation.other_participant

    return {
      id: conversation.id,
      participants: [
        { id: 'me', name: 'You' },
        other ? {
          id: other.id,
          name: `${other.first_name || ''} ${other.last_name || ''}`.trim() || other.email,
          avatar: getAvatarUrl(other.avatar),
          email: other.email,
        } : null,
      ].filter(Boolean),
      unreadCount: conversation.unread_count || 0,
      type: 'direct',
      lastMessage: lastMsg ? {
        id: lastMsg.id,
        senderId: lastMsg.sender_id,
        timestamp: lastMsg.created_at,
        content: lastMsg.content,
        isImportant: lastMsg.is_important,
      } : null,
      lastMessageAt: conversation.last_message_at,
    }
  },
}
