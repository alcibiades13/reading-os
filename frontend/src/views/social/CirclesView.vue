<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { bookClubService } from '@/services/bookClubService'
import { socialService } from '@/services/socialService'
import { useAuthStore } from '@/stores/authStore'
import {
  Users, Sparkles, Lock, ChevronRight, X, Check,
  MessageSquare, Hash, Plus, Send, Paperclip,
  Quote, Brain, MoreVertical, Filter, BookOpen,
  Globe, Heart, Settings, UserPlus, Trash2, Crown,
  Mail, Search, AlertCircle, ChevronDown, ArrowLeft,
  Info, Share2
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

// State
const circles = ref([])
const pendingInvitations = ref([])
const activeCircleId = ref(null)
const activeTopicId = ref(null)
const messages = ref([])
const messageInput = ref('')
const loading = ref(true)
const sendingMessage = ref(false)
const processingInvitation = ref(null) // Track which invitation is being processed
const messagesContainerRef = ref(null)

// Mobile state
const mobileView = ref('topics') // 'topics' | 'chat'
const showCircleSelector = ref(false)
const showMobileTopicMenu = ref(false)

// Mobile navigation
const openMobileChat = (topicId) => {
  activeTopicId.value = topicId
  mobileView.value = 'chat'
}

const closeMobileChat = () => {
  mobileView.value = 'topics'
  activeTopicId.value = null
}

const selectCircle = (circleId) => {
  activeCircleId.value = circleId
  showCircleSelector.value = false
  mobileView.value = 'topics'
}

// Scroll to bottom of messages
const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainerRef.value) {
    messagesContainerRef.value.scrollTop = messagesContainerRef.value.scrollHeight
  }
}

// Modal states
const showCreateCircleModal = ref(false)
const showCreateTopicModal = ref(false)
const showInviteModal = ref(false)
const showSettingsModal = ref(false)
const showMembersModal = ref(false)

// Form states
const circleForm = ref({
  name: '',
  description: '',
  is_invite_only: true,
  accent_color: '#6366f1',
  max_members: 20
})
const topicForm = ref({
  title: '',
  description: '',
  category: 'general',
  is_locked: false,
  required_progress: 0
})
const inviteSearch = ref('')
const inviteResults = ref([])
const inviteMessage = ref('')
const searchingUsers = ref(false)
const creatingCircle = ref(false)
const creatingTopic = ref(false)
const sendingInvite = ref(false)

// Color presets for circles
const colorPresets = [
  '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
  '#f59e0b', '#10b981', '#06b6d4', '#3b82f6'
]

// Category options
const categoryOptions = [
  { value: 'general', label: 'General Discussion', color: 'bg-indigo-500/20 text-indigo-400' },
  { value: 'spoilers', label: 'Spoilers', color: 'bg-rose-500/20 text-rose-400' },
  { value: 'theories', label: 'Theories', color: 'bg-amber-500/20 text-amber-400' },
  { value: 'characters', label: 'Characters', color: 'bg-emerald-500/20 text-emerald-400' },
  { value: 'themes', label: 'Themes', color: 'bg-purple-500/20 text-purple-400' },
  { value: 'quotes', label: 'Favorite Quotes', color: 'bg-cyan-500/20 text-cyan-400' }
]

// Computed
const activeCircle = computed(() => circles.value.find(c => c.id === activeCircleId.value))
const activeTopic = computed(() => activeCircle.value?.topics?.find(t => t.id === activeTopicId.value))
const isCircleAdmin = computed(() => {
  if (!activeCircle.value) return false
  return activeCircle.value.creator?.id === authStore.user?.id ||
    activeCircle.value.memberships?.some(m => m.user?.id === authStore.user?.id && m.role === 'admin')
})

// Load circles and invitations on mount
onMounted(async () => {
  await Promise.all([loadCircles(), loadPendingInvitations()])
})

// Watch for circle change - reset topic
watch(activeCircleId, async (newId) => {
  activeTopicId.value = null
  messages.value = []
  if (newId) {
    await loadCircleDetail(newId)
  }
})

// Watch for topic change - load messages
watch(activeTopicId, async (newId) => {
  if (newId) {
    await loadTopicMessages(newId)
  }
})

async function loadCircles() {
  loading.value = true
  try {
    const data = await bookClubService.getCircles()
    circles.value = data.results || data || []
    if (circles.value.length > 0 && !activeCircleId.value) {
      activeCircleId.value = circles.value[0].id
    }
  } catch (error) {
    console.error('Error loading circles:', error)
  } finally {
    loading.value = false
  }
}

async function loadCircleDetail(circleId) {
  try {
    const detail = await bookClubService.getCircle(circleId)
    // Update circle in list with full details
    const idx = circles.value.findIndex(c => c.id === circleId)
    if (idx !== -1) {
      circles.value[idx] = { ...circles.value[idx], ...detail }
    }
  } catch (error) {
    console.error('Error loading circle detail:', error)
  }
}

async function loadPendingInvitations() {
  try {
    const data = await bookClubService.getInvitations()
    // Filter only pending invitations
    pendingInvitations.value = (data.results || data || []).filter(inv => inv.status === 'pending')
  } catch (error) {
    console.error('Error loading invitations:', error)
  }
}

async function handleAcceptInvitation(invitationId) {
  processingInvitation.value = invitationId
  try {
    await bookClubService.acceptInvitation(invitationId)
    // Remove from pending list
    pendingInvitations.value = pendingInvitations.value.filter(inv => inv.id !== invitationId)
    // Reload circles to show the new circle
    await loadCircles()
  } catch (error) {
    console.error('Error accepting invitation:', error)
  } finally {
    processingInvitation.value = null
  }
}

async function handleDeclineInvitation(invitationId) {
  processingInvitation.value = invitationId
  try {
    await bookClubService.declineInvitation(invitationId)
    // Remove from pending list
    pendingInvitations.value = pendingInvitations.value.filter(inv => inv.id !== invitationId)
  } catch (error) {
    console.error('Error declining invitation:', error)
  } finally {
    processingInvitation.value = null
  }
}

async function loadTopicMessages(topicId) {
  try {
    const data = await bookClubService.getTopicMessages(topicId)
    messages.value = data.results || data || []
    scrollToBottom()
  } catch (error) {
    console.error('Error loading messages:', error)
  }
}

async function handleSendMessage() {
  if (!messageInput.value.trim() || !activeTopicId.value) return

  sendingMessage.value = true
  try {
    const newMessage = await bookClubService.sendTopicMessage({
      topic: activeTopicId.value,
      content: messageInput.value
    })
    // Ensure author data is present (API might not return full author object)
    if (!newMessage.author || !newMessage.author.first_name) {
      newMessage.author = {
        id: authStore.user?.id,
        first_name: authStore.user?.first_name,
        last_name: authStore.user?.last_name,
        email: authStore.user?.email,
        avatar: authStore.user?.avatar
      }
    }
    messages.value.push(newMessage)
    messageInput.value = ''
    scrollToBottom()
  } catch (error) {
    console.error('Error sending message:', error)
  } finally {
    sendingMessage.value = false
  }
}

