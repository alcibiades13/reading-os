
import { Conversation, Message } from '../types';

const STORAGE_KEY_CONVS = 'vellux_conversations';
const CURRENT_USER_ID = 'me';

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 'conv-1',
    participants: [
      { id: 'me', name: 'Julian Thorne' },
      { id: 'u-1', name: 'Elena Rodriguez', avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop' }
    ],
    unreadCount: 2,
    type: 'direct',
    relatedBookIds: ['f_S8DwAAQBAJ', 'D_4yEAAAQBAJ'],
    lastMessage: {
      id: 'm-1',
      senderId: 'u-1',
      senderName: 'Elena Rodriguez',
      timestamp: '2025-05-18T14:30:00Z',
      content: 'I finally reached the third act of Dune and your notes on the "Litany Against Fear" were spot on. Let\'s discuss the philosophy of agency behind it.',
      attachments: [],
      isImportant: true,
      status: 'read'
    }
  },
  {
    id: 'conv-2',
    participants: [
      { id: 'me', name: 'Julian Thorne' },
      { id: 'u-2', name: 'Marcus Chen' }
    ],
    unreadCount: 0,
    type: 'direct',
    relatedBookIds: ['B1hGBAAAQBAJ'],
    lastMessage: {
      id: 'm-2',
      senderId: 'me',
      senderName: 'Julian Thorne',
      timestamp: '2025-05-17T09:15:00Z',
      content: 'Have you checked out this specific edition of Meditations?',
      attachments: [
        { 
          type: 'book', 
          id: 'B1hGBAAAQBAJ', 
          title: 'Meditations', 
          subtitle: 'Marcus Aurelius',
          image: 'https://books.google.com/books/content?id=7S7mDwAAQBAJ&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api' 
        }
      ],
      isImportant: false,
      status: 'sent'
    }
  }
];

const MOCK_MESSAGES: Record<string, Message[]> = {
  'conv-1': [
    {
      id: 'm-0',
      senderId: 'me',
      senderName: 'Julian Thorne',
      timestamp: '2025-05-18T10:00:00Z',
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
      timestamp: '2025-05-18T14:30:00Z',
      content: 'I finally reached the third act of Dune and your notes on the "Litany Against Fear" were spot on. Let\'s discuss the philosophy of agency behind it.',
      attachments: [],
      isImportant: true,
      status: 'read'
    }
  ]
};

export const getConversations = (): Conversation[] => {
  const stored = localStorage.getItem(STORAGE_KEY_CONVS);
  if (!stored) {
    localStorage.setItem(STORAGE_KEY_CONVS, JSON.stringify(MOCK_CONVERSATIONS));
    return MOCK_CONVERSATIONS;
  }
  return JSON.parse(stored);
};

export const getMessages = (convId: string): Message[] => {
  return MOCK_MESSAGES[convId] || [];
};

export const sendMessage = (convId: string, message: Partial<Message>): Message => {
  const newMessage: Message = {
    id: `m-${Date.now()}`,
    senderId: 'me',
    senderName: 'Julian Thorne',
    timestamp: new Date().toISOString(),
    content: message.content || '',
    attachments: message.attachments || [],
    isImportant: message.isImportant || false,
    status: 'sent',
    subject: message.subject
  };

  if (!MOCK_MESSAGES[convId]) MOCK_MESSAGES[convId] = [];
  MOCK_MESSAGES[convId].push(newMessage);
  return newMessage;
};
