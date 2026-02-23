<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useVocabularyStore } from '@/stores/vocabularyStore'
import WordCard from '@/components/vocabulary/WordCard.vue'
import FlashcardPlayer from '@/components/vocabulary/FlashcardPlayer.vue'
import VocabularyModal from '@/components/vocabulary/VocabularyModal.vue'
import { Brain, LayoutGrid, BarChart3, Plus, Search, Sparkles, BookOpen, CheckCircle, Clock, X, Filter, Download } from 'lucide-vue-next'
import { vocabularyAPI } from '@/services/api'
import { downloadBlob } from '@/utils/downloadFile'

const route = useRoute()
const vocabularyStore = useVocabularyStore()

const activeView = ref('library') // 'library' | 'practice' | 'stats'
const searchQuery = ref('')
const filterLevel = ref('all') // 'all' | 'new' | 'learning' | 'mastered'
const filterBookId = ref(null)
const isModalOpen = ref(false)
const editingWord = ref(null)
const showMobileFilters = ref(false)

onMounted(() => {
  vocabularyStore.loadWords()

  // Apply book filter from query param (e.g. navigating from Knowledge Hub)
  const bookFilter = route.query.book
  if (bookFilter) {
    filterBookId.value = Number(bookFilter)
  }
})

const filteredWords = computed(() => {
  let words = vocabularyStore.searchWords(searchQuery.value)
  let result = vocabularyStore.wordsByMastery(filterLevel.value).filter(w =>
    words.includes(w)
  )
  if (filterBookId.value) {
    result = result.filter(w => w.book === filterBookId.value)
  }
  return result
})

const filterBookTitle = computed(() => {
  if (!filterBookId.value) return null
  const match = vocabularyStore.words.find(w => w.book === filterBookId.value)
  return match?.bookTitle || `Book #${filterBookId.value}`
})

const clearBookFilter = () => {
  filterBookId.value = null
}

const practiceWords = computed(() => vocabularyStore.practiceWords)
const stats = computed(() => vocabularyStore.stats)
const wordsByBook = computed(() => vocabularyStore.wordsByBook)

const handleDelete = (id) => {
  if (confirm('Permanently remove this word from your lexicon?')) {
    vocabularyStore.deleteWord(id)
  }
}

const handleEdit = (word) => {
  editingWord.value = word
  isModalOpen.value = true
}

const handleUpdateMastery = (id, level) => {
  vocabularyStore.updateMastery(id, level)
}

const handleSaveWord = (wordData, addAnother) => {
  vocabularyStore.saveWord(wordData)
  if (!addAnother) {
    isModalOpen.value = false
    editingWord.value = null
  }
}

const handleCloseModal = () => {
  isModalOpen.value = false
  editingWord.value = null
}

const handleOpenModal = () => {
  editingWord.value = null
  isModalOpen.value = true
}

const handlePracticeComplete = () => {
  activeView.value = 'library'
}

const showExportMenu = ref(false)

const handleExportVocabulary = async (format) => {
  showExportMenu.value = false
  try {
    const response = await vocabularyAPI.export(format)
    const filenames = { json: 'vocabulary.json', csv: 'vocabulary.csv', anki: 'vocabulary_anki.txt' }
    downloadBlob(response, filenames[format] || 'vocabulary.json')
  } catch (error) {
    console.error('Error exporting vocabulary:', error)
  }
}
</script>

