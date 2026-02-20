<script setup>
import { ref } from 'vue'
import { useCirclesStore } from '@/stores/circlesStore'
import { useAuthStore } from '@/stores/authStore'
import { socialService } from '@/services/socialService'
import { bookClubService } from '@/services/bookClubService'
import {
  X, Check, Lock, AlertCircle, Search, Mail,
  Trash2, Crown, Settings, UserPlus, Plus, Minus
} from 'lucide-vue-next'

const circlesStore = useCirclesStore()
const authStore = useAuthStore()

// Modal visibility props from parent
const props = defineProps({
  showCreateCircle: Boolean,
  showCreateTopic: Boolean,
  showEditTopic: Boolean,
  editingTopic: Object,
  showInvite: Boolean,
  showSettings: Boolean,
  showMembers: Boolean,
})

const emit = defineEmits([
  'update:showCreateCircle',
  'update:showCreateTopic',
  'update:showEditTopic',
  'update:showInvite',
  'update:showSettings',
  'update:showMembers',
])

// Color presets
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
  { value: 'quotes', label: 'Favorite Quotes', color: 'bg-cyan-500/20 text-cyan-400' },
  { value: 'polls', label: 'Polls', color: 'bg-orange-500/20 text-orange-400' },
  { value: 'announcements', label: 'Announcements', color: 'bg-rose-500/20 text-rose-400' },
]

// ===== CREATE CIRCLE =====
const circleForm = ref({ name: '', description: '', is_invite_only: true, accent_color: '#6366f1', max_members: 20 })
const creatingCircle = ref(false)

function resetCircleForm() {
  circleForm.value = { name: '', description: '', is_invite_only: true, accent_color: '#6366f1', max_members: 20 }
}

async function handleCreateCircle() {
  if (!circleForm.value.name.trim()) return
  creatingCircle.value = true
  try {
    await circlesStore.createCircle(circleForm.value)
    emit('update:showCreateCircle', false)
    resetCircleForm()
  } catch (error) {
    console.error('Error:', error)
  } finally {
    creatingCircle.value = false
  }
}

// ===== CREATE TOPIC =====
const topicForm = ref({ title: '', description: '', category: 'general', is_locked: false, required_progress: 0 })
const topicError = ref('')
const creatingTopic = ref(false)

// Poll form (shown when category is 'polls')
const pollForm = ref({
  question: '',
  options: ['', ''],
  allows_multiple: false,
})

function resetTopicForm() {
  topicForm.value = { title: '', description: '', category: 'general', is_locked: false, required_progress: 0 }
  pollForm.value = { question: '', options: ['', ''], allows_multiple: false }
  topicError.value = ''
}

function addPollOption() {
  if (pollForm.value.options.length < 10) {
    pollForm.value.options.push('')
  }
}

function removePollOption(index) {
  if (pollForm.value.options.length > 2) {
    pollForm.value.options.splice(index, 1)
  }
}

async function handleCreateTopic() {
  topicError.value = ''
  if (!topicForm.value.title.trim()) { topicError.value = 'Please enter a topic title'; return }
  if (!circlesStore.activeCircleId) { topicError.value = 'No circle selected'; return }

  // Validate poll fields
  const isPoll = topicForm.value.category === 'polls'
  if (isPoll) {
    if (!pollForm.value.question.trim()) { topicError.value = 'Please enter a poll question'; return }
    const validOptions = pollForm.value.options.filter(o => o.trim())
    if (validOptions.length < 2) { topicError.value = 'Please add at least 2 options'; return }
  }

  creatingTopic.value = true
  try {
    const result = await circlesStore.createTopic({
      title: topicForm.value.title,
      description: topicForm.value.description,
      category: topicForm.value.category,
      is_locked: topicForm.value.is_locked,
      required_progress: topicForm.value.is_locked ? topicForm.value.required_progress : 0,
      circle: circlesStore.activeCircleId,
    })
    if (result.success) {
      // Create poll if category is polls
      if (isPoll && result.data?.id) {
        const validOptions = pollForm.value.options.filter(o => o.trim())
        const pollResult = await circlesStore.createPoll({
          topic_id: result.data.id,
          question: pollForm.value.question,
          poll_type: 'general',
          allows_multiple: pollForm.value.allows_multiple,
          options: validOptions.map(text => ({ text })),
        })
        if (!pollResult.success) {
          topicError.value = 'Topic created but poll creation failed. Please try again.'
          creatingTopic.value = false
          return
        }
        // Re-fetch poll to ensure activePoll is set properly
        await circlesStore.fetchTopicPoll(result.data.id)
      }
      emit('update:showCreateTopic', false)
      resetTopicForm()
    } else {
      const errors = result.error
      if (typeof errors === 'object') {
        topicError.value = Object.values(errors).flat().join(', ')
      } else {
        topicError.value = String(errors || 'Failed to create topic')
      }
    }
  } catch (error) {
    topicError.value = 'Failed to create topic. Please try again.'
  } finally {
    creatingTopic.value = false
  }
}

