<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { Upload, FileText, BookOpen, Link2, X, Search, Loader2 } from 'lucide-vue-next'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { ebooksAPI, booksAPI } from '@/services/api'
import { extractEbookMetadata } from '@/utils/ebookMetadata'

const props = defineProps({
  open: { type: Boolean, default: false },
  ebook: { type: Object, default: null }, // set = edit mode
  maxUploadBytes: { type: Number, default: 100 * 1024 * 1024 },
})

const emit = defineEmits(['update:open', 'saved'])

const isEdit = computed(() => !!props.ebook)

const step = ref('pick') // pick | reading | form | uploading
const file = ref(null)
const meta = ref(null)
const coverPreview = ref(null)
const form = ref({ title: '', author: '', language: '', isbn: '' })
const linkedBook = ref(null)
const trackProgress = ref(false)
const errorMessage = ref('')
const uploadProgress = ref(0)
const isDragging = ref(false)
const fileInput = ref(null)

const bookQuery = ref('')
const bookResults = ref([])
const searchingBooks = ref(false)
let searchTimer = null

const formatSize = (bytes) => `${(bytes / (1024 * 1024)).toFixed(1)} MB`

const resetState = () => {
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  step.value = isEdit.value ? 'form' : 'pick'
  file.value = null
  meta.value = null
  coverPreview.value = null
  errorMessage.value = ''
  uploadProgress.value = 0
  bookQuery.value = ''
  bookResults.value = []
  if (isEdit.value) {
    const { title, author, language, isbn, book_detail } = props.ebook
    form.value = { title, author, language, isbn }
    linkedBook.value = book_detail || null
    trackProgress.value = props.ebook.track_progress === true
  } else {
    form.value = { title: '', author: '', language: '', isbn: '' }
    linkedBook.value = null
  }
}

watch(() => props.open, (open) => {
  if (open) resetState()
})

const close = () => emit('update:open', false)

/* ---------- file selection ---------- */

const handleFile = async (selected) => {
  if (!selected) return
  errorMessage.value = ''
  if (!/\.(epub|pdf)$/i.test(selected.name)) {
    errorMessage.value = 'Please choose an EPUB or PDF file.'
    return
  }
  if (selected.size > props.maxUploadBytes) {
    errorMessage.value = `File is too large (${formatSize(selected.size)}). Maximum is ${formatSize(props.maxUploadBytes)}.`
    return
  }

  file.value = selected
  step.value = 'reading'
  try {
    meta.value = await extractEbookMetadata(selected)
  } catch {
    // Unreadable metadata is fine - the user fills the form in
    meta.value = { format: /\.pdf$/i.test(selected.name) ? 'pdf' : 'epub', title: selected.name.replace(/\.(epub|pdf)$/i, ''), author: '', language: '', isbn: '', pageCount: null, hasText: true, coverBlob: null }
  }
  form.value = {
    title: meta.value.title,
    author: meta.value.author,
    language: meta.value.language,
    isbn: meta.value.isbn,
  }
  if (meta.value.coverBlob) coverPreview.value = URL.createObjectURL(meta.value.coverBlob)
  step.value = 'form'
  suggestCatalogMatch()
}

const onFileInput = (e) => handleFile(e.target.files?.[0])
const onDrop = (e) => {
  isDragging.value = false
  handleFile(e.dataTransfer?.files?.[0])
}

/* ---------- catalog link ---------- */

const searchBooks = async (query) => {
  if (!query || query.trim().length < 2) {
    bookResults.value = []
    return
  }
  searchingBooks.value = true
  try {
    const { data } = await booksAPI.list({ search: query.trim() })
    bookResults.value = (data?.results || data || []).slice(0, 6)
  } catch {
    bookResults.value = []
  } finally {
    searchingBooks.value = false
  }
}

watch(bookQuery, (query) => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => searchBooks(query), 350)
})

// Exact ISBN match links automatically; otherwise offer title matches
const suggestCatalogMatch = async () => {
  const { isbn, title } = form.value
  if (isbn) {
    try {
      const { data } = await booksAPI.list({ search: isbn })
      const exact = (data?.results || data || []).find((b) => b.isbn === isbn)
      if (exact) {
        linkedBook.value = exact
        return
      }
    } catch {
      // ignore
    }
  }
  if (title) {
    bookQuery.value = title
  }
}

const authorNames = (book) =>
  (book?.authors || []).map((a) => (typeof a === 'string' ? a : a.name)).join(', ')

const selectBook = (book) => {
  linkedBook.value = book
  bookQuery.value = ''
  bookResults.value = []
  if (!form.value.author && authorNames(book)) form.value.author = authorNames(book)
}

/* ---------- submit ---------- */

const canSubmit = computed(() => form.value.title.trim() && form.value.author.trim() && step.value === 'form')

