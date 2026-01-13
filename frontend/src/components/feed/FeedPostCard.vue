<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Heart, MessageCircle, Share2, CheckCircle, BookOpen, Bookmark,
  Quote as QuoteIcon, MessageSquare, TrendingUp, Star, MoreHorizontal, ExternalLink, Brain
} from 'lucide-vue-next'
import StarRating from '@/components/ui/StarRating.vue'

const router = useRouter()

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const liked = ref(props.post.stats.hasLiked)
const likeCount = ref(props.post.stats.likes)

const toggleLike = () => {
  liked.value = !liked.value
  likeCount.value = liked.value ? likeCount.value + 1 : likeCount.value - 1
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
</script>

<template>
  <div class="group glass bg-slate-900/50 rounded-2xl border border-slate-800 p-6 hover:border-indigo-500/50 transition-all duration-300 animate-in fade-in slide-in-from-bottom-4 shadow-xl shadow-slate-950/20">
    <!-- Header -->
    <div class="flex items-center justify-between mb-5">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold ring-2 ring-slate-800 ring-offset-2 ring-offset-slate-900">
          {{ getInitials(post.user.name) }}
        </div>
        <div>
          <div class="flex items-center gap-2">
            <span class="text-sm font-bold text-white hover:text-indigo-400 transition-colors cursor-pointer">{{ post.user.name }}</span>
            <div :class="['flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider', config.color]">
              <component :is="config.icon" :size="14" />
              {{ config.label }}
            </div>
          </div>
          <span class="text-xs text-slate-500">{{ post.timestamp }}</span>
        </div>
      </div>
      <button class="text-slate-600 hover:text-slate-400 transition-colors p-2 rounded-full hover:bg-slate-800">
        <MoreHorizontal :size="18" />
      </button>
    </div>

    <!-- Content Area -->
    <div class="flex gap-6 mb-6">
      <!-- Book Cover -->
      <div
        v-if="post.book.cover"
        @click="handleBookClick"
        class="hidden sm:block shrink-0 w-[80px] h-[120px] rounded-lg overflow-hidden shadow-2xl ring-1 ring-white/10 group-hover:scale-105 transition-transform duration-300 cursor-pointer"
      >
        <img :src="post.book.cover" :alt="post.book.title" class="w-full h-full object-cover" />
      </div>

      <div class="flex-1 min-w-0">
        <div class="mb-3">
          <h3
            @click="handleBookClick"
            class="text-base font-bold text-slate-100 group-hover:text-indigo-400 transition-colors cursor-pointer truncate flex items-center gap-2"
          >
            {{ post.book.title }}
            <ExternalLink :size="14" class="opacity-0 group-hover:opacity-100 transition-opacity" />
          </h3>
          <p class="text-sm text-slate-400">by {{ post.book.author }}</p>
        </div>

        <!-- Activity Specific Content -->
        <div class="space-y-3">
          <blockquote v-if="post.type === 'quote' && post.content.quote" class="relative p-4 rounded-xl bg-indigo-500/5 border-l-4 border-indigo-500 italic text-slate-200 font-serif text-base leading-relaxed">
            "{{ post.content.quote }}"
          </blockquote>

          <div v-if="post.content.review">
            <p class="text-sm text-slate-300 leading-relaxed italic line-clamp-3">
              "{{ stripHtml(post.content.review) }}"
            </p>
            <button
              v-if="post.bookId"
              @click="router.push(`/books/${post.bookId}/review-view`)"
              class="mt-3 text-xs font-bold text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
            >
              Read Full Review
              <ExternalLink :size="12" />
            </button>
          </div>

          <div v-if="post.type === 'progress' && post.content.progress" class="w-full bg-slate-800 rounded-full h-2 mb-2 relative overflow-hidden">
            <div
              class="bg-indigo-500 h-full rounded-full transition-all duration-1000 ease-out"
              :style="{ width: `${post.content.progress}%` }"
            />
            <span class="absolute right-0 -top-6 text-[10px] font-bold text-indigo-400">{{ post.content.progress }}% Complete</span>
          </div>

          <StarRating
            v-if="post.content.rating"
            :model-value="post.content.rating"
            :size="14"
            :readonly="true"
            :show-value="true"
          />

          <p v-if="post.content.note" class="text-sm text-slate-400 line-clamp-2">
            {{ post.content.note }}
          </p>

          <div v-if="post.content.challengeTitle" class="p-4 rounded-xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
            <p class="text-sm font-bold text-indigo-400">{{ post.content.challengeTitle }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Actions -->
    <div class="pt-4 border-t border-slate-800 flex items-center justify-between">
      <div class="flex items-center gap-6">
        <button
          @click="toggleLike"
          :class="[
            'flex items-center gap-2 group/btn transition-colors',
            liked ? 'text-indigo-400' : 'text-slate-500 hover:text-indigo-400'
          ]"
        >
          <div :class="['p-2 rounded-full transition-colors', liked ? 'bg-indigo-400/10' : 'group-hover/btn:bg-indigo-400/10']">
            <Heart :size="18" :fill="liked ? 'currentColor' : 'none'" :class="liked ? 'animate-in zoom-in-50 duration-300' : ''" />
          </div>
          <span class="text-xs font-bold">{{ likeCount }}</span>
        </button>

        <button class="flex items-center gap-2 group/btn text-slate-500 hover:text-sky-400 transition-colors">
          <div class="p-2 rounded-full group-hover/btn:bg-sky-400/10 transition-colors">
            <MessageCircle :size="18" />
          </div>
          <span class="text-xs font-bold">{{ post.stats.comments }}</span>
        </button>
      </div>

      <button class="flex items-center gap-2 group/btn text-slate-500 hover:text-emerald-400 transition-colors">
        <div class="p-2 rounded-full group-hover/btn:bg-emerald-400/10 transition-colors">
          <Share2 :size="18" />
        </div>
        <span class="text-xs font-bold hidden sm:inline">Share Insight</span>
      </button>
    </div>
  </div>
</template>
