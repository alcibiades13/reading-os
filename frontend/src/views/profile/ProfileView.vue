<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useQuotesStore } from '@/stores/quotesStore'
import { User, BookOpen, Quote, Target, Mail, MapPin, Globe, Edit2, Save, X, Calendar, Camera } from 'lucide-vue-next'

const authStore = useAuthStore()
const booksStore = useUserBooksStore()
const quotesStore = useQuotesStore()

const isEditing = ref(false)
const avatarFile = ref(null)
const avatarPreview = ref(null)
const profileForm = ref({
  first_name: '',
  last_name: '',
  bio: '',
  location: '',
  website: '',
  birth_date: '',
})

onMounted(async () => {
  if (authStore.user) {
    profileForm.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      bio: authStore.user.bio || '',
      location: authStore.user.location || '',
      website: authStore.user.website || '',
      birth_date: authStore.user.birth_date || '',
    }
    avatarPreview.value = authStore.user.avatar || null
  }

  // Fetch real stats
  await Promise.all([
    booksStore.fetchBooks(),
    quotesStore.fetchQuotes()
  ])
})

const handleAvatarChange = (event) => {
  const file = event.target.files[0]
  if (file) {
    avatarFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      avatarPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  }
}

const initials = computed(() => {
  if (!authStore.user) return 'U'
  const first = authStore.user.first_name?.[0] || ''
  const last = authStore.user.last_name?.[0] || ''
  return (first + last).toUpperCase() || authStore.user.username?.[0]?.toUpperCase() || 'U'
})

const stats = computed(() => ({
  totalBooks: booksStore.books?.length || 0,
  booksRead: booksStore.books?.filter(b => b.status === 'read').length || 0,
  currentlyReading: booksStore.books?.filter(b => b.status === 'currently_reading').length || 0,
  wantToRead: booksStore.books?.filter(b => b.status === 'want_to_read').length || 0,
  quotes: quotesStore.quotes?.length || 0,
}))

const handleSaveProfile = async () => {
  const formData = new FormData()

  // Add text fields
  Object.keys(profileForm.value).forEach(key => {
    if (profileForm.value[key]) {
      formData.append(key, profileForm.value[key])
    }
  })

  // Add avatar if changed
  if (avatarFile.value) {
    formData.append('avatar', avatarFile.value)
  }

  const result = await authStore.updateProfile(formData)
  if (result.success) {
    isEditing.value = false
    avatarFile.value = null
  }
}

const cancelEdit = () => {
  isEditing.value = false
  avatarFile.value = null
  if (authStore.user) {
    profileForm.value = {
      first_name: authStore.user.first_name || '',
      last_name: authStore.user.last_name || '',
      bio: authStore.user.bio || '',
      location: authStore.user.location || '',
      website: authStore.user.website || '',
      birth_date: authStore.user.birth_date || '',
    }
    avatarPreview.value = authStore.user.avatar || null
  }
}
</script>