async function handleToggleLike(messageId) {
  try {
    const result = await bookClubService.toggleMessageLike(messageId)
    const msg = messages.value.find(m => m.id === messageId)
    if (msg) {
      msg.is_liked = result.liked
      msg.likes_count = result.likes_count
    }
  } catch (error) {
    console.error('Error toggling like:', error)
  }
}

// ===== CREATE CIRCLE =====
function openCreateCircleModal() {
  circleForm.value = {
    name: '',
    description: '',
    is_invite_only: true,
    accent_color: '#6366f1',
    max_members: 20
  }
  showCreateCircleModal.value = true
}

async function handleCreateCircle() {
  if (!circleForm.value.name.trim()) return

  creatingCircle.value = true
  try {
    const newCircle = await bookClubService.createCircle(circleForm.value)
    circles.value.unshift(newCircle)
    activeCircleId.value = newCircle.id
    showCreateCircleModal.value = false
  } catch (error) {
    console.error('Error creating circle:', error)
  } finally {
    creatingCircle.value = false
  }
}

// ===== CREATE TOPIC =====
function openCreateTopicModal() {
  topicForm.value = {
    title: '',
    description: '',
    category: 'general',
    is_locked: false,
    required_progress: 0
  }
  topicError.value = ''
  showCreateTopicModal.value = true
}

const topicError = ref('')

async function handleCreateTopic() {
  console.log('handleCreateTopic called', { title: topicForm.value.title, activeCircleId: activeCircleId.value })
  topicError.value = ''

  if (!topicForm.value.title.trim()) {
    topicError.value = 'Please enter a topic title'
    return
  }

  if (!activeCircleId.value) {
    topicError.value = 'No circle selected'
    return
  }

  creatingTopic.value = true
  try {
    const payload = {
      title: topicForm.value.title,
      description: topicForm.value.description,
      category: topicForm.value.category,
      is_locked: topicForm.value.is_locked,
      required_progress: topicForm.value.is_locked ? topicForm.value.required_progress : 0,
      circle: activeCircleId.value
    }
    console.log('Creating topic with payload:', payload)

    const newTopic = await bookClubService.createTopic(payload)
    console.log('Topic created:', newTopic)

    // Reload circle to get updated topics
    await loadCircleDetail(activeCircleId.value)
    showCreateTopicModal.value = false
    activeTopicId.value = newTopic.id
  } catch (error) {
    console.error('Error creating topic:', error)
    if (error.response?.data) {
      // Format API error messages
      const errors = error.response.data
      if (typeof errors === 'object') {
        topicError.value = Object.values(errors).flat().join(', ')
      } else {
        topicError.value = String(errors)
      }
    } else {
      topicError.value = 'Failed to create topic. Please try again.'
    }
  } finally {
    creatingTopic.value = false
  }
}

// ===== INVITE MEMBERS =====
const inviteSentTo = ref([]) // Track who we've sent invites to

function openInviteModal() {
  inviteSearch.value = ''
  inviteResults.value = []
  inviteMessage.value = ''
  inviteError.value = ''
  inviteSentTo.value = []
  showInviteModal.value = true
}

async function searchUsers() {
  if (!inviteSearch.value.trim() || inviteSearch.value.length < 2) {
    inviteResults.value = []
    return
  }

  searchingUsers.value = true
  try {
    const data = await socialService.searchUsers(inviteSearch.value)
    // Filter out users already in circle
    const memberIds = activeCircle.value?.memberships?.map(m => m.user?.id) || []
    inviteResults.value = (data.results || data || []).filter(u => !memberIds.includes(u.id))
  } catch (error) {
    console.error('Error searching users:', error)
  } finally {
    searchingUsers.value = false
  }
}

const inviteError = ref('')

async function handleSendInvite(userId) {
  if (!activeCircleId.value) return

  inviteError.value = ''
  sendingInvite.value = true
  try {
    console.log('Sending invite:', { circleId: activeCircleId.value, userId, message: inviteMessage.value })
    await bookClubService.sendInvitation(activeCircleId.value, userId, inviteMessage.value)
    // Track successful invite
    const user = inviteResults.value.find(u => u.id === userId)
    if (user) {
      inviteSentTo.value.push({ id: user.id, name: `${user.first_name} ${user.last_name}`.trim() || user.email })
    }
    // Remove from results
    inviteResults.value = inviteResults.value.filter(u => u.id !== userId)
  } catch (error) {
    console.error('Error sending invite:', error)
    console.error('Error response data:', error.response?.data)
    if (error.response?.data) {
      const errors = error.response.data
      if (typeof errors === 'object' && !Array.isArray(errors)) {
        inviteError.value = Object.values(errors).flat().join(', ')
      } else if (Array.isArray(errors)) {
        inviteError.value = errors.join(', ')
      } else {
        inviteError.value = String(errors)
      }
    } else {
      inviteError.value = 'Failed to send invitation'
    }
  } finally {
    sendingInvite.value = false
  }
}

// ===== SETTINGS =====
async function handleUpdateCircle() {
  if (!activeCircle.value) return

  try {
    const updated = await bookClubService.updateCircle(activeCircle.value.id, {
      name: activeCircle.value.name,
      description: activeCircle.value.description,
      is_invite_only: activeCircle.value.is_invite_only,
      accent_color: activeCircle.value.accent_color,
      max_members: activeCircle.value.max_members
    })
    const idx = circles.value.findIndex(c => c.id === updated.id)
    if (idx !== -1) {
      circles.value[idx] = { ...circles.value[idx], ...updated }
    }
    showSettingsModal.value = false
  } catch (error) {
    console.error('Error updating circle:', error)
  }
}

async function handleDeleteCircle() {
  if (!activeCircle.value || !confirm('Are you sure you want to delete this circle?')) return

  try {
    await bookClubService.deleteCircle(activeCircle.value.id)
    circles.value = circles.value.filter(c => c.id !== activeCircle.value.id)
    activeCircleId.value = circles.value[0]?.id || null
    showSettingsModal.value = false
  } catch (error) {
    console.error('Error deleting circle:', error)
  }
}

async function handleLeaveCircle() {
  if (!activeCircle.value || !confirm('Are you sure you want to leave this circle?')) return

  try {
    await bookClubService.leaveCircle(activeCircle.value.id)
    circles.value = circles.value.filter(c => c.id !== activeCircle.value.id)
    activeCircleId.value = circles.value[0]?.id || null
    showSettingsModal.value = false
  } catch (error) {
    console.error('Error leaving circle:', error)
  }
}

