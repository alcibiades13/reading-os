<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ChevronLeft, ChevronRight, RotateCcw, Check, Brain, SkipForward, Play, Pause, Shuffle } from 'lucide-vue-next'

const props = defineProps({
  words: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['complete', 'update-mastery'])

const currentIndex = ref(0)
const isFlipped = ref(false)
const isAutoPlay = ref(false)
const isShuffled = ref(false)
const shuffledIndices = ref([])
let autoPlayInterval = null

const shuffleArray = (arr) => {
  const shuffled = [...arr]
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled
}

const doShuffle = () => {
  shuffledIndices.value = shuffleArray(Array.from({ length: props.words.length }, (_, i) => i))
}

const toggleShuffle = () => {
  isShuffled.value = !isShuffled.value
  if (isShuffled.value) {
    doShuffle()
  }
  currentIndex.value = 0
  isFlipped.value = false
}

const activeWords = computed(() => {
  if (!isShuffled.value) return props.words
  return shuffledIndices.value.map(i => props.words[i])
})

const currentWord = computed(() => activeWords.value[currentIndex.value])
const progressPercent = computed(() => ((currentIndex.value + 1) / props.words.length) * 100)

const handleNext = () => {
  isFlipped.value = false
  if (currentIndex.value < props.words.length - 1) {
    currentIndex.value++
  } else {
    emit('complete')
  }
}

const handlePrev = () => {
  isFlipped.value = false
  if (currentIndex.value > 0) {
    currentIndex.value--
  }
}

const handleFlip = () => {
  isFlipped.value = !isFlipped.value
}

const handleKeyDown = (e) => {
  if (e.code === 'Space') {
    e.preventDefault()
    handleFlip()
  } else if (e.code === 'ArrowRight') {
    handleNext()
  } else if (e.code === 'ArrowLeft') {
    handlePrev()
  }
}

const toggleAutoPlay = () => {
  isAutoPlay.value = !isAutoPlay.value
}

watch(isAutoPlay, (newVal) => {
  if (newVal) {
    autoPlayInterval = setInterval(() => {
      if (!isFlipped.value) {
        isFlipped.value = true
      } else {
        handleNext()
      }
    }, 3000)
  } else {
    if (autoPlayInterval) {
      clearInterval(autoPlayInterval)
      autoPlayInterval = null
    }
  }
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (autoPlayInterval) {
    clearInterval(autoPlayInterval)
  }
})
</script>

<template>
  <div v-if="currentWord" class="max-w-3xl mx-auto space-y-6 sm:space-y-12">
    <!-- Top Bar / Progress -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
      <div class="flex items-center gap-3 sm:gap-4">
        <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <Brain :size="18" class="sm:w-5 sm:h-5" />
        </div>
        <div>
          <h3 class="text-white font-bold text-xs sm:text-sm">Lexicon Practice</h3>
          <p class="text-[9px] sm:text-[10px] text-slate-500 font-black uppercase tracking-wider sm:tracking-widest">Mastery Session</p>
        </div>
      </div>

      <div class="flex items-center gap-2 sm:gap-4 w-full sm:w-auto">
        <button
          @click="toggleShuffle"
          :class="[
            'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl border border-slate-800 text-[9px] sm:text-[10px] font-black uppercase tracking-wider sm:tracking-widest transition-all',
            isShuffled ? 'bg-indigo-500 text-white border-indigo-500' : 'text-slate-500 hover:text-white'
          ]"
        >
          <Shuffle :size="12" class="sm:w-3.5 sm:h-3.5" />
          <span class="hidden sm:inline">{{ isShuffled ? 'Shuffled' : 'In Order' }}</span>
        </button>
        <button
          @click="toggleAutoPlay"
          :class="[
            'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl border border-slate-800 text-[9px] sm:text-[10px] font-black uppercase tracking-wider sm:tracking-widest transition-all',
            isAutoPlay ? 'bg-indigo-500 text-white border-indigo-500' : 'text-slate-500 hover:text-white'
          ]"
        >
          <Pause v-if="isAutoPlay" :size="12" class="sm:w-3.5 sm:h-3.5" />
          <Play v-else :size="12" class="sm:w-3.5 sm:h-3.5" />
          <span class="hidden sm:inline">{{ isAutoPlay ? 'Auto' : 'Auto' }}</span>
        </button>
        <div class="flex-1 sm:flex-none sm:text-right">
          <p class="text-xs font-black text-white">{{ currentIndex + 1 }} <span class="text-slate-600">/ {{ words.length }}</span></p>
          <div class="w-full sm:w-32 h-1 bg-slate-900 rounded-full mt-1">
            <div class="h-full bg-indigo-500 transition-all duration-500" :style="{ width: progressPercent + '%' }" />
          </div>
        </div>
      </div>
    </div>

    <!-- Main Card -->
    <div
      :class="['flip-card w-full aspect-[16/10] md:aspect-[2/1] cursor-pointer', isFlipped ? 'flipped' : '']"
      @click="handleFlip"
    >
      <div class="flip-card-inner">
        <!-- Front -->
        <div class="flip-card-front glass bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/20 flex flex-col items-center justify-center p-6 sm:p-12 border border-slate-800 shadow-2xl">
          <span class="text-3xl sm:text-5xl md:text-6xl font-serif text-white tracking-tight text-center selection:bg-indigo-500/30">
            {{ currentWord.word }}
          </span>
          <div class="absolute bottom-4 sm:bottom-8 text-[9px] sm:text-[10px] font-black uppercase tracking-[0.3em] sm:tracking-[0.4em] text-indigo-500/40">
            Tap or Space to Flip
          </div>
        </div>

        <!-- Back -->
        <div class="flip-card-back glass bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/20 p-4 sm:p-10 flex flex-col border border-emerald-500/20 shadow-2xl">
          <!-- Scrollable content area -->
          <div class="flex-1 overflow-y-auto custom-scrollbar min-h-0">
            <div class="mb-3 sm:mb-6">
              <span class="text-[10px] sm:text-xs font-black text-emerald-400 uppercase tracking-widest block mb-2">Definition</span>
              <p class="text-sm sm:text-lg text-white font-medium leading-relaxed">
                {{ currentWord.definition || "No definition provided." }}
              </p>
            </div>

            <div v-if="currentWord.context" class="mb-3 sm:mb-6 p-3 sm:p-4 rounded-xl sm:rounded-2xl bg-emerald-500/5 border-l-4 border-emerald-500/30 italic text-slate-300 font-serif text-xs sm:text-base">
              "{{ currentWord.context }}"
            </div>
          </div>

          <!-- Fixed footer -->
          <div class="flex-shrink-0 flex items-center justify-between pt-3 sm:pt-6 border-t border-slate-800 mt-2">
            <div class="flex items-center gap-2 sm:gap-3">
              <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500">
                <RotateCcw :size="12" class="sm:w-3.5 sm:h-3.5" />
              </div>
              <div>
                <p class="text-[9px] sm:text-[10px] font-black text-slate-500 uppercase">Source</p>
                <p class="text-[10px] sm:text-xs font-bold text-white truncate max-w-[100px] sm:max-w-none">{{ currentWord.bookTitle || "Manual" }}</p>
              </div>
            </div>
            <div v-if="currentWord.pageNumber" class="text-right">
              <p class="text-[9px] sm:text-[10px] font-black text-slate-500 uppercase">Page</p>
              <p class="text-[10px] sm:text-xs font-bold text-white">{{ currentWord.pageNumber }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mastery Actions -->
    <div class="grid grid-cols-3 gap-3 sm:gap-6">
      <button
        @click.stop="emit('update-mastery', currentWord.id, 'learning'); handleNext()"
        class="p-3 sm:p-6 rounded-xl sm:rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-amber-500/10 hover:border-amber-500/30 transition-all flex flex-col items-center gap-2 sm:gap-3 group"
      >
        <div class="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-slate-800 group-hover:bg-amber-500/20 flex items-center justify-center text-slate-500 group-hover:text-amber-400 transition-colors">
          <RotateCcw :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-slate-500 group-hover:text-amber-400 text-center leading-tight">Still Learning</span>
      </button>

      <button
        @click.stop="emit('update-mastery', currentWord.id, 'mastered'); handleNext()"
        class="p-3 sm:p-6 rounded-xl sm:rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-all flex flex-col items-center gap-2 sm:gap-3 group"
      >
        <div class="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-slate-800 group-hover:bg-emerald-500/20 flex items-center justify-center text-slate-500 group-hover:text-emerald-400 transition-colors">
          <Check :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-slate-500 group-hover:text-emerald-400 text-center">Got it!</span>
      </button>

      <button
        @click.stop="handleNext()"
        class="p-3 sm:p-6 rounded-xl sm:rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-slate-800 transition-all flex flex-col items-center gap-2 sm:gap-3 group"
      >
        <div class="w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl bg-slate-800 group-hover:bg-slate-700 flex items-center justify-center text-slate-500 group-hover:text-white transition-colors">
          <SkipForward :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-slate-500 group-hover:text-white text-center">Skip</span>
      </button>
    </div>

    <!-- Navigation Controls -->
    <div class="flex items-center justify-center gap-8 pt-6">
      <button
        @click="handlePrev"
        :disabled="currentIndex === 0"
        class="p-4 rounded-full border border-slate-800 text-slate-500 hover:text-white hover:bg-slate-900 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronLeft :size="24" />
      </button>
      <button
        @click="handleNext"
        class="p-4 rounded-full border border-slate-800 text-slate-500 hover:text-white hover:bg-slate-900 transition-all"
      >
        <ChevronRight :size="24" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.flip-card {
  perspective: 1000px;
}

.flip-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.flip-card.flipped .flip-card-inner {
  transform: rotateY(180deg);
}

.flip-card-front,
.flip-card-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 2rem;
}

.flip-card-back {
  transform: rotateY(180deg);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(71 85 105 / 0.5);
  border-radius: 3px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105 / 0.7);
}
</style>
