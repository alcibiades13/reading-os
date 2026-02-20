<script setup>
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { bookClubService } from '@/services/bookClubService'
import { Heart, Quote, Reply, Trash2, Pin, Pencil, Check, X, Lock as LockIcon } from 'lucide-vue-next'
import { useAuthStore } from '@/stores/authStore'
import PollCard from '@/components/social/PollCard.vue'

const circlesStore = useCirclesStore()
const authStore = useAuthStore()
const messagesContainerRef = ref(null)

const emit = defineEmits(['replyTo'])

// Reaction emoji map
const reactionEmojis = {
  heart: '\u2764\uFE0F',
  thumbsup: '\uD83D\uDC4D',
  fire: '\uD83D\uDD25',
  thinking: '\uD83E\uDD14',
  clap: '\uD83D\uDC4F',
  lightbulb: '\uD83D\uDCA1',
  book: '\uD83D\uDCDA',
  sparkles: '\u2728',
}

const showReactionPicker = ref(null)

function toggleReactionPicker(msgId) {
  showReactionPicker.value = showReactionPicker.value === msgId ? null : msgId
}

async function handleReaction(messageId, emoji) {
  showReactionPicker.value = null
  try {
    const result = await bookClubService.toggleReaction(messageId, emoji)
    const msg = circlesStore.messages.find(m => m.id === messageId)
    if (msg) {
      msg.reactions_summary = {
        counts: result.reactions,
        user_reactions: result.user_reactions,
      }
    }
  } catch (error) {
    console.error('Error toggling reaction:', error)
  }
}

async function handleDeleteMessage(messageId) {
  if (!confirm('Delete this message?')) return
  await circlesStore.deleteMessage(messageId)
}

// Inline edit
const editContent = ref('')

function startEdit(msg) {
  editContent.value = msg.content
  circlesStore.startEditing(msg.id)
}

function cancelEdit() {
  editContent.value = ''
  circlesStore.cancelEditing()
}

async function saveEdit(messageId) {
  if (!editContent.value.trim()) return
  await circlesStore.editMessage(messageId, editContent.value.trim())
  editContent.value = ''
}

const pinnedMessage = computed(() => circlesStore.messages.find(m => m.is_pinned))

async function handlePollVote(pollId, optionId) {
  await circlesStore.votePoll(pollId, optionId)
}

async function handleClosePoll(pollId) {
  if (!confirm('Close this poll? No more votes will be accepted.')) return
  await circlesStore.closePoll(pollId)
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainerRef.value) {
      messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
    }
  })
}

function formatTimeAgo(date) {
  return bookClubService.formatTimeAgo(date)
}

function getUserInitial(user) {
  return user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'
}

// Auto-scroll and polling
watch(() => circlesStore.activeTopicId, async (newId) => {
  if (newId) {
    await circlesStore.fetchTopicMessages(newId)
    scrollToBottom()
    circlesStore.startPolling(newId)
    circlesStore.markTopicRead(newId)
    // Fetch poll if topic is a polls category
    if (circlesStore.activeTopic?.category === 'polls') {
      circlesStore.fetchTopicPoll(newId)
    } else {
      circlesStore.activePoll = null
    }
  } else {
    circlesStore.stopPolling()
  }
})

watch(() => circlesStore.messages.length, () => {
  scrollToBottom()
})

onUnmounted(() => {
  circlesStore.stopPolling()
})

defineExpose({ scrollToBottom })
</script>

