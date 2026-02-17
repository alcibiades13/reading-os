<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { X, Save, Type, Book, BookOpen, AlignLeft, Hash, Star, Globe, Lock, Plus } from 'lucide-vue-next'
import { userBooksAPI } from '@/services/api'

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
const selectedBookId = ref(props.word?.bookId || props.initialBook?.id || null)
const pageNumber = ref(props.word?.pageNumber || null)
const isFavorite = ref(props.word?.isFavorite || false)
const isPublic = ref(props.word?.isPublic ?? true)
const tagsInput = ref(props.word?.tags?.join(', ') || '')

const wordRef = ref(null)

// Book search
const bookSearchResults = ref([])
const showBookDropdown = ref(false)
const isSearchingBooks = ref(false)
let searchTimeout = null

const searchBooks = async (query) => {
  if (!query || query.length < 2) {
    bookSearchResults.value = []
    showBookDropdown.value = false
    return
  }
  isSearchingBooks.value = true
  try {
    const response = await userBooksAPI.list({ search: query })
    bookSearchResults.value = response.data.results || response.data || []
    showBookDropdown.value = bookSearchResults.value.length > 0
  } catch (error) {
    console.error('Error searching books:', error)
    bookSearchResults.value = []
  } finally {
    isSearchingBooks.value = false
  }
}

const handleBookInput = (e) => {
  bookTitle.value = e.target.value
  selectedBookId.value = null
  bookAuthor.value = ''
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => searchBooks(e.target.value), 300)
}

