<script setup>
import { useCirclesStore } from '@/stores/circlesStore'
import { bookClubService } from '@/services/bookClubService'
import { MessageSquare, Plus, Lock, Pin, Pencil, Trash2 } from 'lucide-vue-next'

const circlesStore = useCirclesStore()

const emit = defineEmits(['openCreateTopic', 'editTopic'])

function getCategoryClass(category) {
  return bookClubService.getCategoryInfo(category)?.color || 'bg-slate-500/20 text-slate-400'
}

function formatTimeAgo(date) {
  return bookClubService.formatTimeAgo(date)
}

function isRecentActivity(dateString) {
  if (!dateString) return false
  const date = new Date(dateString)
  const now = new Date()
  return (now - date) / (1000 * 60 * 60) < 24
}

async function togglePin(e, topicId) {
  e.stopPropagation()
  await circlesStore.togglePinTopic(topicId)
}

function handleEditTopic(e, topic) {
  e.stopPropagation()
  emit('editTopic', topic)
}

async function handleDeleteTopic(e, topicId) {
  e.stopPropagation()
  if (!confirm('Delete this topic and all its messages?')) return
  await circlesStore.deleteTopic(topicId)
}
</script>

<template>
  <div class="w-72 border-r border-white/5 flex flex-col bg-slate-950/20 shrink-0">
    <div class="px-3 py-2 flex items-center justify-between shrink-0 border-b border-white/[0.03]">
      <h3 class="text-[9px] font-black text-slate-500 uppercase tracking-widest">Discourses</h3>
      <button
        @click="$emit('openCreateTopic')"
        class="flex items-center gap-1 px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 text-[9px] font-black uppercase hover:bg-indigo-500/20 transition-colors"
      >
        <Plus :size="10" /> New
      </button>
    </div>
    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <div v-if="!circlesStore.activeCircle?.topics?.length" class="text-center py-8">
        <MessageSquare :size="24" class="text-slate-700 mx-auto mb-2" />
        <p class="text-slate-500 text-xs mb-3">No discussions yet</p>
        <button
          @click="$emit('openCreateTopic')"
          class="px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold hover:bg-indigo-500/20 transition-colors"
        >
          Start a Discussion
        </button>
      </div>
      <button
        v-for="topic in circlesStore.activeCircle?.topics"
        :key="topic.id"
        @click="circlesStore.setActiveTopic(topic.id)"
        :class="[
          'w-full text-left px-3 py-2.5 border-b border-white/[0.03] transition-all relative overflow-hidden group',
          circlesStore.activeTopicId === topic.id
            ? 'bg-indigo-500/10 border-l-2 border-l-indigo-500'
            : 'hover:bg-white/[0.04]'
        ]"
      >
        <!-- Lock overlay -->
        <div v-if="topic.is_locked && !topic.can_access" class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm z-10 flex items-center justify-center">
          <Lock :size="14" class="text-slate-500" />
        </div>
        <div class="relative z-0">
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center gap-1.5">
              <div :class="['px-1.5 py-px rounded text-[7px] font-black uppercase tracking-wider', getCategoryClass(topic.category)]">
                {{ topic.category }}
              </div>
              <Pin v-if="topic.is_pinned && !circlesStore.isCircleAdmin" :size="10" class="text-amber-400" />
              <button
                v-if="circlesStore.isCircleAdmin"
                @click="togglePin($event, topic.id)"
                :title="topic.is_pinned ? 'Unpin topic' : 'Pin topic'"
                :class="[
                  'p-0.5 rounded transition-all',
                  topic.is_pinned
                    ? 'text-amber-400 hover:text-amber-300'
                    : 'text-slate-600 opacity-0 group-hover:opacity-100 hover:text-amber-400'
                ]"
              >
                <Pin :size="10" />
              </button>
            </div>
            <div class="flex items-center gap-1.5">
              <div
                v-if="circlesStore.unreadCounts[topic.id]"
                class="px-1.5 py-px rounded-full bg-indigo-500 text-white text-[8px] font-black"
              >
                {{ circlesStore.unreadCounts[topic.id] }}
              </div>
              <div v-else-if="isRecentActivity(topic.last_activity)" class="w-1.5 h-1.5 rounded-full bg-indigo-500" />
              <span class="text-[9px] text-slate-600">{{ formatTimeAgo(topic.last_activity) }}</span>
            </div>
          </div>
          <h4 class="text-sm font-bold text-white mb-0.5 group-hover:text-indigo-400 transition-colors line-clamp-1">{{ topic.title }}</h4>
          <p v-if="topic.description" class="text-[11px] text-slate-500 line-clamp-1 mb-1">{{ topic.description }}</p>
          <div class="flex items-center justify-between">
            <span class="text-[9px] text-slate-600 flex items-center gap-1">
              <MessageSquare :size="9" /> {{ topic.message_count || 0 }} posts
            </span>
            <div v-if="circlesStore.isCircleAdmin" class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleEditTopic($event, topic)"
                class="p-0.5 rounded text-slate-600 hover:text-indigo-400 transition-colors"
                title="Edit topic"
              >
                <Pencil :size="10" />
              </button>
              <button
                @click="handleDeleteTopic($event, topic.id)"
                class="p-0.5 rounded text-slate-600 hover:text-rose-400 transition-colors"
                title="Delete topic"
              >
                <Trash2 :size="10" />
              </button>
            </div>
          </div>
        </div>
      </button>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }
</style>
