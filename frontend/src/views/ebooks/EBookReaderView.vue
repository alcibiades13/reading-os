<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ALargeSmall, ListTree, X, ChevronLeft, ChevronRight, Library, PartyPopper, Quote, Brain, NotebookPen, StickyNote } from 'lucide-vue-next'
import { ebooksAPI } from '@/services/api'
import { getCachedEbook, cacheEbook } from '@/utils/ebookCache'
import { useReaderSettingsStore, READER_THEMES } from '@/stores/readerSettingsStore'
import { getBookUrlWithSuffix } from '@/utils/bookUrl'
import { useToast } from '@/composables/useToast'
import EpubReader from '@/components/ebooks/EpubReader.vue'
import PdfReader from '@/components/ebooks/PdfReader.vue'
import ReaderSettingsPanel from '@/components/ebooks/ReaderSettingsPanel.vue'
import CaptureSheet from '@/components/ebooks/CaptureSheet.vue'
import StickersSheet from '@/components/ebooks/StickersSheet.vue'

const route = useRoute()
const router = useRouter()
const readerSettings = useReaderSettingsStore()
const settings = readerSettings.settings
const { addToast } = useToast()

const ebook = ref(null)
const fileData = ref(null)
const error = ref('')
const downloadProgress = ref(null)

const reader = ref(null)
const ready = ref(false)
const showChrome = ref(true)
const showSettings = ref(false)
const showToc = ref(false)
const toc = ref([])
const pdfHasText = ref(true)

const location = ref({ position: '', progress: null, label: '' })
const sliderValue = ref(null) // while dragging

const theme = computed(() => READER_THEMES[settings.theme] || READER_THEMES.dark)
const progressPercent = computed(() =>
  location.value.progress == null ? null : Math.round(location.value.progress * 100)
)

// Page in the print edition, derived from progress (EPUBs have no fixed pages)
const printPage = computed(() => {
  const total = ebook.value?.total_pages
  if (!total || location.value.progress == null || ebook.value.format === 'pdf') return null
  return Math.min(total, Math.max(1, Math.round(location.value.progress * total)))
})

/* ---------- progress tracking ---------- */

const isTracking = computed(() => ebook.value?.track_progress === true && !!ebook.value?.library_entry)
const showTrackPrompt = ref(false)
const showFinishPrompt = ref(false)
const trackBusy = ref(false)
const trackPages = ref('')
let finishDismissed = false

// EPUB linked to nothing (or to a book without a page count) can't express progress in pages
const askForPages = computed(() => ebook.value?.format === 'epub' && !ebook.value?.total_pages)

const mergeEbook = (data) => {
  // Keep the live position - the server copy may be a few seconds behind
  ebook.value = { ...ebook.value, ...data, position: ebook.value.position, progress: ebook.value.progress }
  syncActiveSticker()
}

/* ---------- stickers: several reading threads in one book ---------- */

const activeBookmarkId = ref(null) // the sticker being read from - it follows the reader
const stickersMode = ref(null) // null | 'manage' | 'continue'
const stickersBusy = ref(false)
const bookmarks = computed(() => ebook.value?.bookmarks || [])
const activeBookmark = computed(() => bookmarks.value.find((b) => b.id === activeBookmarkId.value) || null)

// Keep the local copy of the active sticker at the live position
const syncActiveSticker = () => {
  const active = activeBookmark.value
  if (!active || !location.value.position) return
  active.position = location.value.position
  if (location.value.progress != null) active.progress = location.value.progress
}

// The book is only as far as its earliest sticker
const overallProgress = computed(() => {
  const known = bookmarks.value.map((b) => b.progress).filter((p) => p != null)
  return known.length ? Math.min(...known) : location.value.progress
})

const goToSticker = (bookmark) => {
  activeBookmarkId.value = bookmark.id
  stickersMode.value = null
  reader.value?.goToPosition(bookmark.position)
}

const continueFromLast = () => {
  activeBookmarkId.value = null
  stickersMode.value = null
}

const stickerRequest = async (request, successMessage) => {
  stickersBusy.value = true
  try {
    const { data } = await request()
    mergeEbook(data)
    if (successMessage) addToast(successMessage)
    return data
  } catch {
    addToast('Could not update stickers', 'error')
    return null
  } finally {
    stickersBusy.value = false
  }
}

