<script setup>
import { ref, watch, computed, nextTick } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { BookOpen, Plus, ChevronRight, Trophy, Clock, Check, Search, X } from 'lucide-vue-next'
import api from '@/services/api'

const circlesStore = useCirclesStore()

const showAddBookModal = ref(false)
const bookSearch = ref('')
const bookResults = ref([])
const searchingBooks = ref(false)
const addingBook = ref(false)
const bookStatus = ref('upcoming')
const bookSearchInput = ref(null)

// Focus search input when add book modal opens
watch(showAddBookModal, (val) => {
  if (val) {
    nextTick(() => bookSearchInput.value?.focus())
  }
})

// Load club readings when circle changes
watch(() => circlesStore.activeCircleId, (newId) => {
  if (newId) {
    circlesStore.fetchClubReadings(newId)
    circlesStore.fetchMemberProgress(newId)
  }
}, { immediate: true })

const averageProgress = computed(() => {
  if (!circlesStore.memberProgress.length) return 0
  const total = circlesStore.memberProgress.reduce((sum, m) => sum + m.reading_progress, 0)
  return Math.round(total / circlesStore.memberProgress.length)
})

async function searchBooks() {
  if (!bookSearch.value.trim() || bookSearch.value.length < 2) {
    bookResults.value = []
    return
  }
  searchingBooks.value = true
  try {
    const response = await api.get(`/books/?search=${encodeURIComponent(bookSearch.value)}`)
    bookResults.value = response.data.results || response.data || []
  } catch (error) {
    console.error('Error searching books:', error)
  } finally {
    searchingBooks.value = false
  }
}

async function handleAddBook(book) {
  if (!circlesStore.activeCircleId) return
  addingBook.value = true
  try {
    await circlesStore.addClubReading({
      circle: circlesStore.activeCircleId,
      book: book.id,
      status: bookStatus.value,
    })
    // Re-fetch full data (create response lacks book_data)
    await Promise.all([
      circlesStore.fetchClubReadings(circlesStore.activeCircleId),
      circlesStore.fetchCircleDetail(circlesStore.activeCircleId),
    ])
    showAddBookModal.value = false
    bookSearch.value = ''
    bookResults.value = []
  } catch (error) {
    console.error('Error adding book:', error)
  } finally {
    addingBook.value = false
  }
}

async function handleSetCurrent(readingId) {
  await circlesStore.setCurrentReading(readingId)
  await circlesStore.fetchMemberProgress(circlesStore.activeCircleId)
}

async function handleDeleteReading(readingId) {
  if (!confirm('Remove this book from the reading list?')) return
  await circlesStore.deleteClubReading(readingId)
  // Also refresh circle detail (in case current book changed)
  await circlesStore.fetchCircleDetail(circlesStore.activeCircleId)
}

function getUserInitial(user) {
  return user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'
}
</script>