const extractError = (err) => {
  const data = err?.response?.data
  if (!data) return 'Upload failed. Check your connection and try again.'
  if (typeof data === 'string') return data
  const first = Object.values(data)[0]
  return Array.isArray(first) ? first[0] : String(first)
}

const submit = async () => {
  if (!canSubmit.value) return
  errorMessage.value = ''
  const payload = {
    title: form.value.title.trim(),
    author: form.value.author.trim(),
    language: (form.value.language || '').trim(),
    isbn: (form.value.isbn || '').trim(),
  }

  if (isEdit.value) {
    try {
      let { data } = await ebooksAPI.update(props.ebook.id, { ...payload, book: linkedBook.value?.id ?? null })
      if (trackProgress.value !== (props.ebook.track_progress === true)) {
        data = (await ebooksAPI.setTracking(props.ebook.id, { enabled: trackProgress.value })).data
      }
      emit('saved', data)
      close()
    } catch (err) {
      errorMessage.value = extractError(err)
    }
    return
  }

  const formData = new FormData()
  formData.append('file', file.value)
  Object.entries(payload).forEach(([key, value]) => formData.append(key, value))
  if (linkedBook.value) formData.append('book', linkedBook.value.id)
  if (meta.value?.pageCount) formData.append('page_count', meta.value.pageCount)
  if (meta.value?.coverBlob) {
    formData.append('cover_file', new File([meta.value.coverBlob], 'cover.jpg', { type: meta.value.coverBlob.type || 'image/jpeg' }))
  }

  step.value = 'uploading'
  try {
    const { data } = await ebooksAPI.upload(formData, (e) => {
      if (e.total) uploadProgress.value = Math.round((e.loaded / e.total) * 100)
    })
    emit('saved', data)
    close()
  } catch (err) {
    step.value = 'form'
    errorMessage.value = extractError(err)
  }
}

