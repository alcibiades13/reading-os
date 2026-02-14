<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useAuthStore } from '@/stores/authStore'
import { booksAPI, socialAPI } from '@/services/api'
import { getBookUrlWithSuffix } from '@/utils/bookUrl'
import { ArrowLeft, Calendar, Star, Heart, MessageCircle, Share2, Send, Loader2, User, SquarePen, BookOpen, Hash, Clock, ChevronRight } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const authStore = useAuthStore()

// Route params
const bookId = computed(() => {
  const param = route.params.id
  if (param && param.includes('-')) {
    return param.split('-')[0]
  }
  return param
})
const userId = computed(() => route.params.userId)

// State
const loading = ref(true)
const error = ref(null)
const reviewData = ref(null)
const communityReviews = ref([])
const communityReviewsCount = ref(0)

// Computed
const book = computed(() => reviewData.value?.book || booksStore.currentBook)

const coverUrl = computed(() => {
  return book.value?.cover_image || 'https://via.placeholder.com/400x600?text=No+Cover'
})

const isOwnReview = computed(() => {
  if (!authStore.currentUser || !userId.value) return false
  return String(authStore.currentUser.id) === String(userId.value)
})

const formattedDate = computed(() => {
  if (!reviewData.value?.finished_at && !reviewData.value?.updated_at) return ''
  const dateStr = reviewData.value.finished_at || reviewData.value.updated_at
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
})

const rating = computed(() => {
  if (!reviewData.value?.rating) return null
  return reviewData.value.rating
})

const userName = computed(() => {
  if (!reviewData.value?.user) return 'Unknown User'
  const { first_name, last_name } = reviewData.value.user
  return `${first_name || ''} ${last_name || ''}`.trim() || 'Unknown User'
})

const userInitials = computed(() => {
  if (!reviewData.value?.user) return '?'
  const { first_name, last_name } = reviewData.value.user
  const first = first_name?.charAt(0) || ''
  const last = last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
})

