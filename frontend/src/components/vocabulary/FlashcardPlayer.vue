<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ChevronLeft, ChevronRight, RotateCcw, Check, Brain, SkipForward, Play, Pause, Shuffle, Maximize2, Minimize2 } from 'lucide-vue-next'

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

// Focus mode: card goes fullscreen over the app chrome so long definitions/context fit
const isFocus = ref(false)

const toggleFocus = () => {
  isFocus.value = !isFocus.value
}

watch(isFocus, (on) => {
  document.body.style.overflow = on ? 'hidden' : ''
})

const masteryBtnClass = computed(() => isFocus.value
  ? 'py-3 px-2 flex-row justify-center gap-2'
  : 'p-3 sm:p-6 flex-col gap-2 sm:gap-3')

const masteryIconClass = computed(() => isFocus.value
  ? 'w-7 h-7 rounded-lg'
  : 'w-8 h-8 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl')

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
  if (e.code === 'Escape' && isFocus.value) {
    isFocus.value = false
  } else if (e.code === 'Space') {
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
  document.body.style.overflow = ''
  if (autoPlayInterval) {
    clearInterval(autoPlayInterval)
  }
})
</script>

<template>
  <Teleport to="body" :disabled="!isFocus">
  <div v-if="currentWord" :class="isFocus ? 'flashcard-focus fixed inset-0 z-[100] bg-zinc-950 overflow-hidden' : ''">
  <div
    :class="isFocus
      ? 'h-full max-w-3xl mx-auto flex flex-col gap-4 sm:gap-6 px-4 sm:px-8 pt-[max(1rem,env(safe-area-inset-top))] pb-[max(1rem,env(safe-area-inset-bottom))]'
      : 'max-w-3xl mx-auto space-y-6 sm:space-y-12'"
  >
    <!-- Top Bar / Progress -->
    <div :class="['flex justify-between gap-4', isFocus ? 'shrink-0 flex-row items-center' : 'flex-col sm:flex-row items-start sm:items-center']">
      <div v-if="!isFocus" class="flex items-center gap-3 sm:gap-4">
        <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <Brain :size="18" class="sm:w-5 sm:h-5" />
        </div>
        <div>
          <h3 class="text-white font-bold text-xs sm:text-sm">Lexicon Practice</h3>
          <p class="text-[9px] sm:text-[10px] text-zinc-500 font-black uppercase tracking-wider sm:tracking-widest">Mastery Session</p>
        </div>
      </div>

      <!-- Focus: previous card (bottom nav row is hidden) -->
      <button
        v-if="isFocus"
        @click="handlePrev"
        :disabled="currentIndex === 0"
        class="shrink-0 p-2 rounded-lg border border-zinc-800 text-zinc-500 hover:text-white transition-all disabled:opacity-20"
      >
        <ChevronLeft :size="16" />
      </button>

      <div :class="['flex items-center gap-2 sm:gap-4', isFocus ? 'flex-1 min-w-0' : 'w-full sm:w-auto']">
        <button
          @click="toggleShuffle"
          :class="[
            'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl border border-zinc-800 text-[9px] sm:text-[10px] font-black uppercase tracking-wider sm:tracking-widest transition-all',
            isShuffled ? 'bg-indigo-500 text-white border-indigo-500' : 'text-zinc-500 hover:text-white'
          ]"
        >
          <Shuffle :size="12" class="sm:w-3.5 sm:h-3.5" />
          <span class="hidden sm:inline">{{ isShuffled ? 'Shuffled' : 'In Order' }}</span>
        </button>
        <button
          @click="toggleAutoPlay"
          :class="[
            'flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl border border-zinc-800 text-[9px] sm:text-[10px] font-black uppercase tracking-wider sm:tracking-widest transition-all',
            isAutoPlay ? 'bg-indigo-500 text-white border-indigo-500' : 'text-zinc-500 hover:text-white'
          ]"
        >
          <Pause v-if="isAutoPlay" :size="12" class="sm:w-3.5 sm:h-3.5" />
          <Play v-else :size="12" class="sm:w-3.5 sm:h-3.5" />
          <span class="hidden sm:inline">{{ isAutoPlay ? 'Auto' : 'Auto' }}</span>
        </button>
        <div class="flex-1 sm:flex-none sm:text-right">
          <p class="text-xs font-black text-white">{{ currentIndex + 1 }} <span class="text-zinc-600">/ {{ words.length }}</span></p>
          <div class="w-full sm:w-32 h-1 bg-zinc-900 rounded-full mt-1">
            <div class="h-full bg-indigo-500 transition-all duration-500" :style="{ width: progressPercent + '%' }" />
          </div>
        </div>
        <button
          @click="toggleFocus"
          :title="isFocus ? 'Exit focus (Esc)' : 'Focus mode'"
          :class="[
            'shrink-0 flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg sm:rounded-xl border text-[9px] sm:text-[10px] font-black uppercase tracking-wider sm:tracking-widest transition-all',
            isFocus ? 'bg-indigo-500 text-white border-indigo-500' : 'border-zinc-800 text-zinc-500 hover:text-white'
          ]"
        >
          <Minimize2 v-if="isFocus" :size="12" class="sm:w-3.5 sm:h-3.5" />
          <Maximize2 v-else :size="12" class="sm:w-3.5 sm:h-3.5" />
          <span class="hidden sm:inline">{{ isFocus ? 'Exit' : 'Focus' }}</span>
        </button>
      </div>
    </div>

    <!-- Main Card -->
    <div
      :class="['flip-card w-full cursor-pointer', isFocus ? 'flex-1 min-h-0' : 'aspect-[16/10] md:aspect-[2/1]', isFlipped ? 'flipped' : '']"
      @click="handleFlip"
    >
      <div class="flip-card-inner">
        <!-- Front -->
        <div class="flip-card-front glass bg-gradient-to-br from-zinc-900 via-zinc-900 to-indigo-950/20 flex flex-col items-center justify-center p-6 sm:p-12 border border-zinc-800 shadow-2xl">
          <span class="text-3xl sm:text-5xl md:text-6xl font-serif text-white tracking-tight text-center selection:bg-indigo-500/30">
            {{ currentWord.word }}
          </span>
          <div class="absolute bottom-4 sm:bottom-8 text-[9px] sm:text-[10px] font-black uppercase tracking-[0.3em] sm:tracking-[0.4em] text-indigo-500/40">
            Tap or Space to Flip
          </div>
        </div>

        <!-- Back -->
        <div class="flip-card-back glass bg-gradient-to-br from-zinc-900 via-zinc-900 to-indigo-950/20 p-4 sm:p-10 flex flex-col border border-indigo-500/20 shadow-2xl">
          <!-- Scrollable content area -->
          <div class="flex-1 overflow-y-auto custom-scrollbar min-h-0">
            <div class="mb-3 sm:mb-6">
              <span class="text-[10px] sm:text-xs font-black text-indigo-400 uppercase tracking-widest block mb-2">Definition</span>
              <p class="text-reading-sm sm:text-reading-lg text-white font-medium leading-relaxed">
                {{ currentWord.definition || "No definition provided." }}
              </p>
            </div>

            <div v-if="currentWord.context" class="mb-3 sm:mb-6 p-3 sm:p-4 rounded-xl sm:rounded-2xl bg-indigo-500/5 border-l-4 border-indigo-500/30 italic text-zinc-300 font-serif text-reading-sm sm:text-reading-lg leading-relaxed">
              "{{ currentWord.context }}"
            </div>
          </div>

          <!-- Fixed footer -->
          <div class="flex-shrink-0 flex items-center justify-between pt-3 sm:pt-6 border-t border-zinc-800 mt-2">
            <div class="flex items-center gap-2 sm:gap-3 min-w-0">
              <div class="shrink-0 w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-zinc-800 flex items-center justify-center text-zinc-500">
                <RotateCcw :size="12" class="sm:w-3.5 sm:h-3.5" />
              </div>
              <div class="min-w-0">
                <p class="text-[10px] sm:text-[11px] font-black text-zinc-500 uppercase">Source</p>
                <p class="text-sm font-bold text-white truncate">{{ currentWord.bookTitle || "Manual" }}</p>
              </div>
            </div>
            <div v-if="currentWord.pageNumber" class="shrink-0 text-right pl-3">
              <p class="text-[10px] sm:text-[11px] font-black text-zinc-500 uppercase">Page</p>
              <p class="text-sm font-bold text-white">{{ currentWord.pageNumber }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mastery Actions -->
    <div :class="['grid grid-cols-3', isFocus ? 'shrink-0 gap-2 sm:gap-4' : 'gap-3 sm:gap-6']">
      <button
        @click.stop="emit('update-mastery', currentWord.id, 'learning'); handleNext()"
        :class="['rounded-xl sm:rounded-2xl glass border-zinc-800 bg-zinc-900/50 hover:bg-amber-500/10 hover:border-amber-500/30 transition-all flex items-center group', masteryBtnClass]"
      >
        <div :class="['shrink-0 bg-zinc-800', masteryIconClass]" class="group-hover:bg-amber-500/20 flex items-center justify-center text-zinc-500 group-hover:text-amber-400 transition-colors">
          <RotateCcw :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-zinc-500 group-hover:text-amber-400 text-center leading-tight">Still Learning</span>
      </button>

      <button
        @click.stop="emit('update-mastery', currentWord.id, 'mastered'); handleNext()"
        :class="['rounded-xl sm:rounded-2xl glass border-zinc-800 bg-zinc-900/50 hover:bg-sky-500/10 hover:border-sky-500/30 transition-all flex items-center group', masteryBtnClass]"
      >
        <div :class="['shrink-0 bg-zinc-800', masteryIconClass]" class="group-hover:bg-sky-500/20 flex items-center justify-center text-zinc-500 group-hover:text-sky-400 transition-colors">
          <Check :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-zinc-500 group-hover:text-sky-400 text-center">Got it!</span>
      </button>

      <button
        @click.stop="handleNext()"
        :class="['rounded-xl sm:rounded-2xl glass border-zinc-800 bg-zinc-900/50 hover:bg-zinc-800 transition-all flex items-center group', masteryBtnClass]"
      >
        <div :class="['shrink-0 bg-zinc-800', masteryIconClass]" class="group-hover:bg-zinc-700 flex items-center justify-center text-zinc-500 group-hover:text-white transition-colors">
          <SkipForward :size="16" class="sm:w-6 sm:h-6" />
        </div>
        <span class="text-[9px] sm:text-xs font-black uppercase tracking-wider sm:tracking-widest text-zinc-500 group-hover:text-white text-center">Skip</span>
      </button>
    </div>

    <!-- Navigation Controls -->
    <div v-if="!isFocus" class="flex items-center justify-center gap-8 pt-6">
      <button
        @click="handlePrev"
        :disabled="currentIndex === 0"
        class="p-4 rounded-full border border-zinc-800 text-zinc-500 hover:text-white hover:bg-zinc-900 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ChevronLeft :size="24" />
      </button>
      <button
        @click="handleNext"
        class="p-4 rounded-full border border-zinc-800 text-zinc-500 hover:text-white hover:bg-zinc-900 transition-all"
      >
        <ChevronRight :size="24" />
      </button>
    </div>
  </div>
  </div>
  </Teleport>
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
