<script setup>
import { computed } from 'vue'
import { Star } from 'lucide-vue-next'

const props = defineProps({
  conversation: {
    type: Object,
    required: true
  },
  isActive: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['select'])

const otherParticipant = props.conversation.participants.find(p => p.id !== 'me')
const lastMsg = props.conversation.lastMessage

const hasAvatar = computed(() => {
  return otherParticipant?.avatar && !otherParticipant.avatar.includes('placeholder')
})

const initials = computed(() => {
  const name = otherParticipant?.name || ''
  const parts = name.trim().split(' ')
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  }
  return name.charAt(0).toUpperCase() || '?'
})

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div
    @click="emit('select')"
    :class="[
      'p-6 cursor-pointer transition-all border-l-2',
      isActive
        ? 'bg-indigo-500/10 border-indigo-500 shadow-[inset_10px_0_30px_rgba(99,102,241,0.05)]'
        : 'border-transparent hover:bg-white/[0.02]'
    ]"
  >
    <div class="flex gap-4 items-start">
      <div class="w-12 h-12 rounded-2xl overflow-hidden ring-1 ring-white/10 flex-shrink-0">
        <img
          v-if="hasAvatar"
          :src="otherParticipant.avatar"
          class="w-full h-full object-cover"
        />
        <div
          v-else
          class="w-full h-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-sm"
        >
          {{ initials }}
        </div>
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center justify-between mb-1">
          <h4 class="text-sm font-bold text-slate-50 truncate">{{ otherParticipant?.name }}</h4>
          <span class="text-[9px] font-black text-slate-400 uppercase">
            {{ formatDate(lastMsg?.timestamp) }}
          </span>
        </div>
        <p class="text-xs text-slate-400 line-clamp-2 leading-relaxed">
          <Star
            v-if="lastMsg?.isImportant"
            :size="10"
            class="inline mr-1 text-amber-500 fill-current"
          />
          {{ lastMsg?.content }}
        </p>
        <div
          v-if="conversation.unreadCount > 0"
          class="mt-2 w-2 h-2 rounded-full bg-indigo-500 shadow-[0_0_8px_#6366f1]"
        />
      </div>
    </div>
  </div>
</template>
