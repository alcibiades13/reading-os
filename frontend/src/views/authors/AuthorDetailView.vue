<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authorsAPI } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { getBookUrl } from '@/utils/bookUrl'
import { getAuthorUrl } from '@/utils/authorUrl'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import {
  ArrowLeft, BookOpen, Share2, User, Calendar,
  Globe, ChevronRight, Quote, Heart, Users,
  Plus, Search, Loader2, Link2
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { addToast } = useToast()

const authorId = computed(() => {
  const param = route.params.id
  if (param && param.includes('-')) {
    return param.split('-')[0]
  }
  return param
})

const author = ref(null)
const authorBooks = ref([])
const loading = ref(true)
const isFollowing = ref(false)

// Author linking state
const potentialAliases = ref([])
const loadingPotentialAliases = ref(false)
const isLinkAuthorModalOpen = ref(false)
const aliasSearchQuery = ref('')
const aliasSearchResults = ref([])
const isSearchingAliases = ref(false)

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

// Aliases from backend
const aliases = computed(() => author.value?.aliases || [])

// Notable quote — from author data or first quote from their books
const notableQuote = computed(() => author.value?.notable_quote || null)

const handleBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/books')
  }
}

const fetchPotentialAliases = async () => {
  loadingPotentialAliases.value = true
  try {
    const response = await authorsAPI.potentialAliases(authorId.value)
    potentialAliases.value = response.data || []
  } catch (error) {
    potentialAliases.value = []
  } finally {
    loadingPotentialAliases.value = false
  }
}

const refreshAuthorData = async () => {
  const [authorResponse, booksResponse] = await Promise.all([
    authorsAPI.get(authorId.value),
    authorsAPI.books(authorId.value),
  ])
  author.value = authorResponse.data
  const booksData = booksResponse.data?.results || booksResponse.data
  authorBooks.value = Array.isArray(booksData) ? booksData : []
}

const linkPotentialAlias = async (aliasId) => {
  try {
    const response = await authorsAPI.linkAuthor(authorId.value, aliasId)
    if (response.data.success) {
      addToast('Autor povezan!', 'success')
      await refreshAuthorData()
      potentialAliases.value = potentialAliases.value.filter(a => a.id !== aliasId)
    }
  } catch (error) {
    console.error('Failed to link author:', error)
    addToast(error.response?.data?.error || 'Greska pri povezivanju', 'error')
  }
}

const linkManualAlias = async (aliasId) => {
  try {
    const response = await authorsAPI.linkAuthor(authorId.value, aliasId)
    if (response.data.success) {
      isLinkAuthorModalOpen.value = false
      aliasSearchQuery.value = ''
      aliasSearchResults.value = []
      addToast('Autor povezan!', 'success')
      await refreshAuthorData()
      fetchPotentialAliases()
    }
  } catch (error) {
    console.error('Failed to link author:', error)
    addToast(error.response?.data?.error || 'Greska pri povezivanju', 'error')
  }
}

// Manual alias search with debounce
let aliasSearchTimeout = null
watch(aliasSearchQuery, (newQuery) => {
  clearTimeout(aliasSearchTimeout)
  if (!newQuery || newQuery.trim().length < 2) {
    aliasSearchResults.value = []
    return
  }
  aliasSearchTimeout = setTimeout(async () => {
    isSearchingAliases.value = true
    try {
      const response = await authorsAPI.list({ search: newQuery.trim() })
      const results = response.data?.results || response.data || []
      aliasSearchResults.value = results.filter(a => {
        if (a.id === parseInt(authorId.value)) return false
        if (author.value?.author_group_id && a.author_group_id === author.value.author_group_id) return false
        return true
      }).slice(0, 10)
    } catch (error) {
      aliasSearchResults.value = []
    } finally {
      isSearchingAliases.value = false
    }
  }, 300)
})

