<script setup>
  import { useAuthStore } from '@/stores/authStore'
  import { useRoute } from 'vue-router'
  import { onMounted, computed } from 'vue'
  import Navigation from '@/components/Navigation.vue'
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

      <!-- Navigation - only show when logged in and not on auth pages -->
      <Navigation v-if="showNavigation" />

      <!-- Main content -->
      <router-view />

      <!-- Toast Notifications -->
      <div class="fixed bottom-8 right-8 z-[100] flex flex-col gap-3 pointer-events-none">
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
  .scrollbar-thin::-webkit-scrollbar {
    width: 6px;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    background: rgb(15 23 42);
    border-radius: 10px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    background: rgb(51 65 85);
    border-radius: 10px;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    background: rgb(71 85 105);
  }
  </style>