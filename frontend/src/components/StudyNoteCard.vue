<template>
  <div class="group glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 hover:border-slate-700 transition-all duration-300">
    <div class="flex items-start justify-between mb-4">
      <div class="flex items-center gap-3 flex-wrap">
        <div :class="['flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border', typeConfig.color]">
          <component :is="typeConfig.icon" :size="14" />
          {{ typeConfig.label }}
        </div>
        <template v-if="referencesList.length > 0">
          <span
            v-for="(ref, idx) in referencesList"
            :key="idx"
            class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1"
          >
            <Hash :size="10" /> {{ ref }}
          </span>
        </template>
        <span v-else class="text-[10px] font-bold text-slate-500 uppercase tracking-widest flex items-center gap-1">
          <Hash :size="10" /> {{ note.reference }}
        </span>
        <span class="text-[10px] font-bold text-slate-600 flex items-center gap-1">
          <Clock :size="10" />
          {{ formatDate(note.created_at) }}
        </span>
      </div>

      <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
        <button
          v-if="note.note_type === 'quote' && !note.is_promoted_to_quote"
          @click="$emit('promote', note)"
          title="Promote to Main Quote"
          class="p-2 rounded-lg hover:bg-indigo-500/10 text-slate-500 hover:text-indigo-400 transition-colors"
        >
          <ArrowUpRight :size="14" />
        </button>
        <button
          @click="$emit('edit', note)"
          class="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors"
        >
          <Edit3 :size="14" />
        </button>
        <button
          @click="$emit('delete', note.id)"
          class="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
        >
          <Trash2 :size="14" />
        </button>
      </div>
    </div>

    <div class="font-serif text-lg text-slate-200 leading-relaxed mb-6 whitespace-pre-wrap">
      {{ note.content }}
    </div>

    <div v-if="note.tags && note.tags.length > 0" class="flex flex-wrap gap-2">
      <span
        v-for="tag in note.tags"
        :key="tag.id"
        class="text-[10px] font-bold text-slate-500 hover:text-indigo-400 cursor-pointer transition-colors"
      >
        #{{ tag.name }}
      </span>
    </div>

    <div v-if="note.is_promoted_to_quote" class="pt-4 border-t border-slate-800/50 flex items-center gap-1.5 text-[10px] text-indigo-400 font-bold uppercase tracking-widest">
      <ArrowUpRight :size="12" />
      Promoted to Quote
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  MessageSquare,
  HelpCircle,
  Lightbulb,
  Quote as QuoteIcon,
  Trash2,
  Edit3,
  ArrowUpRight,
  Clock,
  Hash
} from 'lucide-vue-next'

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
})

defineEmits(['edit', 'delete', 'promote'])

const referencesList = computed(() => {
  // If backend sends references_list, use it; otherwise split by comma
  if (props.note.references_list && props.note.references_list.length > 0) {
    return props.note.references_list
  }
  if (props.note.reference) {
    return props.note.reference.split(',').map(r => r.trim()).filter(r => r)
  }
  return []
})

const typeConfig = computed(() => {
  const configs = {
    quote: {
      icon: QuoteIcon,
      color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
      label: 'Quote'
    },
    note: {
      icon: MessageSquare,
      color: 'text-slate-400 bg-slate-500/10 border-slate-500/20',
      label: 'Note'
    },
    question: {
      icon: HelpCircle,
      color: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
      label: 'Question'
    },
    insight: {
      icon: Lightbulb,
      color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
      label: 'Insight'
    }
  }
  return configs[props.note.note_type] || configs.note
})

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString()
}
</script>
