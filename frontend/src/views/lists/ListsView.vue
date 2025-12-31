<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useListsStore } from '@/stores/listsStore'
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { List, Plus, Search, BookOpen, Lock, Globe, Edit, Trash2, Sparkles } from 'lucide-vue-next'

const router = useRouter()
const listsStore = useListsStore()

const searchQuery = ref('')
const isCreateDialogOpen = ref(false)

// New list form
const newList = ref({
  title: '',
  description: '',
  is_smart: false,
  is_public: false,
})

onMounted(async () => {
  await listsStore.fetchLists()
})

const displayedLists = computed(() => listsStore.filteredLists)

const handleSearch = (value) => {
  listsStore.setFilter('search', value)
}

const handleCreateList = async () => {
  const result = await listsStore.createList(newList.value)
  if (result.success) {
    isCreateDialogOpen.value = false
    resetForm()
  }
}

const resetForm = () => {
  newList.value = {
    title: '',
    description: '',
    is_smart: false,
    is_public: false,
  }
}

const viewList = (list) => {
  router.push(`/lists/${list.id}`)
}

const deleteList = async (list) => {
  if (confirm(`Delete "${list.title}"?`)) {
    await listsStore.deleteList(list.id)
  }
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
    <!-- Header -->
    <div class="border-b bg-card">
      <div class="container mx-auto px-4 py-6">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <List class="w-8 h-8 text-primary" />
            <div>
              <h1 class="text-3xl font-bold">My Lists</h1>
              <p class="text-muted-foreground">Organize your reading</p>
            </div>
          </div>
          
          <Dialog v-model:open="isCreateDialogOpen">
            <DialogTrigger as-child>
              <Button size="lg">
                <Plus class="w-4 h-4 mr-2" />
                New List
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Reading List</DialogTitle>
              </DialogHeader>
              <form @submit.prevent="handleCreateList" class="space-y-4">
                <div class="space-y-2">
                  <Label for="title">List Title *</Label>
                  <Input
                    id="title"
                    v-model="newList.title"
                    placeholder="Summer Reads 2024"
                    required
                  />
                </div>

                <div class="space-y-2">
                  <Label for="description">Description</Label>
                  <Textarea
                    id="description"
                    v-model="newList.description"
                    placeholder="Books to read this summer..."
                    rows="3"
                  />
                </div>

                <div class="space-y-3">
                  <label class="flex items-start gap-3 cursor-pointer">
                    <input
                      v-model="newList.is_smart"
                      type="checkbox"
                      class="rounded mt-1"
                    />
                    <div>
                      <div class="flex items-center gap-2">
                        <Sparkles class="w-4 h-4" />
                        <span class="font-medium text-sm">Smart List</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Automatically populate based on filters
                      </p>
                    </div>
                  </label>

                  <label class="flex items-start gap-3 cursor-pointer">
                    <input
                      v-model="newList.is_public"
                      type="checkbox"
                      class="rounded mt-1"
                    />
                    <div>
                      <div class="flex items-center gap-2">
                        <Globe class="w-4 h-4" />
                        <span class="font-medium text-sm">Make Public</span>
                      </div>
                      <p class="text-xs text-muted-foreground">
                        Share this list with others
                      </p>
                    </div>
                  </label>
                </div>

                <div class="flex justify-end gap-2">
                  <Button type="button" variant="outline" @click="isCreateDialogOpen = false">
                    Cancel
                  </Button>
                  <Button type="submit">
                    Create List
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <!-- Search -->
        <div class="relative max-w-md">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            v-model="searchQuery"
            placeholder="Search lists..."
            class="pl-10"
            @input="handleSearch(searchQuery)"
          />
        </div>
      </div>
    </div>

    <!-- Lists Grid -->
    <div class="container mx-auto px-4 py-8">
      <div v-if="listsStore.loading" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Skeleton v-for="i in 6" :key="i" class="h-48" />
      </div>

      <div v-else-if="displayedLists.length === 0" class="text-center py-12">
        <List class="w-16 h-16 text-muted-foreground/30 mx-auto mb-4" />
        <h3 class="text-lg font-semibold mb-2">No lists yet</h3>
        <p class="text-muted-foreground mb-4">
          Create lists to organize your books by theme, mood, or goal
        </p>
        <Button @click="isCreateDialogOpen = true">
          <Plus class="w-4 h-4 mr-2" />
          Create Your First List
        </Button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Card
          v-for="list in displayedLists"
          :key="list.id"
          class="group hover:shadow-lg transition-all cursor-pointer"
          @click="viewList(list)"
        >
          <CardHeader>
            <div class="flex items-start justify-between mb-2">
              <div class="flex items-center gap-2">
                <Sparkles v-if="list.is_smart" class="w-4 h-4 text-purple-500" />
                <Globe v-else-if="list.is_public" class="w-4 h-4 text-blue-500" />
                <Lock v-else class="w-4 h-4 text-muted-foreground" />
              </div>
              <Badge variant="secondary">
                {{ list.books_count }} {{ list.books_count === 1 ? 'book' : 'books' }}
              </Badge>
            </div>
            
            <CardTitle class="group-hover:text-primary transition-colors">
              {{ list.title }}
            </CardTitle>
            
            <CardDescription v-if="list.description" class="line-clamp-2">
              {{ list.description }}
            </CardDescription>
          </CardHeader>

          <CardContent>
            <!-- Book preview (placeholder for now) -->
            <div v-if="list.books_count > 0" class="flex -space-x-2">
              <div
                v-for="i in Math.min(4, list.books_count)"
                :key="i"
                class="w-10 h-14 bg-gradient-to-br from-primary/20 to-primary/10 rounded border-2 border-background"
              >
              </div>
              <div
                v-if="list.books_count > 4"
                class="w-10 h-14 bg-muted rounded border-2 border-background flex items-center justify-center text-xs font-medium"
              >
                +{{ list.books_count - 4 }}
              </div>
            </div>
            <div v-else class="text-sm text-muted-foreground italic">
              Empty list
            </div>
          </CardContent>

          <CardFooter class="flex justify-between items-center border-t pt-4">
            <span class="text-xs text-muted-foreground">
              Updated {{ formatDate(list.updated_at) }}
            </span>
            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
              <Button variant="ghost" size="sm">
                <Edit class="w-3 h-3" />
              </Button>
              <Button variant="ghost" size="sm" @click="deleteList(list)">
                <Trash2 class="w-3 h-3 text-destructive" />
              </Button>
            </div>
          </CardFooter>
        </Card>

        <!-- Create new list card -->
        <Card
          class="border-dashed hover:border-primary transition-colors cursor-pointer"
          @click="isCreateDialogOpen = true"
        >
          <CardContent class="flex flex-col items-center justify-center h-full min-h-[240px] text-muted-foreground hover:text-primary transition-colors">
            <Plus class="w-12 h-12 mb-3" />
            <p class="font-medium">Create New List</p>
          </CardContent>
        </Card>
      </div>
    </div>
  </div>
</template>