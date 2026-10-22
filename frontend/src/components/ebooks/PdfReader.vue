<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { READER_THEMES, READER_FONTS, READER_MARGINS } from '@/stores/readerSettingsStore'
import { textContentToBlocks } from '@/utils/pdfReflow'
import { pdfHasTextLayer } from '@/utils/ebookMetadata'
import { describeRange } from '@/utils/textContext'

const props = defineProps({
  data: { type: ArrayBuffer, required: true },
  initialPosition: { type: String, default: '' },
  settings: { type: Object, required: true },
  language: { type: String, default: '' },
})

const emit = defineEmits(['ready', 'relocated', 'tap', 'error', 'selection'])

const scroller = ref(null)
const numPages = ref(0)
const hasText = ref(true)
const loading = ref(true)
const currentPage = ref(Math.max(1, parseInt(props.initialPosition, 10) || 1))

let doc = null
const pageCache = new Map()
const getPage = (n) => {
  if (!pageCache.has(n)) pageCache.set(n, doc.getPage(n))
  return pageCache.get(n)
}

// Scanned PDFs have no text layer - only page mode is possible
const mode = computed(() => (hasText.value ? props.settings.pdfMode : 'page'))
const theme = computed(() => READER_THEMES[props.settings.theme] || READER_THEMES.dark)
const marginPx = computed(() => READER_MARGINS[props.settings.margin]?.px ?? 28)

const reportLocation = () => {
  if (!numPages.value) return
  emit('relocated', {
    position: String(currentPage.value),
    progress: currentPage.value / numPages.value,
    label: `Page ${currentPage.value} of ${numPages.value}`,
  })
}
watch(currentPage, reportLocation)

/* ============================ PAGE MODE ============================ */

const containerWidth = ref(0)
const baseRatio = ref(1.414) // height / width, from page 1
const pageRatios = ref({})
const intersecting = new Set()
const renderTasks = new Map()
let pageObserver = null
let resizeObserver = null

const pageWidth = computed(() => {
  const available = Math.max(containerWidth.value - 16, 200)
  return Math.round(Math.min(available, 900) * props.settings.pdfZoom)
})
const pageHeight = (n) => Math.round(pageWidth.value * (pageRatios.value[n] || baseRatio.value))

const canvasFilter = computed(() => ({
  dark: 'invert(0.88) hue-rotate(180deg)',
  black: 'invert(1) hue-rotate(180deg)',
  sepia: 'sepia(0.35) brightness(0.97)',
  light: 'none',
}[props.settings.theme] || 'none'))

const pageEl = (n) => scroller.value?.querySelector(`[data-page="${n}"]`)

const clearPage = (n) => {
  renderTasks.get(n)?.cancel()
  renderTasks.delete(n)
  pageEl(n)?.querySelector('canvas')?.remove()
}

const renderPage = async (n) => {
  const el = pageEl(n)
  if (!el || renderTasks.has(n)) return
  try {
    const page = await getPage(n)
    const base = page.getViewport({ scale: 1 })
    if (!pageRatios.value[n]) pageRatios.value = { ...pageRatios.value, [n]: base.height / base.width }

    const dpr = Math.min(window.devicePixelRatio || 1, 2.5)
    const viewport = page.getViewport({ scale: (pageWidth.value / base.width) * dpr })
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(viewport.width)
    canvas.height = Math.round(viewport.height)
    canvas.className = 'block w-full h-full'

    const task = page.render({ canvasContext: canvas.getContext('2d'), viewport })
    renderTasks.set(n, task)
    await task.promise
    if (renderTasks.get(n) !== task) return
    el.querySelector('canvas')?.remove()
    el.appendChild(canvas)
  } catch (err) {
    if (err?.name !== 'RenderingCancelledException') console.warn('PDF render failed', err)
  }
}

const setupPageObserver = () => {
  pageObserver?.disconnect()
  intersecting.clear()
  pageObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const n = Number(entry.target.dataset.page)
      if (entry.isIntersecting) {
        intersecting.add(n)
        renderPage(n)
      } else {
        intersecting.delete(n)
        clearPage(n) // free canvas memory for far-away pages
      }
    })
  }, { root: scroller.value, rootMargin: '150% 0px' })
  scroller.value.querySelectorAll('[data-page]').forEach((el) => pageObserver.observe(el))
}

// Re-render visible pages after zoom/resize changed their size
const rerenderVisible = async (keepPage) => {
  const target = keepPage || currentPage.value
  ;[...renderTasks.keys()].forEach(clearPage)
  await nextTick()
  scrollToPage(target)
  intersecting.forEach((n) => renderPage(n))
}

/* =========================== REFLOW MODE =========================== */

const blocks = ref({}) // page -> blocks
const rangeStart = ref(1)
const rangeEnd = ref(0)
const reflowPages = computed(() => {
  const pages = []
  for (let n = rangeStart.value; n <= rangeEnd.value; n++) pages.push(n)
  return pages
})
let reflowBusy = false
let sentinelObserver = null
const topSentinel = ref(null)
const bottomSentinel = ref(null)