<template>
  <div class="animate-in fade-in duration-700 pb-20">
    <!-- Page Header -->
    <div class="max-w-5xl mx-auto pt-12 pb-8 px-6">
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-12">
        <header>
          <div class="flex items-center gap-2 sm:gap-3 mb-4">
            <div class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <User class="text-indigo-400" :size="18" />
            </div>
            <span class="text-page-meta font-bold text-indigo-400 uppercase tracking-[0.2em] sm:tracking-[0.3em]">Personal Profile</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-4">
            Your <span class="text-indigo-500">Reading</span> Journey
          </h1>
          <p class="text-page-subtitle text-slate-400 max-w-2xl leading-relaxed">
            Track your progress, manage your profile, and see how far you've come on your literary adventure.
          </p>
        </header>
      </div>

      <!-- Profile Section -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Profile Info Card -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Avatar & Basic Info -->
          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 sm:p-8">
            <div class="flex flex-col sm:flex-row items-start sm:items-center gap-6 mb-8">
              <!-- Avatar -->
              <div class="relative flex-shrink-0">
                <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-2xl bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center overflow-hidden">
                  <img
                    v-if="avatarPreview"
                    :src="avatarPreview"
                    alt="Avatar"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="text-2xl sm:text-3xl font-black text-indigo-400">{{ initials }}</span>
                </div>
                <button
                  v-if="isEditing"
                  @click="$refs.avatarInput.click()"
                  class="absolute -bottom-2 -right-2 w-8 h-8 rounded-lg bg-indigo-500 text-white flex items-center justify-center hover:bg-indigo-400 transition-all shadow-lg"
                >
                  <Camera :size="16" />
                </button>
                <input
                  ref="avatarInput"
                  type="file"
                  accept="image/*"
                  @change="handleAvatarChange"
                  class="hidden"
                />
              </div>

              <div class="flex-1 min-w-0">
                <h2 class="text-2xl sm:text-3xl font-black text-white mb-2">
                  {{ authStore.user?.first_name || authStore.user?.last_name
                    ? `${authStore.user.first_name} ${authStore.user.last_name}`.trim()
                    : authStore.user?.username }}
                </h2>
                <p class="text-slate-400 text-sm flex items-center gap-2">
                  <Mail :size="14" />
                  {{ authStore.user?.email }}
                </p>
              </div>

              <button
                v-if="!isEditing"
                @click="isEditing = true"
                class="px-4 py-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-sm font-bold hover:bg-indigo-500/20 transition-all flex items-center gap-2"
              >
                <Edit2 :size="14" />
                Edit
              </button>
            </div>

            <!-- Editable Fields -->
            <div class="space-y-4">
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">First Name</label>
                  <input
                    v-model="profileForm.first_name"
                    :disabled="!isEditing"
                    type="text"
                    placeholder="First name"
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
                <div>
                  <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Last Name</label>
                  <input
                    v-model="profileForm.last_name"
                    :disabled="!isEditing"
                    type="text"
                    placeholder="Last name"
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Bio</label>
                <textarea
                  v-model="profileForm.bio"
                  :disabled="!isEditing"
                  rows="3"
                  placeholder="Tell us about yourself..."
                  class="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all resize-none disabled:opacity-50 disabled:cursor-not-allowed"
                />
              </div>

              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Location</label>
                <div class="relative">
                  <MapPin class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" :size="16" />
                  <input
                    v-model="profileForm.location"
                    :disabled="!isEditing"
                    type="text"
                    placeholder="City, Country"
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Website</label>
                <div class="relative">
                  <Globe class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" :size="16" />
                  <input
                    v-model="profileForm.website"
                    :disabled="!isEditing"
                    type="url"
                    placeholder="https://yourwebsite.com"
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  />
                </div>
              </div>

              <div>
                <label class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Birth Date</label>
                <div class="relative">
                  <Calendar class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" :size="16" />
                  <input
                    v-model="profileForm.birth_date"
                    :disabled="!isEditing"
                    type="date"
                    class="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert"
                  />
                </div>
              </div>

              <div v-if="isEditing" class="flex items-center gap-3 pt-4">
                <button
                  @click="cancelEdit"
                  class="flex-1 px-4 py-2.5 rounded-xl border border-slate-700 text-slate-300 text-sm font-bold hover:bg-slate-800 transition-all flex items-center justify-center gap-2"
                >
                  <X :size="16" />
                  Cancel
                </button>
                <button
                  @click="handleSaveProfile"
                  class="flex-1 px-4 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-all flex items-center justify-center gap-2"
                >
                  <Save :size="16" />
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats Sidebar -->
        <div class="space-y-4">
          <h3 class="text-xs font-black text-slate-500 uppercase tracking-widest mb-4">Reading Statistics</h3>

          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 text-center hover:border-indigo-500/30 transition-all">
            <BookOpen class="w-10 h-10 text-indigo-400 mx-auto mb-3" />
            <p class="text-3xl font-black text-white mb-1">{{ stats.totalBooks }}</p>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Books</p>
          </div>

          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 text-center hover:border-emerald-500/30 transition-all">
            <BookOpen class="w-10 h-10 text-emerald-400 mx-auto mb-3" />
            <p class="text-3xl font-black text-emerald-400 mb-1">{{ stats.booksRead }}</p>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Books Read</p>
          </div>

          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 text-center hover:border-sky-500/30 transition-all">
            <BookOpen class="w-10 h-10 text-sky-400 mx-auto mb-3" />
            <p class="text-3xl font-black text-sky-400 mb-1">{{ stats.currentlyReading }}</p>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Currently Reading</p>
          </div>

          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 text-center hover:border-amber-500/30 transition-all">
            <Quote class="w-10 h-10 text-amber-400 mx-auto mb-3" />
            <p class="text-3xl font-black text-amber-400 mb-1">{{ stats.quotes }}</p>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Quotes Saved</p>
          </div>

          <div class="glass bg-slate-900/40 rounded-2xl border border-slate-800/50 p-6 text-center hover:border-purple-500/30 transition-all">
            <Target class="w-10 h-10 text-purple-400 mx-auto mb-3" />
            <p class="text-3xl font-black text-purple-400 mb-1">{{ stats.wantToRead }}</p>
            <p class="text-xs font-bold text-slate-500 uppercase tracking-wider">Want to Read</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
