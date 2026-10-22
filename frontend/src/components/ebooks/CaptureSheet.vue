<script setup>
import { ref, computed, onMounted } from 'vue'
import { Quote, Brain, NotebookPen, X, Loader2 } from 'lucide-vue-next'
import { ebooksAPI, quotesAPI, vocabularyAPI, studyNotesAPI } from '@/services/api'
import { cleanWord } from '@/utils/textContext'

/**
 * Turns text selected in the reader into a Quote, a Vocabulary word or a Study note,
 * linked to the e-book's catalog book.
 */
const props = defineProps({
  mode: { type: String, required: true }, // 'quote' | 'word' | 'note'
  selection: { type: Object, required: true }, // { text, context }
  ebook: { type: Object, required: true },
  pageNumber: { type: Number, default: null },
  chapter: { type: String, default: '' },
  theme: { type: Object, required: true },
})

const emit = defineEmits(['close', 'saved', 'ebook-updated'])

const NOTE_TYPES = [
  { id: 'note', label: 'Note' },
  { id: 'insight', label: 'Insight' },
  { id: 'question', label: 'Question' },
  { id: 'quote', label: 'Passage' },
]

const saving = ref(false)
const error = ref('')

// Quote
const quoteText = ref(props.selection.text)
const quoteNote = ref('')
// Word
const word = ref(cleanWord(props.selection.text).slice(0, 200))
const definition = ref('')
const context = ref(props.selection.context)
// Where in the book - detected chapter, editable (e.g. add a verse: "Matej 7:12")
const reference = ref(props.chapter || (props.pageNumber ? `Page ${props.pageNumber}` : ''))
// Note
const noteType = ref('note')
const noteContent = ref(`"${props.selection.text}"\n\n`)

const definitionInput = ref(null)
const noteInput = ref(null)

const META = {
  quote: { title: 'Save quote', icon: Quote, color: 'text-indigo-400 bg-indigo-500/15' },
  word: { title: 'Add to vocabulary', icon: Brain, color: 'text-amber-400 bg-amber-500/15' },
  note: { title: 'Study note', icon: NotebookPen, color: 'text-sky-400 bg-sky-500/15' },
}
const meta = computed(() => META[props.mode])

const canSave = computed(() => {
  if (props.mode === 'quote') return quoteText.value.trim().length > 0
  if (props.mode === 'word') return word.value.trim() && definition.value.trim()
  return noteContent.value.trim().length > 0
})

const inputStyle = computed(() => ({
  background: `${props.theme.muted}1a`,
  borderColor: `${props.theme.muted}40`,
  color: props.theme.fg,
}))

onMounted(() => {
  // Put the cursor where the user has to type
  if (props.mode === 'word') definitionInput.value?.focus()
  if (props.mode === 'note') {
    const el = noteInput.value
    el?.focus()
    el?.setSelectionRange(el.value.length, el.value.length)
  }
})

// Quotes, notes and words belong to a catalog book - link the file on first capture
const ensureCatalogBook = async () => {
  if (props.ebook.book_detail) return props.ebook
  const { data } = await ebooksAPI.linkCatalog(props.ebook.id)
  emit('ebook-updated', data)
  return data
}

