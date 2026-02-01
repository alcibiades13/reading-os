<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { correspondenceService } from '@/services/correspondenceService'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useAuthStore } from '@/stores/authStore'
import ConversationListItem from '@/components/correspondence/ConversationListItem.vue'
import MessageCard from '@/components/correspondence/MessageCard.vue'
import MessageComposer from '@/components/correspondence/MessageComposer.vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  MessageSquare, Search, Plus, Star, Inbox,
  MoreHorizontal, User, Loader2
} from 'lucide-vue-next'

const booksStore = useUserBooksStore()
const authStore = useAuthStore()

const conversations = ref([])
const activeConvId = ref(null)
const messages = ref([])
const searchQuery = ref('')
const loading = ref(true)

// New conversation modal state
const showNewConversationModal = ref(false)
const userSearchQuery = ref('')
const userSearchResults = ref([])
const searchingUsers = ref(false)
const selectedUser = ref(null)

// Debounce for user search
let searchDebounce = null

onMounted(async () => {
  loading.value = true
  await Promise.all([
    loadConversations(),
    booksStore.fetchBooks()
  ])
  loading.value = false
})

const loadConversations = async () => {
  const rawConversations = await correspondenceService.getConversations()
  conversations.value = (rawConversations || []).map(c => correspondenceService.transformConversation(c))
}

const loadMessages = async (convId) => {
  const rawMessages = await correspondenceService.getMessages(convId)
  messages.value = rawMessages.map(m => correspondenceService.transformMessage(m))

  // Mark as read
  await correspondenceService.markAsRead(convId)
}

watch(activeConvId, async (newId) => {
  if (newId) {
    await loadMessages(newId)
  }
})

// User search for new conversations
watch(userSearchQuery, (query) => {
  clearTimeout(searchDebounce)

  if (!query || query.trim().length < 2) {
    userSearchResults.value = []
    return
  }

  searchDebounce = setTimeout(async () => {
    searchingUsers.value = true
    userSearchResults.value = await correspondenceService.searchUsers(query)
    searchingUsers.value = false
  }, 300)
})

const filteredConversations = computed(() => {
  if (!searchQuery.value) return conversations.value

  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conv => {
    const otherParticipant = conv.participants.find(p => p.id !== 'me')
    if (otherParticipant?.name?.toLowerCase().includes(query)) return true
    if (conv.lastMessage?.content?.toLowerCase().includes(query)) return true
    return false
  })
})

const activeConv = computed(() =>
  conversations.value.find(c => c.id === activeConvId.value)
)

const otherParticipant = computed(() =>
  activeConv.value?.participants.find(p => p.id !== 'me')
)

const currentUserId = computed(() => authStore.user?.id)

const handleSelectConversation = (convId) => {
  activeConvId.value = convId
}

const handleSendMessage = async (messageData) => {
  if (!activeConvId.value) return

  try {
    const sentRaw = await correspondenceService.sendMessage(activeConvId.value, messageData)
    const sent = correspondenceService.transformMessage(sentRaw)
    messages.value.push(sent)

    // Update conversation's last message
    const convIndex = conversations.value.findIndex(c => c.id === activeConvId.value)
    if (convIndex !== -1) {
      conversations.value[convIndex].lastMessage = {
        id: sent.id,
        senderId: currentUserId.value,
        timestamp: sent.timestamp,
        content: sent.content,
        isImportant: sent.isImportant,
      }
    }

    // Scroll to bottom
    setTimeout(() => {
      const timeline = document.querySelector('.message-timeline')
      if (timeline) {
        timeline.scrollTop = timeline.scrollHeight
      }
    }, 100)
  } catch (error) {
    console.error('Failed to send message:', error)
  }
}

const openNewConversationModal = () => {
  userSearchQuery.value = ''
  userSearchResults.value = []
  selectedUser.value = null
  showNewConversationModal.value = true
}

