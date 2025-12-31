<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { User, Settings, BookOpen, Quote, Target, List as ListIcon, Mail, MapPin, Globe, Edit2, Save } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const isEditing = ref(false)
const profileForm = ref({
  first_name: '',
  last_name: '',
  bio: '',
  location: '',
  website: '',
})

onMounted(() => {
  if (authStore.user) {
    profileForm.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      bio: authStore.user.bio || '',
      location: authStore.user.location || '',
      website: authStore.user.website || '',
    }
  }
})

const initials = computed(() => {
  if (!authStore.user) return 'U'
  const first = authStore.user.first_name?.[0] || ''
  const last = authStore.user.last_name?.[0] || ''
  return (first + last).toUpperCase() || 'U'
})

const handleSaveProfile = async () => {
  const result = await authStore.updateProfile(profileForm.value)
  if (result.success) {
    isEditing.value = false
  }
}

const cancelEdit = () => {
  isEditing.value = false
  if (authStore.user) {
    profileForm.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      bio: authStore.user.bio || '',
      location: authStore.user.location || '',
      website: authStore.user.website || '',
    }
  }
}

// Mock stats (replace with real data)
const stats = ref({
  totalBooks: 42,
  booksRead: 28,
  currentlyReading: 3,
  quotes: 156,
  lists: 8,
  challenges: 2,
})
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- Header -->
    <div class="border-b bg-card">
      <div class="container mx-auto px-4 py-6">
        <div class="flex items-center gap-6">
          <Avatar class="w-24 h-24">
            <AvatarImage :src="authStore.user?.avatar" />
            <AvatarFallback class="text-2xl">{{ initials }}</AvatarFallback>
          </Avatar>
          
          <div class="flex-1">
            <h1 class="text-3xl font-bold">{{ authStore.user?.full_name }}</h1>
            <p class="text-muted-foreground flex items-center gap-2 mt-1">
              <Mail class="w-4 h-4" />
              {{ authStore.user?.email }}
            </p>
          </div>

          <Button 
            v-if="!isEditing"
            @click="isEditing = true"
          >
            <Edit2 class="w-4 h-4 mr-2" />
            Edit Profile
          </Button>
        </div>
      </div>
    </div>

    <div class="container mx-auto px-4 py-8">
      <Tabs default-value="profile" class="space-y-6">
        <TabsList class="grid w-full grid-cols-3 max-w-md">
          <TabsTrigger value="profile">
            <User class="w-4 h-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="stats">
            <BookOpen class="w-4 h-4 mr-2" />
            Stats
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings class="w-4 h-4 mr-2" />
            Settings
          </TabsTrigger>
        </TabsList>

        <!-- Profile Tab -->
        <TabsContent value="profile" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                {{ isEditing ? 'Update your personal information' : 'Your personal information' }}
              </CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="first_name">First Name</Label>
                  <Input
                    id="first_name"
                    v-model="profileForm.first_name"
                    :disabled="!isEditing"
                  />
                </div>
                <div class="space-y-2">
                  <Label for="last_name">Last Name</Label>
                  <Input
                    id="last_name"
                    v-model="profileForm.last_name"
                    :disabled="!isEditing"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <Label for="bio">Bio</Label>
                <Textarea
                  id="bio"
                  v-model="profileForm.bio"
                  rows="4"
                  placeholder="Tell us about yourself..."
                  :disabled="!isEditing"
                />
              </div>

              <div class="space-y-2">
                <Label for="location">Location</Label>
                <div class="relative">
                  <MapPin class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="location"
                    v-model="profileForm.location"
                    placeholder="City, Country"
                    class="pl-10"
                    :disabled="!isEditing"
                  />
                </div>
              </div>

              <div class="space-y-2">
                <Label for="website">Website</Label>
                <div class="relative">
                  <Globe class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="website"
                    v-model="profileForm.website"
                    placeholder="https://yourwebsite.com"
                    class="pl-10"
                    :disabled="!isEditing"
                  />
                </div>
              </div>

              <div v-if="isEditing" class="flex justify-end gap-2 pt-4">
                <Button variant="outline" @click="cancelEdit">
                  Cancel
                </Button>
                <Button @click="handleSaveProfile">
                  <Save class="w-4 h-4 mr-2" />
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <!-- Stats Tab -->
        <TabsContent value="stats" class="space-y-6">
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card>
              <CardContent class="p-6 text-center">
                <BookOpen class="w-8 h-8 text-primary mx-auto mb-2" />
                <p class="text-3xl font-bold">{{ stats.totalBooks }}</p>
                <p class="text-sm text-muted-foreground">Total Books</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-6 text-center">
                <BookOpen class="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p class="text-3xl font-bold text-green-600">{{ stats.booksRead }}</p>
                <p class="text-sm text-muted-foreground">Books Read</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-6 text-center">
                <BookOpen class="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <p class="text-3xl font-bold text-blue-600">{{ stats.currentlyReading }}</p>
                <p class="text-sm text-muted-foreground">Currently Reading</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-6 text-center">
                <Quote class="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <p class="text-3xl font-bold text-purple-600">{{ stats.quotes }}</p>
                <p class="text-sm text-muted-foreground">Quotes Saved</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-6 text-center">
                <ListIcon class="w-8 h-8 text-orange-600 mx-auto mb-2" />
                <p class="text-3xl font-bold text-orange-600">{{ stats.lists }}</p>
                <p class="text-sm text-muted-foreground">Reading Lists</p>
              </CardContent>
            </Card>

            <Card>
              <CardContent class="p-6 text-center">
                <Target class="w-8 h-8 text-red-600 mx-auto mb-2" />
                <p class="text-3xl font-bold text-red-600">{{ stats.challenges }}</p>
                <p class="text-sm text-muted-foreground">Active Challenges</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <!-- Settings Tab -->
        <TabsContent value="settings" class="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Privacy Settings</CardTitle>
              <CardDescription>Control who can see your reading activity</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Public Profile</p>
                  <p class="text-sm text-muted-foreground">Make your profile visible to everyone</p>
                </div>
                <input type="checkbox" class="rounded" />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Show Reading Stats</p>
                  <p class="text-sm text-muted-foreground">Display your reading statistics</p>
                </div>
                <input type="checkbox" class="rounded" checked />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Show Quotes</p>
                  <p class="text-sm text-muted-foreground">Allow others to see your saved quotes</p>
                </div>
                <input type="checkbox" class="rounded" checked />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>Choose what updates you want to receive</CardDescription>
            </CardHeader>
            <CardContent class="space-y-4">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Email Notifications</p>
                  <p class="text-sm text-muted-foreground">Receive updates via email</p>
                </div>
                <input type="checkbox" class="rounded" checked />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Friend Requests</p>
                  <p class="text-sm text-muted-foreground">Get notified of new friend requests</p>
                </div>
                <input type="checkbox" class="rounded" checked />
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium">Circle Invitations</p>
                  <p class="text-sm text-muted-foreground">Notifications for circle invites</p>
                </div>
                <input type="checkbox" class="rounded" checked />
              </div>
            </CardContent>
          </Card>

          <Card class="border-destructive">
            <CardHeader>
              <CardTitle class="text-destructive">Danger Zone</CardTitle>
              <CardDescription>Irreversible actions</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="destructive">
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  </div>
</template>