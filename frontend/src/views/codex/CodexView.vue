<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  getJournalEntries,
  saveJournalEntry,
  deleteJournalEntry,
  getManuscripts,
  getManuscript,
  saveManuscript,
  createManuscript,
  deleteManuscript,
  addChapter,
  saveChapter
} from '@/services/codexService'
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
  X
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
    console.error('Error loading codex data:', error)
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
    console.error('Error creating entry:', error)
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
    console.error('Error saving entry:', error)
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
  } catch (error) {
    console.error('Error deleting entry:', error)
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
    selectedManuscript.value = manuscript
    selectedEntry.value = null
    activeChapterIndex.value = 0
    showNewManuscriptForm.value = false
  } catch (error) {
    console.error('Error creating manuscript:', error)
  }
}

const handleDeleteManuscript = async () => {
  if (!selectedManuscript.value || !confirm(`Delete "${selectedManuscript.value.title}" and all its chapters?`)) return
  try {
    await deleteManuscript(selectedManuscript.value.id)
    manuscripts.value = await getManuscripts()
    selectedManuscript.value = null
  } catch (error) {
    console.error('Error deleting manuscript:', error)
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
    console.error('Error adding chapter:', error)
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
    console.error('Error saving manuscript:', error)
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
    console.error('Error loading manuscript:', error)
  }
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}
</script>

<template>
  <div :class="['h-full flex bg-[#02040a] transition-all duration-1000', isFocusMode ? 'p-0' : '']">

    <!-- 1. CODEX NAVIGATION (Left Sidebar) -->
    <aside
      v-if="!isFocusMode"
      class="w-64 border-r border-white/5 flex-col glass backdrop-blur-3xl z-40 hidden lg:flex flex-shrink-0"
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
          <button
            @click="handleNewEntry"
            class="w-full py-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2 mb-4"
          >
            <Plus :size="16" /> New Reflection
          </button>

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
                v-for="(ch, idx) in ms.chapters"
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

        <div class="flex items-center gap-4">
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
            <Save :size="16" /> Save Changes
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
                    selectedEntry.mood === m ? 'ring-2 ring-white ring-offset-2 ring-offset-[#02040a]' : 'opacity-40'
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
              class="w-full bg-transparent border-none outline-none text-2xl text-slate-300 leading-loose placeholder-slate-900 min-h-[70vh] resize-none font-serif"
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
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
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
</style>
