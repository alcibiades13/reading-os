<script setup>
import { ref, computed, onMounted } from 'vue'
import { useVocabularyStore } from '@/stores/vocabularyStore'
import WordCard from '@/components/vocabulary/WordCard.vue'
import FlashcardPlayer from '@/components/vocabulary/FlashcardPlayer.vue'
import VocabularyModal from '@/components/vocabulary/VocabularyModal.vue'
import { Brain, LayoutGrid, BarChart3, Plus, Search, Sparkles, BookOpen, CheckCircle, Clock } from 'lucide-vue-next'

const vocabularyStore = useVocabularyStore()

const activeView = ref('library') // 'library' | 'practice' | 'stats'
const searchQuery = ref('')
const filterLevel = ref('all') // 'all' | 'new' | 'learning' | 'mastered'
const isModalOpen = ref(false)
const editingWord = ref(null)

onMounted(() => {
  vocabularyStore.loadWords()
})

const filteredWords = computed(() => {
  let words = vocabularyStore.searchWords(searchQuery.value)
  return vocabularyStore.wordsByMastery(filterLevel.value).filter(w =>
    words.includes(w)
  )
})

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
</script>

<template>
  <div class="animate-in fade-in duration-700">
    <!-- Page Header -->
    <div class="max-w-7xl mx-auto pt-12 pb-8 px-6">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
        <header>
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Brain class="text-emerald-400" :size="24" />
            </div>
            <span class="text-sm font-bold text-emerald-400 uppercase tracking-[0.3em]">Personal Lexicon</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
            The <span class="text-emerald-500">Vocabulary</span> Vault
          </h1>
          <p class="text-page-subtitle text-slate-400 max-w-2xl leading-relaxed">
            Build and master a sophisticated vocabulary from your reading explorations. Practice with intelligent flashcards.
          </p>
        </header>

        <button
          @click="handleOpenModal"
          class="group flex items-center gap-3 px-8 py-5 rounded-2xl bg-emerald-500 text-white font-bold shadow-xl shadow-emerald-500/20 hover:bg-emerald-400 active:scale-95 transition-all"
        >
          <Plus :size="24" class="group-hover:rotate-90 transition-transform duration-300" />
          Capture New Word
        </button>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-1.5 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 w-fit mb-12">
        <button
          @click="activeView = 'library'"
          :class="[
            'flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all',
            activeView === 'library' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <LayoutGrid :size="16" />
          Library
        </button>
        <button
          @click="activeView = 'practice'"
          :class="[
            'flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all',
            activeView === 'practice' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <Brain :size="16" />
          Practice
        </button>
        <button
          @click="activeView = 'stats'"
          :class="[
            'flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all',
            activeView === 'stats' ? 'bg-emerald-500 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
          ]"
        >
          <BarChart3 :size="16" />
          Insights
        </button>
      </div>

      <!-- Library View -->
      <div v-if="activeView === 'library'" class="space-y-10">
        <!-- Filter Bar -->
        <div class="flex flex-col lg:flex-row gap-4">
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

        <!-- Library Grid -->
        <div v-if="filteredWords.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          <WordCard
            v-for="word in filteredWords"
            :key="word.id"
            :word="word"
            @edit="handleEdit"
            @delete="handleDelete"
            @update-mastery="handleUpdateMastery"
          />
        </div>
        <div v-else class="py-32 text-center glass border-slate-800 rounded-[2.5rem]">
          <div class="w-16 h-16 rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center mx-auto mb-6 text-slate-600">
            <BookOpen :size="28" />
          </div>
          <h3 class="text-xl font-bold text-white mb-2">Lexicon empty</h3>
          <p class="text-slate-500">Try searching for a different term or capture your first word.</p>
        </div>
      </div>

      <!-- Practice View -->
      <div v-if="activeView === 'practice'" class="py-12">
        <FlashcardPlayer
          v-if="practiceWords.length > 0"
          :words="practiceWords"
          @complete="handlePracticeComplete"
          @update-mastery="handleUpdateMastery"
        />
        <div v-else class="max-w-xl mx-auto py-24 text-center glass border-emerald-500/20 bg-emerald-500/5 rounded-[2.5rem]">
          <div class="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-8 text-emerald-400">
            <CheckCircle :size="40" />
          </div>
          <h3 class="text-2xl font-black text-white mb-4">You're all caught up!</h3>
          <p class="text-slate-400 leading-relaxed mb-8">
            All your collected words are mastered. Collect more insights from your reading to continue learning.
          </p>
          <button
            @click="activeView = 'library'"
            class="px-8 py-4 rounded-xl bg-emerald-500 text-white font-bold"
          >
            Return to Library
          </button>
        </div>
      </div>

      <!-- Stats View -->
      <div v-if="activeView === 'stats'" class="space-y-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <!-- Stat Cards -->
          <div class="p-8 rounded-[2rem] glass border transition-all text-emerald-400 border-emerald-500/20 bg-emerald-500/5">
            <div class="flex items-center gap-3 mb-4 opacity-70">
              <Sparkles :size="20" />
              <span class="text-[10px] font-black uppercase tracking-widest">Total Vault</span>
            </div>
            <p class="text-4xl font-black text-white">{{ stats.total }}</p>
          </div>

          <div class="p-8 rounded-[2rem] glass border transition-all text-indigo-400 border-indigo-500/20 bg-indigo-500/5">
            <div class="flex items-center gap-3 mb-4 opacity-70">
              <Clock :size="20" />
              <span class="text-[10px] font-black uppercase tracking-widest">New Arrivals</span>
            </div>
            <p class="text-4xl font-black text-white">{{ stats.new }}</p>
          </div>

          <div class="p-8 rounded-[2rem] glass border transition-all text-amber-400 border-amber-500/20 bg-amber-500/5">
            <div class="flex items-center gap-3 mb-4 opacity-70">
              <Brain :size="20" />
              <span class="text-[10px] font-black uppercase tracking-widest">Currently Learning</span>
            </div>
            <p class="text-4xl font-black text-white">{{ stats.learning }}</p>
          </div>

          <div class="p-8 rounded-[2rem] glass border transition-all text-sky-400 border-sky-500/20 bg-sky-500/5">
            <div class="flex items-center gap-3 mb-4 opacity-70">
              <CheckCircle :size="20" />
              <span class="text-[10px] font-black uppercase tracking-widest">Mastered</span>
            </div>
            <p class="text-4xl font-black text-white">{{ stats.mastered }}</p>
          </div>
        </div>

        <!-- Top Sources -->
        <div class="p-10 rounded-[2.5rem] glass border-slate-800">
          <h3 class="text-lg font-black text-white mb-8 uppercase tracking-widest flex items-center gap-3">
            <BookOpen :size="20" class="text-emerald-400" /> Top Sources
          </h3>
          <div class="space-y-6">
            <div
              v-for="[book, count] in Object.entries(wordsByBook).sort((a, b) => b[1] - a[1]).slice(0, 5)"
              :key="book"
              class="flex items-center justify-between"
            >
              <span class="text-slate-400 font-bold truncate pr-4">{{ book }}</span>
              <div class="flex items-center gap-4">
                <div class="w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div class="h-full bg-emerald-500" :style="{ width: `${(count / stats.total) * 100}%` }" />
                </div>
                <span class="text-white font-black w-8 text-right">{{ count }}</span>
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