onMounted(async () => {
  loading.value = true
  try {
    await refreshAuthorData()

    if (author.value?.name) {
      document.title = `${author.value.name} — Reading OS`
    }

    // Fetch potential aliases in background
    fetchPotentialAliases()
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

        <!-- Right: Sidebar -->
        <div class="lg:col-span-4 space-y-6">

          <!-- Aliases Section -->
          <div v-if="aliases.length > 0" class="p-6 lg:p-8 rounded-[2rem] bg-slate-950/40 border border-white/5 glass">
            <h3 class="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-4 flex items-center gap-2">
              <Link2 :size="10" />
              Poznato i kao
            </h3>
            <div class="space-y-2">
              <router-link
                v-for="alias in aliases"
                :key="alias.id"
                :to="getAuthorUrl(alias)"
                class="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/[0.08] border border-transparent hover:border-indigo-500/20 transition-all group"
              >
                <div class="w-8 h-8 rounded-lg bg-slate-900 flex items-center justify-center font-black text-[10px] text-indigo-400 border border-white/5">
                  {{ alias.name?.charAt(0) || '?' }}
                </div>
                <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-colors flex-1">{{ alias.name }}</span>
                <span v-if="alias.is_primary" class="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 text-[8px] font-black uppercase">Primary</span>
                <ChevronRight :size="14" class="text-slate-600 group-hover:text-indigo-400 transition-all" />
              </router-link>
            </div>
          </div>

          <!-- Potential Aliases Widget -->
          <div v-if="potentialAliases.length > 0" class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40">
            <div class="mb-4 p-3 rounded-lg bg-amber-500/5 border border-amber-500/10">
              <p class="text-xs text-amber-200/70">
                Pronasli smo autore sa slicnim imenom. Povezi ih ako se radi o istoj osobi.
              </p>
            </div>

            <div class="space-y-3">
              <div
                v-for="alias in potentialAliases"
                :key="alias.id"
                class="p-4 rounded-xl bg-slate-950/50 border border-slate-800 hover:border-amber-500/30 transition-all space-y-3"
              >
                <div class="flex gap-3">
                  <div class="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center font-black text-sm text-amber-400 border border-white/5">
                    {{ alias.name?.charAt(0) || '?' }}
                  </div>
                  <div class="flex-1 min-w-0">
                    <div class="flex items-start gap-2 mb-1">
                      <h4 class="flex-1 font-semibold text-slate-100 text-sm">{{ alias.name }}</h4>
                      <span class="shrink-0 px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[9px] font-bold">
                        {{ Math.round(alias.similarity * 100) }}%
                      </span>
                    </div>
                    <div class="text-[10px] text-slate-500">
                      {{ alias.books_count }} {{ alias.books_count === 1 ? 'book' : 'books' }}
                    </div>
                    <div v-if="alias.bio" class="text-[10px] text-slate-600 line-clamp-2 mt-1">{{ alias.bio }}</div>
                  </div>
                </div>

                <div class="pt-3 border-t border-slate-800/50 flex gap-2">
                  <button
                    @click="linkPotentialAlias(alias.id)"
                    class="flex-1 px-3 py-2 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 text-xs font-bold transition-all"
                  >
                    Povezi
                  </button>
                  <router-link
                    :to="getAuthorUrl(alias)"
                    class="px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs font-bold transition-all"
                  >
                    Pogledaj
                  </router-link>
                </div>
              </div>
            </div>
          </div>

          <!-- Link Author Button -->
          <div class="p-6 rounded-[2rem] glass border-slate-800 bg-slate-900/40 border-dashed">
            <button
              @click="isLinkAuthorModalOpen = true; aliasSearchQuery = ''; aliasSearchResults = []"
              class="w-full px-4 py-3 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 hover:border-indigo-500/50 text-indigo-400 text-sm font-bold transition-all flex items-center justify-center gap-2 group"
            >
              <Plus :size="16" class="group-hover:rotate-90 transition-transform" />
              Povezi sa drugim pravopisom
            </button>
            <p class="text-[10px] text-slate-500 text-center mt-2">
              Povezi autore sa istim imenom na razlicitim jezicima
            </p>
          </div>

          <!-- Similar Minds -->
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

    <!-- ========== LINK AUTHOR MODAL ========== -->
    <Dialog :open="isLinkAuthorModalOpen" @update:open="isLinkAuthorModalOpen = $event">
      <DialogContent class="max-w-2xl glass border-slate-700 max-h-[80vh] flex flex-col">
        <DialogHeader class="border-b border-slate-800 pb-4">
          <DialogTitle class="text-lg font-bold flex items-center gap-2 text-white">
            <Link2 :size="20" class="text-indigo-400" />
            Povezi sa drugim pravopisom
          </DialogTitle>
        </DialogHeader>

        <div class="flex-1 overflow-hidden flex flex-col space-y-4 py-4">
          <p class="text-sm text-slate-300">
            Pronadji autora "{{ author?.name }}" na drugom jeziku ili sa drugim pravopisom imena.
          </p>

          <!-- Search Input -->
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="18" />
            <input
              v-model="aliasSearchQuery"
              type="text"
              placeholder="Pretrazi po imenu autora..."
              class="w-full bg-slate-900 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-50 outline-none focus:border-indigo-500 transition-all placeholder-slate-600"
              autofocus
            />
          </div>

          <!-- Loading State -->
          <div v-if="isSearchingAliases" class="flex items-center justify-center py-8">
            <Loader2 :size="24" class="text-indigo-400 animate-spin" />
          </div>

          <!-- Search Results -->
          <div v-else-if="aliasSearchResults.length > 0" class="flex-1 overflow-y-auto space-y-3">
            <div
              v-for="result in aliasSearchResults"
              :key="result.id"
              class="p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-indigo-500/30 transition-all cursor-pointer"
              @click="linkManualAlias(result.id)"
            >
              <div class="flex gap-3">
                <div class="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center font-black text-sm text-indigo-400 border border-white/5">
                  {{ result.name?.charAt(0) || '?' }}
                </div>
                <div class="flex-1 min-w-0">
                  <h4 class="font-semibold text-slate-100 text-sm mb-1">{{ result.name }}</h4>
                  <div class="text-[11px] text-slate-500">
                    {{ result.books_count || 0 }} {{ (result.books_count || 0) === 1 ? 'book' : 'books' }}
                  </div>
                </div>
                <div class="shrink-0 flex items-center">
                  <div class="px-3 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold">
                    Povezi
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="aliasSearchQuery.trim().length >= 2" class="flex-1 flex flex-col items-center justify-center py-8 text-center">
            <div class="w-16 h-16 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center mb-4">
              <Search :size="24" class="text-slate-600" />
            </div>
            <p class="text-sm font-semibold text-slate-400 mb-1">Nema rezultata</p>
            <p class="text-xs text-slate-500">Probaj drugi termin pretrage</p>
          </div>

          <!-- Initial State -->
          <div v-else class="flex-1 flex flex-col items-center justify-center py-8 text-center">
            <div class="w-16 h-16 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4">
              <User :size="24" class="text-indigo-400" />
            </div>
            <p class="text-sm font-semibold text-slate-300 mb-1">Pretrazi autore</p>
            <p class="text-xs text-slate-500">Pocni da kucas da pronadjes autora u bazi</p>
          </div>

          <!-- Footer -->
          <div class="pt-4 border-t border-slate-800">
            <button
              @click="isLinkAuthorModalOpen = false"
              class="w-full px-4 py-3 rounded-xl text-sm font-bold text-slate-400 hover:text-white hover:bg-slate-800 transition-all border border-slate-700 hover:border-slate-600"
            >
              Otkazi
            </button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>
