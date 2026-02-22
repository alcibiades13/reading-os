<script setup>
import { computed, ref } from 'vue'
import { Fingerprint, BookOpen, Users, Sparkles } from 'lucide-vue-next'

const props = defineProps({
  taste: {
    type: Object,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: 'Reading Taste',
  },
  accentColor: {
    type: String,
    default: 'indigo', // 'indigo' | 'amber'
  },
})

const dnaAttributes = [
  { key: 'pace', label: 'Pace', left: 'Slow', right: 'Fast' },
  { key: 'complexity', label: 'Complexity', left: 'Simple', right: 'Complex' },
  { key: 'emotional_intensity', label: 'Emotion', left: 'Light', right: 'Intense' },
  { key: 'darkness', label: 'Tone', left: 'Light', right: 'Dark' },
  { key: 'character_focus', label: 'Focus', left: 'Plot', right: 'Characters' },
  { key: 'introspection', label: 'Depth', left: 'Action', right: 'Introspective' },
]

const hasDna = computed(() => {
  return props.taste?.dna_vector && Object.keys(props.taste.dna_vector).length > 0
})

const hasGenres = computed(() => props.taste?.top_genres?.length > 0)
const hasAuthors = computed(() => props.taste?.top_authors?.length > 0)
const hasThemes = computed(() => props.taste?.top_themes?.length > 0)
const hasGenreTags = computed(() => props.taste?.top_genre_tags?.length > 0)

const displayGenres = computed(() => (props.taste?.top_genres || []).slice(0, 6))
const authorSortMode = ref('books') // 'books' | 'pages'

const displayAuthors = computed(() => {
  const authors = [...(props.taste?.top_authors || [])]
  if (authorSortMode.value === 'pages') {
    authors.sort((a, b) => (b.total_pages || 0) - (a.total_pages || 0))
  } else {
    authors.sort((a, b) => (b.books_count || 0) - (a.books_count || 0))
  }
  return authors.slice(0, 10)
})
const displayThemes = computed(() => (props.taste?.top_themes || []).slice(0, 8))
const displayGenreTags = computed(() => (props.taste?.top_genre_tags || []).slice(0, 6))

const maxGenreScore = computed(() => {
  if (!displayGenres.value.length) return 1
  return displayGenres.value[0].score || 1
})

// Count how many left-column sections we have
const leftSectionCount = computed(() => {
  let c = 0
  if (hasGenres.value) c++
  if (hasGenreTags.value && !hasGenres.value) c++ // genre tags as fallback
  if (hasAuthors.value) c++
  if (hasThemes.value) c++
  return c
})

function formatPages(pages) {
  return pages.toLocaleString()
}