onBeforeUnmount(() => {
  clearTimeout(searchTimer)
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
})
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-lg glass border-zinc-700 max-h-[90vh] overflow-y-auto">
      <DialogHeader class="border-b border-zinc-800 pb-3">
        <DialogTitle class="text-lg font-bold flex items-center gap-2">
          <Upload v-if="!isEdit" :size="18" class="text-indigo-400" />
          <BookOpen v-else :size="18" class="text-indigo-400" />
          {{ isEdit ? 'Edit e-book' : 'Add an e-book' }}
        </DialogTitle>
        <DialogDescription class="text-xs text-zinc-500">
          {{ isEdit ? 'Update the details or the catalog link.' : 'EPUB or PDF. Your files are private - only you can read them.' }}
        </DialogDescription>
      </DialogHeader>

      <!-- Pick file -->
      <div v-if="step === 'pick'" class="pt-2">
        <label
          class="flex flex-col items-center justify-center gap-3 py-12 px-4 rounded-2xl border-2 border-dashed cursor-pointer transition-all text-center"
          :class="isDragging ? 'border-indigo-500 bg-indigo-500/10' : 'border-zinc-700 hover:border-indigo-500/50 bg-zinc-900/30'"
          @dragover.prevent="isDragging = true"
          @dragleave.prevent="isDragging = false"
          @drop.prevent="onDrop"
        >
          <div class="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Upload :size="24" />
          </div>
          <div>
            <p class="text-sm font-bold text-white">Choose a file</p>
            <p class="text-xs text-zinc-500 mt-1">or drag it here · EPUB, PDF · max {{ formatSize(maxUploadBytes) }}</p>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept=".epub,.pdf,application/epub+zip,application/pdf"
            class="hidden"
            @change="onFileInput"
          />
        </label>
      </div>

      <!-- Reading metadata -->
      <div v-else-if="step === 'reading'" class="py-12 flex flex-col items-center gap-3">
        <Loader2 :size="24" class="text-indigo-400 animate-spin" />
        <p class="text-sm text-zinc-400">Reading book details…</p>
      </div>

      <!-- Form / uploading -->
      <form v-else class="space-y-4 pt-2" @submit.prevent="submit">
        <div v-if="file" class="flex items-center gap-3 p-3 rounded-xl bg-zinc-800/40 border border-zinc-700/50">
          <div class="w-12 h-[72px] shrink-0 rounded-md overflow-hidden bg-zinc-800 flex items-center justify-center">
            <img v-if="coverPreview" :src="coverPreview" class="w-full h-full object-cover" />
            <FileText v-else :size="18" class="text-zinc-500" />
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-sm font-semibold text-white truncate">{{ file.name }}</p>
            <p class="text-xs text-zinc-500">
              {{ meta?.format?.toUpperCase() }} · {{ formatSize(file.size) }}
              <template v-if="meta?.pageCount"> · {{ meta.pageCount }} pages</template>
            </p>
            <p v-if="meta && meta.format === 'pdf' && !meta.hasText" class="text-[11px] text-amber-400 mt-1">
              Scanned PDF (no text) - it can be read as pages, but text can't be resized.
            </p>
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Title *</label>
          <input
            v-model="form.title"
            required
            maxlength="500"
            class="w-full bg-zinc-800/30 border-2 border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <div class="space-y-1.5">
          <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Author *</label>
          <input
            v-model="form.author"
            required
            maxlength="500"
            class="w-full bg-zinc-800/30 border-2 border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Language</label>
            <input
              v-model="form.language"
              maxlength="20"
              placeholder="sr, en…"
              class="w-full bg-zinc-800/30 border-2 border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-indigo-500 outline-none transition-all"
            />
          </div>
          <div class="space-y-1.5">
            <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">ISBN</label>
            <input
              v-model="form.isbn"
              maxlength="20"
              class="w-full bg-zinc-800/30 border-2 border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:border-indigo-500 outline-none transition-all"
            />
          </div>
        </div>

        <!-- Catalog link -->
        <div class="space-y-1.5">
          <label class="text-[10px] font-bold text-zinc-500 uppercase tracking-widest flex items-center gap-1.5">
            <Link2 :size="11" /> Catalog book (optional)
          </label>
          <div v-if="linkedBook" class="flex items-center gap-3 p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
            <img v-if="linkedBook.cover_image" :src="linkedBook.cover_image" class="w-8 h-12 rounded object-cover shrink-0" />
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-white truncate">{{ linkedBook.title }}</p>
              <p class="text-xs text-indigo-300/70 truncate">{{ authorNames(linkedBook) }}</p>
            </div>
            <button type="button" class="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10" @click="linkedBook = null">
              <X :size="14" />
            </button>
          </div>
          <template v-else>
            <div class="relative">
              <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500" />
              <input
                v-model="bookQuery"
                placeholder="Search the catalog to link this file…"
                class="w-full bg-zinc-800/30 border-2 border-zinc-700 rounded-lg pl-9 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:border-indigo-500 outline-none transition-all"
              />
              <Loader2 v-if="searchingBooks" :size="14" class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 animate-spin" />
            </div>
            <div v-if="bookResults.length" class="rounded-xl border border-zinc-700/60 divide-y divide-zinc-800 overflow-hidden">
              <button
                v-for="book in bookResults"
                :key="book.id"
                type="button"
                class="w-full flex items-center gap-3 p-2.5 text-left hover:bg-zinc-800/60 transition-colors"
                @click="selectBook(book)"
              >
                <img v-if="book.cover_image" :src="book.cover_image" class="w-7 h-10 rounded object-cover shrink-0" />
                <div v-else class="w-7 h-10 rounded bg-zinc-800 shrink-0" />
                <div class="min-w-0">
                  <p class="text-sm text-white truncate">{{ book.title }}</p>
                  <p class="text-xs text-zinc-500 truncate">{{ authorNames(book) }}</p>
                </div>
              </button>
            </div>
            <p class="text-[11px] text-zinc-600">Linking lets this file share reviews, quotes and progress with the book in your library.</p>
          </template>
        </div>

        <label v-if="isEdit" class="flex items-start gap-3 p-3 rounded-xl bg-zinc-800/30 border border-zinc-700/50 cursor-pointer">
          <input v-model="trackProgress" type="checkbox" class="mt-0.5 accent-indigo-500" />
          <span>
            <span class="block text-sm font-semibold text-white">Track progress in my library</span>
            <span class="block text-xs text-zinc-500 mt-0.5">
              Reading this file updates the book's page and reading time{{ linkedBook ? '' : ' (it will be added to your library)' }}.
            </span>
          </span>
        </label>

        <p v-if="errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>

        <div v-if="step === 'uploading'" class="space-y-2">
          <div class="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
            <div class="h-full bg-indigo-500 transition-all" :style="{ width: `${uploadProgress}%` }" />
          </div>
          <p class="text-xs text-zinc-500 text-center">Uploading… {{ uploadProgress }}%</p>
        </div>

        <div class="flex gap-3 pt-2">
          <button type="button" class="flex-1 py-2.5 rounded-xl border border-zinc-700 text-sm font-bold text-zinc-400 hover:text-white transition-colors" @click="close">
            Cancel
          </button>
          <button
            type="submit"
            :disabled="!canSubmit"
            class="flex-1 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {{ isEdit ? 'Save' : step === 'uploading' ? 'Uploading…' : 'Add e-book' }}
          </button>
        </div>
      </form>

      <p v-if="step === 'pick' && errorMessage" class="text-sm text-red-400">{{ errorMessage }}</p>
    </DialogContent>
  </Dialog>
</template>