<template>
  <div class="flex-1 flex flex-col bg-slate-950/40 relative">
    <template v-if="circlesStore.activeTopic">
      <!-- Pinned message banner -->
      <div
        v-if="pinnedMessage"
        class="px-5 py-2.5 border-b border-amber-500/10 bg-amber-500/5 flex items-start gap-2.5 shrink-0"
      >
        <Pin :size="12" class="text-amber-400 shrink-0 mt-0.5" />
        <div class="min-w-0 flex-1">
          <span class="text-[9px] font-black text-amber-400 uppercase tracking-widest">Pinned</span>
          <p class="text-xs text-slate-300 line-clamp-1">{{ pinnedMessage.content }}</p>
          <span class="text-[9px] text-slate-500">— {{ pinnedMessage.author?.first_name }}</span>
        </div>
      </div>

      <!-- Messages -->
      <div ref="messagesContainerRef" class="flex-1 overflow-y-auto px-5 py-4 custom-scrollbar space-y-4">
        <div class="text-center py-4 opacity-30">
          <div class="h-px w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent mb-2" />
          <span class="text-[9px] font-black uppercase tracking-[0.4em] text-slate-500">Beginning of Discourse</span>
        </div>

        <!-- Poll (if this topic has one) -->
        <div v-if="circlesStore.activePoll" class="mb-2">
          <PollCard :poll="circlesStore.activePoll" @vote="handlePollVote" />
          <button
            v-if="circlesStore.isCircleAdmin && !circlesStore.activePoll.is_closed"
            @click="handleClosePoll(circlesStore.activePoll.id)"
            class="mt-2 text-[10px] font-bold text-slate-500 hover:text-rose-400 transition-colors"
          >
            Close Poll
          </button>
        </div>

        <div v-if="circlesStore.messages.length === 0" class="text-center py-8 text-slate-500 text-sm">
          No messages yet. Be the first to contribute!
        </div>

        <div v-for="msg in circlesStore.messages" :key="msg.id" class="flex gap-3 group">
          <div class="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-black text-[10px] shrink-0 overflow-hidden">
            <img v-if="msg.author?.avatar" :src="msg.author.avatar" class="w-full h-full object-cover" />
            <span v-else>{{ getUserInitial(msg.author) }}</span>
          </div>
          <div class="flex-1 min-w-0 space-y-1">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="text-xs font-black text-white">
                  {{ msg.author?.first_name }} {{ msg.author?.last_name }}
                </span>
                <span class="text-[9px] text-slate-600">
                  {{ formatTimeAgo(msg.created_at) }}
                </span>
                <span v-if="msg.is_edited" class="text-[9px] text-slate-600 italic">(edited)</span>
              </div>
              <!-- Action buttons on hover -->
              <div
                v-if="circlesStore.editingMessageId !== msg.id"
                class="flex items-center gap-0.5 opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity"
              >
                <button
                  @click="toggleReactionPicker(msg.id)"
                  class="p-1 rounded text-slate-600 hover:text-amber-400 hover:bg-white/5 transition-colors text-xs"
                  title="React"
                >
                  +&#x1F600;
                </button>
                <button
                  @click="$emit('replyTo', msg)"
                  class="p-1 rounded text-slate-600 hover:text-indigo-400 hover:bg-white/5 transition-colors"
                  title="Reply"
                >
                  <Reply :size="13" />
                </button>
                <button
                  @click="circlesStore.toggleMessageLike(msg.id)"
                  :class="['p-1 rounded transition-colors', msg.is_liked ? 'text-rose-400' : 'text-slate-600 hover:text-rose-400 hover:bg-white/5']"
                  title="Like"
                >
                  <Heart :size="13" :class="msg.is_liked ? 'fill-current' : ''" />
                </button>
                <button
                  v-if="circlesStore.isCircleAdmin"
                  @click="circlesStore.togglePinMessage(msg.id)"
                  :class="['p-1 rounded transition-colors', msg.is_pinned ? 'text-amber-400' : 'text-slate-600 hover:text-amber-400 hover:bg-white/5']"
                  :title="msg.is_pinned ? 'Unpin message' : 'Pin message'"
                >
                  <Pin :size="13" />
                </button>
                <button
                  v-if="msg.author?.id === authStore.user?.id"
                  @click="startEdit(msg)"
                  class="p-1 rounded text-slate-600 hover:text-indigo-400 hover:bg-white/5 transition-colors"
                  title="Edit"
                >
                  <Pencil :size="13" />
                </button>
                <button
                  v-if="msg.author?.id === authStore.user?.id"
                  @click="handleDeleteMessage(msg.id)"
                  class="p-1 rounded text-slate-600 hover:text-rose-400 hover:bg-white/5 transition-colors"
                  title="Delete"
                >
                  <Trash2 :size="13" />
                </button>
              </div>
            </div>

            <!-- Reply-to preview -->
            <div
              v-if="msg.reply_to_data"
              class="px-2.5 py-1.5 rounded-lg bg-white/5 border-l-2 border-indigo-500/40 text-xs cursor-pointer hover:bg-white/10 transition-colors"
            >
              <span class="text-indigo-400 font-bold">{{ msg.reply_to_data.author_name }}</span>
              <span class="text-slate-500 ml-1">{{ msg.reply_to_data.content_preview }}</span>
            </div>

            <!-- Message content -->
            <template v-if="circlesStore.editingMessageId === msg.id">
              <div class="space-y-2">
                <textarea
                  v-model="editContent"
                  @keydown.ctrl.enter="saveEdit(msg.id)"
                  @keydown.escape="cancelEdit"
                  class="w-full bg-white/5 border border-indigo-500/40 rounded-lg px-3 py-2 text-sm text-slate-100 focus:border-indigo-500 outline-none resize-none min-h-[60px]"
                  rows="3"
                />
                <div class="flex items-center gap-2">
                  <button
                    @click="saveEdit(msg.id)"
                    class="px-3 py-1 rounded-lg bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-600 transition-colors flex items-center gap-1"
                  >
                    <Check :size="12" /> Save
                  </button>
                  <button
                    @click="cancelEdit"
                    class="px-3 py-1 rounded-lg bg-white/5 text-slate-400 text-xs font-bold hover:bg-white/10 transition-colors flex items-center gap-1"
                  >
                    <X :size="12" /> Cancel
                  </button>
                  <span class="text-[9px] text-slate-600">ctrl+enter to save, esc to cancel</span>
                </div>
              </div>
            </template>
            <div v-else class="text-sm text-slate-300 leading-relaxed">
              {{ msg.content }}
            </div>

            <!-- Image attachment -->
            <div v-if="msg.attachment_image" class="mt-1">
              <img
                :src="msg.attachment_image"
                class="max-w-xs rounded-xl border border-white/10 cursor-pointer hover:opacity-90 transition-opacity"
                @click="() => globalThis.open(msg.attachment_image, '_blank')"
              />
            </div>

            <!-- Quote attachment -->
            <div
              v-if="msg.attached_quote_data"
              class="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center gap-3 mt-1 max-w-xs"
            >
              <Quote :size="12" class="text-indigo-500 shrink-0" />
              <div class="min-w-0">
                <p class="text-[9px] font-black text-indigo-400 uppercase tracking-widest">Shared Quote</p>
                <p class="text-xs text-slate-400 truncate italic">"{{ msg.attached_quote_data.content }}"</p>
              </div>
            </div>

            <!-- Reaction picker -->
            <div
              v-if="showReactionPicker === msg.id"
              class="flex items-center gap-0.5 p-1.5 rounded-lg bg-slate-800 border border-white/10 shadow-xl w-fit"
            >
              <button
                v-for="(emoji, key) in reactionEmojis"
                :key="key"
                @click="handleReaction(msg.id, key)"
                class="p-1 rounded hover:bg-white/10 transition-colors text-base"
                :title="key"
              >
                {{ emoji }}
              </button>
            </div>

            <!-- Reaction badges -->
            <div
              v-if="msg.reactions_summary?.counts && Object.keys(msg.reactions_summary.counts).length > 0"
              class="flex flex-wrap gap-1 mt-0.5"
            >
              <button
                v-for="(count, emoji) in msg.reactions_summary.counts"
                :key="emoji"
                @click="handleReaction(msg.id, emoji)"
                :class="[
                  'px-1.5 py-px rounded-full text-[11px] flex items-center gap-0.5 transition-colors',
                  msg.reactions_summary.user_reactions?.includes(emoji)
                    ? 'bg-indigo-500/20 border border-indigo-500/40 text-indigo-300'
                    : 'bg-white/5 border border-white/10 text-slate-400 hover:bg-white/10'
                ]"
              >
                {{ reactionEmojis[emoji] || emoji }} {{ count }}
              </button>
            </div>

            <!-- Like count badge -->
            <span v-if="msg.likes_count && !msg.reactions_summary?.counts?.heart" class="text-[11px] text-slate-500 flex items-center gap-1">
              <Heart :size="9" class="text-rose-400 fill-current" /> {{ msg.likes_count }}
            </span>
          </div>
        </div>

        <div class="h-8" />
      </div>
    </template>

    <!-- No Topic Selected -->
    <div v-else class="flex-1 flex flex-col items-center justify-center text-center p-12 opacity-30">
      <div class="w-16 h-16 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round" class="text-slate-600"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </div>
      <h3 class="text-lg font-black text-white uppercase tracking-widest mb-2">Select a Discourse</h3>
      <p class="max-w-xs text-sm text-slate-500">
        Join an ongoing discussion or start a new one.
      </p>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }
</style>
