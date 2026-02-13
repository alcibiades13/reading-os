<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { getBookUrl, getBookUrlWithSuffix } from '@/utils/bookUrl'
import { ArrowLeft, SquarePen, Calendar, Star, Heart, MessageCircle, Share2, Send, BookOpen, Clock, Bookmark, Hash } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()
const quotesStore = useQuotesStore()

const bookId = computed(() => {
  const param = route.params.id
  if (param && param.includes('-')) {
    return param.split('-')[0]
  }
  return param
})

const book = computed(() => booksStore.currentBook)
const userBook = computed(() => {
  const numericBookId = parseInt(bookId.value)
  return userBooksStore.books.find(ub => ub.book?.id === numericBookId)
})

const bookQuotes = ref([])

const coverUrl = computed(() => {
  return book.value?.cover_image || 'https://via.placeholder.com/400x600?text=No+Cover'
})

const formattedDate = computed(() => {
  if (!userBook.value?.updated_at) return ''
  const date = new Date(userBook.value.updated_at)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
})

const formattedStartedAt = computed(() => {
  if (!userBook.value?.started_at) return null
  return new Date(userBook.value.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const formattedFinishedAt = computed(() => {
  if (!userBook.value?.finished_at) return null
  return new Date(userBook.value.finished_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const rating = computed(() => {
  if (!userBook.value?.rating) return null
  return parseFloat(userBook.value.rating)
})

const readingDuration = computed(() => {
  if (!userBook.value?.started_at || !userBook.value?.finished_at) return null
  const start = new Date(userBook.value.started_at)
  const end = new Date(userBook.value.finished_at)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  return days
})

// Interaction state
const liked = ref(false)
const likeCount = ref(0)
const comments = ref([])
const newComment = ref('')

const toggleLike = () => {
  liked.value = !liked.value
  likeCount.value = liked.value ? likeCount.value + 1 : likeCount.value - 1
}

const handleShare = () => {
  console.log('Share review')
}

const addComment = () => {
  if (!newComment.value.trim()) return

  comments.value.unshift({
    id: Date.now(),
    user: { name: 'You', avatar: null },
    text: newComment.value,
    timestamp: 'Just now',
    likes: 0
  })

  newComment.value = ''
}

const getInitials = (name) => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

onMounted(async () => {
  await Promise.all([
    booksStore.fetchBook(bookId.value),
    userBooksStore.fetchBooks()
  ])

  // Fetch quotes for sidebar
  const result = await quotesStore.fetchQuotes({ book: bookId.value })
  if (result.success) {
    bookQuotes.value = quotesStore.quotes.slice(0, 5)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-4 sm:p-6 lg:p-8">
    <div class="max-w-6xl mx-auto">
      <!-- Back Button -->
      <button
        @click="router.push(getBookUrl(book))"
        class="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6 lg:mb-8"
      >
        <ArrowLeft :size="18" />
        <span class="font-bold text-sm">Back to Book</span>
      </button>

      <!-- Header: Cover + Info + Reading Stats -->
      <div class="mb-8 lg:mb-12 rounded-2xl lg:rounded-3xl glass border-slate-800 p-4 sm:p-6 lg:p-8 bg-slate-900/30">
        <div class="flex flex-col sm:flex-row gap-4 sm:gap-6 lg:gap-8">
          <!-- Cover -->
          <div class="w-28 sm:w-32 lg:w-40 flex-shrink-0 mx-auto sm:mx-0">
            <div class="aspect-[2/3] rounded-xl lg:rounded-2xl overflow-hidden shadow-2xl border border-slate-800">
              <img :src="coverUrl" :alt="book?.title" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- Book Info -->
          <div class="flex-1 min-w-0">
            <h1 class="text-xl sm:text-2xl lg:text-4xl font-black text-white mb-1 sm:mb-2 text-center sm:text-left">{{ book?.title }}</h1>
            <p class="text-sm sm:text-base lg:text-xl text-slate-400 mb-3 sm:mb-4 text-center sm:text-left">{{ book?.authors?.[0]?.name }}</p>

            <div class="flex flex-wrap items-center justify-center sm:justify-start gap-3 sm:gap-6 text-xs sm:text-sm text-slate-500">
              <div class="flex items-center gap-1.5 sm:gap-2">
                <Calendar :size="14" />
                <span>{{ formattedDate }}</span>
              </div>
              <div v-if="rating" class="flex items-center gap-1.5 sm:gap-2">
                <Star :size="14" class="fill-yellow-500 text-yellow-500" />
                <span class="text-yellow-500 font-bold">{{ rating }}/10</span>
              </div>
              <div v-if="book?.pages" class="flex items-center gap-1.5 sm:gap-2">
                <BookOpen :size="14" />
                <span>{{ book.pages }} pages</span>
              </div>
            </div>

            <!-- Reading Journey Stats -->
            <div v-if="formattedStartedAt || formattedFinishedAt || readingDuration" class="mt-4 flex flex-wrap gap-3">
              <div v-if="formattedStartedAt" class="px-3 py-2 rounded-lg bg-slate-950/50 border border-slate-800">
                <span class="text-[10px] text-slate-500 uppercase tracking-wider block">Started</span>
                <span class="text-xs font-semibold text-slate-300">{{ formattedStartedAt }}</span>
              </div>
              <div v-if="formattedFinishedAt" class="px-3 py-2 rounded-lg bg-slate-950/50 border border-slate-800">
                <span class="text-[10px] text-slate-500 uppercase tracking-wider block">Finished</span>
                <span class="text-xs font-semibold text-emerald-400">{{ formattedFinishedAt }}</span>
              </div>
              <div v-if="readingDuration" class="px-3 py-2 rounded-lg bg-slate-950/50 border border-slate-800">
                <span class="text-[10px] text-slate-500 uppercase tracking-wider block">Duration</span>
                <span class="text-xs font-semibold text-indigo-400">{{ readingDuration }} days</span>
              </div>
            </div>

            <button
              @click="router.push(getBookUrlWithSuffix(book, 'review'))"
              class="mt-4 lg:mt-6 px-4 sm:px-6 py-2 sm:py-3 rounded-lg sm:rounded-xl border border-slate-700 text-slate-300 text-xs sm:text-sm font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center gap-2 mx-auto sm:mx-0 w-fit"
            >
              <SquarePen :size="14" />
              Edit Review
            </button>
          </div>
        </div>
      </div>

      <!-- Two Column Layout: Review + Sidebar -->
      <div class="flex flex-col lg:flex-row gap-6 lg:gap-8">
        <!-- Main Column: Review + Interactions -->
        <div class="flex-1 min-w-0 space-y-6">
          <!-- Review Content -->
          <div class="rounded-2xl lg:rounded-3xl glass border-slate-800 p-5 sm:p-8 lg:p-12 bg-slate-900/30">
            <div
              v-if="userBook?.review"
              class="review-display text-base text-slate-200 leading-relaxed"
              v-html="userBook.review"
            />
            <div v-else class="text-center py-8 lg:py-12">
              <SquarePen :size="32" class="text-slate-700 mx-auto mb-3" />
              <p class="text-slate-500 text-base italic mb-4">No review written yet</p>
              <button
                @click="router.push(getBookUrlWithSuffix(book, 'review'))"
                class="px-6 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-bold hover:bg-indigo-500 transition-all inline-flex items-center gap-2"
              >
                <SquarePen :size="14" />
                Write a Review
              </button>
            </div>
          </div>

          <!-- Interaction Buttons -->
          <div class="flex items-center gap-2 sm:gap-4">
            <button
              @click="toggleLike"
              class="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 rounded-lg sm:rounded-xl transition-all font-bold text-xs sm:text-sm"
              :class="liked ? 'bg-rose-500/10 text-rose-400 border border-rose-500/50' : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600'"
            >
              <Heart :size="16" :class="liked ? 'fill-rose-400' : ''" />
              <span>{{ likeCount > 0 ? likeCount : 'Like' }}</span>
            </button>

            <button
              class="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 rounded-lg sm:rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold text-xs sm:text-sm"
            >
              <MessageCircle :size="16" />
              <span>{{ comments.length > 0 ? comments.length : 'Comment' }}</span>
            </button>

            <button
              @click="handleShare"
              class="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-6 py-2 sm:py-3 rounded-lg sm:rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold text-xs sm:text-sm"
            >
              <Share2 :size="16" />
              <span class="hidden sm:inline">Share</span>
            </button>
          </div>

          <!-- Comments Section -->
          <div class="rounded-2xl lg:rounded-3xl glass border-slate-800 p-4 sm:p-6 lg:p-8 bg-slate-900/30">
            <h3 class="text-sm font-bold text-slate-500 uppercase tracking-widest mb-4 sm:mb-6">
              Comments ({{ comments.length }})
            </h3>

            <!-- Add Comment -->
            <div class="mb-6 sm:mb-8">
              <div class="flex gap-3 sm:gap-4">
                <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs sm:text-sm flex-shrink-0">
                  Y
                </div>
                <div class="flex-1">
                  <textarea
                    v-model="newComment"
                    placeholder="Share your thoughts..."
                    rows="3"
                    class="w-full bg-slate-950/50 border border-slate-700 rounded-xl px-3 sm:px-4 py-2.5 sm:py-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                    @keydown.ctrl.enter="addComment"
                  />
                  <div class="flex justify-end mt-2">
                    <button
                      @click="addComment"
                      :disabled="!newComment.trim()"
                      class="flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg bg-indigo-600 text-white text-xs sm:text-sm font-bold hover:bg-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Send :size="14" />
                      Post
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Comments List -->
            <div v-if="comments.length > 0" class="space-y-4 sm:space-y-6">
              <div
                v-for="comment in comments"
                :key="comment.id"
                class="flex gap-3 sm:gap-4"
              >
                <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs sm:text-sm flex-shrink-0">
                  {{ getInitials(comment.user.name) }}
                </div>
                <div class="flex-1">
                  <div class="bg-slate-950/50 border border-slate-800 rounded-xl p-3 sm:p-4">
                    <div class="flex items-center gap-2 mb-1.5 sm:mb-2">
                      <span class="font-bold text-slate-200 text-xs sm:text-sm">{{ comment.user.name }}</span>
                      <span class="text-[10px] sm:text-xs text-slate-500">{{ comment.timestamp }}</span>
                    </div>
                    <p class="text-slate-300 text-xs sm:text-sm leading-relaxed">{{ comment.text }}</p>
                  </div>
                  <div class="flex items-center gap-4 mt-1.5 sm:mt-2 pl-3 sm:pl-4">
                    <button class="text-[10px] sm:text-xs text-slate-500 hover:text-slate-400 transition-colors font-bold">
                      Like
                    </button>
                    <button class="text-[10px] sm:text-xs text-slate-500 hover:text-slate-400 transition-colors font-bold">
                      Reply
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-6 sm:py-8">
              <p class="text-slate-500 text-xs sm:text-sm italic">No comments yet. Be the first to comment!</p>
            </div>
          </div>
        </div>

        <!-- Sidebar -->
        <div class="w-full lg:w-72 xl:w-80 flex-shrink-0 space-y-4 lg:space-y-6">
          <!-- Book Details Card -->
          <div class="rounded-2xl glass border-slate-800 p-4 sm:p-5 bg-slate-900/30">
            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Book Details</h3>
            <div class="space-y-3">
              <div v-if="book?.pages" class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-slate-400">
                  <BookOpen :size="14" />
                  <span class="text-xs">Pages</span>
                </div>
                <span class="text-xs font-bold text-slate-200">{{ book.pages }}</span>
              </div>
              <div v-if="book?.language" class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-slate-400">
                  <Hash :size="14" />
                  <span class="text-xs">Language</span>
                </div>
                <span class="text-xs font-bold text-slate-200">{{ book.language?.toUpperCase() }}</span>
              </div>
              <div v-if="book?.published_date" class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-slate-400">
                  <Calendar :size="14" />
                  <span class="text-xs">Published</span>
                </div>
                <span class="text-xs font-bold text-slate-200">{{ book.published_date }}</span>
              </div>
              <div v-if="book?.genres?.length > 0" class="pt-2 border-t border-slate-800">
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="genre in book.genres"
                    :key="genre.id"
                    class="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold"
                  >
                    {{ genre.name }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quotes from this Book -->
          <div class="rounded-2xl glass border-slate-800 p-4 sm:p-5 bg-slate-900/30">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest">Quotes</h3>
              <span v-if="bookQuotes.length > 0" class="text-[10px] font-bold text-indigo-400">{{ bookQuotes.length }}</span>
            </div>

            <div v-if="bookQuotes.length > 0" class="space-y-3">
              <div
                v-for="quote in bookQuotes.slice(0, 3)"
                :key="quote.id"
                class="p-3 rounded-xl bg-slate-950/50 border border-slate-800"
              >
                <p class="text-xs text-slate-300 leading-relaxed italic line-clamp-3">
                  "{{ quote.text }}"
                </p>
                <p v-if="quote.page_number" class="text-[10px] text-slate-500 mt-1.5">p. {{ quote.page_number }}</p>
              </div>

              <button
                v-if="bookQuotes.length > 3"
                @click="router.push(getBookUrl(book))"
                class="w-full py-2 text-xs text-indigo-400 font-bold hover:text-indigo-300 transition-colors text-center"
              >
                View all {{ bookQuotes.length }} quotes
              </button>
            </div>

            <div v-else class="text-center py-4">
              <Bookmark :size="20" class="text-slate-700 mx-auto mb-2" />
              <p class="text-slate-500 text-[10px] italic">No quotes saved yet</p>
            </div>
          </div>

          <!-- Reading Stats Card -->
          <div v-if="userBook" class="rounded-2xl glass border-slate-800 p-4 sm:p-5 bg-slate-900/30">
            <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Reading Stats</h3>
            <div class="space-y-3">
              <div v-if="rating" class="flex items-center justify-between">
                <span class="text-xs text-slate-400">My Rating</span>
                <div class="flex items-center gap-1">
                  <Star :size="12" class="fill-yellow-500 text-yellow-500" />
                  <span class="text-xs font-bold text-yellow-500">{{ rating }}/10</span>
                </div>
              </div>
              <div v-if="userBook.status" class="flex items-center justify-between">
                <span class="text-xs text-slate-400">Status</span>
                <span class="text-xs font-bold text-emerald-400 capitalize">{{ userBook.status?.replace('_', ' ') }}</span>
              </div>
              <div v-if="readingDuration" class="flex items-center justify-between">
                <span class="text-xs text-slate-400">Duration</span>
                <div class="flex items-center gap-1">
                  <Clock :size="12" class="text-indigo-400" />
                  <span class="text-xs font-bold text-indigo-400">{{ readingDuration }} days</span>
                </div>
              </div>
              <div v-if="userBook.current_page && book?.pages" class="flex items-center justify-between">
                <span class="text-xs text-slate-400">Progress</span>
                <span class="text-xs font-bold text-slate-200">{{ userBook.current_page }}/{{ book.pages }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.review-display {
  font-size: 16px !important;
}

.review-display * {
  font-size: 16px !important;
}

.review-display p {
  margin: 1em 0;
}

.review-display h1 {
  font-size: 1.5em !important;
  font-weight: bold;
  margin: 1.5em 0 0.75em;
  color: rgb(226 232 240);
}

.review-display h2 {
  font-size: 1.25em !important;
  font-weight: bold;
  margin: 1.25em 0 0.75em;
  color: rgb(226 232 240);
}

.review-display blockquote {
  border-left: 4px solid rgb(99 102 241);
  padding-left: 1.5em;
  padding-right: 1em;
  padding-top: 0.75em;
  padding-bottom: 0.75em;
  margin: 0.75em 0;
  font-style: italic;
  color: rgb(226 232 240);
  background: rgba(99, 102, 241, 0.05);
  border-radius: 0 8px 8px 0;
  font-family: 'Georgia', 'Garamond', 'Times New Roman', serif;
  position: relative;
}

.review-display blockquote::before {
  content: '"';
  font-size: 2em;
  color: rgb(99 102 241);
  position: absolute;
  left: 0.2em;
  top: -0.05em;
  font-family: Georgia, serif;
}

.review-display ul {
  list-style-type: disc;
  margin-left: 2em;
  margin: 1em 0;
}

.review-display li {
  margin: 0.5em 0;
}

.review-display a {
  color: rgb(99 102 241);
  text-decoration: underline;
}

.review-display strong,
.review-display b {
  font-weight: bold;
  color: rgb(226 232 240);
}

.review-display em,
.review-display i {
  font-style: italic;
}
</style>