const selectBook = (userBook) => {
  selectedBookId.value = userBook.book.id
  bookTitle.value = userBook.book.title
  bookAuthor.value = userBook.book.authors?.[0]?.name || ''
  showBookDropdown.value = false
}

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
    bookId: selectedBookId.value,
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
    if (showBookDropdown.value) {
      showBookDropdown.value = false
      return
    }
    emit('close')
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-[110] flex items-end lg:items-center justify-center lg:p-4 bg-slate-950/90 light:bg-white/90 backdrop-blur-md animate-in fade-in duration-300"
    @keydown="handleKeyDown"
    @click.self="emit('close')"
  >
    <div class="relative w-full lg:max-w-2xl glass light:bg-white light:border light:border-slate-200 rounded-t-2xl lg:rounded-[2.5rem] overflow-hidden shadow-2xl flex flex-col max-h-[92vh] lg:max-h-[90vh] animate-in slide-in-from-bottom lg:zoom-in-95 duration-300">

      <!-- Header -->
      <div class="flex items-center justify-between p-4 lg:p-8 border-b border-slate-800 light:border-slate-200 bg-slate-900/50 light:bg-slate-50">
        <div class="flex items-center gap-3 lg:gap-4">
          <div class="w-9 h-9 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shadow-lg shadow-emerald-500/5">
            <Type :size="18" class="lg:w-6 lg:h-6 text-emerald-400" />
          </div>
          <div>
            <h2 class="text-base lg:text-xl font-black text-white light:text-slate-900">{{ word ? 'Edit Word' : 'Add Word' }}</h2>
            <p class="text-[9px] lg:text-[10px] uppercase font-black tracking-wider lg:tracking-widest text-slate-500 light:text-slate-600">Add to your lexicon</p>
          </div>
        </div>
        <button @click="emit('close')" class="p-2 lg:p-2.5 rounded-full hover:bg-slate-800 light:hover:bg-slate-200 text-slate-400 light:text-slate-600 transition-colors">
          <X :size="20" />
        </button>
      </div>

      <!-- Form Content -->
      <div class="flex-1 overflow-y-auto p-4 lg:p-10 custom-scrollbar space-y-5 lg:space-y-10" @click="showBookDropdown = false">
        <!-- Main Word -->
        <div class="space-y-2 lg:space-y-4">
          <label class="text-[9px] lg:text-[10px] font-black text-slate-500 light:text-slate-600 uppercase tracking-wider lg:tracking-widest flex items-center gap-2">
            <Type :size="12" class="lg:w-3.5 lg:h-3.5 text-emerald-400" /> The Word
          </label>
          <input
            ref="wordRef"
            required
            type="text"
            v-model="wordText"
            placeholder="e.g. Mellifluous"
            class="w-full bg-slate-800/20 light:bg-white border-2 border-slate-800 light:border-slate-200 rounded-xl lg:rounded-2xl px-4 lg:px-6 py-3 lg:py-4 text-xl lg:text-3xl font-serif text-white light:text-slate-900 placeholder-slate-700 light:placeholder-slate-400 focus:border-emerald-500/50 transition-all outline-none"
          />
        </div>

        <!-- Context & Definition -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-8">
          <div class="space-y-2 lg:space-y-4">
            <label class="text-[9px] lg:text-[10px] font-black text-slate-500 light:text-slate-600 uppercase tracking-wider lg:tracking-widest flex items-center gap-2">
              <AlignLeft :size="12" class="lg:w-3.5 lg:h-3.5" /> Context / Sentence
            </label>
            <textarea
              v-model="context"
              placeholder="Where did you find it?"
              class="w-full h-20 lg:h-28 bg-slate-800/20 light:bg-white border-2 border-slate-800 light:border-slate-200 rounded-xl lg:rounded-2xl p-3 lg:p-4 text-sm text-slate-300 light:text-slate-900 placeholder-slate-700 light:placeholder-slate-400 focus:border-emerald-500/50 transition-all outline-none resize-none"
            />
          </div>
          <div class="space-y-2 lg:space-y-4">
            <label class="text-[9px] lg:text-[10px] font-black text-slate-500 light:text-slate-600 uppercase tracking-wider lg:tracking-widest flex items-center gap-2">
              <Plus :size="12" class="lg:w-3.5 lg:h-3.5" /> Your Definition
            </label>
            <textarea
              v-model="definition"
              placeholder="What does it mean to you?"
              class="w-full h-20 lg:h-28 bg-slate-800/20 light:bg-white border-2 border-slate-800 light:border-slate-200 rounded-xl lg:rounded-2xl p-3 lg:p-4 text-sm text-slate-300 light:text-slate-900 placeholder-slate-700 light:placeholder-slate-400 focus:border-emerald-500/50 transition-all outline-none resize-none"
            />
          </div>
        </div>

        <!-- Metadata -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-3 lg:gap-8">
          <div class="space-y-2 lg:space-y-4 relative">
            <label class="text-[9px] lg:text-[10px] font-black text-slate-500 light:text-slate-600 uppercase tracking-wider lg:tracking-widest flex items-center gap-2">
              <Book :size="12" class="lg:w-3.5 lg:h-3.5" /> Source Book
            </label>
            <input
              type="text"
              :value="bookTitle"
              @input="handleBookInput"
              @focus="showBookDropdown = bookSearchResults.length > 0"
              placeholder="Search your books or type manually..."
              autocomplete="off"
              class="w-full bg-slate-800/20 light:bg-white border-2 border-slate-800 light:border-slate-200 rounded-xl px-3 lg:px-4 py-2.5 lg:py-3 text-sm text-slate-100 light:text-slate-900 placeholder-slate-700 light:placeholder-slate-400 focus:border-emerald-500/50 transition-all outline-none"
            />
            <!-- Book Search Dropdown -->
            <div
              v-if="showBookDropdown && bookSearchResults.length > 0"
              class="absolute z-50 w-full mt-1 bg-slate-800 light:bg-white border-2 border-slate-700 light:border-slate-200 rounded-xl shadow-2xl max-h-48 overflow-y-auto"
            >
              <button
                v-for="userBook in bookSearchResults"
                :key="userBook.id"
                type="button"
                @click="selectBook(userBook)"
                class="w-full flex items-center gap-3 p-2.5 hover:bg-slate-700 light:hover:bg-slate-100 transition-colors text-left border-b border-slate-700/50 light:border-slate-200/50 last:border-0"
              >
                <div class="w-7 h-10 rounded overflow-hidden flex-shrink-0 bg-slate-700 light:bg-slate-200 flex items-center justify-center">
                  <img
                    v-if="userBook.book.cover_image"
                    :src="userBook.book.cover_image"
                    :alt="userBook.book.title"
                    class="w-full h-full object-cover"
                  />
                  <BookOpen v-else :size="12" class="text-slate-500" />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-white light:text-slate-900 truncate">{{ userBook.book.title }}</p>
                  <p class="text-xs text-slate-400 light:text-slate-500 truncate">{{ userBook.book.authors?.[0]?.name || 'Unknown Author' }}</p>
                </div>
              </button>
            </div>
            <p v-if="isSearchingBooks" class="text-[10px] text-slate-500 mt-1">Searching...</p>
            <p v-if="selectedBookId && bookAuthor" class="text-[10px] text-emerald-400 mt-1">{{ bookAuthor }}</p>
          </div>
          <div class="space-y-2 lg:space-y-4">
            <label class="text-[9px] lg:text-[10px] font-black text-slate-500 light:text-slate-600 uppercase tracking-wider lg:tracking-widest flex items-center gap-2">
              <Hash :size="12" class="lg:w-3.5 lg:h-3.5" /> Page
            </label>
            <input
              type="number"
              v-model.number="pageNumber"
              placeholder="Page..."
              class="w-full bg-slate-800/20 light:bg-white border-2 border-slate-800 light:border-slate-200 rounded-xl px-3 lg:px-4 py-2.5 lg:py-3 text-sm text-slate-100 light:text-slate-900 placeholder-slate-700 light:placeholder-slate-400 focus:border-emerald-500/50 transition-all outline-none"
            />
          </div>
        </div>

        <!-- Toggles -->
        <div class="flex flex-wrap gap-2 lg:gap-4">
          <button
            type="button"
            @click="isFavorite = !isFavorite"
            :class="[
              'flex items-center gap-2 lg:gap-3 px-4 lg:px-6 py-2.5 lg:py-3 rounded-xl border-2 transition-all',
              isFavorite ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' : 'border-slate-800 text-slate-600'
            ]"
          >
            <Star :size="16" class="lg:w-[18px] lg:h-[18px]" :fill="isFavorite ? 'currentColor' : 'none'" />
            <span class="text-[10px] lg:text-xs font-black uppercase tracking-wider lg:tracking-widest">Favorite</span>
          </button>
          <button
            type="button"
            @click="isPublic = !isPublic"
            :class="[
              'flex items-center gap-2 lg:gap-3 px-4 lg:px-6 py-2.5 lg:py-3 rounded-xl border-2 transition-all',
              isPublic ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-800 text-slate-600'
            ]"
          >
            <Globe v-if="isPublic" :size="16" class="lg:w-[18px] lg:h-[18px]" />
            <Lock v-else :size="16" class="lg:w-[18px] lg:h-[18px]" />
            <span class="text-[10px] lg:text-xs font-black uppercase tracking-wider lg:tracking-widest">{{ isPublic ? 'Public' : 'Private' }}</span>
          </button>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-4 lg:p-8 border-t border-slate-800 light:border-slate-200 bg-slate-900/50 light:bg-slate-50 flex gap-3 lg:gap-4 safe-area-bottom">
        <button
          @click="handleSubmit(true)"
          type="button"
          class="px-4 lg:px-6 py-3 lg:py-4 rounded-xl lg:rounded-2xl border border-slate-700 light:border-slate-300 text-slate-300 light:text-slate-700 font-bold lg:font-black text-[10px] lg:text-xs uppercase tracking-wider lg:tracking-widest hover:bg-slate-800 light:hover:bg-slate-200 transition-all"
        >
          <span class="hidden lg:inline">Save & Add Another</span>
          <span class="lg:hidden">+ Another</span>
        </button>
        <button
          @click="handleSubmit(false)"
          type="button"
          class="flex-1 lg:flex-none flex items-center justify-center gap-2 lg:gap-3 px-6 lg:px-10 py-3 lg:py-4 rounded-xl lg:rounded-2xl bg-emerald-500 text-white font-bold lg:font-black text-xs uppercase tracking-wider lg:tracking-widest shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
        >
          <Save :size="18" class="lg:w-5 lg:h-5" />
          <span class="hidden lg:inline">Capture Entry</span>
          <span class="lg:hidden">Save</span>
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

/* Safe area for bottom nav */
.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

@media (min-width: 1024px) {
  .safe-area-bottom {
    padding-bottom: 2rem;
  }
}

/* Mobile slide-in animation */
@keyframes slide-in-from-bottom {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.slide-in-from-bottom {
  animation: slide-in-from-bottom 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
</style>
