<script setup>
import { computed } from 'vue'
import { useScrollReveal } from '@/composables/useScrollReveal'
import { Quote, BookOpen } from 'lucide-vue-next'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const { elementRef, isVisible } = useScrollReveal()

const maxDepth = computed(() => {
  if (!props.data.length) return 1
  return Math.max(...props.data.map(b => b.depth_score)) || 1
})
</script>

<template>
  <div
    ref="elementRef"
    :class="['transition-all duration-700', isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-6']"
  >
    <div class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
      <div class="flex items-center gap-2 mb-1">
        <Quote :size="15" class="text-indigo-400" />
        <h3 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Most Lived With</h3>
      </div>
      <p class="text-xs text-zinc-500 mb-4">Books you engaged with most deeply — through quotes, notes, and annotations.</p>

      <div v-if="!data.length" class="text-center py-6 text-sm text-zinc-500">
        Save quotes from your books to see engagement depth.
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="(book, i) in data"
          :key="i"
          class="flex items-center gap-3 p-3 rounded-xl bg-zinc-800/30 border border-zinc-700/30"
        >
          <!-- Rank -->
          <span class="text-xs font-black text-zinc-600 w-5 text-center flex-shrink-0">{{ i + 1 }}</span>

          <!-- Cover -->
          <div class="w-9 h-13 rounded bg-gradient-to-br from-zinc-700 to-zinc-800 flex-shrink-0 overflow-hidden">
            <img v-if="book.cover" :src="book.cover" :alt="book.title" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center">
              <BookOpen :size="12" class="text-zinc-600" />
            </div>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-zinc-200 truncate">{{ book.title }}</p>
            <p class="text-[10px] text-zinc-500 truncate">{{ book.authors?.join(', ') }}</p>
          </div>

          <!-- Depth bar + count -->
          <div class="flex items-center gap-3 flex-shrink-0">
            <div class="w-20 sm:w-32 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000"
                :style="{ width: `${(book.depth_score / maxDepth) * 100}%` }"
              />
            </div>
            <span class="text-xs font-bold text-indigo-400 w-8 text-right">{{ book.quotes_count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
