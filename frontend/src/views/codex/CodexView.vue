<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  getJournalEntries,
  saveJournalEntry,
  deleteJournalEntry,
  getTrashEntries,
  restoreJournalEntry,
  exportJournal,
  getManuscripts,
  getManuscript,
  saveManuscript,
  createManuscript,
  deleteManuscript,
  getTrashManuscripts,
  restoreManuscript,
  exportManuscript,
  toggleManuscriptShare,
  addChapter,
  saveChapter
} from '@/services/codexService'
import { downloadBlob } from '@/utils/downloadFile'
import {
  PenTool,
  Feather,
  Plus,
  Maximize2,
  Minimize2,
  Clock,
  Save,
  Trash2,
  History,
  FileText,
  X,
  ArrowLeft,
  RotateCcw,
  Download,
  Share2,
  Link,
  Check,
  Printer
} from 'lucide-vue-next'

// State
const activeTab = ref('journal') // 'journal' | 'manuscript'
const entries = ref([])
const manuscripts = ref([])
const loading = ref(false)
const saving = ref(false)

const selectedEntry = ref(null)
const selectedManuscript = ref(null)
const activeChapterIndex = ref(0)

const isFocusMode = ref(false)

// Trash state
const showTrash = ref(false)
const trashEntries = ref([])
const trashManuscripts = ref([])

// Auto-save
const saveStatus = ref('saved') // 'saved' | 'saving' | 'unsaved'
let autoSaveTimer = null

// Share
const shareLink = ref('')
const showShareCopied = ref(false)

// Mobile state
const mobileView = ref('list') // 'list' | 'editor'

// New manuscript form
const showNewManuscriptForm = ref(false)
const newManuscriptTitle = ref('')
const newManuscriptGenre = ref('Fiction')

// Mood types and colors
const moods = ['contemplative', 'inspired', 'melancholic', 'energetic', 'serene']
const moodColors = {
  contemplative: 'bg-indigo-500',
  inspired: 'bg-amber-500',
  melancholic: 'bg-slate-500',
  energetic: 'bg-rose-500',
  serene: 'bg-emerald-500'
}

// Load data on mount
onMounted(async () => {
  loading.value = true
  try {
    entries.value = await getJournalEntries()
    manuscripts.value = await getManuscripts()
  } catch (error) {
    // Codex data load failed
  } finally {
    loading.value = false
  }
})

// Computed
const currentChapter = computed(() => {
  if (!selectedManuscript.value?.chapters) return null
  return selectedManuscript.value.chapters[activeChapterIndex.value]
})

const wordCount = computed(() => {
  if (selectedEntry.value) {
    return selectedEntry.value.content?.split(/\s+/).filter(Boolean).length || 0
  }
  if (currentChapter.value) {
    return currentChapter.value.content?.split(/\s+/).filter(Boolean).length || 0
  }
  return 0
})

// Methods
const handleNewEntry = async () => {
  try {
    const entry = await saveJournalEntry({
      title: 'New Reflection',
      content: '',
      mood: 'contemplative'
    })
    entries.value = await getJournalEntries()
    selectedEntry.value = entry
    selectedManuscript.value = null
  } catch (error) {
    // Entry creation failed
  }
}

const handleSaveEntry = async () => {
  if (!selectedEntry.value) return
  saving.value = true
  try {
    const saved = await saveJournalEntry(selectedEntry.value)
    selectedEntry.value = saved
    entries.value = await getJournalEntries()
  } catch (error) {
    // Entry save failed
  } finally {
    saving.value = false
  }
}

const handleDeleteEntry = async () => {
  if (!selectedEntry.value || !confirm('Delete this reflection?')) return
  try {
    await deleteJournalEntry(selectedEntry.value.id)
    entries.value = await getJournalEntries()
    selectedEntry.value = entries.value[0] || null
    mobileView.value = 'list'
  } catch (error) {
    // Entry deletion failed
  }
}

const openNewManuscriptForm = () => {
  showNewManuscriptForm.value = true
  newManuscriptTitle.value = ''
  newManuscriptGenre.value = 'Fiction'
}

const handleNewManuscript = async () => {
  if (!newManuscriptTitle.value.trim()) return
  try {
    const manuscript = await createManuscript({
      title: newManuscriptTitle.value.trim(),
      genre: newManuscriptGenre.value
    })
    manuscripts.value = await getManuscripts()
    // Fetch detail to get chapters (create response doesn't include them)
    selectedManuscript.value = await getManuscript(manuscript.id)
    selectedEntry.value = null
    activeChapterIndex.value = 0
    showNewManuscriptForm.value = false
  } catch (error) {
    // Manuscript creation failed
  }
}

const handleDeleteManuscript = async () => {
  if (!selectedManuscript.value || !confirm(`Delete "${selectedManuscript.value.title}" and all its chapters?`)) return
  try {
    await deleteManuscript(selectedManuscript.value.id)
    manuscripts.value = await getManuscripts()
    selectedManuscript.value = null
    mobileView.value = 'list'
  } catch (error) {
    // Manuscript deletion failed
  }
}

const handleAddChapter = async () => {
  if (!selectedManuscript.value) return
  try {
    await addChapter(selectedManuscript.value.id)
    // Refresh manuscript detail to get updated chapters
    selectedManuscript.value = await getManuscript(selectedManuscript.value.id)
    manuscripts.value = await getManuscripts()
    activeChapterIndex.value = selectedManuscript.value.chapters.length - 1
  } catch (error) {
    // Chapter add failed
  }
}

