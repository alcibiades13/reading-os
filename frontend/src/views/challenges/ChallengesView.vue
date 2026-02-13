<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChallengesStore } from '@/stores/challengesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Target, Plus, Calendar, TrendingUp, Award, Edit, Trash2, Play, Pause, BookOpen, Trophy } from 'lucide-vue-next'

const challengesStore = useChallengesStore()
const booksStore = useUserBooksStore()

const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)
const selectedYear = ref(new Date().getFullYear())

// New challenge form
const newChallenge = ref({
  title: '',
  description: '',
  target_books: 12,
  start_date: new Date().toISOString().split('T')[0],
  end_date: new Date(new Date().getFullYear(), 11, 31).toISOString().split('T')[0],
  min_pages: null,
  is_active: true,
  is_public: false,
})

onMounted(async () => {
  await challengesStore.fetchChallenges()
})

const currentYear = new Date().getFullYear()

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

const activeChallenges = computed(() => challengesStore.activeChallenges)
const completedChallenges = computed(() => challengesStore.completedChallenges)

const years = computed(() => {
  if (!Array.isArray(challengesStore.challenges)) return []
  const years = new Set()
  challengesStore.challenges.forEach(c => {
    years.add(new Date(c.start_date).getFullYear())
  })
  return Array.from(years).sort((a, b) => b - a)
})

const handleCreateChallenge = async () => {
  const result = await challengesStore.createChallenge(newChallenge.value)
  if (result.success) {
    isCreateDialogOpen.value = false
    resetForm()
  }
}

const resetForm = () => {
  newChallenge.value = {
    title: '',
    description: '',
    target_books: 12,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(new Date().getFullYear(), 11, 31).toISOString().split('T')[0],
    min_pages: null,
    is_active: true,
    is_public: false,
  }
}

// Edit challenge
const editingChallenge = ref(null)
const editForm = ref({})

const openEditDialog = (challenge) => {
  editingChallenge.value = challenge
  editForm.value = {
    title: challenge.title,
    description: challenge.description || '',
    target_books: challenge.target_books,
    start_date: challenge.start_date,
    end_date: challenge.end_date,
    min_pages: challenge.min_pages,
    is_active: challenge.is_active,
    is_public: challenge.is_public,
  }
  isEditDialogOpen.value = true
}

const handleEditChallenge = async () => {
  if (!editingChallenge.value) return
  const result = await challengesStore.updateChallenge(editingChallenge.value.id, editForm.value)
  if (result.success) {
    isEditDialogOpen.value = false
    editingChallenge.value = null
  }
}

const toggleActive = async (challenge) => {
  await challengesStore.updateChallenge(challenge.id, {
    is_active: !challenge.is_active,
  })
}

const deleteChallenge = async (challenge) => {
  if (confirm(`Delete "${challenge.title}"?`)) {
    await challengesStore.deleteChallenge(challenge.id)
  }
}

const refreshProgress = async (challenge) => {
  await challengesStore.updateProgress(challenge.id)
}

const getProgressColor = (percentage) => {
  if (percentage >= 100) return 'text-green-400'
  if (percentage >= 75) return 'text-blue-400'
  if (percentage >= 50) return 'text-yellow-400'
  return 'text-orange-400'
}

const getProgressBg = (percentage) => {
  if (percentage >= 100) return 'bg-green-500'
  if (percentage >= 75) return 'bg-blue-500'
  if (percentage >= 50) return 'bg-yellow-500'
  return 'bg-orange-500'
}

const formatDateShort = (date) => {
  return new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  })
}
</script>

