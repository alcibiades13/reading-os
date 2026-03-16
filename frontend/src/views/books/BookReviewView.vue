<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import StarRating from '@/components/ui/StarRating.vue'
import DatePicker from '@/components/ui/DatePicker.vue'
import {
  ArrowLeft, Bold, Italic, Heading1, Heading2, List, Quote,
  Link as LinkIcon, Save, Send, Globe, Lock, Eye,
  Info, Sparkles, Check, BookmarkPlus, Calendar
} from 'lucide-vue-next'
import { getBookUrl } from '@/utils/bookUrl'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()
const quotesStore = useQuotesStore()

const bookId = computed(() => route.params.id)
const book = computed(() => booksStore.currentBook)
const userBook = computed(() => {
  const numericBookId = parseInt(bookId.value)
  return userBooksStore.books.find(ub => ub.book?.id === numericBookId)
})

const content = ref('')
const isPublic = ref(true)
const isDraft = ref(true)
const isSaving = ref(false)
const wordCount = ref(0)
const editorRef = ref(null)
const selectedBlockquote = ref(null)
const showQuoteMetadata = ref(false)
const quotePageNumber = ref('')
const quoteChapter = ref('')
const quoteTags = ref('')
const startedAt = ref('')
const finishedAt = ref('')

const coverUrl = computed(() => {
  if (!book.value) return ''
  return book.value.cover_image ||
    `https://via.placeholder.com/600x900/1E293B/64748B?text=${encodeURIComponent(book.value.title || 'Book')}`
})

const authorsString = computed(() => {
  if (!book.value?.authors || book.value.authors.length === 0) return 'Unknown Author'
  return book.value.authors.map(a => a.name).join(', ')
})

const personalRating = computed(() => {
  const rating = userBook.value?.rating
  return rating ? parseFloat(rating) : 0
})

const currentStatus = computed(() => userBook.value?.status || null)

const getStatusLabel = (status) => {
  const labels = {
    'want_to_read': 'Want to Read',
    'currently_reading': 'Currently Reading',
    'read': 'Finished',
    'abandoned': 'Abandoned'
  }
  return labels[status] || status
}

// Auto-save to localStorage
onMounted(async () => {
  try {
    // Only fetch book details and user books if not already loaded
    const promises = [booksStore.fetchBook(bookId.value)]

    // Only fetch user books if store is empty
    if (userBooksStore.books.length === 0) {
      promises.push(userBooksStore.fetchBooks())
    }

    // Fetch tags for quote metadata
    if (quotesStore.tags.length === 0) {
      promises.push(quotesStore.fetchTags())
    }

    await Promise.all(promises)

    // Load existing dates
    if (userBook.value?.started_at) {
      startedAt.value = userBook.value.started_at
    }
    if (userBook.value?.finished_at) {
      finishedAt.value = userBook.value.finished_at
    }

    // Wait for next tick to ensure refs are ready
    await nextTick()

    const saved = localStorage.getItem(`draft_review_${bookId.value}`)

    if (saved && !userBook.value?.review) {
      content.value = saved
      if (editorRef.value) editorRef.value.innerHTML = saved
    } else if (userBook.value?.review) {
      content.value = userBook.value.review
      if (editorRef.value) editorRef.value.innerHTML = userBook.value.review
    }

    // Clean up and add metadata button to existing blockquotes
    await nextTick()
    if (editorRef.value) {
      const blockquotes = editorRef.value.querySelectorAll('blockquote')
      blockquotes.forEach(bq => {
        // Remove old page indicators completely
        const oldIndicators = bq.querySelectorAll('.quote-page-indicator')
        oldIndicators.forEach(indicator => indicator.remove())

        // Remove any checkmark spans
        const checkmarks = bq.querySelectorAll('span')
        checkmarks.forEach(span => {
          if (span.textContent.includes('✓') || span.classList.contains('quote-page-indicator')) {
            span.remove()
          }
        })

        // Check if button already exists
        if (!bq.querySelector('.quote-metadata-btn')) {
          const metadataBtn = document.createElement('button')
          metadataBtn.className = 'quote-metadata-btn'
          metadataBtn.innerHTML = '⋯'
          metadataBtn.setAttribute('contenteditable', 'false')
          metadataBtn.addEventListener('click', (e) => {
            e.stopPropagation()
            e.preventDefault()
            selectedBlockquote.value = bq
            quotePageNumber.value = bq.getAttribute('data-page') || ''
            quoteChapter.value = bq.getAttribute('data-chapter') || ''
            quoteTags.value = bq.getAttribute('data-tags') || ''
            showQuoteMetadata.value = true
          })
          bq.appendChild(metadataBtn)
        }
      })
    }
  } catch (error) {
    // Review loading failed
  }
})

