<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { 
  Heart,
  MessageCircle,
  Share2,
  BookOpen,
  Quote,
  Star,
  Target,
  List,
  Users,
  TrendingUp,
  Sparkles
} from 'lucide-vue-next'

const router = useRouter()

const activities = ref([])
const loading = ref(true)

onMounted(async () => {
  await loadFeed()
})

const loadFeed = async () => {
  loading.value = true
  
  // Mock activity feed data
  activities.value = [
    {
      id: 1,
      type: 'book_finished',
      user: {
        id: 1,
        full_name: 'Sarah Johnson',
        avatar: null,
      },
      book: {
        id: 1,
        title: 'Atomic Habits',
        cover_image: null,
        authors: [{ name: 'James Clear' }],
      },
      rating: 5,
      review: 'Absolutely life-changing! The concept of tiny habits compounding over time is brilliant.',
      timestamp: '2024-03-20T14:30:00Z',
      likes_count: 24,
      comments_count: 8,
      is_liked: false,
    },
    {
      id: 2,
      type: 'quote_added',
      user: {
        id: 2,
        full_name: 'Michael Chen',
        avatar: null,
      },
      book: {
        id: 2,
        title: 'Meditations',
        authors: [{ name: 'Marcus Aurelius' }],
      },
      quote: {
        text: 'You have power over your mind - not outside events. Realize this, and you will find strength.',
        page_number: 42,
      },
      timestamp: '2024-03-20T12:15:00Z',
      likes_count: 47,
      comments_count: 12,
      is_liked: true,
    },
    {
      id: 3,
      type: 'challenge_completed',
      user: {
        id: 3,
        full_name: 'Emma Williams',
        avatar: null,
      },
      challenge: {
        title: '2024 Reading Challenge',
        target_books: 50,
        completed_books: 50,
      },
      timestamp: '2024-03-20T10:00:00Z',
      likes_count: 156,
      comments_count: 23,
      is_liked: false,
    },
    {
      id: 4,
      type: 'list_created',
      user: {
        id: 4,
        full_name: 'David Park',
        avatar: null,
      },
      list: {
        id: 1,
        title: 'Best Sci-Fi of 2024',
        books_count: 12,
      },
      timestamp: '2024-03-19T18:45:00Z',
      likes_count: 34,
      comments_count: 5,
      is_liked: false,
    },
    {
      id: 5,
      type: 'reading_session',
      user: {
        id: 5,
        full_name: 'Lisa Anderson',
        avatar: null,
      },
      book: {
        id: 3,
        title: 'The Midnight Library',
        cover_image: null,
      },
      session: {
        duration: '2h 15m',
        pages_read: 87,
      },
      timestamp: '2024-03-19T16:30:00Z',
      likes_count: 12,
      comments_count: 3,
      is_liked: false,
    },
  ]

  loading.value = false
}

const getActivityIcon = (type) => {
  const icons = {
    book_finished: Star,
    quote_added: Quote,
    challenge_completed: Target,
    list_created: List,
    reading_session: BookOpen,
    joined_circle: Users,
  }
  return icons[type] || Sparkles
}

const getActivityColor = (type) => {
  const colors = {
    book_finished: 'text-yellow-500',
    quote_added: 'text-purple-500',
    challenge_completed: 'text-green-500',
    list_created: 'text-blue-500',
    reading_session: 'text-orange-500',
    joined_circle: 'text-pink-500',
  }
  return colors[type] || 'text-primary'
}

const getActivityTitle = (activity) => {
  const titles = {
    book_finished: 'finished reading',
    quote_added: 'saved a quote from',
    challenge_completed: 'completed a challenge',
    list_created: 'created a new list',
    reading_session: 'just read',
    joined_circle: 'joined a circle',
  }
  return titles[activity.type] || 'posted'
}

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const handleLike = (activity) => {
  activity.is_liked = !activity.is_liked
  activity.likes_count += activity.is_liked ? 1 : -1
}

const goToBook = (bookId) => {
  router.push(`/books/${bookId}`)
}

const goToProfile = (userId) => {
  router.push(`/users/${userId}`)
}

