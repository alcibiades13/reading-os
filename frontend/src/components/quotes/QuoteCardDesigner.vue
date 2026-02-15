<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Download, Layout, Palette, Type, RectangleHorizontal, Loader2, Minus, Plus } from 'lucide-vue-next'
import { useQuoteCardDesigner } from '@/composables/useQuoteCardDesigner'

const props = defineProps({
  quote: { type: Object, required: true },
  open: { type: Boolean, default: false },
})
const emit = defineEmits(['update:open'])

const {
  selectedTemplate,
  selectedBackground,
  selectedFont,
  selectedAspectRatio,
  fontSizeAdjust,
  isGenerating,
  templates,
  backgrounds,
  fonts,
  aspectRatios,
  currentBackground,
  currentFont,
  currentAspectRatio,
  isDarkText,
  getQuoteFontSize,
  downloadImage,
} = useQuoteCardDesigner()

const previewRef = ref(null)
const previewContainerRef = ref(null)
const previewScale = ref(0.4)

const cardDimensions = computed(() => ({
  width: currentAspectRatio.value?.width || 1080,
  height: currentAspectRatio.value?.height || 1080,
}))

const updateScale = () => {
  if (!previewContainerRef.value) return
  const container = previewContainerRef.value
  const pad = window.innerWidth < 640 ? 24 : 48
  const cw = container.clientWidth - pad
  const ch = container.clientHeight - pad
  const { width, height } = cardDimensions.value
  previewScale.value = Math.min(cw / width, ch / height, 0.6)
}

watch([selectedAspectRatio], () => nextTick(updateScale))

onMounted(() => {
  nextTick(updateScale)
  window.addEventListener('resize', updateScale)
})

const quoteFontSize = computed(() =>
  getQuoteFontSize(props.quote.text?.length || 0, cardDimensions.value.width, cardDimensions.value.height)
)

// Attribution sizes scale with width for consistent readability
const attrTitleSize = computed(() => cardDimensions.value.width * 0.018)
const attrAuthorSize = computed(() => cardDimensions.value.width * 0.016)
const attrSmallSize = computed(() => cardDimensions.value.width * 0.014)

const attribution = computed(() => {
  const parts = []
  if (props.quote.book_title) parts.push(props.quote.book_title)
  if (props.quote.book_author) parts.push(props.quote.book_author)
  return parts
})

const handleDownload = async () => {
  if (!previewRef.value) return
  await downloadImage(previewRef.value, props.quote.book_title)
}