// ===== EDIT TOPIC =====
const editTopicError = ref('')
const savingTopic = ref(false)

async function handleEditTopic() {
  editTopicError.value = ''
  if (!props.editingTopic?.title?.trim()) { editTopicError.value = 'Title is required'; return }

  savingTopic.value = true
  try {
    const result = await circlesStore.updateTopic(props.editingTopic.id, {
      title: props.editingTopic.title,
      description: props.editingTopic.description || '',
      category: props.editingTopic.category,
      is_locked: props.editingTopic.is_locked,
      required_progress: props.editingTopic.is_locked ? props.editingTopic.required_progress : 0,
    })
    if (result.success) {
      emit('update:showEditTopic', false)
    } else {
      const errors = result.error
      if (typeof errors === 'object') {
        editTopicError.value = Object.values(errors).flat().join(', ')
      } else {
        editTopicError.value = String(errors || 'Failed to update topic')
      }
    }
  } catch (error) {
    editTopicError.value = 'Failed to update topic. Please try again.'
  } finally {
    savingTopic.value = false
  }
}

async function handleDeleteTopicFromEdit() {
  if (!props.editingTopic || !confirm('Delete this topic and all its messages?')) return
  await circlesStore.deleteTopic(props.editingTopic.id)
  emit('update:showEditTopic', false)
}

// ===== INVITE =====
const inviteSearch = ref('')
const inviteResults = ref([])
const inviteMessage = ref('')
const inviteError = ref('')
const inviteSentTo = ref([])
const searchingUsers = ref(false)
const sendingInvite = ref(false)

function resetInviteForm() {
  inviteSearch.value = ''
  inviteResults.value = []
  inviteMessage.value = ''
  inviteError.value = ''
  inviteSentTo.value = []
}

async function searchUsers() {
  if (!inviteSearch.value.trim() || inviteSearch.value.length < 2) { inviteResults.value = []; return }
  searchingUsers.value = true
  try {
    const data = await socialService.searchUsers(inviteSearch.value)
    const memberIds = circlesStore.activeCircle?.memberships?.map(m => m.user?.id) || []
    inviteResults.value = (data.results || data || []).filter(u => !memberIds.includes(u.id))
  } catch (error) {
    console.error('Error:', error)
  } finally {
    searchingUsers.value = false
  }
}

async function handleSendInvite(userId) {
  if (!circlesStore.activeCircleId) return
  inviteError.value = ''
  sendingInvite.value = true
  try {
    await bookClubService.sendInvitation(circlesStore.activeCircleId, userId, inviteMessage.value)
    const user = inviteResults.value.find(u => u.id === userId)
    if (user) inviteSentTo.value.push({ id: user.id, name: `${user.first_name} ${user.last_name}`.trim() || user.email })
    inviteResults.value = inviteResults.value.filter(u => u.id !== userId)
  } catch (error) {
    const errors = error.response?.data
    if (typeof errors === 'object' && !Array.isArray(errors)) inviteError.value = Object.values(errors).flat().join(', ')
    else inviteError.value = String(errors || 'Failed to send invitation')
  } finally {
    sendingInvite.value = false
  }
}