<template>
  <div class="animate-in fade-in duration-700 pb-20 lg:pb-0">
    <!-- Mobile Header (Sticky - minimal) -->
    <div class="lg:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 safe-area-top">
      <div class="flex items-center justify-between px-4 py-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Brain :size="18" class="text-emerald-400" />
          </div>
          <div>
            <h1 class="text-base font-bold text-white">Vocabulary</h1>
            <p class="text-xs text-slate-500">{{ stats.total }} words</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button
            v-if="activeView === 'library'"
            @click="showMobileFilters = true"
            class="w-10 h-10 rounded-xl bg-slate-800/80 border border-slate-700/50 flex items-center justify-center text-slate-400 active:scale-95 transition-transform"
          >
            <Filter :size="18" />
          </button>
          <button
            @click="handleOpenModal"
            class="w-10 h-10 rounded-xl bg-emerald-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20 active:scale-95 transition-transform"
          >
            <Plus :size="20" />
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Navigation (Not sticky) -->
    <div class="lg:hidden px-4 pt-4 pb-2">
      <!-- Mobile Tabs -->
      <div class="flex items-center gap-2 overflow-x-auto scrollbar-hide">
        <button
          @click="activeView = 'library'"
          :class="activeView === 'library' ? 'bg-emerald-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all"
        >
          <LayoutGrid :size="14" />
          Library
        </button>
        <button
          @click="activeView = 'practice'"
          :class="activeView === 'practice' ? 'bg-emerald-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all"
        >
          <Brain :size="14" />
          Practice
        </button>
        <button
          @click="activeView = 'stats'"
          :class="activeView === 'stats' ? 'bg-emerald-500 text-white' : 'bg-slate-800/50 text-slate-400 border-slate-700'"
          class="flex-shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all"
        >
          <BarChart3 :size="14" />
          Insights
        </button>
      </div>

      <!-- Active Filter Indicator -->
      <div v-if="activeView === 'library' && (filterLevel !== 'all' || filterBookId)" class="flex items-center gap-2 mt-3">
        <span class="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Filter:</span>
        <button
          v-if="filterBookId"
          @click="clearBookFilter"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-sky-500/20 border border-sky-500/40 text-sky-400 text-xs font-bold"
        >
          <BookOpen :size="12" />
          {{ filterBookTitle }}
          <X :size="12" />
        </button>
        <button
          v-if="filterLevel !== 'all'"
          @click="filterLevel = 'all'"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 text-xs font-bold"
        >
          {{ filterLevel }}
          <X :size="12" />
        </button>
      </div>
    </div>

    <!-- Mobile Filter Panel -->
    <Teleport to="body">
      <Transition name="slide">
        <div
          v-if="showMobileFilters"
          class="fixed inset-0 z-50 lg:hidden"
        >
          <!-- Backdrop -->
          <div
            class="absolute inset-0 bg-black/60 backdrop-blur-sm"
            @click="showMobileFilters = false"
          />

          <!-- Panel -->
          <div class="absolute right-0 top-0 bottom-0 w-[85%] max-w-sm bg-slate-900 border-l border-slate-800 overflow-y-auto safe-area-inset">
            <!-- Panel Header -->
            <div class="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/50 px-4 py-4">
              <div class="flex items-center justify-between">
                <h2 class="text-lg font-bold text-white">Search & Filter</h2>
                <button
                  @click="showMobileFilters = false"
                  class="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400"
                >
                  <X :size="20" />
                </button>
              </div>
            </div>

            <div class="p-4 space-y-6">
              <!-- Search -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Search</h3>
                <div class="relative">
                  <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
                  <input
                    type="text"
                    v-model="searchQuery"
                    placeholder="Search words..."
                    class="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-emerald-500/50 focus:outline-none transition-colors"
                  />
                </div>
              </div>

              <!-- Mastery Level -->
              <div>
                <h3 class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Mastery Level</h3>
                <div class="space-y-2">
                  <button
                    @click="filterLevel = 'all'; showMobileFilters = false"
                    :class="filterLevel === 'all' ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Sparkles :size="18" />
                    <span class="font-bold">All Words</span>
                    <span class="ml-auto text-sm opacity-70">{{ stats.total }}</span>
                  </button>
                  <button
                    @click="filterLevel = 'new'; showMobileFilters = false"
                    :class="filterLevel === 'new' ? 'border-indigo-500 bg-indigo-500/10 text-indigo-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Clock :size="18" />
                    <span class="font-bold">New</span>
                    <span class="ml-auto text-sm opacity-70">{{ stats.new }}</span>
                  </button>
                  <button
                    @click="filterLevel = 'learning'; showMobileFilters = false"
                    :class="filterLevel === 'learning' ? 'border-amber-500 bg-amber-500/10 text-amber-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <Brain :size="18" />
                    <span class="font-bold">Learning</span>
                    <span class="ml-auto text-sm opacity-70">{{ stats.learning }}</span>
                  </button>
                  <button
                    @click="filterLevel = 'mastered'; showMobileFilters = false"
                    :class="filterLevel === 'mastered' ? 'border-sky-500 bg-sky-500/10 text-sky-400' : 'border-slate-700 text-slate-400'"
                    class="w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 transition-all"
                  >
                    <CheckCircle :size="18" />
                    <span class="font-bold">Mastered</span>
                    <span class="ml-auto text-sm opacity-70">{{ stats.mastered }}</span>
                  </button>
                </div>
              </div>

              <!-- Clear Filter -->
              <button
                v-if="filterLevel !== 'all'"
                @click="filterLevel = 'all'; showMobileFilters = false"
                class="w-full px-4 py-3 rounded-xl border border-red-500/30 text-red-400 font-bold text-sm hover:bg-red-500/10 transition-all"
              >
                Clear Filter
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Page Header (Desktop) -->
    <div class="hidden lg:block max-w-7xl mx-auto pt-12 pb-8 px-6">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
        <header>
          <div class="flex items-center gap-2 sm:gap-3 mb-4">
            <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Brain class="text-emerald-400" :size="18" />
            </div>
            <span class="text-page-meta font-bold text-emerald-400 uppercase tracking-[0.2em] sm:tracking-[0.3em]">Personal Lexicon</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
            The <span class="text-emerald-500">Vocabulary</span> Vault
          </h1>
          <p class="text-page-subtitle text-slate-400 max-w-2xl leading-relaxed">
            Build and master a sophisticated vocabulary from your reading explorations. Practice with intelligent flashcards.
          </p>
        </header>

        <div class="flex items-center gap-3">
          <!-- Export dropdown -->
          <div class="relative">
            <button
              @click="showExportMenu = !showExportMenu"
              class="flex items-center gap-2 px-4 py-3 sm:py-5 rounded-2xl bg-white/5 border border-white/5 text-slate-400 hover:text-emerald-400 hover:border-emerald-500/20 transition-all text-sm font-bold"
            >
              <Download :size="16" />
              <span class="hidden sm:inline">Export</span>
            </button>
            <div v-if="showExportMenu" class="absolute top-full right-0 mt-2 p-2 rounded-xl bg-slate-800 border border-white/10 shadow-2xl z-50 min-w-[140px]">
              <button @click="handleExportVocabulary('json')" class="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/10 transition-colors">JSON</button>
              <button @click="handleExportVocabulary('csv')" class="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/10 transition-colors">CSV</button>
              <button @click="handleExportVocabulary('anki')" class="w-full text-left px-3 py-2 rounded-lg text-sm text-slate-300 hover:bg-white/10 transition-colors">Anki</button>
            </div>
          </div>

          <button
            @click="handleOpenModal"
            class="group flex items-center gap-2 sm:gap-3 px-5 sm:px-8 py-3 sm:py-5 rounded-2xl bg-emerald-500 text-white text-sm sm:text-base font-bold shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
          >
            <Plus :size="18" class="sm:w-6 sm:h-6 group-hover:rotate-90 transition-transform duration-300" />
            <span class="hidden sm:inline">Capture New Word</span>
            <span class="sm:hidden">Add Word</span>
          </button>
        </div>
      </div>

      <!-- Navigation Tabs (Desktop) -->
      <div class="hidden lg:flex items-center gap-1.5 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 w-fit mb-12 overflow-x-auto max-w-full">
        <button
          @click="activeView = 'library'"
          :class="[
            'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
            activeView === 'library' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <LayoutGrid :size="14" class="sm:w-4 sm:h-4" />
          Library
        </button>
        <button
          @click="activeView = 'practice'"
          :class="[
            'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
            activeView === 'practice' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <Brain :size="14" class="sm:w-4 sm:h-4" />
          Practice
        </button>
        <button
          @click="activeView = 'stats'"
          :class="[
            'flex items-center gap-2 px-4 sm:px-6 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-bold transition-all whitespace-nowrap',
            activeView === 'stats' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <BarChart3 :size="14" class="sm:w-4 sm:h-4" />
          Insights
        </button>
      </div>
    </div>

    <!-- Content Views (visible on all screens) -->
    <div class="max-w-7xl mx-auto lg:px-6">
      <!-- Library View -->
      <div v-if="activeView === 'library'" class="space-y-6 lg:space-y-10 px-4 lg:px-0">
        <!-- Filter Bar (Desktop) -->
        <div class="hidden lg:flex flex-col lg:flex-row gap-4">
          <div class="flex-1 relative group">
            <Search class="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-emerald-500 transition-colors" :size="20" />
            <input
              type="text"
              v-model="searchQuery"
              placeholder="Search your lexicon..."
              class="w-full bg-slate-900/50 border-2 border-slate-800 rounded-2xl px-14 py-4 text-white focus:border-emerald-500 transition-all outline-none"
            />
          </div>

          <div class="flex items-center gap-1 p-1 bg-slate-900/50 rounded-2xl border border-slate-800">
            <button
              @click="filterLevel = 'all'"
              :class="[
                'px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                filterLevel === 'all' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'
              ]"
            >
              All
            </button>
            <button
              @click="filterLevel = 'new'"
              :class="[
                'px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                filterLevel === 'new' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'
              ]"
            >
              New
            </button>
            <button
              @click="filterLevel = 'learning'"
              :class="[
                'px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                filterLevel === 'learning' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'
              ]"
            >
              Learning
            </button>
            <button
              @click="filterLevel = 'mastered'"
              :class="[
                'px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                filterLevel === 'mastered' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:text-slate-400'
              ]"
            >
              Mastered
            </button>
          </div>
        </div>

        <!-- Book Filter Banner -->
        <div v-if="filterBookId" class="flex items-center justify-between px-4 py-3 rounded-xl bg-sky-500/10 border border-sky-500/20 mb-6">
          <div class="flex items-center gap-2 text-sm">
            <BookOpen :size="16" class="text-sky-400" />
            <span class="text-slate-400">Showing words from</span>
            <span class="font-bold text-sky-400">{{ filterBookTitle }}</span>
          </div>
          <button
            @click="clearBookFilter"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/50 text-slate-300 text-xs font-bold hover:bg-slate-700/50 transition-colors"
          >
            <X :size="14" />
            Clear Filter
          </button>
        </div>

        <!-- Library Grid -->
        <div v-if="filteredWords.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6">
          <WordCard
            v-for="word in filteredWords"
            :key="word.id"
            :word="word"
            @edit="handleEdit"
            @delete="handleDelete"
            @update-mastery="handleUpdateMastery"
          />
        </div>
        <div v-else class="py-16 lg:py-32 text-center glass border-slate-800 rounded-2xl lg:rounded-[2.5rem]">
          <div class="w-12 h-12 lg:w-16 lg:h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-4 lg:mb-6 text-slate-600">
            <BookOpen :size="24" class="lg:w-7 lg:h-7" />
          </div>
          <h3 class="text-lg lg:text-xl font-bold text-white mb-2">Lexicon empty</h3>
          <p class="text-slate-500 text-sm lg:text-base px-4">Try searching for a different term or capture your first word.</p>
        </div>
      </div>

      <!-- Practice View -->
      <div v-if="activeView === 'practice'" class="py-6 lg:py-12 px-4 lg:px-0">
        <FlashcardPlayer
          v-if="practiceWords.length > 0"
          :words="practiceWords"
          @complete="handlePracticeComplete"
          @update-mastery="handleUpdateMastery"
        />
        <div v-else class="max-w-xl mx-auto py-12 lg:py-24 text-center glass border-emerald-500/20 bg-emerald-500/5 rounded-2xl lg:rounded-[2.5rem]">
          <div class="w-16 h-16 lg:w-20 lg:h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6 lg:mb-8 text-emerald-400">
            <CheckCircle :size="32" class="lg:w-10 lg:h-10" />
          </div>
          <h3 class="text-xl lg:text-2xl font-black text-white mb-3 lg:mb-4">You're all caught up!</h3>
          <p class="text-slate-400 leading-relaxed mb-6 lg:mb-8 text-sm lg:text-base px-4">
            All your collected words are mastered. Collect more insights from your reading to continue learning.
          </p>
          <button
            @click="activeView = 'library'"
            class="px-6 lg:px-8 py-3 lg:py-4 rounded-xl bg-emerald-500 text-white font-bold text-sm lg:text-base"
          >
            Return to Library
          </button>
        </div>
      </div>

      <!-- Stats View -->
      <div v-if="activeView === 'stats'" class="space-y-6 lg:space-y-12 px-4 lg:px-0">
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-6">
          <!-- Stat Cards -->
          <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2rem] glass border transition-all text-emerald-400 border-emerald-500/20 bg-emerald-500/5">
            <div class="flex items-center gap-1.5 lg:gap-3 mb-1.5 lg:mb-4 opacity-70">
              <Sparkles :size="14" class="lg:w-5 lg:h-5" />
              <span class="text-[7px] lg:text-[10px] font-black uppercase tracking-wide lg:tracking-widest">Total</span>
            </div>
            <p class="text-xl lg:text-4xl font-black text-white">{{ stats.total }}</p>
          </div>

          <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2rem] glass border transition-all text-indigo-400 border-indigo-500/20 bg-indigo-500/5">
            <div class="flex items-center gap-1.5 lg:gap-3 mb-1.5 lg:mb-4 opacity-70">
              <Clock :size="14" class="lg:w-5 lg:h-5" />
              <span class="text-[7px] lg:text-[10px] font-black uppercase tracking-wide lg:tracking-widest">New</span>
            </div>
            <p class="text-xl lg:text-4xl font-black text-white">{{ stats.new }}</p>
          </div>

          <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2rem] glass border transition-all text-amber-400 border-amber-500/20 bg-amber-500/5">
            <div class="flex items-center gap-1.5 lg:gap-3 mb-1.5 lg:mb-4 opacity-70">
              <Brain :size="14" class="lg:w-5 lg:h-5" />
              <span class="text-[7px] lg:text-[10px] font-black uppercase tracking-wide lg:tracking-widest">Learning</span>
            </div>
            <p class="text-xl lg:text-4xl font-black text-white">{{ stats.learning }}</p>
          </div>

          <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2rem] glass border transition-all text-sky-400 border-sky-500/20 bg-sky-500/5">
            <div class="flex items-center gap-1.5 lg:gap-3 mb-1.5 lg:mb-4 opacity-70">
              <CheckCircle :size="14" class="lg:w-5 lg:h-5" />
              <span class="text-[7px] lg:text-[10px] font-black uppercase tracking-wide lg:tracking-widest">Mastered</span>
            </div>
            <p class="text-xl lg:text-4xl font-black text-white">{{ stats.mastered }}</p>
          </div>
        </div>

        <!-- Top Sources -->
        <div class="p-5 lg:p-10 rounded-2xl lg:rounded-[2.5rem] glass border-slate-800">
          <h3 class="text-sm lg:text-lg font-black text-white mb-4 lg:mb-8 uppercase tracking-wider lg:tracking-widest flex items-center gap-2 lg:gap-3">
            <BookOpen :size="16" class="lg:w-5 lg:h-5 text-emerald-400" /> Top Sources
          </h3>
          <div class="space-y-4 lg:space-y-6">
            <div
              v-for="[book, count] in Object.entries(wordsByBook).sort((a, b) => b[1] - a[1]).slice(0, 5)"
              :key="book"
              class="flex items-center justify-between gap-3"
            >
              <span class="text-slate-400 font-bold truncate text-sm lg:text-base flex-1 min-w-0">{{ book }}</span>
              <div class="flex items-center gap-2 lg:gap-4 flex-shrink-0">
                <div class="w-16 lg:w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div class="h-full bg-emerald-500" :style="{ width: `${(count / stats.total) * 100}%` }" />
                </div>
                <span class="text-white font-black w-6 lg:w-8 text-right text-sm lg:text-base">{{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <VocabularyModal
      v-if="isModalOpen"
      :word="editingWord"
      @close="handleCloseModal"
      @save="handleSaveWord"
    />
  </div>
</template>

<style scoped>
/* Slide transition for mobile filter panel */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-active > div:last-child,
.slide-leave-active > div:last-child {
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from > div:last-child,
.slide-leave-to > div:last-child {
  transform: translateX(100%);
}

/* Hide scrollbar for horizontal scroll */
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}

/* Safe area support */
.safe-area-top {
  padding-top: env(safe-area-inset-top);
}

.safe-area-inset {
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
}

/* Touch feedback */
button {
  -webkit-tap-highlight-color: transparent;
}
</style>
