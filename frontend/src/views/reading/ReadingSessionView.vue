<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useBooksStore } from '@/stores/booksStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { readingSessionsAPI } from '@/services/api'
import { getBookUrl } from '@/utils/bookUrl'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { 
  Play, 
  Pause, 
  Square, 
  Plus, 
  Minus,
  Quote,
  X,
  CheckCircle,
  Clock,
  BookOpen,
  TrendingUp,
  Award
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const booksStore = useBooksStore()
const userBooksStore = useUserBooksStore()
const quotesStore = useQuotesStore()

const bookId = route.params.id
const book = ref(null)
const userBook = ref(null)
const loadingData = ref(true)

// Session state
const isActive = ref(false)
const isPaused = ref(false)
const startTime = ref(null)
const pausedTime = ref(0)
const elapsedSeconds = ref(0)
const timerInterval = ref(null)
const autoSaveInterval = ref(null)

// Progress tracking
const currentPage = ref(0)
const startPage = ref(0)
const pagesRead = ref(0)

// Quick quote
const isQuoteDialogOpen = ref(false)
const quoteText = ref('')
const quotePage = ref(0)

// Session summary
const isSessionEndDialogOpen = ref(false)
const sessionStats = ref({})

// Reading streak (mock for now)
const currentStreak = ref(7)

onMounted(async () => {
  await loadBookData()
  setupAutoSave()
})

onBeforeUnmount(() => {
  if (timerInterval.value) clearInterval(timerInterval.value)
  if (autoSaveInterval.value) clearInterval(autoSaveInterval.value)
})

const loadBookData = async () => {
  loadingData.value = true
  const result = await booksStore.fetchBook(bookId)
  if (result.success) {
    book.value = result.data
  }

  await userBooksStore.fetchBooks()
  userBook.value = userBooksStore.books.find(b => b.book.id === parseInt(bookId))

  if (!userBook.value) {
    loadingData.value = false
    return
  }

  currentPage.value = userBook.value.current_page || 0
  startPage.value = currentPage.value
  loadingData.value = false
}

const formattedTime = computed(() => {
  const hours = Math.floor(elapsedSeconds.value / 3600)
  const minutes = Math.floor((elapsedSeconds.value % 3600) / 60)
  const seconds = elapsedSeconds.value % 60

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})

const readingProgress = computed(() => {
  if (!book.value?.pages) return 0
  return Math.min(100, (currentPage.value / book.value.pages) * 100)
})

const pagesPerMinute = computed(() => {
  const minutes = elapsedSeconds.value / 60
  if (minutes === 0) return 0
  return (pagesRead.value / minutes).toFixed(1)
})

const estimatedTimeLeft = computed(() => {
  if (!book.value?.pages || pagesPerMinute.value === 0) return 'N/A'
  const pagesLeft = book.value.pages - currentPage.value
  const minutesLeft = Math.ceil(pagesLeft / pagesPerMinute.value)
  
  if (minutesLeft < 60) return `${minutesLeft}m`
  const hours = Math.floor(minutesLeft / 60)
  const mins = minutesLeft % 60
  return `${hours}h ${mins}m`
})

const startSession = () => {
  isActive.value = true
  isPaused.value = false
  startTime.value = Date.now() - (elapsedSeconds.value * 1000)

  timerInterval.value = setInterval(() => {
    if (!isPaused.value) {
      elapsedSeconds.value = Math.floor((Date.now() - startTime.value) / 1000)
    }
  }, 1000)
}

const pauseSession = () => {
  isPaused.value = !isPaused.value
  if (isPaused.value) {
    pausedTime.value = Date.now()
  } else {
    const pauseDuration = Date.now() - pausedTime.value
    startTime.value += pauseDuration
  }
}

const endSession = async () => {
  if (timerInterval.value) clearInterval(timerInterval.value)

  pagesRead.value = currentPage.value - startPage.value

  sessionStats.value = {
    duration: formattedTime.value,
    pagesRead: pagesRead.value,
    startPage: startPage.value,
    endPage: currentPage.value,
    pagesPerMinute: pagesPerMinute.value,
    date: new Date().toLocaleDateString(),
  }

  saveProgress()

  // Persist session to backend
  if (userBook.value && elapsedSeconds.value > 0) {
    try {
      await readingSessionsAPI.create({
        user_book: userBook.value.id,
        duration_seconds: elapsedSeconds.value,
        start_page: startPage.value,
        end_page: currentPage.value,
        pages_read: Math.max(0, pagesRead.value),
        started_at: new Date(startTime.value).toISOString(),
      })
    } catch (err) {
      // Session save failed
    }
  }

  isSessionEndDialogOpen.value = true
  isActive.value = false
}

const incrementPage = () => {
  currentPage.value++
}

const decrementPage = () => {
  if (currentPage.value > 0) currentPage.value--
}

const updatePageManual = (value) => {
  const page = parseInt(value)
  if (!isNaN(page) && page >= 0) {
    currentPage.value = page
  }
}

const saveProgress = async () => {
  if (userBook.value) {
    await userBooksStore.updateProgress(userBook.value.id, currentPage.value)
  }
}

const setupAutoSave = () => {
  autoSaveInterval.value = setInterval(() => {
    if (isActive.value && !isPaused.value) {
      saveProgress()
    }
  }, 30000) // Auto-save every 30 seconds
}

const openQuoteDialog = () => {
  quotePage.value = currentPage.value
  isQuoteDialogOpen.value = true
}

const saveQuote = async () => {
  if (!quoteText.value.trim()) return

  await quotesStore.createQuote({
    book: bookId,
    user_book: userBook.value?.id,
    text: quoteText.value,
    page_number: quotePage.value,
  })

  quoteText.value = ''
  isQuoteDialogOpen.value = false
}

const finishSession = () => {
  isSessionEndDialogOpen.value = false
  router.push(book.value ? getBookUrl(book.value) : `/books/${bookId}`)
}

const getCoverImage = computed(() => {
  return book.value?.cover_image || `https://via.placeholder.com/200x300?text=${book.value?.title}`
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
    <!-- Exit Button -->
    <div class="fixed top-4 left-4 z-50">
      <Button 
        variant="outline" 
        size="icon"
        class="rounded-full shadow-lg bg-white/90 backdrop-blur"
        @click="router.back()"
      >
        <X class="w-5 h-5" />
      </Button>
    </div>

    <!-- Loading State -->
    <div v-if="loadingData" class="flex items-center justify-center py-24">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
    </div>

    <!-- No user book found -->
    <div v-else-if="!userBook" class="text-center py-24">
      <p class="text-red-400 mb-4">This book is not in your library.</p>
      <button @click="router.back()" class="text-amber-500 hover:text-amber-400">Go back</button>
    </div>

    <!-- Main Content -->
    <div v-else class="container mx-auto px-4 py-8 max-w-5xl">
      <!-- Book Info Header -->
      <div class="text-center mb-8">
        <div class="flex items-center justify-center gap-4 mb-4">
          <div class="w-20 h-28 rounded-lg overflow-hidden shadow-lg">
            <img :src="getCoverImage" :alt="book?.title" class="w-full h-full object-cover" />
          </div>
          <div class="text-left">
            <h1 class="text-2xl font-bold">{{ book?.title }}</h1>
            <p class="text-muted-foreground">
              {{ book?.authors?.map(a => a.name).join(', ') }}
            </p>
          </div>
        </div>

        <!-- Reading Streak -->
        <div class="inline-flex items-center gap-2 px-4 py-2 bg-orange-100 dark:bg-orange-900/30 rounded-full">
          <Award class="w-5 h-5 text-orange-600" />
          <span class="font-semibold text-orange-600">{{ currentStreak }} day streak! 🔥</span>
        </div>
      </div>

      <!-- Timer Card -->
      <Card class="mb-6 shadow-xl">
        <CardContent class="p-8">
          <!-- Timer Display -->
          <div class="text-center mb-8">
            <div class="flex items-center justify-center gap-3 mb-2">
              <Clock class="w-8 h-8 text-primary" />
              <div class="text-6xl font-bold font-mono tabular-nums">
                {{ formattedTime }}
              </div>
            </div>
            <p class="text-muted-foreground">
              {{ isPaused ? 'Paused' : isActive ? 'Reading in progress' : 'Ready to start' }}
            </p>
          </div>

          <!-- Timer Controls -->
          <div class="flex items-center justify-center gap-4 mb-8">
            <Button 
              v-if="!isActive"
              size="lg"
              class="rounded-full px-8"
              @click="startSession"
            >
              <Play class="w-5 h-5 mr-2" />
              Start Reading
            </Button>

            <template v-else>
              <Button 
                size="lg"
                variant="outline"
                class="rounded-full"
                @click="pauseSession"
              >
                <component :is="isPaused ? Play : Pause" class="w-5 h-5 mr-2" />
                {{ isPaused ? 'Resume' : 'Pause' }}
              </Button>

              <Button 
                size="lg"
                variant="destructive"
                class="rounded-full"
                @click="endSession"
              >
                <Square class="w-5 h-5 mr-2" />
                End Session
              </Button>
            </template>
          </div>

          <!-- Progress Bar -->
          <div class="space-y-2 mb-6">
            <div class="flex justify-between text-sm text-muted-foreground">
              <span>Progress</span>
              <span>{{ Math.round(readingProgress) }}%</span>
            </div>
            <Progress :model-value="readingProgress" class="h-3" />
          </div>

          <!-- Page Counter -->
          <Card class="bg-muted/50">
            <CardContent class="p-6">
              <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Current Page -->
                <div class="text-center">
                  <p class="text-sm text-muted-foreground mb-3">Current Page</p>
                  <div class="flex items-center justify-center gap-2">
                    <Button 
                      variant="outline" 
                      size="icon"
                      @click="decrementPage"
                      :disabled="!isActive || currentPage === 0"
                    >
                      <Minus class="w-4 h-4" />
                    </Button>
                    
                    <Input
                      v-model="currentPage"
                      type="number"
                      class="w-24 text-center text-2xl font-bold"
                      @change="updatePageManual(currentPage)"
                      :disabled="!isActive"
                    />
                    
                    <Button 
                      variant="outline" 
                      size="icon"
                      @click="incrementPage"
                      :disabled="!isActive"
                    >
                      <Plus class="w-4 h-4" />
                    </Button>
                  </div>
                  <p class="text-xs text-muted-foreground mt-2">
                    of {{ book?.pages || '?' }} pages
                  </p>
                </div>

                <!-- Stats -->
                <div class="text-center">
                  <p class="text-sm text-muted-foreground mb-2">Reading Speed</p>
                  <div class="flex items-center justify-center gap-2">
                    <TrendingUp class="w-5 h-5 text-blue-500" />
                    <p class="text-2xl font-bold">{{ pagesPerMinute }}</p>
                  </div>
                  <p class="text-xs text-muted-foreground mt-1">pages/min</p>
                </div>

                <div class="text-center">
                  <p class="text-sm text-muted-foreground mb-2">Est. Time Left</p>
                  <div class="flex items-center justify-center gap-2">
                    <Clock class="w-5 h-5 text-purple-500" />
                    <p class="text-2xl font-bold">{{ estimatedTimeLeft }}</p>
                  </div>
                  <p class="text-xs text-muted-foreground mt-1">to finish</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <!-- Quick Quote Button -->
          <div class="text-center mt-6">
            <Button 
              variant="outline" 
              @click="openQuoteDialog"
              :disabled="!isActive"
            >
              <Quote class="w-4 h-4 mr-2" />
              Capture Quote
            </Button>
          </div>
        </CardContent>
      </Card>

      <!-- Tips -->
      <Card class="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-900">
        <CardContent class="p-4">
          <p class="text-sm text-center text-blue-700 dark:text-blue-300">
            💡 <strong>Tip:</strong> Progress auto-saves every 30 seconds. Focus on reading, we've got you covered!
          </p>
        </CardContent>
      </Card>
    </div>

    <!-- Quick Quote Dialog -->
    <Dialog v-model:open="isQuoteDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Capture Quote</DialogTitle>
        </DialogHeader>
        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">Quote Text</label>
            <Textarea
              v-model="quoteText"
              placeholder="Enter the quote..."
              rows="4"
              autofocus
            />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium">Page Number</label>
            <Input
              v-model.number="quotePage"
              type="number"
            />
          </div>

          <div class="flex justify-end gap-2">
            <Button variant="outline" @click="isQuoteDialogOpen = false">
              Cancel
            </Button>
            <Button @click="saveQuote">
              <CheckCircle class="w-4 h-4 mr-2" />
              Save Quote
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>

    <!-- Session End Dialog -->
    <Dialog v-model:open="isSessionEndDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle class="text-center text-2xl">Great Session! 🎉</DialogTitle>
        </DialogHeader>
        <div class="space-y-6 py-4">
          <!-- Session Stats -->
          <div class="grid grid-cols-2 gap-4">
            <Card>
              <CardContent class="p-4 text-center">
                <Clock class="w-6 h-6 text-blue-500 mx-auto mb-2" />
                <p class="text-2xl font-bold">{{ sessionStats.duration }}</p>
                <p class="text-xs text-muted-foreground">Time</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <BookOpen class="w-6 h-6 text-green-500 mx-auto mb-2" />
                <p class="text-2xl font-bold">{{ sessionStats.pagesRead }}</p>
                <p class="text-xs text-muted-foreground">Pages Read</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <TrendingUp class="w-6 h-6 text-purple-500 mx-auto mb-2" />
                <p class="text-2xl font-bold">{{ sessionStats.pagesPerMinute }}</p>
                <p class="text-xs text-muted-foreground">Pages/Min</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <Award class="w-6 h-6 text-orange-500 mx-auto mb-2" />
                <p class="text-2xl font-bold">{{ currentStreak }}</p>
                <p class="text-xs text-muted-foreground">Day Streak</p>
              </CardContent>
            </Card>
          </div>

          <div class="text-center">
            <p class="text-sm text-muted-foreground">
              You read from page {{ sessionStats.startPage }} to {{ sessionStats.endPage }}
            </p>
          </div>

          <Button class="w-full" @click="finishSession">
            Done
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  </div>
</template>