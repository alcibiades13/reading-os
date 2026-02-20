<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCirclesStore } from '@/stores/circlesStore'
import {
  Users, Plus, BookOpen, Settings, UserPlus, Mail,
  Check, X, ChevronDown, ArrowLeft, MessageSquare,
  MoreVertical, Info, Share2, Trash2, ChevronRight, Lock, Search
} from 'lucide-vue-next'
import { bookClubService } from '@/services/bookClubService'

const route = useRoute()
const router = useRouter()

// Sub-components
import CircleSidebar from '@/components/social/CircleSidebar.vue'
import TopicList from '@/components/social/TopicList.vue'
import MessageThread from '@/components/social/MessageThread.vue'
import MessageComposer from '@/components/social/MessageComposer.vue'
import ReadingDashboard from '@/components/social/ReadingDashboard.vue'
import CircleModals from '@/components/social/CircleModals.vue'
import SearchMessages from '@/components/social/SearchMessages.vue'
import CircleDiscovery from '@/components/social/CircleDiscovery.vue'

const circlesStore = useCirclesStore()

// Template refs
const composerRef = ref(null)

// Collapse circles sidebar when a topic is active to give more space to chat
const sidebarCollapsed = computed(() => !!circlesStore.activeTopicId)

// Mobile state
const showCircleSelector = ref(false)
const showMobileTopicMenu = ref(false)

// Modal states
const showCreateCircleModal = ref(false)
const showCreateTopicModal = ref(false)
const showInviteModal = ref(false)
const showSettingsModal = ref(false)
const showMembersModal = ref(false)
const showSearch = ref(false)
const showEditTopicModal = ref(false)
const editingTopic = ref(null)

function handleEditTopic(topic) {
  editingTopic.value = { ...topic }
  showEditTopicModal.value = true
}

// Suppress route updates during initialization
let suppressRouteSync = false

// Load data on mount, restoring state from URL
onMounted(async () => {
  await Promise.all([
    circlesStore.fetchCircles(),
    circlesStore.fetchPendingInvitations(),
  ])

  // Restore circle/topic from URL params
  const urlCircleId = route.params.circleId ? Number(route.params.circleId) : null
  const urlTopicId = route.params.topicId ? Number(route.params.topicId) : null

  if (urlCircleId && circlesStore.circles.some(c => c.id === urlCircleId)) {
    suppressRouteSync = true
    circlesStore.activeCircleId = urlCircleId
    await circlesStore.fetchCircleDetail(urlCircleId)
    circlesStore.fetchUnreadCounts(urlCircleId)

    if (urlTopicId && circlesStore.activeCircle?.topics?.some(t => t.id === urlTopicId)) {
      circlesStore.setActiveTopic(urlTopicId)
    }
    suppressRouteSync = false
  }
})

onUnmounted(() => {
  circlesStore.stopPolling()
})

// When active circle changes, load its details and update URL
watch(() => circlesStore.activeCircleId, async (newId) => {
  if (newId) {
    await circlesStore.fetchCircleDetail(newId)
    circlesStore.fetchUnreadCounts(newId)
  }
  if (!suppressRouteSync) {
    updateRoute()
  }
})

// When active topic changes, update URL
watch(() => circlesStore.activeTopicId, () => {
  if (!suppressRouteSync) {
    updateRoute()
  }
})

function updateRoute() {
  const circleId = circlesStore.activeCircleId
  const topicId = circlesStore.activeTopicId
  let path = '/circles'
  if (circleId) {
    path += `/${circleId}`
    if (topicId) {
      path += `/${topicId}`
    }
  }
  if (route.path !== path) {
    router.replace(path)
  }
}

// Connect reply event from MessageThread to MessageComposer
function handleReplyTo(message) {
  composerRef.value?.setReplyTo(message)
}

function selectCircle(circleId) {
  circlesStore.setActiveCircle(circleId)
  showCircleSelector.value = false
}

function formatTimeAgo(date) {
  return bookClubService.formatTimeAgo(date)
}

function getCategoryClass(category) {
  return bookClubService.getCategoryInfo(category)?.color || 'bg-slate-500/20 text-slate-400'
}

function isRecentActivity(dateString) {
  if (!dateString) return false
  return (new Date() - new Date(dateString)) / (1000 * 60 * 60) < 24
}
</script>

