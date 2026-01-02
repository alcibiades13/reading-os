<template>
  <div class="fixed inset-0 z-[100] bg-slate-950 flex flex-col animate-in fade-in duration-500">
    <!-- Header -->
    <header class="h-16 md:h-20 border-b border-slate-900 flex items-center justify-between px-4 md:px-8 glass sticky top-0 z-20">
      <div class="flex items-center gap-3 md:gap-6 min-w-0 flex-1">
        <button @click="handleBack" class="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors flex-shrink-0">
          <ArrowLeft :size="20" class="md:hidden" />
          <ArrowLeft :size="24" class="hidden md:block" />
        </button>
        <div class="h-6 md:h-8 w-px bg-slate-800 flex-shrink-0" />
        <div class="flex items-center gap-2 md:gap-3 min-w-0">
          <div class="w-8 h-8 md:w-10 md:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center flex-shrink-0">
            <Brain class="text-indigo-400" :size="16" />
          </div>
          <div class="min-w-0">
            <h1 class="text-xs md:text-sm font-black text-white uppercase tracking-widest truncate">{{ bookTitle }}</h1>
            <p class="text-[9px] md:text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] hidden md:block">Study Mode Active</p>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 md:gap-4 flex-shrink-0">
        <button @click="showSearch = !showSearch" class="md:hidden p-2 rounded-lg hover:bg-slate-800 text-slate-400 transition-colors">
          <Search :size="18" />
        </button>
        <div class="relative group hidden md:block">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600 group-focus-within:text-indigo-400 transition-colors" :size="16" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search notes..."
            class="bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all w-48"
          />
        </div>
      </div>
    </header>

    <!-- Mobile Search Bar -->
    <div v-if="showSearch" class="md:hidden p-4 border-b border-slate-900 bg-slate-950">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" :size="16" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search notes..."
          class="w-full bg-slate-900/50 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
        />
      </div>
    </div>

    <!-- Main Workspace -->
    <div class="flex-1 flex overflow-hidden">
      <!-- Sidebar: References List - Hidden on mobile, shown as drawer -->
      <aside :class="['border-r border-slate-900 flex flex-col bg-slate-950 transition-transform duration-300 z-10', showReferences ? 'fixed inset-y-0 left-0 w-64 md:w-72 shadow-2xl' : 'hidden md:flex md:w-72']">
        <div class="p-4 md:p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">References</h3>
            <button @click="showReferences = false" class="md:hidden p-1 rounded-lg hover:bg-slate-800 text-slate-500">
              <X :size="16" />
            </button>
          </div>
          <button
            @click="selectedRef = null; showReferences = false"
            :class="['w-full text-left px-4 py-3 rounded-xl text-xs font-bold transition-all mb-2', !selectedRef ? 'bg-indigo-500 text-white' : 'text-slate-400 hover:bg-slate-900']"
          >
            All References ({{ notes.length }})
          </button>
          <div class="space-y-1 overflow-y-auto max-h-[calc(100vh-200px)] custom-scrollbar">
            <button
              v-for="ref in references"
              :key="ref"
              @click="selectedRef = ref; showReferences = false"
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

      <!-- Backdrop for mobile drawer -->
      <div v-if="showReferences" @click="showReferences = false" class="md:hidden fixed inset-0 bg-black/50 z-[5]"></div>

      <!-- Notes Surface -->
      <main class="flex-1 overflow-y-auto custom-scrollbar bg-slate-950/20 p-4 md:p-8 lg:p-12">
        <div class="max-w-[1800px] mx-auto space-y-6 md:space-y-8">
          <!-- Mobile Reference Toggle + Type Filtering -->
          <div class="space-y-3">
            <!-- Mobile reference toggle button -->
            <button
              @click="showReferences = true"
              class="md:hidden w-full flex items-center justify-between px-4 py-3 rounded-xl bg-slate-900 border border-slate-800 text-sm font-bold text-white hover:bg-slate-800 transition-all"
            >
              <div class="flex items-center gap-2">
                <Filter :size="16" />
                <span>{{ selectedRef || 'All References' }}</span>
              </div>
              <span class="text-[10px] bg-slate-800 px-2 py-1 rounded border border-slate-700">
                {{ filteredNotes.length }}
              </span>
            </button>

            <!-- Type Filtering - Wrap on mobile -->
            <div class="flex items-center gap-2 flex-wrap">
              <button
                @click="activeType = 'all'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'all' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <LayoutGrid :size="12" class="md:hidden" />
                <LayoutGrid :size="14" class="hidden md:block" />
                All
              </button>
              <button
                @click="activeType = 'quote'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'quote' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <QuoteIcon :size="12" class="md:hidden" />
                <QuoteIcon :size="14" class="hidden md:block" />
                Quotes
              </button>
              <button
                @click="activeType = 'insight'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'insight' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <Lightbulb :size="12" class="md:hidden" />
                <Lightbulb :size="14" class="hidden md:block" />
                Insights
              </button>
              <button
                @click="activeType = 'question'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'question' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <HelpCircle :size="12" class="md:hidden" />
                <HelpCircle :size="14" class="hidden md:block" />
                Questions
              </button>
              <button
                @click="activeType = 'note'"
                :class="['flex items-center gap-1.5 px-3 md:px-4 py-1.5 md:py-2 rounded-xl text-[10px] md:text-xs font-bold transition-all', activeType === 'note' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/10' : 'text-slate-500 hover:text-slate-300']"
              >
                <MessageSquare :size="12" class="md:hidden" />
                <MessageSquare :size="14" class="hidden md:block" />
                Notes
              </button>
            </div>
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

    <!-- Quick Add Footer - Responsive -->
    <footer class="p-3 md:p-6 bg-slate-900/50 border-t border-slate-900 glass">
      <div class="max-w-5xl mx-auto space-y-3">
        <!-- Desktop Layout: Type selector + Reference + Page + Chapter + Capture -->
        <div class="hidden md:flex items-center gap-4">
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

          <!-- Reference input -->
          <input
            v-model="newNoteRef"
            type="text"
            placeholder="Reference (e.g. John 3:16, Romans 8:28)"
            class="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Page Number input -->
          <input
            v-model="newNotePageNumber"
            type="number"
            placeholder="Page"
            class="w-20 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Chapter input -->
          <input
            v-model="newNoteChapter"
            type="text"
            placeholder="Chapter"
            class="w-28 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
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

        <!-- Mobile Layout: Stacked -->
        <div class="md:hidden space-y-2">
          <!-- Type selector - Wrap instead of scroll -->
          <div class="flex items-center gap-1 flex-wrap">
            <button
              @click="newNoteType = 'note'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'note' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <MessageSquare :size="10" />
              Note
            </button>
            <button
              @click="newNoteType = 'quote'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'quote' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <QuoteIcon :size="10" />
              Quote
            </button>
            <button
              @click="newNoteType = 'insight'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'insight' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <Lightbulb :size="10" />
              Insight
            </button>
            <button
              @click="newNoteType = 'question'"
              :class="['flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[8px] font-black uppercase tracking-widest transition-all', newNoteType === 'question' ? 'bg-slate-800 text-white' : 'text-slate-600 bg-slate-950']"
            >
              <HelpCircle :size="10" />
              Query
            </button>
          </div>

          <!-- Reference full width -->
          <input
            v-model="newNoteRef"
            type="text"
            placeholder="Reference (e.g. John 3:16)"
            class="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
          />

          <!-- Page + Chapter + Capture button row -->
          <div class="flex items-center gap-2">
            <input
              v-model="newNotePageNumber"
              type="number"
              placeholder="Page"
              class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
            />
            <input
              v-model="newNoteChapter"
              type="text"
              placeholder="Chapter"
              class="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 transition-all"
            />
          </div>
        </div>

        <!-- Textarea - Full width on all screens -->
        <textarea
          v-model="newNoteContent"
          @keydown.meta.enter="handleSave"
          @keydown.ctrl.enter="handleSave"
          placeholder="What are you learning?"
          class="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 md:px-4 py-2 md:py-2.5 text-xs md:text-sm text-white outline-none focus:border-indigo-500 transition-all resize-none"
          :rows="5"
        />

        <!-- Mobile Capture button -->
        <button
          @click="handleSave"
          class="md:hidden w-full py-2 rounded-xl bg-indigo-500 text-white font-bold text-xs shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all flex items-center justify-center gap-2"
        >
          <Plus :size="16" />
          Capture
        </button>
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
  LayoutGrid,
  Filter,
  X
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
const showSearch = ref(false)
const showReferences = ref(false)

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
    note_type: newNoteType.value,
    page_number: newNotePageNumber.value ? parseInt(newNotePageNumber.value) : null,
    chapter: newNoteChapter.value || null
  }

  const result = await studyNotesStore.createNote(payload)

  if (result.success) {
    newNoteContent.value = ''
    newNoteRef.value = ''
    newNotePageNumber.value = ''
    newNoteChapter.value = ''
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

.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
</style>