const addSticker = async (label) => {
  await savePosition()
  const before = new Set(bookmarks.value.map((b) => b.id))
  const data = await stickerRequest(() => ebooksAPI.addBookmark(ebook.value.id, {
    label,
    position: location.value.position,
    progress: location.value.progress,
  }), 'Sticker added')
  // You're reading here, so the new sticker follows you
  const created = data?.bookmarks.find((b) => !before.has(b.id))
  if (created) activeBookmarkId.value = created.id
}

const renameSticker = (bookmark, label) =>
  stickerRequest(() => ebooksAPI.updateBookmark(ebook.value.id, bookmark.id, { label }))

const deleteSticker = async (bookmark) => {
  if (bookmark.id === activeBookmarkId.value) activeBookmarkId.value = null
  await stickerRequest(() => ebooksAPI.deleteBookmark(ebook.value.id, bookmark.id), 'Sticker removed')
}

const openStickers = () => {
  showSettings.value = false
  showToc.value = false
  stickersMode.value = 'manage'
}

const answerTracking = async (enabled) => {
  trackBusy.value = true
  try {
    const pages = parseInt(trackPages.value, 10)
    const { data } = await ebooksAPI.setTracking(ebook.value.id, {
      enabled,
      ...(enabled && pages > 0 ? { pages } : {}),
    })
    mergeEbook(data)
    showTrackPrompt.value = false
    if (bookmarks.value.length) stickersMode.value = 'continue'
    chromeTimer = setTimeout(() => {
      if (!showSettings.value && !showToc.value) showChrome.value = false
    }, 1500)
    if (enabled) {
      addToast('Progress will sync to your library')
      lastSaved = ''
      savePosition()
    }
  } catch {
    addToast('Could not update progress tracking', 'error')
  } finally {
    trackBusy.value = false
  }
}

const maybeOfferFinish = (loc) => {
  if (!isTracking.value || finishDismissed || ebook.value.library_entry.status === 'read') return
  // With stickers, every reading thread has to reach the end
  if (bookmarks.value.length) {
    if (overallProgress.value != null && overallProgress.value >= 0.985) showFinishPrompt.value = true
    return
  }
  if (loc.atEnd || (loc.progress != null && loc.progress >= 0.985)) {
    showFinishPrompt.value = true
  }
}

const finishBook = async () => {
  trackBusy.value = true
  try {
    await savePosition()
    const { data } = await ebooksAPI.finish(ebook.value.id)
    mergeEbook(data)
    addToast('Marked as read. Congratulations!')
  } catch {
    addToast('Could not mark the book as read', 'error')
    showFinishPrompt.value = false
  } finally {
    trackBusy.value = false
  }
}

const dismissFinish = () => {
  finishDismissed = true
  showFinishPrompt.value = false
}

const writeReview = () => {
  router.push(getBookUrlWithSuffix(ebook.value.book_detail, 'review'))
}

/* ---------- capture: selected text -> quote / word / study note ---------- */

const selection = ref(null)
const captureMode = ref(null)
const captureSelection = ref(null)

const capturePage = computed(() => {
  if (ebook.value?.format === 'pdf') return captureSelection.value?.page || null
  return printPage.value
})

const handleSelection = (sel) => {
  if (captureMode.value) return
  selection.value = sel
  if (sel) {
    clearTimeout(chromeTimer)
    showChrome.value = false
    showSettings.value = false
  }
}

const openCapture = (mode) => {
  captureSelection.value = selection.value
  captureMode.value = mode
  selection.value = null
  reader.value?.clearSelection()
}

const CAPTURE_TOASTS = { quote: 'Quote saved', word: 'Word added to vocabulary', note: 'Study note saved' }
const handleCaptured = (kind) => {
  captureMode.value = null
  addToast(CAPTURE_TOASTS[kind])
}

/* ---------- reading sessions (feed the stats) ---------- */

const TICK_SECONDS = 15
const IDLE_LIMIT_MS = 5 * 60 * 1000
let sessionSeconds = 0
let sessionStartProgress = null
let lastActivity = Date.now()
let sessionTimer = null