async function handlePromoteMember(userId) {
  if (!activeCircle.value) return

  try {
    await bookClubService.promoteMember(activeCircle.value.id, userId)
    await loadCircleDetail(activeCircle.value.id)
  } catch (error) {
    console.error('Error promoting member:', error)
  }
}

function getCategoryClass(category) {
  const info = bookClubService.getCategoryInfo(category)
  return info.color
}

function formatTimeAgo(date) {
  return bookClubService.formatTimeAgo(date)
}

function isRecentActivity(dateString) {
  if (!dateString) return false
  const date = new Date(dateString)
  const now = new Date()
  const hoursDiff = (now - date) / (1000 * 60 * 60)
  return hoursDiff < 24 // Show "NEW" badge if activity in last 24 hours
}

function getUserInitial(user) {
  return user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'
}
</script>

<template>
  <div class="h-full flex bg-slate-950 animate-in fade-in duration-500">

    <!-- Loading State -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty State -->
    <div v-else-if="circles.length === 0" class="flex-1 flex flex-col items-center justify-center p-20 text-center">
      <!-- Pending Invitations (when no circles) -->
      <div v-if="pendingInvitations.length > 0" class="w-full max-w-lg mb-12">
        <h3 class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-4 flex items-center justify-center gap-2">
          <Mail :size="14" /> Pending Invitations
        </h3>
        <div class="space-y-3">
          <div
            v-for="invitation in pendingInvitations"
            :key="invitation.id"
            class="p-4 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-4"
          >
            <div
              class="w-12 h-12 rounded-xl shrink-0 flex items-center justify-center text-white font-black text-sm shadow-lg"
              :style="{ background: `linear-gradient(135deg, ${invitation.circle?.accent_color || '#6366f1'}dd, #000000)` }"
            >
              {{ invitation.circle?.name?.charAt(0) || '?' }}
            </div>
            <div class="flex-1 min-w-0 text-left">
              <p class="text-white font-bold truncate">{{ invitation.circle?.name }}</p>
              <p class="text-xs text-slate-500">
                Invited by {{ invitation.from_user?.first_name }} {{ invitation.from_user?.last_name }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <button
                @click="handleDeclineInvitation(invitation.id)"
                :disabled="processingInvitation === invitation.id"
                class="p-2 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 transition-colors disabled:opacity-50"
              >
                <X :size="16" />
              </button>
              <button
                @click="handleAcceptInvitation(invitation.id)"
                :disabled="processingInvitation === invitation.id"
                class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
              >
                <Check :size="16" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="w-24 h-24 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mb-8">
        <Users :size="48" class="text-slate-600" />
      </div>
      <h2 class="text-2xl font-black text-white uppercase tracking-widest mb-4">No Circles Yet</h2>
      <p class="text-slate-500 max-w-md mb-8">
        Join or create a reading circle to discuss books with fellow readers.
      </p>
      <button
        @click="openCreateCircleModal"
        class="px-6 py-3 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors flex items-center gap-2"
      >
        <Plus :size="18" />
        Create Your First Circle
      </button>
    </div>

    <template v-else>
      <!-- ==================== DESKTOP LAYOUT ==================== -->
      <div class="hidden lg:flex flex-1">
        <!-- DESKTOP: Circles Sidebar -->
        <aside class="w-72 border-r border-white/5 flex flex-col backdrop-blur-3xl z-40 bg-slate-950/40">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">Circles</h2>
            <button
              @click="openCreateCircleModal"
              class="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all"
            >
              <Plus :size="18" />
            </button>
          </div>

          <div class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
            <button
              v-for="circle in circles"
              :key="circle.id"
              @click="activeCircleId = circle.id"
              :class="[
                'w-full group relative flex items-center gap-4 p-3 rounded-2xl transition-all',
                activeCircleId === circle.id
                  ? 'bg-white/10 shadow-[0_10px_30px_rgba(0,0,0,0.5)]'
                  : 'hover:bg-white/5'
              ]"
            >
              <div v-if="activeCircleId === circle.id" class="absolute left-0 w-1 h-8 bg-indigo-500 rounded-r-full" />
              <div
                class="w-12 h-12 rounded-2xl shrink-0 flex items-center justify-center text-white font-black text-xs shadow-lg"
                :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}dd, #000000)` }"
              >
                {{ circle.name?.charAt(0) }}
              </div>
              <div class="text-left min-w-0">
                <p :class="['text-sm font-bold truncate', activeCircleId === circle.id ? 'text-white' : 'text-slate-400']">
                  {{ circle.name }}
                </p>
                <div class="flex items-center gap-2 mt-0.5">
                  <Users :size="10" class="text-slate-600" />
                  <span class="text-[9px] font-black text-slate-500 uppercase">{{ circle.members_count }} Members</span>
                </div>
              </div>
            </button>
          </div>

          <div class="p-6 border-t border-white/5">
            <div v-if="pendingInvitations.length > 0" class="space-y-2 mb-4">
              <p class="text-[10px] font-black text-amber-400 uppercase tracking-widest flex items-center gap-2">
                <Mail :size="12" /> {{ pendingInvitations.length }} Pending
              </p>
              <div
                v-for="invitation in pendingInvitations"
                :key="invitation.id"
                class="p-3 rounded-xl bg-amber-500/5 border border-amber-500/10"
              >
                <p class="text-xs text-white font-bold truncate mb-1">{{ invitation.circle?.name }}</p>
                <div class="flex gap-2">
                  <button
                    @click="handleDeclineInvitation(invitation.id)"
                    :disabled="processingInvitation === invitation.id"
                    class="flex-1 px-2 py-1 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 text-[10px] font-bold transition-colors disabled:opacity-50"
                  >
                    Decline
                  </button>
                  <button
                    @click="handleAcceptInvitation(invitation.id)"
                    :disabled="processingInvitation === invitation.id"
                    class="flex-1 px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 text-[10px] font-bold transition-colors disabled:opacity-50"
                  >
                    Accept
                  </button>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- DESKTOP: Main Content -->
        <main v-if="activeCircle" class="flex-1 flex flex-col overflow-hidden bg-transparent">
          <!-- Desktop Header -->
          <header class="px-6 py-3 border-b border-white/5 shrink-0 bg-slate-900/50">
            <div class="flex items-center justify-between gap-4">
              <div class="flex items-center gap-3 min-w-0">
                <h1 class="text-xl font-black text-white tracking-tight truncate">{{ activeCircle.name }}</h1>
                <span class="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black text-indigo-400 uppercase tracking-wider shrink-0">
                  {{ activeCircle.is_invite_only ? 'Private' : 'Open' }}
                </span>
              </div>
              <div class="flex items-center gap-4 shrink-0">
                <div v-if="activeCircle.current_book_data" class="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5">
                  <div class="w-6 h-8 rounded overflow-hidden shrink-0">
                    <img v-if="activeCircle.current_book_data.cover_image" :src="activeCircle.current_book_data.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="10" class="text-slate-600" /></div>
                  </div>
                  <div class="text-[10px]">
                    <p class="text-slate-400 truncate max-w-[120px]">{{ activeCircle.current_book_data.title }}</p>
                    <div class="flex items-center gap-1.5">
                      <div class="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div class="h-full bg-indigo-500 rounded-full" :style="{ width: `${activeCircle.average_progress || 0}%` }" />
                      </div>
                      <span class="text-indigo-400 font-bold">{{ activeCircle.average_progress || 0 }}%</span>
                    </div>
                  </div>
                </div>
                <button v-if="isCircleAdmin" @click="openInviteModal" class="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors" title="Invite Members">
                  <UserPlus :size="14" />
                </button>
                <button @click="showSettingsModal = true" class="p-1.5 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors" title="Settings">
                  <Settings :size="14" />
                </button>
                <button @click="showMembersModal = true" class="px-2 py-1.5 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors flex items-center gap-1.5" title="View Members">
                  <Users :size="14" />
                  <span class="text-xs font-bold">{{ activeCircle.members_count }}</span>
                </button>
              </div>
            </div>
          </header>

          <!-- Desktop Topics & Chat -->
          <div class="flex-1 flex overflow-hidden">
            <!-- Topics List -->
            <div class="w-96 border-r border-white/5 flex flex-col bg-slate-950/20">
              <div class="p-6 flex items-center justify-between shrink-0">
                <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Discourses</h3>
                <button @click="openCreateTopicModal" class="flex items-center gap-1.5 px-2 py-1 rounded-lg bg-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase hover:bg-indigo-500/20 transition-colors">
                  <Plus :size="12" /> New
                </button>
              </div>
              <div class="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
                <div v-if="!activeCircle.topics?.length" class="text-center py-10">
                  <MessageSquare :size="32" class="text-slate-700 mx-auto mb-3" />
                  <p class="text-slate-500 text-sm mb-4">No discussions yet</p>
                  <button @click="openCreateTopicModal" class="px-4 py-2 rounded-xl bg-indigo-500/10 text-indigo-400 text-sm font-bold hover:bg-indigo-500/20 transition-colors">Start a Discussion</button>
                </div>
                <button
                  v-for="topic in activeCircle.topics"
                  :key="topic.id"
                  @click="activeTopicId = topic.id"
                  :class="['w-full text-left p-6 rounded-3xl border transition-all relative overflow-hidden group', activeTopicId === topic.id ? 'bg-indigo-500/10 border-indigo-500/40 shadow-xl' : 'bg-white/5 border-white/5 hover:bg-white/[0.08]']"
                >
                  <div v-if="topic.is_locked && !topic.can_access" class="absolute inset-0 bg-slate-950/60 backdrop-blur-sm z-10 flex flex-col items-center justify-center p-4 text-center">
                    <Lock :size="20" class="text-slate-500 mb-2" />
                    <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Restricted</p>
                  </div>
                  <div class="relative z-0">
                    <div class="flex items-center justify-between mb-3">
                      <div :class="['px-2 py-0.5 rounded-lg text-[8px] font-black uppercase tracking-widest', getCategoryClass(topic.category)]">{{ topic.category }}</div>
                      <div class="flex items-center gap-2">
                        <div v-if="isRecentActivity(topic.last_activity)" class="w-2 h-2 rounded-full bg-indigo-500" />
                        <span class="text-[10px] text-slate-600 font-bold">{{ formatTimeAgo(topic.last_activity) }}</span>
                      </div>
                    </div>
                    <h4 class="text-base font-bold text-white mb-2 group-hover:text-indigo-400 transition-colors">{{ topic.title }}</h4>
                    <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed mb-4">{{ topic.description }}</p>
                    <div class="flex items-center gap-4 text-[10px] font-black text-slate-600 uppercase">
                      <span class="flex items-center gap-1.5"><MessageSquare :size="12" /> {{ topic.message_count || 0 }} posts</span>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <!-- Desktop Chat -->
            <div class="flex-1 flex flex-col bg-slate-950/40 relative">
            <template v-if="activeTopic">
              <!-- Messages -->
              <div ref="messagesContainerRef" class="flex-1 overflow-y-auto p-10 custom-scrollbar space-y-8">
                <div class="text-center py-10 opacity-30">
                  <div class="h-px w-full bg-gradient-to-r from-transparent via-slate-800 to-transparent mb-4" />
                  <span class="text-[10px] font-black uppercase tracking-[0.5em] text-slate-500">Beginning of Discourse</span>
                </div>

                <div v-if="messages.length === 0" class="text-center py-10 text-slate-500">
                  <p>No messages yet. Be the first to contribute!</p>
                </div>

                <div v-for="msg in messages" :key="msg.id" class="flex gap-6 group">
                  <div class="w-12 h-12 rounded-2xl bg-indigo-500/20 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-black text-sm shrink-0 shadow-lg group-hover:scale-110 transition-transform overflow-hidden">
                    <img v-if="msg.author?.avatar" :src="msg.author.avatar" class="w-full h-full object-cover" />
                    <span v-else>{{ getUserInitial(msg.author) }}</span>
                  </div>
                  <div class="flex-1 space-y-3">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-3">
                        <span class="text-sm font-black text-white">
                          {{ msg.author?.first_name }} {{ msg.author?.last_name }}
                        </span>
                        <span class="text-[10px] font-bold text-slate-600 uppercase tracking-widest">
                          {{ formatTimeAgo(msg.created_at) }}
                        </span>
                      </div>
                      <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          @click="handleToggleLike(msg.id)"
                          :class="['p-2 rounded-lg transition-colors', msg.is_liked ? 'text-rose-400' : 'text-slate-700 hover:text-slate-400']"
                        >
                          <Heart :size="14" :class="msg.is_liked ? 'fill-current' : ''" />
                        </button>
                        <span v-if="msg.likes_count" class="text-xs text-slate-500">{{ msg.likes_count }}</span>
                      </div>
                    </div>
                    <div class="text-lg font-serif text-slate-300 leading-relaxed">
                      {{ msg.content }}
                    </div>

                    <!-- Attachment -->
                    <div
                      v-if="msg.attached_quote_data"
                      class="p-4 rounded-2xl bg-white/5 border border-white/5 flex items-center gap-4 mt-4 max-w-sm"
                    >
                      <Quote :size="14" class="text-indigo-500 shrink-0" />
                      <div class="min-w-0">
                        <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Shared Quote</p>
                        <p class="text-xs text-slate-400 truncate italic">"{{ msg.attached_quote_data.content }}"</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="h-20" />
              </div>

              <!-- Topic Composer -->
              <div class="p-6 lg:p-8 glass border-t border-white/5 bg-slate-950/80 backdrop-blur-3xl sticky bottom-0">
                <div class="max-w-4xl mx-auto flex items-end gap-4 lg:gap-6">
                  <div class="flex-1 relative">
                    <textarea
                      v-model="messageInput"
                      @keydown.ctrl.enter="handleSendMessage"
                      :placeholder="'Share your thoughts on ' + activeTopic.title + '...'"
                      class="w-full bg-white/5 border border-white/10 rounded-2xl lg:rounded-3xl px-6 lg:px-8 py-4 lg:py-5 text-slate-100 placeholder-slate-600 focus:border-indigo-500 outline-none transition-all min-h-[60px] lg:min-h-[80px] max-h-40 resize-none font-serif text-base lg:text-lg"
                    />
                    <div class="absolute right-4 lg:right-6 bottom-4 lg:bottom-5 flex items-center gap-2">
                      <button class="p-2 text-slate-500 hover:text-indigo-400 transition-colors">
                        <Paperclip :size="18" />
                      </button>
                      <button class="p-2 text-slate-500 hover:text-emerald-400 transition-colors">
                        <Brain :size="18" />
                      </button>
                    </div>
                  </div>
                  <button
                    @click="handleSendMessage"
                    :disabled="!messageInput.trim() || sendingMessage"
                    class="w-12 h-12 lg:w-16 lg:h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-2xl shadow-indigo-500/40 hover:scale-110 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Send :size="20" class="lg:hidden" />
                    <Send :size="24" class="hidden lg:block" />
                  </button>
                </div>
              </div>
            </template>

            <!-- No Topic Selected -->
            <div v-else class="flex-1 flex flex-col items-center justify-center text-center p-20 opacity-30">
              <div class="w-24 h-24 rounded-full border-2 border-dashed border-slate-700 flex items-center justify-center mb-8">
                <MessageSquare :size="48" class="text-slate-600" />
              </div>
              <h3 class="text-2xl font-black text-white uppercase tracking-widest mb-4">Select a Discourse</h3>
              <p class="max-w-xs text-slate-500 font-medium leading-relaxed">
                Join an ongoing thematic discussion or explore the archives of this Circle.
              </p>
            </div>
          </div>
        </div>
      </main>
      </div>
      <!-- END DESKTOP LAYOUT -->

      <!-- ==================== MOBILE LAYOUT ==================== -->
      <div class="lg:hidden flex flex-col h-full w-full">

        <!-- MOBILE: Topics View -->
        <template v-if="mobileView === 'topics'">
          <!-- Mobile Header with Circle Selector -->
          <header class="px-4 py-3 border-b border-white/5 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-30">
            <!-- Circle Dropdown -->
            <button
              @click="showCircleSelector = !showCircleSelector"
              class="w-full flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/10"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  v-if="activeCircle"
                  class="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-white font-black text-sm shadow-lg"
                  :style="{ background: `linear-gradient(135deg, ${activeCircle.accent_color || '#6366f1'}dd, #000000)` }"
                >
                  {{ activeCircle.name?.charAt(0) }}
                </div>
                <div class="text-left min-w-0">
                  <p class="text-sm font-bold text-white truncate">{{ activeCircle?.name || 'Select Circle' }}</p>
                  <p class="text-[10px] text-slate-500 uppercase tracking-wider">{{ activeCircle?.members_count || 0 }} members</p>
                </div>
              </div>
              <ChevronDown :size="20" :class="['text-slate-400 transition-transform', showCircleSelector ? 'rotate-180' : '']" />
            </button>

            <!-- Circle Dropdown Overlay (closes dropdown when clicking outside) -->
            <div
              v-if="showCircleSelector"
              class="fixed inset-0 z-30"
              @click="showCircleSelector = false"
            />

            <!-- Circle Dropdown Panel -->
            <div
              v-if="showCircleSelector"
              class="absolute left-4 right-4 top-full mt-2 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-40 max-h-80 overflow-y-auto"
            >
              <div class="p-2 space-y-1">
                <button
                  v-for="circle in circles"
                  :key="circle.id"
                  @click="selectCircle(circle.id)"
                  :class="[
                    'w-full flex items-center gap-3 p-3 rounded-xl transition-all',
                    activeCircleId === circle.id ? 'bg-indigo-500/20' : 'hover:bg-white/5'
                  ]"
                >
                  <div
                    class="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-white font-black text-sm"
                    :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}dd, #000000)` }"
                  >
                    {{ circle.name?.charAt(0) }}
                  </div>
                  <div class="text-left min-w-0">
                    <p :class="['text-sm font-bold truncate', activeCircleId === circle.id ? 'text-white' : 'text-slate-300']">
                      {{ circle.name }}
                    </p>
                    <p class="text-[10px] text-slate-500">{{ circle.members_count }} members</p>
                  </div>
                  <Check v-if="activeCircleId === circle.id" :size="16" class="text-indigo-400 ml-auto shrink-0" />
                </button>
              </div>

              <!-- Create New Circle -->
              <div class="p-2 border-t border-white/5">
                <button
                  @click="showCircleSelector = false; openCreateCircleModal()"
                  class="w-full flex items-center justify-center gap-2 p-3 rounded-xl bg-indigo-500/10 text-indigo-400 font-bold text-sm hover:bg-indigo-500/20 transition-colors"
                >
                  <Plus :size="16" />
                  Create New Circle
                </button>
              </div>
            </div>

            <!-- Pending Invitations Badge -->
            <div v-if="pendingInvitations.length > 0" class="mt-3">
              <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <p class="text-xs font-bold text-amber-400 flex items-center gap-2 mb-2">
                  <Mail :size="14" /> {{ pendingInvitations.length }} Pending Invitation{{ pendingInvitations.length > 1 ? 's' : '' }}
                </p>
                <div class="flex gap-2">
                  <button
                    v-for="inv in pendingInvitations.slice(0, 2)"
                    :key="inv.id"
                    @click="handleAcceptInvitation(inv.id)"
                    :disabled="processingInvitation === inv.id"
                    class="flex-1 px-3 py-2 rounded-lg bg-amber-500/20 text-amber-300 text-xs font-bold truncate disabled:opacity-50"
                  >
                    {{ inv.circle?.name }}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <!-- Mobile Topics List -->
          <div v-if="activeCircle" class="flex-1 overflow-y-auto custom-scrollbar">
            <!-- Circle Actions Bar -->
            <div class="px-4 py-3 flex items-center justify-between border-b border-white/5 bg-slate-950/50 sticky top-0 z-10">
              <h3 class="text-[10px] font-black text-slate-500 uppercase tracking-widest">Discussions</h3>
              <div class="flex items-center gap-2">
                <button @click="showMembersModal = true" class="p-2 rounded-lg bg-white/5 text-slate-400">
                  <Users :size="16" />
                </button>
                <button v-if="isCircleAdmin" @click="openInviteModal" class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <UserPlus :size="16" />
                </button>
                <button @click="showSettingsModal = true" class="p-2 rounded-lg bg-white/5 text-slate-400">
                  <Settings :size="16" />
                </button>
                <button @click="openCreateTopicModal" class="p-2 rounded-lg bg-indigo-500 text-white">
                  <Plus :size="16" />
                </button>
              </div>
            </div>

            <!-- Current Book Card (if any) -->
            <div v-if="activeCircle.current_book_data" class="mx-4 mt-4">
              <div class="p-4 rounded-2xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
                <p class="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-2">Currently Reading</p>
                <div class="flex items-center gap-3">
                  <div class="w-12 h-16 rounded-lg overflow-hidden shrink-0 shadow-lg">
                    <img v-if="activeCircle.current_book_data.cover_image" :src="activeCircle.current_book_data.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="16" class="text-slate-600" /></div>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm font-bold text-white truncate">{{ activeCircle.current_book_data.title }}</p>
                    <p class="text-xs text-slate-500 truncate">{{ activeCircle.current_book_data.author }}</p>
                    <div class="flex items-center gap-2 mt-2">
                      <div class="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div class="h-full bg-indigo-500 rounded-full transition-all" :style="{ width: `${activeCircle.average_progress || 0}%` }" />
                      </div>
                      <span class="text-xs font-bold text-indigo-400">{{ activeCircle.average_progress || 0 }}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Topics -->
            <div class="p-4 space-y-3">
              <div v-if="!activeCircle.topics?.length" class="text-center py-16">
                <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                  <MessageSquare :size="28" class="text-slate-600" />
                </div>
                <p class="text-slate-500 text-sm mb-4">No discussions yet</p>
                <button @click="openCreateTopicModal" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold">
                  Start First Discussion
                </button>
              </div>

              <button
                v-for="topic in activeCircle.topics"
                :key="topic.id"
                @click="openMobileChat(topic.id)"
                class="w-full text-left p-4 rounded-2xl bg-white/5 border border-white/5 active:scale-[0.98] transition-all relative overflow-hidden"
              >
                <div v-if="topic.is_locked && !topic.can_access" class="absolute inset-0 bg-slate-950/70 backdrop-blur-sm z-10 flex items-center justify-center">
                  <Lock :size="20" class="text-slate-500" />
                </div>
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <div :class="['px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-wider', getCategoryClass(topic.category)]">
                        {{ topic.category }}
                      </div>
                      <div v-if="isRecentActivity(topic.last_activity)" class="w-2 h-2 rounded-full bg-indigo-500" />
                    </div>
                    <h4 class="text-base font-bold text-white mb-1 line-clamp-2">{{ topic.title }}</h4>
                    <p v-if="topic.description" class="text-xs text-slate-500 line-clamp-1 mb-2">{{ topic.description }}</p>
                    <div class="flex items-center gap-3 text-[10px] text-slate-600">
                      <span class="flex items-center gap-1"><MessageSquare :size="10" /> {{ topic.message_count || 0 }}</span>
                      <span>{{ formatTimeAgo(topic.last_activity) }}</span>
                    </div>
                  </div>
                  <ChevronRight :size="18" class="text-slate-600 shrink-0 mt-1" />
                </div>
              </button>
            </div>
          </div>
        </template>

        <!-- MOBILE: Chat View -->
        <template v-if="mobileView === 'chat' && activeTopic">
          <!-- Mobile Chat Header -->
          <header class="px-4 py-3 border-b border-white/5 bg-slate-900/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
            <div class="flex items-center gap-3">
              <button
                @click="closeMobileChat"
                class="p-2 -ml-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <ArrowLeft :size="22" />
              </button>
              <div class="flex-1 min-w-0">
                <h1 class="text-base font-bold text-white truncate">{{ activeTopic.title }}</h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-wider">
                  {{ activeCircle?.name }} · {{ activeTopic.message_count || 0 }} posts
                </p>
              </div>
              <div class="relative">
                <button
                  @click="showMobileTopicMenu = !showMobileTopicMenu"
                  class="p-2 rounded-xl text-slate-400 hover:bg-white/5"
                >
                  <MoreVertical :size="18" />
                </button>

                <!-- Dropdown Menu -->
                <div
                  v-if="showMobileTopicMenu"
                  class="fixed inset-0 z-40"
                  @click="showMobileTopicMenu = false"
                />
                <div
                  v-if="showMobileTopicMenu"
                  class="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
                >
                  <button
                    @click="showMobileTopicMenu = false"
                    class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                  >
                    <Info :size="16" class="text-slate-500" />
                    Topic Info
                  </button>
                  <button
                    @click="showMobileTopicMenu = false"
                    class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                  >
                    <Share2 :size="16" class="text-slate-500" />
                    Share Topic
                  </button>
                  <button
                    @click="showMobileTopicMenu = false"
                    class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                  >
                    <Users :size="16" class="text-slate-500" />
                    View Members
                  </button>
                  <div v-if="isCircleAdmin" class="h-px bg-white/5" />
                  <button
                    v-if="isCircleAdmin"
                    @click="showMobileTopicMenu = false"
                    class="w-full px-4 py-3 text-left text-sm text-rose-400 hover:bg-rose-500/10 flex items-center gap-3"
                  >
                    <Trash2 :size="16" />
                    Delete Topic
                  </button>
                </div>
              </div>
            </div>
          </header>

          <!-- Mobile Messages -->
          <div ref="messagesContainerRef" class="flex-1 overflow-y-auto custom-scrollbar">
            <div class="p-4 space-y-4">
              <!-- Beginning indicator -->
              <div class="text-center py-6 opacity-40">
                <div class="h-px w-full bg-gradient-to-r from-transparent via-slate-700 to-transparent mb-3" />
                <span class="text-[9px] font-black uppercase tracking-[0.3em] text-slate-500">Beginning of Discussion</span>
              </div>

              <div v-if="messages.length === 0" class="text-center py-10 text-slate-500 text-sm">
                No messages yet. Be the first to contribute!
              </div>

              <!-- Messages -->
              <div v-for="msg in messages" :key="msg.id" class="flex gap-3">
                <div class="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-xs shrink-0 overflow-hidden">
                  <img v-if="msg.author?.avatar" :src="msg.author.avatar" class="w-full h-full object-cover" />
                  <span v-else>{{ getUserInitial(msg.author) }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-baseline gap-2 mb-1">
                    <span class="text-sm font-bold text-white">
                      {{ msg.author?.first_name }} {{ msg.author?.last_name }}
                    </span>
                    <span class="text-[9px] text-slate-600">{{ formatTimeAgo(msg.created_at) }}</span>
                  </div>
                  <div class="text-sm text-slate-300 leading-relaxed">
                    {{ msg.content }}
                  </div>

                  <!-- Message Actions -->
                  <div class="flex items-center gap-4 mt-2">
                    <button
                      @click="handleToggleLike(msg.id)"
                      :class="['flex items-center gap-1 text-xs transition-colors', msg.is_liked ? 'text-rose-400' : 'text-slate-600']"
                    >
                      <Heart :size="14" :class="msg.is_liked ? 'fill-current' : ''" />
                      <span v-if="msg.likes_count">{{ msg.likes_count }}</span>
                    </button>
                  </div>

                  <!-- Attached Quote -->
                  <div
                    v-if="msg.attached_quote_data"
                    class="mt-2 p-3 rounded-xl bg-white/5 border border-white/5"
                  >
                    <div class="flex items-center gap-2 mb-1">
                      <Quote :size="12" class="text-indigo-500" />
                      <span class="text-[9px] font-black text-indigo-400 uppercase tracking-wider">Shared Quote</span>
                    </div>
                    <p class="text-xs text-slate-400 italic line-clamp-2">"{{ msg.attached_quote_data.content }}"</p>
                  </div>
                </div>
              </div>

              <div class="h-4" />
            </div>
          </div>

          <!-- Mobile Composer -->
          <div class="p-4 border-t border-white/5 bg-slate-950/90 backdrop-blur-xl safe-area-bottom">
            <div class="flex items-end gap-3">
              <div class="flex-1 relative">
                <textarea
                  v-model="messageInput"
                  @keydown.enter.exact.prevent="handleSendMessage"
                  placeholder="Write a message..."
                  rows="1"
                  class="w-full bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-slate-100 placeholder-slate-600 focus:border-indigo-500 outline-none transition-all resize-none text-sm max-h-32"
                  style="field-sizing: content;"
                />
              </div>
              <button
                @click="handleSendMessage"
                :disabled="!messageInput.trim() || sendingMessage"
                class="w-11 h-11 rounded-full bg-indigo-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed shrink-0 active:scale-95 transition-transform"
              >
                <Send :size="18" />
              </button>
            </div>
          </div>
        </template>
      </div>
      <!-- END MOBILE LAYOUT -->

    </template>

    <!-- ===== MODALS ===== -->

    <!-- Create Circle Modal -->
    <Teleport to="body">
      <div v-if="showCreateCircleModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showCreateCircleModal = false" />
        <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-xl font-black text-white">Create a Circle</h2>
            <button @click="showCreateCircleModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="p-6 space-y-6">
            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Circle Name</label>
              <input
                v-model="circleForm.name"
                type="text"
                placeholder="e.g., Philosophy & Flow"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label>
              <textarea
                v-model="circleForm.description"
                placeholder="What's this circle about?"
                rows="3"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none"
              />
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Accent Color</label>
              <div class="flex gap-2">
                <button
                  v-for="color in colorPresets"
                  :key="color"
                  @click="circleForm.accent_color = color"
                  :class="[
                    'w-8 h-8 rounded-full transition-all',
                    circleForm.accent_color === color ? 'ring-2 ring-white ring-offset-2 ring-offset-slate-900 scale-110' : ''
                  ]"
                  :style="{ backgroundColor: color }"
                />
              </div>
            </div>

            <div class="flex items-center justify-between">
              <div>
                <p class="text-sm font-bold text-white">Private Circle</p>
                <p class="text-xs text-slate-500">Members can only join by invitation</p>
              </div>
              <button
                @click="circleForm.is_invite_only = !circleForm.is_invite_only"
                :class="[
                  'w-12 h-6 rounded-full transition-colors relative',
                  circleForm.is_invite_only ? 'bg-indigo-500' : 'bg-slate-700'
                ]"
              >
                <div
                  :class="[
                    'w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all',
                    circleForm.is_invite_only ? 'left-6' : 'left-0.5'
                  ]"
                />
              </button>
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Max Members</label>
              <input
                v-model.number="circleForm.max_members"
                type="number"
                min="2"
                max="100"
                class="w-24 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white focus:border-indigo-500 outline-none transition-colors"
              />
            </div>
          </div>

          <div class="p-6 border-t border-white/5 flex justify-end gap-3">
            <button
              @click="showCreateCircleModal = false"
              class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              @click="handleCreateCircle"
              :disabled="!circleForm.name.trim() || creatingCircle"
              class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <div v-if="creatingCircle" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Create Circle</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Create Topic Modal -->
    <Teleport to="body">
      <div v-if="showCreateTopicModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showCreateTopicModal = false" />
        <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-xl font-black text-white">Start a Discussion</h2>
            <button @click="showCreateTopicModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="p-6 space-y-6">
            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Topic Title</label>
              <input
                v-model="topicForm.title"
                type="text"
                placeholder="What would you like to discuss?"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors"
              />
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label>
              <textarea
                v-model="topicForm.description"
                placeholder="Add some context..."
                rows="3"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none"
              />
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Category</label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="cat in categoryOptions"
                  :key="cat.value"
                  @click="topicForm.category = cat.value"
                  :class="[
                    'px-3 py-2 rounded-xl text-xs font-bold transition-all text-left',
                    topicForm.category === cat.value
                      ? cat.color + ' ring-2 ring-white/20'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10'
                  ]"
                >
                  {{ cat.label }}
                </button>
              </div>
            </div>

            <div class="flex items-center justify-between p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <div>
                <p class="text-sm font-bold text-amber-400 flex items-center gap-2">
                  <Lock :size="14" /> Spoiler Protection
                </p>
                <p class="text-xs text-amber-400/70 mt-1">Lock until readers reach a certain progress</p>
              </div>
              <button
                @click="topicForm.is_locked = !topicForm.is_locked"
                :class="[
                  'w-12 h-6 rounded-full transition-colors relative',
                  topicForm.is_locked ? 'bg-amber-500' : 'bg-slate-700'
                ]"
              >
                <div
                  :class="[
                    'w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all',
                    topicForm.is_locked ? 'left-6' : 'left-0.5'
                  ]"
                />
              </button>
            </div>

            <div v-if="topicForm.is_locked">
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">
                Required Progress ({{ topicForm.required_progress }}%)
              </label>
              <input
                v-model.number="topicForm.required_progress"
                type="range"
                min="10"
                max="100"
                step="10"
                class="w-full accent-amber-500"
              />
            </div>

            <!-- Error Message -->
            <div v-if="topicError" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
              <AlertCircle :size="18" class="text-rose-400 shrink-0 mt-0.5" />
              <p class="text-sm text-rose-400">{{ topicError }}</p>
            </div>
          </div>

          <div class="p-6 border-t border-white/5 flex justify-end gap-3">
            <button
              @click="showCreateTopicModal = false"
              class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              @click="handleCreateTopic"
              :disabled="!topicForm.title.trim() || creatingTopic"
              class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <div v-if="creatingTopic" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Start Discussion</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Invite Members Modal -->
    <Teleport to="body">
      <div v-if="showInviteModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showInviteModal = false" />
        <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-xl font-black text-white">Invite Members</h2>
            <button @click="showInviteModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="p-6 space-y-6">
            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Search Users</label>
              <div class="relative">
                <Search :size="18" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  v-model="inviteSearch"
                  @input="searchUsers"
                  type="text"
                  placeholder="Search by name or email..."
                  class="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors"
                />
              </div>
            </div>

            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Invitation Message (optional)</label>
              <textarea
                v-model="inviteMessage"
                placeholder="Add a personal message..."
                rows="2"
                class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none"
              />
            </div>

            <!-- Search Results -->
            <div v-if="searchingUsers" class="flex items-center justify-center py-8">
              <div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
            </div>

            <div v-else-if="inviteResults.length > 0" class="space-y-2 max-h-60 overflow-y-auto">
              <div
                v-for="user in inviteResults"
                :key="user.id"
                class="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">
                    {{ user.first_name?.[0] || user.email?.[0] || '?' }}
                  </div>
                  <div>
                    <p class="text-sm font-bold text-white">{{ user.first_name }} {{ user.last_name }}</p>
                    <p class="text-xs text-slate-500">{{ user.email }}</p>
                  </div>
                </div>
                <button
                  @click="handleSendInvite(user.id)"
                  :disabled="sendingInvite"
                  class="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50"
                >
                  <Mail :size="14" />
                </button>
              </div>
            </div>

            <div v-else-if="inviteSearch.length >= 2 && inviteSentTo.length === 0" class="text-center py-8 text-slate-500">
              No users found
            </div>

            <!-- Success Message -->
            <div v-if="inviteSentTo.length > 0" class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
              <p class="text-sm font-bold text-emerald-400 mb-2 flex items-center gap-2">
                <Check :size="16" /> Invitations Sent
              </p>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="user in inviteSentTo"
                  :key="user.id"
                  class="px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 text-xs"
                >
                  {{ user.name }}
                </span>
              </div>
            </div>

            <!-- Error Message -->
            <div v-if="inviteError" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
              <AlertCircle :size="18" class="text-rose-400 shrink-0 mt-0.5" />
              <p class="text-sm text-rose-400">{{ inviteError }}</p>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Settings Modal -->
    <Teleport to="body">
      <div v-if="showSettingsModal && activeCircle" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showSettingsModal = false" />
        <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-xl font-black text-white">Circle Settings</h2>
            <button @click="showSettingsModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="p-6 space-y-6">
            <template v-if="isCircleAdmin">
              <div>
                <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Circle Name</label>
                <input
                  v-model="activeCircle.name"
                  type="text"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors"
                />
              </div>

              <div>
                <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label>
                <textarea
                  v-model="activeCircle.description"
                  rows="3"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors resize-none"
                />
              </div>

              <div>
                <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Accent Color</label>
                <div class="flex gap-2">
                  <button
                    v-for="color in colorPresets"
                    :key="color"
                    @click="activeCircle.accent_color = color"
                    :class="[
                      'w-8 h-8 rounded-full transition-all',
                      activeCircle.accent_color === color ? 'ring-2 ring-white ring-offset-2 ring-offset-slate-900 scale-110' : ''
                    ]"
                    :style="{ backgroundColor: color }"
                  />
                </div>
              </div>

              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-bold text-white">Private Circle</p>
                  <p class="text-xs text-slate-500">Members can only join by invitation</p>
                </div>
                <button
                  @click="activeCircle.is_invite_only = !activeCircle.is_invite_only"
                  :class="[
                    'w-12 h-6 rounded-full transition-colors relative',
                    activeCircle.is_invite_only ? 'bg-indigo-500' : 'bg-slate-700'
                  ]"
                >
                  <div
                    :class="[
                      'w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all',
                      activeCircle.is_invite_only ? 'left-6' : 'left-0.5'
                    ]"
                  />
                </button>
              </div>
            </template>

            <template v-else>
              <p class="text-slate-500 text-sm">Only admins can edit circle settings.</p>
            </template>
          </div>

          <div class="p-6 border-t border-white/5 flex items-center justify-between">
            <button
              v-if="isCircleAdmin"
              @click="handleDeleteCircle"
              class="px-4 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors flex items-center gap-2"
            >
              <Trash2 :size="16" /> Delete Circle
            </button>
            <button
              v-else
              @click="handleLeaveCircle"
              class="px-4 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors"
            >
              Leave Circle
            </button>

            <div class="flex gap-3">
              <button
                @click="showSettingsModal = false"
                class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                v-if="isCircleAdmin"
                @click="handleUpdateCircle"
                class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Members Modal -->
    <Teleport to="body">
      <div v-if="showMembersModal && activeCircle" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="showMembersModal = false" />
        <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div class="p-6 border-b border-white/5 flex items-center justify-between">
            <h2 class="text-xl font-black text-white">Members ({{ activeCircle.members_count }})</h2>
            <button @click="showMembersModal = false" class="p-2 text-slate-500 hover:text-white transition-colors">
              <X :size="20" />
            </button>
          </div>

          <div class="p-6 max-h-96 overflow-y-auto space-y-2">
            <div
              v-for="membership in activeCircle.memberships"
              :key="membership.id"
              class="flex items-center justify-between p-3 rounded-xl bg-white/5"
            >
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold overflow-hidden">
                  <img v-if="membership.user?.avatar" :src="membership.user.avatar" class="w-full h-full object-cover" />
                  <span v-else>{{ getUserInitial(membership.user) }}</span>
                </div>
                <div>
                  <p class="text-sm font-bold text-white flex items-center gap-2">
                    {{ membership.user?.first_name }} {{ membership.user?.last_name }}
                    <Crown v-if="membership.role === 'admin'" :size="12" class="text-amber-400" />
                  </p>
                  <p class="text-xs text-slate-500">{{ membership.user?.email }}</p>
                </div>
              </div>
              <button
                v-if="isCircleAdmin && membership.role !== 'admin' && membership.user?.id !== authStore.user?.id"
                @click="handlePromoteMember(membership.user?.id)"
                class="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-xs font-bold hover:bg-amber-500/20 transition-colors"
                title="Promote to Admin"
              >
                <Crown :size="14" />
              </button>
            </div>

            <div v-if="!activeCircle.memberships?.length" class="text-center py-8 text-slate-500">
              No members found
            </div>
          </div>
        </div>
      </div>
    </Teleport>

  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
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

/* Safe area support for notched phones */
.safe-area-top {
  padding-top: max(0.75rem, env(safe-area-inset-top));
}

.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

/* Mobile touch feedback */
@media (max-width: 1023px) {
  button {
    -webkit-tap-highlight-color: transparent;
  }
}
</style>
