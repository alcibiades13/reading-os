<script setup>
import { useAuthStore } from '@/stores/authStore'
import { useRoute } from 'vue-router'
import { onMounted, computed } from 'vue'
import Sidebar from '@/components/Sidebar.vue'
import HeaderNav from '@/components/HeaderNav.vue'
import GradientBackground from '@/components/GradientBackground.vue'
import ToastNotification from '@/components/ToastNotification.vue'
import { useToast } from '@/composables/useToast'

const authStore = useAuthStore()
const route = useRoute()
const { toasts } = useToast()

// Pages that should NOT show navigation
const noNavRoutes = ['/login', '/register', '/404']

const showNavigation = computed(() => {
  return authStore.isAuthenticated && !noNavRoutes.includes(route.path)
})

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
          <HeaderNav />

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