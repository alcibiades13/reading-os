// Correspondence (Chat) Service
import api from './api'

const STORAGE_KEY_CONVS = 'reading_os_conversations'
const CURRENT_USER_ID = 'me'

// Mock conversations for development
const MOCK_CONVERSATIONS = [
  {
    id: 'conv-1',
    participants: [
      { id: 'me', name: 'You' },
      { id: 'u-1', name: 'Elena Rodriguez', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop' }
    ],
    unreadCount: 2,
    type: 'direct',
    relatedBookIds: [],
    lastMessage: {
      id: 'm-1',
      senderId: 'u-1',
      senderName: 'Elena Rodriguez',
      timestamp: '2025-01-07T14:30:00Z',
      content: 'I finally reached the third act of Dune and your notes on the "Litany Against Fear" were spot on. Let\'s discuss the philosophy of agency behind it.',
      attachments: [],
      isImportant: true,
      status: 'read'
    }
  },
  {
    id: 'conv-2',
    participants: [
      { id: 'me', name: 'You' },
      { id: 'u-2', name: 'Marcus Chen' }
    ],
    unreadCount: 0,
    type: 'direct',
    relatedBookIds: [],
    lastMessage: {
      id: 'm-2',
      senderId: 'me',
      senderName: 'You',
      timestamp: '2025-01-06T09:15:00Z',
      content: 'Have you checked out this specific edition of Meditations?',
      attachments: [
        {
          type: 'book',
          id: '1',
          title: 'Meditations',
          subtitle: 'Marcus Aurelius',
          image: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1'
        }
      ],
      isImportant: false,
      status: 'sent'
    }
  }
]

const MOCK_MESSAGES = {
  'conv-1': [
    {
      id: 'm-0',
      senderId: 'me',
      senderName: 'You',
      timestamp: '2025-01-07T10:00:00Z',
      subject: 'Stoic parallels in modern fiction',
      content: 'Elena, I was thinking about our last conversation regarding Stoicism. I found this quote that perfectly bridges Marcus Aurelius and the themes in our current reading.',
      attachments: [
        {
          type: 'quote',
          id: 'q-1',
          title: 'Meditations Insight',
          content: 'The happiness of your life depends upon the quality of your thoughts.',
          subtitle: 'Marcus Aurelius'
        }
      ],
      isImportant: false,
      status: 'read'
    },
    {
      id: 'm-1',
      senderId: 'u-1',
      senderName: 'Elena Rodriguez',
      timestamp: '2025-01-07T14:30:00Z',
      content: 'I finally reached the third act of Dune and your notes on the "Litany Against Fear" were spot on. Let\'s discuss the philosophy of agency behind it.',
      attachments: [],
      isImportant: true,
      status: 'read'
    }
  ],
  'conv-2': [
    {
      id: 'm-2',
      senderId: 'me',
      senderName: 'You',
      timestamp: '2025-01-06T09:15:00Z',
      content: 'Have you checked out this specific edition of Meditations?',
      attachments: [
        {
          type: 'book',
          id: '1',
          title: 'Meditations',
          subtitle: 'Marcus Aurelius',
          image: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1'
        }
      ],
      isImportant: false,
      status: 'sent'
    }
  ]
}

export const correspondenceService = {
  /**
   * Get all conversations for current user
   */
  async getConversations() {
    try {
      // TODO: Replace with actual API call
      // const response = await api.get('/api/correspondence/conversations/')
      // return response.data

      // For now, use mock data
      const stored = localStorage.getItem(STORAGE_KEY_CONVS)
      if (!stored) {
        localStorage.setItem(STORAGE_KEY_CONVS, JSON.stringify(MOCK_CONVERSATIONS))
        return MOCK_CONVERSATIONS
      }
      return JSON.parse(stored)
    } catch (error) {
      console.error('Error fetching conversations:', error)
      return MOCK_CONVERSATIONS
    }
  },

  /**
   * Get messages for a specific conversation
   */
  async getMessages(conversationId) {
    try {
      // TODO: Replace with actual API call
      // const response = await api.get(`/api/correspondence/conversations/${conversationId}/messages/`)
      // return response.data

      // For now, use mock data
      return MOCK_MESSAGES[conversationId] || []
    } catch (error) {
      console.error('Error fetching messages:', error)
      return []
    }
  },

  /**
   * Send a new message in a conversation
   */
  async sendMessage(conversationId, messageData) {
    try {
      // TODO: Replace with actual API call
      // const response = await api.post(`/api/correspondence/conversations/${conversationId}/messages/`, messageData)
      // return response.data

      // For now, create mock message
      const newMessage = {
        id: `m-${Date.now()}`,
        senderId: 'me',
        senderName: 'You',
        timestamp: new Date().toISOString(),
        content: messageData.content || '',
        attachments: messageData.attachments || [],
        isImportant: messageData.isImportant || false,
        status: 'sent',
        subject: messageData.subject
      }

      if (!MOCK_MESSAGES[conversationId]) {
        MOCK_MESSAGES[conversationId] = []
      }
      MOCK_MESSAGES[conversationId].push(newMessage)

      return newMessage
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    }
  },

  /**
   * Create a new conversation
   */
  async createConversation(participantIds, initialMessage) {
    try {
      // TODO: Replace with actual API call
      // const response = await api.post('/api/correspondence/conversations/', {
      //   participants: participantIds,
      //   initial_message: initialMessage
      // })
      // return response.data

      throw new Error('Not implemented yet')
    } catch (error) {
      console.error('Error creating conversation:', error)
      throw error
    }
  },

  /**
   * Mark message as read
   */
  async markAsRead(conversationId, messageId) {
    try {
      // TODO: Replace with actual API call
      // await api.post(`/api/correspondence/messages/${messageId}/mark_read/`)
    } catch (error) {
      console.error('Error marking message as read:', error)
    }
  },

  /**
   * Search conversations
   */
  async searchConversations(query) {
    try {
      // TODO: Replace with actual API call
      // const response = await api.get('/api/correspondence/conversations/search/', { params: { q: query } })
      // return response.data

      const conversations = await this.getConversations()
      return conversations.filter(conv =>
        conv.participants.some(p => p.name.toLowerCase().includes(query.toLowerCase())) ||
        conv.lastMessage?.content.toLowerCase().includes(query.toLowerCase())
      )
    } catch (error) {
      console.error('Error searching conversations:', error)
      return []
    }
  }
}
