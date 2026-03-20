<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { recommendationsService, CONTEXT_CONFIG } from '@/services/recommendationsService'
import { getBookUrl } from '@/utils/bookUrl'
import BookCard from '@/components/BookCard.vue'
import ReadingTaste from '@/components/recommendations/ReadingTaste.vue'
import {
  Sparkles,
  Leaf,
  Brain,
  Heart,
  Zap,
  Sun,
  BookOpen,
  RefreshCw,
  Users,
  Library,
  BookMarked,
} from 'lucide-vue-next'

const router = useRouter()

const loading = ref(true)
const forYouBooks = ref([])
const contextualSections = ref([])
const readingTaste = ref(null)
const discoverSections = ref({ author_picks: [], genre_picks: [], because_you_read: [] })

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

const contextsToLoad = ['peaceful', 'challenge']

onMounted(async () => {
  loading.value = true

  try {
    // Load all data in parallel
    const [forYou, taste, sections, ...contextual] = await Promise.all([
      recommendationsService.getForYouBooks(12),
      recommendationsService.getReadingTaste('all'),
      recommendationsService.getDiscoverSections(),
      ...contextsToLoad.map(c => recommendationsService.getContextualBooks(c, 8)),
    ])

    forYouBooks.value = forYou
    readingTaste.value = taste
    discoverSections.value = sections
    contextualSections.value = contextual.filter(s => s.books && s.books.length > 0)
  } catch (error) {
    // Recommendations load failed
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
    // Recommendations refresh failed
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 py-8 space-y-12">

    <!-- Header -->
    <div class="mb-2">
      <div class="flex items-center gap-2 mb-2">
        <div class="h-px w-8 bg-indigo-500"></div>
        <span class="text-[10px] font-bold uppercase tracking-[0.3em] text-indigo-500">Discover</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white tracking-tight">
        Book Recommendations
      </h1>
      <p class="text-sm text-slate-400 mt-1">Personalized picks based on your taste and reading history</p>
    </div>

    <!-- Reading Taste Card -->
    <ReadingTaste
      v-if="readingTaste && readingTaste.books_count > 0"
      :taste="readingTaste"
      title="Your Reading Taste"
    />

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

    <!-- Because You Like [Author] Sections -->
    <section v-for="pick in discoverSections.author_picks" :key="'author-' + pick.author.id" class="space-y-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
          <Users :size="16" class="text-violet-400" />
        </div>
        <h2 class="text-xl font-black text-white">Because you like {{ pick.author.name }}</h2>
      </div>

      <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        <div
          v-for="book in pick.books"
          :key="book.id"
          class="flex-shrink-0 w-32 md:w-36 cursor-pointer transform hover:scale-105 transition-transform"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" />
        </div>
      </div>
    </section>

    <!-- More in [Genre] Sections -->
    <section v-for="pick in discoverSections.genre_picks" :key="'genre-' + pick.genre.id" class="space-y-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
          <Library :size="16" class="text-emerald-400" />
        </div>
        <h2 class="text-xl font-black text-white">More in {{ pick.genre.name }}</h2>
      </div>

      <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        <div
          v-for="book in pick.books"
          :key="book.id"
          class="flex-shrink-0 w-32 md:w-36 cursor-pointer transform hover:scale-105 transition-transform"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" />
        </div>
      </div>
    </section>

    <!-- Because You Read [Book] Section -->
    <section v-for="section in discoverSections.because_you_read" :key="'byr-' + section.source_book.id" class="space-y-4">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          <BookMarked :size="16" class="text-amber-400" />
        </div>
        <h2 class="text-xl font-black text-white">Because you read {{ section.source_book.title }}</h2>
      </div>

      <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        <div
          v-for="book in section.similar"
          :key="book.id"
          class="relative flex-shrink-0 w-32 md:w-36 cursor-pointer transform hover:scale-105 transition-transform"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" />
          <div
            v-if="book.similarity_score"
            class="absolute top-2 right-2 px-1.5 py-0.5 bg-amber-500/90 backdrop-blur-sm rounded-md text-[10px] font-black text-white"
          >
            {{ book.similarity_score }}%
          </div>
        </div>
      </div>
    </section>

    <!-- Contextual Sections -->
    <section v-for="section in contextualSections" :key="section.id" class="space-y-4">
      <div class="flex items-center gap-3">
        <component
          :is="contextIcons[section.id] || Sparkles"
          :size="20"
          :class="`text-${contextColors[section.id] || 'indigo'}-400`"
        />
        <h2 class="text-xl font-black text-white">{{ section.label }}</h2>
        <span class="text-xs text-slate-500">{{ section.description }}</span>
      </div>

      <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
        <div
          v-for="book in section.books"
          :key="book.id"
          class="flex-shrink-0 w-32 md:w-36 cursor-pointer transform hover:scale-105 transition-transform"
          @click="goToBook(book)"
        >
          <BookCard :book="book" :showActions="false" />
        </div>
      </div>
    </section>

    <!-- Empty State -->
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
/* Hide scrollbar for horizontal scroll sections */
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

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
