<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import api from '@/services/api'
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
const error = ref(null)
const userBooks = ref([])

onMounted(async () => {
  await loadFeed()
  await loadUserBooks()
})

const loadUserBooks = async () => {
  try {
    const response = await api.get('/reading/user-books/')
    userBooks.value = response.data?.results || response.data || []
  } catch (err) {
    console.error('Failed to load user books:', err)
  }
}

const loadFeed = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await api.get('/social/feed/')
    console.log('Feed API response:', response.data)

    // DRF returns paginated results
    const feedData = response.data?.results || response.data || []

    // Transform API data to match expected format
    activities.value = feedData.map(item => ({
      id: item.id,
      type: item.feed_type,
      user: {
        id: item.actor.id,
        full_name: `${item.actor.first_name} ${item.actor.last_name}`,
        avatar: item.actor.avatar,
      },
      book: item.book_data || null,
      quote: item.feed_type === 'quote_added' ? {
        text: item.preview_text,
        page_number: null,
      } : null,
      rating: null,
      review: item.review_data || null,
      timestamp: item.created_at,
      likes_count: 0,
      comments_count: 0,
      is_liked: false,
      preview_text: item.preview_text,
      preview_image: item.preview_image,
    }))

    loading.value = false
  } catch (err) {
    console.error('Feed error:', err)
    error.value = 'Failed to load activity feed'
    loading.value = false
  }
}

