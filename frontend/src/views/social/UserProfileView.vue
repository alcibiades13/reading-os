<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'
import BookCard from '@/components/BookCard.vue'
import { 
  User,
  UserPlus,
  UserMinus,
  MapPin,
  Globe,
  Calendar,
  BookOpen,
  Quote,
  Star,
  TrendingUp,
  Heart,
  List,
  Target,
  Users
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()

const userId = route.params.id
const user = ref(null)
const loading = ref(true)
const isFollowing = ref(false)

// User's reading data
const userBooks = ref([])
const userQuotes = ref([])
const userLists = ref([])
const readingStats = ref({})

onMounted(async () => {
  await loadUserProfile()
})

const loadUserProfile = async () => {
  loading.value = true
  
  // Mock data - replace with real API calls
  user.value = {
    id: userId,
    first_name: 'Jane',
    last_name: 'Doe',
    full_name: 'Jane Doe',
    email: 'jane@example.com',
    bio: 'Passionate reader | Philosophy enthusiast | Coffee lover ☕',
    location: 'San Francisco, CA',
    website: 'https://janedoe.com',
    avatar: null,
    joined_date: '2023-01-15',
    is_public: true,
  }

  readingStats.value = {
    total_books: 156,
    books_read: 98,
    currently_reading: 4,
    quotes: 342,
    lists: 12,
    followers: 1247,
    following: 892,
    reading_streak: 28,
  }

  // Mock books
  userBooks.value = [
    { id: 1, book: { title: 'Meditations', cover_image: null }, status: 'read', rating: 5 },
    { id: 2, book: { title: 'Atomic Habits', cover_image: null }, status: 'currently_reading', rating: null },
  ]

  userQuotes.value = [
    { 
      id: 1, 
      text: 'You have power over your mind - not outside events. Realize this, and you will find strength.',
      book_title: 'Meditations',
      page_number: 42,
      created_at: '2024-03-15',
      likes_count: 24,
    },
  ]

  userLists.value = [
    { id: 1, title: 'Philosophy Classics', books_count: 18, is_public: true },
    { id: 2, title: 'Summer Reads 2024', books_count: 12, is_public: true },
  ]

  loading.value = false
}

const initials = computed(() => {
  if (!user.value) return 'U'
  const first = user.value.first_name?.[0] || ''
  const last = user.value.last_name?.[0] || ''
  return (first + last).toUpperCase() || 'U'
})

const memberSince = computed(() => {
  if (!user.value?.joined_date) return ''
  const date = new Date(user.value.joined_date)
  return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const handleFollow = async () => {
  // TODO: Call API to follow/unfollow
  isFollowing.value = !isFollowing.value
}

const goToBook = (bookId) => {
  router.push(`/books/${bookId}`)
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    year: 'numeric' 
  })
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Loading State -->
    <div v-if="loading" class="container mx-auto px-4 py-8">
      <Skeleton class="h-48 mb-6" />
      <Skeleton class="h-96" />
    </div>

    <!-- Profile Content -->
    <div v-else-if="user">
      <!-- Header Banner -->
      <div class="border-b bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950">
        <div class="container mx-auto px-4 py-8">
          <div class="flex flex-col md:flex-row items-center md:items-start gap-6">
            <!-- Avatar -->
            <Avatar class="w-32 h-32 border-4 border-background shadow-xl">
              <AvatarImage :src="user.avatar" />
              <AvatarFallback class="text-4xl">{{ initials }}</AvatarFallback>
            </Avatar>

            <!-- User Info -->
            <div class="flex-1 text-center md:text-left">
              <h1 class="text-3xl font-bold mb-2">{{ user.full_name }}</h1>
              
              <div class="flex flex-wrap items-center justify-center md:justify-start gap-4 text-sm text-muted-foreground mb-4">
                <div v-if="user.location" class="flex items-center gap-1">
                  <MapPin class="w-4 h-4" />
                  <span>{{ user.location }}</span>
                </div>
                
                <div v-if="user.website" class="flex items-center gap-1">
                  <Globe class="w-4 h-4" />
                  <a :href="user.website" target="_blank" class="hover:text-primary">
                    Website
                  </a>
                </div>
                
                <div class="flex items-center gap-1">
                  <Calendar class="w-4 h-4" />
                  <span>Joined {{ memberSince }}</span>
                </div>
              </div>

              <p v-if="user.bio" class="text-muted-foreground mb-4 max-w-2xl">
                {{ user.bio }}
              </p>

              <!-- Follow/Message Buttons -->
              <div class="flex items-center justify-center md:justify-start gap-3">
                <Button 
                  :variant="isFollowing ? 'outline' : 'default'"
                  @click="handleFollow"
                >
                  <component :is="isFollowing ? UserMinus : UserPlus" class="w-4 h-4 mr-2" />
                  {{ isFollowing ? 'Unfollow' : 'Follow' }}
                </Button>
                
                <Button variant="outline">
                  Message
                </Button>
              </div>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-3 gap-3">
              <Card class="text-center">
                <CardContent class="p-4">
                  <p class="text-2xl font-bold">{{ readingStats.total_books }}</p>
                  <p class="text-xs text-muted-foreground">Books</p>
                </CardContent>
              </Card>
              
              <Card class="text-center">
                <CardContent class="p-4">
                  <p class="text-2xl font-bold">{{ readingStats.followers }}</p>
                  <p class="text-xs text-muted-foreground">Followers</p>
                </CardContent>
              </Card>
              
              <Card class="text-center">
                <CardContent class="p-4">
                  <p class="text-2xl font-bold">{{ readingStats.following }}</p>
                  <p class="text-xs text-muted-foreground">Following</p>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      <!-- Reading Stats Overview -->
      <div class="border-b bg-card">
        <div class="container mx-auto px-4 py-6">
          <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <Card>
              <CardContent class="p-4 text-center">
                <BookOpen class="w-5 h-5 text-green-500 mx-auto mb-1" />
                <p class="text-xl font-bold">{{ readingStats.books_read }}</p>
                <p class="text-xs text-muted-foreground">Read</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <BookOpen class="w-5 h-5 text-blue-500 mx-auto mb-1" />
                <p class="text-xl font-bold">{{ readingStats.currently_reading }}</p>
                <p class="text-xs text-muted-foreground">Reading</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <Quote class="w-5 h-5 text-purple-500 mx-auto mb-1" />
                <p class="text-xl font-bold">{{ readingStats.quotes }}</p>
                <p class="text-xs text-muted-foreground">Quotes</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <List class="w-5 h-5 text-orange-500 mx-auto mb-1" />
                <p class="text-xl font-bold">{{ readingStats.lists }}</p>
                <p class="text-xs text-muted-foreground">Lists</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <Target class="w-5 h-5 text-red-500 mx-auto mb-1" />
                <p class="text-xl font-bold">3</p>
                <p class="text-xs text-muted-foreground">Challenges</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <TrendingUp class="w-5 h-5 text-yellow-500 mx-auto mb-1" />
                <p class="text-xl font-bold">{{ readingStats.reading_streak }}</p>
                <p class="text-xs text-muted-foreground">Day Streak</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-4 text-center">
                <Users class="w-5 h-5 text-pink-500 mx-auto mb-1" />
                <p class="text-xl font-bold">5</p>
                <p class="text-xs text-muted-foreground">Circles</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <!-- Content Tabs -->
      <div class="container mx-auto px-4 py-8">
        <Tabs default-value="books">
          <TabsList class="grid w-full max-w-md grid-cols-3">
            <TabsTrigger value="books">
              <BookOpen class="w-4 h-4 mr-2" />
              Books
            </TabsTrigger>
            <TabsTrigger value="quotes">
              <Quote class="w-4 h-4 mr-2" />
              Quotes
            </TabsTrigger>
            <TabsTrigger value="lists">
              <List class="w-4 h-4 mr-2" />
              Lists
            </TabsTrigger>
          </TabsList>

          <!-- Books Tab -->
          <TabsContent value="books" class="mt-6">
            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
              <BookCard
                v-for="book in userBooks"
                :key="book.id"
                :book="book"
                @view="goToBook"
              />
            </div>
          </TabsContent>

          <!-- Quotes Tab -->
          <TabsContent value="quotes" class="mt-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card
                v-for="quote in userQuotes"
                :key="quote.id"
                class="hover:shadow-lg transition-shadow"
              >
                <CardContent class="p-6">
                  <blockquote class="text-sm italic mb-4 border-l-2 border-primary pl-3">
                    "{{ quote.text }}"
                  </blockquote>
                  
                  <div class="flex items-center justify-between text-xs text-muted-foreground">
                    <div>
                      <p class="font-medium">{{ quote.book_title }}</p>
                      <p>Page {{ quote.page_number }}</p>
                    </div>
                    <div class="flex items-center gap-2">
                      <Heart class="w-4 h-4" />
                      <span>{{ quote.likes_count }}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <!-- Lists Tab -->
          <TabsContent value="lists" class="mt-6">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <Card
                v-for="list in userLists"
                :key="list.id"
                class="hover:shadow-lg transition-shadow cursor-pointer"
              >
                <CardContent class="p-6">
                  <div class="flex items-start justify-between mb-3">
                    <List class="w-5 h-5 text-primary" />
                    <Badge variant="secondary">
                      {{ list.books_count }} books
                    </Badge>
                  </div>
                  <h3 class="font-semibold text-lg">{{ list.title }}</h3>
                  <p class="text-xs text-muted-foreground mt-1">
                    {{ list.is_public ? 'Public' : 'Private' }}
                  </p>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  </div>
</template>