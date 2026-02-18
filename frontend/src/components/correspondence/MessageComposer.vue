<script setup>
import { ref, computed } from 'vue'
import { Send, Book, Quote as QuoteIcon, Brain, Star, X, Maximize2, Minimize2, ChevronUp, ChevronDown, PenLine } from 'lucide-vue-next'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useStudyNotesStore } from '@/stores/studyNotesStore'

const emit = defineEmits(['send'])

const booksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const studyNotesStore = useStudyNotesStore()

const messageText = ref('')
const isImportant = ref(false)
const attachments = ref([])
const showPicker = ref('none') // 'none' | 'book' | 'quote' | 'note'
const isExpanded = ref(false)
const isMinimized = ref(false)

const handleSend = () => {
  if (!messageText.value.trim() && attachments.value.length === 0) return

  emit('send', {
    content: messageText.value,
    attachments: attachments.value,
    isImportant: isImportant.value
  })

  // Reset
  messageText.value = ''
  attachments.value = []
  isImportant.value = false
  isExpanded.value = false
}

const addBookAttachment = (book) => {
  const attachment = {
    type: 'book',
    id: book.book.id,
    title: book.book.title,
    subtitle: book.book.authors?.[0]?.name || 'Unknown Author',
    image: book.book.cover_image
  }
  attachments.value.push(attachment)
  showPicker.value = 'none'
}

const addQuoteAttachment = (quote) => {
  const attachment = {
    type: 'quote',
    id: quote.id,
    title: 'Shared Quote',
    content: quote.text,
    subtitle: quote.book_title
  }
  attachments.value.push(attachment)
  showPicker.value = 'none'
}

const addNoteAttachment = (note) => {
  const attachment = {
    type: 'note',
    id: note.id,
    title: note.book_title || 'Study Note',
    content: note.content,
    subtitle: note.reference || note.note_type
  }
  attachments.value.push(attachment)
  showPicker.value = 'none'
}

const noteBookFilter = ref(null)

const noteBooks = computed(() => {
  const notes = studyNotesStore.notes || []
  const bookMap = new Map()
  notes.forEach(n => {
    if (n.book && n.book_title) {
      bookMap.set(n.book, n.book_title)
    }
  })
  return Array.from(bookMap, ([id, title]) => ({ id, title }))
})

const filteredNotes = computed(() => {
  const notes = studyNotesStore.notes || []
  if (!noteBookFilter.value) return notes
  return notes.filter(n => n.book === noteBookFilter.value)
})

const openNotePicker = async () => {
  showPicker.value = 'note'
  noteBookFilter.value = null
  if (!studyNotesStore.notes?.length) {
    await studyNotesStore.fetchNotes()
  }
}

const removeAttachment = (index) => {
  attachments.value.splice(index, 1)
}
</script>

