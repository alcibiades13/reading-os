<script setup>
import { reactive, computed } from 'vue'
import { BookPlus, Image, PenLine } from 'lucide-vue-next'

const emit = defineEmits(['submit'])

const form = reactive({
  title: '',
  subtitle: '',
  authors: '',
  publisher: '',
  isbn_13: '',
  isbn_10: '',
  page_count: null,
  language: 'en',
  published_date: '',
  cover_image_url: '',
  description: '',
  categories: '',
})

const languages = [
  { value: 'en', label: 'English' },
  { value: 'sr', label: 'Serbian' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'es', label: 'Spanish' },
  { value: 'it', label: 'Italian' },
  { value: 'ru', label: 'Russian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
]

const isValid = computed(() => form.title.trim().length > 0)

const coverPreviewError = reactive({ failed: false })

function handleSubmit() {
  if (!isValid.value) return

  const bookData = {
    title: form.title.trim(),
    subtitle: form.subtitle.trim() || null,
    authors: form.authors ? form.authors.split(',').map(a => a.trim()).filter(Boolean) : [],
    description: form.description.trim() || null,
    publisher: form.publisher.trim() || null,
    published_date: form.published_date.trim() || null,
    isbn_13: form.isbn_13.trim() || null,
    isbn_10: form.isbn_10.trim() || null,
    page_count: form.page_count ? parseInt(form.page_count) : null,
    language: form.language || 'en',
    cover_image_url: form.cover_image_url.trim() || null,
    categories: form.categories ? form.categories.split(',').map(c => c.trim()).filter(Boolean) : [],
    source: 'manual',
    source_id: null,
    google_books_id: null,
    open_library_id: null,
    raw_data: null,
  }

  emit('submit', bookData)
}
</script>

<template>
  <div class="w-full max-w-5xl mx-auto">
    <div class="glass rounded-2xl lg:rounded-[2rem] border-white/5 p-4 lg:p-8">
      <!-- Header -->
      <div class="flex items-center gap-3 mb-6 lg:mb-8">
        <div class="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
          <PenLine :size="20" class="text-indigo-400" />
        </div>
        <div>
          <h2 class="text-lg lg:text-xl font-bold text-white">Add Book Manually</h2>
          <p class="text-xs text-slate-500">Fill in the book details below. Only title is required.</p>
        </div>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-6">
        <!-- Two-column layout on desktop -->
        <div class="flex flex-col lg:flex-row gap-6 lg:gap-8">
          <!-- Left: Cover Preview -->
          <div class="lg:w-48 flex-shrink-0">
            <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-2">Cover Preview</label>
            <div class="w-32 lg:w-48 aspect-[2/3] rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden flex items-center justify-center mx-auto lg:mx-0">
              <img
                v-if="form.cover_image_url && !coverPreviewError.failed"
                :src="form.cover_image_url"
                class="w-full h-full object-cover"
                @error="coverPreviewError.failed = true"
              />
              <div v-else class="flex flex-col items-center gap-2 text-slate-600">
                <Image :size="32" />
                <span class="text-[10px] font-medium">No cover</span>
              </div>
            </div>
            <!-- Cover URL on mobile goes here -->
            <div class="mt-3 lg:hidden">
              <input
                v-model="form.cover_image_url"
                type="url"
                placeholder="Cover image URL"
                @input="coverPreviewError.failed = false"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none"
              />
            </div>
          </div>

          <!-- Right: Fields -->
          <div class="flex-1 space-y-4">
            <!-- Title (required) -->
            <div>
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">
                Title <span class="text-rose-500">*</span>
              </label>
              <input
                v-model="form.title"
                type="text"
                required
                placeholder="Book title"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
              />
            </div>

            <!-- Subtitle -->
            <div>
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Subtitle</label>
              <input
                v-model="form.subtitle"
                type="text"
                placeholder="Optional subtitle"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
              />
            </div>

            <!-- Authors -->
            <div>
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Authors</label>
              <input
                v-model="form.authors"
                type="text"
                placeholder="Author names, comma-separated"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
              />
            </div>

            <!-- Publisher + Language row -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Publisher</label>
                <input
                  v-model="form.publisher"
                  type="text"
                  placeholder="Publisher name"
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Language</label>
                <select
                  v-model="form.language"
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white focus:border-indigo-500/50 focus:outline-none transition-colors appearance-none"
                >
                  <option v-for="lang in languages" :key="lang.value" :value="lang.value">
                    {{ lang.label }}
                  </option>
                </select>
              </div>
            </div>

            <!-- ISBN row -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">ISBN-13</label>
                <input
                  v-model="form.isbn_13"
                  type="text"
                  maxlength="13"
                  placeholder="978..."
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors font-mono"
                />
              </div>
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">ISBN-10</label>
                <input
                  v-model="form.isbn_10"
                  type="text"
                  maxlength="10"
                  placeholder="Optional"
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors font-mono"
                />
              </div>
            </div>

            <!-- Pages + Published Date row -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Pages</label>
                <input
                  v-model="form.page_count"
                  type="number"
                  min="1"
                  placeholder="Page count"
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
                />
              </div>
              <div>
                <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Published Date</label>
                <input
                  v-model="form.published_date"
                  type="text"
                  placeholder="YYYY or YYYY-MM-DD"
                  class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <!-- Cover URL (desktop only — mobile is near preview) -->
            <div class="hidden lg:block">
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Cover Image URL</label>
              <input
                v-model="form.cover_image_url"
                type="url"
                placeholder="https://..."
                @input="coverPreviewError.failed = false"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
              />
            </div>

            <!-- Categories -->
            <div>
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Genres / Categories</label>
              <input
                v-model="form.categories"
                type="text"
                placeholder="Fiction, Science Fiction, Classic — comma-separated"
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors"
              />
            </div>

            <!-- Description -->
            <div>
              <label class="text-[10px] font-bold text-slate-500 uppercase tracking-wider block mb-1.5">Description</label>
              <textarea
                v-model="form.description"
                rows="4"
                placeholder="Book description or synopsis..."
                class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:border-indigo-500/50 focus:outline-none transition-colors resize-none"
              />
            </div>
          </div>
        </div>

        <!-- Submit -->
        <div class="flex justify-end pt-2">
          <button
            type="submit"
            :disabled="!isValid"
            class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold text-sm hover:bg-indigo-400 active:scale-95 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <BookPlus :size="18" />
            Preview & Import
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