<template>
  <div class="h-full flex bg-slate-950 animate-in fade-in duration-500">

    <!-- Loading State -->
    <div v-if="circlesStore.loading" class="flex-1 flex items-center justify-center">
      <div class="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>

    <!-- Empty State -->
    <div v-else-if="circlesStore.circles.length === 0" class="flex-1 flex flex-col items-center justify-center p-20 text-center">
      <!-- Pending Invitations (when no circles) -->
      <div v-if="circlesStore.pendingInvitations.length > 0" class="w-full max-w-lg mb-12">
        <h3 class="text-[10px] font-black text-indigo-400 uppercase tracking-[0.3em] mb-4 flex items-center justify-center gap-2">
          <Mail :size="14" /> Pending Invitations
        </h3>
        <div class="space-y-3">
          <div
            v-for="invitation in circlesStore.pendingInvitations"
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
                @click="circlesStore.declineInvitation(invitation.id)"
                class="p-2 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 transition-colors"
              >
                <X :size="16" />
              </button>
              <button
                @click="circlesStore.acceptInvitation(invitation.id)"
                class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors"
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
        @click="showCreateCircleModal = true"
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
        <CircleSidebar :collapsed="sidebarCollapsed" @openCreateCircle="showCreateCircleModal = true" />

        <!-- DESKTOP: Discover Mode -->
        <main v-if="circlesStore.activeTab === 'discover' && !circlesStore.activeCircle" class="flex-1 flex flex-col overflow-hidden bg-transparent">
          <CircleDiscovery />
        </main>

        <!-- DESKTOP: Main Content -->
        <main v-else-if="circlesStore.activeCircle" class="flex-1 flex flex-col overflow-hidden bg-transparent">
          <!-- Desktop Header -->
          <header class="px-4 py-2 border-b border-white/5 shrink-0 bg-slate-900/50">
            <div class="flex items-center justify-between gap-3">
              <div class="flex items-center gap-2 min-w-0">
                <h1 class="text-base font-black text-white tracking-tight truncate">{{ circlesStore.activeCircle.name }}</h1>
                <span class="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[9px] font-black text-indigo-400 uppercase tracking-wider shrink-0">
                  {{ circlesStore.activeCircle.is_invite_only ? 'Private' : 'Open' }}
                </span>
              </div>
              <div class="flex items-center gap-2 shrink-0">
                <!-- Current Book mini -->
                <div v-if="circlesStore.activeCircle.current_book_data" class="flex items-center gap-2 px-2 py-1 rounded-lg bg-white/5 border border-white/5">
                  <div class="w-6 h-8 rounded overflow-hidden shrink-0">
                    <img v-if="circlesStore.activeCircle.current_book_data.cover_image" :src="circlesStore.activeCircle.current_book_data.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="10" class="text-slate-600" /></div>
                  </div>
                  <div class="text-[10px]">
                    <p class="text-slate-400 truncate max-w-[120px]">{{ circlesStore.activeCircle.current_book_data.title }}</p>
                    <div class="flex items-center gap-1.5">
                      <div class="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div class="h-full bg-indigo-500 rounded-full" :style="{ width: `${circlesStore.activeCircle.average_progress || 0}%` }" />
                      </div>
                      <span class="text-indigo-400 font-bold">{{ Number(circlesStore.activeCircle.average_progress || 0).toFixed(1) }}%</span>
                    </div>
                  </div>
                </div>

                <!-- Tab toggle: Discussions / Bookshelf -->
                <div class="flex items-center bg-white/5 rounded-xl p-0.5">
                  <button
                    @click="circlesStore.activeTab = 'topics'"
                    :class="['px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
                      circlesStore.activeTab === 'topics' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-slate-300']"
                  >
                    Discussions
                  </button>
                  <button
                    @click="circlesStore.activeTab = 'bookshelf'"
                    :class="['px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
                      circlesStore.activeTab === 'bookshelf' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500 hover:text-slate-300']"
                  >
                    Bookshelf
                  </button>
                </div>

                <button @click="showSearch = true" class="p-1.5 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors" title="Search Messages">
                  <Search :size="14" />
                </button>
                <button v-if="circlesStore.isCircleAdmin" @click="showInviteModal = true" class="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 transition-colors" title="Invite Members">
                  <UserPlus :size="14" />
                </button>
                <button @click="showSettingsModal = true" class="p-1.5 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors" title="Settings">
                  <Settings :size="14" />
                </button>
                <button @click="showMembersModal = true" class="px-2 py-1.5 rounded-lg bg-slate-500/10 text-slate-400 hover:bg-slate-500/20 transition-colors flex items-center gap-1.5" title="View Members">
                  <Users :size="14" />
                  <span class="text-xs font-bold">{{ circlesStore.activeCircle.members_count }}</span>
                </button>
              </div>
            </div>
          </header>

          <!-- Desktop Content Area -->
          <div class="flex-1 flex overflow-hidden">
            <!-- Topics Tab -->
            <template v-if="circlesStore.activeTab === 'topics'">
              <TopicList @openCreateTopic="showCreateTopicModal = true" @editTopic="handleEditTopic" />
              <div class="flex-1 flex flex-col">
                <MessageThread @replyTo="handleReplyTo" />
                <MessageComposer ref="composerRef" />
              </div>
            </template>

            <!-- Bookshelf Tab -->
            <template v-else>
              <ReadingDashboard />
            </template>
          </div>
        </main>
      </div>
      <!-- END DESKTOP LAYOUT -->

      <!-- ==================== MOBILE LAYOUT ==================== -->
      <div class="lg:hidden flex flex-col h-full w-full">

        <!-- MOBILE: Topics View -->
        <template v-if="circlesStore.mobileView === 'topics'">
          <!-- Mobile Header with Circle Selector -->
          <header class="px-4 py-3 border-b border-white/5 bg-slate-900/80 backdrop-blur-xl sticky top-0 z-30">
            <!-- Circle Dropdown -->
            <button
              @click="showCircleSelector = !showCircleSelector"
              class="w-full flex items-center justify-between p-3 rounded-2xl bg-white/5 border border-white/10"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div
                  v-if="circlesStore.activeCircle"
                  class="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-white font-black text-sm shadow-lg"
                  :style="{ background: `linear-gradient(135deg, ${circlesStore.activeCircle.accent_color || '#6366f1'}dd, #000000)` }"
                >
                  {{ circlesStore.activeCircle.name?.charAt(0) }}
                </div>
                <div class="text-left min-w-0">
                  <p class="text-sm font-bold text-white truncate">{{ circlesStore.activeCircle?.name || 'Select Circle' }}</p>
                  <p class="text-[10px] text-slate-500 uppercase tracking-wider">{{ circlesStore.activeCircle?.members_count || 0 }} members</p>
                </div>
              </div>
              <ChevronDown :size="20" :class="['text-slate-400 transition-transform', showCircleSelector ? 'rotate-180' : '']" />
            </button>

            <!-- Circle Dropdown Overlay -->
            <div v-if="showCircleSelector" class="fixed inset-0 z-30" @click="showCircleSelector = false" />

            <!-- Circle Dropdown Panel -->
            <div
              v-if="showCircleSelector"
              class="absolute left-4 right-4 top-full mt-2 bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden z-40 max-h-80 overflow-y-auto"
            >
              <div class="p-2 space-y-1">
                <button
                  v-for="circle in circlesStore.circles"
                  :key="circle.id"
                  @click="selectCircle(circle.id)"
                  :class="['w-full flex items-center gap-3 p-3 rounded-xl transition-all',
                    circlesStore.activeCircleId === circle.id ? 'bg-indigo-500/20' : 'hover:bg-white/5']"
                >
                  <div
                    class="w-10 h-10 rounded-xl shrink-0 flex items-center justify-center text-white font-black text-sm"
                    :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}dd, #000000)` }"
                  >
                    {{ circle.name?.charAt(0) }}
                  </div>
                  <div class="text-left min-w-0">
                    <p :class="['text-sm font-bold truncate', circlesStore.activeCircleId === circle.id ? 'text-white' : 'text-slate-300']">
                      {{ circle.name }}
                    </p>
                    <p class="text-[10px] text-slate-500">{{ circle.members_count }} members</p>
                  </div>
                  <Check v-if="circlesStore.activeCircleId === circle.id" :size="16" class="text-indigo-400 ml-auto shrink-0" />
                </button>
              </div>
              <div class="p-2 border-t border-white/5">
                <button
                  @click="showCircleSelector = false; showCreateCircleModal = true"
                  class="w-full flex items-center justify-center gap-2 p-3 rounded-xl bg-indigo-500/10 text-indigo-400 font-bold text-sm hover:bg-indigo-500/20 transition-colors"
                >
                  <Plus :size="16" />
                  Create New Circle
                </button>
              </div>
            </div>

            <!-- Pending Invitations Badge -->
            <div v-if="circlesStore.pendingInvitations.length > 0" class="mt-3">
              <div class="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20">
                <p class="text-xs font-bold text-amber-400 flex items-center gap-2 mb-2">
                  <Mail :size="14" /> {{ circlesStore.pendingInvitations.length }} Pending Invitation{{ circlesStore.pendingInvitations.length > 1 ? 's' : '' }}
                </p>
                <div class="flex gap-2">
                  <button
                    v-for="inv in circlesStore.pendingInvitations.slice(0, 2)"
                    :key="inv.id"
                    @click="circlesStore.acceptInvitation(inv.id)"
                    class="flex-1 px-3 py-2 rounded-lg bg-amber-500/20 text-amber-300 text-xs font-bold truncate"
                  >
                    {{ inv.circle?.name }}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <!-- Mobile Topics List -->
          <div v-if="circlesStore.activeCircle" class="flex-1 overflow-y-auto custom-scrollbar">
            <!-- Circle Actions Bar -->
            <div class="px-4 py-3 flex items-center justify-between border-b border-white/5 bg-slate-950/50 sticky top-0 z-10">
              <div class="flex items-center bg-white/5 rounded-xl p-0.5">
                <button
                  @click="circlesStore.activeTab = 'topics'"
                  :class="['px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
                    circlesStore.activeTab === 'topics' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500']"
                >
                  Discussions
                </button>
                <button
                  @click="circlesStore.activeTab = 'bookshelf'"
                  :class="['px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wider transition-all',
                    circlesStore.activeTab === 'bookshelf' ? 'bg-indigo-500/20 text-indigo-400' : 'text-slate-500']"
                >
                  Bookshelf
                </button>
              </div>
              <div class="flex items-center gap-2">
                <button @click="showMembersModal = true" class="p-2 rounded-lg bg-white/5 text-slate-400">
                  <Users :size="16" />
                </button>
                <button v-if="circlesStore.isCircleAdmin" @click="showInviteModal = true" class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                  <UserPlus :size="16" />
                </button>
                <button @click="showSettingsModal = true" class="p-2 rounded-lg bg-white/5 text-slate-400">
                  <Settings :size="16" />
                </button>
                <button v-if="circlesStore.activeTab === 'topics'" @click="showCreateTopicModal = true" class="p-2 rounded-lg bg-indigo-500 text-white">
                  <Plus :size="16" />
                </button>
              </div>
            </div>

            <!-- Mobile: Topics or Bookshelf -->
            <template v-if="circlesStore.activeTab === 'topics'">
              <!-- Current Book Card (mobile) -->
              <div v-if="circlesStore.activeCircle.current_book_data" class="mx-4 mt-4">
                <div class="p-4 rounded-2xl bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/20">
                  <p class="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-2">Currently Reading</p>
                  <div class="flex items-center gap-3">
                    <div class="w-12 h-16 rounded-lg overflow-hidden shrink-0 shadow-lg">
                      <img v-if="circlesStore.activeCircle.current_book_data.cover_image" :src="circlesStore.activeCircle.current_book_data.cover_image" class="w-full h-full object-cover" />
                      <div v-else class="w-full h-full bg-slate-800 flex items-center justify-center"><BookOpen :size="16" class="text-slate-600" /></div>
                    </div>
                    <div class="min-w-0 flex-1">
                      <p class="text-sm font-bold text-white truncate">{{ circlesStore.activeCircle.current_book_data.title }}</p>
                      <p class="text-xs text-slate-500 truncate">{{ circlesStore.activeCircle.current_book_data.author }}</p>
                      <div class="flex items-center gap-2 mt-2">
                        <div class="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div class="h-full bg-indigo-500 rounded-full transition-all" :style="{ width: `${circlesStore.activeCircle.average_progress || 0}%` }" />
                        </div>
                        <span class="text-xs font-bold text-indigo-400">{{ Number(circlesStore.activeCircle.average_progress || 0).toFixed(1) }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Mobile Topic Cards -->
              <div class="p-4 space-y-3">
                <div v-if="!circlesStore.activeCircle.topics?.length" class="text-center py-16">
                  <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                    <MessageSquare :size="28" class="text-slate-600" />
                  </div>
                  <p class="text-slate-500 text-sm mb-4">No discussions yet</p>
                  <button @click="showCreateTopicModal = true" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold">
                    Start First Discussion
                  </button>
                </div>

                <button
                  v-for="topic in circlesStore.activeCircle.topics"
                  :key="topic.id"
                  @click="circlesStore.openMobileChat(topic.id)"
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
                        <div
                          v-if="circlesStore.unreadCounts[topic.id]"
                          class="px-1.5 py-0.5 rounded-full bg-indigo-500 text-white text-[9px] font-black"
                        >
                          {{ circlesStore.unreadCounts[topic.id] }}
                        </div>
                        <div v-else-if="isRecentActivity(topic.last_activity)" class="w-2 h-2 rounded-full bg-indigo-500" />
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
            </template>

            <!-- Mobile: Bookshelf tab -->
            <template v-else>
              <ReadingDashboard />
            </template>
          </div>
        </template>

        <!-- MOBILE: Chat View -->
        <template v-if="circlesStore.mobileView === 'chat' && circlesStore.activeTopic">
          <!-- Mobile Chat Header -->
          <header class="px-4 py-3 border-b border-white/5 bg-slate-900/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
            <div class="flex items-center gap-3">
              <button
                @click="circlesStore.closeMobileChat()"
                class="p-2 -ml-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <ArrowLeft :size="22" />
              </button>
              <div class="flex-1 min-w-0">
                <h1 class="text-base font-bold text-white truncate">{{ circlesStore.activeTopic.title }}</h1>
                <p class="text-[10px] text-slate-500 uppercase tracking-wider">
                  {{ circlesStore.activeCircle?.name }} · {{ circlesStore.activeTopic.message_count || 0 }} posts
                </p>
              </div>
              <div class="relative">
                <button
                  @click="showMobileTopicMenu = !showMobileTopicMenu"
                  class="p-2 rounded-xl text-slate-400 hover:bg-white/5"
                >
                  <MoreVertical :size="18" />
                </button>

                <div v-if="showMobileTopicMenu" class="fixed inset-0 z-40" @click="showMobileTopicMenu = false" />
                <div
                  v-if="showMobileTopicMenu"
                  class="absolute right-0 top-full mt-2 w-48 bg-slate-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
                >
                  <button @click="showMobileTopicMenu = false" class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3">
                    <Info :size="16" class="text-slate-500" /> Topic Info
                  </button>
                  <button @click="showMobileTopicMenu = false" class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3">
                    <Share2 :size="16" class="text-slate-500" /> Share Topic
                  </button>
                  <button @click="showMobileTopicMenu = false; showMembersModal = true" class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3">
                    <Users :size="16" class="text-slate-500" /> View Members
                  </button>
                  <div v-if="circlesStore.isCircleAdmin" class="h-px bg-white/5" />
                  <button
                    v-if="circlesStore.isCircleAdmin"
                    @click="showMobileTopicMenu = false; handleEditTopic(circlesStore.activeTopic)"
                    class="w-full px-4 py-3 text-left text-sm text-slate-300 hover:bg-white/5 flex items-center gap-3"
                  >
                    <Settings :size="16" class="text-slate-500" /> Edit Topic
                  </button>
                  <button
                    v-if="circlesStore.isCircleAdmin"
                    @click="showMobileTopicMenu = false; circlesStore.deleteTopic(circlesStore.activeTopicId); circlesStore.closeMobileChat()"
                    class="w-full px-4 py-3 text-left text-sm text-rose-400 hover:bg-rose-500/10 flex items-center gap-3"
                  >
                    <Trash2 :size="16" /> Delete Topic
                  </button>
                </div>
              </div>
            </div>
          </header>

          <!-- Mobile Messages -->
          <MessageThread @replyTo="handleReplyTo" />

          <!-- Mobile Composer -->
          <MessageComposer ref="composerRef" />
        </template>
      </div>
      <!-- END MOBILE LAYOUT -->

    </template>

    <!-- ===== MODALS ===== -->
    <CircleModals
      :showCreateCircle="showCreateCircleModal"
      :showCreateTopic="showCreateTopicModal"
      :showEditTopic="showEditTopicModal"
      :editingTopic="editingTopic"
      :showInvite="showInviteModal"
      :showSettings="showSettingsModal"
      :showMembers="showMembersModal"
      @update:showCreateCircle="showCreateCircleModal = $event"
      @update:showCreateTopic="showCreateTopicModal = $event"
      @update:showEditTopic="showEditTopicModal = $event"
      @update:showInvite="showInviteModal = $event"
      @update:showSettings="showSettingsModal = $event"
      @update:showMembers="showMembersModal = $event"
    />

    <!-- Search -->
    <SearchMessages
      :show="showSearch"
      @update:show="showSearch = $event"
    />

  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }

/* Safe area support for notched phones */
.safe-area-top { padding-top: max(0.75rem, env(safe-area-inset-top)); }
.safe-area-bottom { padding-bottom: max(1rem, env(safe-area-inset-bottom)); }

/* Mobile touch feedback */
@media (max-width: 1023px) {
  button { -webkit-tap-highlight-color: transparent; }
}
</style>
