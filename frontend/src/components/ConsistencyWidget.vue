<script setup>
import { ref, onMounted } from 'vue'
import { usersAPI } from '@/services/api'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Zap, BookOpen, Quote, Brain, BookType, Pen, MessageCircle, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  compact: { type: Boolean, default: false }
})

const days = ref([])
const streak = ref(0)
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await usersAPI.getConsistency()
    days.value = res.data.days
    streak.value = res.data.streak
  } catch (e) {
    console.error('Error loading consistency data:', e)
  } finally {
    loading.value = false
  }
})

const getCellClass = (day) => {
  if (!day || day.total === 0) return 'bg-slate-800'
  if (day.total === 1) return 'bg-indigo-500/20'
  if (day.total <= 3) return 'bg-indigo-500/50'
  return 'bg-indigo-500'
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}
</script>

<template>
  <div
    :class="[compact ? 'p-6 rounded-2xl' : 'p-8 rounded-[2rem]']"
    class="glass border-slate-800 bg-slate-900/40"
  >
    <h3
      :class="compact ? 'mb-4' : 'mb-6'"
      class="text-slate-500 font-black uppercase tracking-[0.3em] text-[10px]"
    >
      Consistency
    </h3>

    <!-- Loading skeleton -->
    <div v-if="loading" :class="['grid grid-cols-7', compact ? 'gap-1 mb-4' : 'gap-1.5 mb-5']">
      <div
        v-for="i in 28"
        :key="i"
        class="aspect-square rounded-[2px] bg-slate-800 animate-pulse"
      />
    </div>

    <!-- Heatmap grid -->
    <div v-else :class="['grid grid-cols-7', compact ? 'gap-1 mb-4' : 'gap-1.5 mb-5']">
      <Popover v-for="(day, i) in days" :key="i">
        <PopoverTrigger as-child>
          <button
            :class="getCellClass(day)"
            class="aspect-square rounded-[2px] cursor-pointer hover:ring-1 hover:ring-indigo-400/50 transition-all"
          />
        </PopoverTrigger>
        <PopoverContent
          side="top"
          :side-offset="8"
          class="w-44 !p-3 !bg-slate-900 !border-slate-700 !rounded-xl"
        >
          <p class="font-bold text-white text-xs mb-2">{{ formatDate(day.date) }}</p>
          <div v-if="day.total === 0" class="text-slate-500 text-[11px]">No activity</div>
          <div v-else class="space-y-1.5">
            <div v-if="day.quotes" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <Quote :size="10" class="text-indigo-400" /> Quotes
              </span>
              <span class="text-white font-bold text-[11px]">{{ day.quotes }}</span>
            </div>
            <div v-if="day.study_notes" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <Brain :size="10" class="text-emerald-400" /> Study Notes
              </span>
              <span class="text-white font-bold text-[11px]">{{ day.study_notes }}</span>
            </div>
            <div v-if="day.vocabulary" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <BookType :size="10" class="text-sky-400" /> Vocabulary
              </span>
              <span class="text-white font-bold text-[11px]">{{ day.vocabulary }}</span>
            </div>
            <div v-if="day.reading" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <BookOpen :size="10" class="text-amber-400" /> Reading
              </span>
              <span class="text-emerald-400 font-bold text-[11px]">Active</span>
            </div>
            <div v-if="day.journal" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <Pen :size="10" class="text-purple-400" /> Journal
              </span>
              <span class="text-white font-bold text-[11px]">{{ day.journal }}</span>
            </div>
            <div v-if="day.writing" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <Pen :size="10" class="text-rose-400" /> Writing
              </span>
              <span class="text-emerald-400 font-bold text-[11px]">Active</span>
            </div>
            <div v-if="day.discussions" class="flex items-center justify-between">
              <span class="text-slate-400 text-[11px] flex items-center gap-1.5">
                <MessageCircle :size="10" class="text-cyan-400" /> Discussions
              </span>
              <span class="text-white font-bold text-[11px]">{{ day.discussions }}</span>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </div>

    <!-- Streak -->
    <div class="flex justify-between items-center">
      <div>
        <span :class="compact ? 'text-lg' : 'text-xl'" class="font-black text-white block">
          {{ loading ? '—' : streak }} {{ streak === 1 ? 'Day' : 'Days' }}
        </span>
        <span class="text-[9px] font-bold text-slate-500 uppercase tracking-widest">Active Streak</span>
      </div>
      <div class="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400">
        <Zap :size="16" class="fill-current" />
      </div>
    </div>
  </div>
</template>
