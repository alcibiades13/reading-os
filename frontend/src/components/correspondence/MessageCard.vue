<script setup>
import { Star, Book, Quote as QuoteIcon, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  message: {
    type: Object,
    required: true
  },
  isMe: {
    type: Boolean,
    default: false
  }
})

const formatDateTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleString()
}
</script>

<template>
  <div :class="['flex flex-col max-w-3xl', isMe ? 'items-end ml-auto' : 'items-start']">
    <!-- Message Header -->
    <div :class="['flex items-center gap-3 mb-3', isMe ? 'flex-row-reverse' : '']">
      <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">
        {{ message.senderName }}
      </span>
      <span class="text-[9px] text-slate-700 font-bold">
        {{ formatDateTime(message.timestamp) }}
      </span>
      <span
        v-if="message.isImportant"
        class="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-[8px] font-black uppercase text-amber-500 tracking-widest"
      >
        <Star :size="10" fill="currentColor" /> Important Correspondence
      </span>
    </div>

    <!-- Message Card -->
    <div
      :class="[
        'p-4 rounded-2xl border w-full',
        isMe
          ? 'bg-white/[0.04] border-indigo-500/30 shadow-[0_20px_50px_rgba(0,0,0,0.4)]'
          : 'bg-slate-900/30 border-white/5 shadow-xl'
      ]"
    >
      <!-- Subject Line -->
      <h3
        v-if="message.subject"
        class="text-indigo-400 font-black uppercase tracking-[0.2em] text-[11px] mb-4 flex items-center gap-3"
      >
        <div class="w-1.5 h-1.5 rounded-full bg-indigo-500"></div>
        Subject: {{ message.subject }}
      </h3>

      <!-- Message Content -->
      <p class="text-sm text-slate-200 leading-relaxed mb-3 selection:bg-indigo-500/30">
        {{ message.content }}
      </p>

      <!-- Attachments -->
      <div v-if="message.attachments && message.attachments.length > 0" class="space-y-4 pt-6 border-t border-white/5">
        <div
          v-for="(attachment, i) in message.attachments"
          :key="i"
        >
          <!-- Book Attachment -->
          <div
            v-if="attachment.type === 'book'"
            class="flex items-center gap-6 p-6 rounded-3xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all group"
          >
            <div class="w-16 h-24 rounded-xl overflow-hidden shadow-2xl group-hover:scale-105 transition-transform duration-500 ring-1 ring-white/10">
              <img :src="attachment.image" class="w-full h-full object-cover" />
            </div>
            <div class="flex-1">
              <p class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-2 flex items-center gap-2">
                <Book :size="12" /> Volume Recommendation
              </p>
              <h4 class="text-lg font-black text-white tracking-tight">{{ attachment.title }}</h4>
              <p class="text-xs text-slate-500 font-bold">{{ attachment.subtitle }}</p>
              <button class="mt-4 px-6 py-2 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-white hover:bg-white/10 transition-all flex items-center gap-2">
                View Entry <ChevronRight :size="12" />
              </button>
            </div>
          </div>

          <!-- Quote Attachment -->
          <div
            v-else-if="attachment.type === 'quote'"
            class="p-8 rounded-3xl bg-white/[0.02] border border-white/5 italic font-serif text-slate-300 relative group overflow-hidden"
          >
            <div class="absolute top-0 right-0 p-6 opacity-[0.05] group-hover:scale-110 transition-transform">
              <QuoteIcon :size="64" />
            </div>
            <p class="text-lg leading-relaxed relative z-10">"{{ attachment.content }}"</p>
            <p class="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400 mt-6 relative z-10">
              — {{ attachment.subtitle }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&display=swap');

.font-serif {
  font-family: 'Crimson Pro', Georgia, serif;
}
</style>
