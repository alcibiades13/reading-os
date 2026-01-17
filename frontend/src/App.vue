<script setup>
  import { useAuthStore } from '@/stores/authStore'
  import { useRoute, useRouter } from 'vue-router'
  import { onMounted, computed } from 'vue'
  import Sidebar from '@/components/Sidebar.vue'
  import SearchDropdown from '@/components/SearchDropdown.vue'
  import GradientBackground from '@/components/GradientBackground.vue'
  import ToastNotification from '@/components/ToastNotification.vue'
  import NotificationDropdown from '@/components/NotificationDropdown.vue'
  import { useToast } from '@/composables/useToast'
  import { useThemeStore } from '@/stores/themeStore'
  import { Sun, Moon, ChevronDown, User, Settings, LogOut } from 'lucide-vue-next'
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
  } from '@/components/ui/dropdown-menu'

  const authStore = useAuthStore()
  const route = useRoute()
  const router = useRouter()
  const themeStore = useThemeStore()
  const { toasts } = useToast()

  // Pages that should NOT show navigation
  const noNavRoutes = ['/login', '/register', '/404']

  const showNavigation = computed(() => {
    return authStore.isAuthenticated && !noNavRoutes.includes(route.path)
  })

  const userInitials = computed(() => {
    const user = authStore.user
    if (user?.first_name && user?.last_name) {
      return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    }
    return user?.email?.[0]?.toUpperCase() || 'U'
  })

  const handleLogout = () => {
    authStore.logout()
    router.push('/login')
  }

  // Initialize auth state on app mount
  onMounted(() => {
    authStore.initAuth()
  })
  </script>

  <template>
    <div id="app" class="min-h-screen bg-slate-950 text-slate-50 selection:bg-sky-500/30">
      <!-- Background Gradients -->
      <GradientBackground />

      <!-- Layout with Sidebar and Main Content -->
      <div v-if="showNavigation" class="flex min-h-screen transition-colors duration-500 overflow-hidden">
        <!-- Sidebar -->
        <Sidebar />

        <!-- Main Content Area -->
        <div class="flex-1 flex flex-col h-screen overflow-hidden">
          <!-- Top Header -->
          <header class="h-20 border-b border-slate-800/50 flex items-center justify-between px-8 bg-slate-950/50 backdrop-blur-xl z-40">
            <SearchDropdown />

            <div class="flex items-center gap-6 ml-8">
              <!-- Theme Toggle -->
              <div class="flex items-center gap-1 p-1 bg-white/5 rounded-xl border border-slate-800/50">
                <button
                  @click="themeStore.setTheme('light')"
                  :class="[
                    'p-2 rounded-lg transition-all',
                    themeStore.theme === 'light'
                      ? 'bg-indigo-500 text-white shadow-lg'
                      : 'text-slate-400 hover:text-indigo-500'
                  ]"
                >
                  <Sun :size="18" />
                </button>
                <button
                  @click="themeStore.setTheme('dark')"
                  :class="[
                    'p-2 rounded-lg transition-all',
                    themeStore.theme === 'dark'
                      ? 'bg-indigo-500 text-white shadow-lg'
                      : 'text-slate-400 hover:text-indigo-500'
                  ]"
                >
                  <Moon :size="18" />
                </button>
              </div>

              <!-- Notifications -->
              <NotificationDropdown />

              <div class="h-8 w-px bg-slate-800/50" />

              <!-- User Dropdown -->
              <DropdownMenu>
                <DropdownMenuTrigger as-child>
                  <div class="flex items-center gap-3 cursor-pointer group">
                    <div class="w-9 h-9 rounded-full border-2 border-white/10 bg-slate-800 flex items-center justify-center text-[10px] font-black text-white group-hover:border-indigo-500/50 transition-all">
                      {{ userInitials }}
                    </div>
                    <ChevronDown :size="16" class="text-slate-400 group-hover:text-indigo-500 transition-colors" />
                  </div>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" class="w-56">
                  <DropdownMenuLabel>
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold overflow-hidden flex-shrink-0">
                        <span>{{ userInitials }}</span>
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

          <!-- View Content -->
          <main class="flex-1 overflow-y-auto custom-scrollbar bg-slate-950">
            <router-view />
          </main>
        </div>
      </div>

      <!-- Content without Sidebar (Login, Register, 404) -->
      <router-view v-else />

      <!-- Toast Notifications -->
      <div class="fixed bottom-8 right-8 z-[200] flex flex-col gap-3 pointer-events-none">
        <ToastNotification
          v-for="toast in toasts"
          :key="toast.id"
          :message="toast.message"
          :type="toast.type"
        />
      </div>
    </div>
  </template>

  <style>
  /* Page transition */
  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.2s ease;
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }

  /* Custom scrollbar */
  .scrollbar-thin::-webkit-scrollbar,
  .custom-scrollbar::-webkit-scrollbar {
    width: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-track,
  .custom-scrollbar::-webkit-scrollbar-track {
    background: rgb(15 23 42);
    border-radius: 10px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb,
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgb(51 65 85);
    border-radius: 10px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover,
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgb(71 85 105);
  }
  </style>