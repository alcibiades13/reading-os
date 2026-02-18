<script setup>
import { useCirclesStore } from '@/stores/circlesStore'
import { Users, Plus, Mail, X, Check, Globe } from 'lucide-vue-next'

const circlesStore = useCirclesStore()

defineProps({
  collapsed: Boolean,
})

defineEmits(['openCreateCircle'])
</script>

<template>
  <!-- Collapsed mode: slim vertical strip -->
  <aside v-if="collapsed" class="w-12 border-r border-white/5 flex flex-col bg-slate-950/40 shrink-0">
    <div class="flex-1 overflow-y-auto custom-scrollbar py-2 flex flex-col items-center">
      <button
        v-for="circle in circlesStore.circles"
        :key="circle.id"
        @click="circlesStore.setActiveCircle(circle.id)"
        :title="circle.name"
        class="w-full flex items-center justify-center py-2 relative group transition-all"
      >
        <!-- Active indicator bar -->
        <div
          v-if="circlesStore.activeCircleId === circle.id"
          class="absolute left-0 w-[3px] h-5 bg-indigo-500 rounded-r-full"
        />
        <div
          :class="[
            'w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-white font-black text-[9px] relative transition-all',
            circlesStore.activeCircleId === circle.id
              ? 'shadow-md shadow-indigo-500/20'
              : 'opacity-50 group-hover:opacity-100'
          ]"
          :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}cc, ${circle.accent_color || '#6366f1'}44)` }"
        >
          {{ circle.name?.charAt(0) }}
          <div
            v-if="circlesStore.circleUnreadCounts[circle.id]"
            class="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-indigo-500 border border-slate-950"
          />
        </div>
      </button>

      <!-- Divider -->
      <div class="w-5 h-px bg-white/5 my-1" />

      <!-- Add + Discover -->
      <button
        @click="$emit('openCreateCircle')"
        class="py-2 w-full flex justify-center text-slate-600 hover:text-indigo-400 transition-colors"
        title="New Circle"
      >
        <Plus :size="14" />
      </button>
      <button
        @click="circlesStore.activeTab = 'discover'; circlesStore.activeCircleId = null"
        :class="['py-2 w-full flex justify-center transition-colors', circlesStore.activeTab === 'discover' && !circlesStore.activeCircleId ? 'text-indigo-400' : 'text-slate-600 hover:text-slate-300']"
        title="Discover"
      >
        <Globe :size="14" />
      </button>
    </div>
  </aside>

  <!-- Expanded mode -->
  <aside v-else class="circles-sidebar w-56 border-r border-white/5 flex flex-col backdrop-blur-3xl z-40 bg-slate-950/40 shrink-0">
    <div class="px-3 py-2.5 border-b border-white/5 flex items-center justify-between">
      <h2 class="text-[9px] font-black text-slate-500 uppercase tracking-[0.3em]">Circles</h2>
      <button
        @click="$emit('openCreateCircle')"
        class="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400 hover:bg-indigo-500 hover:text-white transition-all"
      >
        <Plus :size="14" />
      </button>
    </div>

    <div class="flex-1 overflow-y-auto custom-scrollbar">
      <button
        v-for="circle in circlesStore.circles"
        :key="circle.id"
        @click="circlesStore.setActiveCircle(circle.id)"
        :class="[
          'w-full group relative flex items-center gap-2.5 px-3 py-2 transition-all border-b border-white/[0.03]',
          circlesStore.activeCircleId === circle.id
            ? 'bg-white/10'
            : 'hover:bg-white/5'
        ]"
      >
        <div v-if="circlesStore.activeCircleId === circle.id" class="absolute left-0 w-0.5 h-6 bg-indigo-500 rounded-r-full" />
        <div
          class="w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-white font-black text-[10px] relative shadow-sm circle-icon"
          :style="{ background: `linear-gradient(135deg, ${circle.accent_color || '#6366f1'}, ${circle.accent_color || '#6366f1'}99)` }"
        >
          {{ circle.name?.charAt(0) }}
          <div
            v-if="circlesStore.circleUnreadCounts[circle.id]"
            class="absolute -top-0.5 -right-0.5 min-w-[14px] h-[14px] px-0.5 rounded-full bg-indigo-500 border border-slate-950 flex items-center justify-center text-[7px] font-black text-white"
          >
            {{ circlesStore.circleUnreadCounts[circle.id] > 9 ? '9+' : circlesStore.circleUnreadCounts[circle.id] }}
          </div>
        </div>
        <div class="text-left min-w-0">
          <p :class="['text-xs font-bold truncate circle-name', circlesStore.activeCircleId === circle.id ? 'text-white' : 'text-slate-400']">
            {{ circle.name }}
          </p>
          <span class="text-[8px] text-slate-600 font-bold circle-members">{{ circle.members_count }} members</span>
        </div>
      </button>
    </div>

    <!-- Discover -->
    <button
      @click="circlesStore.activeTab = 'discover'; circlesStore.activeCircleId = null"
      :class="[
        'flex items-center gap-2.5 px-3 py-2 border-t border-white/5 transition-all',
        circlesStore.activeTab === 'discover' && !circlesStore.activeCircleId
          ? 'bg-indigo-500/10 text-indigo-400'
          : 'text-slate-500 hover:bg-white/5 hover:text-slate-300'
      ]"
    >
      <Globe :size="14" />
      <span class="text-xs font-bold">Discover</span>
    </button>

    <!-- Pending Invitations -->
    <div v-if="circlesStore.pendingInvitations.length > 0" class="px-3 py-2 border-t border-white/5">
      <p class="text-[9px] font-black text-amber-400 uppercase tracking-widest flex items-center gap-1.5 mb-1.5">
        <Mail :size="10" /> {{ circlesStore.pendingInvitations.length }} Pending
      </p>
      <div class="space-y-1">
        <div
          v-for="invitation in circlesStore.pendingInvitations"
          :key="invitation.id"
          class="p-2 rounded-lg bg-amber-500/5 border border-amber-500/10"
        >
          <p class="text-[10px] text-white font-bold truncate mb-1">{{ invitation.circle?.name }}</p>
          <div class="flex gap-1.5">
            <button
              @click="circlesStore.declineInvitation(invitation.id)"
              class="flex-1 px-1.5 py-0.5 rounded bg-slate-500/10 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 text-[9px] font-bold transition-colors"
            >
              Decline
            </button>
            <button
              @click="circlesStore.acceptInvitation(invitation.id)"
              class="flex-1 px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 text-[9px] font-bold transition-colors"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 3px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(99, 102, 241, 0.3); border-radius: 10px; }
.custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(99, 102, 241, 0.5); }
</style>
