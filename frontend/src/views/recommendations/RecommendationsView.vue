<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { recommendationsService, CONTEXT_CONFIG } from '@/services/recommendationsService'
import { getBookUrl } from '@/utils/bookUrl'
import BookCard from '@/components/BookCard.vue'
import TasteProfile from '@/components/recommendations/TasteProfile.vue'
import {
  Sparkles,
  Leaf,
  Brain,
  Heart,
  Zap,
  Sun,
  BookOpen,
  RefreshCw,
} from 'lucide-vue-next'

const router = useRouter()

const loading = ref(true)
const forYouBooks = ref([])
const contextualSections = ref([])
const tasteProfile = ref(null)

// Context icon mapping
const contextIcons = {
  peaceful: Leaf,
  challenge: Brain,
  emotional: Heart,
  quick: Zap,
  light: Sun,
  deep: Sparkles,
}

// Context color mapping
const contextColors = {
  peaceful: 'emerald',
  challenge: 'purple',
  emotional: 'rose',
  quick: 'amber',
  light: 'yellow',
  deep: 'indigo',
}

const contextsToLoad = ['peaceful', 'challenge', 'emotional', 'quick']

onMounted(async () => {
  loading.value = true

  try {
    // Load all data in parallel
    const [forYou, profile, ...contextual] = await Promise.all([
      recommendationsService.getForYouBooks(12),
      recommendationsService.getTasteProfile(),
      ...contextsToLoad.map(c => recommendationsService.getContextualBooks(c, 8)),
    ])

    forYouBooks.value = forYou
    tasteProfile.value = profile
    contextualSections.value = contextual.filter(s => s.books && s.books.length > 0)
  } catch (error) {
    console.error('Error loading recommendations:', error)
  } finally {
    loading.value = false
  }
})

const goToBook = (book) => {
  router.push(getBookUrl(book))
}

const refreshRecommendations = async () => {
  loading.value = true
  try {
    forYouBooks.value = await recommendationsService.getForYouBooks(12)
  } catch (error) {
    console.error('Error refreshing recommendations:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-12">

    <!-- Header -->
    <div class="text-center space-y-4">
      <div class="flex items-center justify-center gap-3">
        <div class="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <Sparkles :size="28" class="text-indigo-400" />
        </div>
      </div>
      <h1 class="text-4xl font-black text-white tracking-tighter">
        Discover <span class="text-indigo-500">Books</span>
      </h1>
      <p class="text-slate-400 font-medium max-w-md mx-auto">
        Personalized recommendations based on your taste and reading history
      </p>
    </div>

    <!-- Taste Profile Card (if available) -->
    <TasteProfile v-if="tasteProfile && tasteProfile.vote_count > 0" :profile="tasteProfile" />

    <!-- For You Section -->
    <section>
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <Sparkles :size="20" class="text-indigo-400" />
          <h2 class="text-2xl font-black text-white">For You</h2>
          <span class="text-sm text-slate-500">based on your taste</span>
        </div>
        <button
          @click="refreshRecommendations"
          class="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all"
          :disabled="loading"
        >
          <RefreshCw :size="18" :class="{ 'animate-spin': loading }" />
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div v-for="i in 6" :key="i" class="aspect-[2/3] bg-white/5 rounded-xl animate-pulse" />
      </div>

      <!-- Empty State -->
      <div v-else-if="forYouBooks.length === 0" class="text-center py-12 rounded-3xl bg-white/[0.02] border border-white/5">
        <div class="w-16 h-16 mx-auto rounded-full bg-white/5 flex items-center justify-center mb-4">
          <BookOpen :size="32" class="text-slate-600" />
        </div>
        <h3 class="text-lg font-bold text-white mb-2">Not enough data yet</h3>
        <p class="text-slate-500 text-sm max-w-sm mx-auto">
          Read more books and complete surveys to get personalized recommendations
        </p>
      </div>

      <!-- Books Grid -->
      <div v-else class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div
          v-for="book in forYouBooks"
          :key="book.id"
          class="relative group cursor-pointer"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" />
          <!-- Match Score Badge -->
          <div
            v-if="book.match_score"
            class="absolute top-2 right-2 px-2 py-1 bg-indigo-500/90 backdrop-blur-sm rounded-lg text-xs font-black text-white shadow-lg"
          >
            {{ book.match_score }}%
          </div>
        </div>
      </div>
    </section>

    <!-- Contextual Sections -->
    <section v-for="section in contextualSections" :key="section.id" class="space-y-6">
      <div class="flex items-center gap-3">
        <component
          :is="contextIcons[section.id] || Sparkles"
          :size="20"
          :class="`text-${contextColors[section.id] || 'indigo'}-400`"
        />
        <h2 class="text-xl font-black text-white">{{ section.label }}</h2>
        <span class="text-xs text-slate-500">{{ section.description }}</span>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
        <div
          v-for="book in section.books"
          :key="book.id"
          class="cursor-pointer transform hover:scale-105 transition-transform"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" size="small" />
        </div>
      </div>
    </section>

    <!-- Empty State for Contextual -->
    <div v-if="!loading && contextualSections.length === 0 && forYouBooks.length === 0" class="text-center py-20">
      <div class="w-20 h-20 mx-auto rounded-full bg-white/5 flex items-center justify-center mb-6">
        <BookOpen :size="40" class="text-slate-700" />
      </div>
      <h3 class="text-2xl font-black text-white mb-2">Start reading</h3>
      <p class="text-slate-500 max-w-md mx-auto mb-6">
        Add books to your library and rate them to get personalized recommendations
      </p>
      <router-link
        to="/books"
        class="inline-flex items-center gap-2 px-6 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-bold rounded-xl transition-colors"
      >
        <BookOpen :size="18" />
        Explore Books
      </router-link>
    </div>
  </div>
</template>

<style scoped>
/* Light mode adjustments */
:global(body.light) .text-white {
  color: #0f172a !important;
}

:global(body.light) .text-slate-400,
:global(body.light) .text-slate-500 {
  color: #64748b !important;
}

:global(body.light) .bg-white\/5 {
  background-color: rgba(0, 0, 0, 0.03) !important;
}
</style>
