<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { correspondenceService } from '@/services/correspondenceService'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useAuthStore } from '@/stores/authStore'
import ConversationListItem from '@/components/correspondence/ConversationListItem.vue'
import MessageCard from '@/components/correspondence/MessageCard.vue'
import MessageComposer from '@/components/correspondence/MessageComposer.vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  MessageSquare, Search, Plus, Star, Inbox,
  MoreHorizontal, User, Loader2, ArrowLeft, Send
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

// Mobile state
const mobileView = ref('list') // 'list' | 'chat'
const mobileMessageInput = ref('')
const sendingMobileMessage = ref(false)
const mobileMessagesRef = ref(null)
const showMobileMenu = ref(false)

// Mobile navigation
const openMobileChat = (convId) => {
  activeConvId.value = convId
  mobileView.value = 'chat'
}

const closeMobileChat = () => {
  mobileView.value = 'list'
}

// Mobile scroll to bottom
const scrollMobileToBottom = async () => {
  await nextTick()
  if (mobileMessagesRef.value) {
    mobileMessagesRef.value.scrollTop = mobileMessagesRef.value.scrollHeight
  }
}

// Mobile send message
const handleMobileSend = async () => {
  if (!mobileMessageInput.value.trim() || !activeConvId.value) return

  sendingMobileMessage.value = true
  try {
    const sentRaw = await correspondenceService.sendMessage(activeConvId.value, {
      content: mobileMessageInput.value,
      attachments: [],
      isImportant: false
    })
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

    mobileMessageInput.value = ''
    scrollMobileToBottom()
  } catch (error) {
    console.error('Failed to send message:', error)
  } finally {
    sendingMobileMessage.value = false
  }
}

// Helper to get other participant
const getOtherParticipant = (conv) => {
  return conv?.participants?.find(p => p.id !== 'me')
}