watch(content, (newContent) => {
  const timeout = setTimeout(() => {
    localStorage.setItem(`draft_review_${bookId.value}`, newContent)
  }, 1000)

  const text = newContent.replace(/<[^>]*>/g, '')
  wordCount.value = text.split(/\s+/).filter(Boolean).length

  return () => clearTimeout(timeout)
})

const handleCommand = (command, value) => {
  if (!editorRef.value) return

  // Focus editor first to ensure we have selection
  editorRef.value.focus()

  if (command === 'formatBlock' && value === '<blockquote>') {
    // Special handling for blockquote
    const selection = window.getSelection()

    if (!selection || selection.rangeCount === 0) {
      return
    }

    const range = selection.getRangeAt(0)

    // Check if there's actually selected text
    if (range.collapsed) {
      return
    }

    const selectedText = range.extractContents()
    const blockquote = document.createElement('blockquote')
    blockquote.appendChild(selectedText)
    blockquote.classList.add('quote-block')

    // Add metadata button
    const metadataBtn = document.createElement('button')
    metadataBtn.className = 'quote-metadata-btn'
    metadataBtn.innerHTML = '📖'
    metadataBtn.setAttribute('contenteditable', 'false')
    metadataBtn.addEventListener('click', (e) => {
      e.stopPropagation()
      e.preventDefault()
      selectedBlockquote.value = blockquote
      quotePageNumber.value = blockquote.getAttribute('data-page') || ''
      quoteChapter.value = blockquote.getAttribute('data-chapter') || ''
      quoteTags.value = blockquote.getAttribute('data-tags') || ''
      showQuoteMetadata.value = true
    })
    blockquote.appendChild(metadataBtn)

    range.insertNode(blockquote)

    // Update content
    content.value = editorRef.value.innerHTML

    // Move cursor after blockquote
    const newRange = document.createRange()
    newRange.setStartAfter(blockquote)
    newRange.collapse(true)
    selection.removeAllRanges()
    selection.addRange(newRange)
  } else {
    // For all other commands, just execute them
    // The mousedown preventDefault should preserve selection
    document.execCommand(command, false, value)
    if (editorRef.value) content.value = editorRef.value.innerHTML
  }
}

const cleanReviewHtml = (htmlContent) => {
  const div = document.createElement('div')
  div.innerHTML = htmlContent

  // Remove all metadata buttons from blockquotes
  const buttons = div.querySelectorAll('.quote-metadata-btn')
  buttons.forEach(btn => btn.remove())

  return div.innerHTML
}

const extractQuotesFromReview = (htmlContent) => {
  const div = document.createElement('div')
  div.innerHTML = htmlContent
  const blockquotes = div.querySelectorAll('blockquote')

  const quotes = []
  blockquotes.forEach(bq => {
    // Remove the metadata button from text
    const metadataBtn = bq.querySelector('.quote-metadata-btn')
    if (metadataBtn) {
      metadataBtn.remove()
    }

    const text = bq.textContent || bq.innerText || ''
    const pageNumber = bq.getAttribute('data-page') || null
    const chapter = bq.getAttribute('data-chapter') || null
    const tagsString = bq.getAttribute('data-tags') || null

    // Parse tags from comma-separated string
    const tags = tagsString
      ? tagsString.split(',').map(t => t.trim()).filter(Boolean)
      : []

    // Save quote even without page number - user can add it later
    if (text.trim()) {
      quotes.push({
        text: text.trim(),
        page_number: pageNumber ? parseInt(pageNumber) : null,
        chapter: chapter || null,
        tags: tags
      })
    }
  })

  return quotes
}