const loadBlocks = async (n) => {
  if (blocks.value[n]) return
  const content = await (await getPage(n)).getTextContent()
  const result = textContentToBlocks(content)
  // A page that starts mid-sentence continues the previous page's paragraph
  if (result[0]?.type === 'p' && /^\p{Ll}/u.test(result[0].text)) result[0].continues = true
  blocks.value = { ...blocks.value, [n]: result }
}

const appendPage = async () => {
  if (reflowBusy || rangeEnd.value >= numPages.value) return
  reflowBusy = true
  try {
    await loadBlocks(rangeEnd.value + 1)
    rangeEnd.value++
  } finally {
    reflowBusy = false
  }
}

const prependPage = async () => {
  if (reflowBusy || rangeStart.value <= 1) return
  reflowBusy = true
  try {
    const el = scroller.value
    await loadBlocks(rangeStart.value - 1)
    const prevHeight = el.scrollHeight
    const prevTop = el.scrollTop
    rangeStart.value--
    await nextTick()
    // Keep the text the user is reading in place
    el.scrollTop = prevTop + (el.scrollHeight - prevHeight)
  } finally {
    reflowBusy = false
  }
}

const initReflow = async (startPage) => {
  sentinelObserver?.disconnect()
  rangeStart.value = startPage
  rangeEnd.value = startPage - 1
  await appendPage()
  await nextTick()
  scroller.value.scrollTop = 0
  // Fill at least two screens so scrolling has somewhere to go
  while (rangeEnd.value < numPages.value && scroller.value.scrollHeight < scroller.value.clientHeight * 2) {
    await appendPage()
    await nextTick()
  }
  sentinelObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return
      if (entry.target === bottomSentinel.value) appendPage()
      else if (entry.target === topSentinel.value) prependPage()
    })
  }, { root: scroller.value, rootMargin: '600px 0px' })
  sentinelObserver.observe(topSentinel.value)
  sentinelObserver.observe(bottomSentinel.value)
}

const reflowStyle = computed(() => ({
  fontFamily: READER_FONTS[props.settings.fontFamily]?.css || READER_FONTS.serif.css,
  fontSize: `calc(1.0625rem * ${props.settings.fontSize / 100})`,
  lineHeight: props.settings.lineHeight,
  paddingLeft: `${marginPx.value}px`,
  paddingRight: `${marginPx.value}px`,
}))

/* ============================== SHARED ============================== */

// The page whose top edge has most recently scrolled past the top of the viewport
let scrollRaf = null
const handleScroll = () => {
  if (scrollRaf) return
  scrollRaf = requestAnimationFrame(() => {
    scrollRaf = null
    const el = scroller.value
    if (!el) return
    const probe = el.scrollTop + el.clientHeight * 0.3
    let page = null
    el.querySelectorAll('[data-page]').forEach((node) => {
      if (node.offsetTop <= probe) page = Number(node.dataset.page)
    })
    if (page) currentPage.value = page
  })
}

const scrollToPage = (n) => {
  const el = pageEl(n)
  if (el && scroller.value) scroller.value.scrollTop = el.offsetTop
}

const setupMode = async () => {
  const startPage = currentPage.value
  await nextTick()
  if (mode.value === 'page') {
    sentinelObserver?.disconnect()
    await nextTick()
    setupPageObserver()
    scrollToPage(startPage)
  } else {
    pageObserver?.disconnect()
    ;[...renderTasks.keys()].forEach(clearPage)
    await initReflow(startPage)
  }
  currentPage.value = startPage
  reportLocation()
}

const goToPage = async (n) => {
  const page = Math.min(Math.max(1, Math.round(n)), numPages.value)
  if (mode.value === 'page') {
    scrollToPage(page)
  } else {
    blocks.value = {}
    await initReflow(page)
  }
  currentPage.value = page
}

const goToProgress = (fraction) => goToPage(Math.max(1, Math.ceil(fraction * numPages.value)))

const scrollByScreen = (direction) => {
  const el = scroller.value
  el?.scrollBy({ top: direction * el.clientHeight * 0.9, behavior: 'smooth' })
}
const next = () => scrollByScreen(1)
const prev = () => scrollByScreen(-1)

// Text selection works in reflow mode (page mode is a rendered image)
let selectionTimer = null
const handleSelectionChange = () => {
  clearTimeout(selectionTimer)
  selectionTimer = setTimeout(() => {
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || !selection.rangeCount || mode.value !== 'reflow') {
      emit('selection', null)
      return
    }
    const range = selection.getRangeAt(0)
    if (!scroller.value?.contains(range.commonAncestorContainer)) return
    const info = describeRange(range)
    if (!info) return
    let node = range.startContainer
    if (node.nodeType !== 1) node = node.parentElement
    const page = Number(node?.closest('[data-page]')?.dataset.page) || currentPage.value
    // Chapter = last heading recognised before the selection (among the loaded pages)
    let chapter = ''
    for (const heading of scroller.value.querySelectorAll('.pdf-reflow-page h2')) {
      if (!(heading.compareDocumentPosition(range.startContainer) & Node.DOCUMENT_POSITION_FOLLOWING)) break
      chapter = heading.textContent.replace(/\s+/g, ' ').trim().slice(0, 200)
    }
    emit('selection', { ...info, page, chapter })
  }, 300)
}

