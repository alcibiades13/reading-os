<template>
  <div class="fixed inset-0 z-[100] bg-slate-950 flex flex-col animate-in fade-in duration-500">
    <!-- Header -->
    <header class="h-20 border-b border-slate-900 flex items-center justify-between px-8 glass sticky top-0 z-20">
      <div class="flex items-center gap-6">
        <button @click="handleBack" class="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
          <ArrowLeft :size="24" />
        </button>
        <div class="h-8 w-px bg-slate-800" />
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Brain class="text-indigo-400" :size="20" />
          </div>
          <div>
            <h1 class="text-sm font-black text-white uppercase tracking-widest">{{ bookTitle }}</h1>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Study Mode Active</p>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="relative group">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-400 transition-colors" :size="16" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search notes..."
            class="bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />
        </div>
      </div>
    </header>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: References List -->
      <aside class="w-72 border-r border-slate-900 flex flex-col bg-slate-950">
        <div class="p-6">
          <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">References</h3>
          <button
            @click="selectedRef = null"
            :class="['w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all mb-2', !selectedRef ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:bg-slate-900']"
          >
            All References ({{ notes.length }})
          </button>
          <div class="space-y-1 overflow-y-auto max-h-[calc(100vh-250px)] custom-scrollbar">
            <button
              v-for="ref in references"
              :key="ref"
              @click="selectedRef = ref"
              :class="['w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all flex justify-between items-center', selectedRef === ref ? 'bg-slate-800 text-white' : 'text-slate-500 hover:bg-slate-900']"
            >
              <span class="truncate">{{ ref }}</span>
              <span class="text-[8px] bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800">
                {{ notes.filter(n => n.reference === ref).length }}
              </span>
            </button>
          </div>
        </div>
      </aside>

      <!-- Notes Surface -->
      <main class="flex-1 overflow-y-auto custom-scrollbar bg-slate-950/20 p-12">
        <div class="max-w-[1800px] mx-auto space-y-8">
          <!-- Type Filtering - Left aligned -->
          <div class="flex items-center gap-2">
            <button
              @click="activeType = 'all'"
              :class="['flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all', activeType === 'all' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
            >
              <LayoutGrid :size="14" />
              All
            </button>
            <button
              @click="activeType = 'quote'"
              :class="['flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all', activeType === 'quote' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
            >
              <QuoteIcon :size="14" />
              Quotes
            </button>
            <button
              @click="activeType = 'insight'"
              :class="['flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all', activeType === 'insight' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
            >
              <Lightbulb :size="14" />
              Insights
            </button>
            <button
              @click="activeType = 'question'"
              :class="['flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all', activeType === 'question' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
            >
              <HelpCircle :size="14" />
              Questions
            </button>
            <button
              @click="activeType = 'note'"
              :class="['flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all', activeType === 'note' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
            >
              <MessageSquare :size="14" />
              Notes
            </button>
          </div>

          <!-- Two-column masonry grid -->
          <div v-if="filteredNotes.length > 0" class="columns-1 md:columns-2 gap-6 space-y-6">
            <StudyNoteCard
              v-for="note in filteredNotes"
              :key="note.id"
              :note="note"
              @edit="handleEdit"
              @delete="handleDelete"
              @promote="handlePromote"
              class="break-inside-avoid mb-6"
            />
          </div>
          <div v-else class="py-40 text-center">
            <div class="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-6 text-slate-700">
              <BookOpen :size="28" />
            </div>
            <h3 class="text-xl font-bold text-white mb-2">No notes here yet</h3>
            <p class="text-slate-500 text-sm">Start your study session using the capture bar below.</p>
          </div>
        </div>
      </main>
    </div>

    <!-- Quick Add Footer - Two rows -->
    <footer class="p-6 bg-slate-900/50 border-t border-slate-900 glass">
      <div class="max-w-5xl mx-auto space-y-3">
        <!-- Row 1: Type selector + Reference + Capture button -->
        <div class="flex items-center gap-4">
          <!-- Type selector -->
          <div class="flex items-center gap-1 p-1 bg-slate-950 rounded-xl border border-slate-800">
            <button
              @click="newNoteType = 'note'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'note' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <MessageSquare :size="12" />
              Note
            </button>
            <button
              @click="newNoteType = 'quote'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'quote' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <QuoteIcon :size="12" />
              Quote
            </button>
            <button
              @click="newNoteType = 'insight'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'insight' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <Lightbulb :size="12" />
              Insight
            </button>
            <button
              @click="newNoteType = 'question'"
              :class="['flex items-center gap-2 px-3 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all', newNoteType === 'question' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400']"
            >
              <HelpCircle :size="12" />
              Query
            </button>
          </div>

          <!-- Reference input - takes remaining space -->
          <input
            v-model="newNoteRef"
            type="text"
            placeholder="Reference (e.g. John 3:16, Romans 8:28)"
            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Capture button -->
          <button
            @click="handleSave"
            class="px-6 py-2 rounded-xl bg-indigo-500 text-white font-bold text-sm shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center gap-2 whitespace-nowrap"
          >
            Capture
            <Plus :size="18" />
          </button>
        </div>

        <!-- Row 2: Textarea full width -->
        <textarea
          v-model="newNoteContent"
          @keydown.meta.enter="handleSave"
          @keydown.ctrl.enter="handleSave"
          placeholder="What are you learning? (Cmd+Enter to save)"
          class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all resize-none"
          rows="4"
        />
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStudyNotesStore } from '@/stores/studyNotesStore'
import { useQuotesStore } from '@/stores/quotesStore'
import StudyNoteCard from '@/components/StudyNoteCard.vue'
import {
  ArrowLeft,
  Brain,
  Search,
  Plus,
  BookOpen,
  MessageSquare,
  HelpCircle,
  Lightbulb,
  Quote as QuoteIcon,
  LayoutGrid
} from 'lucide-vue-next'

