<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import {
  Library,
  Search,
  Users,
  Quote,
  Brain,
  MessageSquare,
  Trophy,
  Settings,
  ChevronDown,
  LogOut,
  User,
  Layers,
  Compass,
  Sparkles
} from 'lucide-vue-next'
import SidebarItem from './sidebar/SidebarItem.vue'
import NavGroup from './sidebar/NavGroup.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const booksStore = useUserBooksStore()

const userInitials = computed(() => {
  const user = authStore.user
  if (user?.first_name && user?.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
  }
  return user?.email?.[0]?.toUpperCase() || 'U'
})

const isActive = (path) => {
  if (path === '/feed') {
    return route.path === '/feed'
  }
  if (path === '/import') {
    return route.path === '/import'
  }
  if (path === '/books') {
    return route.path === '/books'
  }
  if (path === '/library') {
    return route.path === '/library' && route.path !== '/library/shelf'
  }
  if (path === '/quotes') {
    return route.path === '/quotes'
  }
  if (path === '/vocabulary') {
    return route.path === '/vocabulary'
  }
  if (path === '/correspondence') {
    return route.path === '/correspondence'
  }
  if (path === '/challenges') {
    return route.path === '/challenges'
  }
  return false
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleStudyModeClick = () => {
  if (route.path.includes('/study')) {
    return
  }

  const currentlyReading = booksStore.books.filter(b => b.status === 'currently_reading')
  if (currentlyReading.length > 0) {
    const lastBook = currentlyReading[0]
    router.push(`/books/${lastBook.book.id}/study?title=${encodeURIComponent(lastBook.book.title)}`)
  } else if (booksStore.books.length > 0) {
    const lastBook = booksStore.books[0]
    router.push(`/books/${lastBook.book.id}/study?title=${encodeURIComponent(lastBook.book.title)}`)
  } else {
    router.push('/library')
  }
}
</script>

<template>
  <aside class="w-72 hidden lg:flex flex-col glass border-r border-slate-800/50 z-50 sticky top-0 h-screen bg-slate-950/50 backdrop-blur-3xl">
    <div class="p-6">
      <div
        class="flex items-center gap-3 mb-8 cursor-pointer group"
        @click="router.push('/library')"
      >
        <div class="w-9 h-9 rounded-xl bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/40 group-hover:scale-105 transition-transform">
          <Library :size="20" class="text-white" />
        </div>
        <span class="font-black text-xl tracking-tighter text-slate-50">Marginalia</span>
      </div>

      <nav class="space-y-1">
        <NavGroup label="Main">
          <SidebarItem
            :active="isActive('/feed')"
            @click="router.push('/feed')"
            :icon="Users"
            label="Feed"
          />
          <SidebarItem
            :active="isActive('/library')"
            @click="router.push('/library')"
            label="Vault"
            :icon="Library"
          />
          <SidebarItem
            :active="isActive('/import')"
            @click="router.push('/import')"
            :icon="Compass"
            label="Discover"
          />
          <SidebarItem
            :active="isActive('/books')"
            @click="router.push('/books')"
            :icon="Search"
            label="Books"
          />
          <SidebarItem
            :active="route.path === '/library/shelf'"
            @click="router.push('/library/shelf')"
            label="Shelf"
            :icon="Layers"
          />
        </NavGroup>

        <NavGroup label="Commonplace">
          <SidebarItem
            :active="isActive('/quotes')"
            @click="router.push('/quotes')"
            label="Quotes"
            :icon="Quote"
          />
          <SidebarItem
            :active="isActive('/vocabulary')"
            @click="router.push('/vocabulary')"
            label="Vocabulary"
            :icon="Brain"
          />
          <SidebarItem
            :active="isActive('/correspondence')"
            @click="router.push('/correspondence')"
            label="Messages"
            :icon="MessageSquare"
            badge="2"
          />
          <SidebarItem
            :active="route.path.includes('/study')"
            @click="handleStudyModeClick"
            label="Study"
            :icon="Sparkles"
          />
          <SidebarItem
            :active="isActive('/challenges')"
            @click="router.push('/challenges')"
            label="Challenges"
            :icon="Trophy"
          />
        </NavGroup>
      </nav>
    </div>

    <div class="mt-auto border-t border-slate-800/50">
      <nav class="p-4 space-y-1">
        <SidebarItem
          :active="route.path === `/users/${authStore.user?.id}`"
          @click="router.push(`/users/${authStore.user?.id}`)"
          label="Profile"
          :icon="User"
        />
        <SidebarItem
          :active="route.path === '/profile'"
          @click="router.push('/profile')"
          label="Settings"
          :icon="Settings"
        />
        <button
          @click="handleLogout"
          class="w-full flex items-center gap-3 px-4 py-2.5 rounded-2xl transition-all duration-300 group text-slate-400 hover:text-red-400 hover:bg-red-500/10"
        >
          <LogOut :size="16" class="text-slate-400 group-hover:text-red-400 transition-colors flex-shrink-0" />
          <span class="text-sm tracking-tight">Logout</span>
        </button>
      </nav>
    </div>
  </aside>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
}
</style>