const handlePublish = async () => {
  if (!userBook.value || !content.value || content.value.trim() === '') {
    return
  }

  isSaving.value = true

  try {
    // Clean HTML before saving - remove metadata buttons
    const cleanedContent = cleanReviewHtml(content.value)

    // Prepare update data
    const updateData = {
      review: cleanedContent
    }

    // Add dates if provided
    if (startedAt.value) {
      updateData.started_at = startedAt.value
    }
    if (finishedAt.value) {
      updateData.finished_at = finishedAt.value
    }

    // Save review and dates
    await userBooksStore.updateBook(userBook.value.id, updateData)

    // Extract and save quotes from blockquotes
    const quotes = extractQuotesFromReview(content.value)

    if (quotes.length > 0) {
      for (const quote of quotes) {
        const payload = {
          book: book.value.id,
          user_book: userBook.value.id,
          book_title: book.value.title,
          book_author: book.value.authors?.map(a => a.name).join(', ') || '',
          text: quote.text,
          page_number: quote.page_number,
          chapter: quote.chapter,
          is_public: false
        }

        // Process tags if present
        if (quote.tags && quote.tags.length > 0) {
          const tagIds = []
          for (const tagName of quote.tags) {
            // Check if tag already exists in store
            const existingTag = quotesStore.tags.find(t =>
              t.name.toLowerCase() === tagName.toLowerCase()
            )

            if (existingTag) {
              tagIds.push(existingTag.id)
            } else {
              // Create new tag
              const result = await quotesStore.createTag({ name: tagName })
              if (result.success) {
                tagIds.push(result.data.id)
              }
            }
          }
          payload.tag_ids = tagIds
        }

        await quotesStore.createQuote(payload)
      }
    }

    isDraft.value = false
    localStorage.removeItem(`draft_review_${bookId.value}`)

    // Navigate back to book detail
    router.push(book.value ? getBookUrl(book.value) : `/books/${bookId.value}`)
  } catch (error) {
    // Review publish failed
  } finally {
    isSaving.value = false
  }
}

const handleBack = () => {
  router.push(book.value ? getBookUrl(book.value) : `/books/${bookId.value}`)
}

const saveQuoteMetadata = () => {
  if (!selectedBlockquote.value) return

  // Remove existing page indicator if present
  const existingIndicator = selectedBlockquote.value.querySelector('.quote-page-indicator')
  if (existingIndicator) {
    existingIndicator.remove()
  }

  if (quotePageNumber.value) {
    selectedBlockquote.value.setAttribute('data-page', quotePageNumber.value)
  } else {
    selectedBlockquote.value.removeAttribute('data-page')
  }

  if (quoteChapter.value) {
    selectedBlockquote.value.setAttribute('data-chapter', quoteChapter.value)
  } else {
    selectedBlockquote.value.removeAttribute('data-chapter')
  }

  if (quoteTags.value) {
    selectedBlockquote.value.setAttribute('data-tags', quoteTags.value)
  } else {
    selectedBlockquote.value.removeAttribute('data-tags')
  }

  // Update content
  content.value = editorRef.value.innerHTML

  // Close modal
  showQuoteMetadata.value = false
  selectedBlockquote.value = null
  quotePageNumber.value = ''
  quoteChapter.value = ''
  quoteTags.value = ''
}
</script>

