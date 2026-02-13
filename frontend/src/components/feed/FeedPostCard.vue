<script setup>
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Heart, MessageCircle, Share2, CheckCircle, BookOpen, Bookmark,
  Quote as QuoteIcon, MessageSquare, TrendingUp, Star, ExternalLink, Brain, ChevronDown, Send
} from 'lucide-vue-next'
import StarRating from '@/components/ui/StarRating.vue'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import api from '@/services/api'
import { useAuthStore } from '@/stores/authStore'
import { getMediaUrl } from '@/utils/mediaUrl'

const router = useRouter()
const authStore = useAuthStore()

const props = defineProps({
  post: {
    type: Object,
    required: true
  },
  userBooks: {
    type: Array,
    default: () => []
  }
})

const getUserBookStatus = (bookId) => {
  if (!bookId) return null
  const userBook = props.userBooks.find(ub => ub.book?.id === bookId)
  return userBook?.status || null
}

const getStatusLabel = (status) => {
  const labels = {
    'currently_reading': 'Currently Reading',
    'read': 'Finished',
    'want_to_read': 'Want to Read',
    'abandoned': 'Abandoned'
  }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = {
    'currently_reading': 'default',
    'read': 'secondary',
    'want_to_read': 'outline',
    'abandoned': 'destructive'
  }
  return variants[status] || 'outline'
}

const emit = defineEmits(['book-added', 'book-updated'])

const addToLibrary = async (bookId, status) => {
  if (!bookId) return
  try {
    const response = await api.post('/reading/user-books/', {
      book: bookId,
      status: status
    })
    if (response.data) {
      emit('book-added', response.data)
    }
  } catch (err) {
    console.error('Failed to add book to library:', err)
  }
}

const updateBookStatus = async (bookId, newStatus) => {
  if (!bookId) return
  const userBook = props.userBooks.find(ub => ub.book?.id === bookId)
  if (!userBook) return

  try {
    const response = await api.patch(`/reading/user-books/${userBook.id}/`, {
      status: newStatus
    })
    if (response.data) {
      emit('book-updated', response.data)
    }
  } catch (err) {
    console.error('Failed to update book status:', err)
  }
}

const statusOptions = [
  { value: 'want_to_read', label: 'Want to Read', icon: Bookmark },
  { value: 'currently_reading', label: 'Currently Reading', icon: BookOpen },
  { value: 'read', label: 'Finished', icon: CheckCircle },
  { value: 'abandoned', label: 'Abandoned', icon: Star }
]

// Like state
const liked = ref(props.post.stats.hasLiked)
const likeCount = ref(props.post.stats.likes)
const likePending = ref(false)

const toggleLike = async () => {
  if (likePending.value) return
  // Optimistic update
  liked.value = !liked.value
  likeCount.value = liked.value ? likeCount.value + 1 : likeCount.value - 1
  likePending.value = true
  try {
    const response = await api.post(`/social/feed/${props.post.id}/toggle_like/`)
    liked.value = response.data.liked
    likeCount.value = response.data.likes_count
  } catch (err) {
    // Revert on error
    liked.value = !liked.value
    likeCount.value = liked.value ? likeCount.value + 1 : likeCount.value - 1
    console.error('Failed to toggle like:', err)
  } finally {
    likePending.value = false
  }
}

// Comment state
const showComments = ref(false)
const comments = ref([])
const commentText = ref('')
const commentsLoading = ref(false)
const commentSending = ref(false)
const commentCount = ref(props.post.stats.comments)
const commentInputRef = ref(null)

const toggleComments = async () => {
  showComments.value = !showComments.value
  if (showComments.value && comments.value.length === 0) {
    await fetchComments()
  }
  if (showComments.value) {
    await nextTick()
    commentInputRef.value?.focus()
  }
}

const fetchComments = async () => {
  commentsLoading.value = true
  try {
    const response = await api.get(`/social/feed/${props.post.id}/comments/`)
    comments.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch comments:', err)
  } finally {
    commentsLoading.value = false
  }
}

const submitComment = async () => {
  const content = commentText.value.trim()
  if (!content || commentSending.value) return
  commentSending.value = true
  try {
    const response = await api.post(`/social/feed/${props.post.id}/add_comment/`, { content })
    comments.value.push(response.data)
    commentCount.value++
    commentText.value = ''
  } catch (err) {
    console.error('Failed to add comment:', err)
  } finally {
    commentSending.value = false
  }
}

const getCommentAuthorInitials = (author) => {
  const name = `${author.first_name || ''} ${author.last_name || ''}`.trim()
  if (!name) return '?'
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

const getInitials = (name) => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}

