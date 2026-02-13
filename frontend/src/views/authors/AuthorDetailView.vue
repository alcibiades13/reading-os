<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authorsAPI } from '@/services/api'
import { getBookUrl } from '@/utils/bookUrl'
import { getAuthorUrl } from '@/utils/authorUrl'
import {
  ArrowLeft, BookOpen, Share2, User, Calendar,
  Globe, ChevronRight, Quote, Heart, Users
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const authorId = computed(() => route.params.id)

const author = ref(null)
const authorBooks = ref([])
const loading = ref(true)
const isFollowing = ref(false)

const volumeCount = computed(() => author.value?.books_count || authorBooks.value.length)

const lifespan = computed(() => {
  if (!author.value) return null
  const birth = author.value.birth_date
  const death = author.value.death_date
  if (!birth && !death) return null
  const birthYear = birth ? new Date(birth).getFullYear() : '?'
  const deathYear = death ? new Date(death).getFullYear() : 'present'
  return `${birthYear} – ${deathYear}`
})

const authorInitials = computed(() => {
  if (!author.value?.name) return '?'
  return author.value.name
    .split(' ')
    .map(w => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

const photoUrl = computed(() => author.value?.photo || null)

// Tags from author data, or empty array
const authorTags = computed(() => author.value?.tags || [])

// Similar authors from backend, or empty array
const similarAuthors = computed(() => author.value?.similar_authors || [])

// Notable quote — from author data or first quote from their books
const notableQuote = computed(() => author.value?.notable_quote || null)

const handleBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/books')
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [authorResponse, booksResponse] = await Promise.all([
      authorsAPI.get(authorId.value),
      authorsAPI.books(authorId.value),
    ])

    author.value = authorResponse.data
    const booksData = booksResponse.data?.results || booksResponse.data
    authorBooks.value = Array.isArray(booksData) ? booksData : []

    if (author.value?.name) {
      document.title = `${author.value.name} — Reading OS`
    }
  } catch (error) {
    console.error('Failed to load author:', error)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="animate-in fade-in duration-1000">

    <!-- ==================== LOADING STATE ==================== -->
    <div v-if="loading" class="max-w-7xl mx-auto px-8 py-20 flex flex-col items-center justify-center min-h-[60vh]">
      <div class="w-12 h-12 border-4 border-slate-800 border-t-indigo-500 rounded-full animate-spin mb-4" />
      <p class="text-slate-500 font-black uppercase tracking-widest text-[9px]">Fetching Chronicles...</p>
    </div>

    <!-- ==================== ERROR / NOT FOUND ==================== -->
    <div v-else-if="!author" class="max-w-7xl mx-auto px-8 py-20">
      <div class="text-center py-24">
        <div class="w-16 h-16 rounded-full bg-rose-500/10 flex items-center justify-center mx-auto mb-4">
          <User :size="32" class="text-rose-400" />
        </div>
        <h2 class="text-xl font-bold text-white mb-2">Author Not Found</h2>
        <p class="text-slate-500 mb-6">This author doesn't exist or has been removed.</p>
        <button
          @click="handleBack"
          class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-400 transition-colors"
        >
          Go Back
        </button>
      </div>
    </div>

    <!-- ==================== MAIN CONTENT ==================== -->
    <template v-else>

      <!-- ========== 1. COMPACT HERO SECTION ========== -->
      <section class="relative min-h-[35vh] lg:min-h-[45vh] flex flex-col justify-end p-6 lg:p-16 overflow-hidden border-b border-white/5">
        <!-- Background glow -->
        <div class="absolute inset-0 opacity-10 pointer-events-none">
          <div class="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-indigo-500/15 blur-[120px] rounded-full" />
        </div>

        <!-- Back button -->
        <button
          @click="handleBack"
          class="absolute top-6 left-6 lg:top-8 lg:left-8 z-50 flex items-center gap-2 text-slate-500 hover:text-white transition-all font-black text-[9px] uppercase tracking-widest group"
        >
          <ArrowLeft :size="14" class="group-hover:-translate-x-1 transition-transform" />
          Library
        </button>

        <!-- Hero grid -->
        <div class="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-10 items-end">
          <!-- Left: Tags + Name + Stats + Actions -->
          <div class="lg:col-span-9 space-y-4 lg:space-y-6">
            <!-- Tags -->
            <div class="flex flex-wrap gap-2">
              <span
                v-for="tag in authorTags"
                :key="tag"
                class="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[8px] font-black text-indigo-400 uppercase tracking-widest"
              >
                {{ tag }}
              </span>
              <!-- Lifespan as tag if no tags exist -->
              <span
                v-if="authorTags.length === 0 && lifespan"
                class="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[8px] font-black text-indigo-400 uppercase tracking-widest flex items-center gap-1.5"
              >
                <Calendar :size="10" />
                {{ lifespan }}
              </span>
            </div>

            <!-- Author name -->
            <h1 class="text-4xl sm:text-5xl lg:text-7xl font-black text-white tracking-tighter leading-[0.95]">
              {{ author.name }}
            </h1>

            <!-- Stats + Actions row -->
            <div class="flex flex-wrap items-center gap-6 lg:gap-8">
              <!-- Volumes stat -->
              <div>
                <p class="text-[8px] font-black text-slate-600 uppercase tracking-[0.2em] mb-0.5">Volumes</p>
                <p class="text-lg font-black text-white tracking-tight">{{ volumeCount }}</p>
              </div>

              <!-- Reach stat -->
              <div>
                <p class="text-[8px] font-black text-slate-600 uppercase tracking-[0.2em] mb-0.5">Reach</p>
                <p class="text-lg font-black text-white tracking-tight">Global</p>
              </div>

              <div class="h-8 w-px bg-white/10 mx-1 hidden lg:block" />

              <!-- Follow Author button -->
              <button
                @click="isFollowing = !isFollowing"
                :class="[
                  'px-6 py-3 rounded-xl font-black text-[9px] uppercase tracking-widest transition-all',
                  isFollowing
                    ? 'bg-white/10 text-white border border-white/20'
                    : 'bg-indigo-500 text-white shadow-xl shadow-indigo-500/20 hover:scale-105'
                ]"
              >
                {{ isFollowing ? 'Following' : 'Follow Author' }}
              </button>

              <!-- Share button -->
              <button class="p-3 rounded-xl bg-white/5 text-slate-400 hover:text-white transition-all border border-white/5">
                <Share2 :size="16" />
              </button>
            </div>
          </div>

          <!-- Right: Portrait -->
          <div class="lg:col-span-3 flex justify-center lg:justify-end order-first lg:order-last">
            <div class="relative w-36 h-44 sm:w-40 sm:h-52 lg:w-56 lg:h-72 rounded-[2rem] overflow-hidden shadow-2xl ring-1 ring-white/10 group">
              <img
                v-if="photoUrl"
                :src="photoUrl"
                :alt="author.name"
                class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-1000"
              />
              <div v-else class="w-full h-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
                <span class="text-5xl lg:text-7xl font-black text-slate-500/60">{{ authorInitials }}</span>
              </div>
              <div class="absolute inset-0 bg-gradient-to-t from-slate-950/60 to-transparent" />
            </div>
          </div>
        </div>
      </section>

      <!-- ========== 2. BIOGRAPHY & SIDEBAR ========== -->
      <section class="p-6 lg:p-16 grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-16">
        <!-- Left: Bio + Social + Quote -->
        <div class="lg:col-span-8 space-y-8 lg:space-y-10">
          <!-- Section header -->
          <div class="flex items-center gap-4">
            <div class="w-8 h-px bg-indigo-500" />
            <h2 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">The Profile</h2>
          </div>

          <!-- Bio text -->
          <div class="space-y-8">
            <p v-if="author.bio" class="text-xl sm:text-2xl lg:text-3xl font-serif italic text-slate-300 leading-relaxed max-w-4xl">
              {{ author.bio }}
            </p>
            <p v-else class="text-xl sm:text-2xl lg:text-3xl font-serif italic text-slate-500 leading-relaxed max-w-4xl">
              No biography available yet. This author's story remains to be written.
            </p>

            <!-- Birth/death details -->
            <div v-if="author.birth_date || author.death_date" class="flex flex-wrap gap-4 text-xs text-slate-500">
              <div v-if="author.birth_date" class="flex items-center gap-1.5">
                <Calendar :size="12" class="text-slate-600" />
                Born {{ new Date(author.birth_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) }}
              </div>
              <div v-if="author.death_date" class="flex items-center gap-1.5">
                <Calendar :size="12" class="text-slate-600" />
                Died {{ new Date(author.death_date).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) }}
              </div>
            </div>

            <!-- Social links -->
            <div class="flex gap-4 pt-2">
              <button class="p-2.5 rounded-xl bg-white/5 border border-white/5 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"/></svg>
              </button>
              <button class="p-2.5 rounded-xl bg-white/5 border border-white/5 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/></svg>
              </button>
              <button class="p-2.5 rounded-xl bg-white/5 border border-white/5 text-slate-500 hover:text-indigo-400 hover:border-indigo-500/30 transition-all">
                <Globe :size="18" />
              </button>
            </div>
          </div>

          <!-- Notable Quote Block -->
          <div class="relative p-8 lg:p-10 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 overflow-hidden">
            <Quote :size="60" class="absolute top-[-10px] left-[-10px] text-indigo-500/5" />
            <p v-if="notableQuote" class="relative z-10 text-lg lg:text-xl font-serif italic text-indigo-300/80 leading-relaxed">
              "{{ notableQuote }}"
            </p>
            <p v-else class="relative z-10 text-lg lg:text-xl font-serif italic text-indigo-300/40 leading-relaxed">
              "No notable quotes recorded yet. Add quotes from this author's works to see them here."
            </p>
          </div>
        </div>

        <!-- Right: Similar Minds Sidebar -->
        <div class="lg:col-span-4 space-y-10">
          <div class="p-6 lg:p-8 rounded-[2rem] bg-slate-950/40 border border-white/5 glass">
            <h3 class="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-6">Similar Minds</h3>
            <div v-if="similarAuthors.length > 0" class="space-y-3">
              <router-link
                v-for="sim in similarAuthors"
                :key="sim.id"
                :to="getAuthorUrl(sim)"
                class="w-full group flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-transparent hover:border-indigo-500/20 hover:bg-white/[0.08] transition-all"
              >
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center font-black text-[10px] text-indigo-400 border border-white/5">
                    {{ sim.name?.charAt(0) || '?' }}
                  </div>
                  <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">{{ sim.name }}</span>
                </div>
                <ChevronRight :size="14" class="text-slate-600 group-hover:text-indigo-400 transition-all" />
              </router-link>
            </div>
            <!-- Empty state for similar minds -->
            <div v-else class="space-y-3">
              <div class="flex items-center justify-center py-8">
                <div class="text-center">
                  <Users :size="24" class="text-slate-700 mx-auto mb-3" />
                  <p class="text-[10px] text-slate-600 font-bold">No similar authors found yet</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- ========== 3. MASTERWORKS / BIBLIOGRAPHY ========== -->
      <section class="p-6 lg:p-16 border-t border-white/5">
        <div class="flex items-center justify-between mb-8 lg:mb-12">
          <div class="flex items-center gap-4">
            <div class="w-8 h-px bg-indigo-500" />
            <h2 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">Masterworks</h2>
          </div>
          <span v-if="authorBooks.length > 0" class="text-[9px] font-black text-slate-600 uppercase tracking-widest">{{ authorBooks.length }} Titles</span>
        </div>

        <!-- Books Grid -->
        <div v-if="authorBooks.length > 0" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-5 gap-y-8 lg:gap-x-6 lg:gap-y-10">
          <router-link
            v-for="book in authorBooks"
            :key="book.id"
            :to="getBookUrl(book)"
            class="group"
          >
            <div class="aspect-[2/3] rounded-xl lg:rounded-2xl overflow-hidden bg-slate-800/50 shadow-lg ring-1 ring-white/5 mb-2 lg:mb-3">
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <BookOpen :size="24" class="text-slate-600" />
              </div>
            </div>
            <h4 class="text-xs lg:text-sm font-bold text-white line-clamp-2 leading-tight group-hover:text-indigo-400 transition-colors">{{ book.title }}</h4>
            <p v-if="book.published_date" class="text-[10px] text-slate-500 mt-0.5">{{ book.published_date?.split('-')[0] }}</p>
          </router-link>
        </div>

        <!-- Empty State -->
        <div v-else class="text-center py-16 lg:py-24">
          <BookOpen :size="40" class="text-slate-700 mx-auto mb-4" />
          <p class="text-slate-500 text-sm">No books found for this author in the database.</p>
        </div>
      </section>

    </template>
  </div>
</template>
