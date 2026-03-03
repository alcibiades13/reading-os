<script setup>
import { BookOpen, ArrowRight } from 'lucide-vue-next'
import { getBookUrl } from '@/utils/bookUrl'

defineProps({
  editions: { type: Array, required: true },
  userBookId: { type: Number, default: null },
  isInLibrary: { type: Boolean, default: false },
  compact: { type: Boolean, default: false },
})

defineEmits(['switchEdition', 'clickEdition'])
</script>

<template>
  <div>
    <!-- Header -->
    <div class="flex items-center gap-3 mb-5" v-if="!compact">
      <div class="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
        <BookOpen :size="16" class="text-indigo-400" />
      </div>
      <div>
        <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Other Editions</h3>
        <p class="text-slate-600 text-[9px]">{{ editions.length }} edition{{ editions.length !== 1 ? 's' : '' }}</p>
      </div>
    </div>
    <div v-else class="flex items-center gap-2 mb-4">
      <BookOpen :size="16" class="text-indigo-400" />
      <h3 class="text-slate-400 font-black uppercase tracking-[0.2em] text-[10px]">Other Editions</h3>
    </div>

    <!-- Editions List -->
    <div :class="compact ? 'space-y-3' : 'space-y-4'">
      <div
        v-for="edition in editions"
        :key="edition.id"
        :class="[
          'rounded-xl bg-slate-950/50 border border-slate-800',
          compact ? 'p-3' : 'p-4 hover:border-indigo-500/30 transition-all space-y-3'
        ]"
      >
        <!-- Edition info -->
        <router-link
          :to="getBookUrl(edition)"
          @click="$emit('clickEdition', edition)"
          :class="compact ? 'flex gap-3' : 'flex gap-3 cursor-pointer group/card'"
        >
          <div :class="[
            'shrink-0 rounded-lg overflow-hidden bg-gradient-to-br from-slate-700 to-slate-800 shadow-md flex items-center justify-center',
            compact ? 'w-10 h-14' : 'w-12 h-16'
          ]">
            <img
              v-if="edition.cover_image"
              :src="edition.cover_image"
              :alt="edition.title"
              class="w-full h-full object-cover"
              @error="(e) => e.target.style.display = 'none'"
            />
            <BookOpen v-else :size="compact ? 14 : 16" class="text-slate-600" />
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <h4 :class="[
                'font-semibold text-slate-100 text-sm',
                compact ? 'line-clamp-1' : 'line-clamp-2 group-hover/card:text-indigo-400 transition-colors'
              ]">{{ edition.title }}</h4>
              <span
                v-if="!compact && userBookId === edition.id"
                class="shrink-0 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-black uppercase tracking-wider"
              >
                Your Edition
              </span>
            </div>
            <div class="space-y-1">
              <div class="flex items-center gap-2 text-[10px]">
                <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-bold uppercase">
                  {{ edition.language?.toUpperCase() || 'N/A' }}
                </span>
                <span class="text-slate-500">{{ edition.pages }} pages</span>
              </div>
              <div v-if="!compact && edition.publisher" class="text-[10px] text-slate-500 truncate">
                {{ edition.publisher }}
              </div>
              <div v-if="!compact && edition.published_date" class="text-[10px] text-slate-600">
                {{ edition.published_date.split('-')[0] }}
              </div>
            </div>
          </div>
        </router-link>

        <!-- Actions (full mode only for rich buttons) -->
        <div v-if="!compact" class="pt-3 border-t border-slate-800/50">
          <router-link
            v-if="userBookId === edition.id"
            :to="getBookUrl(edition)"
            class="block w-full px-3 py-2 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/20 text-emerald-400 text-xs font-bold transition-all text-center"
          >
            View Your Edition
          </router-link>
          <button
            v-else-if="isInLibrary"
            @click="$emit('switchEdition', edition.id)"
            class="w-full px-3 py-2 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 text-xs font-bold transition-all flex items-center justify-center gap-2 group"
          >
            <ArrowRight :size="14" class="group-hover:translate-x-0.5 transition-transform" />
            Switch to this edition
          </button>
          <router-link
            v-else
            :to="getBookUrl(edition)"
            class="block w-full px-3 py-2 rounded-lg bg-slate-800/50 hover:bg-slate-800 text-slate-300 text-xs font-bold transition-all text-center"
          >
            View edition
          </router-link>
        </div>

        <!-- Compact switch button -->
        <button
          v-if="compact && isInLibrary && userBookId !== edition.id"
          @click="$emit('switchEdition', edition.id); $emit('clickEdition', edition)"
          class="w-full mt-2 px-3 py-2 rounded-lg bg-indigo-500/10 text-indigo-400 text-xs font-bold"
        >
          Switch to this edition
        </button>
      </div>
    </div>
  </div>
</template>
