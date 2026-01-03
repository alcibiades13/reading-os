<script setup>
import { ref, watch } from 'vue'
import { X, Save, BookOpen } from 'lucide-vue-next'

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

const emit = defineEmits(['close', 'save'])

// Editable fields - initialize from book prop
const editableData = ref({
  title: '',
  authors: '',
  page_count: '',
  publisher: '',
  published_date: '',
  isbn: '',
  cover_image: '',
  description: '',
  language: '',
})

// Watch for book changes and update editableData
watch(() => props.book, (newBook) => {
  if (newBook) {
    editableData.value = {
      title: newBook.title || '',
      authors: newBook.authors?.map(a => a.name).join(', ') || '',
      page_count: newBook.pages || '',
      publisher: newBook.publisher?.name || '',
      published_date: newBook.published_date || '',
      isbn: newBook.isbn || '',
      cover_image: newBook.cover_image || '',
      description: newBook.description || '',
      language: newBook.language || 'en',
    }
  }
}, { immediate: true })

const handleSave = () => {
  // Parse authors from comma-separated string
  const authorsArray = editableData.value.authors
    .split(',')
    .map(a => a.trim())
    .filter(a => a)

  const payload = {
    title: editableData.value.title,
    authors: authorsArray,
    pages: editableData.value.page_count ? parseInt(editableData.value.page_count) : null,
    publisher_name: editableData.value.publisher,
    published_date: editableData.value.published_date,
    isbn: editableData.value.isbn,
    cover_image: editableData.value.cover_image,
    description: editableData.value.description,
    language: editableData.value.language,
  }

  emit('save', payload)
}

const handleClose = () => {
  emit('close')
}

const hasCover = ref(true)
</script>

<template>
  <div class="fixed inset-0 z-[70] flex items-center justify-center p-4 md:p-6 pt-20 bg-slate-950/90 light:bg-white/90 backdrop-blur-sm animate-in fade-in duration-300">
    <div class="relative w-full max-w-5xl h-[85vh] glass light:bg-white light:border light:border-slate-200 rounded-3xl overflow-hidden shadow-2xl flex flex-col md:flex-row animate-in zoom-in-95 duration-300 ring-2 ring-indigo-500">

      <!-- Close Button -->
      <button
        @click="handleClose"
        class="absolute top-6 right-6 z-20 p-2 rounded-full bg-slate-900/50 light:bg-slate-200 hover:bg-slate-800 light:hover:bg-slate-300 text-slate-300 light:text-slate-700 transition-colors"
      >
        <X :size="20" />
      </button>

      <!-- Left Column - Cover Preview -->
      <div class="w-full md:w-[40%] bg-slate-900/50 light:bg-slate-50 p-8 flex flex-col items-center overflow-y-auto border-r border-slate-700/30 light:border-slate-200">
        <div class="mb-4 w-full">
          <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-2 block">Cover Image URL</label>
          <input
            v-model="editableData.cover_image"
            type="text"
            class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-300 focus:border-indigo-500 focus:outline-none"
            placeholder="https://..."
          />
        </div>

        <div class="relative w-full max-w-[240px] aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl ring-1 ring-white/10">
          <img
            v-if="hasCover && editableData.cover_image"
            :src="editableData.cover_image"
            :alt="editableData.title"
            class="w-full h-full object-cover"
            @error="hasCover = false"
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
          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1 block">Pages</label>
            <input
              v-model="editableData.page_count"
              type="number"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
              placeholder="Pages"
            />
          </div>

          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1 block">Language</label>
            <input
              v-model="editableData.language"
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none uppercase"
              placeholder="EN"
            />
          </div>

          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1 block">Published Date</label>
            <input
              v-model="editableData.published_date"
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
              placeholder="YYYY or YYYY-MM-DD"
            />
          </div>

          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1 block">Publisher</label>
            <input
              v-model="editableData.publisher"
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
              placeholder="Publisher"
            />
          </div>

          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-1 block">ISBN</label>
            <input
              v-model="editableData.isbn"
              type="text"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-semibold focus:border-indigo-500 focus:outline-none"
              placeholder="ISBN-13 or ISBN-10"
            />
          </div>
        </div>
      </div>

      <!-- Right Column - Details -->
      <div class="w-full md:w-[60%] flex flex-col h-full bg-slate-900/20 light:bg-white">
        <div class="flex-1 overflow-y-auto p-8 custom-scrollbar pt-24">
          <header class="mb-6">
            <div class="space-y-3">
              <div>
                <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-1 block">Title</label>
                <input
                  v-model="editableData.title"
                  type="text"
                  class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-lg md:text-xl font-bold text-white light:text-slate-900 focus:border-indigo-500 focus:outline-none"
                  placeholder="Book Title"
                />
              </div>
              <div>
                <label class="text-xs text-slate-400 light:text-slate-600 font-bold uppercase tracking-wider mb-1 block">Authors (comma-separated)</label>
                <input
                  v-model="editableData.authors"
                  type="text"
                  class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-lg text-indigo-400/80 font-medium focus:border-indigo-500 focus:outline-none"
                  placeholder="Author 1, Author 2"
                />
              </div>
            </div>
          </header>

          <section class="mb-6">
            <h2 class="text-xs font-bold text-slate-500 light:text-slate-600 uppercase tracking-[0.2em] mb-3">Description</h2>
            <div>
              <textarea
                v-model="editableData.description"
                rows="8"
                class="w-full bg-slate-900 light:bg-white border border-slate-700 light:border-slate-200 rounded-lg px-3 py-2 text-slate-300 light:text-slate-900 text-sm leading-relaxed focus:border-indigo-500 focus:outline-none resize-none"
                placeholder="Book description..."
              />
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
            @click="handleSave"
            class="flex-[2] px-5 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
          >
            <Save :size="18" />
            Save Changes
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
