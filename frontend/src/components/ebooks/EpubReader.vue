<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { READER_THEMES, READER_FONTS, READER_MARGINS } from '@/stores/readerSettingsStore'
import { describeRange } from '@/utils/textContext'

const props = defineProps({
  data: { type: ArrayBuffer, required: true },
  ebookId: { type: [Number, String], required: true },
  initialPosition: { type: String, default: '' },
  settings: { type: Object, required: true },
})

const emit = defineEmits(['ready', 'relocated', 'tap', 'error', 'selection'])

const viewer = ref(null)
let book = null
let rendition = null
let toc = []
let currentCfi = props.initialPosition || ''
let locationsReady = false
let touchStart = null

const STYLE_ID = 'lumina-reader-style'
const LOCATIONS_KEY = `ebook_locations_${props.ebookId}`

// Reader styles injected into every chapter document. !important so publisher CSS can't win.
const buildCss = () => {
  const s = props.settings
  const theme = READER_THEMES[s.theme] || READER_THEMES.dark
  const font = READER_FONTS[s.fontFamily]?.css
  return `
    html, body { background: ${theme.bg} !important; }
    body {
      color: ${theme.fg} !important;
      font-size: ${s.fontSize}% !important;
      line-height: ${s.lineHeight} !important;
      ${font ? `font-family: ${font} !important;` : ''}
      -webkit-text-size-adjust: none;
    }
    body * { color: inherit !important; background-color: transparent !important; }
    p, li, blockquote, dd, dt, td { line-height: ${s.lineHeight} !important; ${font ? 'font-family: inherit !important;' : ''} }
    p, li, blockquote { font-size: 1em !important; }
    a, a * { color: ${theme.link} !important; }
    img, svg, video { max-width: 100% !important; height: auto; }
    ::selection { background: rgba(99, 102, 241, 0.35); }
  `
}

const applyStyleTo = (doc) => {
  if (!doc) return
  let el = doc.getElementById(STYLE_ID)
  if (!el) {
    el = doc.createElement('style')
    el.id = STYLE_ID
    doc.head?.appendChild(el)
  }
  el.textContent = buildCss()
}

const applyStyles = () => {
  if (!rendition) return
  rendition.getContents().forEach((contents) => applyStyleTo(contents.document))
}

const tocLabelFor = (href) => {
  if (!href) return ''
  const base = href.split('#')[0]
  let found = ''
  const walk = (items) => {
    for (const item of items) {
      if (item.href && item.href.split('#')[0].endsWith(base)) found = item.label.trim()
      if (item.subitems?.length) walk(item.subitems)
    }
  }
  walk(toc)
  return found
}

const emitLocation = (location) => {
  if (!location?.start) return
  currentCfi = location.start.cfi
  const progress = locationsReady ? book.locations.percentageFromCfi(currentCfi) : null
  emit('relocated', {
    position: currentCfi,
    progress,
    label: tocLabelFor(location.start.href),
    atStart: location.atStart,
    atEnd: location.atEnd,
  })
}

const loadLocations = async () => {
  try {
    const cached = localStorage.getItem(LOCATIONS_KEY)
    if (cached) {
      book.locations.load(cached)
    } else {
      await book.locations.generate(1600)
      try {
        localStorage.setItem(LOCATIONS_KEY, book.locations.save())
      } catch {
        // too big for localStorage - regenerate next time
      }
    }
    locationsReady = true
    const location = rendition?.currentLocation()
    if (location) emitLocation(location)
  } catch {
    // progress % unavailable, reading still works
  }
}

// Tap zones (paginated): left third = previous, right third = next, middle = toggle chrome
const handleClick = (e) => {
  const selection = e.view?.getSelection?.()
  if (selection && selection.toString().trim()) return

  if (props.settings.epubFlow === 'scrolled') {
    emit('tap', 'center')
    return
  }
  const frameLeft = e.view?.frameElement?.getBoundingClientRect().left || 0
  const rect = viewer.value.getBoundingClientRect()
  const x = (frameLeft + e.clientX - rect.left) / rect.width
  if (x < 0.3) prev()
  else if (x > 0.7) next()
  else emit('tap', 'center')
}