const handleSaveManuscript = async () => {
  if (!selectedManuscript.value) return
  saving.value = true
  try {
    // Save manuscript metadata
    await saveManuscript(selectedManuscript.value)

    // Save current chapter content
    if (currentChapter.value) {
      await saveChapter(currentChapter.value)
    }

    // Refresh
    selectedManuscript.value = await getManuscript(selectedManuscript.value.id)
    manuscripts.value = await getManuscripts()
  } catch (error) {
    // Manuscript save failed
  } finally {
    saving.value = false
  }
}

const selectEntry = (entry) => {
  selectedEntry.value = { ...entry }
  selectedManuscript.value = null
}

const selectManuscript = async (manuscript) => {
  try {
    selectedManuscript.value = await getManuscript(manuscript.id)
    selectedEntry.value = null
    activeChapterIndex.value = 0
  } catch (error) {
    // Manuscript load failed
  }
}

// Mobile navigation
const mobileSelectEntry = (entry) => {
  selectEntry(entry)
  mobileView.value = 'editor'
}

const mobileSelectManuscript = async (manuscript) => {
  await selectManuscript(manuscript)
  mobileView.value = 'editor'
}

const mobileNewEntry = async () => {
  await handleNewEntry()
  mobileView.value = 'editor'
}

const mobileNewManuscript = async () => {
  await handleNewManuscript()
  if (selectedManuscript.value) {
    mobileView.value = 'editor'
  }
}

