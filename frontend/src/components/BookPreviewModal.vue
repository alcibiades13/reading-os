<script setup>
import { ref, computed } from 'vue'
import { X, Star, BookOpen, Calendar, Globe, Hash, Building2, Bookmark, PlayCircle, CheckCircle, Lightbulb, Library, Check, Edit3 } from 'lucide-vue-next'
import StarRating from '@/components/ui/StarRating.vue'

const props = defineProps({
  book: {
    type: Object,
    required: true,
  },
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'import'])

const selectedAction = ref(null)
const rating = ref(null)
const showFullDescription = ref(false)
const isEditMode = ref(false)

// Editable fields
const editableData = ref({
  title: props.book.title || '',
  authors: props.book.authors?.join(', ') || '',
  page_count: props.book.page_count || '',
  publisher: props.book.publisher || '',
  published_date: props.book.published_date || '',
  isbn_13: props.book.isbn_13 || '',
  cover_image_url: props.book.cover_image_url || '',
  description: props.book.description || '',
  language: props.book.language || 'en',
  categories: props.book.categories || []
})

const handleStatusToggle = (status) => {
  selectedAction.value = selectedAction.value === status ? null : status
  if (status !== 'read') rating.value = null
}

const handleImport = () => {
  const action = selectedAction.value
  const isLibraryAction = !!action

  // Use edited data instead of original book data
  const bookData = isEditMode.value ? {
    ...props.book,
    title: editableData.value.title,
    authors: editableData.value.authors.split(',').map(a => a.trim()).filter(a => a),
    page_count: editableData.value.page_count ? parseInt(editableData.value.page_count) : null,
    publisher: editableData.value.publisher,
    published_date: editableData.value.published_date,
    isbn_13: editableData.value.isbn_13,
    cover_image_url: editableData.value.cover_image_url,
    description: editableData.value.description,
    language: editableData.value.language,
    categories: editableData.value.categories
  } : props.book

  const payload = {
    book: bookData,
    addToLibrary: isLibraryAction,
    libraryData: isLibraryAction ? {
      status: action,
      rating: rating.value,
    } : null
  }
  emit('import', payload)
}

const handleClose = () => {
  emit('close')
}

const formattedDate = computed(() => {
  if (!props.book.published_date) return 'N/A'
  const date = new Date(props.book.published_date)
  if (isNaN(date.getTime())) return props.book.published_date.split('-')[0] || 'N/A'
  return date.getFullYear().toString()
})

const languageName = computed(() => {
  const langMap = {
    en: 'EN',
    sr: 'SR',
    fr: 'FR',
    de: 'DE',
    es: 'ES',
    it: 'IT',
    ru: 'RU',
  }
  return langMap[props.book.language] || props.book.language?.toUpperCase() || 'N/A'
})

const hasCover = computed(() => !!editableData.value.cover_image_url)

const truncatedDescription = computed(() => {
  if (!editableData.value.description) return ''
  const text = editableData.value.description.replace(/<[^>]*>/g, '') // Strip HTML tags
  const words = text.split(' ')
  if (words.length <= 100) return editableData.value.description
  return words.slice(0, 100).join(' ') + '...'
})
</script>