const handleTouchStart = (e) => {
  const t = e.changedTouches?.[0]
  if (t) touchStart = { x: t.screenX, y: t.screenY, time: Date.now() }
}

// Report text selections (for quotes / words / notes) - debounced while handles are dragged
const watchSelection = (contents) => {
  const doc = contents.document
  let timer = null
  doc.addEventListener('selectionchange', () => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      const selection = doc.getSelection()
      if (!selection || selection.isCollapsed || !selection.rangeCount) {
        emit('selection', null)
        return
      }
      const range = selection.getRangeAt(0)
      const info = describeRange(range)
      if (!info) return
      let cfi = ''
      try {
        cfi = contents.cfiFromRange(range)
      } catch {
        // CFI is optional
      }
      emit('selection', { ...info, cfi })
    }, 300)
  })
}

const clearSelection = () => {
  rendition?.getContents().forEach((contents) => contents.window?.getSelection()?.removeAllRanges())
}

const handleTouchEnd = (e) => {
  const t = e.changedTouches?.[0]
  if (!t || !touchStart || props.settings.epubFlow === 'scrolled') return
  // Dragging selection handles must not turn the page
  if (e.view?.getSelection?.()?.toString().trim()) {
    touchStart = null
    return
  }
  const dx = t.screenX - touchStart.x
  const dy = t.screenY - touchStart.y
  const fast = Date.now() - touchStart.time < 600
  touchStart = null
  if (fast && Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    dx < 0 ? next() : prev()
  }
}

const handleKey = (e) => {
  if (e.key === 'ArrowRight' || e.key === 'PageDown') next()
  else if (e.key === 'ArrowLeft' || e.key === 'PageUp') prev()
}

const createRendition = async (target) => {
  const scrolled = props.settings.epubFlow === 'scrolled'
  rendition = book.renderTo(viewer.value, {
    width: '100%',
    height: '100%',
    spread: 'none',
    flow: scrolled ? 'scrolled' : 'paginated',
    manager: scrolled ? 'continuous' : 'default',
    allowScriptedContent: false,
  })
  rendition.hooks.content.register((contents) => {
    applyStyleTo(contents.document)
    watchSelection(contents)
  })
  rendition.on('relocated', emitLocation)
  rendition.on('click', handleClick)
  rendition.on('touchstart', handleTouchStart)
  rendition.on('touchend', handleTouchEnd)
  rendition.on('keyup', handleKey)

  try {
    await rendition.display(target || undefined)
  } catch {
    // Saved CFI no longer valid - start from the beginning
    await rendition.display()
  }
}

// Changing flow needs a fresh rendition; reopen at the same spot
const rebuild = async () => {
  const target = currentCfi
  rendition?.destroy()
  rendition = null
  await createRendition(target)
}

const next = () => rendition?.next()
const prev = () => rendition?.prev()
const goToHref = (href) => rendition?.display(href)
const goToProgress = (fraction) => {
  if (!locationsReady) return
  rendition?.display(book.locations.cfiFromPercentage(Math.min(Math.max(fraction, 0), 1)))
}

defineExpose({ next, prev, goToHref, goToProgress, clearSelection })

onMounted(async () => {
  try {
    const { default: ePub } = await import('epubjs')
    book = ePub(props.data)
    await book.ready
    const navigation = await book.loaded.navigation
    toc = navigation?.toc || []
    await createRendition(props.initialPosition)
    emit('ready', { toc })
    loadLocations()
  } catch (err) {
    emit('error', err)
  }
})

watch(
  () => [props.settings.theme, props.settings.fontSize, props.settings.fontFamily, props.settings.lineHeight],
  applyStyles
)
watch(() => props.settings.epubFlow, () => rebuild())
watch(() => props.settings.margin, async () => {
  await nextTick()
  rendition?.resize()
})

onBeforeUnmount(() => {
  rendition?.destroy()
  book?.destroy()
})
</script>

<template>
  <div
    class="h-full w-full max-w-[760px] mx-auto"
    :style="{ paddingLeft: `${READER_MARGINS[settings.margin]?.px ?? 28}px`, paddingRight: `${READER_MARGINS[settings.margin]?.px ?? 28}px` }"
  >
    <div ref="viewer" class="h-full w-full" />
  </div>
</template>
