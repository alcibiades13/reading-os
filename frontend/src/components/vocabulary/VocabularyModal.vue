<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { X, Save, Type, Book, AlignLeft, Hash, Star, Globe, Lock, Plus } from 'lucide-vue-next'

const props = defineProps({
  word: {
    type: Object,
    default: null
  },
  initialBook: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close', 'save'])

const wordText = ref(props.word?.word || '')
const definition = ref(props.word?.definition || '')
const context = ref(props.word?.context || '')
const bookTitle = ref(props.word?.bookTitle || props.initialBook?.title || '')
const bookAuthor = ref(props.word?.bookAuthor || props.initialBook?.authors?.[0]?.name || '')
const pageNumber = ref(props.word?.pageNumber || null)
const isFavorite = ref(props.word?.isFavorite || false)
const isPublic = ref(props.word?.isPublic ?? true)
const tagsInput = ref(props.word?.tags?.join(', ') || '')

const wordRef = ref(null)

onMounted(async () => {
  await nextTick()
  wordRef.value?.focus()
})

const handleSubmit = (addAnother = false) => {
  if (!wordText.value.trim()) return

  const payload = {
    id: props.word?.id,
    word: wordText.value,
    definition: definition.value,
    context: context.value,
    bookTitle: bookTitle.value,
    bookAuthor: bookAuthor.value,
    bookId: props.word?.bookId || props.initialBook?.id,
    pageNumber: pageNumber.value,
    isFavorite: isFavorite.value,
    isPublic: isPublic.value,
    tags: tagsInput.value.split(',').map(t => t.trim()).filter(t => t !== '')
  }

  emit('save', payload, addAnother)

  if (addAnother) {
    wordText.value = ''
    definition.value = ''
    context.value = ''
    tagsInput.value = ''
    nextTick(() => wordRef.value?.focus())
  }
}

const handleKeyDown = (e) => {
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
    handleSubmit(false)
  }
  if (e.key === 'Escape') {
    emit('close')
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-[110] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md animate-in fade-in duration-300"
    @keydown="handleKeyDown"
  >
    <div class="relative w-full max-w-2xl glass rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-300">

      <!-- Header -->
      <div class="flex items-center justify-between p-8 border-b border-slate-800 bg-slate-900/50">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-lg shadow-emerald-500/5">
            <Type :size="24" class="text-emerald-400" />
          </div>
          <div>
            <h2 class="text-xl font-black text-white">{{ word ? 'Edit Word' : 'Capture Vocabulary' }}</h2>
            <p class="text-[10px] uppercase font-black tracking-widest text-slate-500">Add to your lexicon</p>
          </div>
        </div>
        <button @click="emit('close')" class="p-2.5 rounded-full hover:bg-slate-800 text-slate-400 transition-colors">
          <X :size="20" />
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-10">
        <!-- Main Word -->
        <div class="space-y-4">
          <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
            <Type :size="14" class="text-emerald-400" /> The Word
          </label>
          <input
            ref="wordRef"
            required
            type="text"
            v-model="wordText"
            placeholder="e.g. Mellifluous"
            class="w-full bg-slate-800/20 border-2 border-slate-800 rounded-2xl px-6 py-4 text-3xl font-serif text-white placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none"
          />
        </div>

        <!-- Context & Definition -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-4">
            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <AlignLeft :size="14" /> Context / Sentence
            </label>
            <textarea
              v-model="context"
              placeholder="Where did you find it?"
              class="w-full h-28 bg-slate-800/20 border-2 border-slate-800 rounded-2xl p-4 text-sm text-slate-300 placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none resize-none"
            />
          </div>
          <div class="space-y-4">
            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Plus :size="14" /> Your Definition
            </label>
            <textarea
              v-model="definition"
              placeholder="What does it mean to you?"
              class="w-full h-28 bg-slate-800/20 border-2 border-slate-800 rounded-2xl p-4 text-sm text-slate-300 placeholder-slate-700 focus:border-emerald-500/50 transition-all outline-none resize-none"
            />
          </div>
        </div>

        <!-- Metadata -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="space-y-4">
            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Book :size="14" /> Source Book
            </label>
            <input
              type="text"
              v-model="bookTitle"
              placeholder="Title..."
              class="w-full bg-slate-800/20 border-2 border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:border-emerald-500/50 transition-all outline-none"
            />
          </div>
          <div class="space-y-4">
            <label class="text-[10px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-2">
              <Hash :size="14" /> Page
            </label>
            <input
              type="number"
              v-model.number="pageNumber"
              placeholder="Page number..."
              class="w-full bg-slate-800/20 border-2 border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 focus:border-emerald-500/50 transition-all outline-none"
            />
          </div>
        </div>

        <!-- Toggles -->
        <div class="flex flex-wrap gap-4">
          <button
            type="button"
            @click="isFavorite = !isFavorite"
            :class="[
              'flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all',
              isFavorite ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' : 'border-slate-800 text-slate-600'
            ]"
          >
            <Star :size="18" :fill="isFavorite ? 'currentColor' : 'none'" />
            <span class="text-xs font-black uppercase tracking-widest">Favorite</span>
          </button>
          <button
            type="button"
            @click="isPublic = !isPublic"
            :class="[
              'flex items-center gap-3 px-6 py-3 rounded-xl border-2 transition-all',
              isPublic ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-800 text-slate-600'
            ]"
          >
            <Globe v-if="isPublic" :size="18" />
            <Lock v-else :size="18" />
            <span class="text-xs font-black uppercase tracking-widest">{{ isPublic ? 'Public' : 'Private' }}</span>
          </button>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-8 border-t border-slate-800 bg-slate-900/50 flex flex-wrap gap-4">
        <button
          @click="handleSubmit(true)"
          type="button"
          class="px-6 py-4 rounded-2xl border border-slate-700 text-slate-300 font-black text-xs uppercase tracking-widest hover:bg-slate-800 transition-all"
        >
          Save & Add Another
        </button>
        <div class="flex-1 min-w-0" />
        <button
          @click="handleSubmit(false)"
          type="button"
          class="flex items-center gap-3 px-10 py-4 rounded-2xl bg-emerald-500 text-white font-black text-xs uppercase tracking-widest shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
        >
          <Save :size="20" />
          Capture Entry
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(71 85 105 / 0.5);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105 / 0.7);
}
</style>