const activityConfig = {
  finished: { icon: CheckCircle, label: 'Finished', color: 'text-emerald-400 bg-emerald-400/10' },
  started: { icon: BookOpen, label: 'Started Reading', color: 'text-indigo-400 bg-indigo-400/10' },
  want_to_read: { icon: Bookmark, label: 'Want to Read', color: 'text-sky-400 bg-sky-400/10' },
  quote: { icon: QuoteIcon, label: 'Shared a Quote', color: 'text-purple-400 bg-purple-400/10' },
  review: { icon: MessageSquare, label: 'Reviewed', color: 'text-sky-400 bg-sky-400/10' },
  progress: { icon: TrendingUp, label: 'Reading Progress', color: 'text-amber-400 bg-amber-400/10' },
  challenge: { icon: Star, label: 'Challenge Update', color: 'text-pink-400 bg-pink-400/10' },
  list: { icon: MessageCircle, label: 'Created a List', color: 'text-indigo-400 bg-indigo-400/10' },
  vocabulary: { icon: Brain, label: 'Expanded Lexicon', color: 'text-emerald-400 bg-emerald-400/10' }
}

// Helper to strip HTML tags and get text preview
const stripHtml = (html) => {
  if (!html) return ''
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent || div.innerText || ''
}

const config = computed(() => activityConfig[props.post.type])

const handleBookClick = () => {
  if (props.post.bookId) {
    router.push(`/books/${props.post.bookId}`)
  }
}

