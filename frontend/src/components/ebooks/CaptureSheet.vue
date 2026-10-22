<script setup>
import { ref, computed, onMounted } from 'vue'
import { Quote, Brain, NotebookPen, X, Loader2, Sparkles } from 'lucide-vue-next'
import { ebooksAPI } from '@/services/api'
import { cleanWord } from '@/utils/textContext'
import { useOfflineSyncStore, isNetworkError } from '@/stores/offlineSyncStore'

/**
 * Turns text selected in the reader into a Quote, a Vocabulary word or a Study note,
 * saved together with its place in the book (shown as a highlight). Works offline:
 * the capture is queued and sent when the connection returns.
 */
const props = defineProps({
  mode: { type: String, required: true }, // 'quote' | 'word' | 'note'
  selection: { type: Object, required: true }, // { text, context, cfi?, page? }
  ebook: { type: Object, required: true },
  pageNumber: { type: Number, default: null },
  chapter: { type: String, default: '' },
  theme: { type: Object, required: true },
})

const emit = defineEmits(['close', 'saved'])
const sync = useOfflineSyncStore()

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
const suggesting = ref(false)
const suggestError = ref('')
const suggested = ref(false)
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

// What the word means in this sentence (Gemini) - a suggestion the user can edit
const suggestDefinition = async (auto = false) => {
  if (!word.value.trim() || suggesting.value) return
  suggesting.value = true
  suggestError.value = ''
  try {
    const { data } = await ebooksAPI.define(word.value.trim(), context.value.trim())
    // The automatic suggestion never overwrites what the user started typing
    if (!auto || !definition.value.trim()) {
      definition.value = data.definition
      suggested.value = true
    }
  } catch (err) {
    suggestError.value = isNetworkError(err)
      ? 'Suggestions need a connection - type the meaning yourself.'
      : err?.response?.data?.detail || 'Could not suggest a definition.'
  } finally {
    suggesting.value = false
  }
}

onMounted(() => {
  // Put the cursor where the user has to type
  if (props.mode === 'word') {
    definitionInput.value?.focus()
    if (sync.online) suggestDefinition(true)
  }
  if (props.mode === 'note') {
    const el = noteInput.value
    el?.focus()
    el?.setSelectionRange(el.value.length, el.value.length)
  }
})

const buildData = () => {
  const page = props.pageNumber || null
  const chapter = reference.value.trim().slice(0, 100)
  if (props.mode === 'quote') {
    return { text: quoteText.value.trim(), note: quoteNote.value.trim(), chapter, page_number: page }
  }
  if (props.mode === 'word') {
    return { word: word.value.trim(), definition: definition.value.trim(), context: context.value.trim(), page_number: page }
  }
  return {
    note_type: noteType.value,
    content: noteContent.value.trim(),
    reference: (chapter || (page ? `Page ${page}` : props.ebook.title)).slice(0, 255),
    page_number: page,
    chapter,
  }
}

// Shown as a highlight right away, even before the server has it
const localAnnotation = (clientId, data, position) => ({
  id: `local-${clientId}`,
  kind: props.mode,
  position,
  text: props.selection.text,
  title: props.mode === 'word' ? data.word : props.mode === 'quote' ? 'Quote' : 'Note',
  body: props.mode === 'word' ? data.definition : props.mode === 'quote' ? data.note : data.content,
  reference: data.reference || data.chapter || '',
  pending: true,
})

const save = async () => {
  if (!canSave.value || saving.value) return
  saving.value = true
  error.value = ''
  const clientId = crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`
  const position = props.selection.cfi || String(props.selection.page || props.pageNumber || '')
  const data = buildData()
  const body = { kind: props.mode, data, position, text: props.selection.text, client_id: clientId }
  try {
    const result = await sync.run(
      () => ebooksAPI.capture(props.ebook.id, body),
      { method: 'post', url: `/ebooks/${props.ebook.id}/capture/`, data: body },
    )
    if (result.queued) {
      emit('saved', { kind: props.mode, queued: true, annotation: localAnnotation(clientId, data, position) })
    } else {
      emit('saved', { kind: props.mode, annotation: result.data.annotation, ebook: result.data.ebook })
    }
  } catch (err) {
    const detail = err?.response?.data
    const inner = detail?.data && typeof detail.data === 'object' ? detail.data : detail
    const first = inner && typeof inner === 'object' ? Object.values(inner)[0] : null
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
      <div class="relative">
        <textarea
          ref="definitionInput"
          v-model="definition"
          rows="3"
          @input="suggested = false"
          :placeholder="suggesting ? 'Looking up the meaning in this sentence…' : 'Definition / meaning *'"
          class="w-full rounded-xl px-3 py-2.5 pr-11 text-sm outline-none border focus:border-indigo-500 resize-none"
          :style="inputStyle"
        />
        <button
          type="button"
          class="absolute right-2 top-2 p-1.5 rounded-lg text-amber-400 hover:bg-amber-500/15 disabled:opacity-50"
          title="Suggest the meaning in this sentence"
          :disabled="suggesting || !word.trim()"
          @click="suggestDefinition()"
        >
          <Loader2 v-if="suggesting" :size="16" class="animate-spin" />
          <Sparkles v-else :size="16" />
        </button>
      </div>
      <p v-if="suggestError" class="text-[11px] -mt-2 text-amber-400">{{ suggestError }}</p>
      <p v-else-if="suggested && definition && !suggesting" class="text-[11px] -mt-2" :style="{ color: theme.muted }">Suggested by AI - check and edit before saving.</p>
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