<template>
  <div class="animate-in fade-in duration-700">

    <!-- ==================== MOBILE HEADER ==================== -->
    <header class="lg:hidden sticky top-0 z-30 border-b border-white/5 bg-slate-900/80 backdrop-blur-xl">
      <div class="px-4 pt-4 pb-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
              <Target :size="20" class="text-white" />
            </div>
            <div>
              <h1 class="text-lg font-black text-white">Challenges</h1>
              <p class="text-[10px] text-slate-500 uppercase tracking-wider">{{ activeChallenges.length }} active</p>
            </div>
          </div>
          <Dialog v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <button class="p-2.5 rounded-xl bg-indigo-500 text-white active:bg-indigo-600 transition-colors">
                <Plus :size="18" />
              </button>
            </DialogTrigger>
            <DialogContent class="max-w-[calc(100vw-2rem)] sm:max-w-2xl max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Reading Challenge</DialogTitle>
              </DialogHeader>
              <form @submit.prevent="handleCreateChallenge" class="space-y-4">
                <div class="space-y-2">
                  <Label for="m-title">Challenge Title *</Label>
                  <Input
                    id="m-title"
                    v-model="newChallenge.title"
                    placeholder="2026 Reading Challenge"
                    required
                  />
                </div>

                <div class="space-y-2">
                  <Label for="m-description">Description</Label>
                  <Textarea
                    id="m-description"
                    v-model="newChallenge.description"
                    placeholder="Describe your reading goal..."
                    rows="3"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label for="m-target">Target Books *</Label>
                    <Input
                      id="m-target"
                      v-model.number="newChallenge.target_books"
                      type="number"
                      min="1"
                      required
                    />
                  </div>

                  <div class="space-y-2">
                    <Label for="m-min-pages">Min Pages</Label>
                    <Input
                      id="m-min-pages"
                      v-model.number="newChallenge.min_pages"
                      type="number"
                      placeholder="200"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label for="m-start-date">Start Date *</Label>
                    <Input
                      id="m-start-date"
                      v-model="newChallenge.start_date"
                      type="date"
                      required
                    />
                  </div>

                  <div class="space-y-2">
                    <Label for="m-end-date">End Date *</Label>
                    <Input
                      id="m-end-date"
                      v-model="newChallenge.end_date"
                      type="date"
                      required
                    />
                  </div>
                </div>

                <div class="flex gap-4">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="newChallenge.is_active"
                      type="checkbox"
                      class="rounded"
                    />
                    <span class="text-sm">Active</span>
                  </label>

                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="newChallenge.is_public"
                      type="checkbox"
                      class="rounded"
                    />
                    <span class="text-sm">Public</span>
                  </label>
                </div>

                <div class="flex justify-end gap-2 pt-2">
                  <button type="button" @click="isCreateDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-slate-400 hover:text-white transition-colors">
                    Cancel
                  </button>
                  <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">
                    Create Challenge
                  </button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </header>

    <!-- Page Container -->
    <div class="w-full max-w-[1600px] mx-auto px-4 lg:px-6 py-4 lg:py-12">

      <!-- Desktop Header -->
      <header class="mb-12 hidden lg:block">
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <Target :size="24" class="text-amber-400" />
              </div>
              <span class="text-page-meta font-bold text-amber-400 uppercase tracking-[0.3em]">Reading Goals</span>
            </div>
            <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
              Reading <span class="text-amber-500">Challenges</span>
            </h1>
            <p class="text-page-subtitle text-slate-400 leading-relaxed max-w-2xl">
              Set reading goals and track your progress throughout the year.
            </p>
          </div>

          <Dialog v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <button class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-400 transition-all flex items-center gap-2">
                <Plus :size="18" />
                New Challenge
              </button>
            </DialogTrigger>
            <DialogContent class="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Reading Challenge</DialogTitle>
              </DialogHeader>
              <form @submit.prevent="handleCreateChallenge" class="space-y-4">
                <div class="space-y-2">
                  <Label for="title">Challenge Title *</Label>
                  <Input
                    id="title"
                    v-model="newChallenge.title"
                    placeholder="2026 Reading Challenge"
                    required
                  />
                </div>

                <div class="space-y-2">
                  <Label for="description">Description</Label>
                  <Textarea
                    id="description"
                    v-model="newChallenge.description"
                    placeholder="Describe your reading goal..."
                    rows="3"
                  />
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label for="target">Target Books *</Label>
                    <Input
                      id="target"
                      v-model.number="newChallenge.target_books"
                      type="number"
                      min="1"
                      required
                    />
                  </div>

                  <div class="space-y-2">
                    <Label for="min-pages">Min Pages (optional)</Label>
                    <Input
                      id="min-pages"
                      v-model.number="newChallenge.min_pages"
                      type="number"
                      placeholder="200"
                    />
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label for="start-date">Start Date *</Label>
                    <Input
                      id="start-date"
                      v-model="newChallenge.start_date"
                      type="date"
                      required
                    />
                  </div>

                  <div class="space-y-2">
                    <Label for="end-date">End Date *</Label>
                    <Input
                      id="end-date"
                      v-model="newChallenge.end_date"
                      type="date"
                      required
                    />
                  </div>
                </div>

                <div class="flex gap-4">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="newChallenge.is_active"
                      type="checkbox"
                      class="rounded"
                    />
                    <span class="text-sm">Active</span>
                  </label>

                  <label class="flex items-center gap-2 cursor-pointer">
                    <input
                      v-model="newChallenge.is_public"
                      type="checkbox"
                      class="rounded"
                    />
                    <span class="text-sm">Public</span>
                  </label>
                </div>

                <div class="flex justify-end gap-2">
                  <button type="button" @click="isCreateDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-slate-400 hover:text-white transition-colors border border-slate-700">
                    Cancel
                  </button>
                  <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">
                    Create Challenge
                  </button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <!-- Active Challenges -->
      <section v-if="activeChallenges.length > 0" class="mb-8 lg:mb-12">
        <div class="flex items-center justify-between mb-4 lg:mb-6">
          <h2 class="text-base lg:text-2xl font-bold text-white flex items-center gap-2">
            <Play :size="18" class="text-green-400" />
            Active Challenges
          </h2>
          <span class="text-xs font-bold text-slate-500 bg-white/5 px-2.5 py-1 rounded-full">{{ activeChallenges.length }}</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
          <div
            v-for="challenge in activeChallenges"
            :key="challenge.id"
            class="rounded-2xl border border-slate-800 bg-slate-900/50 p-4 sm:p-5 hover:border-slate-700 transition-all"
          >
            <!-- Title & Status -->
            <div class="flex items-start justify-between mb-3">
              <div class="flex-1 min-w-0">
                <h3 class="text-sm sm:text-base font-bold text-white truncate">{{ challenge.title }}</h3>
                <p v-if="challenge.description" class="text-xs text-slate-500 mt-1 line-clamp-2">{{ challenge.description }}</p>
              </div>
              <span
                :class="[
                  'text-[10px] font-bold px-2 py-0.5 rounded-full ml-2 flex-shrink-0',
                  challenge.is_completed
                    ? 'bg-green-500/10 text-green-400 border border-green-500/20'
                    : 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                ]"
              >
                {{ challenge.is_completed ? 'Done' : 'In Progress' }}
              </span>
            </div>

            <!-- Progress -->
            <div class="mb-4">
              <div class="flex items-baseline justify-between mb-2">
                <span class="text-2xl sm:text-3xl font-black" :class="getProgressColor(challenge.progress_percentage || 0)">
                  {{ challenge.completed_books || 0 }}
                </span>
                <span class="text-xs text-slate-500">/ {{ challenge.target_books || 0 }} books</span>
              </div>
              <div class="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  :class="['h-full rounded-full transition-all duration-500', getProgressBg(challenge.progress_percentage || 0)]"
                  :style="{ width: Math.min(challenge.progress_percentage || 0, 100) + '%' }"
                />
              </div>
              <div class="flex justify-between mt-1.5 text-[10px] text-slate-500">
                <span>{{ Math.round(challenge.progress_percentage || 0) }}%</span>
                <span v-if="(challenge.target_books || 0) - (challenge.completed_books || 0) > 0">
                  {{ (challenge.target_books || 0) - (challenge.completed_books || 0) }} to go
                </span>
              </div>
            </div>

            <!-- Pages Read -->
            <div class="flex items-center gap-2 py-2.5 border-t border-slate-800">
              <BookOpen :size="14" class="text-indigo-400" />
              <span class="text-xs text-slate-400">
                <span class="font-bold text-white">{{ pagesReadThisYear.toLocaleString() }}</span> pages in {{ currentYear }}
              </span>
            </div>

            <!-- Dates -->
            <div class="flex items-center gap-2 text-xs text-slate-500 mt-1">
              <Calendar :size="12" />
              <span>{{ formatDateShort(challenge.start_date) }} — {{ formatDateShort(challenge.end_date) }}</span>
            </div>

            <!-- Min Pages -->
            <div v-if="challenge.min_pages" class="text-[10px] text-slate-500 mt-1">
              Min {{ challenge.min_pages }} pages per book
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-between mt-4 pt-3 border-t border-slate-800">
              <div class="flex gap-1">
                <button @click="toggleActive(challenge)" class="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all" title="Pause">
                  <Pause :size="14" />
                </button>
                <button @click="refreshProgress(challenge)" class="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all" title="Refresh">
                  <TrendingUp :size="14" />
                </button>
              </div>
              <div class="flex gap-1">
                <button @click="openEditDialog(challenge)" class="p-2 rounded-lg text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-all" title="Edit">
                  <Edit :size="14" />
                </button>
                <button @click="deleteChallenge(challenge)" class="p-2 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/5 transition-all" title="Delete">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Completed Challenges -->
      <section v-if="completedChallenges.length > 0" class="mb-8">
        <div class="flex items-center justify-between mb-4 lg:mb-6">
          <h2 class="text-base lg:text-2xl font-bold text-white flex items-center gap-2">
            <Award :size="18" class="text-yellow-400" />
            Completed
          </h2>
          <span class="text-xs font-bold text-slate-500 bg-white/5 px-2.5 py-1 rounded-full">{{ completedChallenges.length }}</span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 lg:gap-4">
          <div
            v-for="challenge in completedChallenges"
            :key="challenge.id"
            class="rounded-2xl border border-green-500/10 bg-gradient-to-br from-green-950/30 to-emerald-950/30 p-4 hover:border-green-500/20 transition-all"
          >
            <Trophy :size="24" class="text-yellow-500 mb-2" />
            <h3 class="font-bold text-white text-sm mb-1 truncate">{{ challenge.title }}</h3>
            <p class="text-lg sm:text-xl font-black text-green-400">
              {{ challenge.completed_books || 0 }}/{{ challenge.target_books || 0 }}
            </p>
            <p class="text-[10px] text-slate-500 mt-2">
              Completed {{ formatDateShort(challenge.end_date) }}
            </p>
          </div>
        </div>
      </section>

      <!-- Edit Challenge Dialog -->
      <Dialog v-model:open="isEditDialogOpen">
        <DialogContent class="max-w-[calc(100vw-2rem)] sm:max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Challenge</DialogTitle>
          </DialogHeader>
          <form @submit.prevent="handleEditChallenge" class="space-y-4">
            <div class="space-y-2">
              <Label for="edit-title">Challenge Title *</Label>
              <Input
                id="edit-title"
                v-model="editForm.title"
                placeholder="2026 Reading Challenge"
                required
              />
            </div>

            <div class="space-y-2">
              <Label for="edit-description">Description</Label>
              <Textarea
                id="edit-description"
                v-model="editForm.description"
                placeholder="Describe your reading goal..."
                rows="3"
              />
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="edit-target">Target Books *</Label>
                <Input
                  id="edit-target"
                  v-model.number="editForm.target_books"
                  type="number"
                  min="1"
                  required
                />
              </div>

              <div class="space-y-2">
                <Label for="edit-min-pages">Min Pages</Label>
                <Input
                  id="edit-min-pages"
                  v-model.number="editForm.min_pages"
                  type="number"
                  placeholder="200"
                />
              </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-2">
                <Label for="edit-start-date">Start Date *</Label>
                <Input
                  id="edit-start-date"
                  v-model="editForm.start_date"
                  type="date"
                  required
                />
              </div>

              <div class="space-y-2">
                <Label for="edit-end-date">End Date *</Label>
                <Input
                  id="edit-end-date"
                  v-model="editForm.end_date"
                  type="date"
                  required
                />
              </div>
            </div>

            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="editForm.is_active"
                  type="checkbox"
                  class="rounded"
                />
                <span class="text-sm">Active</span>
              </label>

              <label class="flex items-center gap-2 cursor-pointer">
                <input
                  v-model="editForm.is_public"
                  type="checkbox"
                  class="rounded"
                />
                <span class="text-sm">Public</span>
              </label>
            </div>

            <div class="flex justify-end gap-2 pt-2">
              <button type="button" @click="isEditDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-slate-400 hover:text-white transition-colors">
                Cancel
              </button>
              <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">
                Save Changes
              </button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <!-- Empty State -->
      <div v-if="activeChallenges.length === 0 && completedChallenges.length === 0" class="text-center py-16 lg:py-24">
        <div class="w-20 h-20 rounded-2xl bg-slate-900/50 border border-slate-800 flex items-center justify-center mx-auto mb-6">
          <Target :size="40" class="text-slate-700" />
        </div>
        <h3 class="text-lg font-bold text-white mb-2">No challenges yet</h3>
        <p class="text-sm text-slate-500 mb-6 max-w-xs mx-auto">
          Set a reading goal to stay motivated and track your progress!
        </p>
        <button
          @click="isCreateDialogOpen = true"
          class="px-6 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-all inline-flex items-center gap-2"
        >
          <Plus :size="16" />
          Create Your First Challenge
        </button>
      </div>
    </div>
  </div>
</template>