const initials = (name) => {
  return name.split(' ').map(n => n[0]).join('').toUpperCase()
}
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="border-b bg-card">
      <div class="container mx-auto px-4 py-6">
        <div class="flex items-center gap-3">
          <TrendingUp class="w-8 h-8 text-primary" />
          <div>
            <h1 class="text-3xl font-bold">Activity Feed</h1>
            <p class="text-muted-foreground">See what your friends are reading</p>
          </div>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-8 max-w-3xl">
      <!-- Loading State -->
      <div v-if="loading" class="space-y-6">
        <Skeleton v-for="i in 5" :key="i" class="h-48" />
      </div>

      <!-- Activity Cards -->
      <div v-else class="space-y-6">
        <Card
          v-for="activity in activities"
          :key="activity.id"
          class="hover:shadow-lg transition-shadow"
        >
          <CardHeader class="pb-3">
            <div class="flex items-start gap-3">
              <!-- User Avatar -->
              <Avatar 
                class="cursor-pointer"
                @click="goToProfile(activity.user.id)"
              >
                <AvatarImage :src="activity.user.avatar" />
                <AvatarFallback>{{ initials(activity.user.full_name) }}</AvatarFallback>
              </Avatar>

              <!-- Activity Header -->
              <div class="flex-1">
                <div class="flex items-center gap-2 flex-wrap">
                  <button
                    @click="goToProfile(activity.user.id)"
                    class="font-semibold hover:text-primary"
                  >
                    {{ activity.user.full_name }}
                  </button>
                  <span class="text-muted-foreground">{{ getActivityTitle(activity) }}</span>
                  
                  <component 
                    :is="getActivityIcon(activity.type)" 
                    :class="getActivityColor(activity.type)"
                    class="w-4 h-4"
                  />
                </div>
                <p class="text-xs text-muted-foreground">
                  {{ formatTimestamp(activity.timestamp) }}
                </p>
              </div>
            </div>
          </CardHeader>

          <CardContent class="space-y-4">
            <!-- Book Finished Activity -->
            <div v-if="activity.type === 'book_finished'" class="space-y-3">
              <div 
                class="flex gap-4 cursor-pointer hover:bg-muted/50 p-3 rounded-lg transition-colors"
                @click="goToBook(activity.book.id)"
              >
                <div class="w-16 h-24 bg-muted rounded overflow-hidden flex-shrink-0">
                  <img
                    v-if="activity.book.cover_image"
                    :src="activity.book.cover_image"
                    :alt="activity.book.title"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div>
                  <h3 class="font-semibold">{{ activity.book.title }}</h3>
                  <p class="text-sm text-muted-foreground">
                    {{ activity.book.authors.map(a => a.name).join(', ') }}
                  </p>
                  <div v-if="activity.rating" class="flex gap-1 mt-2">
                    <Star
                      v-for="i in 5"
                      :key="i"
                      :class="i <= activity.rating ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'"
                      class="w-4 h-4"
                    />
                  </div>
                </div>
              </div>
              <p v-if="activity.review" class="text-sm">
                {{ activity.review }}
              </p>
            </div>

            <!-- Quote Activity -->
            <div v-if="activity.type === 'quote_added'" class="space-y-3">
              <blockquote class="text-sm italic border-l-4 border-primary pl-4 py-2">
                "{{ activity.quote.text }}"
              </blockquote>
              <div class="flex items-center justify-between text-xs text-muted-foreground">
                <button 
                  @click="goToBook(activity.book.id)"
                  class="hover:text-primary font-medium"
                >
                  {{ activity.book.title }}
                </button>
                <span>Page {{ activity.quote.page_number }}</span>
              </div>
            </div>

            <!-- Challenge Completed -->
            <div v-if="activity.type === 'challenge_completed'" class="space-y-2">
              <div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 p-4 rounded-lg">
                <div class="flex items-center gap-3 mb-2">
                  <Target class="w-6 h-6 text-green-600" />
                  <h3 class="font-semibold">{{ activity.challenge.title }}</h3>
                </div>
                <p class="text-2xl font-bold text-green-600">
                  {{ activity.challenge.completed_books }} / {{ activity.challenge.target_books }} books
                </p>
                <Badge variant="default" class="mt-2">Completed! 🎉</Badge>
              </div>
            </div>

            <!-- List Created -->
            <div v-if="activity.type === 'list_created'" class="space-y-2">
              <div class="bg-muted/50 p-4 rounded-lg">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <List class="w-5 h-5 text-primary" />
                    <h3 class="font-semibold">{{ activity.list.title }}</h3>
                  </div>
                  <Badge variant="secondary">{{ activity.list.books_count }} books</Badge>
                </div>
              </div>
            </div>

            <!-- Reading Session -->
            <div v-if="activity.type === 'reading_session'" class="space-y-2">
              <div class="flex items-center gap-4 text-sm">
                <div class="flex items-center gap-2">
                  <BookOpen class="w-4 h-4 text-orange-500" />
                  <span class="font-medium">{{ activity.session.pages_read }} pages</span>
                </div>
                <div class="flex items-center gap-2">
                  <TrendingUp class="w-4 h-4 text-blue-500" />
                  <span class="font-medium">{{ activity.session.duration }}</span>
                </div>
              </div>
              <button 
                @click="goToBook(activity.book.id)"
                class="text-sm text-primary hover:underline"
              >
                {{ activity.book.title }}
              </button>
            </div>

            <!-- Interaction Buttons -->
            <div class="flex items-center gap-6 pt-3 border-t">
              <button
                @click="handleLike(activity)"
                class="flex items-center gap-2 text-sm hover:text-primary transition-colors"
                :class="activity.is_liked ? 'text-red-500' : 'text-muted-foreground'"
              >
                <Heart :class="activity.is_liked ? 'fill-current' : ''" class="w-4 h-4" />
                <span>{{ activity.likes_count }}</span>
              </button>

              <button class="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors">
                <MessageCircle class="w-4 h-4" />
                <span>{{ activity.comments_count }}</span>
              </button>

              <button class="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors">
                <Share2 class="w-4 h-4" />
                <span>Share</span>
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>