<template>
  <div
    :class="[
      'border-t border-white/5 glass transition-all duration-300',
      isMinimized ? 'py-2 px-4' : 'px-4 py-3',
      isExpanded && !isMinimized ? 'h-[50vh]' : 'h-auto'
    ]"
  >
    <!-- Minimized State -->
    <div v-if="isMinimized" class="max-w-4xl mx-auto">
      <button
        @click="isMinimized = false"
        class="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white hover:border-indigo-500/30 transition-all"
      >
        <PenLine :size="14" />
        <span class="text-[10px] font-bold uppercase tracking-wider">Compose</span>
        <ChevronUp :size="14" />
      </button>
    </div>

    <!-- Expanded Composer -->
    <div v-else class="max-w-4xl mx-auto space-y-2">
      <!-- Attachment Preview Bar -->
      <div v-if="attachments.length > 0" class="flex flex-wrap gap-1.5">
        <div
          v-for="(attachment, idx) in attachments"
          :key="idx"
          class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-bold text-indigo-400"
        >
          <Book v-if="attachment.type === 'book'" :size="10" />
          <Brain v-else-if="attachment.type === 'note'" :size="10" />
          <QuoteIcon v-else :size="10" />
          <span class="truncate max-w-[100px]">{{ attachment.title }}</span>
          <button @click="removeAttachment(idx)" class="hover:text-indigo-300">
            <X :size="10" />
          </button>
        </div>
      </div>

      <!-- Textarea -->
      <div class="relative group">
        <textarea
          v-model="messageText"
          placeholder="Draft a thoughtful response..."
          :class="[
            'w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 focus:border-indigo-500 transition-all outline-none resize-none',
            isExpanded ? 'h-full' : 'h-20'
          ]"
        />
        <div class="absolute bottom-2 right-3 flex items-center gap-2">
          <button
            @click="isExpanded = !isExpanded"
            class="p-1.5 text-slate-600 hover:text-white transition-colors"
          >
            <Minimize2 v-if="isExpanded" :size="14" />
            <Maximize2 v-else :size="14" />
          </button>
        </div>
      </div>

      <!-- Action Bar -->
      <div class="flex items-center justify-between">
        <!-- Minimize button -->
        <button
          @click="isMinimized = true"
          class="p-1.5 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
          title="Minimize composer"
        >
          <ChevronDown :size="16" />
        </button>

        <div class="flex items-center gap-0.5 p-0.5 bg-white/5 rounded-xl border border-white/5">
          <!-- Attach Book -->
          <button
            @click="showPicker = 'book'"
            class="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
            title="Attach book"
          >
            <Book :size="14" />
          </button>

          <!-- Attach Quote -->
          <button
            @click="showPicker = 'quote'"
            class="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
            title="Attach quote"
          >
            <QuoteIcon :size="14" />
          </button>

          <!-- Attach Note -->
          <button
            @click="openNotePicker"
            class="p-2 rounded-lg text-slate-500 hover:text-white hover:bg-white/5 transition-all"
            title="Attach study note"
          >
            <Brain :size="14" />
          </button>

          <div class="w-px h-5 bg-white/10 mx-1" />

          <!-- Mark Important -->
          <button
            @click="isImportant = !isImportant"
            :class="[
              'p-2 rounded-lg transition-all',
              isImportant ? 'text-amber-400 bg-amber-400/10' : 'text-slate-500 hover:text-slate-300'
            ]"
            title="Mark important"
          >
            <Star :size="14" :fill="isImportant ? 'currentColor' : 'none'" />
          </button>
        </div>

        <!-- Send Button -->
        <button
          @click="handleSend"
          class="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all"
        >
          Send <Send :size="14" />
        </button>
      </div>
    </div>
  </div>

  <!-- Book Picker Modal -->
  <Teleport to="body">
    <div
      v-if="showPicker !== 'none'"
      class="fixed inset-0 z-[200] flex items-center justify-center p-8 bg-slate-950/90 backdrop-blur-xl"
    >
      <div class="w-full max-w-2xl glass rounded-[2.5rem] border-white/10 flex flex-col max-h-[80vh]">
        <div class="p-8 border-b border-white/5 flex items-center justify-between">
          <h3 class="text-xl font-black text-white">
            Select {{ showPicker === 'book' ? 'Volume' : showPicker === 'quote' ? 'Insight' : 'Study Note' }}
          </h3>
          <button
            @click="showPicker = 'none'"
            class="p-2 text-slate-500 hover:text-white transition-colors"
          >
            <X :size="24" />
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-8 grid grid-cols-2 gap-4 custom-scrollbar">
          <!-- Book Picker -->
          <div
            v-if="showPicker === 'book'"
            v-for="book in booksStore.books"
            :key="book.id"
            @click="addBookAttachment(book)"
            class="p-4 rounded-3xl bg-white/5 border border-white/10 hover:border-indigo-500 cursor-pointer transition-all flex gap-4"
          >
            <img
              :src="book.book.cover_image || 'https://via.placeholder.com/100x150'"
              class="w-12 h-18 rounded-lg object-cover"
            />
            <div class="min-w-0">
              <p class="text-sm font-bold text-white truncate">{{ book.book.title }}</p>
              <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">
                {{ book.book.authors?.[0]?.name || 'Unknown' }}
              </p>
            </div>
          </div>

          <!-- Quote Picker -->
          <div
            v-else-if="showPicker === 'quote'"
            v-for="quote in quotesStore.quotes"
            :key="quote.id"
            @click="addQuoteAttachment(quote)"
            class="p-6 rounded-3xl bg-white/5 border border-white/10 hover:border-indigo-500 cursor-pointer transition-all italic font-serif text-slate-300"
          >
            "{{ quote.text.substring(0, 60) }}..."
            <p class="text-[9px] font-black uppercase tracking-widest text-indigo-400 mt-4">
              — {{ quote.book_title }}
            </p>
          </div>

          <!-- Note Picker -->
          <template v-else-if="showPicker === 'note'">
            <!-- Book Filter -->
            <div v-if="noteBooks.length > 1" class="col-span-2 mb-2">
              <div class="flex flex-wrap gap-1.5">
                <button
                  @click="noteBookFilter = null"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all',
                    !noteBookFilter
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'
                  ]"
                >
                  All Books
                </button>
                <button
                  v-for="book in noteBooks"
                  :key="book.id"
                  @click="noteBookFilter = book.id"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all truncate max-w-[180px]',
                    noteBookFilter === book.id
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'
                  ]"
                >
                  {{ book.title }}
                </button>
              </div>
            </div>

            <div v-if="studyNotesStore.loading" class="col-span-2 text-center py-8 text-slate-500 text-sm">
              Loading notes...
            </div>
            <div v-else-if="!filteredNotes.length" class="col-span-2 text-center py-8 text-slate-500 text-sm">
              {{ noteBookFilter ? 'No notes for this book' : 'No study notes yet' }}
            </div>
            <div
              v-else
              v-for="note in filteredNotes"
              :key="note.id"
              @click="addNoteAttachment(note)"
              class="p-4 rounded-3xl bg-white/5 border border-white/10 hover:border-indigo-500 cursor-pointer transition-all"
            >
              <p class="text-sm text-slate-300 line-clamp-3 mb-3">{{ note.content }}</p>
              <div class="flex items-center gap-2">
                <span class="text-[9px] font-black uppercase tracking-widest text-emerald-400">{{ note.note_type }}</span>
                <span v-if="note.book_title" class="text-[9px] text-slate-600">|</span>
                <span v-if="note.book_title" class="text-[9px] font-bold text-slate-500 truncate">{{ note.book_title }}</span>
              </div>
              <p v-if="note.reference" class="text-[9px] text-slate-600 mt-1">{{ note.reference }}</p>
            </div>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,700;1,400&display=swap');

.font-serif {
  font-family: 'Crimson Pro', Georgia, serif;
}
</style>