const props = defineProps({
  bookId: {
    type: [String, Number],
    required: true
  },
  bookTitle: {
    type: String,
    default: 'Study Session'
  }
})

const router = useRouter()

const studyNotesStore = useStudyNotesStore()
const quotesStore = useQuotesStore()

const notes = computed(() => studyNotesStore.notes || [])
const searchQuery = ref('')
const selectedRef = ref(null)
const activeType = ref('all')
const newNoteContent = ref('')
const newNoteRef = ref('')
const newNoteType = ref('note')
const newNotePageNumber = ref('')
const newNoteChapter = ref('')

onMounted(async () => {
  await studyNotesStore.fetchNotes({ book: props.bookId })
  window.scrollTo(0, 0)
})

const references = computed(() => {
  const refs = new Set()

  notes.value.forEach(note => {
    // If backend sends references_list, use it; otherwise split by comma
    const refList = note.references_list || (note.reference ? note.reference.split(',').map(r => r.trim()) : ['General'])
    refList.forEach(ref => {
      if (ref) refs.add(ref)
    })
  })

  return Array.from(refs).sort()
})

const filteredNotes = computed(() => {
  let filtered = [...notes.value]

  if (selectedRef.value) {
    filtered = filtered.filter(n => {
      // Check if note contains the selected reference (supports multiple references)
      const refList = n.references_list || (n.reference ? n.reference.split(',').map(r => r.trim()) : [])
      return refList.includes(selectedRef.value)
    })
  }

  if (activeType.value !== 'all') {
    filtered = filtered.filter(n => n.note_type === activeType.value)
  }

  if (searchQuery.value) {
    const search = searchQuery.value.toLowerCase()
    filtered = filtered.filter(n =>
      n.content.toLowerCase().includes(search) ||
      n.reference?.toLowerCase().includes(search)
    )
  }

  return filtered
})

const handleSave = async () => {
  if (!newNoteContent.value.trim()) return

  const payload = {
    book: props.bookId,
    content: newNoteContent.value,
    reference: newNoteRef.value || 'General',
    note_type: newNoteType.value
  }

  const result = await studyNotesStore.createNote(payload)

  if (result.success) {
    newNoteContent.value = ''
    newNoteRef.value = ''
  }
}

const handleDelete = async (id) => {
  if (confirm('Delete study note?')) {
    await studyNotesStore.deleteNote(id)
  }
}

const handleEdit = (note) => {
  // TODO: Implement edit modal
  console.log('Edit note:', note)
}

const handlePromote = async (note) => {
  if (confirm('Promote this study note to a main quote?')) {
    const result = await studyNotesStore.promoteToQuote(note.id)
    if (result.success) {
      // Refresh quotes store to show new quote
      await quotesStore.fetchQuotes()
    }
  }
}

const handleBack = () => {
  router.push(`/books/${props.bookId}`)
}
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(51 65 85 / 0.5);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(51 65 85 / 0.8);
}

.glass {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
</style>