const tickSession = () => {
  // Only count time while the reader is visible and the user is actually turning pages
  if (document.visibilityState === 'visible' && Date.now() - lastActivity < IDLE_LIMIT_MS) {
    sessionSeconds += TICK_SECONDS
  }
}

const flushSession = () => {
  const seconds = sessionSeconds
  const start = sessionStartProgress
  const end = location.value.progress
  sessionSeconds = 0
  sessionStartProgress = end
  if (!isTracking.value || seconds < 60 || end == null) return
  ebooksAPI.logSession(ebook.value.id, {
    duration_seconds: seconds,
    start_progress: start ?? end,
    end_progress: end,
  }).catch(() => {})
}

/* ---------- loading ---------- */

const loadFile = async (meta) => {
  const cached = await getCachedEbook(meta.id, meta.file_size)
  if (cached) return cached

  const { data } = await ebooksAPI.file(meta.id, (e) => {
    if (e.total) downloadProgress.value = Math.round((e.loaded / e.total) * 100)
  })
  cacheEbook(meta.id, meta.file_size, data)
  return data
}

onMounted(async () => {
  window.addEventListener('keydown', handleKey)
  document.addEventListener('visibilitychange', handleVisibility)
  try {
    const { data: meta } = await ebooksAPI.get(route.params.id)
    ebook.value = meta
    location.value = { position: meta.position, progress: meta.progress, label: '' }
    fileData.value = await loadFile(meta)
  } catch (err) {
    error.value = err?.response?.status === 404 ? 'This e-book was not found.' : 'Could not open this e-book.'
  }
})

/* ---------- position saving ---------- */

let saveTimer = null
let lastSaved = ''

const savePosition = async () => {
  clearTimeout(saveTimer)
  saveTimer = null
  const { position, progress } = location.value
  if (!ebook.value || !position || position === lastSaved) return
  lastSaved = position
  const payload = { position }
  if (progress != null) payload.progress = progress
  if (activeBookmarkId.value) payload.bookmark = activeBookmarkId.value
  try {
    await ebooksAPI.update(ebook.value.id, payload)
  } catch {
    lastSaved = '' // retry on next move
  }
}

const handleRelocated = (loc) => {
  location.value = {
    position: loc.position,
    progress: loc.progress ?? location.value.progress,
    label: loc.label || '',
  }
  syncActiveSticker()
  lastActivity = Date.now()
  if (sessionStartProgress == null) sessionStartProgress = location.value.progress
  clearTimeout(saveTimer)
  saveTimer = setTimeout(savePosition, 2000)
  maybeOfferFinish(loc)
}

const handleVisibility = () => {
  if (document.visibilityState === 'hidden') {
    savePosition()
    flushSession()
  } else {
    lastActivity = Date.now()
  }
}

/* ---------- reader events ---------- */

let chromeTimer = null
const handleReady = (info) => {
  ready.value = true
  if (info?.toc) toc.value = info.toc
  if (info && 'hasText' in info) pdfHasText.value = info.hasText
  lastActivity = Date.now()
  sessionTimer = setInterval(tickSession, TICK_SECONDS * 1000)
  if (ebook.value.track_progress == null) {
    setTimeout(() => { showTrackPrompt.value = true }, 600)
    return
  }
  if (bookmarks.value.length) {
    stickersMode.value = 'continue'
    return
  }
  chromeTimer = setTimeout(() => {
    if (!showSettings.value && !showToc.value) showChrome.value = false
  }, 2500)
}

const handleReaderError = () => {
  error.value = 'This file could not be read. It may be damaged or DRM-protected.'
}

const handleTap = () => {
  if (showSettings.value || showToc.value) {
    showSettings.value = false
    showToc.value = false
    return
  }
  clearTimeout(chromeTimer)
  showChrome.value = !showChrome.value
}

const openToc = () => {
  showSettings.value = false
  showToc.value = true
}

const openSettings = () => {
  showToc.value = false
  showSettings.value = !showSettings.value
}

// Jumping elsewhere (contents, slider) leaves the current reading thread:
// the sticker stays where it was instead of following to the new place
const detachSticker = () => {
  if (!activeBookmarkId.value) return
  activeBookmarkId.value = null
  addToast('Sticker kept in place - you jumped to another part')
}

