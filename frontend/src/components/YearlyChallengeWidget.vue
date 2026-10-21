<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useChallengesStore } from '@/stores/challengesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { challengesAPI } from '@/services/api'
import { Target, Edit2, Plus, TrendingUp, BookOpen, ChevronDown, ChevronUp } from 'lucide-vue-next'

const challengesStore = useChallengesStore()
const booksStore = useUserBooksStore()
const router = useRouter()

const emit = defineEmits(['edit', 'create'])

const currentYear = new Date().getFullYear()

onMounted(async () => {
  await challengesStore.fetchCurrentChallenges()
})

const yearlyChallenge = computed(() => challengesStore.currentYearChallenge)

const progressPercentage = computed(() => {
  if (!yearlyChallenge.value) return 0
  return yearlyChallenge.value.progress_percentage || 0
})

const pagesReadThisYear = computed(() => {
  let totalPages = 0
  booksStore.books.forEach(userBook => {
    const book = userBook.book
    const finishedAt = userBook.finished_at ? new Date(userBook.finished_at) : null
    if (userBook.status === 'read' && finishedAt && finishedAt.getFullYear() === currentYear) {
      totalPages += book?.pages || 0
    } else if (userBook.status === 'currently_reading') {
      totalPages += userBook.current_page || 0
    }
  })
  return totalPages
})

const handleEdit = () => {
  if (yearlyChallenge.value) {
    emit('edit', yearlyChallenge.value)
  } else {
    emit('create')
  }
}

// Books list
const showBooks = ref(false)
const books = ref([])
const loadingBooks = ref(false)

const toggleBooks = async () => {
  showBooks.value = !showBooks.value
  if (!showBooks.value || books.value.length) return
  loadingBooks.value = true
  try {
    const res = await challengesAPI.progressDetails(yearlyChallenge.value.id)
    books.value = res.data.qualifying_items || []
  } finally {
    loadingBooks.value = false
  }
}

const goToBook = (book) => {
  router.push(`/books/${book.id}-${book.slug}`)
}
</script>

<template>
  <div class="glass rounded-2xl p-6 border border-zinc-800">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Target :size="18" class="text-indigo-400" />
        <h3 class="text-sm font-bold text-white">{{ currentYear }} Reading Challenge</h3>
      </div>
      <button
        @click="handleEdit"
        class="p-1.5 rounded-lg bg-zinc-800/50 hover:bg-zinc-700 text-zinc-400 hover:text-white transition-colors"
      >
        <Edit2 v-if="yearlyChallenge" :size="14" />
        <Plus v-else :size="14" />
      </button>
    </div>

    <!-- Challenge Display -->
    <div v-if="yearlyChallenge" class="space-y-4">
      <!-- Progress Numbers -->
      <div class="flex items-baseline gap-2">
        <span class="text-4xl font-black text-white">{{ yearlyChallenge.completed_books || 0 }}</span>
        <span class="text-2xl font-bold text-zinc-500">/</span>
        <span class="text-2xl font-bold text-zinc-400">{{ yearlyChallenge.target_books || 0 }}</span>
        <span class="text-xs text-zinc-500 ml-1">books</span>
      </div>

      <!-- Progress Bar -->
      <div class="relative w-full h-3 bg-zinc-800 rounded-full overflow-hidden">
        <div
          :style="{ width: `${progressPercentage}%` }"
          class="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
        />
      </div>

      <!-- Progress Percentage -->
      <div class="flex items-center justify-between text-xs">
        <span class="text-zinc-500">{{ progressPercentage.toFixed(0) }}% complete</span>
        <div v-if="yearlyChallenge.is_completed" class="flex items-center gap-1 text-green-400">
          <TrendingUp :size="12" />
          <span class="font-semibold">Completed!</span>
        </div>
        <span v-else class="text-zinc-500">
          {{ (yearlyChallenge.target_books || 0) - (yearlyChallenge.completed_books || 0) }} to go
        </span>
      </div>

      <!-- Books toggle -->
      <button
        @click="toggleBooks"
        class="w-full flex items-center justify-between pt-3 mt-1 border-t border-zinc-800/50 text-xs text-zinc-400 hover:text-white transition-colors"
      >
        <div class="flex items-center gap-2">
          <BookOpen :size="14" class="text-indigo-400" />
          <span><span class="font-bold text-white">{{ pagesReadThisYear.toLocaleString() }}</span> pages · {{ yearlyChallenge.completed_books || 0 }} books</span>
        </div>
        <ChevronUp v-if="showBooks" :size="14" />
        <ChevronDown v-else :size="14" />
      </button>

      <!-- Books list -->
      <div v-if="showBooks" class="space-y-1 max-h-52 overflow-y-auto -mx-1 px-1">
        <div v-if="loadingBooks" class="text-xs text-zinc-500 py-3 text-center">Loading...</div>
        <template v-else>
          <div
            v-for="book in books"
            :key="book.id"
            @click="goToBook(book)"
            class="flex items-center gap-2 py-1.5 px-1 rounded-lg hover:bg-zinc-800/60 cursor-pointer transition-colors"
          >
            <img v-if="book.cover_image" :src="book.cover_image" class="w-6 h-9 object-cover rounded shrink-0" />
            <div v-else class="w-6 h-9 bg-zinc-800 rounded shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-xs font-medium text-zinc-200 truncate">{{ book.title }}</p>
              <p class="text-[10px] text-zinc-500 truncate">{{ book.authors?.join(', ') }}</p>
            </div>
            <span class="text-[10px] text-zinc-600 shrink-0">{{ book.finished_at }}</span>
          </div>
          <p v-if="!books.length" class="text-xs text-zinc-500 py-2 text-center">No books read yet.</p>
        </template>
      </div>

      <!-- Challenge Title (if custom) -->
      <p v-if="yearlyChallenge.title && yearlyChallenge.title !== `${currentYear} Reading Challenge`" class="text-xs text-zinc-400 italic">
        "{{ yearlyChallenge.title }}"
      </p>
    </div>

    <!-- No Challenge State -->
    <div v-else class="text-center py-6">
      <div class="p-4 rounded-full bg-zinc-800/50 w-fit mx-auto mb-3">
        <Target :size="24" class="text-zinc-600" />
      </div>
      <p class="text-sm text-zinc-500 mb-3">No reading challenge set for {{ currentYear }}</p>
      <button
        @click="handleEdit"
        class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold transition-colors"
      >
        Create Challenge
      </button>
    </div>
  </div>
</template>
