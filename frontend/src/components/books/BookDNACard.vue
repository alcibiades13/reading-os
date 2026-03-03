<script setup>
import { Dna } from 'lucide-vue-next'

defineProps({
  dna: { type: Object, required: true },
  compact: { type: Boolean, default: false },
})

const attributes = [
  { key: 'pace', label: 'Pace', color: 'bg-indigo-500', lowLabel: 'Slow', highLabel: 'Fast' },
  { key: 'complexity', label: 'Complexity', color: 'bg-purple-500', lowLabel: 'Light', highLabel: 'Dense' },
  { key: 'emotional_intensity', label: 'Emotion', color: 'bg-rose-500', lowLabel: 'Calm', highLabel: 'Intense' },
  { key: 'darkness', label: 'Tone', color: 'bg-slate-500', lowLabel: 'Light', highLabel: 'Dark' },
  { key: 'character_focus', label: 'Focus', color: 'bg-amber-500', lowLabel: 'Plot', highLabel: 'Characters' },
  { key: 'introspection', label: 'Style', color: 'bg-cyan-500', lowLabel: 'Action', highLabel: 'Reflective' },
]
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5" v-if="!compact">
      <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
        <Dna :size="16" class="text-indigo-400" />
      </div>
      <div>
        <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Book DNA</h3>
        <p class="text-slate-600 text-[9px]">{{ dna.vote_count || 0 }} reader{{ dna.vote_count !== 1 ? 's' : '' }} rated</p>
      </div>
    </div>
    <div v-else class="flex items-center gap-2 mb-4">
      <Dna :size="16" class="text-indigo-400" />
      <div>
        <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Book DNA</h3>
        <p class="text-slate-600 text-[9px]">{{ dna.vote_count || 0 }} reader{{ dna.vote_count !== 1 ? 's' : '' }} rated</p>
      </div>
    </div>

    <!-- DNA Attributes -->
    <div :class="compact ? 'space-y-2' : 'space-y-3'">
      <template v-for="attr in attributes" :key="attr.key">
        <div v-if="dna[attr.key] !== undefined">
          <!-- Compact layout (horizontal) -->
          <div v-if="compact" class="flex items-center gap-2">
            <span class="text-[9px] font-bold text-slate-500 uppercase w-16">{{ attr.label }}</span>
            <div class="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
              <div :class="['h-full rounded-full', attr.color]" :style="{ width: `${dna[attr.key] * 100}%` }" />
            </div>
            <span class="text-[9px] text-slate-600 w-12 text-right">{{ dna[attr.key] > 0.5 ? attr.highLabel : attr.lowLabel }}</span>
          </div>
          <!-- Full layout (stacked) -->
          <div v-else>
            <div class="flex items-center justify-between mb-1">
              <span class="text-[9px] font-bold text-slate-500 uppercase">{{ attr.label }}</span>
              <span class="text-[9px] text-slate-600">{{ dna[attr.key] > 0.5 ? attr.highLabel : attr.lowLabel }}</span>
            </div>
            <div class="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all', attr.color]"
                :style="{ width: `${dna[attr.key] * 100}%` }"
              />
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Themes -->
    <div v-if="dna.themes?.length > 0" :class="compact ? 'mt-3 pt-3 border-t border-slate-800' : 'mt-5 pt-4 border-t border-slate-800'">
      <span class="text-[9px] font-bold text-slate-500 uppercase block mb-2">Themes</span>
      <div :class="compact ? 'flex flex-wrap gap-1' : 'flex flex-wrap gap-1.5'">
        <span
          v-for="theme in dna.themes.slice(0, 4)"
          :key="theme"
          class="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400"
        >
          {{ theme }}
        </span>
      </div>
    </div>
  </div>
</template>
