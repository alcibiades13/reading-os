<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { correspondenceService } from '@/services/correspondenceService'
import { useUserBooksStore } from '@/stores/userBooksStore'
import ConversationListItem from '@/components/correspondence/ConversationListItem.vue'
import MessageCard from '@/components/correspondence/MessageCard.vue'
import MessageComposer from '@/components/correspondence/MessageComposer.vue'
import {
  MessageSquare, Search, Plus, Star, Inbox,
  MoreHorizontal
} from 'lucide-vue-next'

const booksStore = useUserBooksStore()

const conversations = ref([])
const activeConvId = ref(null)
const messages = ref([])
const searchQuery = ref('')

onMounted(async () => {
  await loadConversations()
  await booksStore.fetchBooks()
})

const loadConversations = async () => {
  conversations.value = await correspondenceService.getConversations()
}

const loadMessages = async (convId) => {
  messages.value = await correspondenceService.getMessages(convId)
}

watch(activeConvId, async (newId) => {
  if (newId) {
    await loadMessages(newId)
  }
})

const activeConv = computed(() =>
  conversations.value.find(c => c.id === activeConvId.value)
)

const otherParticipant = computed(() =>
  activeConv.value?.participants.find(p => p.id !== 'me')
)

const handleSelectConversation = (convId) => {
  activeConvId.value = convId
}

const handleSendMessage = async (messageData) => {
  if (!activeConvId.value) return

  const sent = await correspondenceService.sendMessage(activeConvId.value, messageData)
  messages.value.push(sent)

  // Scroll to bottom
  setTimeout(() => {
    const timeline = document.querySelector('.message-timeline')
    if (timeline) {
      timeline.scrollTop = timeline.scrollHeight
    }
  }, 100)
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
          <button class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all">
            <Plus :size="16" />
          </button>
        </div>
        <div class="relative group">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" :size="14" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Filter peer discussions..."
            class="w-full bg-white/5 border border-slate-800/50 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-50 outline-none focus:border-indigo-500 transition-all"
          />
        </div>
      </div>

      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <ConversationListItem
          v-for="conv in conversations"
          :key="conv.id"
          :conversation="conv"
          :isActive="activeConvId === conv.id"
          @select="handleSelectConversation(conv.id)"
        />
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
        <div class="flex-1 overflow-y-auto p-12 custom-scrollbar space-y-12 message-timeline">
          <MessageCard
            v-for="msg in messages"
            :key="msg.id"
            :message="msg"
            :isMe="msg.senderId === 'me'"
          />
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
