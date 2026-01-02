<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  BookOpen,
  Library,
  Quote,
  ListChecks,
  Trophy,
  Users,
  Search,
  User,
  LogOut,
  Menu,
  X,
  BookPlus,
  Rss,
  Brain
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const mobileMenuOpen = ref(false)

const navItems = [
  { name: 'Library', path: '/library', icon: Library },
  { name: 'Books', path: '/books', icon: Search },
  { name: 'Import', path: '/import', icon: BookPlus },
  { name: 'Quotes', path: '/quotes', icon: Quote },
  { name: 'Lexicon', path: '/vocabulary', icon: Brain },
  { name: 'Feed', path: '/feed', icon: Rss },
  { name: 'Circles', path: '/circles', icon: Users },
]

const isActive = (path) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const userInitials = computed(() => {
  const user = authStore.user
  if (user?.first_name && user?.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
  }
  return user?.email?.[0]?.toUpperCase() || 'U'
})
</script>

<template>
  <nav class="relative z-[60] border-b border-slate-900 bg-slate-950/50 backdrop-blur-md sticky top-0">
    <div class="max-w-7xl mx-auto px-6">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center gap-2 cursor-pointer" @click="router.push('/library')">
          <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <BookOpen :size="18" class="text-white" />
          </div>
          <span class="font-black text-xl tracking-tighter text-white">READING OS</span>
        </div>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-8">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="router.push(item.path)"
            :class="isActive(item.path) ? 'text-indigo-400' : 'text-slate-400 hover:text-white'"
            class="text-sm font-bold transition-all flex items-center gap-2"
          >
            <component :is="item.icon" :size="16" />
            {{ item.name }}
          </button>
        </div>

        <!-- User Menu -->
        <div class="flex items-center gap-4">
          <!-- Mobile menu button -->
          <Button
            variant="ghost"
            size="icon"
            class="md:hidden"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <Menu v-if="!mobileMenuOpen" class="w-5 h-5" />
            <X v-else class="w-5 h-5" />
          </Button>

          <!-- User dropdown -->
          <DropdownMenu>
            <DropdownMenuTrigger as-child>
              <button class="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 hover:border-indigo-500 transition-colors flex items-center justify-center text-[10px] font-bold overflow-hidden">
                <img
                  v-if="authStore.user?.avatar"
                  :src="authStore.user.avatar"
                  alt="Avatar"
                  class="w-full h-full object-cover"
                />
                <span v-else>{{ userInitials }}</span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" class="w-56">
              <DropdownMenuLabel>
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold overflow-hidden flex-shrink-0">
                    <img
                      v-if="authStore.user?.avatar"
                      :src="authStore.user.avatar"
                      alt="Avatar"
                      class="w-full h-full object-cover"
                    />
                    <span v-else>{{ userInitials }}</span>
                  </div>
                  <div class="flex flex-col space-y-1 min-w-0">
                    <p class="text-sm font-medium truncate">
                      {{ authStore.user?.first_name || authStore.user?.last_name
                        ? `${authStore.user.first_name || ''} ${authStore.user.last_name || ''}`.trim()
                        : authStore.user?.email?.split('@')[0] || 'User' }}
                    </p>
                    <p class="text-xs text-muted-foreground truncate">{{ authStore.user?.email }}</p>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="router.push('/profile')">
                <User class="w-4 h-4 mr-2" />
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem @click="router.push('/lists')">
                <ListChecks class="w-4 h-4 mr-2" />
                My Lists
              </DropdownMenuItem>
              <DropdownMenuItem @click="router.push('/challenges')">
                <Trophy class="w-4 h-4 mr-2" />
                Challenges
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem @click="handleLogout" class="text-destructive focus:text-destructive">
                <LogOut class="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <!-- Mobile Navigation -->
      <div
        v-if="mobileMenuOpen"
        class="md:hidden py-4 border-t border-slate-900"
      >
        <div class="flex flex-col gap-2">
          <button
            v-for="item in navItems"
            :key="item.path"
            @click="router.push(item.path); mobileMenuOpen = false"
            :class="isActive(item.path) ? 'text-indigo-400' : 'text-slate-400'"
            class="flex items-center gap-2 px-4 py-2 text-sm font-bold hover:text-white transition-colors"
          >
            <component :is="item.icon" :size="16" />
            {{ item.name }}
          </button>
        </div>
      </div>
    </div>
  </nav>
</template>
