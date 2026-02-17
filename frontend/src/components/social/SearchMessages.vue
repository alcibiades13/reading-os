<script setup>
import { ref, watch } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { bookClubService } from '@/services/bookClubService'
import { Search, X, MessageSquare } from 'lucide-vue-next'

const circlesStore = useCirclesStore()

const props = defineProps({
  show: Boolean,
})

const emit = defineEmits(['update:show', 'navigateToMessage'])

const query = ref('')
const results = ref([])
const searching = ref(false)
let debounceTimer = null

watch(() => props.show, (val) => {
  if (!val) {
    query.value = ''
    results.value = []
  }
})

function handleInput() {
  clearTimeout(debounceTimer)
  if (!query.value.trim() || query.value.length < 2) {
    results.value = []
    return
  }
  debounceTimer = setTimeout(doSearch, 400)
}

async function doSearch() {
  if (!query.value.trim() || !circlesStore.activeCircleId) return
  searching.value = true
  try {
    const data = await bookClubService.searchMessages(circlesStore.activeCircleId, query.value)
    results.value = data.results || data || []
  } catch (error) {
    console.error('Error searching messages:', error)
  } finally {
    searching.value = false
  }
}

function handleResultClick(message) {
  // Navigate to the topic and scroll to the message
  circlesStore.setActiveTopic(message.topic)
  emit('update:show', false)
}

function formatTimeAgo(date) {
  return bookClubService.formatTimeAgo(date)
}

function getUserInitial(user) {
  return user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'
}
</script>

<template>
  <Teleport to="body">
    <div v-if="show" class="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="$emit('update:show', false)" />
      <div class="relative w-full max-w-xl bg-slate-900 rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
        <!-- Search input -->
        <div class="p-4 border-b border-white/5">
          <div class="relative">
            <Search :size="18" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              v-model="query"
              @input="handleInput"
              type="text"
              autofocus
              placeholder="Search messages in this circle..."
              class="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-10 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors"
            />
            <button
              v-if="query"
              @click="query = ''; results = []"
              class="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-500 hover:text-white transition-colors"
            >
              <X :size="16" />
            </button>
          </div>
        </div>

        <!-- Results -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="searching" class="flex items-center justify-center py-10">
            <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>

          <div v-else-if="results.length > 0" class="p-2 space-y-1">
            <button
              v-for="msg in results"
              :key="msg.id"
              @click="handleResultClick(msg)"
              class="w-full text-left p-3 rounded-xl hover:bg-white/5 transition-colors"
            >
              <div class="flex items-start gap-3">
                <div class="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs shrink-0 overflow-hidden">
                  <img v-if="msg.author?.avatar" :src="msg.author.avatar" class="w-full h-full object-cover" />
                  <span v-else>{{ getUserInitial(msg.author) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-0.5">
                    <span class="text-xs font-bold text-white">{{ msg.author?.first_name }} {{ msg.author?.last_name }}</span>
                    <span class="text-[9px] text-slate-600">{{ formatTimeAgo(msg.created_at) }}</span>
                  </div>
                  <p class="text-sm text-slate-400 line-clamp-2">{{ msg.content }}</p>
                  <p v-if="msg.topic_title" class="text-[10px] text-slate-600 mt-1 flex items-center gap-1">
                    <MessageSquare :size="10" /> {{ msg.topic_title }}
                  </p>
                </div>
              </div>
            </button>
          </div>

          <div v-else-if="query.length >= 2 && !searching" class="text-center py-10 text-slate-500 text-sm">
            No messages found
          </div>

          <div v-else class="text-center py-10 text-slate-600 text-sm">
            Type to search messages...
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
