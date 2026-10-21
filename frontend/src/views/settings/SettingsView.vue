<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore, READING_SCALES } from '@/stores/themeStore'
import { useToast } from '@/composables/useToast'
import { usersAPI } from '@/services/api'
import { downloadBlob } from '@/utils/downloadFile'
import {
  Settings,
  User,
  Bell,
  Shield,
  Palette,
  Download,
  Eye,
  EyeOff,
  Sun,
  Moon,
  Save,
  Loader2,
  BookOpen,
  Quote,
  BarChart3,
  Mail,
  Users,
  MessageCircle,
  Camera,
  MapPin,
  Globe,
  Calendar,
  Trash2,
  AlertTriangle,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const themeStore = useThemeStore()
const { addToast } = useToast()

const saving = ref(false)
const exportingData = ref(false)
const avatarFile = ref(null)
const avatarPreview = ref(null)

const showDeleteDialog = ref(false)
const deletePassword = ref('')
const deletingAccount = ref(false)
const deleteError = ref('')

// Profile form
const profileForm = ref({
  first_name: '',
  last_name: '',
  bio: '',
  location: '',
  website: '',
  birth_date: '',
})

// Settings form
const settingsForm = ref({
  is_public: true,
  show_reading_stats: true,
  show_quotes: true,
  email_on_friend_request: true,
  email_on_circle_invite: true,
  email_on_quote_comment: true,
  reading_goal_year: null,
})

onMounted(() => {
  const u = authStore.user
  if (u) {
    profileForm.value = {
      first_name: u.first_name || '',
      last_name: u.last_name || '',
      bio: u.bio || '',
      location: u.location || '',
      website: u.website || '',
      birth_date: u.birth_date || '',
    }
    avatarPreview.value = u.avatar || null
  }
  if (u?.profile) {
    const p = u.profile
    settingsForm.value = {
      is_public: p.is_public ?? true,
      show_reading_stats: p.show_reading_stats ?? true,
      show_quotes: p.show_quotes ?? true,
      email_on_friend_request: p.email_on_friend_request ?? true,
      email_on_circle_invite: p.email_on_circle_invite ?? true,
      email_on_quote_comment: p.email_on_quote_comment ?? true,
      reading_goal_year: p.reading_goal_year || null,
    }
  }
})

const isDark = computed(() => themeStore.theme !== 'light')

const initials = computed(() => {
  const u = authStore.user
  if (!u) return 'U'
  const first = u.first_name?.[0] || ''
  const last = u.last_name?.[0] || ''
  return (first + last).toUpperCase() || u.email?.[0]?.toUpperCase() || 'U'
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

const handleSave = async () => {
  saving.value = true

  // Build data — use FormData only if avatar is included (multipart), otherwise JSON
  if (avatarFile.value) {
    const formData = new FormData()
    formData.append('avatar', avatarFile.value)
    formData.append('first_name', profileForm.value.first_name)
    formData.append('last_name', profileForm.value.last_name)
    formData.append('bio', profileForm.value.bio)
    formData.append('location', profileForm.value.location)
    formData.append('website', profileForm.value.website)
    if (profileForm.value.birth_date) {
      formData.append('birth_date', profileForm.value.birth_date)
    }
    await authStore.updateProfile(formData)
    avatarFile.value = null
  } else {
    await authStore.updateProfile({
      first_name: profileForm.value.first_name,
      last_name: profileForm.value.last_name,
      bio: profileForm.value.bio,
      location: profileForm.value.location,
      website: profileForm.value.website,
      birth_date: profileForm.value.birth_date || null,
    })
  }

  // Save settings (profile nested fields)
  const result = await authStore.updateProfile({
    profile: {
      is_public: settingsForm.value.is_public,
      show_reading_stats: settingsForm.value.show_reading_stats,
      show_quotes: settingsForm.value.show_quotes,
      email_on_friend_request: settingsForm.value.email_on_friend_request,
      email_on_circle_invite: settingsForm.value.email_on_circle_invite,
      email_on_quote_comment: settingsForm.value.email_on_quote_comment,
      reading_goal_year: settingsForm.value.reading_goal_year ? parseInt(settingsForm.value.reading_goal_year) : null,
    },
  })

  saving.value = false
  if (result.success) {
    addToast('Settings saved')
  }
}

const handleExportData = async () => {
  exportingData.value = true
  try {
    const response = await usersAPI.exportAllData()
    downloadBlob(response, 'marginalia_export.zip')
    addToast('Data exported successfully')
  } catch {
    addToast('Export failed', 'error')
  } finally {
    exportingData.value = false
  }
}

const handleDeleteAccount = async () => {
  if (!deletePassword.value) {
    deleteError.value = 'Password is required.'
    return
  }
  deletingAccount.value = true
  deleteError.value = ''
  try {
    await usersAPI.deleteAccount(deletePassword.value)
    authStore.logout()
  } catch (e) {
    deleteError.value = e?.response?.data?.error || 'Incorrect password or error occurred.'
    deletingAccount.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10">

    <!-- Page Header -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-2">
        <div class="w-9 h-9 rounded-xl bg-zinc-800/50 border border-zinc-700/50 flex items-center justify-center">
          <Settings :size="18" class="text-zinc-400" />
        </div>
        <h1 class="text-2xl sm:text-3xl font-black tracking-tight">Settings</h1>
      </div>
    </div>

    <div class="space-y-6">

      <!-- ===== PROFILE ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-5">
          <User :size="16" class="text-indigo-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Profile</h2>
        </div>

        <!-- Avatar -->
        <div class="flex items-center gap-4 mb-6">
          <div class="relative flex-shrink-0">
            <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border-2 border-indigo-500/20 flex items-center justify-center overflow-hidden">
              <img v-if="avatarPreview" :src="avatarPreview" alt="Avatar" class="w-full h-full object-cover" />
              <span v-else class="text-xl font-black text-indigo-400">{{ initials }}</span>
            </div>
            <button
              @click="$refs.avatarInput.click()"
              class="absolute -bottom-1 -right-1 w-6 h-6 rounded-lg bg-indigo-500 text-white flex items-center justify-center hover:bg-indigo-400 transition-all shadow-lg"
            >
              <Camera :size="12" />
            </button>
            <input
              ref="avatarInput"
              type="file"
              accept="image/*"
              @change="handleAvatarChange"
              class="hidden"
            />
          </div>
          <div>
            <p class="text-sm font-semibold text-white">Profile photo</p>
            <p class="text-xs text-zinc-500">Click the camera icon to change</p>
          </div>
        </div>

        <!-- Name fields -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">First Name</label>
            <input
              v-model="profileForm.first_name"
              type="text"
              placeholder="First name"
              class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all"
            />
          </div>
          <div>
            <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">Last Name</label>
            <input
              v-model="profileForm.last_name"
              type="text"
              placeholder="Last name"
              class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all"
            />
          </div>
        </div>

        <!-- Bio -->
        <div class="mb-4">
          <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">Bio</label>
          <textarea
            v-model="profileForm.bio"
            rows="3"
            placeholder="Tell us about yourself..."
            class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl px-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all resize-none"
          />
        </div>

        <!-- Location & Website -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
          <div>
            <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">Location</label>
            <div class="relative">
              <MapPin class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" :size="14" />
              <input
                v-model="profileForm.location"
                type="text"
                placeholder="City, Country"
                class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all"
              />
            </div>
          </div>
          <div>
            <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">Website</label>
            <div class="relative">
              <Globe class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" :size="14" />
              <input
                v-model="profileForm.website"
                type="url"
                placeholder="https://..."
                class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all"
              />
            </div>
          </div>
        </div>

        <!-- Birth Date -->
        <div>
          <label class="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-1.5 block">Birth Date</label>
          <div class="relative max-w-xs">
            <Calendar class="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-600" :size="14" />
            <input
              v-model="profileForm.birth_date"
              type="date"
              class="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white outline-none focus:border-indigo-500/50 transition-all [&::-webkit-calendar-picker-indicator]:filter [&::-webkit-calendar-picker-indicator]:invert"
            />
          </div>
        </div>
      </section>

      <!-- ===== APPEARANCE ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <Palette :size="16" class="text-indigo-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Appearance</h2>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-white">Theme</p>
            <p class="text-xs text-zinc-500 mt-0.5">Choose your preferred color scheme</p>
          </div>
          <div class="flex items-center gap-1 p-1 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
            <button
              @click="themeStore.setTheme('dark')"
              :class="isDark ? 'bg-indigo-500 text-white shadow-lg' : 'text-zinc-400 hover:text-zinc-300'"
              class="px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all"
            >
              <Moon :size="13" /> Dark
            </button>
            <button
              @click="themeStore.setTheme('light')"
              :class="!isDark ? 'bg-indigo-500 text-white shadow-lg' : 'text-zinc-400 hover:text-zinc-300'"
              class="px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all"
            >
              <Sun :size="13" /> Light
            </button>
          </div>
        </div>

        <div class="mt-5 pt-5 border-t border-zinc-800/50">
          <div class="mb-3">
            <p class="text-sm font-semibold text-white">Reading text size</p>
            <p class="text-xs text-zinc-500 mt-0.5">Quotes, notes, reviews, codex, letters and vocabulary. Saved on this device.</p>
          </div>
          <div class="grid grid-cols-4 gap-1 p-1 rounded-xl bg-zinc-800/50 border border-zinc-700/50">
            <button
              v-for="(scale, i) in READING_SCALES"
              :key="scale.id"
              @click="themeStore.setReadingScale(scale.id)"
              :class="themeStore.readingScale === scale.id ? 'bg-indigo-500 text-white shadow-lg' : 'text-zinc-400 hover:text-zinc-300'"
              class="py-2 rounded-lg font-bold flex flex-col items-center gap-0.5 transition-all"
              :title="scale.label"
            >
              <span :style="{ fontSize: `${13 + i * 3}px` }" class="leading-none font-serif">Aa</span>
              <span class="text-[10px] font-semibold opacity-80">{{ scale.label }}</span>
            </button>
          </div>
          <p class="mt-4 p-4 rounded-xl bg-zinc-950/40 border border-zinc-800/50 font-serif italic text-quote text-zinc-200 leading-relaxed">
            "A reader lives a thousand lives before he dies. The man who never reads lives only one."
          </p>
        </div>
      </section>

      <!-- ===== PRIVACY ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <Shield :size="16" class="text-emerald-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Privacy</h2>
        </div>

        <div class="space-y-4">
          <label class="flex items-center justify-between cursor-pointer group">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <Eye v-if="settingsForm.is_public" :size="14" class="text-emerald-400" />
                <EyeOff v-else :size="14" class="text-zinc-500" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Public profile</p>
                <p class="text-xs text-zinc-500">Other users can find and view your profile</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.is_public" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>

          <label class="flex items-center justify-between cursor-pointer group">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <BarChart3 :size="14" class="text-sky-400" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Show reading stats</p>
                <p class="text-xs text-zinc-500">Display your reading statistics on your profile</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.show_reading_stats" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>

          <label class="flex items-center justify-between cursor-pointer group">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <Quote :size="14" class="text-amber-400" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Show quotes</p>
                <p class="text-xs text-zinc-500">Display your public quotes on your profile</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.show_quotes" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>
        </div>
      </section>

      <!-- ===== NOTIFICATIONS ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <Bell :size="16" class="text-amber-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Notifications</h2>
        </div>

        <div class="space-y-4">
          <label class="flex items-center justify-between cursor-pointer">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <Users :size="14" class="text-indigo-400" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Friend requests</p>
                <p class="text-xs text-zinc-500">Email when someone sends you a friend request</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.email_on_friend_request" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>

          <label class="flex items-center justify-between cursor-pointer">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <MessageCircle :size="14" class="text-purple-400" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Circle invitations</p>
                <p class="text-xs text-zinc-500">Email when you're invited to a reading circle</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.email_on_circle_invite" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>

          <label class="flex items-center justify-between cursor-pointer">
            <div class="flex items-center gap-3">
              <div class="w-8 h-8 rounded-lg bg-zinc-800/50 flex items-center justify-center">
                <Mail :size="14" class="text-rose-400" />
              </div>
              <div>
                <p class="text-sm font-semibold text-white">Quote comments</p>
                <p class="text-xs text-zinc-500">Email when someone comments on your quote</p>
              </div>
            </div>
            <input type="checkbox" v-model="settingsForm.email_on_quote_comment" class="sr-only peer" />
            <div class="w-10 h-5 rounded-full bg-zinc-700 peer-checked:bg-indigo-500 relative transition-colors after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:w-4 after:h-4 after:rounded-full after:bg-white after:transition-transform peer-checked:after:translate-x-5" />
          </label>
        </div>
      </section>

      <!-- ===== READING GOAL ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <BookOpen :size="16" class="text-sky-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Reading Goal</h2>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-white">Yearly reading goal</p>
            <p class="text-xs text-zinc-500">Number of books you'd like to read this year</p>
          </div>
          <div class="flex items-center gap-2">
            <input
              v-model="settingsForm.reading_goal_year"
              type="number"
              min="1"
              max="365"
              placeholder="—"
              class="w-20 text-center px-3 py-2 rounded-xl bg-zinc-800/50 border border-zinc-700/50 text-sm text-white font-bold outline-none focus:border-indigo-500/50 [appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
            />
            <span class="text-xs text-zinc-500">books</span>
          </div>
        </div>
      </section>

      <!-- ===== DATA ===== -->
      <section class="rounded-2xl border border-zinc-800/50 bg-zinc-900/40 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <Download :size="16" class="text-zinc-400" />
          <h2 class="text-sm font-bold text-zinc-300 uppercase tracking-wider">Data</h2>
        </div>

        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-white">Export all data</p>
            <p class="text-xs text-zinc-500">Download your books, quotes, journals, and notes as a ZIP file</p>
          </div>
          <button
            @click="handleExportData"
            :disabled="exportingData"
            class="px-4 py-2 rounded-xl border border-zinc-700 text-xs font-bold text-zinc-300 hover:border-zinc-500 hover:text-white transition-all disabled:opacity-50 flex items-center gap-1.5"
          >
            <Loader2 v-if="exportingData" :size="14" class="animate-spin" />
            <Download v-else :size="14" />
            {{ exportingData ? 'Exporting...' : 'Export' }}
          </button>
        </div>
      </section>

      <!-- Save Button -->
      <div class="pt-2">
        <button
          @click="handleSave"
          :disabled="saving"
          class="w-full sm:w-auto px-8 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 transition-all disabled:opacity-50"
        >
          <Loader2 v-if="saving" :size="16" class="animate-spin" />
          <Save v-else :size="16" />
          {{ saving ? 'Saving...' : 'Save Settings' }}
        </button>
      </div>

      <!-- ===== DANGER ZONE ===== -->
      <section class="rounded-2xl border border-red-500/20 bg-red-500/5 p-5 sm:p-6">
        <div class="flex items-center gap-2.5 mb-4">
          <AlertTriangle :size="16" class="text-red-400" />
          <h2 class="text-sm font-bold text-red-400 uppercase tracking-wider">Danger Zone</h2>
        </div>

        <div v-if="!showDeleteDialog" class="flex items-center justify-between">
          <div>
            <p class="text-sm font-semibold text-white">Delete account</p>
            <p class="text-xs text-zinc-500">Permanently delete your account and all data. This cannot be undone.</p>
          </div>
          <button
            @click="showDeleteDialog = true"
            class="px-4 py-2 rounded-xl border border-red-500/40 text-xs font-bold text-red-400 hover:border-red-500 hover:bg-red-500/10 transition-all flex items-center gap-1.5"
          >
            <Trash2 :size="14" />
            Delete
          </button>
        </div>

        <div v-else class="space-y-4">
          <div class="flex items-start gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
            <AlertTriangle :size="16" class="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p class="text-sm font-bold text-red-300">This will permanently delete your account</p>
              <p class="text-xs text-red-400/80 mt-0.5">All your books, quotes, notes, and vocabulary will be lost. We recommend exporting your data first.</p>
            </div>
          </div>

          <button
            @click="handleExportData"
            :disabled="exportingData"
            class="w-full px-4 py-2.5 rounded-xl border border-zinc-700 text-xs font-bold text-zinc-300 hover:border-zinc-500 hover:text-white transition-all disabled:opacity-50 flex items-center justify-center gap-1.5"
          >
            <Loader2 v-if="exportingData" :size="14" class="animate-spin" />
            <Download v-else :size="14" />
            {{ exportingData ? 'Exporting...' : 'Export my data first (recommended)' }}
          </button>

          <div>
            <label class="block text-xs font-medium text-zinc-400 mb-1.5">Confirm with your password</label>
            <input
              v-model="deletePassword"
              type="password"
              placeholder="Your password"
              class="w-full bg-zinc-800/80 border border-zinc-700/60 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-red-500/50 transition-all"
            />
            <p v-if="deleteError" class="text-xs text-red-400 mt-1.5">{{ deleteError }}</p>
          </div>

          <div class="flex gap-2">
            <button
              @click="showDeleteDialog = false; deletePassword = ''; deleteError = ''"
              class="flex-1 px-4 py-2.5 rounded-xl border border-zinc-700 text-xs font-bold text-zinc-400 hover:text-white hover:border-zinc-500 transition-all"
            >
              Cancel
            </button>
            <button
              @click="handleDeleteAccount"
              :disabled="deletingAccount"
              class="flex-1 px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/40 text-xs font-bold text-red-400 hover:bg-red-500 hover:text-white hover:border-red-500 transition-all disabled:opacity-50 flex items-center justify-center gap-1.5"
            >
              <Loader2 v-if="deletingAccount" :size="14" class="animate-spin" />
              <Trash2 v-else :size="14" />
              {{ deletingAccount ? 'Deleting...' : 'Delete my account' }}
            </button>
          </div>
        </div>
      </section>

    </div>
  </div>
</template>