<template>
  <div v-if="book" class="min-h-screen bg-slate-950 animate-in fade-in duration-700">
    <!-- Header -->
    <nav class="sticky top-0 z-50 glass border-b border-slate-800 px-6 h-20 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <button
          @click="handleBack"
          class="p-2 rounded-full hover:bg-slate-800 text-slate-400 transition-colors"
        >
          <ArrowLeft :size="24" />
        </button>
        <div class="hidden sm:block h-8 w-px bg-slate-800" />
        <div>
          <h1 class="text-lg font-bold text-white flex items-center gap-2">
            <span class="text-slate-500 font-medium">Review:</span> {{ book.title }}
          </h1>
          <div class="flex items-center gap-2">
            <span :class="['w-2 h-2 rounded-full', isDraft ? 'bg-amber-500' : 'bg-emerald-500']" />
            <span class="text-[10px] uppercase font-black tracking-widest text-slate-500">
              {{ isDraft ? 'Draft Mode' : 'Published' }}
            </span>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-[11px] font-bold text-slate-400">
          <Sparkles :size="12" class="text-indigo-400" />
          Auto-saving active
        </div>
        <button
          @click="handlePublish"
          :disabled="isSaving"
          class="px-6 py-2.5 rounded-xl bg-indigo-500 text-white font-bold text-sm shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-2"
        >
          <div v-if="isSaving" class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          <Send v-else :size="16" />
          Publish Review
        </button>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto px-6 py-12">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">

        <!-- Main Writing Surface -->
        <div class="lg:col-span-8 space-y-6">
          <!-- Toolbar -->
          <div class="flex items-center flex-wrap gap-1 p-2 rounded-2xl glass border-slate-800 sticky top-24 z-40">
            <ToolbarButton :icon="Bold" @command="handleCommand('bold')" label="Bold" />
            <ToolbarButton :icon="Italic" @command="handleCommand('italic')" label="Italic" />
            <div class="w-px h-6 bg-slate-800 mx-1" />
            <ToolbarButton :icon="Heading1" @command="handleCommand('formatBlock', 'H1')" label="H1" />
            <ToolbarButton :icon="Heading2" @command="handleCommand('formatBlock', 'H2')" label="H2" />
            <div class="w-px h-6 bg-slate-800 mx-1" />
            <ToolbarButton :icon="List" @command="handleCommand('insertUnorderedList')" label="List" />
            <ToolbarButton :icon="Quote" @command="handleCommand('formatBlock', '<blockquote>')" label="Quote" />
            <ToolbarButton
              :icon="LinkIcon"
              @command="() => {
                const url = prompt('Enter URL');
                if (url) handleCommand('createLink', url);
              }"
              label="Link"
            />

            <div class="ml-auto pr-4 flex items-center gap-6">
               <div class="flex items-center gap-2 text-slate-500 text-xs font-bold">
                 <Eye :size="14" />
                 <span>{{ wordCount }} words</span>
               </div>
            </div>
          </div>

          <!-- Content Area -->
          <div class="min-h-[60vh] p-10 rounded-3xl glass border-slate-800 bg-slate-900/30 group relative">
            <div
              ref="editorRef"
              contenteditable="true"
              @input="(e) => content = e.target.innerHTML"
              class="editor-surface text-sm text-slate-200 leading-relaxed min-h-[50vh] focus:outline-none"
            />
            <div
              v-if="content === ''"
              class="absolute top-10 left-10 text-slate-500 text-sm pointer-events-none"
            >
              What moved you about this book? Share your thoughts...
            </div>
          </div>

          <!-- Visibility Toggle -->
          <div class="flex items-center justify-between p-6 rounded-2xl bg-slate-900/50 border border-slate-800">
            <div class="flex items-center gap-4">
              <div :class="['p-3 rounded-xl', isPublic ? 'bg-sky-500/10 text-sky-400' : 'bg-slate-800 text-slate-500']">
                <Globe v-if="isPublic" :size="20" />
                <Lock v-else :size="20" />
              </div>
              <div>
                <h4 class="text-sm font-bold text-white">{{ isPublic ? 'Public Review' : 'Private Journal' }}</h4>
                <p class="text-xs text-slate-500">
                  {{ isPublic ? 'Visible to the Lumina community' : 'Only you can see this reflection' }}
                </p>
              </div>
            </div>
            <button
              @click="isPublic = !isPublic"
              :class="['relative w-12 h-6 rounded-full transition-colors', isPublic ? 'bg-indigo-500' : 'bg-slate-800']"
            >
              <div :class="['absolute top-1 w-4 h-4 rounded-full bg-white transition-all', isPublic ? 'left-7' : 'left-1']" />
            </button>
          </div>

          <!-- Reading Dates -->
          <div class="p-6 rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
            <div class="flex items-center gap-2 mb-4">
              <Calendar :size="18" class="text-indigo-400" />
              <h4 class="text-sm font-bold text-white">Reading Journey</h4>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">
                  Date Started
                </label>
                <DatePicker v-model="startedAt" placeholder="Select start date" />
              </div>

              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">
                  Date Finished
                </label>
                <DatePicker v-model="finishedAt" placeholder="Select finish date" />
              </div>
            </div>

            <p class="text-xs text-slate-500 italic">
              Track when you started and finished reading this book
            </p>
          </div>
        </div>

        <!-- Sidebar - Book Info -->
        <div class="lg:col-span-4 sticky top-24 space-y-6">
          <div class="rounded-3xl glass border-slate-800 overflow-hidden shadow-2xl bg-slate-900/40 max-w-full">
            <div class="aspect-[2/3] w-52 mx-auto overflow-hidden">
              <img :src="coverUrl" :alt="book.title" class="w-full h-full object-cover" />
            </div>
            <div class="p-8 space-y-6">
              <div>
                <h3 class="text-xl font-black text-white leading-tight mb-2">{{ book.title }}</h3>
                <p class="text-indigo-400 font-bold">{{ authorsString }}</p>
              </div>

              <div class="space-y-4 pt-6 border-t border-slate-800">
                <div>
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-2">My Rating</span>
                  <StarRating
                    :key="`rating-${userBook?.id}-${userBook?.rating}`"
                    :model-value="personalRating"
                    :readonly="true"
                    :size="18"
                    :show-value="true"
                  />
                </div>

                <div class="flex items-center justify-between">
                  <div>
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Status</span>
                    <div class="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
                      <Check :size="14" />
                      {{ getStatusLabel(currentStatus) }}
                    </div>
                  </div>
                  <div class="text-right">
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-1">Finished</span>
                    <span class="text-slate-300 font-bold text-xs">Today</span>
                  </div>
                </div>
              </div>

              <div class="p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex items-start gap-3">
                <Info :size="16" class="text-indigo-400 shrink-0 mt-0.5" />
                <p class="text-[11px] text-slate-400 leading-relaxed italic">
                  Your review helps other readers discover hidden gems and deep insights. Be honest, be detailed.
                </p>
              </div>
            </div>
          </div>

          <button
            @click="isDraft = true"
            class="w-full py-4 rounded-2xl border border-slate-800 text-slate-400 font-bold hover:bg-slate-800 hover:text-white transition-all flex items-center justify-center gap-3"
          >
            <Save :size="18" />
            Save Draft
          </button>
        </div>
      </div>
    </div>

    <!-- Quote Metadata Modal -->
    <div
      v-if="showQuoteMetadata"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
      style="z-index: 9999;"
      @click="showQuoteMetadata = false"
    >
      <div
        @click.stop
        class="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-md w-full shadow-2xl"
      >
        <h3 class="text-lg font-bold text-white mb-4">Quote Details</h3>
        <p class="text-sm text-slate-400 mb-6">Add page number and chapter (optional) to help organize this quote</p>

        <div class="space-y-4 mb-6">
          <div>
            <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">
              Page Number
            </label>
            <input
              v-model="quotePageNumber"
              type="number"
              placeholder="e.g. 42"
              class="w-full bg-slate-950/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">
              Chapter
            </label>
            <input
              v-model="quoteChapter"
              type="text"
              placeholder="e.g. Chapter 3 or Introduction"
              class="w-full bg-slate-950/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label class="text-xs font-bold text-slate-500 uppercase tracking-widest block mb-2">
              Tags
            </label>
            <input
              v-model="quoteTags"
              type="text"
              placeholder="e.g. philosophy, key-insight, favorite"
              class="w-full bg-slate-950/50 border border-slate-700 rounded-lg px-4 py-2.5 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <p class="text-xs text-slate-500 mt-1.5">Separate multiple tags with commas</p>
          </div>
        </div>

        <div class="flex gap-3">
          <button
            @click="showQuoteMetadata = false"
            class="flex-1 px-4 py-2.5 rounded-lg border border-slate-700 text-slate-400 font-bold hover:border-slate-600 transition-all"
          >
            Cancel
          </button>
          <button
            @click="saveQuoteMetadata"
            class="flex-1 px-4 py-2.5 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-all"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// ToolbarButton component