// Format date helper
const formatTimeAgo = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Now'
  if (diffMins < 60) return `${diffMins}m`
  if (diffHours < 24) return `${diffHours}h`
  if (diffDays < 7) return `${diffDays}d`
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

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
    scrollMobileToBottom()
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
  <div class="h-full flex flex-col lg:flex-row animate-in fade-in duration-700 bg-slate-950">

    <!-- ==================== DESKTOP LAYOUT ==================== -->
    <div class="hidden lg:flex flex-1">
      <!-- DESKTOP: INBOX SIDEBAR (Secondary Sidebar) -->
      <aside class="w-72 border-r border-slate-800/50 flex flex-col bg-slate-950/50 backdrop-blur-md">
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
    </div>
    <!-- END DESKTOP LAYOUT -->

    <!-- ==================== MOBILE LAYOUT ==================== -->
    <div class="lg:hidden flex flex-col h-full">

      <!-- MOBILE: Conversations List View -->
      <template v-if="mobileView === 'list'">
        <!-- Mobile Header -->
        <header class="px-4 py-3 border-b border-slate-800/50 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-30">
          <div class="flex items-center justify-between mb-3">
            <h1 class="text-lg font-black text-white">Messages</h1>
            <button
              @click="openNewConversationModal"
              class="p-2 rounded-xl bg-indigo-500 text-white"
            >
              <Plus :size="18" />
            </button>
          </div>

          <!-- Search -->
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search conversations..."
              class="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-slate-500 outline-none focus:border-indigo-500 transition-all"
            />
          </div>
        </header>

        <!-- Mobile Conversations List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar">
          <!-- Loading -->
          <div v-if="loading" class="flex items-center justify-center py-16">
            <Loader2 :size="28" class="text-indigo-400 animate-spin" />
          </div>

          <!-- Conversations -->
          <template v-else-if="filteredConversations.length > 0">
            <button
              v-for="conv in filteredConversations"
              :key="conv.id"
              @click="openMobileChat(conv.id)"
              class="w-full p-4 border-b border-white/5 active:bg-white/5 transition-all flex items-center gap-4 text-left"
            >
              <!-- Avatar -->
              <div class="w-12 h-12 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-sm shrink-0 overflow-hidden">
                <img
                  v-if="getOtherParticipant(conv)?.avatar && !getOtherParticipant(conv)?.avatar.includes('placeholder')"
                  :src="getOtherParticipant(conv).avatar"
                  class="w-full h-full object-cover"
                />
                <span v-else>{{ getOtherParticipant(conv)?.name?.charAt(0) || '?' }}</span>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <h3 class="text-sm font-bold text-white truncate">{{ getOtherParticipant(conv)?.name }}</h3>
                  <span class="text-[10px] text-slate-500 shrink-0 ml-2">{{ formatTimeAgo(conv.lastMessage?.timestamp) }}</span>
                </div>
                <div class="flex items-center gap-2">
                  <Star v-if="conv.lastMessage?.isImportant" :size="10" class="text-amber-500 fill-current shrink-0" />
                  <p class="text-xs text-slate-400 truncate">{{ conv.lastMessage?.content || 'No messages yet' }}</p>
                </div>
              </div>

              <!-- Unread indicator -->
              <div
                v-if="conv.unreadCount > 0"
                class="w-2.5 h-2.5 rounded-full bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.5)] shrink-0"
              />
            </button>
          </template>

          <!-- Empty State -->
          <div v-else class="flex flex-col items-center justify-center py-16 px-6 text-center">
            <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
              <MessageSquare :size="28" class="text-slate-600" />
            </div>
            <p class="text-sm text-slate-500 mb-4">No conversations yet</p>
            <button
              @click="openNewConversationModal"
              class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold"
            >
              Start a Conversation
            </button>
          </div>
        </div>
      </template>

      <!-- MOBILE: Chat View -->
      <template v-if="mobileView === 'chat' && activeConv">
        <!-- Mobile Chat Header -->
        <header class="px-4 py-3 border-b border-slate-800/50 bg-slate-900/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
          <div class="flex items-center gap-3">
            <button
              @click="closeMobileChat"
              class="p-2 -ml-2 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft :size="22" />
            </button>

            <!-- Avatar -->
            <div class="w-9 h-9 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-xs overflow-hidden">
              <img
                v-if="otherParticipant?.avatar && !otherParticipant?.avatar.includes('placeholder')"
                :src="otherParticipant.avatar"
                class="w-full h-full object-cover"
              />
              <span v-else>{{ otherParticipant?.name?.charAt(0) || '?' }}</span>
            </div>

            <div class="flex-1 min-w-0">
              <h1 class="text-base font-bold text-white truncate">{{ otherParticipant?.name }}</h1>
              <p class="text-[10px] text-slate-500 uppercase tracking-wider">Correspondence</p>
            </div>

            <div class="relative">
              <button
                @click="showMobileMenu = !showMobileMenu"
                class="p-2 rounded-xl text-slate-400 hover:bg-white/5"
              >
                <MoreHorizontal :size="18" />
              </button>

              <!-- Dropdown Menu -->
              <div
                v-if="showMobileMenu"
                class="fixed inset-0 z-40"
                @click="showMobileMenu = false"
              />
              <div
                v-if="showMobileMenu"
                class="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
              >
                <button
                  @click="showMobileMenu = false"
                  class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                >
                  <User :size="16" class="text-slate-500" />
                  View Profile
                </button>
                <button
                  @click="showMobileMenu = false"
                  class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                >
                  <Star :size="16" class="text-slate-500" />
                  Mark Important
                </button>
                <div class="h-px bg-white/5" />
                <button
                  @click="showMobileMenu = false"
                  class="w-full px-4 py-3 text-left text-sm text-rose-400 hover:bg-rose-500/10 flex items-center gap-3"
                >
                  <Inbox :size="16" />
                  Archive Chat
                </button>
              </div>
            </div>
          </div>
        </header>

        <!-- Mobile Messages -->
        <div ref="mobileMessagesRef" class="flex-1 overflow-y-auto custom-scrollbar">
          <div class="p-4 space-y-4">
            <!-- Beginning indicator -->
            <div class="text-center py-6 opacity-40">
              <div class="h-px w-full bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-3" />
              <span class="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">Beginning of Conversation</span>
            </div>

            <!-- No messages -->
            <div v-if="messages.length === 0" class="text-center py-10 text-slate-500 text-sm">
              Start the conversation with {{ otherParticipant?.name }}
            </div>

            <!-- Messages -->
            <div
              v-for="msg in messages"
              :key="msg.id"
              :class="['flex flex-col', msg.isOwn ? 'items-end' : 'items-start']"
            >
              <!-- Sender info -->
              <div :class="['flex items-center gap-2 mb-1', msg.isOwn ? 'flex-row-reverse' : '']">
                <span class="text-[10px] font-bold text-slate-500">{{ msg.senderName }}</span>
                <span class="text-[9px] text-slate-600">{{ formatTimeAgo(msg.timestamp) }}</span>
              </div>

              <!-- Message bubble -->
              <div
                :class="[
                  'max-w-[85%] p-4 rounded-2xl',
                  msg.isOwn
                    ? 'bg-indigo-500/20 border border-indigo-500/30'
                    : 'bg-white/5 border border-white/10'
                ]"
              >
                <!-- Important badge -->
                <div v-if="msg.isImportant" class="flex items-center gap-1.5 mb-2">
                  <Star :size="10" class="text-amber-500 fill-current" />
                  <span class="text-[8px] font-black text-amber-500 uppercase tracking-wider">Important</span>
                </div>

                <!-- Content -->
                <p class="text-sm text-slate-200 leading-relaxed">{{ msg.content }}</p>

                <!-- Attachments -->
                <div v-if="msg.attachments?.length > 0" class="mt-3 pt-3 border-t border-white/5 space-y-2">
                  <div
                    v-for="(att, i) in msg.attachments"
                    :key="i"
                    class="p-3 rounded-xl bg-white/5"
                  >
                    <p class="text-[9px] font-black text-indigo-400 uppercase tracking-wider mb-1">
                      {{ att.type === 'book' ? 'Book' : 'Quote' }}
                    </p>
                    <p class="text-xs text-white font-bold truncate">{{ att.title }}</p>
                    <p v-if="att.subtitle" class="text-[10px] text-slate-500 truncate">{{ att.subtitle }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="h-4" />
          </div>
        </div>

        <!-- Mobile Composer -->
        <div class="p-4 border-t border-slate-800/50 bg-slate-950/90 backdrop-blur-xl safe-area-bottom">
          <div class="flex items-end gap-3">
            <div class="flex-1">
              <textarea
                v-model="mobileMessageInput"
                @keydown.enter.exact.prevent="handleMobileSend"
                placeholder="Write a message..."
                rows="1"
                class="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-slate-100 placeholder-slate-600 focus:border-indigo-500 outline-none transition-all resize-none text-sm max-h-32"
                style="field-sizing: content;"
              />
            </div>
            <button
              @click="handleMobileSend"
              :disabled="!mobileMessageInput.trim() || sendingMobileMessage"
              class="w-11 h-11 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 active:scale-95 transition-transform"
            >
              <Send :size="18" />
            </button>
          </div>
        </div>
      </template>
    </div>
    <!-- END MOBILE LAYOUT -->

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

/* Safe area support for notched phones */
.safe-area-top {
  padding-top: max(0.75rem, env(safe-area-inset-top));
}

.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

/* Mobile touch feedback */
@media (max-width: 1023px) {
  button {
    -webkit-tap-highlight-color: transparent;
  }
}

/* Mobile-specific light mode */
body.light .bg-slate-900\/80,
body.light .bg-slate-900\/90 {
  background-color: rgba(255, 255, 255, 0.95) !important;
}

body.light .bg-slate-950\/90 {
  background-color: rgba(255, 255, 255, 0.95) !important;
}

body.light .bg-indigo-500\/20 {
  background-color: rgba(99, 102, 241, 0.15) !important;
}

body.light .border-indigo-500\/30 {
  border-color: rgba(99, 102, 241, 0.3) !important;
}

body.light .border-slate-800\/50 {
  border-color: #e2e8f0 !important;
}
</style>