const goToTocItem = (item) => {
  showToc.value = false
  detachSticker()
  reader.value?.goToHref(item.href)
}

const handleSliderInput = (e) => {
  sliderValue.value = Number(e.target.value)
}

const handleSliderChange = (e) => {
  const value = Number(e.target.value) / 1000
  sliderValue.value = null
  detachSticker()
  reader.value?.goToProgress(value)
}

const handleKey = (e) => {
  if (stickersMode.value) {
    if (e.key === 'Escape') {
      if (stickersMode.value === 'continue') continueFromLast()
      else stickersMode.value = null
    }
    return
  }
  if (captureMode.value) {
    if (e.key === 'Escape') captureMode.value = null
    return
  }
  if (e.key === 'Escape') {
    if (showSettings.value || showToc.value) {
      showSettings.value = false
      showToc.value = false
    } else {
      goBack()
    }
  } else if (ebook.value?.format === 'epub' && e.target === document.body) {
    if (e.key === 'ArrowRight' || e.key === 'PageDown') reader.value?.next()
    else if (e.key === 'ArrowLeft' || e.key === 'PageUp') reader.value?.prev()
  }
}

const goBack = () => {
  if (window.history.state?.back) router.back()
  else router.push('/ebooks')
}

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKey)
  document.removeEventListener('visibilitychange', handleVisibility)
  clearTimeout(chromeTimer)
  clearInterval(sessionTimer)
  savePosition()
  flushSession()
})
</script>

