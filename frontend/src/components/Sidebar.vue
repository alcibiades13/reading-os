<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { getBookUrlWithSuffix } from '@/utils/bookUrl'
import { getMediaUrl } from '@/utils/mediaUrl'
import { correspondenceService } from '@/services/correspondenceService'
import { useMobileSidebar } from '@/composables/useMobileSidebar'
import {
  Library,
  Search,
  Users,
  Quote,
  Brain,
  MessageSquare,
  Trophy,
  Settings,
  LogOut,
  User,
  Layers, Home,
  Compass,
  Sparkles,
  Download,
  PanelLeftClose,
  PanelLeft,
  Hexagon,
  X,
  CircleDot,
  PenTool
} from 'lucide-vue-next'
import SidebarItem from './sidebar/SidebarItem.vue'
import NavGroup from './sidebar/NavGroup.vue'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const booksStore = useUserBooksStore()
const { isOpen: isMobileOpen, close: closeMobile } = useMobileSidebar()

// Close mobile sidebar on route change
watch(() => route.path, () => {
  closeMobile()
})

// Sidebar collapse state
const isCollapsed = ref(false)

// Unread messages count
const unreadMessagesCount = ref(0)

// Load collapsed state and fetch unread count
onMounted(async () => {
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved !== null) {
    isCollapsed.value = saved === 'true'
  }

  // Fetch unread messages count
  await fetchUnreadCount()
})

const fetchUnreadCount = async () => {
  try {
    const conversations = await correspondenceService.getConversations()
    const transformed = conversations.map(c => correspondenceService.transformConversation(c))
    unreadMessagesCount.value = transformed.reduce((sum, c) => sum + (c.unreadCount || 0), 0)
  } catch (error) {
    console.error('Error fetching unread count:', error)
  }
}

// Computed for badge display
const unreadBadge = computed(() => {
  return unreadMessagesCount.value > 0 ? unreadMessagesCount.value.toString() : null
})

// Toggle sidebar collapse
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', isCollapsed.value.toString())
}

const userInitials = computed(() => {
  const user = authStore.user
  if (user?.first_name && user?.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
  }
  return user?.email?.[0]?.toUpperCase() || 'U'
})

const userAvatarUrl = computed(() => getMediaUrl(authStore.user?.avatar))
const sidebarAvatarError = ref(false)

const userName = computed(() => {
  const user = authStore.user
  if (user?.first_name || user?.last_name) {
    return `${user.first_name || ''} ${user.last_name || ''}`.trim()
  }
  return user?.email?.split('@')[0] || 'User'
})

