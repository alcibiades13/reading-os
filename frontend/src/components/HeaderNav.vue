<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useThemeStore } from '@/stores/themeStore'
import { useMobileSidebar } from '@/composables/useMobileSidebar'
import SearchDropdown from '@/components/SearchDropdown.vue'
import NotificationDropdown from '@/components/NotificationDropdown.vue'
import { Sun, Moon, User, Settings, LogOut, Menu } from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const router = useRouter()
const authStore = useAuthStore()
const themeStore = useThemeStore()
const { toggle: toggleMobileSidebar } = useMobileSidebar()

const userInitials = computed(() => {
  const user = authStore.user
  if (user?.first_name && user?.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
  }
  return user?.email?.[0]?.toUpperCase() || 'U'
})

const userAvatarUrl = computed(() => authStore.user?.avatar || null)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="h-14 lg:h-20 border-b border-slate-800/50 flex items-center justify-between px-3 sm:px-4 lg:px-8 bg-slate-950/50 backdrop-blur-xl z-40">
    <!-- Mobile hamburger -->
    <button
      @click="toggleMobileSidebar"
      class="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-all flex-shrink-0 mr-2"
    >
      <Menu :size="22" />
    </button>

    <SearchDropdown />

    <div class="flex items-center gap-2 sm:gap-3 lg:gap-6 ml-2 sm:ml-4 lg:ml-8">
      <!-- Theme Toggle -->
      <div class="flex items-center gap-0.5 p-0.5 lg:p-1 bg-white/5 rounded-lg lg:rounded-xl border border-slate-800/50">
        <button
          @click="themeStore.setTheme('light')"
          :class="[
            'p-1.5 lg:p-2 rounded-md lg:rounded-lg transition-all',
            themeStore.theme === 'light'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-400 hover:text-indigo-500'
          ]"
        >
          <Sun :size="14" class="lg:!w-[18px] lg:!h-[18px]" />
        </button>
        <button
          @click="themeStore.setTheme('dark')"
          :class="[
            'p-1.5 lg:p-2 rounded-md lg:rounded-lg transition-all',
            themeStore.theme === 'dark'
              ? 'bg-indigo-500 text-white shadow-lg'
              : 'text-slate-400 hover:text-indigo-500'
          ]"
        >
          <Moon :size="14" class="lg:!w-[18px] lg:!h-[18px]" />
        </button>
      </div>

      <!-- Notifications -->
      <NotificationDropdown />

      <div class="hidden lg:block h-8 w-px bg-slate-800/50" />

      <!-- User Dropdown -->
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <div class="group p-0.5 rounded-full bg-transparent hover:bg-gradient-to-tr hover:from-indigo-500 hover:to-purple-500 transition-all cursor-pointer">
            <div class="w-8 h-8 lg:w-9 lg:h-9 rounded-full bg-slate-800 flex items-center justify-center text-[10px] font-black text-white overflow-hidden">
              <img v-if="userAvatarUrl" :src="userAvatarUrl" class="w-full h-full object-cover" />
              <span v-else>{{ userInitials }}</span>
            </div>
          </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" class="w-56">
          <DropdownMenuLabel>
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold overflow-hidden flex-shrink-0">
                <img v-if="userAvatarUrl" :src="userAvatarUrl" class="w-full h-full object-cover" />
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
          <DropdownMenuItem @click="router.push(`/users/${authStore.user?.id}`)">
            <User class="w-4 h-4 mr-2" />
            My Profile
          </DropdownMenuItem>
          <DropdownMenuItem @click="router.push('/profile')">
            <Settings class="w-4 h-4 mr-2" />
            Settings
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleLogout" class="text-destructive focus:text-destructive">
            <LogOut class="w-4 h-4 mr-2" />
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  </header>
</template>
