<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useBookImportStore } from '@/stores/bookImportStore'
import { genresAPI } from '@/services/api'
import {
  BookOpen,
  Quote,
  Brain,
  CircleDot,
  Dna,
  PenTool,
  ArrowRight,
  ArrowLeft,
  Search,
  Check,
  Plus,
  Loader2,
  Upload,
  Star,
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const importStore = useBookImportStore()

const currentStep = ref(0)
const direction = ref('forward') // 'forward' | 'backward'
const totalSteps = 4

// Step 2: Genres
const genres = ref([])
const selectedGenres = ref([])
const loadingGenres = ref(false)

// Step 3: Reading goal
const readingGoal = ref(null)
const customGoal = ref('')
const goalPresets = [12, 24, 36, 52]

// Step 4: Book search
const bookSearchQuery = ref('')
const addedBooks = ref([])
const searchDebounce = ref(null)

const userName = computed(() => authStore.user?.first_name || 'Reader')

onMounted(async () => {
  // Load genres for step 2
  loadingGenres.value = true
  try {
    const response = await genresAPI.list({ page_size: 100 })
    genres.value = response.data.results || response.data || []
  } catch {
    genres.value = []
  } finally {
    loadingGenres.value = false
  }
})

// Navigation
function nextStep() {
  if (currentStep.value < totalSteps - 1) {
    direction.value = 'forward'
    saveCurrentStep()
    currentStep.value++
  } else {
    completeOnboarding()
  }
}

function prevStep() {
  if (currentStep.value > 0) {
    direction.value = 'backward'
    currentStep.value--
  }
}

function skipStep() {
  if (currentStep.value < totalSteps - 1) {
    direction.value = 'forward'
    currentStep.value++
  } else {
    completeOnboarding()
  }
}

// Genre toggling
function toggleGenre(genre) {
  const name = genre.name
  const idx = selectedGenres.value.indexOf(name)
  if (idx >= 0) {
    selectedGenres.value.splice(idx, 1)
  } else {
    selectedGenres.value.push(name)
  }
}

function isGenreSelected(genre) {
  return selectedGenres.value.includes(genre.name)
}

// Goal selection
function selectGoal(value) {
  readingGoal.value = value
  customGoal.value = ''
}

function setCustomGoal() {
  const num = parseInt(customGoal.value)
  if (num > 0 && num <= 365) {
    readingGoal.value = num
  }
}

// Book search
function onSearchInput() {
  clearTimeout(searchDebounce.value)
  searchDebounce.value = setTimeout(() => {
    if (bookSearchQuery.value.trim().length >= 2) {
      importStore.searchBooks(bookSearchQuery.value.trim())
    }
  }, 400)
}

async function addBook(book) {
  const result = await importStore.importBookToDatabase({
    book,
    addToLibrary: true,
    libraryData: { status: 'want_to_read' },
  })
  if (result.success) {
    addedBooks.value.push(book.title)
  }
}

function isBookAdded(book) {
  return addedBooks.value.includes(book.title)
}

// Save data at each step
async function saveCurrentStep() {
  if (currentStep.value === 1 && selectedGenres.value.length > 0) {
    await authStore.updateProfile({ profile: { favorite_genres: selectedGenres.value } })
  } else if (currentStep.value === 2 && readingGoal.value) {
    await authStore.updateProfile({ profile: { reading_goal_year: readingGoal.value } })
  }
}

async function completeOnboarding() {
  await saveCurrentStep()
  await authStore.updateProfile({ profile: { onboarding_completed: true } })
  router.push('/library')
}

// Genre colors
const genreColors = [
  'border-indigo-500/40 bg-indigo-500/10 text-indigo-300',
  'border-purple-500/40 bg-purple-500/10 text-purple-300',
  'border-sky-500/40 bg-sky-500/10 text-sky-300',
  'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
  'border-amber-500/40 bg-amber-500/10 text-amber-300',
  'border-rose-500/40 bg-rose-500/10 text-rose-300',
  'border-cyan-500/40 bg-cyan-500/10 text-cyan-300',
  'border-pink-500/40 bg-pink-500/10 text-pink-300',
]

function getGenreColor(idx) {
  return genreColors[idx % genreColors.length]
}

function getGenreSelectedColor(idx) {
  const base = genreColors[idx % genreColors.length]
  return base
    .replace('/40', '')
    .replace('/10', '/25')
}
</script>

<template>
  <div class="onboarding-page min-h-screen bg-slate-950 text-slate-50 flex flex-col">

    <!-- Background -->
    <div class="fixed inset-0 pointer-events-none">
      <div class="absolute top-[-10%] left-[-5%] w-[50%] h-[50%] bg-indigo-900/20 blur-[160px] rounded-full" />
      <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-900/15 blur-[140px] rounded-full" />
    </div>

    <!-- Header -->
    <header class="relative z-10 flex items-center justify-between px-6 sm:px-10 py-5">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
          <BookOpen :size="16" class="text-white" />
        </div>
        <span class="font-black text-lg tracking-tight">Marginalia</span>
      </div>

      <!-- Progress dots -->
      <div class="flex items-center gap-2">
        <div
          v-for="n in totalSteps"
          :key="n"
          :class="[
            'h-1.5 rounded-full transition-all duration-500',
            n - 1 === currentStep ? 'w-8 bg-indigo-500' :
            n - 1 < currentStep ? 'w-1.5 bg-indigo-500/60' : 'w-1.5 bg-slate-700'
          ]"
        />
      </div>

      <!-- Skip all -->
      <button
        @click="completeOnboarding"
        class="text-xs text-slate-500 hover:text-slate-300 transition-colors"
      >
        Skip all
      </button>
    </header>

    <!-- Content -->
    <main class="relative z-10 flex-1 flex items-center justify-center px-6 py-8">
      <div class="w-full max-w-xl">

        <!-- ===== STEP 0: WELCOME ===== -->
        <Transition :name="direction === 'forward' ? 'slide-left' : 'slide-right'" mode="out-in">
          <div v-if="currentStep === 0" key="welcome" class="space-y-8">
            <div class="text-center">
              <h1 class="text-3xl sm:text-4xl font-black tracking-tight mb-3">
                Welcome, {{ userName }}.
              </h1>
              <p class="text-slate-400 text-base leading-relaxed max-w-md mx-auto">
                Let's set up your personal reading space.
                This takes about a minute.
              </p>
            </div>

            <!-- Highlights -->
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div class="rounded-xl border border-slate-800/60 bg-slate-900/40 p-4 text-center">
                <div class="w-10 h-10 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-3">
                  <Quote :size="16" class="text-indigo-400" />
                </div>
                <p class="text-xs font-semibold mb-1">Save quotes</p>
                <p class="text-[10px] text-slate-500 leading-relaxed">Passages that matter, always accessible</p>
              </div>
              <div class="rounded-xl border border-slate-800/60 bg-slate-900/40 p-4 text-center">
                <div class="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center mx-auto mb-3">
                  <Dna :size="16" class="text-purple-400" />
                </div>
                <p class="text-xs font-semibold mb-1">Know your taste</p>
                <p class="text-[10px] text-slate-500 leading-relaxed">Discover patterns in what you love</p>
              </div>
              <div class="rounded-xl border border-slate-800/60 bg-slate-900/40 p-4 text-center">
                <div class="w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mx-auto mb-3">
                  <CircleDot :size="16" class="text-sky-400" />
                </div>
                <p class="text-xs font-semibold mb-1">Read together</p>
                <p class="text-[10px] text-slate-500 leading-relaxed">Book circles with spoiler protection</p>
              </div>
            </div>

            <div class="text-center">
              <button
                @click="nextStep"
                class="group px-8 py-3 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-lg shadow-indigo-500/20 inline-flex items-center gap-2"
              >
                Let's begin
                <ArrowRight :size="15" class="group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>

          <!-- ===== STEP 1: GENRES ===== -->
          <div v-else-if="currentStep === 1" key="genres" class="space-y-6">
            <div class="text-center">
              <h2 class="text-2xl sm:text-3xl font-black tracking-tight mb-2">
                What do you love to read?
              </h2>
              <p class="text-slate-400 text-sm">
                Pick as many as you like. This helps us personalise your experience.
              </p>
            </div>

            <!-- Genre grid -->
            <div v-if="loadingGenres" class="flex justify-center py-12">
              <Loader2 :size="24" class="text-indigo-400 animate-spin" />
            </div>
            <div v-else class="flex flex-wrap justify-center gap-2">
              <button
                v-for="(genre, idx) in genres"
                :key="genre.id || genre.slug"
                @click="toggleGenre(genre)"
                :class="[
                  'px-3.5 py-2 rounded-lg text-xs font-semibold border transition-all duration-200',
                  isGenreSelected(genre)
                    ? getGenreSelectedColor(idx) + ' ring-1 ring-white/20 scale-105'
                    : 'border-slate-700/50 bg-slate-800/30 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                ]"
              >
                <span class="flex items-center gap-1.5">
                  <Check v-if="isGenreSelected(genre)" :size="11" />
                  {{ genre.name }}
                </span>
              </button>
            </div>

            <p v-if="selectedGenres.length > 0" class="text-center text-xs text-indigo-400 font-medium">
              {{ selectedGenres.length }} selected
            </p>

            <!-- Navigation -->
            <div class="flex items-center justify-between pt-4">
              <button @click="prevStep" class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors">
                <ArrowLeft :size="14" /> Back
              </button>
              <div class="flex items-center gap-3">
                <button @click="skipStep" class="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                  Skip
                </button>
                <button
                  @click="nextStep"
                  class="group px-6 py-2.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-lg shadow-indigo-500/20 text-sm inline-flex items-center gap-1.5"
                >
                  Continue
                  <ArrowRight :size="14" class="group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>
            </div>
          </div>

          <!-- ===== STEP 2: READING GOAL ===== -->
          <div v-else-if="currentStep === 2" key="goal" class="space-y-8">
            <div class="text-center">
              <h2 class="text-2xl sm:text-3xl font-black tracking-tight mb-2">
                Set a reading intention
              </h2>
              <p class="text-slate-400 text-sm">
                How many books would you like to read this year? No pressure — this is just for you.
              </p>
            </div>

            <!-- Goal presets -->
            <div class="flex flex-wrap justify-center gap-3">
              <button
                v-for="preset in goalPresets"
                :key="preset"
                @click="selectGoal(preset)"
                :class="[
                  'relative w-20 h-20 rounded-2xl border-2 flex flex-col items-center justify-center transition-all duration-300',
                  readingGoal === preset
                    ? 'border-indigo-500 bg-indigo-500/15 shadow-lg shadow-indigo-500/20 scale-105'
                    : 'border-slate-700 bg-slate-900/40 hover:border-slate-600 hover:bg-slate-800/40'
                ]"
              >
                <span class="text-2xl font-black" :class="readingGoal === preset ? 'text-indigo-400' : 'text-slate-300'">{{ preset }}</span>
                <span class="text-[9px] text-slate-500 font-medium">books</span>
              </button>

              <!-- Custom -->
              <div
                :class="[
                  'relative w-20 h-20 rounded-2xl border-2 flex flex-col items-center justify-center transition-all duration-300',
                  readingGoal && !goalPresets.includes(readingGoal)
                    ? 'border-indigo-500 bg-indigo-500/15'
                    : 'border-slate-700 bg-slate-900/40'
                ]"
              >
                <input
                  v-model="customGoal"
                  @blur="setCustomGoal"
                  @keyup.enter="setCustomGoal"
                  type="number"
                  min="1"
                  max="365"
                  placeholder="?"
                  class="w-10 text-center text-2xl font-black bg-transparent outline-none text-slate-300 placeholder-slate-600 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                />
                <span class="text-[9px] text-slate-500 font-medium">custom</span>
              </div>
            </div>

            <p v-if="readingGoal" class="text-center text-sm text-slate-400">
              That's about <span class="text-indigo-400 font-bold">{{ Math.ceil(readingGoal / 12) }} book{{ Math.ceil(readingGoal / 12) > 1 ? 's' : '' }}</span> per month
            </p>

            <!-- Navigation -->
            <div class="flex items-center justify-between pt-4">
              <button @click="prevStep" class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors">
                <ArrowLeft :size="14" /> Back
              </button>
              <div class="flex items-center gap-3">
                <button @click="skipStep" class="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                  Skip
                </button>
                <button
                  @click="nextStep"
                  class="group px-6 py-2.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-lg shadow-indigo-500/20 text-sm inline-flex items-center gap-1.5"
                >
                  Continue
                  <ArrowRight :size="14" class="group-hover:translate-x-0.5 transition-transform" />
                </button>
              </div>
            </div>
          </div>

          <!-- ===== STEP 3: ADD BOOKS ===== -->
          <div v-else-if="currentStep === 3" key="books" class="space-y-6">
            <div class="text-center">
              <h2 class="text-2xl sm:text-3xl font-black tracking-tight mb-2">
                Bring your library
              </h2>
              <p class="text-slate-400 text-sm">
                Search for books you've read or want to read. You can always add more later.
              </p>
            </div>

            <!-- Search bar -->
            <div class="relative">
              <Search :size="16" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                v-model="bookSearchQuery"
                @input="onSearchInput"
                type="text"
                placeholder="Search by title or author..."
                class="w-full pl-11 pr-4 py-3 rounded-xl bg-slate-900/60 border border-slate-700/50 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all"
              />
            </div>

            <!-- Added count -->
            <div v-if="addedBooks.length > 0" class="flex items-center justify-center gap-2 text-xs text-emerald-400 font-medium">
              <Check :size="13" />
              {{ addedBooks.length }} book{{ addedBooks.length > 1 ? 's' : '' }} added to your library
            </div>

            <!-- Search results -->
            <div v-if="importStore.loading" class="flex justify-center py-8">
              <Loader2 :size="24" class="text-indigo-400 animate-spin" />
            </div>
            <div v-else-if="importStore.searchResults.length > 0" class="space-y-2 max-h-72 overflow-y-auto custom-scrollbar pr-1">
              <div
                v-for="book in importStore.searchResults.slice(0, 10)"
                :key="book.isbn_13 || book.title"
                class="flex items-center gap-3 p-3 rounded-xl bg-slate-900/40 border border-slate-800/50 hover:border-slate-700 transition-colors"
              >
                <!-- Cover -->
                <div class="w-10 h-14 rounded bg-gradient-to-br from-slate-700 to-slate-800 flex-shrink-0 overflow-hidden">
                  <img
                    v-if="book.cover_image_url"
                    :src="book.cover_image_url"
                    :alt="book.title"
                    class="w-full h-full object-cover"
                  />
                </div>
                <!-- Info -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-slate-200 truncate">{{ book.title }}</p>
                  <p class="text-[11px] text-slate-500 truncate">{{ book.authors?.join(', ') || 'Unknown author' }}</p>
                </div>
                <!-- Add button -->
                <button
                  v-if="!isBookAdded(book)"
                  @click="addBook(book)"
                  class="px-3 py-1.5 rounded-lg bg-indigo-500/15 border border-indigo-500/30 text-indigo-400 text-xs font-semibold hover:bg-indigo-500/25 transition-colors flex items-center gap-1 flex-shrink-0"
                >
                  <Plus :size="12" /> Add
                </button>
                <div v-else class="px-3 py-1.5 rounded-lg bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-semibold flex items-center gap-1 flex-shrink-0">
                  <Check :size="12" /> Added
                </div>
              </div>
            </div>
            <div v-else-if="bookSearchQuery.length >= 2 && !importStore.loading" class="text-center py-8 text-sm text-slate-500">
              No books found. Try a different search.
            </div>

            <!-- Alternative actions -->
            <div v-if="!bookSearchQuery && importStore.searchResults.length === 0" class="space-y-3 pt-2">
              <button
                @click="router.push('/import')"
                class="w-full flex items-center gap-3 p-4 rounded-xl border border-slate-800/50 bg-slate-900/30 hover:border-slate-700 transition-colors text-left"
              >
                <div class="w-9 h-9 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center flex-shrink-0">
                  <Upload :size="15" class="text-amber-400" />
                </div>
                <div>
                  <p class="text-sm font-semibold">Import from Goodreads</p>
                  <p class="text-[10px] text-slate-500">Bring your entire reading history</p>
                </div>
              </button>
            </div>

            <!-- Navigation -->
            <div class="flex items-center justify-between pt-4">
              <button @click="prevStep" class="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-300 transition-colors">
                <ArrowLeft :size="14" /> Back
              </button>
              <div class="flex items-center gap-3">
                <button @click="skipStep" class="text-xs text-slate-500 hover:text-slate-300 transition-colors">
                  I'll do this later
                </button>
                <button
                  @click="completeOnboarding"
                  class="group px-6 py-2.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-lg shadow-indigo-500/20 text-sm inline-flex items-center gap-1.5"
                >
                  Finish
                  <Check :size="14" />
                </button>
              </div>
            </div>
          </div>
        </Transition>

      </div>
    </main>
  </div>
</template>

<style scoped>
.onboarding-page {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: #0f172a !important;
  color: #f8fafc !important;
}

/* Step transitions */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.35s ease;
}

.slide-left-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-40px);
}

.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-40px);
}
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(40px);
}

/* Custom scrollbar for book results */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
}
</style>