const isActive = (path) => {
  if (path === '/feed') {
    return route.path === '/feed'
  }
  if (path === '/import') {
    return route.path === '/import'
  }
  if (path === '/discover') {
    return route.path === '/discover'
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
  if (path === '/circles') {
    return route.path === '/circles'
  }
  if (path === '/challenges') {
    return route.path === '/challenges'
  }
  if (path === '/codex') {
    return route.path === '/codex'
  }
  return false
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const handleStudyModeClick = async () => {
  if (route.path.includes('/study')) {
    return
  }

  // Ensure books are loaded before deciding where to navigate
  if (booksStore.books.length === 0 && !booksStore.loading) {
    await booksStore.fetchBooks()
  }

  const currentlyReading = booksStore.books.filter(b => b.status === 'currently_reading')
  if (currentlyReading.length > 0) {
    const lastBook = currentlyReading[0]
    router.push(`${getBookUrlWithSuffix(lastBook.book, 'study')}?title=${encodeURIComponent(lastBook.book.title)}`)
  } else if (booksStore.books.length > 0) {
    const lastBook = booksStore.books[0]
    router.push(`${getBookUrlWithSuffix(lastBook.book, 'study')}?title=${encodeURIComponent(lastBook.book.title)}`)
  } else {
    router.push('/library')
  }
}
</script>

<template>
  <!-- Mobile Backdrop -->
  <Transition name="fade">
    <div
      v-if="isMobileOpen"
      class="fixed inset-x-0 top-14 bottom-0 bg-black/60 backdrop-blur-sm z-[60] lg:hidden"
      @click="closeMobile"
    />
  </Transition>

  <aside
    :class="[
      'flex flex-col glass border-r border-slate-800/50 bg-slate-950/90 lg:bg-slate-950/50 backdrop-blur-3xl transition-transform duration-300 ease-in-out',
      // Desktop: static sidebar
      'max-lg:fixed max-lg:top-14 max-lg:bottom-0 max-lg:left-0 max-lg:z-[70] max-lg:w-60',
      'lg:flex lg:sticky lg:top-0 lg:h-screen lg:z-50 lg:transition-all',
      isCollapsed ? 'lg:w-14' : 'lg:w-60',
      // Mobile: slide in/out via transform
      isMobileOpen
        ? 'max-lg:translate-x-0 max-lg:pointer-events-auto'
        : 'max-lg:-translate-x-full max-lg:pointer-events-none'
    ]"
  >
    <!-- Header with Logo (desktop only) -->
    <div :class="['flex-shrink-0 hidden lg:block', isCollapsed ? 'p-2' : 'p-3']">
      <div :class="['flex items-center', isCollapsed ? 'justify-center' : 'justify-between', 'mb-3']">
        <!-- Logo: navigates when expanded, toggles sidebar when collapsed -->
        <div
          class="flex items-center gap-2 cursor-pointer group"
          @click="isCollapsed ? toggleSidebar() : router.push('/library')"
        >
          <div :class="['w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/40 transition-transform flex-shrink-0', isCollapsed ? 'group-hover:ring-2 group-hover:ring-indigo-400/50' : 'group-hover:scale-105']">
            <PanelLeft v-if="isCollapsed" :size="16" class="text-white" />
            <Library v-else :size="18" class="text-white" />
          </div>
          <span
            v-show="!isCollapsed"
            class="font-black text-lg tracking-tighter text-slate-50 whitespace-nowrap overflow-hidden transition-opacity duration-200"
            :class="isCollapsed ? 'opacity-0 w-0' : 'opacity-100'"
          >
            Marginalia
          </span>
        </div>

        <!-- Collapse Button (only when expanded) -->
        <button
          v-if="!isCollapsed"
          @click="toggleSidebar"
          class="p-1.5 rounded-lg text-slate-500 hover:text-indigo-400 hover:bg-slate-800/50 transition-all duration-200 flex-shrink-0"
          title="Collapse sidebar"
        >
          <PanelLeftClose :size="16" />
        </button>
      </div>
    </div>

    <!-- Scrollable Nav Area -->
    <div :class="['flex-1 overflow-y-auto custom-scrollbar', isCollapsed && !isMobileOpen ? 'px-2' : 'px-3']">
      <nav class="space-y-0.5">
        <NavGroup label="Main" :collapsed="isCollapsed && !isMobileOpen">
          <SidebarItem
            :active="isActive('/feed')"
            @click="router.push('/feed')"
            :icon="Users"
            label="Feed"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/library')"
            @click="router.push('/library')"
            label="Vault"
            :icon="Library"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/discover')"
            @click="router.push('/discover')"
            :icon="Compass"
            label="Discover"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/books')"
            @click="router.push('/books')"
            :icon="Search"
            label="Books"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/import')"
            @click="router.push('/import')"
            :icon="Download"
            label="Import"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="route.path === '/library/shelf'"
            @click="router.push('/library/shelf')"
            label="Home Library"
            :icon="Home"
            :collapsed="isCollapsed && !isMobileOpen"
          />
        </NavGroup>

        <NavGroup label="Commonplace" :collapsed="isCollapsed && !isMobileOpen">
          <SidebarItem
            :active="isActive('/quotes')"
            @click="router.push('/quotes')"
            label="Quotes"
            :icon="Quote"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/vocabulary')"
            @click="router.push('/vocabulary')"
            label="Vocabulary"
            :icon="Brain"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="route.path.includes('/study')"
            @click="handleStudyModeClick"
            label="Study"
            :icon="Sparkles"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/challenges')"
            @click="router.push('/challenges')"
            label="Challenges"
            :icon="Trophy"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/codex')"
            @click="router.push('/codex')"
            label="Codex"
            :icon="PenTool"
            :collapsed="isCollapsed && !isMobileOpen"
          />
        </NavGroup>

        <NavGroup label="Exchange" :collapsed="isCollapsed && !isMobileOpen">
          <SidebarItem
            :active="isActive('/correspondence')"
            @click="router.push('/correspondence')"
            label="Messages"
            :icon="MessageSquare"
            :badge="unreadBadge"
            :collapsed="isCollapsed && !isMobileOpen"
          />
          <SidebarItem
            :active="isActive('/circles')"
            @click="router.push('/circles')"
            label="Circles"
            :icon="CircleDot"
            :collapsed="isCollapsed && !isMobileOpen"
          />
        </NavGroup>
      </nav>
    </div>

    <!-- Profile Card with Dropdown -->
    <div class="border-t border-slate-800/50 flex-shrink-0">
      <div :class="[isCollapsed && !isMobileOpen ? 'p-2' : 'p-3']">
        <DropdownMenu>
          <DropdownMenuTrigger as-child>
            <button
              :class="[
                'profile-btn group w-full flex items-center gap-2.5 rounded-xl transition-all duration-200 cursor-pointer',
                isCollapsed && !isMobileOpen ? 'p-1.5 justify-center' : 'p-2'
              ]"
            >
              <div class="p-0.5 rounded-lg bg-transparent group-hover:bg-gradient-to-tr group-hover:from-indigo-500 group-hover:to-purple-500 transition-all flex-shrink-0">
                <div class="w-8 h-8 rounded-md bg-slate-800 flex items-center justify-center text-xs font-bold text-white overflow-hidden">
                  <img v-if="userAvatarUrl && !sidebarAvatarError" :src="userAvatarUrl" @error="sidebarAvatarError = true" class="w-full h-full object-cover" />
                  <span v-else>{{ userInitials }}</span>
                </div>
              </div>
              <div v-show="!isCollapsed || isMobileOpen" class="flex-1 text-left min-w-0">
                <p class="text-xs font-semibold text-white truncate">{{ userName }}</p>
                <p class="text-[9px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                  <Hexagon :size="8" class="fill-indigo-400" />
                  Premium Member
                </p>
              </div>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" side="top" class="w-56 mb-2">
            <DropdownMenuItem @click="router.push(`/users/${authStore.user?.id}`)">
              <User class="w-4 h-4 mr-2" />
              Profile
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
    </div>
  </aside>
</template>

<style>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
}

/* Profile button - dark theme (default) */
.profile-btn {
  background: rgba(15, 23, 42, 0.5);
}
.profile-btn:hover {
  background: rgba(255, 255, 255, 0.08) !important;
}

/* Profile button - light theme */
body.light .profile-btn {
  background: transparent;
}
body.light .profile-btn:hover {
  background: rgba(0, 0, 0, 0.1) !important;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}


.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