const selectUserForConversation = async (user) => {
  try {
    // Start or get existing conversation
    const conversationRaw = await correspondenceService.startConversation(user.id)
    const conversation = correspondenceService.transformConversation(conversationRaw)

    // Check if conversation already exists in list
    const existingIndex = conversations.value.findIndex(c => c.id === conversation.id)
    if (existingIndex === -1) {
      conversations.value.unshift(conversation)
    }

    // Select the conversation
    activeConvId.value = conversation.id
    showNewConversationModal.value = false

    // Load messages
    await loadMessages(conversation.id)
  } catch (error) {
    console.error('Failed to start conversation:', error)
  }
}

// Get books mentioned in conversation
const mentionedBooks = computed(() => {
  if (!activeConv.value) return []

  const bookIds = new Set()
  messages.value.forEach(msg => {
    msg.attachments?.forEach(att => {
      if (att.type === 'book') {
        bookIds.add(att.id)
      }
    })
  })

  return booksStore.books.filter(book => bookIds.has(book.book.id.toString()))
})
</script>

<template>
  <div class="h-full flex animate-in fade-in duration-700 bg-slate-950">

    <!-- INBOX SIDEBAR (Secondary Sidebar) -->
    <aside class="w-80 border-r border-slate-800/50 flex flex-col bg-slate-950/50 backdrop-blur-md">
      <div class="p-6 border-b border-slate-800/50">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xs font-black text-slate-50 uppercase tracking-[0.3em]">Correspondents</h2>
          <button
            @click="openNewConversationModal"
            class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all"
            title="Start new conversation"
          >
            <Plus :size="16" />
          </button>
        </div>
        <div class="relative group">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" :size="14" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filter conversations..."
            class="w-full bg-white/5 border border-slate-800/50 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-50 outline-none focus:border-indigo-500 transition-all"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <!-- Loading state -->
        <div v-if="loading" class="flex items-center justify-center py-12">
          <Loader2 :size="24" class="text-indigo-400 animate-spin" />
        </div>

        <!-- Conversations list -->
        <template v-else-if="filteredConversations.length > 0">
          <ConversationListItem
            v-for="conv in filteredConversations"
            :key="conv.id"
            :conversation="conv"
            :isActive="activeConvId === conv.id"
            @select="handleSelectConversation(conv.id)"
          />
        </template>

        <!-- Empty state -->
        <div v-else class="flex flex-col items-center justify-center py-12 px-6 text-center">
          <MessageSquare :size="32" class="text-slate-600 mb-4" />
          <p class="text-sm text-slate-500">No conversations yet</p>
          <button
            @click="openNewConversationModal"
            class="mt-4 px-4 py-2 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold hover:bg-indigo-500/20 transition-all"
          >
            Start a conversation
          </button>
        </div>
      </div>
    </aside>

    <!-- THREAD AREA -->
    <main class="flex-1 flex flex-col relative">
      <template v-if="activeConv">
        <!-- Thread Header -->
        <header class="h-16 border-b border-slate-800/50 px-8 flex items-center justify-between bg-slate-950/50 backdrop-blur-md sticky top-0 z-20">
          <div class="flex items-center gap-4">
            <div class="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center text-[10px] font-black text-white">
              {{ otherParticipant?.name?.charAt(0) || '?' }}
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-50">{{ otherParticipant?.name }}</h3>
              <span class="text-[9px] text-slate-400 font-black uppercase tracking-widest">Deliberate Exchange</span>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button class="p-2 text-slate-400 hover:text-slate-50 transition-colors">
              <Star :size="18" />
            </button>
            <button class="p-2 text-slate-400 hover:text-slate-50 transition-colors">
              <MoreHorizontal :size="18" />
            </button>
          </div>
        </header>

        <!-- Message Timeline -->
        <div class="flex-1 overflow-y-auto p-6 custom-scrollbar space-y-6 message-timeline">
          <template v-if="messages.length > 0">
            <MessageCard
              v-for="msg in messages"
              :key="msg.id"
              :message="msg"
              :isMe="msg.isOwn"
            />
          </template>

          <!-- No messages yet -->
          <div v-else class="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare :size="32" class="text-slate-600 mb-4" />
            <p class="text-sm text-slate-500">Start the conversation</p>
          </div>

          <div class="h-20" /> <!-- Spacer -->
        </div>

        <!-- Advanced Composer -->
        <MessageComposer @send="handleSendMessage" />
      </template>

      <!-- Empty State -->
      <div v-else class="flex-1 flex flex-col items-center justify-center text-center p-12 opacity-40">
        <Inbox :size="48" class="text-slate-400 mb-8" />
        <h3 class="text-2xl font-black text-slate-50 mb-2 uppercase tracking-[0.3em]">Correspondence Chamber</h3>
        <p class="max-w-xs text-slate-400 font-medium">Select a correspondent to begin a deliberate intellectual exchange.</p>
      </div>
    </main>

    <!-- New Conversation Modal -->
    <Dialog v-model:open="showNewConversationModal">
      <DialogContent class="max-w-md glass border-slate-700">
        <DialogHeader class="border-b border-slate-800 pb-4">
          <DialogTitle class="text-lg font-bold flex items-center gap-2 text-white">
            <MessageSquare :size="20" class="text-indigo-400" />
            New Conversation
          </DialogTitle>
        </DialogHeader>

        <div class="space-y-4 py-4">
          <p class="text-sm text-slate-400">
            Search for a friend to start a conversation with.
          </p>

          <!-- User search input -->
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
            <input
              v-model="userSearchQuery"
              type="text"
              placeholder="Search by name or email..."
              class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-50 outline-none focus:border-indigo-500 transition-all placeholder-slate-500"
              autofocus
            />
          </div>

          <!-- Loading state -->
          <div v-if="searchingUsers" class="flex items-center justify-center py-8">
            <Loader2 :size="24" class="text-indigo-400 animate-spin" />
          </div>

          <!-- Search results -->
          <div v-else-if="userSearchResults.length > 0" class="max-h-64 overflow-y-auto space-y-2">
            <button
              v-for="user in userSearchResults"
              :key="user.id"
              @click="selectUserForConversation(user)"
              class="w-full p-3 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 hover:bg-slate-800/50 transition-all flex items-center gap-3 text-left"
            >
              <div class="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-sm font-bold text-indigo-400">
                {{ (user.first_name?.[0] || user.email?.[0] || '?').toUpperCase() }}
              </div>
              <div class="flex-1 min-w-0">
                <p class="font-semibold text-slate-100 text-sm truncate">
                  {{ user.first_name }} {{ user.last_name }}
                </p>
                <p class="text-xs text-slate-500 truncate">{{ user.email }}</p>
              </div>
              <div class="text-xs text-slate-600">
                {{ user.books_read_count || 0 }} books
              </div>
            </button>
          </div>

          <!-- Empty state -->
          <div v-else-if="userSearchQuery.length >= 2" class="flex flex-col items-center justify-center py-8 text-center">
            <User :size="32" class="text-slate-600 mb-4" />
            <p class="text-sm text-slate-500">No users found</p>
            <p class="text-xs text-slate-600 mt-1">Try a different search term</p>
          </div>

          <!-- Initial state -->
          <div v-else class="flex flex-col items-center justify-center py-8 text-center">
            <Search :size="32" class="text-slate-600 mb-4" />
            <p class="text-sm text-slate-500">Type at least 2 characters to search</p>
          </div>
        </div>

        <!-- Footer -->
        <div class="pt-4 border-t border-slate-800">
          <button
            @click="showNewConversationModal = false"
            class="w-full px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all border border-slate-700 hover:border-slate-600"
          >
            Cancel
          </button>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&display=swap');

.font-serif {
  font-family: 'Crimson Pro', Georgia, serif;
}

.animate-in {
  animation: fadeIn 0.7s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Custom scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}

.glass {
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(12px);
}

/* Light mode adjustments */
body.light .bg-slate-950 {
  background-color: #f8fafc !important;
}

body.light .bg-slate-900\/20 {
  background-color: rgba(255, 255, 255, 0.9) !important;
}

body.light .text-white {
  color: #0f172a !important;
}

body.light .text-slate-500 {
  color: #64748b !important;
}

body.light .text-slate-200 {
  color: #1e293b !important;
}

body.light .border-white\/5,
body.light .border-white\/10 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}

body.light .bg-white\/5 {
  background-color: rgba(0, 0, 0, 0.03) !important;
}
</style>
