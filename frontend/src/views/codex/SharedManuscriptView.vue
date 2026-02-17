<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { getSharedManuscript } from '@/services/codexService'
import { BookOpen, ChevronRight } from 'lucide-vue-next'

const route = useRoute()
const manuscript = ref(null)
const loading = ref(true)
const error = ref(null)
const activeChapterIndex = ref(0)

const activeChapter = computed(() => {
  if (!manuscript.value?.chapters?.length) return null
  return manuscript.value.chapters[activeChapterIndex.value]
})

onMounted(async () => {
  try {
    manuscript.value = await getSharedManuscript(route.params.token)
  } catch (e) {
    error.value = 'This manuscript is not available or sharing has been disabled.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <div class="animate-pulse text-slate-500">Loading manuscript...</div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center justify-center min-h-screen">
      <div class="text-center max-w-md">
        <BookOpen :size="48" class="text-slate-700 mx-auto mb-4" />
        <h1 class="text-xl font-black text-white mb-2">Manuscript Not Found</h1>
        <p class="text-slate-500 text-sm">{{ error }}</p>
      </div>
    </div>

    <!-- Manuscript -->
    <div v-else-if="manuscript" class="max-w-4xl mx-auto px-6 py-12">
      <!-- Title Page -->
      <div class="text-center mb-16 py-12 border-b border-white/5">
        <h1 class="text-4xl font-black text-white tracking-tight mb-2">{{ manuscript.title }}</h1>
        <p v-if="manuscript.subtitle" class="text-lg text-slate-400 italic">{{ manuscript.subtitle }}</p>
        <div class="mt-4 flex items-center justify-center gap-3 text-xs text-slate-600">
          <span class="uppercase tracking-widest">{{ manuscript.genre }}</span>
          <span>&middot;</span>
          <span>{{ (manuscript.currentWordCount || 0).toLocaleString() }} words</span>
        </div>
      </div>

      <!-- Chapter Navigation -->
      <div v-if="manuscript.chapters?.length > 1" class="mb-8 flex flex-wrap gap-2">
        <button
          v-for="(ch, idx) in manuscript.chapters"
          :key="ch.id"
          @click="activeChapterIndex = idx"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-bold transition-all',
            activeChapterIndex === idx
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
              : 'bg-white/5 text-slate-500 border border-white/5 hover:bg-white/10'
          ]"
        >
          {{ ch.title || `Chapter ${idx + 1}` }}
        </button>
      </div>

      <!-- Active Chapter Content -->
      <div v-if="activeChapter" class="prose-reader">
        <h2 class="text-2xl font-black text-white mb-8">{{ activeChapter.title }}</h2>
        <div class="text-base text-slate-300 leading-[1.9] whitespace-pre-wrap font-serif">{{ activeChapter.content }}</div>
      </div>

      <!-- Chapter Navigation -->
      <div class="mt-12 flex justify-between items-center pt-8 border-t border-white/5">
        <button
          v-if="activeChapterIndex > 0"
          @click="activeChapterIndex--"
          class="text-sm text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          &larr; Previous Chapter
        </button>
        <div v-else />
        <button
          v-if="activeChapterIndex < (manuscript.chapters?.length || 0) - 1"
          @click="activeChapterIndex++"
          class="text-sm text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1"
        >
          Next Chapter <ChevronRight :size="14" />
        </button>
      </div>

      <!-- Footer -->
      <div class="mt-16 text-center text-[10px] text-slate-700 uppercase tracking-widest">
        Shared via Reading OS
      </div>
    </div>
  </div>
</template>
