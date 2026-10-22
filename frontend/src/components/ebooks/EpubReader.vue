<script setup>
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { READER_THEMES, READER_FONTS, READER_MARGINS } from '@/stores/readerSettingsStore'
import { describeRange } from '@/utils/textContext'
import { normalizeQuery, findAll, excerpt } from '@/utils/textSearch'

const props = defineProps({
  data: { type: ArrayBuffer, required: true },
  ebookId: { type: [Number, String], required: true },
  initialPosition: { type: String, default: '' },
  settings: { type: Object, required: true },
  annotations: { type: Array, default: () => [] }, // highlights: { id, kind, position (CFI range) }
})

const emit = defineEmits(['ready', 'relocated', 'tap', 'error', 'selection', 'annotation-click'])

const viewer = ref(null)
let book = null
let rendition = null
let EpubCFI = null
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

/* ---------- chapter detection (for the progress label and note references) ---------- */

let flatToc = [] // TOC in reading order: { label, href, parent }

const flattenToc = (items, parent = '') => {
  for (const item of items) {
    const label = (item.label || '').replace(/\s+/g, ' ').trim()
    flatToc.push({ label, href: item.href || '', parent })
    if (item.subitems?.length) flattenToc(item.subitems, label)
  }
}

const fileOf = (href) => (href || '').split('#')[0]
const sameFile = (a, b) => !!a && !!b && (a.endsWith(b) || b.endsWith(a))
const normalize = (text) => (text || '').replace(/\s+/g, ' ').trim()

// "Glava 7" / "ГЛАВА 7" / "Chapter 7" / "Псалам 23" -> "7" (so references read "Matej 7:12")
const CHAPTER_WORD = /^(глава|glava|поглавље|poglavlje|chapter|chap\.?|kapitel|chapitre|capitolo|capítulo|псалам|psalam|psalm)\s+(\d+)\.?$/i
const chapterNumber = (label) => label.match(CHAPTER_WORD)?.[2] || label

// "Matej" + "7" -> "Matej 7"; "Matej" + "Glava 7" -> "Matej 7"; otherwise "Matej › Title"
const joinLabel = (parent, label) => {
  if (!parent) return label
  if (!label) return parent
  label = chapterNumber(label)
  if (/^\d+$/.test(label)) return `${parent} ${label}`
  if (label.toLowerCase().includes(parent.toLowerCase())) return label
  return `${parent} › ${label}`
}

// True if element `el` comes before (or contains) `node` in the document
const precedes = (el, node) =>
  el === node || el.contains(node) || !!(el.compareDocumentPosition(node) & Node.DOCUMENT_POSITION_FOLLOWING)

// Chapters often exist only as headings in the text (e.g. Bible books split into numbered chapters)
const HEADING_SELECTOR = 'h1, h2, h3, h4, h5, h6, [class*="chapter" i], [class*="chap" i], [class*="glava" i], [class*="poglav" i]'
const lastHeadingBefore = (doc, node) => {
  let found = ''
  for (const el of doc.querySelectorAll(HEADING_SELECTOR)) {
    if (!precedes(el, node)) break
    const text = normalize(el.textContent)
    if (text && text.length <= 60) found = text
  }
  return found
}

const chapterAt = (doc, node, sectionHref) => {
  const file = fileOf(sectionHref)
  let best = null
  for (const item of flatToc) {
    if (!sameFile(fileOf(item.href), file)) continue
    const fragment = item.href.split('#')[1]
    if (!fragment) {
      if (!best) best = item
      continue
    }
    const el = doc.getElementById(decodeURIComponent(fragment))
    if (el && precedes(el, node)) best = item
  }

  let label = best ? joinLabel(best.parent, best.label) : ''
  if (!best || !best.href.includes('#')) {
    const heading = lastHeadingBefore(doc, node)
    const same = heading && label && (label.toLowerCase().includes(heading.toLowerCase()) || heading.toLowerCase().includes(label.toLowerCase()))
    if (heading && !same) label = joinLabel(label, heading)
  }
  return label.slice(0, 200)
}

// Fallback when the DOM isn't available: the TOC entry for the file
const tocLabelFor = (href) => {
  const item = flatToc.find((i) => sameFile(fileOf(i.href), fileOf(href)))
  return item ? joinLabel(item.parent, item.label) : ''
}

const labelForLocation = (location) => {
  try {
    const range = rendition.getRange(location.start.cfi)
    if (range) return chapterAt(range.startContainer.ownerDocument, range.startContainer, location.start.href)
  } catch {
    // section not rendered yet
  }
  return tocLabelFor(location.start.href)
}

// Where the current spine section (e.g. one Gospel) ends, as a progress fraction - for time estimates
const sectionEnds = new Map()
const sectionEndProgress = (index) => {
  if (!locationsReady || index == null) return null
  if (!sectionEnds.has(index)) {
    const all = book.locations._locations || []
    const next = all.findIndex((cfi) => new EpubCFI(cfi).spinePos > index)
    sectionEnds.set(index, next < 0 ? 1 : next / all.length)
  }
  return sectionEnds.get(index)
}

