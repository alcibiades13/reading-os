<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useChallengesStore } from '@/stores/challengesStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Target, Plus, Calendar, TrendingUp, Award, Edit, Trash2, Play, Pause,
  BookOpen, Trophy, ChevronDown, ChevronUp, GripVertical, X, Search, ListTodo,
} from 'lucide-vue-next'
import { challengesAPI, schedulesAPI } from '@/services/api'
import draggable from 'vuedraggable'

const challengesStore = useChallengesStore()
const booksStore = useUserBooksStore()

// ===== TABS =====
const activeTab = ref('challenges')

function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'schedule' && schedules.value.length === 0 && !scheduleLoading.value) {
    fetchSchedules()
  }
}

// ===== CHALLENGE STATE =====
const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)

const CHALLENGE_TYPES = [
  { value: 'books', label: 'Books Read' },
  { value: 'vocabulary_words', label: 'Vocabulary Words' },
  { value: 'quotes', label: 'Quotes Collected' },
  { value: 'manuscript_words', label: 'Manuscript Words' },
]

const getTargetLabel = (type) => {
  if (type === 'vocabulary_words' || type === 'manuscript_words') return 'Target Words'
  if (type === 'quotes') return 'Target Quotes'
  return 'Target Books'
}

const getUnitLabel = (type) => {
  if (type === 'vocabulary_words' || type === 'manuscript_words') return 'words'
  if (type === 'quotes') return 'quotes'
  return 'books'
}

const newChallenge = ref({
  title: '',
  description: '',
  challenge_type: 'books',
  target_books: 12,
  start_date: new Date().toISOString().split('T')[0],
  end_date: new Date(new Date().getFullYear(), 11, 31).toISOString().split('T')[0],
  min_pages: null,
  is_active: true,
  is_public: false,
})

onMounted(async () => {
  await challengesStore.fetchChallenges()
  if (booksStore.books.length === 0) {
    await booksStore.fetchBooks()
  }
})

const currentYear = new Date().getFullYear()

const activeChallenges = computed(() => challengesStore.activeChallenges)
const completedChallenges = computed(() => challengesStore.completedChallenges)

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
    challenge_type: 'books',
    target_books: 12,
    start_date: new Date().toISOString().split('T')[0],
    end_date: new Date(new Date().getFullYear(), 11, 31).toISOString().split('T')[0],
    min_pages: null,
    is_active: true,
    is_public: false,
  }
}

const editingChallenge = ref(null)
const editForm = ref({})

