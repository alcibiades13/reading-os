<script setup>
import { ref } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { Send, Paperclip, X, Reply } from 'lucide-vue-next'

const circlesStore = useCirclesStore()

const messageInput = ref('')
const sendingMessage = ref(false)
const replyingTo = ref(null)
const fileInput = ref(null)

async function handleSendMessage() {
  if (!messageInput.value.trim() || !circlesStore.activeTopicId) return

  sendingMessage.value = true
  try {
    const data = {
      topic: circlesStore.activeTopicId,
      content: messageInput.value,
    }
    if (replyingTo.value) {
      data.reply_to = replyingTo.value.id
    }
    await circlesStore.sendMessage(data)
    messageInput.value = ''
    replyingTo.value = null
  } catch (error) {
    console.error('Error sending message:', error)
  } finally {
    sendingMessage.value = false
  }
}

function setReplyTo(message) {
  replyingTo.value = message
}

function cancelReply() {
  replyingTo.value = null
}

function handleFileClick() {
  fileInput.value?.click()
}

async function handleFileSelect(event) {
  const file = event.target.files?.[0]
  if (!file || !circlesStore.activeTopicId) return

  sendingMessage.value = true
  try {
    const formData = new FormData()
    formData.append('topic', circlesStore.activeTopicId)
    formData.append('content', messageInput.value || `Shared an image`)
    formData.append('attachment_image', file)
    if (replyingTo.value) {
      formData.append('reply_to', replyingTo.value.id)
    }

    const { default: api } = await import('@/services/api')
    const response = await api.post('/social/topic-messages/', formData)
    circlesStore.messages.push(response.data)
    circlesStore.lastMessageTimestamp = response.data.created_at
    messageInput.value = ''
    replyingTo.value = null
  } catch (error) {
    console.error('Error uploading file:', error)
  } finally {
    sendingMessage.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

defineExpose({ setReplyTo })
</script>

<template>
  <div v-if="circlesStore.activeTopic" class="px-3 lg:px-4 py-2 lg:py-3 border-t border-white/5 bg-slate-950/80 backdrop-blur-xl sticky bottom-0 safe-area-bottom">
    <!-- Reply preview bar -->
    <div
      v-if="replyingTo"
      class="mb-2 flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20"
    >
      <Reply :size="12" class="text-indigo-400 shrink-0" />
      <div class="flex-1 min-w-0">
        <span class="text-[11px] text-indigo-400 font-bold">{{ replyingTo.author?.first_name }}</span>
        <span class="text-[11px] text-slate-500 ml-1 truncate">{{ replyingTo.content?.substring(0, 60) }}{{ replyingTo.content?.length > 60 ? '...' : '' }}</span>
      </div>
      <button @click="cancelReply" class="p-1 rounded text-slate-500 hover:text-white transition-colors">
        <X :size="14" />
      </button>
    </div>

    <div class="flex items-end gap-2">
      <div class="flex-1 relative">
        <textarea
          v-model="messageInput"
          @keydown.ctrl.enter="handleSendMessage"
          :placeholder="'Message ' + circlesStore.activeTopic.title + '...'"
          class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:border-indigo-500 outline-none transition-all min-h-[40px] max-h-32 resize-none"
        />
        <div class="absolute right-2 bottom-2 flex items-center gap-1">
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            @change="handleFileSelect"
            class="hidden"
          />
          <button
            @click="handleFileClick"
            class="p-1.5 text-slate-500 hover:text-indigo-400 transition-colors"
            title="Attach image"
          >
            <Paperclip :size="16" />
          </button>
        </div>
      </div>
      <button
        @click="handleSendMessage"
        :disabled="!messageInput.trim() || sendingMessage"
        class="w-10 h-10 rounded-xl bg-indigo-500 text-white flex items-center justify-center hover:bg-indigo-600 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
      >
        <Send :size="16" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.safe-area-bottom {
  padding-bottom: max(0.5rem, env(safe-area-inset-bottom));
}
</style>