<template>
  <div class="flex-1 overflow-y-auto custom-scrollbar p-8 space-y-8">
    <!-- Current Book Hero -->
    <div v-if="circlesStore.activeCircle?.current_book_data" class="p-6 rounded-3xl bg-gradient-to-br from-indigo-500/10 via-purple-500/5 to-transparent border border-indigo-500/20">
      <p class="text-[9px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-4">Currently Reading</p>
      <div class="flex gap-6">
        <div class="w-24 h-36 rounded-xl overflow-hidden shrink-0 shadow-xl shadow-black/40">
          <img
            v-if="circlesStore.activeCircle.current_book_data.cover_image"
            :src="circlesStore.activeCircle.current_book_data.cover_image"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center">
            <BookOpen :size="24" class="text-slate-600" />
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-xl font-black text-white mb-1">{{ circlesStore.activeCircle.current_book_data.title }}</h3>
          <p class="text-sm text-slate-400 mb-4">
            {{ circlesStore.activeCircle.current_book_data.authors?.map(a => a.name).join(', ') }}
          </p>
          <div class="mb-2">
            <div class="flex items-center justify-between mb-1">
              <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Circle Progress</span>
              <span class="text-sm font-black text-indigo-400">{{ averageProgress }}%</span>
            </div>
            <div class="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
                :style="{ width: `${averageProgress}%` }"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Member Progress Leaderboard -->
    <div v-if="circlesStore.memberProgress.length > 0">
      <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
        <Trophy :size="14" class="text-amber-400" /> Member Progress
      </h3>
      <div class="space-y-2">
        <div
          v-for="(member, idx) in circlesStore.memberProgress"
          :key="member.user?.id"
          class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5"
        >
          <span class="text-[10px] font-black text-slate-600 w-5 text-center">{{ idx + 1 }}</span>
          <div class="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs shrink-0 overflow-hidden">
            <img v-if="member.user?.avatar" :src="member.user.avatar" class="w-full h-full object-cover" />
            <span v-else>{{ getUserInitial(member.user) }}</span>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-white truncate">{{ member.user?.first_name }} {{ member.user?.last_name }}</p>
            <div class="flex items-center gap-2 mt-1">
              <div class="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                <div
                  class="h-full bg-indigo-500 rounded-full transition-all"
                  :style="{ width: `${member.reading_progress}%` }"
                />
              </div>
              <span class="text-[10px] font-black text-indigo-400 shrink-0">{{ member.reading_progress }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Upcoming Queue -->
    <div v-if="circlesStore.upcomingReadings.length > 0">
      <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
        <Clock :size="14" class="text-cyan-400" /> Up Next
      </h3>
      <div class="space-y-2">
        <div
          v-for="reading in circlesStore.upcomingReadings"
          :key="reading.id"
          class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5 group"
        >
          <div class="w-10 h-14 rounded-lg overflow-hidden shrink-0 shadow-lg">
            <img v-if="reading.book_data?.cover_image" :src="reading.book_data.cover_image" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="12" class="text-slate-600" /></div>
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-bold text-white truncate">{{ reading.book_data?.title }}</p>
            <p class="text-xs text-slate-500 truncate">{{ reading.book_data?.authors?.map(a => a.name).join(', ') }}</p>
          </div>
          <div v-if="circlesStore.isCircleAdmin" class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click="handleSetCurrent(reading.id)"
              class="px-2 py-1 rounded-lg bg-indigo-500/20 text-indigo-400 text-[10px] font-bold hover:bg-indigo-500/30 transition-colors"
            >
              Set Current
            </button>
            <button
              @click="handleDeleteReading(reading.id)"
              class="p-1 rounded-lg text-slate-600 hover:text-rose-400 transition-colors"
            >
              <X :size="12" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Past Reads -->
    <div v-if="circlesStore.completedReadings.length > 0">
      <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-4 flex items-center gap-2">
        <Check :size="14" class="text-emerald-400" /> Previously Read
      </h3>
      <div class="flex flex-wrap gap-3">
        <div
          v-for="reading in circlesStore.completedReadings"
          :key="reading.id"
          class="w-16 group relative"
        >
          <div class="w-16 h-24 rounded-lg overflow-hidden shadow-lg">
            <img v-if="reading.book_data?.cover_image" :src="reading.book_data.cover_image" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="14" class="text-slate-600" /></div>
          </div>
          <p class="text-[9px] text-slate-500 text-center mt-1 truncate">{{ reading.book_data?.title }}</p>
        </div>
      </div>
    </div>

    <!-- Admin: Add Book -->
    <div v-if="circlesStore.isCircleAdmin">
      <button
        @click="showAddBookModal = true"
        class="w-full p-4 rounded-2xl border-2 border-dashed border-white/10 text-slate-500 hover:border-indigo-500/40 hover:text-indigo-400 transition-all flex items-center justify-center gap-2"
      >
        <Plus :size="18" />
        <span class="text-sm font-bold">Add Book to Reading List</span>
      </button>
    </div>

    <!-- No readings state -->
    <div v-if="!circlesStore.activeCircle?.current_book_data && !circlesStore.upcomingReadings.length && !circlesStore.completedReadings.length" class="text-center py-16">
      <BookOpen :size="48" class="text-slate-700 mx-auto mb-4" />
      <h3 class="text-lg font-black text-slate-400 mb-2">No Books Yet</h3>
      <p class="text-sm text-slate-600 mb-4">Start your reading journey by adding a book to the club.</p>
      <button
        v-if="circlesStore.isCircleAdmin"
        @click="showAddBookModal = true"
        class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors"
      >
        Add First Book
      </button>
    </div>
  </div>

  <!-- Add Book Modal -->
  <Teleport to="body">
    <div v-if="showAddBookModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showAddBookModal = false" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Add Book to Club</h2>
          <button @click="showAddBookModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
            <X :size="20" />
          </button>
        </div>
        <div class="p-6 space-y-6">
          <div>
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Search Books</label>
            <div class="relative">
              <Search :size="18" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                ref="bookSearchInput"
                v-model="bookSearch"
                @input="searchBooks"
                type="text"
                placeholder="Search by title or author..."
                class="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div>
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Add as</label>
            <div class="flex gap-2">
              <button
                @click="bookStatus = 'upcoming'"
                :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-colors', bookStatus === 'upcoming' ? 'bg-cyan-500/20 text-cyan-400' : 'bg-white/5 text-slate-400']"
              >
                Upcoming
              </button>
              <button
                @click="bookStatus = 'current'"
                :class="['px-3 py-1.5 rounded-lg text-xs font-bold transition-colors', bookStatus === 'current' ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/5 text-slate-400']"
              >
                Current
              </button>
            </div>
          </div>

          <div v-if="searchingBooks" class="flex items-center justify-center py-8">
            <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
          </div>

          <div v-else-if="bookResults.length > 0" class="space-y-2 max-h-60 overflow-y-auto">
            <button
              v-for="book in bookResults"
              :key="book.id"
              @click="handleAddBook(book)"
              :disabled="addingBook"
              class="w-full flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors text-left disabled:opacity-50"
            >
              <div class="w-10 h-14 rounded-lg overflow-hidden shrink-0 shadow-lg">
                <img v-if="book.cover_image" :src="book.cover_image" class="w-full h-full object-cover" />
                <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="12" class="text-slate-600" /></div>
              </div>
              <div class="min-w-0">
                <p class="text-sm font-bold text-white truncate">{{ book.title }}</p>
                <p class="text-xs text-slate-500 truncate">{{ book.authors?.map(a => a.name).join(', ') }}</p>
              </div>
              <ChevronRight :size="16" class="text-slate-600 shrink-0 ml-auto" />
            </button>
          </div>

          <div v-else-if="bookSearch.length >= 2" class="text-center py-8 text-slate-500 text-sm">
            No books found
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }
</style>