function humanizeSlug(slug) {
  return slug.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getDnaWidth(key) {
  const val = props.taste?.dna_vector?.[key] ?? 0.5
  return `${val * 100}%`
}

// Accent color classes
const accentClasses = computed(() => {
  const c = props.accentColor
  return {
    gradient: c === 'amber'
      ? 'from-amber-500/5 via-transparent to-orange-500/5'
      : 'from-indigo-500/5 via-transparent to-purple-500/5',
    iconBg: c === 'amber' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-indigo-500/10 border-indigo-500/20',
    iconText: c === 'amber' ? 'text-amber-400' : 'text-indigo-400',
    pill: c === 'amber'
      ? 'bg-amber-500/10 border-amber-500/20 text-amber-400'
      : 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400',
    bar: c === 'amber'
      ? 'from-amber-500 to-orange-500'
      : 'from-indigo-500 to-purple-500',
    authorDot: c === 'amber' ? 'bg-amber-500' : 'bg-indigo-500',
  }
})
</script>

<template>
  <div :class="['p-6 rounded-3xl bg-gradient-to-br border border-white/5', accentClasses.gradient]">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
      <div :class="['w-10 h-10 rounded-xl border flex items-center justify-center', accentClasses.iconBg]">
        <Fingerprint :size="20" :class="accentClasses.iconText" />
      </div>
      <div>
        <h3 class="text-lg font-black text-white">{{ title }}</h3>
        <p class="text-xs text-slate-500">Based on {{ taste.books_count || 0 }} books</p>
      </div>
    </div>

    <!-- Multi-column layout -->
    <div :class="['grid gap-6', compact ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3']">

      <!-- Column 1: Authors -->
      <div v-if="hasAuthors" class="space-y-5">
        <div>
          <div class="flex items-center justify-between mb-2">
            <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest">
              <Users :size="10" class="inline mr-1 -mt-0.5" />Top Authors
            </span>
            <div class="flex gap-0.5 bg-white/5 rounded-lg p-0.5">
              <button
                @click="authorSortMode = 'books'"
                :class="['px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider transition-colors',
                  authorSortMode === 'books' ? 'bg-white/10 text-slate-300' : 'text-slate-500 hover:text-slate-400']"
              >Books</button>
              <button
                @click="authorSortMode = 'pages'"
                :class="['px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider transition-colors',
                  authorSortMode === 'pages' ? 'bg-white/10 text-slate-300' : 'text-slate-500 hover:text-slate-400']"
              >Pages</button>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-x-4 gap-y-1.5">
            <div v-for="(author, i) in displayAuthors" :key="author.id" class="flex items-center gap-2">
              <div :class="['w-1.5 h-1.5 rounded-full shrink-0', accentClasses.authorDot]" :style="{ opacity: 1 - i * 0.05 }" />
              <div class="min-w-0">
                <span class="text-sm text-slate-300 font-medium truncate block">{{ author.name }}</span>
                <span class="text-[10px] text-slate-500">
                  <template v-if="authorSortMode === 'pages' && author.total_pages">{{ formatPages(author.total_pages) }} pg · {{ author.books_count }} {{ author.books_count === 1 ? 'book' : 'books' }}</template>
                  <template v-else>{{ author.books_count }} {{ author.books_count === 1 ? 'book' : 'books' }}<template v-if="author.total_pages"> · {{ formatPages(author.total_pages) }} pg</template></template>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Column 2: Genres + Themes -->
      <div v-if="hasGenres || hasGenreTags || hasThemes" class="space-y-5">
        <!-- Top Genres -->
        <div v-if="hasGenres">
          <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest block mb-2">
            <BookOpen :size="10" class="inline mr-1 -mt-0.5" />Top Genres
          </span>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="genre in displayGenres"
              :key="genre.id"
              :class="['px-2.5 py-1 rounded-xl border text-[10px] font-black uppercase tracking-wider', accentClasses.pill]"
              :style="{ opacity: 0.5 + (genre.score / maxGenreScore) * 0.5 }"
            >
              {{ genre.name }}
            </span>
          </div>
        </div>

        <!-- Genre Tags (fallback if no genres) -->
        <div v-else-if="hasGenreTags">
          <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest block mb-2">
            <BookOpen :size="10" class="inline mr-1 -mt-0.5" />Top Genres
          </span>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="tag in displayGenreTags"
              :key="tag"
              :class="['px-2.5 py-1 rounded-xl border text-[10px] font-black uppercase tracking-wider', accentClasses.pill]"
            >
              {{ humanizeSlug(tag) }}
            </span>
          </div>
        </div>

        <!-- Themes & Motifs -->
        <div v-if="hasThemes">
          <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest block mb-2">
            <Sparkles :size="10" class="inline mr-1 -mt-0.5" />Themes & Motifs
          </span>
          <div class="flex flex-wrap gap-1.5">
            <span
              v-for="theme in displayThemes"
              :key="theme"
              class="px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold text-slate-400 capitalize"
            >
              {{ humanizeSlug(theme) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Column 3: DNA Vector -->
      <div v-if="hasDna">
        <span class="text-[10px] font-black text-slate-600 uppercase tracking-widest block mb-2">
          Reading Profile
        </span>
        <div class="grid gap-2.5 grid-cols-1">
          <div v-for="attr in dnaAttributes" :key="attr.key" class="space-y-0.5">
            <div class="flex justify-between text-[9px] text-slate-500 uppercase tracking-wider font-bold">
              <span>{{ attr.left }}</span>
              <span class="text-slate-400">{{ attr.label }}</span>
              <span>{{ attr.right }}</span>
            </div>
            <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden">
              <div
                :class="['h-full bg-gradient-to-r rounded-full transition-all duration-500', accentClasses.bar]"
                :style="{ width: getDnaWidth(attr.key) }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
:global(body.light) .text-white {
  color: #0f172a !important;
}
:global(body.light) .bg-slate-800 {
  background-color: #e2e8f0 !important;
}
:global(body.light) .text-slate-300 {
  color: #334155 !important;
}
:global(body.light) .bg-white\/5 {
  background-color: rgba(0, 0, 0, 0.05) !important;
}
:global(body.light) .bg-white\/10 {
  background-color: rgba(0, 0, 0, 0.08) !important;
}
</style>
