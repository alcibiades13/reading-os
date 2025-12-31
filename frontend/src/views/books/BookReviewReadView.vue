<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { ArrowLeft, SquarePen, Calendar, Star, Heart, MessageCircle, Share2, Send } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()

const bookId = computed(() => route.params.id)

const book = computed(() => booksStore.currentBook)
const userBook = computed(() => {
  const numericBookId = parseInt(bookId.value)
  return userBooksStore.books.find(ub => ub.book?.id === numericBookId)
})

const coverUrl = computed(() => {
  return book.value?.cover_image || 'https://via.placeholder.com/400x600?text=No+Cover'
})

const formattedDate = computed(() => {
  if (!userBook.value?.updated_at) return ''
  const date = new Date(userBook.value.updated_at)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
})

const rating = computed(() => {
  if (!userBook.value?.rating) return null
  return parseFloat(userBook.value.rating)
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
  // TODO: Implement share functionality
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
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-8">
    <div class="max-w-5xl mx-auto">
      <!-- Header -->
      <div class="mb-12">
        <button
          @click="router.push(`/books/${bookId}`)"
          class="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8"
        >
          <ArrowLeft :size="18" />
          <span class="font-bold text-sm">Back to Book</span>
        </button>

        <div class="flex items-start gap-8">
          <!-- Cover -->
          <div class="w-40 flex-shrink-0">
            <div class="aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl border border-slate-800">
              <img :src="coverUrl" :alt="book?.title" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- Book Info -->
          <div class="flex-1">
            <h1 class="text-4xl font-black text-white mb-2">{{ book?.title }}</h1>
            <p class="text-xl text-slate-400 mb-4">{{ book?.authors?.[0]?.name }}</p>

            <div class="flex items-center gap-6 text-sm text-slate-500">
              <div class="flex items-center gap-2">
                <Calendar :size="14" />
                <span>{{ formattedDate }}</span>
              </div>
              <div v-if="rating" class="flex items-center gap-2">
                <Star :size="14" class="fill-yellow-500 text-yellow-500" />
                <span class="text-yellow-500 font-bold">{{ rating }}/10</span>
              </div>
            </div>

            <button
              @click="router.push(`/books/${bookId}/review`)"
              class="mt-6 px-6 py-3 rounded-xl border border-slate-700 text-slate-300 font-bold hover:border-indigo-500 hover:text-indigo-400 hover:bg-indigo-500/5 transition-all flex items-center gap-2"
            >
              <SquarePen :size="16" />
              Edit Review
            </button>
          </div>
        </div>
      </div>

      <!-- Review Content -->
      <div class="rounded-3xl glass border-slate-800 p-12 bg-slate-900/30">
        <div
          v-if="userBook?.review"
          class="review-display text-base text-slate-200 leading-relaxed"
          v-html="userBook.review"
        />
        <div v-else class="text-center py-12">
          <p class="text-slate-500 text-lg italic">No review yet</p>
        </div>
      </div>

      <!-- Interaction Buttons -->
      <div class="flex items-center gap-4 pt-6">
        <button
          @click="toggleLike"
          class="flex items-center gap-2 px-6 py-3 rounded-xl transition-all font-bold"
          :class="liked ? 'bg-rose-500/10 text-rose-400 border border-rose-500/50' : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600'"
        >
          <Heart :size="18" :class="liked ? 'fill-rose-400' : ''" />
          <span>{{ likeCount > 0 ? likeCount : 'Like' }}</span>
        </button>

        <button
          class="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold"
        >
          <MessageCircle :size="18" />
          <span>{{ comments.length > 0 ? comments.length : 'Comment' }}</span>
        </button>

        <button
          @click="handleShare"
          class="flex items-center gap-2 px-6 py-3 rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold"
        >
          <Share2 :size="18" />
          <span>Share</span>
        </button>
      </div>

      <!-- Comments Section -->
      <div class="mt-12 rounded-3xl glass border-slate-800 p-8 bg-slate-900/30">
        <h3 class="text-sm font-bold text-slate-500 uppercase tracking-widest mb-6">
          Comments ({{ comments.length }})
        </h3>

        <!-- Add Comment -->
        <div class="mb-8">
          <div class="flex gap-4">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              Y
            </div>
            <div class="flex-1">
              <textarea
                v-model="newComment"
                placeholder="Share your thoughts..."
                rows="3"
                class="w-full bg-slate-950/50 border border-slate-700 rounded-xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                @keydown.ctrl.enter="addComment"
              />
              <div class="flex justify-end mt-2">
                <button
                  @click="addComment"
                  :disabled="!newComment.trim()"
                  class="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white font-bold hover:bg-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send :size="16" />
                  Post Comment
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Comments List -->
        <div v-if="comments.length > 0" class="space-y-6">
          <div
            v-for="comment in comments"
            :key="comment.id"
            class="flex gap-4"
          >
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
              {{ getInitials(comment.user.name) }}
            </div>
            <div class="flex-1">
              <div class="bg-slate-950/50 border border-slate-800 rounded-xl p-4">
                <div class="flex items-center gap-2 mb-2">
                  <span class="font-bold text-slate-200 text-sm">{{ comment.user.name }}</span>
                  <span class="text-xs text-slate-500">{{ comment.timestamp }}</span>
                </div>
                <p class="text-slate-300 text-sm leading-relaxed">{{ comment.text }}</p>
              </div>
              <div class="flex items-center gap-4 mt-2 pl-4">
                <button class="text-xs text-slate-500 hover:text-slate-400 transition-colors font-bold">
                  Like
                </button>
                <button class="text-xs text-slate-500 hover:text-slate-400 transition-colors font-bold">
                  Reply
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="text-center py-8">
          <p class="text-slate-500 text-sm italic">No comments yet. Be the first to comment!</p>
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