<template>
  <div class="fixed inset-0 z-[70] flex items-center justify-center p-4 md:p-6 pt-20 bg-slate-950/90 light:bg-white/90 backdrop-blur-sm animate-in fade-in duration-300">
    <div :class="['relative w-full max-w-5xl h-[85vh] glass light:bg-white light:border light:border-slate-200 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row animate-in zoom-in-95 duration-300', isEditMode ? 'ring-2 ring-indigo-500' : '']">

      <!-- Close Button -->
      <button
        @click="handleClose"
        class="absolute top-6 right-6 z-20 p-2 rounded-full bg-slate-900/50 light:bg-slate-200 hover:bg-slate-800 light:hover:bg-slate-300 text-slate-300 light:text-slate-700 transition-colors"
      >
        <X :size="20" />
      </button>

      <!-- Edit Toggle Button -->
      <button
        @click="isEditMode = !isEditMode"
        :class="[
          'absolute top-6 right-20 z-20 px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all',
          isEditMode ? 'bg-indigo-500 text-white' : 'bg-slate-900/50 light:bg-slate-200 hover:bg-slate-800 light:hover:bg-slate-300 text-slate-300 light:text-slate-700'
        ]"
      >
        <Edit3 :size="14" />
        {{ isEditMode ? 'View Mode' : 'Edit Details' }}
      </button>

      <!-- Left Column - Cover & Quick Stats -->
      <div class="w-full md:w-[40%] bg-slate-900/50 light:bg-slate-50 p-8 flex flex-col items-center overflow-y-auto border-r border-slate-700/30 light:border-slate-200">
        <div class="relative w-full max-w-[240px] aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10">
          <img
            v-if="hasCover"
            :src="editableData.cover_image_url"
            :alt="editableData.title"
            class="w-full h-full object-cover"
            @error="editableData.cover_image_url = ''"
          />
          <div v-else class="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
            <div class="w-24 h-24 rounded-full bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center mb-6">
              <BookOpen :size="40" class="text-indigo-500/40" />
            </div>
            <p class="text-slate-500 text-sm text-center">
              No cover available
            </p>
          </div>
          <div class="absolute inset-0 shadow-[inset_0_0_80px_rgba(0,0,0,0.4)]" />
        </div>

        <div class="w-full mt-8 space-y-4">
          <div class="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
            <Star class="text-amber-400" :size="20" fill="currentColor" />
            <div>
              <p class="text-xs text-slate-400 font-medium uppercase tracking-wider">Average Rating</p>
              <p class="text-slate-100 font-semibold">{{ book.average_rating ? `${book.average_rating}/5` : 'N/A' }}</p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div class="flex items-center gap-2 text-slate-500 mb-1">
                <BookOpen :size="16" />
                <span class="text-[10px] font-bold uppercase tracking-wider">Pages</span>
              </div>
              <input
                v-if="isEditMode"
                v-model="editableData.page_count"
                type="number"
                class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
                placeholder="Pages"
              />
              <p v-else class="text-slate-200 font-semibold truncate text-sm">{{ editableData.page_count || 'N/A' }}</p>
            </div>

            <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div class="flex items-center gap-2 text-slate-500 mb-1">
                <Globe :size="16" />
                <span class="text-[10px] font-bold uppercase tracking-wider">Language</span>
              </div>
              <input
                v-if="isEditMode"
                v-model="editableData.language"
                type="text"
                class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none uppercase"
                placeholder="EN"
              />
              <p v-else class="text-slate-200 font-semibold truncate text-sm">{{ languageName }}</p>
            </div>

            <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div class="flex items-center gap-2 text-slate-500 mb-1">
                <Calendar :size="16" />
                <span class="text-[10px] font-bold uppercase tracking-wider">Published</span>
              </div>
              <input
                v-if="isEditMode"
                v-model="editableData.published_date"
                type="text"
                class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
                placeholder="YYYY or YYYY-MM-DD"
              />
              <p v-else class="text-slate-200 font-semibold truncate text-sm">{{ formattedDate }}</p>
            </div>

            <div class="p-3 rounded-xl bg-slate-800/50 border border-slate-700/50">
              <div class="flex items-center gap-2 text-slate-500 mb-1">
                <Building2 :size="16" />
                <span class="text-[10px] font-bold uppercase tracking-wider">Publisher</span>
              </div>
              <input
                v-if="isEditMode"
                v-model="editableData.publisher"
                type="text"
                class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
                placeholder="Publisher"
              />
              <p v-else class="text-slate-200 font-semibold truncate text-sm">{{ editableData.publisher || 'N/A' }}</p>
            </div>
          </div>

          <div class="flex items-center gap-3 p-3 rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden">
            <Hash class="text-indigo-400 shrink-0" :size="16" />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-slate-400 font-medium uppercase tracking-wider">ISBN</p>
              <input
                v-if="isEditMode"
                v-model="editableData.isbn_13"
                type="text"
                class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
                placeholder="ISBN-13"
              />
              <p v-else class="text-slate-100 font-semibold truncate text-sm">{{ editableData.isbn_13 || 'N/A' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column - Details & Actions -->
      <div class="w-full md:w-[60%] flex flex-col h-full bg-slate-900/20 light:bg-white">
        <div :class="['flex-1 overflow-y-auto p-8 custom-scrollbar', isEditMode ? 'pt-24' : '']">
          <header class="mb-6">
            <div v-if="isEditMode" class="space-y-3">
              <div>
                <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-1 block">Title</label>
                <input
                  v-model="editableData.title"
                  type="text"
                  class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-2xl md:text-3xl font-bold text-white light:text-slate-900 focus:border-indigo-500 focus:outline-none"
                  placeholder="Book Title"
                />
              </div>
              <div>
                <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-1 block">Authors (comma-separated)</label>
                <input
                  v-model="editableData.authors"
                  type="text"
                  class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-lg text-indigo-400/80 light:text-indigo-600 font-medium focus:border-indigo-500 focus:outline-none"
                  placeholder="Author 1, Author 2"
                />
              </div>
              <div>
                <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-1 block">Cover Image URL</label>
                <input
                  v-model="editableData.cover_image_url"
                  type="text"
                  class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-sm text-slate-300 light:text-slate-900 focus:border-indigo-500 focus:outline-none"
                  placeholder="https://..."
                />
              </div>
            </div>
            <div v-else>
              <h1 class="text-2xl md:text-3xl font-bold text-white light:text-slate-900 leading-tight">{{ editableData.title }}</h1>
              <p v-if="editableData.authors" class="text-lg text-indigo-400/80 light:text-indigo-600 mt-2 font-medium">
                {{ editableData.authors }}
              </p>
            </div>
          </header>

          <section class="mb-6">
            <h2 class="text-xs font-bold text-slate-500 light:text-slate-600 uppercase tracking-[0.2em] mb-3">Description</h2>
            <div v-if="isEditMode">
              <textarea
                v-model="editableData.description"
                rows="6"
                class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-slate-300 light:text-slate-900 text-sm leading-relaxed focus:border-indigo-500 focus:outline-none resize-none"
                placeholder="Book description..."
              />
            </div>
            <div v-else-if="editableData.description">
              <div
                :class="showFullDescription ? '' : 'line-clamp-6'"
                class="text-slate-300 light:text-slate-700 text-sm leading-relaxed"
                v-html="showFullDescription ? editableData.description : truncatedDescription"
              />
              <button
                v-if="editableData.description && editableData.description.replace(/<[^>]*>/g, '').split(' ').length > 100"
                @click="showFullDescription = !showFullDescription"
                class="mt-3 text-xs text-indigo-400 light:text-indigo-600 hover:text-indigo-300 light:hover:text-indigo-500 font-semibold underline underline-offset-4"
              >
                {{ showFullDescription ? 'Show Less' : 'Read More' }}
              </button>
            </div>
            <p v-else class="text-slate-300 light:text-slate-700 text-sm leading-relaxed">
              No description available for this title.
            </p>
          </section>

          <section class="mb-8">
            <h2 class="text-xs font-bold text-slate-500 light:text-slate-600 uppercase tracking-[0.2em] mb-3">Categories</h2>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="category in (book.categories || [])"
                :key="category"
                class="px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-medium hover:bg-indigo-500/20 transition-colors cursor-default"
              >
                {{ category }}
              </span>
              <p v-if="!book.categories || book.categories.length === 0" class="text-slate-500 text-sm italic">
                General
              </p>
            </div>
          </section>

          <!-- Import Logic -->
          <section class="p-5 rounded-2xl bg-slate-800/40 border border-slate-700/50">
            <h3 class="text-base font-semibold text-white mb-5 flex items-center gap-2">
              Add to Shelf (Optional)
            </h3>

            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                @click="handleStatusToggle('want_to_read')"
                :class="selectedAction === 'want_to_read'
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.1)]'
                  : 'border-slate-700 bg-slate-800/20 text-slate-400 hover:border-slate-500'"
                class="p-3 rounded-xl flex items-center gap-3 border-2 transition-all duration-300"
              >
                <span :class="selectedAction === 'want_to_read' ? 'scale-110' : ''" class="transition-transform duration-300">
                  <Bookmark :size="18" />
                </span>
                <span class="text-sm font-semibold">Want to Read</span>
                <Check v-if="selectedAction === 'want_to_read'" :size="16" class="ml-auto" />
              </button>

              <button
                @click="handleStatusToggle('currently_reading')"
                :class="selectedAction === 'currently_reading'
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.1)]'
                  : 'border-slate-700 bg-slate-800/20 text-slate-400 hover:border-slate-500'"
                class="p-3 rounded-xl flex items-center gap-3 border-2 transition-all duration-300"
              >
                <span :class="selectedAction === 'currently_reading' ? 'scale-110' : ''" class="transition-transform duration-300">
                  <PlayCircle :size="18" />
                </span>
                <span class="text-sm font-semibold">Reading</span>
                <Check v-if="selectedAction === 'currently_reading'" :size="16" class="ml-auto" />
              </button>

              <button
                @click="handleStatusToggle('read')"
                :class="selectedAction === 'read'
                  ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.1)]'
                  : 'border-slate-700 bg-slate-800/20 text-slate-400 hover:border-slate-500'"
                class="p-3 rounded-xl flex items-center gap-3 border-2 transition-all duration-300"
              >
                <span :class="selectedAction === 'read' ? 'scale-110' : ''" class="transition-transform duration-300">
                  <CheckCircle :size="18" />
                </span>
                <span class="text-sm font-semibold">Finished</span>
                <Check v-if="selectedAction === 'read'" :size="16" class="ml-auto" />
              </button>
            </div>

            <div v-if="selectedAction === 'read'" class="mt-8 pt-8 border-t border-slate-700/50 animate-in slide-in-from-top-4 duration-300">
              <p class="text-sm font-medium text-slate-300 mb-4">
                Your Rating (Optional)
                <span class="text-xs text-slate-500 ml-2">Click once for full star, double-click for half star</span>
              </p>
              <div class="flex items-center gap-2">
                <StarRating
                  v-model="rating"
                  :size="32"
                  :show-value="true"
                />
                <button
                  v-if="rating"
                  @click="rating = null"
                  class="ml-4 text-xs text-slate-500 hover:text-slate-300 underline underline-offset-4"
                >
                  Clear
                </button>
              </div>
            </div>
          </section>
        </div>

        <!-- Footer Actions -->
        <div class="p-6 border-t border-slate-700/30 light:border-slate-200 bg-slate-900/50 light:bg-slate-50 flex flex-col sm:flex-row gap-3">
          <button
            @click="handleClose"
            class="px-5 py-3 rounded-xl border border-slate-700 light:border-slate-300 text-slate-300 light:text-slate-700 text-sm font-semibold hover:bg-slate-800 light:hover:bg-slate-200 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleImport"
            class="flex-[2] px-5 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
          >
            <Library :size="18" />
            Import Book
          </button>
        </div>
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
