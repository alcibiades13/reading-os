<script setup>
import { ref, computed, onMounted } from 'vue'
import { useChallengesStore } from '@/stores/challengesStore'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { Target, Plus, Calendar, TrendingUp, Award, Edit, Trash2, Play, Pause } from 'lucide-vue-next'

const challengesStore = useChallengesStore()

const isCreateDialogOpen = ref(false)
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
  if (percentage >= 100) return 'text-green-600'
  if (percentage >= 75) return 'text-blue-600'
  if (percentage >= 50) return 'text-yellow-600'
  return 'text-orange-600'
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
  <div class="min-h-screen bg-slate-950">
    <!-- Header -->
    <div class="border-b border-slate-800 bg-slate-900/50">
      <div class="container mx-auto px-4 py-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <Target class="w-8 h-8 text-primary" />
            <div>
              <h1 class="text-3xl font-bold">Reading Challenges</h1>
              <p class="text-muted-foreground">Track your reading goals</p>
            </div>
          </div>
          
          <Dialog v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <Button size="lg">
                <Plus class="w-4 h-4 mr-2" />
                New Challenge
              </Button>
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
                    placeholder="2024 Reading Challenge"
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
                  <Button type="button" variant="outline" @click="isCreateDialogOpen = false">
                    Cancel
                  </Button>
                  <Button type="submit">
                    Create Challenge
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-8 space-y-8">
      <!-- Active Challenges -->
      <section v-if="activeChallenges.length > 0">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <Play class="w-6 h-6 text-green-600" />
            Active Challenges
          </h2>
          <Badge variant="default">{{ activeChallenges.length }}</Badge>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card
            v-for="challenge in activeChallenges"
            :key="challenge.id"
            class="hover:shadow-lg transition-shadow"
          >
            <CardHeader>
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <CardTitle class="text-lg mb-1">{{ challenge.title }}</CardTitle>
                  <CardDescription class="line-clamp-2">
                    {{ challenge.description || 'No description' }}
                  </CardDescription>
                </div>
                <Badge :variant="challenge.is_completed ? 'default' : 'secondary'">
                  {{ challenge.is_completed ? 'Completed' : 'In Progress' }}
                </Badge>
              </div>
            </CardHeader>

            <CardContent class="space-y-4">
              <!-- Progress -->
              <div class="space-y-2">
                <div class="flex justify-between items-center">
                  <span class="text-2xl font-bold" :class="getProgressColor(challenge.progress_percentage || 0)">
                    {{ challenge.completed_books || 0 }}
                  </span>
                  <span class="text-sm text-muted-foreground">
                    / {{ challenge.target_books || 0 }} books
                  </span>
                </div>
                <Progress :model-value="challenge.progress_percentage || 0" class="h-3" />
                <div class="flex justify-between text-xs text-muted-foreground">
                  <span>{{ Math.round(challenge.progress_percentage || 0) }}% complete</span>
                  <span v-if="(challenge.target_books || 0) - (challenge.completed_books || 0) > 0">
                    {{ (challenge.target_books || 0) - (challenge.completed_books || 0) }} to go
                  </span>
                </div>
              </div>

              <!-- Dates -->
              <div class="flex items-center gap-2 text-xs text-muted-foreground">
                <Calendar class="w-3 h-3" />
                <span>{{ formatDate(challenge.start_date) }} - {{ formatDate(challenge.end_date) }}</span>
              </div>

              <!-- Filters -->
              <div v-if="challenge.min_pages" class="text-xs text-muted-foreground">
                Min {{ challenge.min_pages }} pages per book
              </div>
            </CardContent>

            <CardFooter class="flex justify-between gap-2 border-t pt-4">
              <div class="flex gap-1">
                <Button variant="ghost" size="sm" @click="toggleActive(challenge)">
                  <Pause class="w-3 h-3" />
                </Button>
                <Button variant="ghost" size="sm" @click="refreshProgress(challenge)">
                  <TrendingUp class="w-3 h-3" />
                </Button>
              </div>
              <div class="flex gap-1">
                <Button variant="ghost" size="sm">
                  <Edit class="w-3 h-3" />
                </Button>
                <Button variant="ghost" size="sm" @click="deleteChallenge(challenge)">
                  <Trash2 class="w-3 h-3 text-destructive" />
                </Button>
              </div>
            </CardFooter>
          </Card>
        </div>
      </section>

      <!-- Completed Challenges -->
      <section v-if="completedChallenges.length > 0">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-2xl font-bold flex items-center gap-2">
            <Award class="w-6 h-6 text-yellow-600" />
            Completed Challenges
          </h2>
          <Badge variant="outline">{{ completedChallenges.length }}</Badge>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card
            v-for="challenge in completedChallenges"
            :key="challenge.id"
            class="hover:shadow-md transition-shadow bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950"
          >
            <CardContent class="p-6">
              <Award class="w-8 h-8 text-yellow-600 mb-3" />
              <h3 class="font-semibold mb-1">{{ challenge.title }}</h3>
              <p class="text-2xl font-bold text-green-600">
                {{ challenge.completed_books || 0 }}/{{ challenge.target_books || 0 }}
              </p>
              <p class="text-xs text-muted-foreground mt-2">
                Completed {{ formatDate(challenge.end_date) }}
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      <!-- Empty State -->
      <div v-if="activeChallenges.length === 0 && completedChallenges.length === 0" class="text-center py-12">
        <Target class="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
        <h3 class="text-lg font-semibold mb-2">No challenges yet</h3>
        <p class="text-muted-foreground mb-4">
          Set a reading goal to stay motivated!
        </p>
        <Button @click="isCreateDialogOpen = true">
          <Plus class="w-4 h-4 mr-2" />
          Create Your First Challenge
        </Button>
      </div>
    </div>
  </div>
</template>