<script setup>
import { computed } from 'vue'
import { Minus, Plus, RotateCcw, FileText, AlignLeft, BookOpen, ScrollText } from 'lucide-vue-next'
import {
  useReaderSettingsStore,
  READER_THEMES,
  READER_FONTS,
  READER_MARGINS,
  FONT_SIZE_STEP,
  FONT_SIZE_MIN,
  FONT_SIZE_MAX,
} from '@/stores/readerSettingsStore'

const props = defineProps({
  format: { type: String, required: true }, // 'epub' | 'pdf'
  pdfHasText: { type: Boolean, default: true },
})

const store = useReaderSettingsStore()
const s = store.settings

const LINE_HEIGHTS = [1.3, 1.5, 1.6, 1.8, 2.0]
const ZOOMS = [0.75, 1, 1.25, 1.5, 2, 2.5]

const theme = computed(() => READER_THEMES[s.theme] || READER_THEMES.dark)
// Text options don't apply to PDF page mode (it shows the original page image)
const showTextOptions = computed(() => props.format === 'epub' || (s.pdfMode === 'reflow' && props.pdfHasText))

const optionClass = (active) => [
  'flex-1 py-2 rounded-lg text-xs font-bold transition-all',
  active ? 'bg-indigo-500 text-white shadow' : 'opacity-70 hover:opacity-100',
]
</script>

<template>
  <div
    class="rounded-t-2xl sm:rounded-2xl shadow-2xl border p-4 sm:p-5 space-y-5 max-h-[75vh] overflow-y-auto"
    :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
    @click.stop
  >
    <!-- PDF mode -->
    <div v-if="format === 'pdf'">
      <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">View</p>
      <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
        <button
          :class="optionClass(s.pdfMode === 'reflow' && pdfHasText)"
          :disabled="!pdfHasText"
          class="flex items-center justify-center gap-1.5 disabled:opacity-30"
          @click="s.pdfMode = 'reflow'"
        >
          <AlignLeft :size="14" /> Reflow text
        </button>
        <button :class="optionClass(s.pdfMode === 'page' || !pdfHasText)" class="flex items-center justify-center gap-1.5" @click="s.pdfMode = 'page'">
          <FileText :size="14" /> Original pages
        </button>
      </div>
      <p v-if="!pdfHasText" class="text-[11px] mt-2" :style="{ color: theme.muted }">
        This PDF has no text layer (scanned pages), so only the original pages can be shown.
      </p>
      <p v-else-if="s.pdfMode === 'reflow'" class="text-[11px] mt-2" :style="{ color: theme.muted }">
        Text is re-wrapped to your screen. Tables, columns and images may not come through - switch to Original pages for those.
      </p>
    </div>

    <!-- Theme -->
    <div>
      <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Theme</p>
      <div class="grid grid-cols-4 gap-2">
        <button
          v-for="(t, id) in READER_THEMES"
          :key="id"
          class="h-11 rounded-xl border-2 text-xs font-bold transition-all"
          :style="{ background: t.bg, color: t.fg, borderColor: s.theme === id ? '#6366f1' : `${t.muted}55` }"
          @click="s.theme = id"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <template v-if="showTextOptions">
      <!-- Font size -->
      <div>
        <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Text size</p>
        <div class="flex items-center gap-3">
          <button
            class="w-11 h-11 rounded-xl flex items-center justify-center disabled:opacity-30"
            :style="{ background: `${theme.muted}26` }"
            :disabled="s.fontSize <= FONT_SIZE_MIN"
            aria-label="Smaller text"
            @click="store.changeFontSize(-FONT_SIZE_STEP)"
          >
            <Minus :size="16" />
          </button>
          <div class="flex-1 text-center font-bold tabular-nums">{{ s.fontSize }}%</div>
          <button
            class="w-11 h-11 rounded-xl flex items-center justify-center disabled:opacity-30"
            :style="{ background: `${theme.muted}26` }"
            :disabled="s.fontSize >= FONT_SIZE_MAX"
            aria-label="Larger text"
            @click="store.changeFontSize(FONT_SIZE_STEP)"
          >
            <Plus :size="16" />
          </button>
        </div>
      </div>

      <!-- Font -->
      <div>
        <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Font</p>
        <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
          <button
            v-for="(f, id) in READER_FONTS"
            v-show="id !== 'publisher' || format === 'epub'"
            :key="id"
            :class="optionClass(s.fontFamily === id)"
            :style="{ fontFamily: f.css || 'inherit' }"
            @click="s.fontFamily = id"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <!-- Line height -->
      <div>
        <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Line spacing</p>
        <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
          <button v-for="lh in LINE_HEIGHTS" :key="lh" :class="optionClass(s.lineHeight === lh)" @click="s.lineHeight = lh">
            {{ lh.toFixed(1) }}
          </button>
        </div>
      </div>

      <!-- Margins -->
      <div>
        <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Margins</p>
        <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
          <button v-for="(m, id) in READER_MARGINS" :key="id" :class="optionClass(s.margin === id)" @click="s.margin = id">
            {{ m.label }}
          </button>
        </div>
      </div>
    </template>

    <!-- EPUB layout -->
    <div v-if="format === 'epub'">
      <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Layout</p>
      <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
        <button :class="optionClass(s.epubFlow === 'paginated')" class="flex items-center justify-center gap-1.5" @click="s.epubFlow = 'paginated'">
          <BookOpen :size="14" /> Pages
        </button>
        <button :class="optionClass(s.epubFlow === 'scrolled')" class="flex items-center justify-center gap-1.5" @click="s.epubFlow = 'scrolled'">
          <ScrollText :size="14" /> Scroll
        </button>
      </div>
    </div>

    <!-- PDF zoom (page mode) -->
    <div v-if="format === 'pdf' && (s.pdfMode === 'page' || !pdfHasText)">
      <p class="text-[10px] font-black uppercase tracking-widest mb-2" :style="{ color: theme.muted }">Zoom</p>
      <div class="flex gap-1 p-1 rounded-xl" :style="{ background: `${theme.muted}26` }">
        <button v-for="z in ZOOMS" :key="z" :class="optionClass(s.pdfZoom === z)" @click="s.pdfZoom = z">
          {{ Math.round(z * 100) }}%
        </button>
      </div>
    </div>

    <button class="w-full flex items-center justify-center gap-2 py-2 text-xs font-bold opacity-60 hover:opacity-100" @click="store.reset()">
      <RotateCcw :size="12" /> Reset to defaults
    </button>
  </div>
</template>