import { defineComponent, h } from 'vue'

const ToolbarButton = defineComponent({
  name: 'ToolbarButton',
  props: {
    icon: [Object, Function],
    label: String
  },
  emits: ['command'],
  setup(props, { emit }) {
    return () => h('button', {
      type: 'button',
      onMousedown: (e) => {
        e.preventDefault()
        emit('command')
      },
      class: 'p-3 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all group relative',
      title: props.label
    }, [
      h(props.icon, { size: 18 }),
      h('span', {
        class: 'absolute -bottom-10 left-1/2 -translate-x-1/2 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50'
      }, props.label)
    ])
  }
})
</script>

<style>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.editor-surface {
  outline: none;
  font-size: 16px !important;
}

.editor-surface * {
  font-size: 16px !important;
}

.editor-surface:focus {
  outline: none;
}

.editor-surface p {
  font-size: 16px !important;
  margin: 0.5em 0;
}

.editor-surface h1 {
  font-size: 1.5em !important;
  font-weight: bold;
  margin: 1em 0 0.5em;
}

.editor-surface h2 {
  font-size: 1.25em !important;
  font-weight: bold;
  margin: 1em 0 0.5em;
}

.editor-surface blockquote {
  border-left: 4px solid rgb(99 102 241);
  padding-left: 1.5em;
  padding-right: 3em;
  padding-top: 0.5em;
  padding-bottom: 0.5em;
  margin: 0.75em 0;
  font-style: italic;
  color: rgb(226 232 240);
  background: rgba(99, 102, 241, 0.05);
  border-radius: 0 8px 8px 0;
  font-size: 16px !important;
  font-family: 'Georgia', 'Garamond', 'Times New Roman', serif;
  position: relative;
  transition: all 0.2s;
}

body.light .editor-surface blockquote {
  color: rgb(30 41 59); /* slate-800 for light mode */
  background: rgba(99, 102, 241, 0.08);
}

.editor-surface blockquote:hover {
  background: rgba(99, 102, 241, 0.1);
  border-left-color: rgb(129 140 248);
}

.quote-metadata-btn {
  position: absolute;
  bottom: 0.5em;
  right: 0.5em;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: rgb(99 102 241);
  border: none;
  color: white;
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: all 0.2s;
  user-select: none;
}

.quote-metadata-btn:hover {
  opacity: 1;
  transform: scale(1.1);
}

.editor-surface blockquote::before {
  content: '"';
  font-size: 2em;
  color: rgb(99 102 241);
  position: absolute;
  left: 0.2em;
  top: -0.1em;
  font-family: Georgia, serif;
}

.editor-surface ul {
  list-style-type: disc;
  margin-left: 2em;
  margin: 1em 0;
}

.editor-surface li {
  font-size: 16px !important;
}

.editor-surface a {
  color: rgb(99 102 241);
  text-decoration: underline;
  font-size: 16px !important;
}
</style>
