<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ChevronLeft, ChevronRight, RotateCcw, Check, Brain, SkipForward, Play, Pause } from 'lucide-vue-next'

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
let autoPlayInterval = null

const currentWord = computed(() => props.words[currentIndex.value])
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
  <div v-if="currentWord" class="max-w-3xl mx-auto space-y-12">
    <!-- Top Bar / Progress -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-4">
        <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
          <Brain :size="20" />
        </div>
        <div>
          <h3 class="text-white font-bold text-sm">Lexicon Practice</h3>
          <p class="text-[10px] text-slate-500 font-black uppercase tracking-widest">Mastery focus session</p>
        </div>
      </div>

      <div class="flex items-center gap-6">
        <button
          @click="toggleAutoPlay"
          :class="[
            'flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-800 text-[10px] font-black uppercase tracking-widest transition-all',
            isAutoPlay ? 'bg-indigo-500 text-white border-indigo-500' : 'text-slate-500 hover:text-white'
          ]"
        >
          <Pause v-if="isAutoPlay" :size="14" />
          <Play v-else :size="14" />
          {{ isAutoPlay ? 'Auto-play On' : 'Auto-play Off' }}
        </button>
        <div class="text-right">
          <p class="text-xs font-black text-white">{{ currentIndex + 1 }} <span class="text-slate-600">/ {{ words.length }}</span></p>
          <div class="w-32 h-1 bg-slate-900 rounded-full mt-1">
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
        <div class="flip-card-front glass bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/20 flex flex-col items-center justify-center p-12 border border-slate-800 shadow-2xl">
          <span class="text-5xl md:text-7xl font-serif text-white tracking-tight text-center selection:bg-indigo-500/30">
            {{ currentWord.word }}
          </span>
          <div class="absolute bottom-8 text-[10px] font-black uppercase tracking-[0.4em] text-indigo-500/40">
            Tap or Space to Flip
          </div>
        </div>

        <!-- Back -->
        <div class="flip-card-back glass bg-gradient-to-br from-slate-900 via-slate-900 to-emerald-950/20 p-10 flex flex-col border border-emerald-500/20 shadow-2xl overflow-y-auto custom-scrollbar">
          <div class="mb-8">
            <span class="text-xs font-black text-emerald-400 uppercase tracking-widest block mb-2">Definition</span>
            <p class="text-2xl text-white font-medium leading-relaxed">
              {{ currentWord.definition || "No definition provided." }}
            </p>
          </div>

          <div v-if="currentWord.context" class="mb-8 p-6 rounded-2xl bg-emerald-500/5 border-l-4 border-emerald-500/30 italic text-slate-300 font-serif text-lg">
            "{{ currentWord.context }}"
          </div>

          <div class="mt-auto flex items-center justify-between pt-6 border-t border-slate-800">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-slate-500">
                <RotateCcw :size="14" />
              </div>
              <div>
                <p class="text-[10px] font-black text-slate-500 uppercase">Book Source</p>
                <p class="text-xs font-bold text-white">{{ currentWord.bookTitle || "Manual Entry" }}</p>
              </div>
            </div>
            <div v-if="currentWord.pageNumber" class="text-right">
              <p class="text-[10px] font-black text-slate-500 uppercase">Page</p>
              <p class="text-xs font-bold text-white">{{ currentWord.pageNumber }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mastery Actions -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <button
        @click.stop="emit('update-mastery', currentWord.id, 'learning'); handleNext()"
        class="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-amber-500/10 hover:border-amber-500/30 transition-all flex flex-col items-center gap-3 group"
      >
        <div class="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-amber-500/20 flex items-center justify-center text-slate-500 group-hover:text-amber-400 transition-colors">
          <RotateCcw :size="24" />
        </div>
        <span class="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-amber-400">Still Learning</span>
      </button>

      <button
        @click.stop="emit('update-mastery', currentWord.id, 'mastered'); handleNext()"
        class="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-emerald-500/10 hover:border-emerald-500/30 transition-all flex flex-col items-center gap-3 group"
      >
        <div class="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-emerald-500/20 flex items-center justify-center text-slate-500 group-hover:text-emerald-400 transition-colors">
          <Check :size="24" />
        </div>
        <span class="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-emerald-400">Got it!</span>
      </button>

      <button
        @click.stop="handleNext()"
        class="p-6 rounded-2xl glass border-slate-800 bg-slate-900/50 hover:bg-slate-800 transition-all flex flex-col items-center gap-3 group"
      >
        <div class="w-12 h-12 rounded-xl bg-slate-800 group-hover:bg-slate-700 flex items-center justify-center text-slate-500 group-hover:text-white transition-colors">
          <SkipForward :size="24" />
        </div>
        <span class="text-xs font-black uppercase tracking-widest text-slate-500 group-hover:text-white">Skip</span>
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