const formattedStartedAt = computed(() => {
  if (!reviewData.value?.started_at) return null
  return new Date(reviewData.value.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const formattedFinishedAt = computed(() => {
  if (!reviewData.value?.finished_at) return null
  return new Date(reviewData.value.finished_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})

const readingDuration = computed(() => {
  if (!reviewData.value?.started_at || !reviewData.value?.finished_at) return null
  const start = new Date(reviewData.value.started_at)
  const end = new Date(reviewData.value.finished_at)
  const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
  return days
})

const getReviewerInitials = (user) => {
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
}

const getReviewerName = (user) => {
  return `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Unknown'
}

const myInitials = computed(() => {
  if (!authStore.currentUser) return '?'
  const { first_name, last_name } = authStore.currentUser
  const first = first_name?.charAt(0) || ''
  const last = last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
})

// Interaction state
const liked = ref(false)
const likeCount = ref(0)
const comments = ref([])
const newComment = ref('')
const isSubmittingComment = ref(false)
const isTogglingLike = ref(false)

const userBookId = computed(() => reviewData.value?.id)

const toggleLike = async () => {
  if (isTogglingLike.value || !userBookId.value) return
  isTogglingLike.value = true
  try {
    const response = await socialAPI.toggleReviewLike(userBookId.value)
    liked.value = response.data.liked
    likeCount.value = response.data.like_count
  } catch (err) {
    console.error('Failed to toggle like:', err)
  } finally {
    isTogglingLike.value = false
  }
}

const handleShare = () => {
  navigator.clipboard.writeText(window.location.href)
}

const addComment = async () => {
  if (!newComment.value.trim() || isSubmittingComment.value || !userBookId.value) return
  isSubmittingComment.value = true
  try {
    const response = await socialAPI.addReviewComment(userBookId.value, newComment.value.trim())
    comments.value.unshift(response.data)
    newComment.value = ''
  } catch (err) {
    console.error('Failed to add comment:', err)
  } finally {
    isSubmittingComment.value = false
  }
}

const deleteComment = async (commentId) => {
  try {
    await socialAPI.deleteReviewComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
  } catch (err) {
    console.error('Failed to delete comment:', err)
  }
}

const fetchInteractionData = async () => {
  if (!userBookId.value) return
  try {
    const [commentsRes, likeRes] = await Promise.all([
      socialAPI.reviewComments(userBookId.value).catch(() => null),
      socialAPI.reviewLikeStatus(userBookId.value).catch(() => null)
    ])

    if (commentsRes?.data) {
      const data = commentsRes.data?.results || commentsRes.data || []
      comments.value = Array.isArray(data) ? data : []
    }
    if (likeRes?.data) {
      liked.value = likeRes.data.liked
      likeCount.value = likeRes.data.like_count
    }
  } catch (err) {
    console.error('Failed to fetch interaction data:', err)
  }
}

const getCommentAuthorName = (comment) => {
  if (!comment.author) return 'Unknown'
  return `${comment.author.first_name || ''} ${comment.author.last_name || ''}`.trim() || 'Unknown'
}

const getCommentAuthorInitials = (comment) => {
  if (!comment.author) return '?'
  const first = comment.author.first_name?.charAt(0) || ''
  const last = comment.author.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
}

const formatCommentDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const goBack = () => {
  router.push(`/books/${route.params.id}`)
}

// Fetch review data
const fetchReview = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await booksAPI.userReview(bookId.value, userId.value)
    reviewData.value = response.data
  } catch (err) {
    console.error('Failed to fetch review:', err)
    error.value = err.response?.data?.error || 'Failed to load review'
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchReview()

  // Initialize like data from review response
  if (reviewData.value) {
    likeCount.value = reviewData.value.likes_count || 0
    liked.value = reviewData.value.has_liked || false
  }

  // Also fetch book details and community reviews
  try {
    await booksStore.fetchBook(bookId.value)
  } catch (e) { /* book info from reviewData is enough */ }

  try {
    const response = await booksAPI.communityActivity(bookId.value)
    // Filter out the current review's author from community reviews
    const allReviews = response.data.reviews || []
    communityReviews.value = allReviews.filter(r => String(r.user.id) !== String(userId.value))
    communityReviewsCount.value = response.data.reviews_count || 0
  } catch (err) {
    console.error('Failed to fetch community reviews:', err)
  }

  // Fetch comments and full like status
  await fetchInteractionData()
})
</script>

<template>
  <div class="animate-in fade-in duration-700">

    <!-- ==================== MOBILE HEADER ==================== -->
    <header class="lg:hidden sticky top-0 z-30 border-b border-white/5 bg-slate-900/80 backdrop-blur-xl">
      <div class="px-4 py-3 flex items-center gap-3">
        <button
          @click="goBack"
          class="p-2 -ml-2 rounded-xl text-slate-400 active:bg-white/5 transition-colors"
        >
          <ArrowLeft :size="20" />
        </button>
        <div class="flex-1 min-w-0">
          <h1 class="text-sm font-bold text-white truncate">{{ userName }}'s Review</h1>
          <p class="text-[10px] text-slate-500 truncate">{{ book?.title }}</p>
        </div>
        <button
          v-if="isOwnReview"
          @click="router.push(getBookUrlWithSuffix(book, 'review'))"
          class="px-3 py-1.5 rounded-lg border border-slate-700 text-indigo-400 text-xs font-bold hover:border-indigo-500 transition-all flex items-center gap-1.5"
        >
          <SquarePen :size="12" />
          Edit
        </button>
      </div>
    </header>

    <!-- Page Container -->
    <div class="w-full max-w-[1400px] mx-auto px-4 lg:px-6 py-4 lg:py-10">

      <!-- Desktop Back Button -->
      <button
        @click="goBack"
        class="hidden lg:flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6"
      >
        <ArrowLeft :size="18" />
        <span class="font-bold text-sm">Back to Book</span>
      </button>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-24">
        <Loader2 :size="32" class="text-indigo-400 animate-spin" />
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-24">
        <div class="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mx-auto mb-4">
          <User :size="32" class="text-rose-400" />
        </div>
        <h2 class="text-xl font-bold text-white mb-2">Review Not Found</h2>
        <p class="text-slate-500">{{ error }}</p>
        <button
          @click="goBack"
          class="mt-6 px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-400 transition-colors"
        >
          Return to Book
        </button>
      </div>

      <!-- Review Content -->
      <template v-else-if="reviewData">

        <!-- ==================== COMPACT HEADER ==================== -->
        <div class="flex items-start gap-4 lg:gap-6 mb-6 lg:mb-10">
          <!-- Small Cover -->
          <div class="w-16 sm:w-20 flex-shrink-0">
            <div class="aspect-[2/3] rounded-lg lg:rounded-xl overflow-hidden shadow-xl border border-slate-800">
              <img :src="coverUrl" :alt="book?.title" class="w-full h-full object-cover" />
            </div>
          </div>

          <!-- Book Info + Meta -->
          <div class="flex-1 min-w-0">
            <h1 class="text-lg sm:text-xl lg:text-2xl font-black text-white leading-tight mb-0.5 sm:mb-1">{{ book?.title }}</h1>
            <p class="text-sm text-slate-400 mb-3">
              {{ book?.authors?.map(a => a.name).join(', ') || 'Unknown Author' }}
            </p>

            <!-- Meta row -->
            <div class="flex flex-wrap items-center gap-2 sm:gap-3">
              <!-- Reviewer pill -->
              <div class="flex items-center gap-2 px-2.5 py-1.5 rounded-full bg-slate-800/60 border border-slate-700/50">
                <div class="w-5 h-5 rounded-full bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 text-[9px] font-bold overflow-hidden">
                  <img
                    v-if="reviewData.user.avatar && !reviewData.user.avatar.includes('placeholder')"
                    :src="reviewData.user.avatar"
                    class="w-full h-full object-cover"
                  />
                  <span v-else>{{ userInitials }}</span>
                </div>
                <span class="text-xs font-semibold text-slate-300">{{ userName }}</span>
              </div>

              <!-- Rating pill -->
              <div v-if="rating" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/20">
                <Star :size="11" class="fill-yellow-500 text-yellow-500" />
                <span class="text-xs font-bold text-yellow-500">{{ rating }}/10</span>
              </div>

              <!-- Date -->
              <span v-if="formattedDate" class="text-xs text-slate-500 hidden sm:inline">{{ formattedDate }}</span>

              <!-- Edit button (desktop, only for own review) -->
              <button
                v-if="isOwnReview"
                @click="router.push(getBookUrlWithSuffix(book, 'review'))"
                class="hidden sm:flex ml-auto px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 text-xs font-bold hover:border-indigo-500 hover:text-indigo-400 transition-all items-center gap-1.5"
              >
                <SquarePen :size="12" />
                Edit
              </button>
            </div>
          </div>
        </div>

        <!-- ==================== TWO COLUMN LAYOUT ==================== -->
        <div class="flex flex-col lg:flex-row gap-6 lg:gap-8">

          <!-- ========== MAIN COLUMN ========== -->
          <div class="flex-1 min-w-0 space-y-4 sm:space-y-6">

            <!-- Review Content -->
            <div class="rounded-2xl border border-slate-800 p-4 sm:p-8 lg:p-10 bg-slate-900/40">
              <div
                v-if="reviewData.review"
                class="review-display text-base text-slate-200 leading-relaxed"
                v-html="reviewData.review"
              />
              <div v-else class="text-center py-8 lg:py-12">
                <p class="text-slate-500 text-sm sm:text-lg italic">This user hasn't written a review yet.</p>
              </div>
            </div>

            <!-- Interaction Buttons -->
            <div class="flex items-center gap-2 sm:gap-3">
              <button
                @click="toggleLike"
                class="flex items-center gap-1.5 px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl transition-all font-bold text-xs sm:text-sm"
                :class="liked ? 'bg-rose-500/10 text-rose-400 border border-rose-500/50' : 'bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600'"
              >
                <Heart :size="15" :class="liked ? 'fill-rose-400' : ''" />
                <span>{{ likeCount > 0 ? likeCount : 'Like' }}</span>
              </button>

              <button
                class="flex items-center gap-1.5 px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold text-xs sm:text-sm"
              >
                <MessageCircle :size="15" />
                <span>{{ comments.length > 0 ? comments.length : 'Comment' }}</span>
              </button>

              <button
                @click="handleShare"
                class="flex items-center gap-1.5 px-3 sm:px-5 py-2 sm:py-2.5 rounded-xl bg-slate-800/50 text-slate-400 border border-slate-700 hover:border-slate-600 transition-all font-bold text-xs sm:text-sm"
              >
                <Share2 :size="15" />
                <span class="hidden sm:inline">Share</span>
              </button>
            </div>

            <!-- Comments Section -->
            <div class="rounded-2xl border border-slate-800 p-4 sm:p-6 lg:p-8 bg-slate-900/40">
              <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4 sm:mb-6">
                Comments ({{ comments.length }})
              </h3>

              <!-- Add Comment -->
              <div class="mb-6">
                <div class="flex gap-3">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-[10px] flex-shrink-0">
                    {{ myInitials }}
                  </div>
                  <div class="flex-1">
                    <textarea
                      v-model="newComment"
                      placeholder="Share your thoughts..."
                      rows="2"
                      class="w-full bg-slate-950/50 border border-slate-700 rounded-xl px-3 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 resize-none"
                      @keydown.ctrl.enter="addComment"
                    />
                    <div class="flex justify-end mt-2">
                      <button
                        @click="addComment"
                        :disabled="!newComment.trim() || isSubmittingComment"
                        class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Send :size="12" />
                        {{ isSubmittingComment ? 'Posting...' : 'Post' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Comments List -->
              <div v-if="comments.length > 0" class="space-y-4">
                <div v-for="comment in comments" :key="comment.id" class="flex gap-3">
                  <div class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-[10px] flex-shrink-0">
                    {{ getCommentAuthorInitials(comment) }}
                  </div>
                  <div class="flex-1">
                    <div class="bg-slate-950/50 border border-slate-800 rounded-xl p-3">
                      <div class="flex items-center gap-2 mb-1">
                        <span class="font-bold text-slate-200 text-xs">{{ getCommentAuthorName(comment) }}</span>
                        <span class="text-[10px] text-slate-500">{{ formatCommentDate(comment.created_at) }}</span>
                      </div>
                      <p class="text-slate-300 text-xs leading-relaxed">{{ comment.content }}</p>
                    </div>
                    <div class="flex items-center gap-4 mt-1.5 pl-3">
                      <button
                        v-if="comment.author?.id === authStore.currentUser?.id"
                        @click="deleteComment(comment.id)"
                        class="text-[10px] text-rose-500/70 hover:text-rose-400 transition-colors font-bold"
                      >Delete</button>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else class="text-center py-6">
                <p class="text-slate-600 text-xs italic">No comments yet. Be the first to comment!</p>
              </div>
            </div>
          </div>

          <!-- ========== SIDEBAR ========== -->
          <div class="hidden lg:block w-72 xl:w-80 flex-shrink-0 space-y-5">

            <!-- Reading Journey Card -->
            <div v-if="formattedStartedAt || formattedFinishedAt || readingDuration" class="rounded-2xl border border-slate-800 p-5 bg-slate-900/40">
              <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Reading Journey</h3>
              <div class="space-y-3">
                <div v-if="formattedStartedAt" class="flex items-center justify-between">
                  <span class="text-xs text-slate-400">Started</span>
                  <span class="text-xs font-semibold text-slate-200">{{ formattedStartedAt }}</span>
                </div>
                <div v-if="formattedFinishedAt" class="flex items-center justify-between">
                  <span class="text-xs text-slate-400">Finished</span>
                  <span class="text-xs font-semibold text-emerald-400">{{ formattedFinishedAt }}</span>
                </div>
                <div v-if="readingDuration" class="flex items-center justify-between">
                  <span class="text-xs text-slate-400">Duration</span>
                  <div class="flex items-center gap-1">
                    <Clock :size="11" class="text-indigo-400" />
                    <span class="text-xs font-semibold text-indigo-400">{{ readingDuration }} days</span>
                  </div>
                </div>
                <div v-if="reviewData?.status" class="flex items-center justify-between">
                  <span class="text-xs text-slate-400">Status</span>
                  <span class="text-xs font-semibold text-emerald-400 capitalize">{{ reviewData.status?.replace('_', ' ') }}</span>
                </div>
              </div>
            </div>

            <!-- Community Reviews -->
            <div v-if="communityReviews.length > 0" class="rounded-2xl border border-slate-800 p-5 bg-slate-900/40">
              <div class="flex items-center justify-between mb-4">
                <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Other Reviews</h3>
                <span class="text-[10px] font-bold text-indigo-400">{{ communityReviewsCount }}</span>
              </div>

              <div class="space-y-3">
                <button
                  v-for="review in communityReviews.slice(0, 4)"
                  :key="review.id"
                  @click="router.push(`/books/${route.params.id}/review/${review.user.id}`)"
                  class="w-full text-left p-3 rounded-xl bg-slate-950/40 border border-slate-800 hover:border-slate-700 transition-all group"
                >
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-6 h-6 rounded-full bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-[9px] font-bold overflow-hidden flex-shrink-0">
                      <img
                        v-if="review.user.avatar && !review.user.avatar.includes('placeholder')"
                        :src="review.user.avatar"
                        class="w-full h-full object-cover"
                      />
                      <span v-else>{{ getReviewerInitials(review.user) }}</span>
                    </div>
                    <span class="text-xs font-semibold text-slate-300 truncate">{{ getReviewerName(review.user) }}</span>
                    <div v-if="review.rating" class="flex items-center gap-0.5 ml-auto flex-shrink-0">
                      <Star :size="9" class="fill-yellow-500 text-yellow-500" />
                      <span class="text-[10px] font-bold text-yellow-500">{{ review.rating }}</span>
                    </div>
                  </div>
                  <p class="text-[11px] text-slate-400 leading-relaxed line-clamp-2">{{ review.review_preview }}</p>
                  <div class="flex items-center gap-1 mt-1.5 text-[10px] text-indigo-400/70 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>Read full review</span>
                    <ChevronRight :size="10" />
                  </div>
                </button>
              </div>
            </div>

            <!-- Book Details -->
            <div v-if="booksStore.currentBook" class="rounded-2xl border border-slate-800 p-5 bg-slate-900/40">
              <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Book Details</h3>
              <div class="space-y-3">
                <div v-if="booksStore.currentBook?.pages" class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-slate-400">
                    <BookOpen :size="13" />
                    <span class="text-xs">Pages</span>
                  </div>
                  <span class="text-xs font-bold text-slate-200">{{ booksStore.currentBook.pages }}</span>
                </div>
                <div v-if="booksStore.currentBook?.language" class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-slate-400">
                    <Hash :size="13" />
                    <span class="text-xs">Language</span>
                  </div>
                  <span class="text-xs font-bold text-slate-200">{{ booksStore.currentBook.language?.toUpperCase() }}</span>
                </div>
                <div v-if="booksStore.currentBook?.published_date" class="flex items-center justify-between">
                  <div class="flex items-center gap-2 text-slate-400">
                    <Calendar :size="13" />
                    <span class="text-xs">Published</span>
                  </div>
                  <span class="text-xs font-bold text-slate-200">{{ booksStore.currentBook.published_date }}</span>
                </div>
                <div v-if="booksStore.currentBook?.genres?.length > 0" class="pt-2 border-t border-slate-800">
                  <div class="flex flex-wrap gap-1.5">
                    <span
                      v-for="genre in booksStore.currentBook.genres"
                      :key="genre.id"
                      class="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-bold"
                    >
                      {{ genre.name }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== MOBILE: Community Reviews ==================== -->
        <div v-if="communityReviews.length > 0" class="lg:hidden mt-6">
          <h3 class="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3 px-1">Other Reviews</h3>
          <div class="flex gap-3 overflow-x-auto pb-2 -mx-1 px-1 scrollbar-none">
            <button
              v-for="review in communityReviews.slice(0, 6)"
              :key="review.id"
              @click="router.push(`/books/${route.params.id}/review/${review.user.id}`)"
              class="flex-shrink-0 w-56 text-left p-3 rounded-xl bg-slate-900/60 border border-slate-800 active:bg-slate-800/60 transition-all"
            >
              <div class="flex items-center gap-2 mb-2">
                <div class="w-6 h-6 rounded-full bg-indigo-500/15 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-[9px] font-bold flex-shrink-0">
                  {{ getReviewerInitials(review.user) }}
                </div>
                <span class="text-xs font-semibold text-slate-300 truncate">{{ getReviewerName(review.user) }}</span>
                <div v-if="review.rating" class="flex items-center gap-0.5 ml-auto">
                  <Star :size="9" class="fill-yellow-500 text-yellow-500" />
                  <span class="text-[10px] font-bold text-yellow-500">{{ review.rating }}</span>
                </div>
              </div>
              <p class="text-[11px] text-slate-400 leading-relaxed line-clamp-3">{{ review.review_preview }}</p>
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
.scrollbar-none {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>

<style>
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
  content: '\201C';
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

/* Light mode overrides */
body.light .review-display h1,
body.light .review-display h2 {
  color: rgb(15 23 42);
}

body.light .review-display blockquote {
  color: rgb(30 41 59);
  background: rgba(99, 102, 241, 0.08);
}

body.light .review-display strong,
body.light .review-display b {
  color: rgb(15 23 42);
}
</style>
