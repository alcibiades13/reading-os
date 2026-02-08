<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChallengesStore } from '@/stores/challengesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { Target, Edit2, Plus, TrendingUp, BookOpen } from 'lucide-vue-next'

const challengesStore = useChallengesStore()
const booksStore = useUserBooksStore()

const emit = defineEmits(['edit', 'create'])

const currentYear = new Date().getFullYear()

// Fetch current challenges on mount
onMounted(async () => {
  await challengesStore.fetchCurrentChallenges()
})

// Get current year's challenge
const yearlyChallenge = computed(() => challengesStore.currentYearChallenge)

// Progress percentage
const progressPercentage = computed(() => {
  if (!yearlyChallenge.value) return 0
  return yearlyChallenge.value.progress_percentage || 0
})

// Calculate pages read this year
const pagesReadThisYear = computed(() => {
  let totalPages = 0

  booksStore.books.forEach(userBook => {
    const book = userBook.book
    const finishedAt = userBook.finished_at ? new Date(userBook.finished_at) : null

    // Completed books finished this year
    if (userBook.status === 'read' && finishedAt && finishedAt.getFullYear() === currentYear) {
      totalPages += book?.pages || 0
    }
    // Currently reading books - add current progress
    else if (userBook.status === 'currently_reading') {
      totalPages += userBook.current_page || 0
    }
  })

  return totalPages
})

// Handle edit click
const handleEdit = () => {
  if (yearlyChallenge.value) {
    emit('edit', yearlyChallenge.value)
  } else {
    emit('create')
  }
}
</script>

<template>
  <div class="glass rounded-2xl p-6 border border-slate-800">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <Target :size="18" class="text-indigo-400" />
        <h3 class="text-sm font-bold text-white">{{ currentYear }} Reading Challenge</h3>
      </div>
      <button
        @click="handleEdit"
        class="p-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
      >
        <Edit2 v-if="yearlyChallenge" :size="14" />
        <Plus v-else :size="14" />
      </button>
    </div>

    <!-- Challenge Display -->
    <div v-if="yearlyChallenge" class="space-y-4">
      <!-- Progress Numbers -->
      <div class="flex items-baseline gap-2">
        <span class="text-4xl font-black text-white">
          {{ yearlyChallenge.completed_books || 0 }}
        </span>
        <span class="text-2xl font-bold text-slate-500">/</span>
        <span class="text-2xl font-bold text-slate-400">
          {{ yearlyChallenge.target_books || 0 }}
        </span>
        <span class="text-xs text-slate-500 ml-1">books</span>
      </div>

      <!-- Progress Bar -->
      <div class="relative w-full h-3 bg-slate-800 rounded-full overflow-hidden">
        <div
          :style="{ width: `${progressPercentage}%` }"
          class="absolute inset-y-0 left-0 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500"
        />
      </div>

      <!-- Progress Percentage -->
      <div class="flex items-center justify-between text-xs">
        <span class="text-slate-500">{{ progressPercentage.toFixed(0) }}% complete</span>
        <div v-if="yearlyChallenge.is_completed" class="flex items-center gap-1 text-green-400">
          <TrendingUp :size="12" />
          <span class="font-semibold">Completed!</span>
        </div>
        <span v-else class="text-slate-500">
          {{ (yearlyChallenge.target_books || 0) - (yearlyChallenge.completed_books || 0) }} to go
        </span>
      </div>

      <!-- Pages Read This Year -->
      <div class="flex items-center gap-2 pt-3 mt-3 border-t border-slate-800/50">
        <BookOpen :size="14" class="text-indigo-400" />
        <span class="text-xs text-slate-400">
          <span class="font-bold text-white">{{ pagesReadThisYear.toLocaleString() }}</span> pages read this year
        </span>
      </div>

      <!-- Challenge Title (if custom) -->
      <p v-if="yearlyChallenge.title && yearlyChallenge.title !== `${currentYear} Reading Challenge`" class="text-xs text-slate-400 italic mt-2">
        "{{ yearlyChallenge.title }}"
      </p>
    </div>

    <!-- No Challenge State -->
    <div v-else class="text-center py-6">
      <div class="p-4 rounded-full bg-slate-800/50 w-fit mx-auto mb-3">
        <Target :size="24" class="text-slate-600" />
      </div>
      <p class="text-sm text-slate-500 mb-3">No reading challenge set for {{ currentYear }}</p>
      <button
        @click="handleEdit"
        class="px-4 py-2 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white text-xs font-semibold transition-colors"
      >
        Create Challenge
      </button>
    </div>
  </div>
</template>