const emitLocation = (location) => {
  if (!location?.start) return
  currentCfi = location.start.cfi
  const progress = locationsReady ? book.locations.percentageFromCfi(currentCfi) : null
  emit('relocated', {
    position: currentCfi,
    progress,
    label: labelForLocation(location),
    section: tocLabelFor(location.start.href),
    sectionEnd: sectionEndProgress(location.start.index),
    atStart: location.atStart,
    atEnd: location.atEnd,
  })
}

/* ---------- highlights (saved quotes / notes / words) ---------- */

const HIGHLIGHT_STYLES = {
  quote: { fill: '#818cf8', 'fill-opacity': '0.32' },
  note: { fill: '#38bdf8', 'fill-opacity': '0.32' },
  word: { fill: '#fbbf24', 'fill-opacity': '0.38' },
}
const drawn = new Map() // annotation id -> CFI
let lastHighlightClick = 0

const drawAnnotations = () => {
  if (!rendition) return
  const wanted = new Map(props.annotations.filter((a) => a.position?.startsWith('epubcfi')).map((a) => [a.id, a]))
  for (const [id, cfi] of drawn) {
    if (wanted.get(id)?.position !== cfi) {
      rendition.annotations.remove(cfi, 'highlight')
      drawn.delete(id)
    }
  }
  for (const [id, annotation] of wanted) {
    if (drawn.has(id)) continue
    try {
      rendition.annotations.highlight(annotation.position, { id }, () => {
        lastHighlightClick = Date.now()
        emit('annotation-click', id)
      }, `hl-${annotation.kind}`, HIGHLIGHT_STYLES[annotation.kind] || HIGHLIGHT_STYLES.quote)
      drawn.set(id, annotation.position)
    } catch {
      // position no longer valid in this file
    }
  }
}

// Briefly mark a search hit
const flash = (cfi) => {
  try {
    rendition.annotations.highlight(cfi, {}, null, 'search-hit', { fill: '#facc15', 'fill-opacity': '0.55' })
    setTimeout(() => rendition?.annotations.remove(cfi, 'highlight'), 2500)
  } catch {
    // ignore
  }
}

/* ---------- search ---------- */

let searchRun = 0
// Streams results section by section via onResults([...]); a newer search cancels older ones
const search = async (query, onResults) => {
  const run = ++searchRun
  const normalized = normalizeQuery(query)
  if (normalized.length < 2 || !book) return
  let total = 0
  for (const section of book.spine.spineItems) {
    if (run !== searchRun || total >= 500) return
    try {
      await section.load(book.load.bind(book))
      const doc = section.document
      const walker = doc.createTreeWalker(doc.body || doc.documentElement, NodeFilter.SHOW_TEXT)
      const results = []
      let node
      while ((node = walker.nextNode()) && total + results.length < 500) {
        for (const match of findAll(node.textContent, normalized, 50)) {
          const range = doc.createRange()
          range.setStart(node, match.start)
          range.setEnd(node, match.end)
          results.push({
            cfi: section.cfiFromRange(range),
            chapter: chapterAt(doc, node, section.href),
            excerpt: excerpt(node.textContent, match.start, match.end),
          })
        }
      }
      section.unload()
      total += results.length
      if (results.length && run === searchRun) onResults(results)
    } catch {
      // unreadable section - skip
    }
    await new Promise((resolve) => setTimeout(resolve)) // keep the UI responsive
  }
}

const cancelSearch = () => { searchRun++ }

const goToSearchResult = async (cfi) => {
  await rendition?.display(cfi)
  flash(cfi)
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
  // A tap on a highlight opens it - don't also turn the page
  setTimeout(() => {
    if (Date.now() - lastHighlightClick < 400) return
    handleTap(e)
  }, 40)
}

const handleTap = (e) => {
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
      const sectionHref = book.spine.get(contents.sectionIndex)?.href
      emit('selection', { ...info, cfi, chapter: chapterAt(doc, range.startContainer, sectionHref) })
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
  drawn.clear()
  drawAnnotations()
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

const goToPosition = (cfi) => rendition?.display(cfi)

defineExpose({ next, prev, goToHref, goToProgress, goToPosition, clearSelection, search, cancelSearch, goToSearchResult })

onMounted(async () => {
  try {
    const epubjs = await import('epubjs')
    const ePub = epubjs.default
    EpubCFI = epubjs.EpubCFI || ePub.CFI
    book = ePub(props.data)
    await book.ready
    const navigation = await book.loaded.navigation
    toc = navigation?.toc || []
    flatToc = []
    flattenToc(toc)
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
watch(() => props.annotations, drawAnnotations, { deep: true })
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
