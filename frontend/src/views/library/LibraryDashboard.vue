<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { useChallengesStore } from '@/stores/challengesStore'
import { useListsStore } from '@/stores/listsStore'
import { getBookUrl } from '@/utils/bookUrl'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Progress } from '@/components/ui/progress'
import {
  BookOpen,
  Heart,
  Library as LibraryIcon,
  Plus,
  Quote,
  Target,
  List,
  TrendingUp,
  Calendar,
  Star,
  BookMarked,
  ArrowRight
} from 'lucide-vue-next'

const router = useRouter()
const booksStore = useUserBooksStore()
const quotesStore = useQuotesStore()
const challengesStore = useChallengesStore()
const listsStore = useListsStore()

const loading = ref(true)

// Fetch all data
onMounted(async () => {
  loading.value = true
  await Promise.all([
    booksStore.fetchBooks(),
    quotesStore.fetchQuotes(),
    challengesStore.fetchChallenges(),
    listsStore.fetchLists(),
  ])
  loading.value = false
})

// Currently reading books
const currentlyReading = computed(() => {
  return booksStore.books
    .filter(b => b.status === 'currently_reading')
    .slice(0, 4) // Show max 4
})

// Stats
const stats = computed(() => booksStore.stats)

// Real data from stores
const recentQuotes = computed(() => {
  const quotes = quotesStore.quotes
  if (!Array.isArray(quotes)) return []
  return quotes.slice(0, 3)
})

const activeChallenges = computed(() => {
  return challengesStore.activeChallenges
})

const readingLists = computed(() => {
  const lists = listsStore.lists
  if (!Array.isArray(lists)) return []
  return lists.slice(0, 3)
})

const quotesCount = computed(() => {
  const quotes = quotesStore.quotes
  return Array.isArray(quotes) ? quotes.length : 0
})

// Navigation helpers
const goToBooks = () => router.push('/library/all')
const goToQuotes = () => router.push('/quotes')
const goToChallenges = () => router.push('/challenges')
const goToLists = () => router.push('/lists')
const goToBrowse = () => router.push('/books')
const goToFeed = () => router.push('/feed')