const openEditDialog = (challenge) => {
  editingChallenge.value = challenge
  editForm.value = {
    title: challenge.title,
    description: challenge.description || '',
    challenge_type: challenge.challenge_type || 'books',
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
  await challengesStore.updateChallenge(challenge.id, { is_active: !challenge.is_active })
}

const deleteChallenge = async (challenge) => {
  if (confirm(`Delete "${challenge.title}"?`)) {
    await challengesStore.deleteChallenge(challenge.id)
  }
}

const refreshProgress = async (challenge) => {
  await challengesStore.updateProgress(challenge.id)
}

const getProgressColor = (pct) => {
  if (pct >= 100) return 'text-green-400'
  if (pct >= 75) return 'text-blue-400'
  if (pct >= 50) return 'text-yellow-400'
  return 'text-orange-400'
}

const getProgressBg = (pct) => {
  if (pct >= 100) return 'bg-green-500'
  if (pct >= 75) return 'bg-blue-500'
  if (pct >= 50) return 'bg-yellow-500'
  return 'bg-orange-500'
}

const formatDateShort = (date) => {
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Challenge item lists (books or vocabulary words)
const expandedChallenges = ref({})
const challengeItems = ref({})   // { [id]: { type: 'books'|'vocabulary', items: [] } }
const loadingBooks = ref({})

const toggleBooks = async (challenge) => {
  const id = challenge.id
  if (expandedChallenges.value[id]) {
    expandedChallenges.value[id] = false
    return
  }
  expandedChallenges.value[id] = true
  if (challengeItems.value[id]) return
  loadingBooks.value[id] = true
  try {
    const res = await challengesAPI.progressDetails(id)
    challengeItems.value[id] = {
      type: res.data.item_type,
      items: res.data.qualifying_items,
    }
  } finally {
    loadingBooks.value[id] = false
  }
}

const MASTERY_LABEL = { new: 'New', learning: 'Learning', mastered: 'Mastered' }
const MASTERY_COLOR = { new: 'text-zinc-400', learning: 'text-amber-400', mastered: 'text-green-400' }

// ===== SCHEDULE STATE =====
const schedules = ref([])
const selectedScheduleId = ref(null)
const scheduleLoading = ref(false)
const bookSearch = ref('')
const newScheduleTitle = ref('')
const isCreatingSchedule = ref(false)
const editingSectionId = ref(null)
const editingSectionTitle = ref('')
const activeSectionId = ref(null)
const localSections = ref([])

const bookById = computed(() => {
  const map = {}
  booksStore.books.forEach(ub => { if (ub.book) map[ub.book.id] = ub.book })
  return map
})

const libraryBooks = computed(() => {
  return booksStore.books
    .filter(ub => ub.book)
    .map(ub => ub.book)
    .filter(book => {
      if (!bookSearch.value.trim()) return true
      const q = bookSearch.value.toLowerCase()
      return (
        book.title?.toLowerCase().includes(q) ||
        book.authors?.some(a => (a.name || a)?.toString().toLowerCase().includes(q))
      )
    })
})

const activeSection = computed(() =>
  localSections.value.find(s => s.id === activeSectionId.value) || localSections.value[0] || null
)

const getAuthorNames = (book) => {
  if (!book?.authors?.length) return ''
  return book.authors.map(a => typeof a === 'string' ? a : a.name).filter(Boolean).join(', ')
}

function buildLocalSections(schedule) {
  localSections.value = (schedule.sections || []).map(sec => ({
    id: sec.id,
    title: sec.title,
    order: sec.order,
    bookItems: (sec.book_ids || []).map(id => bookById.value[id]).filter(Boolean),
  }))
  if (localSections.value.length && !activeSectionId.value) {
    activeSectionId.value = localSections.value[0].id
  }
}

async function fetchSchedules() {
  scheduleLoading.value = true
  try {
    const res = await schedulesAPI.list()
    schedules.value = Array.isArray(res.data) ? res.data : (res.data.results || [])
    if (schedules.value.length) {
      const first = schedules.value[0]
      selectedScheduleId.value = first.id
      buildLocalSections(first)
    }
  } finally {
    scheduleLoading.value = false
  }
}

function selectSchedule(schedule) {
  selectedScheduleId.value = schedule.id
  activeSectionId.value = null
  buildLocalSections(schedule)
}

async function createSchedule() {
  if (!newScheduleTitle.value.trim()) return
  const res = await schedulesAPI.create({ title: newScheduleTitle.value.trim() })
  schedules.value.push(res.data)
  selectSchedule(res.data)
  newScheduleTitle.value = ''
  isCreatingSchedule.value = false
}

async function deleteSchedule(schedule) {
  if (!confirm(`Delete schedule "${schedule.title}"?`)) return
  await schedulesAPI.delete(schedule.id)
  schedules.value = schedules.value.filter(s => s.id !== schedule.id)
  if (selectedScheduleId.value === schedule.id) {
    selectedScheduleId.value = null
    localSections.value = []
    activeSectionId.value = null
    if (schedules.value.length) selectSchedule(schedules.value[0])
  }
}

async function addSection() {
  if (!selectedScheduleId.value) return
  const res = await schedulesAPI.addSection(selectedScheduleId.value, { title: 'New Section' })
  const newSec = { id: res.data.id, title: res.data.title, order: res.data.order, bookItems: [] }
  localSections.value.push(newSec)
  activeSectionId.value = newSec.id
  editingSectionId.value = newSec.id
  editingSectionTitle.value = newSec.title
  await nextTick()
  document.querySelector(`input[data-section-id="${newSec.id}"]`)?.focus()
}

async function deleteSection(section) {
  if (!confirm(`Delete section "${section.title}"?`)) return
  await schedulesAPI.deleteSection(selectedScheduleId.value, section.id)
  localSections.value = localSections.value.filter(s => s.id !== section.id)
  if (activeSectionId.value === section.id) {
    activeSectionId.value = localSections.value[0]?.id || null
  }
}

async function startEditSection(id, title) {
  editingSectionId.value = id
  editingSectionTitle.value = title
  await nextTick()
  document.querySelector(`input[data-section-id="${id}"]`)?.focus()
}

async function saveSectionTitle(section) {
  const t = editingSectionTitle.value.trim()
  if (!t) { editingSectionId.value = null; return }
  section.title = t
  editingSectionId.value = null
  await schedulesAPI.updateSection(selectedScheduleId.value, section.id, { title: t })
}

async function saveSectionBooks(section) {
  await schedulesAPI.updateSection(selectedScheduleId.value, section.id, {
    book_ids: section.bookItems.map(b => b.id),
  })
}

function addBookToSection(book) {
  const sec = activeSection.value
  if (!sec) return
  if (sec.bookItems.find(b => b.id === book.id)) return
  sec.bookItems.push(book)
  saveSectionBooks(sec)
}

function removeBookFromSection(section, index) {
  section.bookItems.splice(index, 1)
  saveSectionBooks(section)
}

function onSectionBooksChange(section, event) {
  // Deduplicate when a cloned book from library is dropped into a section that already has it
  if (event?.added) {
    const addedId = event.added.element.id
    const dupes = section.bookItems.filter(b => b.id === addedId)
    if (dupes.length > 1) {
      section.bookItems.splice(event.added.newIndex, 1)
      return
    }
  }
  saveSectionBooks(section)
}

async function onSectionsReorder() {
  for (let i = 0; i < localSections.value.length; i++) {
    const s = localSections.value[i]
    if (s.order !== i) {
      s.order = i
      await schedulesAPI.updateSection(selectedScheduleId.value, s.id, { order: i })
    }
  }
}

const isBookInSchedule = (bookId) => {
  return localSections.value.some(sec => sec.bookItems.some(b => b.id === bookId))
}
</script>

<template>
  <div class="animate-in fade-in duration-700">

    <!-- ==================== MOBILE HEADER ==================== -->
    <header class="lg:hidden sticky top-0 z-30 border-b border-white/5 bg-zinc-900/80 backdrop-blur-xl">
      <div class="px-4 pt-4 pb-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
              <Target :size="20" class="text-white" />
            </div>
            <div>
              <h1 class="text-lg font-black text-white">Reading Plans</h1>
              <p class="text-[10px] text-zinc-500 uppercase tracking-wider">{{ activeChallenges.length }} active</p>
            </div>
          </div>
          <Dialog v-if="activeTab === 'challenges'" v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <button class="p-2.5 rounded-xl bg-indigo-500 text-white active:bg-indigo-600 transition-colors">
                <Plus :size="18" />
              </button>
            </DialogTrigger>
            <DialogContent class="max-w-[calc(100vw-2rem)] sm:max-w-2xl max-h-[85vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Challenge</DialogTitle>
              </DialogHeader>
              <form @submit.prevent="handleCreateChallenge" class="space-y-4">
                <div class="space-y-2">
                  <Label>Challenge Title *</Label>
                  <Input v-model="newChallenge.title" placeholder="2026 Reading Challenge" required />
                </div>
                <div class="space-y-2">
                  <Label>Description</Label>
                  <Textarea v-model="newChallenge.description" placeholder="Describe your goal..." rows="2" />
                </div>
                <div class="space-y-2">
                  <Label>Challenge Type</Label>
                  <select v-model="newChallenge.challenge_type" class="flex h-10 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option v-for="opt in CHALLENGE_TYPES" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label>{{ getTargetLabel(newChallenge.challenge_type) }} *</Label>
                    <Input v-model.number="newChallenge.target_books" type="number" min="1" required />
                  </div>
                  <div v-if="newChallenge.challenge_type === 'books'" class="space-y-2">
                    <Label>Min Pages</Label>
                    <Input v-model.number="newChallenge.min_pages" type="number" placeholder="200" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label>Start Date *</Label>
                    <Input v-model="newChallenge.start_date" type="date" required />
                  </div>
                  <div class="space-y-2">
                    <Label>End Date *</Label>
                    <Input v-model="newChallenge.end_date" type="date" required />
                  </div>
                </div>
                <div class="flex gap-4">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="newChallenge.is_active" type="checkbox" class="rounded" />
                    <span class="text-sm">Active</span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="newChallenge.is_public" type="checkbox" class="rounded" />
                    <span class="text-sm">Public</span>
                  </label>
                </div>
                <div class="flex justify-end gap-2 pt-2">
                  <button type="button" @click="isCreateDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-zinc-400 hover:text-white transition-colors">Cancel</button>
                  <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">Create</button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <!-- Mobile Tab Switcher -->
        <div class="flex mt-3 p-1 rounded-xl bg-zinc-800/50 gap-1">
          <button
            @click="switchTab('challenges')"
            :class="['flex-1 py-1.5 rounded-lg text-xs font-bold transition-all', activeTab === 'challenges' ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300']"
          >
            <Target :size="12" class="inline mr-1" />Challenges
          </button>
          <button
            @click="switchTab('schedule')"
            :class="['flex-1 py-1.5 rounded-lg text-xs font-bold transition-all', activeTab === 'schedule' ? 'bg-white/10 text-white' : 'text-zinc-500 hover:text-zinc-300']"
          >
            <ListTodo :size="12" class="inline mr-1" />Schedule
          </button>
        </div>
      </div>
    </header>

    <!-- Page Container -->
    <div class="w-full max-w-[1600px] mx-auto px-4 lg:px-6 py-4 lg:py-12">

      <!-- Desktop Header -->
      <header class="mb-8 hidden lg:block">
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-3 mb-4">
              <div class="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
                <Target :size="24" class="text-amber-400" />
              </div>
              <span class="text-page-meta font-bold text-amber-400 uppercase tracking-[0.3em]">Goals & Schedules</span>
            </div>
            <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
              Reading <span class="text-amber-500">Plans</span>
            </h1>
          </div>

          <Dialog v-if="activeTab === 'challenges'" v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <button class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-400 transition-all flex items-center gap-2">
                <Plus :size="18" />
                New Challenge
              </button>
            </DialogTrigger>
            <DialogContent class="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create Challenge</DialogTitle>
              </DialogHeader>
              <form @submit.prevent="handleCreateChallenge" class="space-y-4">
                <div class="space-y-2">
                  <Label>Challenge Title *</Label>
                  <Input v-model="newChallenge.title" placeholder="2026 Reading Challenge" required />
                </div>
                <div class="space-y-2">
                  <Label>Description</Label>
                  <Textarea v-model="newChallenge.description" placeholder="Describe your goal..." rows="3" />
                </div>
                <div class="space-y-2">
                  <Label>Challenge Type</Label>
                  <select v-model="newChallenge.challenge_type" class="flex h-10 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option v-for="opt in CHALLENGE_TYPES" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                  </select>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label>{{ getTargetLabel(newChallenge.challenge_type) }} *</Label>
                    <Input v-model.number="newChallenge.target_books" type="number" min="1" required />
                  </div>
                  <div v-if="newChallenge.challenge_type === 'books'" class="space-y-2">
                    <Label>Min Pages (optional)</Label>
                    <Input v-model.number="newChallenge.min_pages" type="number" placeholder="200" />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-2">
                    <Label>Start Date *</Label>
                    <Input v-model="newChallenge.start_date" type="date" required />
                  </div>
                  <div class="space-y-2">
                    <Label>End Date *</Label>
                    <Input v-model="newChallenge.end_date" type="date" required />
                  </div>
                </div>
                <div class="flex gap-4">
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="newChallenge.is_active" type="checkbox" class="rounded" />
                    <span class="text-sm">Active</span>
                  </label>
                  <label class="flex items-center gap-2 cursor-pointer">
                    <input v-model="newChallenge.is_public" type="checkbox" class="rounded" />
                    <span class="text-sm">Public</span>
                  </label>
                </div>
                <div class="flex justify-end gap-2">
                  <button type="button" @click="isCreateDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-zinc-400 hover:text-white transition-colors border border-zinc-700">Cancel</button>
                  <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">Create Challenge</button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <!-- Desktop Tab Switcher -->
        <div class="flex gap-1 p-1 rounded-xl bg-zinc-900/50 border border-zinc-800 w-fit">
          <button
            @click="switchTab('challenges')"
            :class="['px-5 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2', activeTab === 'challenges' ? 'bg-indigo-500 text-white shadow-lg' : 'text-zinc-400 hover:text-white hover:bg-white/5']"
          >
            <Target :size="15" />Challenges
          </button>
          <button
            @click="switchTab('schedule')"
            :class="['px-5 py-2 rounded-lg text-sm font-bold transition-all flex items-center gap-2', activeTab === 'schedule' ? 'bg-indigo-500 text-white shadow-lg' : 'text-zinc-400 hover:text-white hover:bg-white/5']"
          >
            <ListTodo :size="15" />Reading Schedule
          </button>
        </div>
      </header>

      <!-- ==================== CHALLENGES TAB ==================== -->
      <div v-show="activeTab === 'challenges'">

        <!-- Active Challenges -->
        <section v-if="activeChallenges.length > 0" class="mb-8 lg:mb-12">
          <div class="flex items-center justify-between mb-4 lg:mb-6">
            <h2 class="text-base lg:text-2xl font-bold text-white flex items-center gap-2">
              <Play :size="18" class="text-green-400" />
              Active Challenges
            </h2>
            <span class="text-xs font-bold text-zinc-500 bg-white/5 px-2.5 py-1 rounded-full">{{ activeChallenges.length }}</span>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 lg:gap-6">
            <div
              v-for="challenge in activeChallenges"
              :key="challenge.id"
              class="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 sm:p-5 hover:border-zinc-700 transition-all"
            >
              <!-- Title & Status -->
              <div class="flex items-start justify-between mb-3">
                <div class="flex-1 min-w-0">
                  <h3 class="text-sm sm:text-base font-bold text-white truncate">{{ challenge.title }}</h3>
                  <p v-if="challenge.description" class="text-xs text-zinc-500 mt-1 line-clamp-2">{{ challenge.description }}</p>
                  <span class="text-[10px] font-medium text-zinc-600 mt-0.5 block">
                    {{ CHALLENGE_TYPES.find(t => t.value === challenge.challenge_type)?.label || 'Books Read' }}
                  </span>
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
              <div class="mb-3">
                <div class="flex items-baseline justify-between mb-2">
                  <span class="text-2xl sm:text-3xl font-black" :class="getProgressColor(challenge.progress_percentage || 0)">
                    {{ challenge.completed_books || 0 }}
                  </span>
                  <span class="text-xs text-zinc-500">/ {{ challenge.target_books || 0 }} {{ getUnitLabel(challenge.challenge_type) }}</span>
                </div>
                <div class="w-full h-2 rounded-full bg-zinc-800 overflow-hidden">
                  <div
                    :class="['h-full rounded-full transition-all duration-500', getProgressBg(challenge.progress_percentage || 0)]"
                    :style="{ width: Math.min(challenge.progress_percentage || 0, 100) + '%' }"
                  />
                </div>
                <div class="flex justify-between mt-1.5 text-[10px] text-zinc-500">
                  <span>{{ Math.round(challenge.progress_percentage || 0) }}%</span>
                  <span v-if="(challenge.target_books || 0) - (challenge.completed_books || 0) > 0">
                    {{ (challenge.target_books || 0) - (challenge.completed_books || 0) }} to go
                  </span>
                </div>
              </div>

              <!-- Toggle (books or vocabulary) -->
              <template v-if="!challenge.challenge_type || challenge.challenge_type === 'books' || challenge.challenge_type === 'vocabulary_words'">
                <button
                  @click="toggleBooks(challenge)"
                  class="w-full flex items-center justify-between py-2.5 border-t border-zinc-800 text-xs text-zinc-400 hover:text-white transition-colors"
                >
                  <div class="flex items-center gap-2">
                    <BookOpen :size="14" class="text-indigo-400" />
                    <span>{{ challenge.completed_books || 0 }} {{ getUnitLabel(challenge.challenge_type) }}</span>
                  </div>
                  <ChevronUp v-if="expandedChallenges[challenge.id]" :size="14" />
                  <ChevronDown v-else :size="14" />
                </button>

                <div v-if="expandedChallenges[challenge.id]" class="border-t border-zinc-800/50 pt-2 space-y-1 max-h-48 overflow-y-auto">
                  <div v-if="loadingBooks[challenge.id]" class="text-xs text-zinc-500 py-2 text-center">Loading...</div>
                  <template v-else-if="challengeItems[challenge.id]">

                    <!-- Books list -->
                    <template v-if="challengeItems[challenge.id].type === 'books'">
                      <div
                        v-for="book in challengeItems[challenge.id].items"
                        :key="book.id"
                        class="flex items-center gap-2 py-1 px-1 rounded hover:bg-zinc-800/50 cursor-pointer transition-colors"
                        @click="$router.push(`/books/${book.id}-${book.slug}`)"
                      >
                        <img v-if="book.cover_image" :src="book.cover_image" class="w-6 h-9 object-cover rounded shrink-0" />
                        <div v-else class="w-6 h-9 bg-zinc-800 rounded shrink-0" />
                        <div class="flex-1 min-w-0">
                          <p class="text-xs font-medium text-zinc-200 truncate">{{ book.title }}</p>
                          <p class="text-[10px] text-zinc-500 truncate">{{ book.authors?.join(', ') }}</p>
                        </div>
                        <span class="text-[10px] text-zinc-500 shrink-0">{{ book.finished_at }}</span>
                      </div>
                      <p v-if="!challengeItems[challenge.id].items.length" class="text-xs text-zinc-500 py-2 text-center">No books read yet.</p>
                    </template>

                    <!-- Vocabulary list -->
                    <template v-else-if="challengeItems[challenge.id].type === 'vocabulary'">
                      <div
                        v-for="word in challengeItems[challenge.id].items"
                        :key="word.id"
                        class="flex items-start gap-2 py-1.5 px-1.5 rounded hover:bg-zinc-800/50 transition-colors"
                      >
                        <div class="flex-1 min-w-0">
                          <div class="flex items-center gap-2">
                            <p class="text-xs font-bold text-zinc-200">{{ word.word }}</p>
                            <span :class="['text-[10px] font-medium', MASTERY_COLOR[word.mastery]]">{{ MASTERY_LABEL[word.mastery] }}</span>
                          </div>
                          <p class="text-[10px] text-zinc-500 truncate mt-0.5">{{ word.definition }}</p>
                          <p v-if="word.book_title" class="text-[10px] text-zinc-600 truncate">{{ word.book_title }}</p>
                        </div>
                        <span class="text-[10px] text-zinc-600 shrink-0 mt-0.5">{{ word.created_at }}</span>
                      </div>
                      <p v-if="!challengeItems[challenge.id].items.length" class="text-xs text-zinc-500 py-2 text-center">No words added yet.</p>
                    </template>

                  </template>
                </div>
              </template>

              <!-- Dates -->
              <div class="flex items-center gap-2 text-xs text-zinc-500 mt-3 border-t border-zinc-800 pt-3">
                <Calendar :size="12" />
                <span>{{ formatDateShort(challenge.start_date) }} — {{ formatDateShort(challenge.end_date) }}</span>
              </div>
              <div v-if="challenge.min_pages" class="text-[10px] text-zinc-500 mt-1">
                Min {{ challenge.min_pages }} pages per book
              </div>

              <!-- Actions -->
              <div class="flex items-center justify-between mt-3 pt-3 border-t border-zinc-800">
                <div class="flex gap-1">
                  <button @click="toggleActive(challenge)" class="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all" title="Pause">
                    <Pause :size="14" />
                  </button>
                  <button @click="refreshProgress(challenge)" class="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all" title="Refresh progress">
                    <TrendingUp :size="14" />
                  </button>
                </div>
                <div class="flex gap-1">
                  <button @click="openEditDialog(challenge)" class="p-2 rounded-lg text-zinc-500 hover:text-zinc-300 hover:bg-white/5 transition-all" title="Edit">
                    <Edit :size="14" />
                  </button>
                  <button @click="deleteChallenge(challenge)" class="p-2 rounded-lg text-zinc-500 hover:text-rose-400 hover:bg-rose-500/5 transition-all" title="Delete">
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
            <span class="text-xs font-bold text-zinc-500 bg-white/5 px-2.5 py-1 rounded-full">{{ completedChallenges.length }}</span>
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
              <p class="text-[10px] text-zinc-500 mt-1">
                {{ CHALLENGE_TYPES.find(t => t.value === challenge.challenge_type)?.label || 'Books Read' }}
              </p>
              <p class="text-[10px] text-zinc-500 mt-1">
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
                <Label>Challenge Title *</Label>
                <Input v-model="editForm.title" placeholder="2026 Reading Challenge" required />
              </div>
              <div class="space-y-2">
                <Label>Description</Label>
                <Textarea v-model="editForm.description" placeholder="Describe your goal..." rows="3" />
              </div>
              <div class="space-y-2">
                <Label>Challenge Type</Label>
                <select v-model="editForm.challenge_type" class="flex h-10 w-full rounded-md border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option v-for="opt in CHALLENGE_TYPES" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>{{ getTargetLabel(editForm.challenge_type) }} *</Label>
                  <Input v-model.number="editForm.target_books" type="number" min="1" required />
                </div>
                <div v-if="editForm.challenge_type === 'books'" class="space-y-2">
                  <Label>Min Pages</Label>
                  <Input v-model.number="editForm.min_pages" type="number" placeholder="200" />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label>Start Date *</Label>
                  <Input v-model="editForm.start_date" type="date" required />
                </div>
                <div class="space-y-2">
                  <Label>End Date *</Label>
                  <Input v-model="editForm.end_date" type="date" required />
                </div>
              </div>
              <div class="flex gap-4">
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editForm.is_active" type="checkbox" class="rounded" />
                  <span class="text-sm">Active</span>
                </label>
                <label class="flex items-center gap-2 cursor-pointer">
                  <input v-model="editForm.is_public" type="checkbox" class="rounded" />
                  <span class="text-sm">Public</span>
                </label>
              </div>
              <div class="flex justify-end gap-2 pt-2">
                <button type="button" @click="isEditDialogOpen = false" class="px-4 py-2 rounded-lg text-sm font-bold text-zinc-400 hover:text-white transition-colors">Cancel</button>
                <button type="submit" class="px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors">Save Changes</button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        <!-- Empty State -->
        <div v-if="activeChallenges.length === 0 && completedChallenges.length === 0" class="text-center py-16 lg:py-24">
          <div class="w-20 h-20 rounded-2xl bg-zinc-900/50 border border-zinc-800 flex items-center justify-center mx-auto mb-6">
            <Target :size="40" class="text-zinc-700" />
          </div>
          <h3 class="text-lg font-bold text-white mb-2">No challenges yet</h3>
          <p class="text-sm text-zinc-500 mb-6 max-w-xs mx-auto">
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

      <!-- ==================== SCHEDULE TAB ==================== -->
      <div v-show="activeTab === 'schedule'">

        <!-- Loading -->
        <div v-if="scheduleLoading" class="flex items-center justify-center py-24">
          <div class="w-8 h-8 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin" />
        </div>

        <div v-else class="flex gap-0 lg:gap-6 items-start">

          <!-- ===== SIDEBAR ===== -->
          <aside class="hidden lg:flex flex-col w-64 xl:w-72 shrink-0 gap-4 sticky top-4">

            <!-- Schedules list -->
            <div class="rounded-2xl border border-zinc-800 bg-zinc-900/50 overflow-hidden flex flex-col">
              <div class="flex items-center justify-between px-4 py-3 border-b border-zinc-800">
                <span class="text-xs font-bold text-zinc-400 uppercase tracking-widest">Schedules</span>
                <button @click="isCreatingSchedule = !isCreatingSchedule" class="p-1 rounded-lg text-zinc-500 hover:text-white hover:bg-white/10 transition-all">
                  <Plus :size="14" />
                </button>
              </div>

              <!-- New schedule input -->
              <div v-if="isCreatingSchedule" class="px-3 py-2 border-b border-zinc-800">
                <div class="flex gap-2">
                  <input
                    v-model="newScheduleTitle"
                    @keydown.enter="createSchedule"
                    @keydown.escape="isCreatingSchedule = false; newScheduleTitle = ''"
                    placeholder="Schedule title..."
                    autofocus
                    class="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button @click="createSchedule" class="px-2 py-1.5 rounded-lg bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-400 transition-colors">Add</button>
                </div>
              </div>

              <!-- Schedule list -->
              <div class="flex-1 overflow-y-auto">
                <div v-if="schedules.length === 0" class="py-8 text-center">
                  <ListTodo :size="28" class="text-zinc-700 mx-auto mb-2" />
                  <p class="text-xs text-zinc-500">No schedules yet</p>
                </div>
                <div
                  v-for="schedule in schedules"
                  :key="schedule.id"
                  @click="selectSchedule(schedule)"
                  :class="[
                    'w-full flex items-center gap-2 px-4 py-3 cursor-pointer transition-all border-b border-zinc-800/50 group',
                    selectedScheduleId === schedule.id ? 'bg-indigo-500/10 text-white' : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                  ]"
                >
                  <ListTodo :size="14" :class="selectedScheduleId === schedule.id ? 'text-indigo-400' : 'text-zinc-600'" />
                  <span class="flex-1 text-sm font-medium truncate">{{ schedule.title }}</span>
                  <button
                    @click.stop="deleteSchedule(schedule)"
                    class="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-rose-400 transition-all"
                  >
                    <Trash2 :size="12" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Library books -->
            <div class="rounded-2xl border border-zinc-800 bg-zinc-900/50 overflow-hidden flex flex-col">
              <div class="px-4 py-3 border-b border-zinc-800">
                <span class="text-xs font-bold text-zinc-400 uppercase tracking-widest block mb-2">Library</span>
                <div class="relative">
                  <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
                  <input
                    v-model="bookSearch"
                    placeholder="Search books..."
                    class="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <p class="text-[10px] text-zinc-500 mt-1.5">Drag to section or click <span class="text-indigo-400">+</span></p>
              </div>

              <draggable
                :list="libraryBooks"
                class="overflow-y-auto p-2 space-y-0.5 max-h-[380px]"
                item-key="id"
                :animation="150"
                :group="{ name: 'schedule-books', pull: 'clone', put: false }"
                :sort="false"
                :clone="(book) => ({ ...book })"
                handle=".library-drag-handle"
              >
                <template #item="{ element: book }">
                  <div
                    :class="[
                      'flex items-center gap-2 p-1.5 rounded-lg transition-colors group',
                      isBookInSchedule(book.id) ? 'opacity-40' : 'hover:bg-zinc-800/50'
                    ]"
                  >
                    <GripVertical
                      v-if="!isBookInSchedule(book.id)"
                      :size="12"
                      class="library-drag-handle text-zinc-600 cursor-grab active:cursor-grabbing shrink-0 touch-none"
                    />
                    <div v-else class="w-3 shrink-0" />
                    <img v-if="book.cover_image" :src="book.cover_image" class="w-7 h-10 object-cover rounded shrink-0" />
                    <div v-else class="w-7 h-10 bg-zinc-800 rounded shrink-0 flex items-center justify-center">
                      <BookOpen :size="10" class="text-zinc-600" />
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="text-[11px] font-medium text-zinc-200 leading-tight truncate">{{ book.title }}</p>
                      <p class="text-[10px] text-zinc-500 truncate">{{ getAuthorNames(book) }}</p>
                    </div>
                    <button
                      v-if="!isBookInSchedule(book.id) && activeSection"
                      @click.stop="addBookToSection(book)"
                      class="opacity-0 group-hover:opacity-100 p-1 rounded text-zinc-500 hover:text-indigo-400 hover:bg-indigo-500/10 transition-all shrink-0"
                      title="Add to active section"
                    >
                      <Plus :size="13" />
                    </button>
                  </div>
                </template>
                <template #footer>
                  <p v-if="libraryBooks.length === 0" class="text-xs text-zinc-500 py-4 text-center">No books found</p>
                </template>
              </draggable>
            </div>
          </aside>

          <!-- ===== MAIN BOARD ===== -->
          <div class="flex-1 flex flex-col min-w-0">

            <!-- Mobile schedule picker -->
            <div class="lg:hidden mb-4 shrink-0">
              <div class="flex items-center gap-2">
                <select
                  :value="selectedScheduleId || ''"
                  @change="(e) => { const s = schedules.find(s => s.id === Number(e.target.value)); if (s) selectSchedule(s); }"
                  class="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 appearance-none"
                >
                  <option value="" disabled>Select a schedule...</option>
                  <option v-for="s in schedules" :key="s.id" :value="s.id">{{ s.title }}</option>
                </select>
                <button
                  @click="isCreatingSchedule = true"
                  class="p-2.5 rounded-xl bg-indigo-500 text-white shrink-0"
                >
                  <Plus :size="16" />
                </button>
                <button
                  v-if="selectedScheduleId"
                  @click="deleteSchedule(schedules.find(s => s.id === selectedScheduleId))"
                  class="p-2.5 rounded-xl border border-zinc-700 text-zinc-500 hover:text-rose-400 shrink-0"
                >
                  <Trash2 :size="16" />
                </button>
              </div>
              <!-- Mobile new schedule input -->
              <div v-if="isCreatingSchedule" class="mt-2 flex gap-2">
                <input
                  v-model="newScheduleTitle"
                  @keydown.enter="createSchedule"
                  @keydown.escape="isCreatingSchedule = false; newScheduleTitle = ''"
                  placeholder="Schedule title..."
                  autofocus
                  class="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                />
                <button @click="createSchedule" class="px-4 py-2 rounded-xl bg-indigo-500 text-white text-sm font-bold">Add</button>
              </div>
            </div>

            <!-- No schedule selected -->
            <div v-if="!selectedScheduleId" class="flex-1 flex items-center justify-center">
              <div class="text-center">
                <ListTodo :size="48" class="text-zinc-700 mx-auto mb-4" />
                <p class="text-zinc-500 mb-4">No schedule selected</p>
                <button
                  @click="isCreatingSchedule = true"
                  class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors flex items-center gap-2 mx-auto"
                >
                  <Plus :size="15" />
                  Create Schedule
                </button>
              </div>
            </div>

            <template v-else>
              <!-- Board header -->
              <div class="flex items-center justify-between mb-4 shrink-0">
                <div>
                  <h2 class="text-lg font-bold text-white">{{ schedules.find(s => s.id === selectedScheduleId)?.title }}</h2>
                  <p class="text-xs text-zinc-500">{{ localSections.length }} sections · drag books between sections</p>
                </div>
                <button
                  @click="addSection"
                  class="px-4 py-2 rounded-xl border border-dashed border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-600 text-sm font-medium flex items-center gap-1.5 transition-all"
                >
                  <Plus :size="14" />
                  Add Section
                </button>
              </div>

              <!-- Mobile library books toggle bar -->
              <div class="lg:hidden mb-3 shrink-0">
                <div class="flex items-center gap-2">
                  <div class="relative flex-1">
                    <Search :size="13" class="absolute left-2.5 top-1/2 -translate-y-1/2 text-zinc-500" />
                    <input
                      v-model="bookSearch"
                      placeholder="Search library..."
                      class="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-8 pr-3 py-2 text-xs text-white placeholder-zinc-500 focus:outline-none"
                    />
                  </div>
                </div>
                <!-- Mobile library quick-add books -->
                <div v-if="bookSearch.trim()" class="mt-2 rounded-xl border border-zinc-800 bg-zinc-900/80 p-2 max-h-40 overflow-y-auto space-y-1">
                  <div
                    v-for="book in libraryBooks.slice(0, 8)"
                    :key="book.id"
                    class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-zinc-800/50 transition-colors"
                  >
                    <div class="flex-1 min-w-0">
                      <p class="text-xs font-medium text-zinc-200 truncate">{{ book.title }}</p>
                    </div>
                    <button
                      v-if="!isBookInSchedule(book.id) && activeSection"
                      @click="addBookToSection(book)"
                      class="p-1 rounded text-indigo-400 hover:bg-indigo-500/10 transition-colors shrink-0"
                    >
                      <Plus :size="13" />
                    </button>
                  </div>
                </div>
              </div>

              <!-- Sections Board -->
              <div class="pb-4">
                <draggable
                  v-model="localSections"
                  class="flex flex-wrap gap-4 items-start"
                  item-key="id"
                  :animation="200"
                  handle=".section-drag-handle"
                  @end="onSectionsReorder"
                >
                  <template #item="{ element: section }">
                    <div
                      :class="[
                        'w-56 xl:w-64 shrink-0 rounded-2xl border overflow-hidden transition-colors',
                        activeSectionId === section.id ? 'border-indigo-500/40 bg-indigo-950/20' : 'border-zinc-800 bg-zinc-900/50'
                      ]"
                      @click="activeSectionId = section.id"
                    >
                      <!-- Section header -->
                      <div class="flex items-center gap-1.5 px-3 py-2.5 border-b border-zinc-800 shrink-0">
                        <GripVertical :size="14" class="section-drag-handle text-zinc-600 cursor-grab active:cursor-grabbing shrink-0" />
                        <input
                          v-if="editingSectionId === section.id"
                          v-model="editingSectionTitle"
                          :data-section-id="section.id"
                          @blur="saveSectionTitle(section)"
                          @keydown.enter.prevent="saveSectionTitle(section)"
                          @keydown.escape="editingSectionId = null"
                          class="flex-1 bg-transparent text-sm font-bold text-white border-b border-indigo-500 outline-none min-w-0"
                          @click.stop
                        />
                        <span
                          v-else
                          @dblclick.stop="startEditSection(section.id, section.title)"
                          class="flex-1 text-sm font-bold text-zinc-200 truncate cursor-pointer"
                          title="Double-click to rename"
                        >{{ section.title }}</span>
                        <span class="text-[10px] text-zinc-600 shrink-0">{{ section.bookItems.length }}</span>
                        <button @click.stop="deleteSection(section)" class="text-zinc-600 hover:text-rose-400 transition-colors shrink-0">
                          <X :size="12" />
                        </button>
                      </div>

                      <!-- Books list (draggable) -->
                      <draggable
                        v-model="section.bookItems"
                        class="p-2 space-y-1.5 overflow-y-auto max-h-80"
                        style="min-height: 64px"
                        item-key="id"
                        :animation="150"
                        :group="{ name: 'schedule-books', pull: true, put: true }"
                        ghost-class="opacity-30"
                        handle=".book-drag-handle"
                        @change="(evt) => onSectionBooksChange(section, evt)"
                      >
                        <template #item="{ element: book, index }">
                          <div class="flex items-center gap-2 p-1.5 rounded-lg bg-zinc-800/60 hover:bg-zinc-800 group transition-colors">
                            <GripVertical :size="12" class="book-drag-handle text-zinc-600 cursor-grab active:cursor-grabbing shrink-0 touch-none" />
                            <img v-if="book.cover_image" :src="book.cover_image" class="w-7 h-10 object-cover rounded shrink-0" />
                            <div v-else class="w-7 h-10 bg-zinc-700 rounded shrink-0 flex items-center justify-center">
                              <BookOpen :size="10" class="text-zinc-500" />
                            </div>
                            <div class="flex-1 min-w-0">
                              <p class="text-[11px] font-medium text-zinc-200 leading-tight line-clamp-2">{{ book.title }}</p>
                              <p class="text-[10px] text-zinc-500 truncate">{{ getAuthorNames(book) }}</p>
                            </div>
                            <button @click.stop="removeBookFromSection(section, index)" class="opacity-0 group-hover:opacity-100 text-zinc-600 hover:text-rose-400 transition-all shrink-0 p-0.5">
                              <X :size="11" />
                            </button>
                          </div>
                        </template>
                        <template #footer>
                          <div v-if="section.bookItems.length === 0" class="flex items-center justify-center py-6 rounded-lg border border-dashed border-zinc-800 text-zinc-600 text-xs">
                            Drop books here
                          </div>
                        </template>
                      </draggable>
                    </div>
                  </template>
                </draggable>

                <!-- Empty board state -->
                <div v-if="localSections.length === 0" class="flex items-center justify-center h-48">
                  <div class="text-center">
                    <p class="text-zinc-500 text-sm mb-3">No sections yet</p>
                    <button @click="addSection" class="px-4 py-2 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors flex items-center gap-2 mx-auto">
                      <Plus :size="14" />
                      Add First Section
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Mobile: No schedule empty state -->
        <div v-if="!scheduleLoading && schedules.length === 0 && activeTab === 'schedule'" class="lg:hidden text-center py-12">
          <ListTodo :size="40" class="text-zinc-700 mx-auto mb-3" />
          <p class="text-zinc-500 text-sm mb-4">Create a reading schedule to plan your books</p>
          <button
            @click="isCreatingSchedule = true; newScheduleTitle = 'My Reading Plan'"
            class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-colors inline-flex items-center gap-2"
          >
            <Plus :size="14" />
            Create Schedule
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