// ===== SETTINGS =====
async function handleUpdateCircle() {
  if (!circlesStore.activeCircle) return
  const ac = circlesStore.activeCircle
  await circlesStore.updateCircle(ac.id, {
    name: ac.name, description: ac.description,
    is_invite_only: ac.is_invite_only, accent_color: ac.accent_color, max_members: ac.max_members,
  })
  emit('update:showSettings', false)
}

async function handleDeleteCircle() {
  if (!circlesStore.activeCircle || !confirm('Are you sure you want to delete this circle?')) return
  await circlesStore.deleteCircle(circlesStore.activeCircle.id)
  emit('update:showSettings', false)
}

async function handleLeaveCircle() {
  if (!circlesStore.activeCircle || !confirm('Are you sure you want to leave this circle?')) return
  await circlesStore.leaveCircle(circlesStore.activeCircle.id)
  emit('update:showSettings', false)
}

async function handlePromoteMember(userId) {
  if (!circlesStore.activeCircle) return
  await circlesStore.promoteMember(circlesStore.activeCircle.id, userId)
}

function getUserInitial(user) {
  return user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'
}
</script>

<template>
  <!-- Create Circle Modal -->
  <Teleport to="body">
    <div v-if="showCreateCircle" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showCreateCircle', false)" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Create a Circle</h2>
          <button @click="$emit('update:showCreateCircle', false)" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 space-y-6">
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Circle Name</label><input v-model="circleForm.name" type="text" placeholder="e.g., Philosophy & Flow" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors" /></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label><textarea v-model="circleForm.description" placeholder="What's this circle about?" rows="3" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none" /></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Accent Color</label><div class="flex gap-2"><button v-for="color in colorPresets" :key="color" @click="circleForm.accent_color = color" :class="['w-8 h-8 rounded-full transition-all', circleForm.accent_color === color ? 'ring-2 ring-white ring-offset-2 ring-offset-slate-900 scale-110' : '']" :style="{ backgroundColor: color }" /></div></div>
          <div class="flex items-center justify-between"><div><p class="text-sm font-bold text-white">Private Circle</p><p class="text-xs text-slate-500">Members can only join by invitation</p></div><button @click="circleForm.is_invite_only = !circleForm.is_invite_only" :class="['w-12 h-6 rounded-full transition-colors relative', circleForm.is_invite_only ? 'bg-indigo-500' : 'bg-slate-700']"><div :class="['w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all', circleForm.is_invite_only ? 'left-6' : 'left-0.5']" /></button></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Max Members</label><input v-model.number="circleForm.max_members" type="number" min="2" max="100" class="w-24 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-white focus:border-indigo-500 outline-none transition-colors" /></div>
        </div>
        <div class="p-6 border-t border-white/5 flex justify-end gap-3">
          <button @click="$emit('update:showCreateCircle', false)" class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors">Cancel</button>
          <button @click="handleCreateCircle" :disabled="!circleForm.name.trim() || creatingCircle" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50 flex items-center gap-2">
            <div v-if="creatingCircle" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Create Circle</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Create Topic Modal -->
  <Teleport to="body">
    <div v-if="showCreateTopic" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showCreateTopic', false)" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Start a Discussion</h2>
          <button @click="$emit('update:showCreateTopic', false)" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 space-y-6">
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Topic Title</label><input v-model="topicForm.title" type="text" placeholder="What would you like to discuss?" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors" /></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label><textarea v-model="topicForm.description" placeholder="Add some context..." rows="3" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none" /></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Category</label>
            <div class="grid grid-cols-2 gap-2">
              <button v-for="cat in categoryOptions" :key="cat.value" @click="topicForm.category = cat.value" :class="['px-3 py-2 rounded-xl text-xs font-bold transition-all text-left', topicForm.category === cat.value ? cat.color + ' ring-2 ring-white/20' : 'bg-white/5 text-slate-400 hover:bg-white/10']">{{ cat.label }}</button>
            </div>
          </div>
          <!-- Poll form (shown when category is 'polls') -->
          <div v-if="topicForm.category === 'polls'" class="space-y-4 p-4 rounded-xl bg-orange-500/10 border border-orange-500/20">
            <p class="text-[10px] font-black text-orange-400 uppercase tracking-widest">Poll Setup</p>
            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Question</label>
              <input v-model="pollForm.question" type="text" placeholder="What do you want to ask?" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-orange-500 outline-none transition-colors" />
            </div>
            <div>
              <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Options</label>
              <div class="space-y-2">
                <div v-for="(opt, i) in pollForm.options" :key="i" class="flex items-center gap-2">
                  <span class="text-xs text-slate-600 w-5 shrink-0 text-center">{{ i + 1 }}.</span>
                  <input v-model="pollForm.options[i]" type="text" :placeholder="`Option ${i + 1}`" class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 focus:border-orange-500 outline-none transition-colors" />
                  <button v-if="pollForm.options.length > 2" @click="removePollOption(i)" class="p-1.5 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-white/5 transition-colors"><Minus :size="14" /></button>
                </div>
              </div>
              <button v-if="pollForm.options.length < 10" @click="addPollOption" class="mt-2 flex items-center gap-1.5 text-xs font-bold text-orange-400 hover:text-orange-300 transition-colors"><Plus :size="14" /> Add Option</button>
            </div>
            <div class="flex items-center justify-between">
              <div><p class="text-sm font-bold text-white">Allow Multiple Votes</p><p class="text-xs text-slate-500">Members can select more than one option</p></div>
              <button @click="pollForm.allows_multiple = !pollForm.allows_multiple" :class="['w-12 h-6 rounded-full transition-colors relative', pollForm.allows_multiple ? 'bg-orange-500' : 'bg-slate-700']"><div :class="['w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all', pollForm.allows_multiple ? 'left-6' : 'left-0.5']" /></button>
            </div>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-amber-500/10 border border-amber-500/20"><div><p class="text-sm font-bold text-amber-400 flex items-center gap-2"><Lock :size="14" /> Spoiler Protection</p><p class="text-xs text-amber-400/70 mt-1">Lock until readers reach a certain progress</p></div><button @click="topicForm.is_locked = !topicForm.is_locked" :class="['w-12 h-6 rounded-full transition-colors relative', topicForm.is_locked ? 'bg-amber-500' : 'bg-slate-700']"><div :class="['w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all', topicForm.is_locked ? 'left-6' : 'left-0.5']" /></button></div>
          <div v-if="topicForm.is_locked"><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Required Progress ({{ topicForm.required_progress }}%)</label><input v-model.number="topicForm.required_progress" type="range" min="10" max="100" step="10" class="w-full accent-amber-500" /></div>
          <div v-if="topicError" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3"><AlertCircle :size="18" class="text-rose-400 shrink-0 mt-0.5" /><p class="text-sm text-rose-400">{{ topicError }}</p></div>
        </div>
        <div class="p-6 border-t border-white/5 flex justify-end gap-3">
          <button @click="$emit('update:showCreateTopic', false)" class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors">Cancel</button>
          <button @click="handleCreateTopic" :disabled="!topicForm.title.trim() || creatingTopic" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50 flex items-center gap-2">
            <div v-if="creatingTopic" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            <span>Start Discussion</span>
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Edit Topic Modal -->
  <Teleport to="body">
    <div v-if="showEditTopic && editingTopic" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showEditTopic', false)" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Edit Topic</h2>
          <button @click="$emit('update:showEditTopic', false)" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 space-y-6">
          <div>
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Topic Title</label>
            <input v-model="editingTopic.title" type="text" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors" />
          </div>
          <div>
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label>
            <textarea v-model="editingTopic.description" rows="3" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors resize-none" />
          </div>
          <div>
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Category</label>
            <div class="grid grid-cols-2 gap-2">
              <button v-for="cat in categoryOptions" :key="cat.value" @click="editingTopic.category = cat.value" :class="['px-3 py-2 rounded-xl text-xs font-bold transition-all text-left', editingTopic.category === cat.value ? cat.color + ' ring-2 ring-white/20' : 'bg-white/5 text-slate-400 hover:bg-white/10']">{{ cat.label }}</button>
            </div>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
            <div>
              <p class="text-sm font-bold text-amber-400 flex items-center gap-2"><Lock :size="14" /> Spoiler Protection</p>
              <p class="text-xs text-amber-400/70 mt-1">Lock until readers reach a certain progress</p>
            </div>
            <button @click="editingTopic.is_locked = !editingTopic.is_locked" :class="['w-12 h-6 rounded-full transition-colors relative', editingTopic.is_locked ? 'bg-amber-500' : 'bg-slate-700']"><div :class="['w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all', editingTopic.is_locked ? 'left-6' : 'left-0.5']" /></button>
          </div>
          <div v-if="editingTopic.is_locked">
            <label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Required Progress ({{ editingTopic.required_progress }}%)</label>
            <input v-model.number="editingTopic.required_progress" type="range" min="10" max="100" step="10" class="w-full accent-amber-500" />
          </div>
          <div v-if="editTopicError" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
            <AlertCircle :size="18" class="text-rose-400 shrink-0 mt-0.5" />
            <p class="text-sm text-rose-400">{{ editTopicError }}</p>
          </div>
        </div>
        <div class="p-6 border-t border-white/5 flex items-center justify-between">
          <button @click="handleDeleteTopicFromEdit" class="px-4 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors flex items-center gap-2">
            <Trash2 :size="16" /> Delete
          </button>
          <div class="flex gap-3">
            <button @click="$emit('update:showEditTopic', false)" class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors">Cancel</button>
            <button @click="handleEditTopic" :disabled="!editingTopic.title?.trim() || savingTopic" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50 flex items-center gap-2">
              <div v-if="savingTopic" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              <span>Save Changes</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Invite Members Modal -->
  <Teleport to="body">
    <div v-if="showInvite" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showInvite', false); resetInviteForm()" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Invite Members</h2>
          <button @click="$emit('update:showInvite', false); resetInviteForm()" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 space-y-6">
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Search Users</label><div class="relative"><Search :size="18" class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" /><input v-model="inviteSearch" @input="searchUsers" type="text" placeholder="Search by name or email..." class="w-full bg-white/5 border border-white/10 rounded-xl pl-11 pr-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors" /></div></div>
          <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Invitation Message (optional)</label><textarea v-model="inviteMessage" placeholder="Add a personal message..." rows="2" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-600 focus:border-indigo-500 outline-none transition-colors resize-none" /></div>
          <div v-if="searchingUsers" class="flex items-center justify-center py-8"><div class="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" /></div>
          <div v-else-if="inviteResults.length > 0" class="space-y-2 max-h-60 overflow-y-auto">
            <div v-for="user in inviteResults" :key="user.id" class="flex items-center justify-between p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
              <div class="flex items-center gap-3"><div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold">{{ user.first_name?.[0] || user.email?.[0] || '?' }}</div><div><p class="text-sm font-bold text-white">{{ user.first_name }} {{ user.last_name }}</p><p class="text-xs text-slate-500">{{ user.email }}</p></div></div>
              <button @click="handleSendInvite(user.id)" :disabled="sendingInvite" class="px-3 py-1.5 rounded-lg bg-indigo-500 text-white text-xs font-bold hover:bg-indigo-600 transition-colors disabled:opacity-50"><Mail :size="14" /></button>
            </div>
          </div>
          <div v-else-if="inviteSearch.length >= 2 && inviteSentTo.length === 0" class="text-center py-8 text-slate-500">No users found</div>
          <div v-if="inviteSentTo.length > 0" class="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20"><p class="text-sm font-bold text-emerald-400 mb-2 flex items-center gap-2"><Check :size="16" /> Invitations Sent</p><div class="flex flex-wrap gap-2"><span v-for="user in inviteSentTo" :key="user.id" class="px-2 py-1 rounded-lg bg-emerald-500/20 text-emerald-300 text-xs">{{ user.name }}</span></div></div>
          <div v-if="inviteError" class="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3"><AlertCircle :size="18" class="text-rose-400 shrink-0 mt-0.5" /><p class="text-sm text-rose-400">{{ inviteError }}</p></div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Settings Modal -->
  <Teleport to="body">
    <div v-if="showSettings && circlesStore.activeCircle" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showSettings', false)" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Circle Settings</h2>
          <button @click="$emit('update:showSettings', false)" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 space-y-6">
          <template v-if="circlesStore.isCircleAdmin">
            <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Circle Name</label><input v-model="circlesStore.activeCircle.name" type="text" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors" /></div>
            <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Description</label><textarea v-model="circlesStore.activeCircle.description" rows="3" class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:border-indigo-500 outline-none transition-colors resize-none" /></div>
            <div><label class="block text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Accent Color</label><div class="flex gap-2"><button v-for="color in colorPresets" :key="color" @click="circlesStore.activeCircle.accent_color = color" :class="['w-8 h-8 rounded-full transition-all', circlesStore.activeCircle.accent_color === color ? 'ring-2 ring-white ring-offset-2 ring-offset-slate-900 scale-110' : '']" :style="{ backgroundColor: color }" /></div></div>
            <div class="flex items-center justify-between"><div><p class="text-sm font-bold text-white">Private Circle</p><p class="text-xs text-slate-500">Members can only join by invitation</p></div><button @click="circlesStore.activeCircle.is_invite_only = !circlesStore.activeCircle.is_invite_only" :class="['w-12 h-6 rounded-full transition-colors relative', circlesStore.activeCircle.is_invite_only ? 'bg-indigo-500' : 'bg-slate-700']"><div :class="['w-5 h-5 bg-white rounded-full absolute top-0.5 transition-all', circlesStore.activeCircle.is_invite_only ? 'left-6' : 'left-0.5']" /></button></div>
          </template>
          <template v-else><p class="text-slate-500 text-sm">Only admins can edit circle settings.</p></template>
        </div>
        <div class="p-6 border-t border-white/5 flex items-center justify-between">
          <button v-if="circlesStore.isCircleAdmin" @click="handleDeleteCircle" class="px-4 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors flex items-center gap-2"><Trash2 :size="16" /> Delete</button>
          <button v-else @click="handleLeaveCircle" class="px-4 py-2 rounded-xl text-rose-400 hover:bg-rose-500/10 transition-colors">Leave Circle</button>
          <div class="flex gap-3">
            <button @click="$emit('update:showSettings', false)" class="px-5 py-2.5 rounded-xl text-slate-400 hover:text-white transition-colors">Cancel</button>
            <button v-if="circlesStore.isCircleAdmin" @click="handleUpdateCircle" class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white font-bold hover:bg-indigo-600 transition-colors">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Members Modal -->
  <Teleport to="body">
    <div v-if="showMembers && circlesStore.activeCircle" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/80 backdrop-blur-sm" @click="$emit('update:showMembers', false)" />
      <div class="relative w-full max-w-lg bg-slate-900 rounded-3xl border border-white/10 shadow-2xl overflow-hidden max-h-[90vh] overflow-y-auto">
        <div class="p-6 border-b border-white/5 flex items-center justify-between">
          <h2 class="text-xl font-black text-white">Members ({{ circlesStore.activeCircle.members_count }})</h2>
          <button @click="$emit('update:showMembers', false)" class="p-2 text-slate-500 hover:text-white transition-colors"><X :size="20" /></button>
        </div>
        <div class="p-6 max-h-96 overflow-y-auto space-y-2">
          <div v-for="membership in circlesStore.activeCircle.memberships" :key="membership.id" class="flex items-center justify-between p-3 rounded-xl bg-white/5">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold overflow-hidden"><img v-if="membership.user?.avatar" :src="membership.user.avatar" class="w-full h-full object-cover" /><span v-else>{{ getUserInitial(membership.user) }}</span></div>
              <div><p class="text-sm font-bold text-white flex items-center gap-2">{{ membership.user?.first_name }} {{ membership.user?.last_name }}<Crown v-if="membership.role === 'admin'" :size="12" class="text-amber-400" /></p><p class="text-xs text-slate-500">{{ membership.user?.email }}</p></div>
            </div>
            <button v-if="circlesStore.isCircleAdmin && membership.role !== 'admin' && membership.user?.id !== authStore.user?.id" @click="handlePromoteMember(membership.user?.id)" class="px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-xs font-bold hover:bg-amber-500/20 transition-colors" title="Promote to Admin"><Crown :size="14" /></button>
          </div>
          <div v-if="!circlesStore.activeCircle.memberships?.length" class="text-center py-8 text-slate-500">No members found</div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