// Book actions
const viewBook = (book) => router.push(getBookUrl(book.book))
const updateProgress = (book) => {
  router.push(getBookUrl(book.book))
}
const addQuote = (book) => {
  router.push(`/quotes/new?book=${book.book.id}`)
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="border-b bg-card">
      <div class="container mx-auto px-4 py-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <LibraryIcon class="w-8 h-8 text-primary" />
            <div>
              <h1 class="text-3xl font-bold">My Library</h1>
              <p class="text-muted-foreground">Your reading journey at a glance</p>
            </div>
          </div>
          <Button size="lg" @click="goToBrowse">
            <Plus class="w-4 h-4 mr-2" />
            Add Book
          </Button>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-8 space-y-8">
      <!-- Stats Overview -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="goToBooks">
          <CardContent class="p-6">
            <div class="flex items-center justify-between mb-2">
              <BookOpen class="w-5 h-5 text-muted-foreground" />
              <TrendingUp class="w-4 h-4 text-green-500" />
            </div>
            <p class="text-2xl font-bold">{{ stats.total }}</p>
            <p class="text-sm text-muted-foreground">Total Books</p>
          </CardContent>
        </Card>

        <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="goToBooks">
          <CardContent class="p-6">
            <div class="flex items-center justify-between mb-2">
              <BookMarked class="w-5 h-5 text-blue-500" />
            </div>
            <p class="text-2xl font-bold text-blue-600">{{ stats.currently_reading }}</p>
            <p class="text-sm text-muted-foreground">Currently Reading</p>
          </CardContent>
        </Card>

        <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="goToBooks">
          <CardContent class="p-6">
            <div class="flex items-center justify-between mb-2">
              <Star class="w-5 h-5 text-green-500" />
            </div>
            <p class="text-2xl font-bold text-green-600">{{ stats.read }}</p>
            <p class="text-sm text-muted-foreground">Books Read</p>
          </CardContent>
        </Card>

        <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="goToQuotes">
          <CardContent class="p-6">
            <div class="flex items-center justify-between mb-2">
              <Quote class="w-5 h-5 text-purple-500" />
            </div>
            <p class="text-2xl font-bold text-purple-600">{{ quotesCount }}</p>
            <p class="text-sm text-muted-foreground">Quotes Saved</p>
          </CardContent>
        </Card>
      </div>

      <!-- Currently Reading -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <BookMarked class="w-6 h-6 text-primary" />
            Currently Reading
          </h2>
          <Button variant="ghost" @click="goToBooks">
            View All
            <ArrowRight class="w-4 h-4 ml-2" />
          </Button>
        </div>

        <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Skeleton v-for="i in 4" :key="i" class="h-48" />
        </div>

        <div v-else-if="currentlyReading.length === 0" class="text-center py-12 bg-muted/30 rounded-lg">
          <BookOpen class="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
          <p class="text-muted-foreground mb-4">No books in progress</p>
          <Button @click="goToBrowse">Start Reading</Button>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card 
            v-for="book in currentlyReading" 
            :key="book.id"
            class="hover:shadow-lg transition-shadow cursor-pointer group"
          >
            <CardHeader class="pb-3" @click="viewBook(book)">
              <div class="flex gap-3">
                <div class="w-16 h-24 bg-muted rounded overflow-hidden flex-shrink-0">
                  <img
                    :src="book.book?.cover_image || `https://via.placeholder.com/150x200?text=${book.book?.title}`"
                    :alt="book.book?.title"
                    class="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <CardTitle class="text-sm line-clamp-2 mb-1">{{ book.book?.title }}</CardTitle>
                  <CardDescription class="text-xs line-clamp-1">
                    {{ book.book?.authors?.map(a => a.name).join(', ') }}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent class="space-y-3">
              <!-- Progress -->
              <div class="space-y-1">
                <div class="flex justify-between text-xs text-muted-foreground">
                  <span>{{ book.current_page || 0 }} / {{ book.book?.pages || '?' }} pages</span>
                  <span>{{ book.reading_progress || 0 }}%</span>
                </div>
                <Progress :model-value="book.reading_progress || 0" class="h-2" />
              </div>

              <!-- Quick actions -->
              <div class="flex gap-2">
                <Button size="sm" variant="outline" class="flex-1" @click="updateProgress(book)">
                  Update
                </Button>
                <Button size="sm" class="flex-1" @click="addQuote(book)">
                  <Quote class="w-3 h-3 mr-1" />
                  Quote
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <!-- Two column layout for Quotes and Challenges -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Recent Quotes -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold flex items-center gap-2">
              <Quote class="w-6 h-6 text-primary" />
              Recent Quotes
            </h2>
            <Button variant="ghost" size="sm" @click="goToQuotes">
              View All
              <ArrowRight class="w-4 h-4 ml-2" />
            </Button>
          </div>

          <div class="space-y-3">
            <Card 
              v-for="quote in recentQuotes" 
              :key="quote.id"
              class="hover:shadow-md transition-shadow cursor-pointer"
              @click="goToQuotes"
            >
              <CardContent class="p-4">
                <blockquote class="text-sm italic mb-2 line-clamp-2">
                  "{{ quote.text }}"
                </blockquote>
                <div class="flex items-center justify-between">
                  <p class="text-xs text-muted-foreground">
                    {{ quote.book_title || quote.book?.title || 'Unknown Book' }}
                  </p>
                  <Badge variant="secondary" class="text-xs">
                    {{ new Date(quote.created_at).toLocaleDateString() }}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Button variant="outline" class="w-full" @click="goToQuotes">
              <Plus class="w-4 h-4 mr-2" />
              Add New Quote
            </Button>
          </div>
        </section>

        <!-- Active Challenges -->
        <section>
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold flex items-center gap-2">
              <Target class="w-6 h-6 text-primary" />
              Reading Challenges
            </h2>
            <Button variant="ghost" size="sm" @click="goToChallenges">
              View All
              <ArrowRight class="w-4 h-4 ml-2" />
            </Button>
          </div>

          <div class="space-y-3">
            <Card 
              v-for="challenge in activeChallenges" 
              :key="challenge.id"
              class="hover:shadow-md transition-shadow cursor-pointer"
              @click="goToChallenges"
            >
              <CardContent class="p-4 space-y-3">
                <div class="flex items-start justify-between">
                  <div>
                    <h3 class="font-semibold">{{ challenge.title }}</h3>
                    <p class="text-sm text-muted-foreground">
                      {{ challenge.completed_books }} / {{ challenge.target_books }} books
                    </p>
                  </div>
                  <Badge :variant="challenge.progress_percentage >= 100 ? 'default' : 'secondary'">
                    {{ Math.round(challenge.progress_percentage) }}%
                  </Badge>
                </div>
                <Progress :model-value="challenge.progress_percentage" />
              </CardContent>
            </Card>

            <Button variant="outline" class="w-full" @click="goToChallenges">
              <Plus class="w-4 h-4 mr-2" />
              Create Challenge
            </Button>
          </div>
        </section>
      </div>

      <!-- Reading Lists -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <List class="w-6 h-6 text-primary" />
            My Lists
          </h2>
          <Button variant="ghost" @click="goToLists">
            View All
            <ArrowRight class="w-4 h-4 ml-2" />
          </Button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card 
            v-for="list in readingLists" 
            :key="list.id"
            class="hover:shadow-lg transition-shadow cursor-pointer"
            @click="goToLists"
          >
            <CardContent class="p-6">
              <div class="flex items-center justify-between mb-2">
                <List class="w-5 h-5 text-muted-foreground" />
                <Badge variant="secondary">{{ list.books_count }} books</Badge>
              </div>
              <h3 class="font-semibold">{{ list.title }}</h3>
            </CardContent>
          </Card>

          <Card class="border-dashed hover:border-primary transition-colors cursor-pointer" @click="goToLists">
            <CardContent class="p-6 flex flex-col items-center justify-center h-full text-muted-foreground hover:text-primary transition-colors">
              <Plus class="w-8 h-8 mb-2" />
              <p class="text-sm font-medium">Create New List</p>
            </CardContent>
          </Card>
        </div>
      </section>

      <!-- Friend Activity / Feed -->
      <section>
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <TrendingUp class="w-6 h-6 text-primary" />
            Friend Activity
          </h2>
          <Button variant="ghost" @click="goToFeed">
            View All
            <ArrowRight class="w-4 h-4 ml-2" />
          </Button>
        </div>

        <Card class="hover:shadow-lg transition-shadow cursor-pointer" @click="goToFeed">
          <CardContent class="p-8 text-center">
            <TrendingUp class="w-12 h-12 text-primary mx-auto mb-3" />
            <h3 class="font-semibold text-lg mb-2">See What Friends Are Reading</h3>
            <p class="text-muted-foreground mb-4 max-w-md mx-auto">
              Stay updated with your friends' reading activity, quotes, and recommendations
            </p>
            <Button size="lg">
              Open Activity Feed
              <ArrowRight class="w-4 h-4 ml-2" />
            </Button>
          </CardContent>
        </Card>
      </section>
    </div>
  </div>
</template>