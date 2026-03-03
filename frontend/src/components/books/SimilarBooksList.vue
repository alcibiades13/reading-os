<script setup>
import { BookOpen, Sparkles } from 'lucide-vue-next'
import { getBookUrl } from '@/utils/bookUrl'

defineProps({
  books: { type: Array, required: true },
  loading: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
})

defineEmits(['clickBook'])
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5" v-if="!compact">
      <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
        <Sparkles :size="16" class="text-indigo-400" />
      </div>
      <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Similar Books</h3>
    </div>
    <div v-else class="flex items-center gap-2 mb-4">
      <Sparkles :size="16" class="text-indigo-400" />
      <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Similar Books</h3>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="space-y-4">
      <div v-for="n in 3" :key="n" class="flex items-center gap-3 animate-pulse">
        <div class="w-12 h-16 rounded-lg bg-slate-800" />
        <div class="flex-1 space-y-2">
          <div class="h-3 bg-slate-800 rounded w-3/4" />
          <div class="h-2 bg-slate-800 rounded w-1/2" />
        </div>
      </div>
    </div>

    <!-- Books List -->
    <div v-else-if="books.length > 0" class="space-y-1">
      <router-link
        v-for="simBook in books"
        :key="simBook.id"
        :to="getBookUrl(simBook)"
        @click="$emit('clickBook', simBook)"
        :class="[
          'group flex items-center gap-3 p-2 -mx-1 rounded-xl transition-all',
          compact ? 'active:bg-white/5 -mx-2' : 'hover:bg-white/5'
        ]"
      >
        <div :class="[
          'shrink-0 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center',
          compact ? 'w-10 h-14' : 'w-14 h-20'
        ]">
          <img
            v-if="simBook.cover_image"
            :src="simBook.cover_image"
            :alt="simBook.title"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            @error="(e) => e.target.style.display = 'none'"
          />
          <BookOpen v-else :size="compact ? 14 : 18" class="text-slate-600" />
        </div>
        <div class="flex-1 min-w-0 py-0.5">
          <h4 :class="[
            'font-bold text-white text-sm leading-snug group-hover:text-indigo-400 transition-colors',
            compact ? 'line-clamp-1' : 'line-clamp-2'
          ]">
            {{ simBook.title }}
          </h4>
          <p class="text-slate-400 text-xs truncate mt-0.5">
            {{ simBook.authors?.map(a => a.name).join(', ') || 'Unknown' }}
          </p>
          <span v-if="simBook.similarity_score" class="text-[10px] font-bold text-indigo-400">
            {{ Math.round(simBook.similarity_score) }}% {{ compact ? 'match' : 'similar' }}
          </span>
        </div>
      </router-link>
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-6">
      <div class="w-12 h-12 mx-auto rounded-full bg-slate-800/50 flex items-center justify-center mb-3">
        <BookOpen :size="20" class="text-slate-600" />
      </div>
      <p class="text-slate-500 text-xs">
        Rate this book to discover similar reads
      </p>
    </div>
  </div>
</template>
