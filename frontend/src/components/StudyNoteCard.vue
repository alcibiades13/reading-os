<template>
  <div class="group glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-4 lg:p-6 hover:border-slate-700 transition-all duration-300">
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
        <span v-if="note.page_number" class="text-[10px] font-bold text-slate-600 flex items-center gap-1">
          p. {{ note.page_number }}
        </span>
        <span v-if="note.chapter" class="text-[10px] font-bold text-slate-600 flex items-center gap-1">
          Ch. {{ note.chapter }}
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

    <div class="relative">
      <div
        @mouseup="handleTextSelection"
        @click="handleClickOnContent"
        class="font-serif text-sm lg:text-lg text-slate-200 leading-relaxed mb-4 lg:mb-6 whitespace-pre-wrap select-text"
        v-html="contentWithHighlights"
      />

      <!-- Highlight Button Popup -->
      <Teleport to="body">
        <button
          v-if="showHighlightButton"
          data-highlight-btn
          @click.stop="applyHighlight"
          @mousedown.prevent
          :style="{
            position: 'fixed',
            left: `${highlightButtonPosition.x}px`,
            top: `${highlightButtonPosition.y}px`,
            transform: 'translateX(-50%)',
            zIndex: 9999
          }"
          class="px-3 py-1.5 rounded-lg bg-yellow-500 text-slate-900 font-bold text-xs shadow-2xl hover:bg-yellow-400 transition-all flex items-center gap-1.5"
        >
          <Highlighter :size="14" />
          Highlight
        </button>
      </Teleport>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import {
  MessageSquare,
  HelpCircle,
  Lightbulb,
  Quote as QuoteIcon,
  Trash2,
  Edit3,
  ArrowUpRight,
  Clock,
  Hash,
  Highlighter
} from 'lucide-vue-next'

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'promote', 'highlight', 'remove-highlight'])

const showHighlightButton = ref(false)
const highlightButtonPosition = ref({ x: 0, y: 0 })

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

const handleTextSelection = (event) => {
  // Small delay to ensure selection is complete
  setTimeout(() => {
    const selection = window.getSelection()
    const selectedText = selection.toString().trim()

    if (selectedText.length > 0) {
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()

      // Position button above the selection (fixed positioning, no scroll offset needed)
      highlightButtonPosition.value = {
        x: rect.left + rect.width / 2,
        y: rect.top - 45
      }
      showHighlightButton.value = true
    } else {
      showHighlightButton.value = false
    }
  }, 10)
}

const handleClickOutside = (event) => {
  // Hide highlight button if clicking outside the selection
  if (showHighlightButton.value && !event.target.closest('button[data-highlight-btn]')) {
    const selection = window.getSelection()
    if (!selection.toString().trim()) {
      showHighlightButton.value = false
    }
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})

const applyHighlight = () => {
  const selection = window.getSelection()
  const selectedText = selection.toString().trim()

  console.log('applyHighlight - props.note:', props.note)
  console.log('applyHighlight - props.note.id:', props.note.id)

  if (selectedText.length > 0) {
    emit('highlight', {
      noteId: props.note.id,
      text: selectedText,
      startOffset: selection.anchorOffset,
      endOffset: selection.focusOffset
    })
  }

  showHighlightButton.value = false
  selection.removeAllRanges()
}

const handleClickOnContent = (event) => {
  // Check if clicked element is a remove highlight button
  const button = event.target.closest('[data-remove-highlight]')
  if (button) {
    event.preventDefault()
    event.stopPropagation()

    const highlightText = button.getAttribute('data-highlight-text')
    console.log('handleClickOnContent - button clicked')
    console.log('handleClickOnContent - highlightText:', highlightText)
    console.log('handleClickOnContent - props.note:', props.note)
    console.log('handleClickOnContent - props.note.id:', props.note.id)
    if (highlightText) {
      emit('remove-highlight', {
        noteId: props.note.id,
        text: highlightText
      })
    }

    // Clear any text selection that might have been made
    window.getSelection().removeAllRanges()
    showHighlightButton.value = false
  }
}

const contentWithHighlights = computed(() => {
  if (!props.note.highlights || props.note.highlights.length === 0) {
    return props.note.content
  }

  let content = props.note.content

  // Sort highlights by the order they appear in the text
  const highlights = [...props.note.highlights].sort((a, b) => {
    const indexA = content.indexOf(a.text)
    const indexB = content.indexOf(b.text)
    return indexB - indexA // Process from end to start to preserve positions
  })

  // Replace each highlighted text with marked version and remove button
  highlights.forEach((highlight) => {
    // Escape special regex characters in the text
    const escapedText = highlight.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(escapedText, 'g')

    // Escape highlight text for HTML attribute
    const escapedForAttr = highlight.text.replace(/"/g, '&quot;')

    // Only replace if not already highlighted
    const highlightHTML = `<mark class="bg-yellow-400/30 px-0.5 rounded highlight-text group" style="display: inline;">${highlight.text}<sup><button data-remove-highlight data-highlight-text="${escapedForAttr}" class="opacity-0 group-hover:opacity-100 ml-0.5 w-3 h-3 bg-red-500/90 hover:bg-red-600 rounded-full text-white text-[8px] leading-none transition-all" style="display: inline-block; vertical-align: super;" title="Remove highlight">×</button></sup></mark>`

    if (!content.includes(highlightHTML)) {
      content = content.replace(regex, highlightHTML)
    }
  })

  return content
})
</script>
