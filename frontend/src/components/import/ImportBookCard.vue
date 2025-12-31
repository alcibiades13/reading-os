<script setup>
import { Star, BookOpen, Calendar, Globe } from 'lucide-vue-next'

const props = defineProps({
  book: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['click'])

const coverUrl = props.book.cover_image_url
const hasCover = !!props.book.cover_image_url
const authors = props.book.authors?.join(', ') || 'Unknown Author'
const publishedYear = props.book.published_date?.split('-')[0] || null
</script>

<template>
  <div
    class="group cursor-pointer transition-all duration-300 transform hover:-translate-y-2"
    @click="emit('click', book)"
  >
    <!-- Cover Image Container -->
    <div class="relative aspect-[2/3] w-full rounded-xl overflow-hidden shadow-2xl bg-slate-800 border border-slate-700/50">
      <img
        v-if="hasCover"
        :src="coverUrl"
        :alt="book.title"
        class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        loading="lazy"
      />

      <!-- Beautiful placeholder for missing covers -->
      <div v-else class="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-br from-slate-800 via-slate-900 to-slate-950">
        <div class="w-20 h-20 rounded-full bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center mb-4">
          <BookOpen :size="32" class="text-indigo-500/40" />
        </div>
        <h3 class="text-slate-400 text-sm font-bold text-center line-clamp-3 leading-tight">
          {{ book.title }}
        </h3>
        <p class="text-slate-600 text-xs mt-2 text-center">
          No cover available
        </p>
      </div>

      <!-- Hover Overlay -->
      <div class="absolute inset-0 bg-slate-950/80 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col items-center justify-center p-6 text-center space-y-4">
        <div v-if="book.average_rating" class="flex items-center gap-1.5 text-amber-400">
          <Star :size="16" fill="currentColor" />
          <span class="font-semibold">{{ book.average_rating }}</span>
        </div>

        <div class="flex flex-col items-center text-slate-300 text-sm space-y-1">
          <span v-if="book.page_count" class="flex items-center gap-1.5">
            <BookOpen :size="14" /> {{ book.page_count }} pages
          </span>
          <span v-if="publishedYear" class="flex items-center gap-1.5">
            <Calendar :size="14" /> {{ publishedYear }}
          </span>
        </div>

        <button class="px-5 py-2 glass rounded-full text-white text-sm font-medium hover:bg-white/20 transition-colors">
          Preview Details
        </button>
      </div>
    </div>

    <!-- Book Info -->
    <div class="mt-4 px-1">
      <h3 class="text-slate-100 font-semibold line-clamp-2 leading-tight group-hover:text-indigo-400 transition-colors">
        {{ book.title }}
      </h3>
      <p class="text-slate-400 text-sm mt-1 truncate">{{ authors }}</p>

      <div class="flex flex-wrap gap-2 mt-3">
        <span
          v-if="publishedYear"
          class="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider"
        >
          {{ publishedYear }}
        </span>
        <span
          v-if="book.language"
          class="px-2 py-0.5 rounded bg-slate-800 text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1"
        >
          <Globe :size="10" /> {{ book.language.toUpperCase() }}
        </span>
        <span
          v-if="book.source === 'google_books'"
          class="px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-bold uppercase tracking-wider"
        >
          Google
        </span>
        <span
          v-if="book.source === 'open_library'"
          class="px-2 py-0.5 rounded bg-green-500/10 text-green-400 border border-green-500/20 text-[10px] font-bold uppercase tracking-wider"
        >
          Open Library
        </span>
      </div>
    </div>
  </div>
</template>