<template>
  <div class="ebook-reader fixed inset-0 z-[60] flex flex-col overflow-hidden" :style="{ background: theme.bg, color: theme.fg }">
    <!-- Error -->
    <div v-if="error" class="flex-1 flex flex-col items-center justify-center gap-4 p-6 text-center">
      <p class="text-sm">{{ error }}</p>
      <button class="px-4 py-2 rounded-xl bg-indigo-500 text-white text-sm font-bold" @click="router.push('/ebooks')">
        Back to e-books
      </button>
    </div>

    <!-- Downloading -->
    <div v-else-if="!fileData" class="flex-1 flex flex-col items-center justify-center gap-3 p-6">
      <div class="w-8 h-8 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
      <p class="text-sm" :style="{ color: theme.muted }">
        {{ downloadProgress != null ? `Downloading… ${downloadProgress}%` : 'Opening…' }}
      </p>
    </div>

    <template v-else>
      <!-- Reading surface -->
      <div class="flex-1 min-h-0 relative pt-[env(safe-area-inset-top)] pb-[env(safe-area-inset-bottom)]">
        <EpubReader
          v-if="ebook.format === 'epub'"
          ref="reader"
          :data="fileData"
          :ebook-id="ebook.id"
          :initial-position="ebook.position"
          :settings="settings"
          class="py-10"
          @ready="handleReady"
          @relocated="handleRelocated"
          @tap="handleTap"
          @selection="handleSelection"
          @error="handleReaderError"
        />
        <PdfReader
          v-else
          ref="reader"
          :data="fileData"
          :initial-position="ebook.position"
          :settings="settings"
          :language="ebook.language"
          @ready="handleReady"
          @relocated="handleRelocated"
          @tap="handleTap"
          @selection="handleSelection"
          @error="handleReaderError"
        />

        <!-- Desktop page-turn buttons (EPUB paginated) -->
        <template v-if="ebook.format === 'epub' && settings.epubFlow === 'paginated' && ready">
          <button
            class="hidden lg:flex absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full items-center justify-center opacity-30 hover:opacity-100 transition-opacity"
            :style="{ background: `${theme.muted}33` }"
            @click="reader?.prev()"
          >
            <ChevronLeft :size="20" />
          </button>
          <button
            class="hidden lg:flex absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full items-center justify-center opacity-30 hover:opacity-100 transition-opacity"
            :style="{ background: `${theme.muted}33` }"
            @click="reader?.next()"
          >
            <ChevronRight :size="20" />
          </button>
        </template>

        <!-- Minimal progress when chrome is hidden -->
        <div
          v-if="!showChrome && ready"
          class="absolute bottom-[max(0.5rem,env(safe-area-inset-bottom))] inset-x-0 text-center text-[11px] pointer-events-none tabular-nums"
          :style="{ color: theme.muted }"
        >
          {{ progressPercent != null ? `${progressPercent}%` : location.label }}
        </div>
      </div>

      <!-- Top bar -->
      <Transition name="reader-bar-top">
        <header
          v-if="showChrome"
          class="absolute top-0 inset-x-0 z-10 border-b backdrop-blur-xl pt-[env(safe-area-inset-top)]"
          :style="{ background: `${theme.bg}f2`, borderColor: `${theme.muted}33` }"
        >
          <div class="flex items-center gap-2 px-2 sm:px-4 h-14">
            <button class="p-2.5 rounded-xl hover:opacity-70" @click="goBack">
              <ArrowLeft :size="20" />
            </button>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold truncate">{{ ebook.title }}</p>
              <p class="text-[11px] truncate" :style="{ color: theme.muted }">{{ ebook.author }}</p>
            </div>
            <button class="relative p-2.5 rounded-xl hover:opacity-70" title="Stickers" @click="openStickers">
              <StickyNote :size="20" />
              <span
                v-if="bookmarks.length"
                class="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-amber-500 text-[10px] font-black text-black flex items-center justify-center"
              >{{ bookmarks.length }}</span>
            </button>
            <button v-if="ebook.format === 'epub' && toc.length" class="p-2.5 rounded-xl hover:opacity-70" title="Contents" @click="openToc">
              <ListTree :size="20" />
            </button>
            <button
              class="p-2.5 rounded-xl transition-colors"
              :class="showSettings ? 'bg-indigo-500 text-white' : 'hover:opacity-70'"
              title="Reading settings"
              @click="openSettings"
            >
              <ALargeSmall :size="20" />
            </button>
          </div>
        </header>
      </Transition>

      <!-- Bottom bar -->
      <Transition name="reader-bar-bottom">
        <footer
          v-if="showChrome && !showSettings"
          class="absolute bottom-0 inset-x-0 z-10 border-t backdrop-blur-xl pb-[env(safe-area-inset-bottom)]"
          :style="{ background: `${theme.bg}f2`, borderColor: `${theme.muted}33` }"
        >
          <div class="px-4 sm:px-6 py-3 max-w-3xl mx-auto">
            <div class="flex items-center justify-between text-[11px] mb-2 gap-3" :style="{ color: theme.muted }">
              <span class="truncate">
                <span v-if="activeBookmark" class="inline-flex items-center gap-1 mr-1.5 px-1.5 py-0.5 rounded-md bg-amber-500/15 text-amber-400 font-bold">
                  <StickyNote :size="10" /> {{ activeBookmark.label }}
                </span>{{ location.label || ' ' }}
              </span>
              <span class="shrink-0 tabular-nums">
                {{ sliderValue != null ? `${Math.round(sliderValue / 10)}%` : progressPercent != null ? `${progressPercent}%` : '' }}
                <template v-if="sliderValue == null && printPage"> · p. {{ printPage }}/{{ ebook.total_pages }}</template>
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1000"
              :value="sliderValue ?? Math.round((location.progress || 0) * 1000)"
              :disabled="location.progress == null"
              class="reader-slider w-full accent-indigo-500"
              @input="handleSliderInput"
              @change="handleSliderChange"
            />
          </div>
        </footer>
      </Transition>

      <!-- Settings sheet -->
      <Transition name="reader-sheet">
        <div v-if="showSettings" class="absolute inset-x-0 bottom-0 z-20 sm:bottom-auto sm:top-16 sm:right-4 sm:left-auto sm:w-96">
          <ReaderSettingsPanel :format="ebook.format" :pdf-has-text="pdfHasText" class="pb-[max(1rem,env(safe-area-inset-bottom))] sm:pb-5" />
        </div>
      </Transition>

      <!-- Selected text actions -->
      <Transition name="reader-sheet">
        <div
          v-if="selection && !captureMode"
          class="absolute inset-x-0 bottom-0 z-40 flex justify-center px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pointer-events-none"
        >
          <div
            class="pointer-events-auto flex items-center gap-1 p-1.5 rounded-2xl border shadow-2xl"
            :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
          >
            <button class="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-sm font-bold hover:bg-indigo-500/15" @mousedown.prevent @click="openCapture('quote')">
              <Quote :size="16" class="text-indigo-400" /> Quote
            </button>
            <button class="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-sm font-bold hover:bg-amber-500/15" @mousedown.prevent @click="openCapture('word')">
              <Brain :size="16" class="text-amber-400" /> Word
            </button>
            <button class="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-sm font-bold hover:bg-sky-500/15" @mousedown.prevent @click="openCapture('note')">
              <NotebookPen :size="16" class="text-sky-400" /> Note
            </button>
          </div>
        </div>
      </Transition>

      <Transition name="reader-sheet">
        <div v-if="captureMode" class="absolute inset-0 z-50 flex items-end sm:items-center justify-center bg-black/30" @click="captureMode = null">
          <CaptureSheet
            :mode="captureMode"
            :selection="captureSelection"
            :ebook="ebook"
            :page-number="capturePage"
            :chapter="captureSelection?.chapter ?? (ebook.format === 'epub' ? location.label : '')"
            :theme="theme"
            class="w-full sm:w-[30rem]"
            @close="captureMode = null"
            @saved="handleCaptured"
            @ebook-updated="mergeEbook"
          />
        </div>
      </Transition>

      <!-- Stickers: manage, or choose where to continue on open -->
      <Transition name="reader-sheet">
        <div v-if="stickersMode" class="absolute inset-0 z-50 flex items-end sm:items-center justify-center bg-black/30" @click="stickersMode === 'continue' ? continueFromLast() : (stickersMode = null)">
          <StickersSheet
            :key="stickersMode"
            :mode="stickersMode"
            :bookmarks="bookmarks"
            :active-id="activeBookmarkId"
            :current-label="location.label"
            :last-progress="location.progress"
            :total-pages="ebook.total_pages"
            :format="ebook.format"
            :theme="theme"
            :busy="stickersBusy"
            class="w-full sm:w-[30rem]"
            @close="stickersMode === 'continue' ? continueFromLast() : (stickersMode = null)"
            @go="goToSticker"
            @add="addSticker"
            @rename="renameSticker"
            @delete="deleteSticker"
            @unfollow="activeBookmarkId = null"
            @continue-last="continueFromLast"
          />
        </div>
      </Transition>

      <!-- Track progress? (asked once per e-book) -->
      <Transition name="reader-sheet">
        <div v-if="showTrackPrompt" class="absolute inset-x-0 bottom-0 z-40 sm:inset-auto sm:bottom-6 sm:left-1/2 sm:-translate-x-1/2 sm:w-[28rem]">
          <div
            class="rounded-t-2xl sm:rounded-2xl border shadow-2xl p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:pb-5 space-y-4"
            :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
          >
            <div class="flex items-start gap-3">
              <div class="w-10 h-10 shrink-0 rounded-xl bg-indigo-500/15 text-indigo-400 flex items-center justify-center">
                <Library :size="20" />
              </div>
              <div>
                <p class="font-bold">Track your progress?</p>
                <p class="text-sm mt-1" :style="{ color: theme.muted }">
                  <template v-if="ebook.book_detail">
                    Your reading will update <strong>{{ ebook.book_detail.title }}</strong> in your library, and reading time will count toward your stats.
                  </template>
                  <template v-else>
                    We'll add this book to your library as Currently Reading and keep its progress up to date as you read.
                  </template>
                </p>
              </div>
            </div>
            <div v-if="askForPages">
              <label class="text-[11px] font-bold uppercase tracking-wider" :style="{ color: theme.muted }">Pages in the print edition (optional)</label>
              <input
                v-model="trackPages"
                type="number"
                min="1"
                inputmode="numeric"
                placeholder="e.g. 320"
                class="mt-1.5 w-full rounded-xl px-3 py-2 text-sm outline-none border focus:border-indigo-500"
                :style="{ background: `${theme.muted}1a`, borderColor: `${theme.muted}40`, color: theme.fg }"
              />
              <p class="text-[11px] mt-1" :style="{ color: theme.muted }">E-books have no fixed pages - this lets us show your progress as page numbers.</p>
            </div>
            <div class="flex gap-2">
              <button class="flex-1 py-2.5 rounded-xl text-sm font-bold border" :style="{ borderColor: `${theme.muted}40` }" :disabled="trackBusy" @click="answerTracking(false)">
                Not now
              </button>
              <button class="flex-1 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 text-white disabled:opacity-50" :disabled="trackBusy" @click="answerTracking(true)">
                Track progress
              </button>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Reached the end -->
      <Transition name="reader-sheet">
        <div v-if="showFinishPrompt" class="absolute inset-x-0 bottom-0 z-40 sm:inset-auto sm:bottom-6 sm:left-1/2 sm:-translate-x-1/2 sm:w-[28rem]">
          <div
            class="rounded-t-2xl sm:rounded-2xl border shadow-2xl p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sm:pb-5 space-y-4"
            :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
          >
            <template v-if="ebook.library_entry?.status === 'read'">
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 shrink-0 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center">
                  <PartyPopper :size="20" />
                </div>
                <div>
                  <p class="font-bold">Finished!</p>
                  <p class="text-sm mt-1" :style="{ color: theme.muted }">{{ ebook.book_detail?.title || ebook.title }} is now on your Read shelf.</p>
                </div>
              </div>
              <div class="flex gap-2">
                <button class="flex-1 py-2.5 rounded-xl text-sm font-bold border" :style="{ borderColor: `${theme.muted}40` }" @click="dismissFinish">Close</button>
                <button v-if="ebook.book_detail" class="flex-1 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 text-white" @click="writeReview">Write a review</button>
              </div>
            </template>
            <template v-else>
              <div class="flex items-start gap-3">
                <div class="w-10 h-10 shrink-0 rounded-xl bg-indigo-500/15 text-indigo-400 flex items-center justify-center">
                  <PartyPopper :size="20" />
                </div>
                <div>
                  <p class="font-bold">You've reached the end</p>
                  <p class="text-sm mt-1" :style="{ color: theme.muted }">Mark this book as read?</p>
                </div>
              </div>
              <div class="flex gap-2">
                <button class="flex-1 py-2.5 rounded-xl text-sm font-bold border" :style="{ borderColor: `${theme.muted}40` }" :disabled="trackBusy" @click="dismissFinish">Not yet</button>
                <button class="flex-1 py-2.5 rounded-xl text-sm font-bold bg-indigo-500 text-white disabled:opacity-50" :disabled="trackBusy" @click="finishBook">Mark as read</button>
              </div>
            </template>
          </div>
        </div>
      </Transition>

      <!-- Table of contents -->
      <Transition name="reader-sheet">
        <div v-if="showToc" class="absolute inset-0 z-30 flex" @click="showToc = false">
          <div class="absolute inset-0 bg-black/40" />
          <nav
            class="relative w-[85%] max-w-sm h-full overflow-y-auto shadow-2xl pt-[env(safe-area-inset-top)]"
            :style="{ background: theme.bg }"
            @click.stop
          >
            <div class="flex items-center justify-between px-4 h-14 border-b" :style="{ borderColor: `${theme.muted}33` }">
              <p class="text-sm font-bold">Contents</p>
              <button class="p-2 rounded-lg hover:opacity-70" @click="showToc = false"><X :size="18" /></button>
            </div>
            <ul class="py-2">
              <template v-for="item in toc" :key="item.id || item.href">
                <li>
                  <button class="w-full text-left px-4 py-3 text-sm hover:opacity-70" @click="goToTocItem(item)">
                    {{ item.label.trim() }}
                  </button>
                </li>
                <li v-for="sub in item.subitems || []" :key="sub.id || sub.href">
                  <button class="w-full text-left pl-8 pr-4 py-2.5 text-xs hover:opacity-70" :style="{ color: theme.muted }" @click="goToTocItem(sub)">
                    {{ sub.label.trim() }}
                  </button>
                </li>
              </template>
            </ul>
          </nav>
        </div>
      </Transition>
    </template>
  </div>
</template>

<style scoped>
.reader-bar-top-enter-active,
.reader-bar-top-leave-active,
.reader-bar-bottom-enter-active,
.reader-bar-bottom-leave-active,
.reader-sheet-enter-active,
.reader-sheet-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.reader-bar-top-enter-from,
.reader-bar-top-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
.reader-bar-bottom-enter-from,
.reader-bar-bottom-leave-to,
.reader-sheet-enter-from,
.reader-sheet-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
.reader-slider {
  height: 4px;
}
</style>
