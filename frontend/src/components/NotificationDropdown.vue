<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell } from 'lucide-vue-next'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import api from '@/services/api'

const router = useRouter()
const notifications = ref([])
const loading = ref(false)

const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

const loadNotifications = async () => {
  loading.value = true
  try {
    const response = await api.get('/social/notifications/')
    notifications.value = response.data.results || response.data
  } catch (error) {
    console.error('Error loading notifications:', error)
  } finally {
    loading.value = false
  }
}

const markAsRead = async (notification) => {
  if (notification.is_read) return

  try {
    await api.post(`/social/notifications/${notification.id}/mark_read/`)
    notification.is_read = true
  } catch (error) {
    console.error('Error marking notification as read:', error)
  }
}

const handleNotificationClick = async (notification) => {
  await markAsRead(notification)

  // Navigate based on notification type
  if (notification.notification_type === 'new_follower' && notification.actor) {
    router.push(`/users/${notification.actor.id}`)
  }
}

const markAllAsRead = async () => {
  try {
    await api.post('/social/notifications/mark_all_read/')
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('Error marking all as read:', error)
  }
}

const formatTimeAgo = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return `${Math.floor(seconds / 604800)}w ago`
}

onMounted(() => {
  loadNotifications()
  // Poll for new notifications every 30 seconds
  setInterval(loadNotifications, 30000)
})
</script>

<template>
  <DropdownMenu>
    <DropdownMenuTrigger as-child>
      <button
        class="relative p-2 rounded-lg border border-slate-800 bg-slate-900 text-slate-400 hover:text-indigo-400 hover:border-indigo-500/30 transition-all"
        aria-label="Notifications"
      >
        <Bell :size="18" />
        <span
          v-if="unreadCount > 0"
          class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-indigo-500 text-white text-[10px] font-bold flex items-center justify-center"
        >
          {{ unreadCount > 9 ? '9+' : unreadCount }}
        </span>
      </button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="w-80">
      <DropdownMenuLabel class="flex items-center justify-between">
        <span>Notifications</span>
        <button
          v-if="unreadCount > 0"
          @click="markAllAsRead"
          class="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
        >
          Mark all as read
        </button>
      </DropdownMenuLabel>
      <DropdownMenuSeparator />

      <!-- Loading State -->
      <div v-if="loading" class="p-8 text-center">
        <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto" />
      </div>

      <!-- Empty State -->
      <div v-else-if="notifications.length === 0" class="p-8 text-center text-slate-500 text-sm">
        No notifications yet
      </div>

      <!-- Notifications List -->
      <div v-else class="max-h-96 overflow-y-auto">
        <DropdownMenuItem
          v-for="notification in notifications"
          :key="notification.id"
          @click="handleNotificationClick(notification)"
          :class="[
            'cursor-pointer flex items-start gap-3 p-3',
            !notification.is_read ? 'bg-indigo-500/5' : ''
          ]"
        >
          <!-- Actor Avatar -->
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center flex-shrink-0 overflow-hidden">
            <img
              v-if="notification.actor?.avatar"
              :src="notification.actor.avatar"
              class="w-full h-full object-cover"
            />
            <span v-else class="text-white text-xs font-bold">
              {{ notification.actor?.first_name?.[0]?.toUpperCase() || '?' }}
            </span>
          </div>

          <!-- Notification Content -->
          <div class="flex-1 min-w-0">
            <p class="text-sm text-slate-200 leading-snug mb-1">
              {{ notification.message }}
            </p>
            <p class="text-xs text-slate-500">
              {{ formatTimeAgo(notification.created_at) }}
            </p>
          </div>

          <!-- Unread Indicator -->
          <div
            v-if="!notification.is_read"
            class="w-2 h-2 rounded-full bg-indigo-500 flex-shrink-0 mt-1"
          />
        </DropdownMenuItem>
      </div>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