// Text colors derived from background
const textPrimary = computed(() => isDarkText.value ? '#0f172a' : '#f8fafc')
const textSecondary = computed(() => isDarkText.value ? '#475569' : 'rgba(248,250,252,0.6)')
const textAccent = computed(() => isDarkText.value ? '#6366f1' : '#a5b4fc')
const dividerColor = computed(() => isDarkText.value ? 'rgba(15,23,42,0.15)' : 'rgba(248,250,252,0.15)')
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="max-w-5xl glass border-slate-700 overflow-hidden p-0 gap-0 rounded-none sm:rounded-2xl !inset-0 !translate-x-0 !translate-y-0 sm:!inset-auto sm:!left-1/2 sm:!top-1/2 sm:!-translate-x-1/2 sm:!-translate-y-1/2 sm:w-[calc(100%-2rem)] sm:max-h-[90vh]">
      <div class="flex flex-col lg:flex-row h-[100dvh] sm:h-auto sm:max-h-[90vh]">

        <!-- LEFT: Live Preview Panel -->
        <div
          ref="previewContainerRef"
          class="h-[35dvh] sm:h-auto flex-none sm:flex-1 bg-slate-950/50 lg:min-h-[500px] overflow-hidden relative"
        >
          <!-- Checkerboard pattern hint -->
          <div class="absolute inset-0 opacity-[0.02]" style="background-image: linear-gradient(45deg, #fff 25%, transparent 25%), linear-gradient(-45deg, #fff 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #fff 75%), linear-gradient(-45deg, transparent 75%, #fff 75%); background-size: 20px 20px; background-position: 0 0, 0 10px, 10px -10px, -10px 0;" />

          <!-- Scaled preview wrapper (absolute so it doesn't affect layout) -->
          <div
            class="absolute inset-0 flex items-center justify-center"
          >
            <div
              :style="{
                transform: `scale(${previewScale})`,
                transformOrigin: 'center center',
                width: cardDimensions.width + 'px',
                height: cardDimensions.height + 'px',
                flexShrink: 0,
              }"
            >
            <!-- THE CARD (captured by html2canvas) -->
            <div
              ref="previewRef"
              :style="{
                ...currentBackground?.style,
                width: cardDimensions.width + 'px',
                height: cardDimensions.height + 'px',
                fontFamily: currentFont?.family,
              }"
              class="relative overflow-hidden"
            >
              <!-- ═══ TEMPLATE: Classic ═══ -->
              <div
                v-if="selectedTemplate === 'classic'"
                class="absolute inset-0 flex flex-col items-center justify-center overflow-hidden"
                :style="{ padding: (Math.min(cardDimensions.width, cardDimensions.height) * 0.08) + 'px ' + (cardDimensions.width * 0.1) + 'px' }"
              >
                <!-- Decorative quote mark -->
                <div
                  :style="{
                    color: textAccent,
                    fontFamily: currentFont?.family,
                    fontSize: (Math.min(cardDimensions.width, cardDimensions.height) * 0.1) + 'px',
                    lineHeight: '1',
                    opacity: 0.3,
                    marginBottom: (Math.min(cardDimensions.width, cardDimensions.height) * 0.015) + 'px',
                    flexShrink: 0,
                  }"
                >"</div>

                <!-- Quote text -->
                <div
                  :style="{
                    color: textPrimary,
                    fontFamily: currentFont?.family,
                    fontSize: quoteFontSize + 'px',
                    lineHeight: '1.5',
                    textAlign: 'center',
                    fontStyle: 'italic',
                    fontWeight: 400,
                    whiteSpace: 'pre-line',
                    overflow: 'hidden',
                  }"
                >{{ quote.text }}</div>

                <!-- Divider -->
                <div
                  :style="{
                    width: '40px',
                    height: '2px',
                    background: dividerColor,
                    margin: (Math.min(cardDimensions.width, cardDimensions.height) * 0.025) + 'px auto',
                    flexShrink: 0,
                  }"
                />

                <!-- Attribution -->
                <div :style="{ textAlign: 'center', flexShrink: 0 }">
                  <div
                    v-if="attribution[0]"
                    :style="{
                      color: textPrimary,
                      fontSize: attrTitleSize + 'px',
                      fontWeight: 700,
                      fontFamily: currentFont?.family,
                      letterSpacing: '0.02em',
                    }"
                  >{{ attribution[0] }}</div>
                  <div
                    v-if="attribution[1]"
                    :style="{
                      color: textAccent,
                      fontSize: attrAuthorSize + 'px',
                      fontWeight: 500,
                      fontFamily: currentFont?.family,
                      marginTop: '4px',
                    }"
                  >{{ attribution[1] }}</div>
                </div>
              </div>

              <!-- ═══ TEMPLATE: Editorial ═══ -->
              <div
                v-else-if="selectedTemplate === 'editorial'"
                class="absolute inset-0 flex items-center overflow-hidden"
                :style="{ padding: (Math.min(cardDimensions.width, cardDimensions.height) * 0.08) + 'px ' + (cardDimensions.width * 0.08) + 'px' }"
              >
                <div
                  :style="{
                    borderLeft: '4px solid ' + textAccent,
                    paddingLeft: (Math.min(cardDimensions.width, cardDimensions.height) * 0.04) + 'px',
                    overflow: 'hidden',
                  }"
                >
                  <!-- Quote text -->
                  <div
                    :style="{
                      color: textPrimary,
                      fontFamily: currentFont?.family,
                      fontSize: quoteFontSize + 'px',
                      lineHeight: '1.5',
                      fontStyle: 'italic',
                      fontWeight: 400,
                      whiteSpace: 'pre-line',
                      marginBottom: (Math.min(cardDimensions.width, cardDimensions.height) * 0.03) + 'px',
                    }"
                  >{{ quote.text }}</div>

                  <!-- Book title (uppercase) -->
                  <div
                    v-if="attribution[0]"
                    :style="{
                      color: textPrimary,
                      fontSize: attrSmallSize + 'px',
                      fontWeight: 800,
                      fontFamily: currentFont?.family,
                      textTransform: 'uppercase',
                      letterSpacing: '0.15em',
                    }"
                  >{{ attribution[0] }}</div>

                  <!-- Author + page -->
                  <div
                    :style="{
                      color: textSecondary,
                      fontSize: attrSmallSize + 'px',
                      fontFamily: currentFont?.family,
                      marginTop: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }"
                  >
                    <span v-if="attribution[1]">{{ attribution[1] }}</span>
                    <span v-if="attribution[1] && quote.page_number" :style="{ color: textAccent }">·</span>
                    <span v-if="quote.page_number">p. {{ quote.page_number }}</span>
                  </div>
                </div>
              </div>

              <!-- ═══ TEMPLATE: Minimal ═══ -->
              <div
                v-else-if="selectedTemplate === 'minimal'"
                class="absolute inset-0 flex flex-col justify-center overflow-hidden"
                :style="{ padding: (Math.min(cardDimensions.width, cardDimensions.height) * 0.1) + 'px ' + (cardDimensions.width * 0.12) + 'px' }"
              >
                <!-- Quote text -->
                <div
                  :style="{
                    color: textPrimary,
                    fontFamily: currentFont?.family,
                    fontSize: (quoteFontSize * 0.9) + 'px',
                    lineHeight: '1.7',
                    fontWeight: 400,
                    whiteSpace: 'pre-line',
                    marginBottom: (Math.min(cardDimensions.width, cardDimensions.height) * 0.04) + 'px',
                    overflow: 'hidden',
                  }"
                >{{ quote.text }}</div>

                <!-- Em-dash attribution (right-aligned) -->
                <div :style="{ textAlign: 'right', flexShrink: 0 }">
                  <div
                    v-if="attribution[1]"
                    :style="{
                      color: textSecondary,
                      fontSize: attrAuthorSize + 'px',
                      fontFamily: currentFont?.family,
                    }"
                  >— {{ attribution[1] }}</div>
                  <div
                    v-if="attribution[0]"
                    :style="{
                      color: textSecondary,
                      fontSize: attrSmallSize + 'px',
                      fontFamily: currentFont?.family,
                      fontStyle: 'italic',
                      marginTop: '4px',
                      opacity: 0.7,
                    }"
                  >{{ attribution[0] }}</div>
                </div>
              </div>

              <!-- ═══ TEMPLATE: Bold ═══ -->
              <div
                v-else-if="selectedTemplate === 'bold'"
                class="absolute inset-0 flex flex-col justify-between overflow-hidden"
                :style="{ padding: (Math.min(cardDimensions.width, cardDimensions.height) * 0.07) + 'px ' + (cardDimensions.width * 0.07) + 'px' }"
              >
                <!-- Quote text (uppercase, heavy) -->
                <div
                  class="flex-1 flex items-center overflow-hidden"
                >
                  <div
                    :style="{
                      color: textPrimary,
                      fontFamily: currentFont?.family,
                      fontSize: quoteFontSize + 'px',
                      lineHeight: '1.5',
                      fontWeight: 900,
                      textTransform: 'uppercase',
                      letterSpacing: '-0.02em',
                      whiteSpace: 'pre-line',
                    }"
                  >{{ quote.text }}</div>
                </div>

                <!-- Attribution at bottom -->
                <div
                  :style="{
                    textAlign: 'center',
                    paddingTop: (Math.min(cardDimensions.width, cardDimensions.height) * 0.02) + 'px',
                    borderTop: '2px solid ' + dividerColor,
                    flexShrink: 0,
                  }"
                >
                  <span
                    :style="{
                      color: textSecondary,
                      fontSize: attrSmallSize + 'px',
                      fontFamily: currentFont?.family,
                      fontWeight: 600,
                      textTransform: 'uppercase',
                      letterSpacing: '0.2em',
                    }"
                  >
                    <template v-if="attribution[0]">{{ attribution[0] }}</template>
                    <template v-if="attribution[0] && attribution[1]"> —— </template>
                    <template v-if="attribution[1]">{{ attribution[1] }}</template>
                  </span>
                </div>
              </div>
            </div>
          </div>
          </div>
        </div>

        <!-- RIGHT: Controls Sidebar -->
        <div class="w-full lg:w-80 border-t lg:border-t-0 lg:border-l border-slate-800 flex flex-col flex-1 min-h-0">

          <!-- Header -->
          <DialogHeader class="px-4 py-3 sm:p-5 border-b border-slate-800 shrink-0">
            <DialogTitle class="text-base sm:text-lg font-black text-white flex items-center gap-2">
              <div class="w-6 h-6 sm:w-7 sm:h-7 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                <Download :size="14" class="text-white" />
              </div>
              Design Card
            </DialogTitle>
            <DialogDescription class="sr-only">
              Customize and download your quote as a styled card image
            </DialogDescription>
          </DialogHeader>

          <!-- Scrollable Controls -->
          <div class="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 sm:space-y-6 custom-scrollbar">

            <!-- Section: Layout Template -->
            <div>
              <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2 mb-3">
                <Layout :size="12" /> Layout
              </label>
              <div class="grid grid-cols-2 gap-2">
                <button
                  v-for="tmpl in templates"
                  :key="tmpl.id"
                  @click="selectedTemplate = tmpl.id"
                  :class="selectedTemplate === tmpl.id
                    ? 'border-indigo-500 bg-indigo-500/10 text-white'
                    : 'border-slate-700 text-slate-400 hover:border-slate-600 hover:text-slate-300'"
                  class="px-3 py-2.5 rounded-xl border-2 text-left transition-all"
                >
                  <span class="text-xs font-bold block">{{ tmpl.label }}</span>
                  <span class="text-[9px] text-slate-500 block mt-0.5">{{ tmpl.description }}</span>
                </button>
              </div>
            </div>

            <!-- Section: Background -->
            <div>
              <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2 mb-3">
                <Palette :size="12" /> Background
              </label>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="bg in backgrounds"
                  :key="bg.id"
                  @click="selectedBackground = bg.id"
                  :title="bg.name"
                  :class="selectedBackground === bg.id
                    ? 'ring-2 ring-indigo-500 ring-offset-2 ring-offset-slate-900 scale-110'
                    : 'hover:scale-105'"
                  class="w-8 h-8 rounded-lg transition-all border border-slate-600"
                  :style="{ background: bg.preview }"
                />
              </div>
            </div>

            <!-- Section: Font -->
            <div>
              <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2 mb-3">
                <Type :size="12" /> Font
              </label>
              <div class="space-y-1.5">
                <button
                  v-for="font in fonts"
                  :key="font.id"
                  @click="selectedFont = font.id"
                  :class="selectedFont === font.id
                    ? 'border-indigo-500 bg-indigo-500/10'
                    : 'border-slate-700/50 hover:border-slate-600'"
                  class="w-full text-left px-3 py-2 sm:py-2.5 rounded-xl border-2 transition-all"
                >
                  <span :style="{ fontFamily: font.family }" class="text-white text-xs sm:text-sm font-medium">
                    {{ font.name }}
                  </span>
                  <span :style="{ fontFamily: font.family }" class="text-slate-500 text-[10px] sm:text-xs italic block mt-0.5 hidden sm:block">
                    {{ font.preview }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Section: Font Size -->
            <div>
              <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2 mb-3">
                <Type :size="12" /> Size Adjust
              </label>
              <div class="flex items-center gap-3">
                <button
                  @click="fontSizeAdjust = Math.max(fontSizeAdjust - 1, -5)"
                  :disabled="fontSizeAdjust <= -5"
                  class="w-9 h-9 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 flex items-center justify-center hover:border-slate-500 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Minus :size="14" />
                </button>
                <div class="flex-1 text-center">
                  <span
                    class="text-sm font-bold"
                    :class="fontSizeAdjust === 0 ? 'text-slate-500' : 'text-indigo-400'"
                  >
                    {{ fontSizeAdjust === 0 ? 'Default' : (fontSizeAdjust > 0 ? '+' : '') + fontSizeAdjust }}
                  </span>
                </div>
                <button
                  @click="fontSizeAdjust = Math.min(fontSizeAdjust + 1, 5)"
                  :disabled="fontSizeAdjust >= 5"
                  class="w-9 h-9 rounded-lg border border-slate-700 bg-slate-800 text-slate-300 flex items-center justify-center hover:border-slate-500 hover:text-white transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Plus :size="14" />
                </button>
                <button
                  v-if="fontSizeAdjust !== 0"
                  @click="fontSizeAdjust = 0"
                  class="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
                >
                  Reset
                </button>
              </div>
            </div>

            <!-- Section: Aspect Ratio -->
            <div>
              <label class="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2 mb-3">
                <RectangleHorizontal :size="12" /> Size
              </label>
              <div class="flex gap-2">
                <button
                  v-for="ratio in aspectRatios"
                  :key="ratio.id"
                  @click="selectedAspectRatio = ratio.id"
                  :class="selectedAspectRatio === ratio.id
                    ? 'bg-indigo-500 text-white border-indigo-500'
                    : 'bg-slate-800 text-slate-400 border-slate-700 hover:border-slate-600'"
                  class="flex-1 px-3 py-2 rounded-xl text-center border transition-all"
                >
                  <span class="text-xs font-bold block">{{ ratio.label }}</span>
                  <span class="text-[9px] opacity-60">{{ ratio.ratio }}</span>
                </button>
              </div>
            </div>
          </div>

          <!-- Footer: Download Button -->
          <div class="p-4 sm:p-5 border-t border-slate-800 shrink-0" style="padding-bottom: max(1rem, env(safe-area-inset-bottom))">
            <button
              @click="handleDownload"
              :disabled="isGenerating"
              class="w-full px-4 py-2.5 sm:py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="isGenerating" :size="18" class="animate-spin" />
              <Download v-else :size="18" />
              {{ isGenerating ? 'Generating...' : 'Download PNG' }}
            </button>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