const getActivityIcon = (type) => {
  const icons = {
    book_finished: Star,
    quote_added: Quote,
    challenge_completed: Target,
    list_created: List,
    reading_session: BookOpen,
    progress_update: TrendingUp,
    book_started: BookOpen,
    want_to_read: Heart,
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
    progress_update: 'text-amber-500',
    book_started: 'text-indigo-500',
    want_to_read: 'text-rose-500',
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
    progress_update: 'made progress on',
    book_started: 'started reading',
    want_to_read: 'wants to read',
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

const getUserBookStatus = (bookId) => {
  if (!bookId) return null
  const userBook = userBooks.value.find(ub => ub.book?.id === bookId)
  return userBook?.status || null
}

const getStatusLabel = (status) => {
  const labels = {
    'currently_reading': 'Currently Reading',
    'read': 'Finished',
    'want_to_read': 'Want to Read',
    'abandoned': 'Abandoned'
  }
  return labels[status] || status
}

const getStatusVariant = (status) => {
  const variants = {
    'currently_reading': 'default',
    'read': 'secondary',
    'want_to_read': 'outline',
    'abandoned': 'destructive'
  }
  return variants[status] || 'outline'
}

const addToLibrary = async (bookId, status) => {
  if (!bookId) return

  try {
    const response = await api.post('/reading/user-books/', {
      book: bookId,
      status: status
    })

    // Add to local userBooks array
    if (response.data) {
      userBooks.value.push(response.data)
    }
  } catch (err) {
    console.error('Failed to add book to library:', err)
  }
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

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-12">
        <div class="text-red-500 mb-4">
          <TrendingUp class="w-12 h-12 mx-auto mb-2" />
          <p class="text-lg font-semibold">{{ error }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="activities.length === 0" class="text-center py-12">
        <div class="text-muted-foreground mb-4">
          <Sparkles class="w-12 h-12 mx-auto mb-2" />
          <p class="text-lg font-semibold">No activity yet</p>
          <p class="text-sm mt-2">Start following users to see their reading activity here!</p>
        </div>
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
                <AvatarImage v-if="activity.user.avatar" :src="activity.user.avatar" />
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
                @click="activity.book && goToBook(activity.book.id)"
              >
                <div v-if="activity.preview_image" class="w-16 h-24 bg-muted rounded overflow-hidden flex-shrink-0">
                  <img
                    :src="activity.preview_image"
                    :alt="activity.book?.title"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div>
                  <h3 v-if="activity.book" class="font-semibold">{{ activity.book.title }}</h3>
                  <p v-if="activity.book?.authors?.length" class="text-sm text-muted-foreground">
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
                "{{ activity.quote?.text || activity.preview_text }}"
              </blockquote>
              <div v-if="activity.book" class="flex items-center justify-between text-xs text-muted-foreground">
                <button
                  @click="goToBook(activity.book.id)"
                  class="hover:text-primary font-medium"
                >
                  {{ activity.book.title }}
                </button>
                <span v-if="activity.quote?.page_number">Page {{ activity.quote.page_number }}</span>
              </div>
            </div>

            <!-- Challenge Completed -->
            <div v-if="activity.type === 'challenge_completed'" class="space-y-2">
              <div class="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 p-4 rounded-lg">
                <div class="flex items-center gap-3 mb-2">
                  <Target class="w-6 h-6 text-green-600" />
                  <h3 v-if="activity.challenge" class="font-semibold">{{ activity.challenge.title }}</h3>
                </div>
                <p v-if="activity.challenge" class="text-2xl font-bold text-green-600">
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
                    <h3 v-if="activity.list" class="font-semibold">{{ activity.list.title }}</h3>
                  </div>
                  <Badge v-if="activity.list" variant="secondary">{{ activity.list.books_count }} books</Badge>
                </div>
              </div>
            </div>

            <!-- Reading Session / Progress Update -->
            <div v-if="activity.type === 'reading_session' || activity.type === 'progress_update'" class="space-y-2">
              <div v-if="activity.session" class="flex items-center gap-4 text-sm">
                <div v-if="activity.session.pages_read" class="flex items-center gap-2">
                  <BookOpen class="w-4 h-4 text-orange-500" />
                  <span class="font-medium">{{ activity.session.pages_read }} pages</span>
                </div>
                <div v-if="activity.session.duration" class="flex items-center gap-2">
                  <TrendingUp class="w-4 h-4 text-blue-500" />
                  <span class="font-medium">{{ activity.session.duration }}</span>
                </div>
              </div>
              <div v-if="activity.preview_text" class="text-sm">
                {{ activity.preview_text }}
              </div>
              <button
                v-if="activity.book"
                @click="goToBook(activity.book.id)"
                class="text-sm text-primary hover:underline"
              >
                {{ activity.book.title }}
              </button>
            </div>

            <!-- Book Started / Want to Read -->
            <div v-if="activity.type === 'book_started' || activity.type === 'want_to_read'" class="space-y-3">
              <div class="flex gap-4 p-3 rounded-lg bg-muted/30">
                <div
                  v-if="activity.preview_image"
                  class="w-16 h-24 bg-muted rounded overflow-hidden flex-shrink-0 cursor-pointer hover:opacity-80 transition-opacity"
                  @click="activity.book && goToBook(activity.book.id)"
                >
                  <img
                    :src="activity.preview_image"
                    :alt="activity.book?.title"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-1 flex flex-col justify-between">
                  <div>
                    <h3
                      class="font-semibold text-base mb-1 cursor-pointer hover:text-primary transition-colors"
                      @click="activity.book && goToBook(activity.book.id)"
                    >
                      {{ activity.book?.title || 'Unknown Book' }}
                    </h3>
                    <p v-if="activity.book?.authors?.length" class="text-sm text-muted-foreground mb-3">
                      {{ activity.book.authors.map(a => a.name).join(', ') }}
                    </p>
                  </div>
                  <!-- Status Badge or Want to Read Button -->
                  <div class="flex items-center gap-2">
                    <Badge
                      v-if="getUserBookStatus(activity.book?.id)"
                      :variant="getStatusVariant(getUserBookStatus(activity.book?.id))"
                      class="text-xs"
                    >
                      {{ getStatusLabel(getUserBookStatus(activity.book?.id)) }}
                    </Badge>
                    <button
                      v-else
                      @click.stop="addToLibrary(activity.book?.id, 'want_to_read')"
                      class="px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary text-xs font-semibold hover:bg-primary hover:text-primary-foreground transition-all"
                    >
                      Want to Read
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Generic preview text for other types -->
            <div v-if="!['book_finished', 'quote_added', 'challenge_completed', 'list_created', 'reading_session', 'progress_update', 'book_started', 'want_to_read'].includes(activity.type) && activity.preview_text" class="space-y-2">
              <p class="text-sm">{{ activity.preview_text }}</p>
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