const save = async () => {
  if (!canSave.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    const ebook = await ensureCatalogBook()
    const book = ebook.book_detail
    const common = {
      book: book.id,
      book_title: book.title || ebook.title,
      book_author: (book.authors || []).join(', ') || ebook.author,
      page_number: props.pageNumber || null,
    }
    const chapter = reference.value.trim().slice(0, 100)

    if (props.mode === 'quote') {
      await quotesAPI.create({
        ...common,
        user_book: ebook.library_entry?.id || null,
        text: quoteText.value.trim(),
        note: quoteNote.value.trim(),
        chapter,
      })
    } else if (props.mode === 'word') {
      await vocabularyAPI.create({
        ...common,
        word: word.value.trim(),
        definition: definition.value.trim(),
        context: context.value.trim(),
      })
    } else {
      await studyNotesAPI.create({
        book: book.id,
        user_book: ebook.library_entry?.id || null,
        note_type: noteType.value,
        content: noteContent.value.trim(),
        reference: (reference.value.trim() || (props.pageNumber ? `Page ${props.pageNumber}` : ebook.title)).slice(0, 255),
        page_number: props.pageNumber || null,
        chapter,
      })
    }
    emit('saved', props.mode)
  } catch (err) {
    const data = err?.response?.data
    const first = data && typeof data === 'object' ? Object.values(data)[0] : null
    error.value = (Array.isArray(first) ? first[0] : first) || 'Could not save. Please try again.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div
    class="rounded-t-2xl sm:rounded-2xl border shadow-2xl p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:pb-5 space-y-4 max-h-[80vh] overflow-y-auto"
    :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
    @click.stop
  >
    <div class="flex items-center gap-3">
      <div :class="['w-9 h-9 shrink-0 rounded-xl flex items-center justify-center', meta.color]">
        <component :is="meta.icon" :size="18" />
      </div>
      <p class="flex-1 font-bold">{{ meta.title }}</p>
      <button class="p-2 rounded-lg hover:opacity-70" @click="emit('close')"><X :size="18" /></button>
    </div>

    <!-- QUOTE -->
    <template v-if="mode === 'quote'">
      <textarea
        v-model="quoteText"
        rows="4"
        class="w-full rounded-xl px-3 py-2.5 text-sm font-serif italic leading-relaxed outline-none border focus:border-indigo-500 resize-none"
        :style="inputStyle"
      />
      <textarea
        v-model="quoteNote"
        rows="2"
        placeholder="Your thoughts (optional)"
        class="w-full rounded-xl px-3 py-2.5 text-sm outline-none border focus:border-indigo-500 resize-none"
        :style="inputStyle"
      />
    </template>

    <!-- WORD -->
    <template v-else-if="mode === 'word'">
      <input
        v-model="word"
        maxlength="200"
        class="w-full rounded-xl px-3 py-2.5 text-lg font-serif font-bold outline-none border focus:border-indigo-500"
        :style="inputStyle"
      />
      <textarea
        ref="definitionInput"
        v-model="definition"
        rows="2"
        placeholder="Definition / meaning *"
        class="w-full rounded-xl px-3 py-2.5 text-sm outline-none border focus:border-indigo-500 resize-none"
        :style="inputStyle"
      />
      <div>
        <p class="text-[10px] font-black uppercase tracking-widest mb-1.5" :style="{ color: theme.muted }">Context</p>
        <textarea
          v-model="context"
          rows="3"
          class="w-full rounded-xl px-3 py-2.5 text-sm font-serif italic leading-relaxed outline-none border focus:border-indigo-500 resize-none"
          :style="inputStyle"
        />
      </div>
    </template>

    <!-- NOTE -->
    <template v-else>
      <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
        <button
          v-for="type in NOTE_TYPES"
          :key="type.id"
          :class="['flex-1 py-1.5 rounded-lg text-xs font-bold transition-all', noteType === type.id ? 'bg-indigo-500 text-white' : 'opacity-70']"
          @click="noteType = type.id"
        >
          {{ type.label }}
        </button>
      </div>
      <textarea
        ref="noteInput"
        v-model="noteContent"
        rows="6"
        class="w-full rounded-xl px-3 py-2.5 text-sm leading-relaxed outline-none border focus:border-indigo-500 resize-none"
        :style="inputStyle"
      />
    </template>

    <!-- Where in the book (quotes and notes) -->
    <div v-if="mode !== 'word'">
      <p class="text-[10px] font-black uppercase tracking-widest mb-1.5" :style="{ color: theme.muted }">
        {{ mode === 'note' ? 'Reference' : 'Chapter' }}
      </p>
      <input
        v-model="reference"
        maxlength="100"
        :placeholder="mode === 'note' ? 'e.g. Matej 7:12' : 'e.g. Chapter 7'"
        class="w-full rounded-xl px-3 py-2 text-sm outline-none border focus:border-indigo-500"
        :style="inputStyle"
      />
    </div>

    <p class="text-[11px]" :style="{ color: theme.muted }">
      {{ ebook.book_detail?.title || ebook.title }}<template v-if="mode === 'word' && chapter"> · {{ chapter }}</template><template v-if="pageNumber"> · p. {{ pageNumber }}</template>
    </p>

    <p v-if="error" class="text-sm text-red-400">{{ error }}</p>

    <div class="flex gap-2">
      <button class="flex-1 py-2.5 rounded-xl text-sm font-bold border" :style="{ borderColor: `${theme.muted}40` }" @click="emit('close')">
        Cancel
      </button>
      <button
        class="flex-1 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 text-white disabled:opacity-40 flex items-center justify-center gap-2"
        :disabled="!canSave || saving"
        @click="save"
      >
        <Loader2 v-if="saving" :size="14" class="animate-spin" />
        Save
      </button>
    </div>
  </div>
</template>