const closeMobileEditor = () => {
  mobileView.value = 'list'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

// ============ TRASH ============

const loadTrash = async () => {
  try {
    trashEntries.value = await getTrashEntries()
    trashManuscripts.value = await getTrashManuscripts()
  } catch (error) {
    // Trash load failed
  }
}

const handleRestoreEntry = async (entryId) => {
  try {
    await restoreJournalEntry(entryId)
    entries.value = await getJournalEntries()
    await loadTrash()
  } catch (error) {
    // Entry restore failed
  }
}

const handleRestoreManuscript = async (msId) => {
  try {
    await restoreManuscript(msId)
    manuscripts.value = await getManuscripts()
    await loadTrash()
  } catch (error) {
    // Manuscript restore failed
  }
}

const toggleTrash = async () => {
  showTrash.value = !showTrash.value
  if (showTrash.value) await loadTrash()
}

// ============ EXPORT ============

const handleExportJournal = async () => {
  try {
    const response = await exportJournal()
    downloadBlob(response, 'journal_entries.json')
  } catch (error) {
    // Journal export failed
  }
}

const handleExportManuscript = (format = 'txt') => {
  if (!selectedManuscript.value) return
  const ms = selectedManuscript.value
  // Open printable HTML in new window
  const printWindow = window.open('', '_blank')
  const chaptersHtml = (ms.chapters || []).map((ch, idx) => `
    <div style="${idx > 0 ? 'page-break-before: always;' : ''}">
      <h2 style="font-size: 18pt; margin-bottom: 24px;">${ch.title || `Chapter ${idx + 1}`}</h2>
      <div style="white-space: pre-wrap; word-wrap: break-word;">${(ch.content || '').replace(/</g, '&lt;').replace(/>/g, '&gt;')}</div>
    </div>
  `).join('')

  printWindow.document.write(`<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>${ms.title}</title>
<style>
@page { margin: 25mm; }
body { font-family: 'Georgia', 'Times New Roman', serif; font-size: 12pt; line-height: 1.8; color: #1a1a1a; margin: 40px; }
.title-page { text-align: center; padding-top: 30vh; page-break-after: always; }
.title-page h1 { font-size: 28pt; margin-bottom: 8px; }
.title-page .subtitle { font-size: 16pt; color: #666; font-style: italic; }
.title-page .genre { font-size: 10pt; color: #999; margin-top: 24px; text-transform: uppercase; letter-spacing: 2px; }
.title-page .word-count { font-size: 9pt; color: #aaa; margin-top: 8px; }
</style></head><body>
<div class="title-page">
  <h1>${ms.title}</h1>
  ${ms.subtitle ? `<div class="subtitle">${ms.subtitle}</div>` : ''}
  <div class="genre">${ms.genre}</div>
  <div class="word-count">${(ms.currentWordCount || 0).toLocaleString()} words</div>
</div>
${chaptersHtml}
</body></html>`)
  printWindow.document.close()
  printWindow.print()
}

// ============ SHARE ============

const handleToggleShare = async () => {
  if (!selectedManuscript.value) return
  try {
    const updated = await toggleManuscriptShare(selectedManuscript.value.id)
    selectedManuscript.value = updated
    manuscripts.value = await getManuscripts()
    if (updated.isShared && updated.shareToken) {
      shareLink.value = `${window.location.origin}/manuscripts/shared/${updated.shareToken}`
    } else {
      shareLink.value = ''
    }
  } catch (error) {
    // Share toggle failed
  }
}

const copyShareLink = () => {
  if (!shareLink.value) return
  navigator.clipboard.writeText(shareLink.value)
  showShareCopied.value = true
  setTimeout(() => { showShareCopied.value = false }, 2000)
}

// ============ AUTO-SAVE ============

const triggerAutoSave = () => {
  saveStatus.value = 'unsaved'
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
  autoSaveTimer = setTimeout(async () => {
    saveStatus.value = 'saving'
    try {
      if (selectedManuscript.value) {
        await handleSaveManuscript()
      }
      saveStatus.value = 'saved'
    } catch {
      saveStatus.value = 'unsaved'
    }
  }, 3000)
}

// Watch chapter content changes for auto-save
watch(
  () => currentChapter.value?.content,
  (newVal, oldVal) => {
    if (oldVal !== undefined && newVal !== oldVal && selectedManuscript.value) {
      triggerAutoSave()
    }
  }
)

watch(
  () => currentChapter.value?.title,
  (newVal, oldVal) => {
    if (oldVal !== undefined && newVal !== oldVal && selectedManuscript.value) {
      triggerAutoSave()
    }
  }
)

onUnmounted(() => {
  if (autoSaveTimer) clearTimeout(autoSaveTimer)
})
</script>

<template>
  <div class="h-full bg-ink">

    <!-- ==================== DESKTOP LAYOUT ==================== -->
    <div :class="['hidden lg:flex h-full transition-all duration-1000', isFocusMode ? 'p-0' : '']">

      <!-- 1. CODEX NAVIGATION (Left Sidebar) -->
      <aside
        v-if="!isFocusMode"
        class="w-72 border-r border-white/5 flex flex-col glass backdrop-blur-3xl z-40 flex-shrink-0"
      >
        <div class="p-5 border-b border-white/5">
          <div class="flex items-center gap-2 mb-5">
            <div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
              <PenTool :size="16" class="text-indigo-400" />
            </div>
            <h2 class="text-base font-black text-white uppercase tracking-tighter">The Codex</h2>
          </div>

          <!-- Tab Switcher -->
          <div class="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
            <button
              @click="activeTab = 'journal'"
              :class="[
                'flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                activeTab === 'journal' ? 'bg-indigo-500 text-white' : 'text-slate-500 hover:text-white'
              ]"
            >
              Journal
            </button>
            <button
              @click="activeTab = 'manuscript'"
              :class="[
                'flex-1 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                activeTab === 'manuscript' ? 'bg-indigo-500 text-white' : 'text-slate-500 hover:text-white'
              ]"
            >
              Studio
            </button>
          </div>
        </div>

        <!-- Entry/Manuscript List -->
        <div class="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
          <!-- Journal Tab -->
          <template v-if="activeTab === 'journal'">
            <div class="flex items-center gap-2 mb-4">
              <button
                @click="handleNewEntry"
                class="flex-1 py-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2"
              >
                <Plus :size="16" /> New Reflection
              </button>
              <button
                @click="handleExportJournal"
                class="p-3 rounded-2xl bg-white/5 border border-white/5 text-slate-500 hover:text-emerald-400 hover:border-emerald-500/20 transition-all"
                title="Export journal"
              >
                <Download :size="14" />
              </button>
              <button
                @click="toggleTrash"
                :class="['p-3 rounded-2xl border transition-all', showTrash ? 'bg-rose-500/10 border-rose-500/20 text-rose-400' : 'bg-white/5 border-white/5 text-slate-500 hover:text-rose-400']"
                title="Trash"
              >
                <Trash2 :size="14" />
              </button>
            </div>

            <!-- Trash Section -->
            <div v-if="showTrash" class="mb-4 p-3 rounded-2xl bg-rose-500/5 border border-rose-500/10 space-y-2">
              <p class="text-[10px] font-black text-rose-400 uppercase tracking-widest">Trash</p>
              <div v-if="trashEntries.length === 0 && trashManuscripts.length === 0" class="text-[10px] text-slate-600 italic">Nothing in trash</div>
              <div v-for="entry in trashEntries" :key="'t-' + entry.id" class="flex items-center justify-between p-2 rounded-xl bg-white/5">
                <div class="min-w-0">
                  <p class="text-xs font-bold text-slate-400 truncate">{{ entry.title }}</p>
                  <p class="text-[9px] text-slate-600">{{ formatDate(entry.deletedAt) }}</p>
                </div>
                <button @click="handleRestoreEntry(entry.id)" class="p-1.5 rounded-lg text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all" title="Restore">
                  <RotateCcw :size="12" />
                </button>
              </div>
              <div v-for="ms in trashManuscripts" :key="'tm-' + ms.id" class="flex items-center justify-between p-2 rounded-xl bg-white/5">
                <div class="min-w-0">
                  <p class="text-xs font-bold text-slate-400 truncate">{{ ms.title }}</p>
                  <p class="text-[9px] text-slate-600">Manuscript &middot; {{ formatDate(ms.deletedAt) }}</p>
                </div>
                <button @click="handleRestoreManuscript(ms.id)" class="p-1.5 rounded-lg text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all" title="Restore">
                  <RotateCcw :size="12" />
                </button>
              </div>
            </div>

            <button
              v-for="entry in entries"
              :key="entry.id"
              @click="selectEntry(entry)"
              :class="[
                'w-full text-left p-4 rounded-2xl border transition-all relative overflow-hidden group',
                selectedEntry?.id === entry.id
                  ? 'bg-indigo-500/10 border-indigo-500/30'
                  : 'bg-white/5 border-white/5 hover:bg-white/10'
              ]"
            >
              <div class="flex items-center justify-between mb-2">
                <span class="text-[10px] font-bold text-slate-500">{{ formatDate(entry.date) }}</span>
                <!-- MoodOrb -->
                <div
                  :class="['w-2 h-2 rounded-full shadow-[0_0_15px_rgba(255,255,255,0.2)] animate-pulse', moodColors[entry.mood]]"
                />
              </div>
              <h4 class="text-sm font-bold text-white truncate group-hover:text-indigo-400 transition-colors">
                {{ entry.title }}
              </h4>
              <p class="text-[10px] text-slate-500 line-clamp-1 mt-1 italic">
                {{ entry.content.substring(0, 40) }}...
              </p>
            </button>
          </template>

          <!-- Manuscript Tab -->
          <template v-else>
            <!-- New Manuscript Button / Form -->
            <div v-if="showNewManuscriptForm" class="p-4 rounded-2xl bg-white/5 border border-indigo-500/20 space-y-3 mb-4">
              <div class="flex items-center justify-between">
                <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">New Manuscript</span>
                <button @click="showNewManuscriptForm = false" class="text-slate-500 hover:text-white">
                  <X :size="14" />
                </button>
              </div>
              <input
                v-model="newManuscriptTitle"
                placeholder="Title..."
                class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-indigo-500/50"
                @keyup.enter="handleNewManuscript"
                autofocus
              />
              <input
                v-model="newManuscriptGenre"
                placeholder="Genre (e.g. Fiction, Poetry...)"
                class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-600 outline-none focus:border-indigo-500/50"
                @keyup.enter="handleNewManuscript"
              />
              <button
                @click="handleNewManuscript"
                :disabled="!newManuscriptTitle.trim()"
                class="w-full py-2 rounded-xl bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest hover:bg-indigo-400 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                Create
              </button>
            </div>
            <button
              v-else
              @click="openNewManuscriptForm"
              class="w-full py-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2 mb-4"
            >
              <Plus :size="16" /> New Manuscript
            </button>

            <div v-for="ms in manuscripts" :key="ms.id" class="space-y-4">
              <div class="relative group/ms">
                <button
                  @click="selectManuscript(ms)"
                  :class="[
                    'w-full text-left p-5 rounded-2xl border transition-all',
                    selectedManuscript?.id === ms.id
                      ? 'bg-indigo-500/10 border-indigo-500/30'
                      : 'bg-white/5 border-white/5 hover:bg-white/10'
                  ]"
                >
                  <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{{ ms.genre }}</p>
                  <h4 class="text-sm font-black text-white mb-2">{{ ms.title }}</h4>
                  <div class="flex items-center justify-between text-[10px] font-bold text-slate-500">
                    <span>{{ ms.targetWordCount ? Math.round((ms.currentWordCount / ms.targetWordCount) * 100) : 0 }}%</span>
                    <span>{{ (ms.currentWordCount || 0).toLocaleString() }} words</span>
                  </div>
                </button>
                <!-- Delete manuscript button -->
                <button
                  @click.stop="selectedManuscript?.id === ms.id && handleDeleteManuscript()"
                  v-if="selectedManuscript?.id === ms.id"
                  class="absolute top-2 right-2 p-1.5 rounded-lg text-slate-600 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
                  title="Delete manuscript"
                >
                  <Trash2 :size="12" />
                </button>
              </div>

              <!-- Chapter Navigator -->
              <div
                v-if="selectedManuscript?.id === ms.id"
                class="pl-4 space-y-2 border-l border-white/5 ml-2 mt-4"
              >
                <button
                  v-for="(ch, idx) in selectedManuscript.chapters"
                  :key="ch.id"
                  @click="activeChapterIndex = idx"
                  :class="[
                    'w-full text-left px-4 py-2 rounded-xl text-xs font-bold transition-all',
                    activeChapterIndex === idx
                      ? 'text-indigo-400 bg-white/5'
                      : 'text-slate-500 hover:text-slate-300'
                  ]"
                >
                  {{ idx + 1 }}. {{ ch.title }}
                </button>
                <button
                  @click="handleAddChapter"
                  class="w-full text-left px-4 py-2 rounded-xl text-[10px] font-black text-slate-600 uppercase hover:text-indigo-400 flex items-center gap-2"
                >
                  <Plus :size="12" /> Add Chapter
                </button>
              </div>
            </div>
          </template>
        </div>
      </aside>

      <!-- 2. WRITING SURFACE (Center) -->
      <main class="flex-1 flex flex-col relative overflow-hidden">

        <!-- Toolbar -->
        <header
          v-if="!isFocusMode"
          class="p-5 border-b border-white/5 glass backdrop-blur-2xl flex items-center justify-between z-10"
        >
          <div class="flex items-center gap-6">
            <div>
              <template v-if="selectedManuscript">
                <input
                  v-model="selectedManuscript.title"
                  class="bg-transparent border-none text-xl font-black text-white tracking-tighter outline-none w-full placeholder-slate-800"
                  placeholder="Manuscript Title..."
                />
                <div class="flex items-center gap-1.5 mt-1">
                  <input
                    v-model="selectedManuscript.genre"
                    :size="selectedManuscript.genre?.length || 5"
                    class="bg-transparent border-none text-[10px] font-black text-indigo-400 uppercase tracking-widest outline-none placeholder-slate-700"
                    placeholder="Genre..."
                  />
                  <span class="text-[10px] font-black text-slate-600">·</span>
                  <span class="text-[10px] font-black text-slate-500 uppercase tracking-widest">
                    Chapter {{ activeChapterIndex + 1 }}
                  </span>
                </div>
              </template>
              <template v-else>
                <h3 class="text-xl font-black text-white tracking-tighter">
                  {{ selectedEntry ? 'Daily Reflection' : 'Codex Studio' }}
                </h3>
                <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">
                  {{ selectedEntry ? `Current Mood: ${selectedEntry.mood}` : 'Ready to write' }}
                </p>
              </template>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <!-- Auto-save indicator (manuscripts) -->
            <span v-if="selectedManuscript" :class="['text-[10px] font-bold uppercase tracking-widest transition-colors', saveStatus === 'saved' ? 'text-emerald-500' : saveStatus === 'saving' ? 'text-amber-400' : 'text-slate-500']">
              {{ saveStatus === 'saved' ? 'Saved' : saveStatus === 'saving' ? 'Saving...' : 'Unsaved' }}
            </span>

            <!-- Export (manuscript) -->
            <button
              v-if="selectedManuscript"
              @click="handleExportManuscript"
              class="p-3 rounded-2xl bg-white/5 text-slate-400 hover:text-emerald-400 transition-all"
              title="Print / Export"
            >
              <Printer :size="16" />
            </button>

            <!-- Share (manuscript) -->
            <div v-if="selectedManuscript" class="relative">
              <button
                @click="handleToggleShare"
                :class="['p-3 rounded-2xl transition-all', selectedManuscript.isShared ? 'bg-indigo-500/10 text-indigo-400' : 'bg-white/5 text-slate-400 hover:text-indigo-400']"
                :title="selectedManuscript.isShared ? 'Disable sharing' : 'Share manuscript'"
              >
                <Share2 :size="16" />
              </button>
              <!-- Share link popover -->
              <div v-if="selectedManuscript.isShared && shareLink" class="absolute top-full right-0 mt-2 p-3 rounded-xl bg-slate-800 border border-white/10 shadow-2xl z-50 min-w-[280px]">
                <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-2">Share Link</p>
                <div class="flex items-center gap-2">
                  <input :value="shareLink" readonly class="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-300 outline-none" />
                  <button @click="copyShareLink" class="p-2 rounded-lg bg-indigo-500/20 text-indigo-400 hover:bg-indigo-500/30 transition-all">
                    <Check v-if="showShareCopied" :size="14" />
                    <Link v-else :size="14" />
                  </button>
                </div>
              </div>
            </div>

            <button
              @click="isFocusMode = true"
              class="p-3 rounded-2xl bg-white/5 text-slate-400 hover:text-white transition-all flex items-center gap-2 text-[10px] font-black uppercase tracking-widest"
            >
              <Maximize2 :size="16" /> Focus
            </button>
            <button
              @click="selectedEntry ? handleSaveEntry() : handleSaveManuscript()"
              class="px-6 py-3 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-all flex items-center gap-2"
            >
              <Save :size="16" /> Save
            </button>
          </div>
        </header>

        <!-- EDITOR AREA -->
        <div
          :class="[
            'flex-1 overflow-y-auto custom-scrollbar relative p-6 lg:p-10 flex justify-center transition-all duration-1000',
            isFocusMode ? 'bg-[#010206]' : ''
          ]"
        >
          <!-- Exit Focus Mode Button -->
          <button
            v-if="isFocusMode"
            @click="isFocusMode = false"
            class="absolute top-10 right-10 p-4 rounded-full bg-white/5 text-slate-700 hover:text-white transition-all z-50 group"
          >
            <Minimize2 :size="24" />
            <span class="absolute top-full mt-2 left-1/2 -translate-x-1/2 text-[10px] font-black uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
              Exit Focus
            </span>
          </button>

          <div class="w-full max-w-4xl space-y-12">
            <!-- Journal Entry Editor -->
            <div v-if="selectedEntry" class="animate-in fade-in slide-in-from-bottom-10 duration-1000">
              <div class="flex items-center justify-between mb-8 gap-4 flex-wrap">
                <input
                  v-model="selectedEntry.title"
                  class="bg-transparent border-none text-3xl lg:text-4xl font-black text-white outline-none flex-1 min-w-0 tracking-tighter placeholder-slate-800"
                  placeholder="Reflection Title..."
                />
                <!-- Mood Selector -->
                <div class="flex gap-2 p-2 rounded-xl bg-white/5 border border-white/5 flex-shrink-0">
                  <button
                    v-for="m in moods"
                    :key="m"
                    @click="selectedEntry.mood = m"
                    :class="[
                      'w-5 h-5 rounded-full transition-all hover:scale-125',
                      selectedEntry.mood === m ? 'ring-2 ring-white ring-offset-2 ring-offset-ink' : 'opacity-40'
                    ]"
                    :title="m"
                  >
                    <div :class="['w-full h-full rounded-full', moodColors[m]]" />
                  </button>
                </div>
              </div>
              <textarea
                v-model="selectedEntry.content"
                class="w-full bg-transparent border-none outline-none text-2xl md:text-3xl font-serif italic text-slate-300 leading-relaxed placeholder-slate-900 min-h-[60vh] resize-none"
                placeholder="Breathe and let your thoughts flow onto the digital parchment..."
              />
            </div>

            <!-- Manuscript Chapter Editor -->
            <div v-else-if="selectedManuscript && currentChapter" class="animate-in fade-in slide-in-from-bottom-10 duration-1000">
              <p class="text-indigo-500 font-black text-xs uppercase tracking-[0.3em] mb-3">
                Chapter {{ activeChapterIndex + 1 }}
              </p>
              <input
                v-model="currentChapter.title"
                class="bg-transparent border-none text-3xl lg:text-4xl font-black text-white outline-none w-full tracking-tighter mb-8"
                placeholder="Chapter Title"
              />
              <textarea
                v-model="currentChapter.content"
                class="w-full bg-transparent border-none outline-none text-xl text-slate-300 leading-[1.9] placeholder-slate-700 min-h-[60vh] resize-none font-serif overflow-hidden"
                placeholder="Continue the legacy..."
              />
            </div>

            <!-- Empty State -->
            <div v-else class="h-full flex flex-col items-center justify-center text-center py-40 opacity-30 animate-pulse">
              <Feather :size="80" class="text-slate-500 mb-8" />
              <h3 class="text-4xl font-black text-white uppercase tracking-[0.2em] mb-4">The Chamber of Silence</h3>
              <p class="max-w-md mx-auto text-slate-500 text-lg">
                Every great work begins with the first drop of ink. Select an entry or start a new creation.
              </p>
            </div>
          </div>
        </div>

        <!-- Writing Stats / Status Bar -->
        <footer
          v-if="!isFocusMode && (selectedEntry || selectedManuscript)"
          class="p-6 border-t border-white/5 glass backdrop-blur-3xl flex items-center justify-between px-10"
        >
          <div class="flex items-center gap-8">
            <div class="flex items-center gap-2">
              <FileText :size="14" class="text-slate-500" />
              <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                {{ wordCount }} words{{ selectedManuscript ? ' in chapter' : '' }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <Clock :size="14" class="text-slate-500" />
              <span v-if="selectedManuscript" :class="['text-[10px] font-bold uppercase tracking-widest', saveStatus === 'saved' ? 'text-emerald-500/60' : saveStatus === 'saving' ? 'text-amber-400/60' : 'text-slate-500']">
                {{ saveStatus === 'saved' ? 'All changes saved' : saveStatus === 'saving' ? 'Saving...' : 'Unsaved changes' }}
              </span>
              <span v-else class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                Last edited just now
              </span>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <button
              v-if="selectedEntry"
              @click="handleDeleteEntry"
              class="p-2 text-slate-600 hover:text-rose-500 transition-all"
              title="Delete reflection"
            >
              <Trash2 :size="18" />
            </button>
            <button
              v-if="selectedManuscript"
              @click="handleDeleteManuscript"
              class="p-2 text-slate-600 hover:text-rose-500 transition-all"
              title="Delete manuscript"
            >
              <Trash2 :size="18" />
            </button>
            <button class="p-2 text-slate-600 hover:text-white transition-all">
              <History :size="18" />
            </button>
          </div>
        </footer>
      </main>
    </div>

    <!-- ==================== MOBILE LAYOUT ==================== -->
    <div class="lg:hidden flex flex-col h-full">

      <!-- MOBILE: List View -->
      <template v-if="mobileView === 'list'">

        <!-- Mobile Header -->
        <header class="px-4 py-3 border-b border-white/5 bg-ink/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                <PenTool :size="16" class="text-indigo-400" />
              </div>
              <h1 class="text-lg font-black text-white tracking-tight">The Codex</h1>
            </div>
            <button
              @click="activeTab === 'journal' ? mobileNewEntry() : openNewManuscriptForm()"
              class="p-2.5 rounded-xl bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 active:scale-95 transition-transform"
            >
              <Plus :size="18" />
            </button>
          </div>

          <!-- Tab Switcher -->
          <div class="flex gap-1 p-1 bg-white/5 rounded-xl border border-white/5">
            <button
              @click="activeTab = 'journal'"
              :class="[
                'flex-1 py-2.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                activeTab === 'journal' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30' : 'text-slate-500'
              ]"
            >
              Journal
            </button>
            <button
              @click="activeTab = 'manuscript'"
              :class="[
                'flex-1 py-2.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all',
                activeTab === 'manuscript' ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30' : 'text-slate-500'
              ]"
            >
              Studio
            </button>
          </div>
        </header>

        <!-- Mobile List Content -->
        <div class="flex-1 overflow-y-auto">

          <!-- Loading -->
          <div v-if="loading" class="flex items-center justify-center py-16">
            <div class="w-8 h-8 rounded-full border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
          </div>

          <!-- Journal Entries -->
          <template v-else-if="activeTab === 'journal'">
            <div v-if="entries.length > 0" class="p-4 space-y-3">
              <button
                v-for="entry in entries"
                :key="entry.id"
                @click="mobileSelectEntry(entry)"
                class="w-full text-left p-4 rounded-2xl bg-ink-light border border-white/5 active:scale-[0.98] transition-all relative overflow-hidden"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="text-[10px] font-bold text-slate-500">{{ formatDate(entry.date) }}</span>
                  <div
                    :class="['w-2.5 h-2.5 rounded-full shadow-[0_0_12px_rgba(255,255,255,0.15)] animate-pulse', moodColors[entry.mood]]"
                  />
                </div>
                <h4 class="text-sm font-bold text-white truncate mb-1">
                  {{ entry.title }}
                </h4>
                <p class="text-[10px] text-slate-500 line-clamp-2 italic leading-relaxed">
                  {{ entry.content.substring(0, 80) }}{{ entry.content.length > 80 ? '...' : '' }}
                </p>
              </button>
            </div>

            <!-- Empty State -->
            <div v-else class="flex flex-col items-center justify-center py-20 px-6 text-center">
              <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                <Feather :size="28" class="text-slate-600" />
              </div>
              <p class="text-sm text-slate-500 mb-1 font-bold">No reflections yet</p>
              <p class="text-xs text-slate-600 mb-5">Start your first journal entry</p>
              <button
                @click="mobileNewEntry"
                class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold active:scale-95 transition-transform shadow-lg shadow-indigo-500/30"
              >
                New Reflection
              </button>
            </div>
          </template>

          <!-- Manuscripts -->
          <template v-else>
            <!-- New Manuscript Form (Mobile) -->
            <div v-if="showNewManuscriptForm" class="p-4">
              <div class="p-4 rounded-2xl bg-ink-light border border-indigo-500/20 space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">New Manuscript</span>
                  <button @click="showNewManuscriptForm = false" class="text-slate-500 p-1">
                    <X :size="16" />
                  </button>
                </div>
                <input
                  v-model="newManuscriptTitle"
                  placeholder="Title..."
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-indigo-500/50"
                  @keyup.enter="mobileNewManuscript"
                  autofocus
                />
                <input
                  v-model="newManuscriptGenre"
                  placeholder="Genre (e.g. Fiction, Poetry...)"
                  class="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-indigo-500/50"
                  @keyup.enter="mobileNewManuscript"
                />
                <button
                  @click="mobileNewManuscript"
                  :disabled="!newManuscriptTitle.trim()"
                  class="w-full py-3 rounded-xl bg-indigo-500 text-white text-[10px] font-black uppercase tracking-widest active:scale-[0.98] transition-all disabled:opacity-30 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/30"
                >
                  Create
                </button>
              </div>
            </div>

            <div v-if="manuscripts.length > 0" class="p-4 space-y-3">
              <button
                v-for="ms in manuscripts"
                :key="ms.id"
                @click="mobileSelectManuscript(ms)"
                class="w-full text-left p-5 rounded-2xl bg-ink-light border border-white/5 active:scale-[0.98] transition-all relative overflow-hidden"
              >
                <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest mb-1">{{ ms.genre }}</p>
                <h4 class="text-sm font-black text-white mb-3">{{ ms.title }}</h4>
                <!-- Progress bar -->
                <div class="w-full h-1 rounded-full bg-white/5 mb-2 overflow-hidden">
                  <div
                    class="h-full rounded-full bg-indigo-500/60 transition-all"
                    :style="{ width: `${ms.targetWordCount ? Math.min(100, Math.round((ms.currentWordCount / ms.targetWordCount) * 100)) : 0}%` }"
                  />
                </div>
                <div class="flex items-center justify-between text-[10px] font-bold text-slate-500">
                  <span>{{ ms.chapters?.length || 0 }} chapter{{ (ms.chapters?.length || 0) !== 1 ? 's' : '' }}</span>
                  <span>{{ (ms.currentWordCount || 0).toLocaleString() }} words</span>
                </div>
              </button>
            </div>

            <!-- Empty State -->
            <div v-else-if="!showNewManuscriptForm" class="flex flex-col items-center justify-center py-20 px-6 text-center">
              <div class="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                <PenTool :size="28" class="text-slate-600" />
              </div>
              <p class="text-sm text-slate-500 mb-1 font-bold">No manuscripts yet</p>
              <p class="text-xs text-slate-600 mb-5">Begin your first masterwork</p>
              <button
                @click="openNewManuscriptForm"
                class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold active:scale-95 transition-transform shadow-lg shadow-indigo-500/30"
              >
                New Manuscript
              </button>
            </div>
          </template>
        </div>
      </template>

      <!-- MOBILE: Journal Editor View -->
      <template v-if="mobileView === 'editor' && selectedEntry">

        <!-- Mobile Editor Header -->
        <header class="px-4 py-3 border-b border-white/5 bg-ink/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
          <div class="flex items-center gap-3">
            <button
              @click="closeMobileEditor"
              class="p-2 -ml-2 rounded-xl text-slate-400 active:scale-95 transition-all"
            >
              <ArrowLeft :size="22" />
            </button>
            <div class="flex-1 min-w-0">
              <input
                v-model="selectedEntry.title"
                class="bg-transparent border-none text-base font-black text-white tracking-tight outline-none w-full placeholder-slate-700"
                placeholder="Reflection Title..."
              />
            </div>
            <button
              @click="handleSaveEntry"
              :class="[
                'p-2.5 rounded-xl text-white transition-all active:scale-95 shadow-lg',
                saving ? 'bg-indigo-400 shadow-indigo-400/30' : 'bg-indigo-500 shadow-indigo-500/30'
              ]"
            >
              <Save :size="18" />
            </button>
          </div>

          <!-- Mood Selector -->
          <div class="flex items-center gap-3 mt-3 ml-8">
            <span class="text-[10px] font-bold text-slate-600 uppercase tracking-wider">Mood</span>
            <div class="flex gap-2.5">
              <button
                v-for="m in moods"
                :key="m"
                @click="selectedEntry.mood = m"
                :class="[
                  'w-6 h-6 rounded-full transition-all active:scale-110',
                  selectedEntry.mood === m ? 'ring-2 ring-white ring-offset-2 ring-offset-ink scale-110' : 'opacity-40'
                ]"
              >
                <div :class="['w-full h-full rounded-full', moodColors[m]]" />
              </button>
            </div>
          </div>
        </header>

        <!-- Mobile Entry Editor -->
        <div class="flex-1 overflow-y-auto p-5">
          <textarea
            v-model="selectedEntry.content"
            class="w-full bg-transparent border-none outline-none text-lg font-serif italic text-slate-300 leading-relaxed placeholder-slate-900 min-h-[60vh] resize-none"
            placeholder="Breathe and let your thoughts flow onto the digital parchment..."
          />
        </div>

        <!-- Mobile Entry Footer -->
        <footer class="px-5 py-3 border-t border-white/5 bg-ink/90 backdrop-blur-xl safe-area-bottom">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <FileText :size="13" class="text-slate-600" />
              <span class="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{{ wordCount }} words</span>
            </div>
            <button
              @click="handleDeleteEntry"
              class="p-2 text-slate-600 active:text-rose-400 transition-colors"
            >
              <Trash2 :size="16" />
            </button>
          </div>
        </footer>
      </template>

      <!-- MOBILE: Manuscript Editor View -->
      <template v-if="mobileView === 'editor' && selectedManuscript">

        <!-- Mobile Manuscript Header -->
        <header class="px-4 py-3 border-b border-white/5 bg-ink/90 backdrop-blur-xl sticky top-0 z-30 safe-area-top">
          <div class="flex items-center gap-3">
            <button
              @click="closeMobileEditor"
              class="p-2 -ml-2 rounded-xl text-slate-400 active:scale-95 transition-all"
            >
              <ArrowLeft :size="22" />
            </button>
            <div class="flex-1 min-w-0">
              <input
                v-model="selectedManuscript.title"
                class="bg-transparent border-none text-base font-black text-white tracking-tight outline-none w-full placeholder-slate-700"
                placeholder="Manuscript Title..."
              />
              <div class="flex items-center gap-1.5 mt-0.5">
                <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{{ selectedManuscript.genre }}</span>
                <span class="text-[10px] font-black text-slate-700">·</span>
                <span class="text-[10px] font-bold text-slate-600">Ch. {{ activeChapterIndex + 1 }}</span>
              </div>
            </div>
            <button
              @click="handleSaveManuscript"
              :class="[
                'p-2.5 rounded-xl text-white transition-all active:scale-95 shadow-lg',
                saving ? 'bg-indigo-400 shadow-indigo-400/30' : 'bg-indigo-500 shadow-indigo-500/30'
              ]"
            >
              <Save :size="18" />
            </button>
          </div>

          <!-- Chapter Horizontal Scroll -->
          <div class="flex gap-2 mt-3 overflow-x-auto pb-1 -mx-4 px-4 no-scrollbar">
            <button
              v-for="(ch, idx) in selectedManuscript.chapters"
              :key="ch.id"
              @click="activeChapterIndex = idx"
              :class="[
                'px-3.5 py-1.5 rounded-full text-[10px] font-bold whitespace-nowrap shrink-0 transition-all active:scale-95',
                activeChapterIndex === idx
                  ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30'
                  : 'bg-white/5 text-slate-500 border border-white/5'
              ]"
            >
              {{ idx + 1 }}. {{ ch.title || `Chapter ${idx + 1}` }}
            </button>
            <button
              @click="handleAddChapter"
              class="px-3 py-1.5 rounded-full bg-white/5 border border-white/5 text-slate-600 text-[10px] font-bold shrink-0 flex items-center gap-1 active:scale-95 transition-all"
            >
              <Plus :size="12" /> Add
            </button>
          </div>
        </header>

        <!-- Mobile Manuscript Editor -->
        <div v-if="currentChapter" class="flex-1 overflow-y-auto p-5">
          <input
            v-model="currentChapter.title"
            class="bg-transparent border-none text-xl font-black text-white outline-none w-full tracking-tighter mb-4 placeholder-slate-800"
            placeholder="Chapter Title"
          />
          <textarea
            v-model="currentChapter.content"
            class="w-full bg-transparent border-none outline-none text-base text-slate-300 leading-loose placeholder-slate-700 min-h-[60vh] resize-none font-serif"
            placeholder="Continue the legacy..."
          />
        </div>

        <!-- Mobile Manuscript Footer -->
        <footer class="px-5 py-3 border-t border-white/5 bg-ink/90 backdrop-blur-xl safe-area-bottom">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <FileText :size="13" class="text-slate-600" />
              <span class="text-[10px] font-bold text-slate-600 uppercase tracking-wider">{{ wordCount }} words in chapter</span>
            </div>
            <button
              @click="handleDeleteManuscript"
              class="p-2 text-slate-600 active:text-rose-400 transition-colors"
            >
              <Trash2 :size="16" />
            </button>
          </div>
        </footer>
      </template>

    </div>

  </div>
</template>

<style scoped>
.glass {
  background: rgba(2, 4, 10, 0.8);
  backdrop-filter: blur(20px);
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(99, 102, 241, 0.5);
}

/* Animation utilities */
.animate-in {
  animation: animate-in 0.5s ease-out;
}

.fade-in {
  --tw-enter-opacity: 0;
}

.slide-in-from-bottom-10 {
  --tw-enter-translate-y: 2.5rem;
}

@keyframes animate-in {
  from {
    opacity: var(--tw-enter-opacity, 1);
    transform: translateY(var(--tw-enter-translate-y, 0));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Hide scrollbar for chapter horizontal scroll */
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* Safe area support for notched phones */
.safe-area-top {
  padding-top: max(0.75rem, env(safe-area-inset-top));
}

.safe-area-bottom {
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}

/* Mobile touch feedback */
@media (max-width: 1023px) {
  button {
    -webkit-tap-highlight-color: transparent;
  }
}
</style>
