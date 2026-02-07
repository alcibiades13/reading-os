<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { booksAPI } from '@/services/api'
import { Star, Users, Quote, MessageSquare, ChevronRight, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  bookId: {
    type: [String, Number],
    required: true
  },
  bookTitle: {
    type: String,
    default: ''
  }
})

const router = useRouter()

// State
const loading = ref(true)
const activeTab = ref('reviews') // 'reviews' | 'quotes'
const communityData = ref({
  reviews: [],
  quotes: [],
  reviews_count: 0,
  quotes_count: 0
})

// Fetch community activity
const fetchCommunityActivity = async () => {
  loading.value = true
  try {
    const response = await booksAPI.communityActivity(props.bookId)
    communityData.value = response.data
  } catch (error) {
    console.error('Failed to fetch community activity:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchCommunityActivity)

// Computed
const hasActivity = computed(() => {
  return communityData.value.reviews.length > 0 || communityData.value.quotes.length > 0
})

// Helpers
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const getUserInitials = (user) => {
  if (!user) return '?'
  const first = user.first_name?.charAt(0) || ''
  const last = user.last_name?.charAt(0) || ''
  return (first + last).toUpperCase() || '?'
}

const getUserName = (user) => {
  if (!user) return 'Unknown'
  return `${user.first_name || ''} ${user.last_name || ''}`.trim() || 'Unknown'
}

const viewFullReview = (review) => {
  router.push(`/books/${review.book_id}/review/${review.user.id}`)
}
</script>

<template>
  <section class="space-y-6 pt-12 border-t border-slate-900">
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.2em] flex items-center gap-3">
        <Users :size="16" /> Community Activity
      </h2>

      <!-- Tab Switcher -->
      <div v-if="!loading && hasActivity" class="flex items-center gap-1 p-1 rounded-xl bg-slate-900/50 border border-slate-800">
        <button
          @click="activeTab = 'reviews'"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5',
            activeTab === 'reviews'
              ? 'bg-indigo-500/20 text-indigo-400'
              : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <MessageSquare :size="12" />
          Reviews
          <span v-if="communityData.reviews_count > 0" class="text-[10px] opacity-70">({{ communityData.reviews_count }})</span>
        </button>
        <button
          @click="activeTab = 'quotes'"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5',
            activeTab === 'quotes'
              ? 'bg-indigo-500/20 text-indigo-400'
              : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <Quote :size="12" />
          Quotes
          <span v-if="communityData.quotes_count > 0" class="text-[10px] opacity-70">({{ communityData.quotes_count }})</span>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <Loader2 :size="24" class="text-indigo-400 animate-spin" />
    </div>

    <!-- Reviews Tab -->
    <div v-else-if="activeTab === 'reviews'" class="space-y-4">
      <template v-if="communityData.reviews.length > 0">
        <div
          v-for="review in communityData.reviews"
          :key="review.id"
          class="flex gap-4 p-4 rounded-2xl hover:bg-slate-900/50 transition-colors border border-transparent hover:border-slate-800 group"
        >
          <!-- Avatar -->
          <div class="w-10 h-10 rounded-full bg-slate-800 flex-shrink-0 border border-slate-700 flex items-center justify-center font-bold text-slate-400 text-xs overflow-hidden">
            <img
              v-if="review.user.avatar && !review.user.avatar.includes('placeholder')"
              :src="review.user.avatar"
              class="w-full h-full object-cover"
            />
            <span v-else>{{ getUserInitials(review.user) }}</span>
          </div>

          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center justify-between mb-1">
              <span class="font-bold text-white text-sm">{{ getUserName(review.user) }}</span>
              <div class="flex items-center gap-2">
                <span
                  v-if="review.status === 'read'"
                  class="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold uppercase"
                >
                  Finished
                </span>
                <span class="text-[10px] text-slate-600">{{ formatDate(review.finished_at || review.updated_at) }}</span>
              </div>
            </div>

            <!-- Rating -->
            <div v-if="review.rating" class="flex items-center gap-1 mb-2">
              <Star :size="12" class="text-amber-400 fill-current" />
              <span class="text-xs font-bold text-amber-400">{{ review.rating.toFixed(1) }}</span>
            </div>

            <!-- Review Preview -->
            <p class="text-sm text-slate-400 leading-relaxed">
              "{{ review.review_preview }}"
            </p>

            <!-- Read More -->
            <button
              v-if="review.has_full_review"
              @click="viewFullReview(review)"
              class="mt-3 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1 group-hover:gap-2"
            >
              Read full review <ChevronRight :size="14" class="transition-all" />
            </button>
          </div>
        </div>
      </template>

      <!-- Empty State for Reviews -->
      <div v-else class="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/50 text-center">
        <MessageSquare :size="32" class="text-slate-700 mx-auto mb-3" />
        <p class="text-slate-500 text-sm">No community reviews yet.</p>
        <p class="text-slate-600 text-xs mt-1">Be the first to share your thoughts!</p>
      </div>
    </div>

    <!-- Quotes Tab -->
    <div v-else-if="activeTab === 'quotes'" class="space-y-4">
      <template v-if="communityData.quotes.length > 0">
        <div
          v-for="quote in communityData.quotes"
          :key="quote.id"
          class="p-5 rounded-2xl glass border-slate-800/50 hover:border-indigo-500/30 transition-all space-y-3"
        >
          <!-- Quote Text -->
          <blockquote class="text-sm font-serif text-slate-200 italic leading-relaxed border-l-4 border-indigo-500 pl-4">
            "{{ quote.text }}"
          </blockquote>

          <!-- Quote Meta -->
          <div class="flex items-center justify-between pt-3 border-t border-slate-800/50">
            <div class="flex items-center gap-3">
              <!-- User Avatar -->
              <div class="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-[9px] font-bold text-slate-500 overflow-hidden">
                <img
                  v-if="quote.user.avatar && !quote.user.avatar.includes('placeholder')"
                  :src="quote.user.avatar"
                  class="w-full h-full object-cover"
                />
                <span v-else>{{ getUserInitials(quote.user) }}</span>
              </div>
              <span class="text-xs text-slate-500">{{ getUserName(quote.user) }}</span>
              <span v-if="quote.page_number" class="text-xs text-slate-600">• p. {{ quote.page_number }}</span>
            </div>

            <!-- Tags -->
            <div v-if="quote.tags?.length > 0" class="flex items-center gap-1">
              <span
                v-for="tag in quote.tags.slice(0, 2)"
                :key="tag.id"
                class="px-2 py-0.5 rounded text-[9px] font-medium bg-slate-800/50 text-slate-500"
              >
                {{ tag.name }}
              </span>
            </div>
          </div>
        </div>
      </template>

      <!-- Empty State for Quotes -->
      <div v-else class="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/50 text-center">
        <Quote :size="32" class="text-slate-700 mx-auto mb-3" />
        <p class="text-slate-500 text-sm">No shared quotes yet.</p>
        <p class="text-slate-600 text-xs mt-1">Readers haven't shared any highlights from this book.</p>
      </div>
    </div>

    <!-- No Activity State -->
    <div v-if="!loading && !hasActivity" class="p-6 rounded-2xl bg-slate-900/30 border border-slate-800/50 flex items-center justify-between">
      <div>
        <p class="text-slate-400 text-sm">No community activity for this book yet.</p>
        <p class="text-slate-600 text-xs mt-1">Be the first to share your experience!</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
}

.font-serif {
  font-family: 'Georgia', 'Garamond', 'Times New Roman', serif;
}

/* Light mode */
body.light .bg-slate-900\/50,
body.light .bg-slate-900\/30 {
  background-color: #f8fafc !important;
}

body.light .border-slate-800,
body.light .border-slate-800\/50 {
  border-color: #e2e8f0 !important;
}

body.light .text-slate-400 {
  color: #64748b !important;
}

body.light .text-slate-500 {
  color: #94a3b8 !important;
}

body.light .text-white {
  color: #1e293b !important;
}

body.light .text-slate-200 {
  color: #334155 !important;
}

body.light .bg-slate-800 {
  background-color: #e2e8f0 !important;
}

body.light .hover\:bg-slate-900\/50:hover {
  background-color: #f1f5f9 !important;
}
</style>
