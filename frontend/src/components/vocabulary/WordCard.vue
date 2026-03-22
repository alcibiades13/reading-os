<script setup>
import { computed } from 'vue'
import { Star, Edit3, Trash2, Bookmark, RotateCcw } from 'lucide-vue-next'

const props = defineProps({
  word: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'delete', 'update-mastery'])

const masteryConfig = {
  new: { label: 'New', color: 'bg-indigo-500' },
  learning: { label: 'Learning', color: 'bg-amber-500' },
  mastered: { label: 'Mastered', color: 'bg-sky-500' }
}

const config = computed(() => masteryConfig[props.word.mastery])

const returnToLearning = () => {
  emit('update-mastery', props.word.id, 'learning')
}
</script>

<template>
  <div class="group glass bg-slate-900/40 rounded-2xl p-6 border border-slate-800/50 hover:border-indigo-500/30 transition-all duration-300">
    <div class="flex items-start justify-between mb-4 gap-2">
      <div class="min-w-0 flex-1">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="text-xl font-serif font-black text-white group-hover:text-indigo-400 transition-colors overflow-wrap-anywhere">
            {{ word.word }}
          </h3>
          <span :class="['px-2 py-0.5 rounded text-[8px] font-black uppercase text-white tracking-widest flex-shrink-0', config.color]">
            {{ config.label }}
          </span>
          <button
            v-if="word.mastery === 'mastered'"
            @click="returnToLearning"
            class="p-1 rounded hover:bg-amber-500/20 text-amber-400/60 hover:text-amber-400 transition-all group/reset flex-shrink-0"
            title="Return to practice rotation"
          >
            <RotateCcw :size="10" class="group-hover/reset:rotate-180 transition-transform duration-500" />
          </button>
          <Star v-if="word.isFavorite" :size="12" class="text-amber-400 flex-shrink-0" fill="currentColor" />
        </div>
      </div>
      <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
        <button @click="emit('edit', word)" class="p-2 rounded-lg hover:bg-slate-800 text-slate-500 hover:text-white transition-colors">
          <Edit3 :size="14" />
        </button>
        <button @click="emit('delete', word.id)" class="p-2 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors">
          <Trash2 :size="14" />
        </button>
      </div>
    </div>

    <p class="text-sm text-slate-400 italic mb-4 line-clamp-[8]">
      "{{ word.context || "No context provided." }}"
    </p>

    <div class="pt-4 border-t border-slate-800 flex items-center justify-between">
      <div class="flex items-center gap-2 text-[10px] font-bold text-slate-500 truncate max-w-[150px]">
        <Bookmark :size="12" />
        <span class="truncate">{{ word.bookTitle || 'Manual' }}</span>
      </div>
      <div class="text-[10px] font-black text-slate-600 uppercase tracking-widest">
        {{ word.reviewCount }} Reviews
      </div>
    </div>
  </div>
</template>