const clearSelection = () => window.getSelection()?.removeAllRanges()

const handleClick = (e) => {
  if (e.target.closest('a')) return
  if (window.getSelection()?.toString().trim()) return
  emit('tap', 'center')
}

const handleKey = (e) => {
  if (['ArrowDown', 'PageDown', ' '].includes(e.key) && e.target === document.body) {
    e.preventDefault()
    next()
  } else if (['ArrowUp', 'PageUp'].includes(e.key) && e.target === document.body) {
    e.preventDefault()
    prev()
  }
}

onMounted(async () => {
  try {
    const { default: pdfjs } = await import('@/utils/pdfjs')
    // pdf.js takes ownership of the buffer it is given - pass a copy (original stays cached)
    doc = await pdfjs.getDocument({ data: props.data.slice(0) }).promise
    numPages.value = doc.numPages
    currentPage.value = Math.min(currentPage.value, doc.numPages)

    const first = (await getPage(1)).getViewport({ scale: 1 })
    baseRatio.value = first.height / first.width
    hasText.value = await pdfHasTextLayer(doc).catch(() => true)

    containerWidth.value = scroller.value.clientWidth
    resizeObserver = new ResizeObserver(() => {
      const width = scroller.value?.clientWidth || 0
      if (Math.abs(width - containerWidth.value) > 20) {
        containerWidth.value = width
        if (mode.value === 'page') rerenderVisible()
      }
    })
    resizeObserver.observe(scroller.value)

    loading.value = false
    emit('ready', { numPages: doc.numPages, hasText: hasText.value })
    await setupMode()
  } catch (err) {
    loading.value = false
    emit('error', err)
  }
  window.addEventListener('keydown', handleKey)
  document.addEventListener('selectionchange', handleSelectionChange)
})

watch(mode, (value, old) => {
  if (old && !loading.value) setupMode()
})
watch(() => props.settings.pdfZoom, () => {
  if (mode.value === 'page') rerenderVisible(currentPage.value)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKey)
  document.removeEventListener('selectionchange', handleSelectionChange)
  clearTimeout(selectionTimer)
  pageObserver?.disconnect()
  sentinelObserver?.disconnect()
  resizeObserver?.disconnect()
  renderTasks.forEach((task) => task.cancel())
  doc?.destroy()
})

const goToPosition = (position) => goToPage(parseInt(position, 10) || 1)

defineExpose({ next, prev, goToPage, goToProgress, goToPosition, clearSelection })
</script>

<template>
  <div
    ref="scroller"
    class="relative h-full w-full overflow-auto overscroll-contain"
    :style="{ background: theme.bg, color: theme.fg }"
    @scroll.passive="handleScroll"
    @click="handleClick"
  >
    <div v-if="loading" class="h-full flex items-center justify-center text-sm" :style="{ color: theme.muted }">
      Opening PDF…
    </div>

    <!-- PAGE MODE: rendered pages, lazily drawn as they approach the viewport -->
    <div v-else-if="mode === 'page'" class="py-4 space-y-3 flex flex-col items-center min-w-fit">
      <div
        v-for="n in numPages"
        :key="n"
        :data-page="n"
        class="pdf-page relative shrink-0 shadow-lg bg-white"
        :style="{ width: `${pageWidth}px`, height: `${pageHeight(n)}px`, filter: canvasFilter }"
      />
    </div>

    <!-- REFLOW MODE: extracted text, re-wrapped to the screen like an e-book -->
    <div v-else class="max-w-[42rem] mx-auto py-6" :lang="language || undefined" :style="reflowStyle">
      <div ref="topSentinel" class="h-px" />
      <section v-for="n in reflowPages" :key="n" :data-page="n" class="pdf-reflow-page">
        <template v-for="(block, i) in blocks[n]" :key="i">
          <h2 v-if="block.type === 'h'" class="font-bold mt-8 mb-4" style="font-size: 1.35em; line-height: 1.3">
            {{ block.text }}
          </h2>
          <!-- Justify only where lines are long enough not to leave word gaps -->
          <p v-else :class="[block.continues ? '' : 'mt-[0.9em]', 'text-left sm:text-justify']" style="hyphens: auto">
            {{ block.text }}
          </p>
        </template>
        <div class="text-center text-xs my-6 select-none font-sans" :style="{ color: theme.muted }">— {{ n }} —</div>
      </section>
      <div ref="bottomSentinel" class="h-px" />
    </div>
  </div>
</template>