const formatCommentTime = (dateStr) => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`
  return `${Math.floor(diff / 86400)}d`
}
</script>

<template>
  <div class="group border-b border-slate-800 py-3 lg:glass lg:bg-slate-900/50 lg:rounded-2xl lg:border lg:border-slate-800 lg:p-5 lg:hover:border-indigo-500/50 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4 lg:shadow-xl lg:shadow-slate-950/20">
    <!-- Header -->
    <div class="flex items-center gap-2.5 mb-2 lg:mb-4">
      <div class="w-7 h-7 lg:w-10 lg:h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-[9px] lg:text-xs font-bold ring-1 lg:ring-2 ring-slate-800 shrink-0 overflow-hidden">
        <img v-if="post.user.avatar" :src="getMediaUrl(post.user.avatar)" class="w-full h-full object-cover" />
        <span v-else>{{ getInitials(post.user.name) }}</span>
      </div>
      <div class="min-w-0 flex-1">
        <span class="text-xs lg:text-sm font-bold text-white truncate">{{ post.user.name }}</span>
        <div :class="['flex items-center gap-1 text-[9px] lg:text-[10px] font-bold uppercase tracking-wider', config.color.replace(/bg-\S+/g, '')]">
          <component :is="config.icon" :size="10" />
          {{ config.label }}
        </div>
      </div>
      <span class="text-[10px] lg:text-xs text-slate-600 shrink-0 self-start">{{ post.timestamp }}</span>
    </div>

    <!-- Content Area -->
    <div class="flex gap-3 lg:gap-6 mb-2 lg:mb-4">
      <!-- Book Cover -->
      <div
        v-if="post.book.cover"
        @click="handleBookClick"
        class="hidden sm:block shrink-0 w-[80px] h-[120px] rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 group-hover:scale-105 transition-transform duration-300 cursor-pointer"
      >
        <img :src="post.book.cover" :alt="post.book.title" class="w-full h-full object-cover" />
      </div>

      <div class="flex-1 min-w-0">
        <div class="mb-1.5 lg:mb-3">
          <h3
            @click="handleBookClick"
            class="text-xs lg:text-base font-bold text-slate-100 group-hover:text-indigo-400 transition-colors cursor-pointer truncate"
          >
            {{ post.book.title }}
          </h3>
          <p class="text-[11px] lg:text-sm text-slate-500">{{ post.book.author }}</p>

          <!-- Status Dropdown for want_to_read and started types -->
          <div v-if="post.type === 'want_to_read' || post.type === 'started'" class="mt-2 lg:mt-3">
            <DropdownMenu>
              <DropdownMenuTrigger as-child>
                <button
                  class="px-2.5 py-1 lg:px-3 lg:py-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] lg:text-xs font-semibold hover:bg-indigo-500/20 transition-all flex items-center gap-1.5"
                >
                  {{ getUserBookStatus(post.bookId) ? getStatusLabel(getUserBookStatus(post.bookId)) : 'Add to Library' }}
                  <ChevronDown :size="12" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" class="bg-slate-900 border-slate-800">
                <DropdownMenuItem
                  v-for="option in statusOptions"
                  :key="option.value"
                  @click="getUserBookStatus(post.bookId) ? updateBookStatus(post.bookId, option.value) : addToLibrary(post.bookId, option.value)"
                  class="text-xs cursor-pointer hover:bg-slate-800 text-slate-200 flex items-center gap-2"
                >
                  <component :is="option.icon" :size="14" />
                  {{ option.label }}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        <!-- Activity Specific Content -->
        <div class="space-y-1.5 lg:space-y-3">
          <blockquote v-if="post.type === 'quote' && post.content.quote" class="relative p-2.5 lg:p-4 rounded-lg lg:rounded-xl bg-indigo-500/5 border-l-2 lg:border-l-4 border-indigo-500 italic text-slate-200 font-serif text-xs lg:text-base leading-relaxed">
            "{{ post.content.quote }}"
          </blockquote>

          <div v-if="post.content.review">
            <p class="text-xs lg:text-sm text-slate-300 leading-relaxed italic line-clamp-2 lg:line-clamp-3">
              "{{ stripHtml(post.content.review) }}"
            </p>
            <button
              v-if="post.bookId"
              @click="router.push(`/books/${post.bookId}/review-view`)"
              class="mt-1.5 lg:mt-3 text-[10px] lg:text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
            >
              Read Full Review
              <ExternalLink :size="10" />
            </button>
          </div>

          <div v-if="post.type === 'progress' && post.content.progress" class="flex items-center gap-2">
            <div class="flex-1 bg-slate-800 rounded-full h-1.5 lg:h-2 overflow-hidden">
              <div
                class="bg-indigo-500 h-full rounded-full transition-all duration-1000 ease-out"
                :style="{ width: `${post.content.progress}%` }"
              />
            </div>
            <span class="text-[10px] font-bold text-indigo-400 shrink-0">{{ post.content.progress }}%</span>
          </div>

          <StarRating
            v-if="post.content.rating"
            :model-value="post.content.rating"
            :size="12"
            :readonly="true"
            :show-value="true"
          />

          <p v-if="post.content.note" class="text-[11px] lg:text-sm text-slate-400 line-clamp-2">
            {{ post.content.note }}
          </p>

          <div v-if="post.content.challengeTitle" class="p-2 lg:p-4 rounded-lg lg:rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
            <p class="text-[11px] lg:text-sm font-bold text-indigo-400">{{ post.content.challengeTitle }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="pt-2 lg:pt-3 border-t border-slate-800/50 lg:border-slate-800 flex items-center justify-between">
      <div class="flex items-center gap-4">
        <button
          @click="toggleLike"
          :class="[
            'flex items-center gap-1 transition-colors',
            liked ? 'text-indigo-400' : 'text-slate-500 hover:text-indigo-400'
          ]"
        >
          <Heart :size="14" :fill="liked ? 'currentColor' : 'none'" :class="liked ? 'animate-in zoom-in-50 duration-300' : ''" />
          <span class="text-[10px] lg:text-xs font-bold">{{ likeCount }}</span>
        </button>

        <button
          @click="toggleComments"
          :class="[
            'flex items-center gap-1 transition-colors',
            showComments ? 'text-sky-400' : 'text-slate-500 hover:text-sky-400'
          ]"
        >
          <MessageCircle :size="14" />
          <span class="text-[10px] lg:text-xs font-bold">{{ commentCount }}</span>
        </button>
      </div>

      <button class="flex items-center gap-1 text-slate-500 hover:text-emerald-400 transition-colors">
        <Share2 :size="14" />
      </button>
    </div>

    <!-- Comments Section -->
    <div v-if="showComments" class="mt-3 pt-3 border-t border-slate-800/50 space-y-3">
      <!-- Loading -->
      <div v-if="commentsLoading" class="flex justify-center py-2">
        <div class="w-4 h-4 rounded-full border-2 border-slate-700 border-t-indigo-500 animate-spin" />
      </div>

      <!-- Comment List -->
      <div v-else-if="comments.length > 0" class="space-y-2.5">
        <div v-for="comment in comments" :key="comment.id" class="flex gap-2">
          <div class="w-5 h-5 lg:w-6 lg:h-6 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-white text-[7px] lg:text-[8px] font-bold shrink-0 overflow-hidden">
            <img v-if="comment.author.avatar" :src="getMediaUrl(comment.author.avatar)" class="w-full h-full object-cover" />
            <span v-else>{{ getCommentAuthorInitials(comment.author) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1.5">
              <span class="text-[10px] lg:text-xs font-bold text-slate-300">{{ comment.author.first_name }} {{ comment.author.last_name }}</span>
              <span class="text-[9px] text-slate-600">{{ formatCommentTime(comment.created_at) }}</span>
            </div>
            <p class="text-[11px] lg:text-xs text-slate-400 leading-relaxed">{{ comment.content }}</p>
          </div>
        </div>
      </div>

      <!-- No comments yet -->
      <p v-else-if="!commentsLoading" class="text-[10px] text-slate-600 text-center py-1">No comments yet</p>

      <!-- Comment Input -->
      <div class="flex items-center gap-2">
        <div class="w-5 h-5 lg:w-6 lg:h-6 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-[7px] lg:text-[8px] font-bold shrink-0">
          {{ getInitials(authStore.user?.first_name && authStore.user?.last_name ? `${authStore.user.first_name} ${authStore.user.last_name}` : authStore.user?.username || 'U') }}
        </div>
        <div class="flex-1 flex items-center gap-1.5 bg-slate-800/50 rounded-lg border border-slate-700/50 px-2.5 py-1.5">
          <input
            ref="commentInputRef"
            v-model="commentText"
            @keydown.enter="submitComment"
            type="text"
            placeholder="Write a comment..."
            class="flex-1 bg-transparent text-[11px] lg:text-xs text-slate-200 placeholder-slate-600 outline-none"
          />
          <button
            @click="submitComment"
            :disabled="!commentText.trim() || commentSending"
            :class="[
              'transition-colors shrink-0',
              commentText.trim() ? 'text-indigo-400 hover:text-indigo-300' : 'text-slate-700'
            ]"
          >
            <Send :size="12" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
