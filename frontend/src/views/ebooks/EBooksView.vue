<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Plus, Search, Tablet, Pencil, Trash2, Lock, Link2, RefreshCw, CheckCircle2, Library, Landmark, CloudOff } from 'lucide-vue-next'
import { ebooksAPI } from '@/services/api'
import { removeCachedEbook } from '@/utils/ebookCache'
import { kvGet, kvSet } from '@/utils/offlineStore'
import { isNetworkError } from '@/stores/offlineSyncStore'
import { getBookUrl } from '@/utils/bookUrl'
import { useToast } from '@/composables/useToast'
import EBookCover from '@/components/ebooks/EBookCover.vue'
import EBookFormDialog from '@/components/ebooks/EBookFormDialog.vue'
import PublicDomainCatalog from '@/components/ebooks/PublicDomainCatalog.vue'

const router = useRouter()
const route = useRoute()
const { addToast } = useToast()

// 'mine' | 'classics' - kept in the URL so the tab survives reloads and back navigation
const tab = computed({
  get: () => (route.query.tab === 'classics' ? 'classics' : 'mine'),
  set: (value) => router.replace({ query: { ...route.query, tab: value === 'classics' ? 'classics' : undefined } }),
})

const ebooks = ref([])
const loading = ref(true)
const usage = ref(null)
const searchQuery = ref('')

const dialogOpen = ref(false)
const editingEbook = ref(null)

const filtered = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return ebooks.value
  return ebooks.value.filter((e) => e.title.toLowerCase().includes(q) || e.author.toLowerCase().includes(q))
})

const usagePercent = computed(() =>
  usage.value ? Math.min(100, (usage.value.used_bytes / usage.value.quota_bytes) * 100) : 0
)

const formatSize = (bytes) => {
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  return `${Math.max(0.1, bytes / (1024 * 1024)).toFixed(1)} MB`
}

// With stickers the book is as far as its earliest sticker
const progressPercent = (ebook) => Math.round((ebook.overall_progress ?? ebook.progress ?? 0) * 100)

const loadUsage = async () => {
  try {
    usage.value = (await ebooksAPI.usage()).data
  } catch {
    // non-critical
  }
}

const offline = ref(false)

// Keep the device copy current (uploads, edits, deletes) so the list works offline
watch(ebooks, (list) => {
  if (!loading.value && !offline.value) kvSet('ebooks:list', list)
}, { deep: true })

const loadEbooks = async () => {
  loading.value = true
  try {
    const { data } = await ebooksAPI.list({ page_size: 200 })
    ebooks.value = data?.results || data || []
    offline.value = false
    kvSet('ebooks:list', ebooks.value)
  } catch (err) {
    // No connection: show the list saved on this device (opened books read offline)
    const cached = isNetworkError(err) ? await kvGet('ebooks:list') : null
    if (cached) {
      ebooks.value = cached
      offline.value = true
    } else {
      addToast('Could not load your e-books', 'error')
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadEbooks()
  loadUsage()
})

const openUpload = () => {
  editingEbook.value = null
  dialogOpen.value = true
}

const openEdit = (ebook) => {
  editingEbook.value = ebook
  dialogOpen.value = true
}

const handleSaved = (saved) => {
  const index = ebooks.value.findIndex((e) => e.id === saved.id)
  if (index >= 0) {
    ebooks.value.splice(index, 1, saved)
    addToast('E-book updated')
  } else {
    ebooks.value.unshift(saved)
    addToast('E-book added', 'success', { label: 'Read now', callback: () => openReader(saved) })
    loadUsage()
  }
}

const handleDelete = async (ebook) => {
  if (!confirm(`Delete "${ebook.title}"? The file will be removed permanently.`)) return
  try {
    await ebooksAPI.delete(ebook.id)
    ebooks.value = ebooks.value.filter((e) => e.id !== ebook.id)
    removeCachedEbook(ebook.id)
    try {
      localStorage.removeItem(`ebook_locations_${ebook.id}`)
    } catch {
      // ignore
    }
    loadUsage()
    addToast('E-book deleted')
  } catch {
    addToast('Could not delete the e-book', 'error')
  }
}

const openReader = (ebook) => router.push(`/ebooks/${ebook.id}/read`)

const handleImported = (ebook) => {
  ebooks.value.unshift(ebook)
  loadUsage()
  addToast(`"${ebook.title}" added to your e-books`, 'success', { label: 'Read now', callback: () => openReader(ebook) })
}
</script>

<template>
  <div class="animate-in fade-in duration-700 pb-20">
    <div class="max-w-7xl mx-auto px-4 lg:px-6 pt-6 lg:pt-12">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 lg:mb-10">
        <div>
          <div class="flex items-center gap-2 mb-2 lg:mb-4">
            <Tablet :size="14" class="text-indigo-400" />
            <span class="text-page-meta font-bold text-indigo-400 uppercase tracking-[0.2em]">Your digital shelf</span>
          </div>
          <h1 class="text-page-heading font-black text-white tracking-tight mb-2">E-books</h1>
          <p class="text-page-subtitle text-zinc-400 max-w-2xl flex items-center gap-1.5">
            <Lock :size="13" class="shrink-0 text-zinc-500" />
            Your EPUB and PDF files, readable right here. Only you can see them.
          </p>
        </div>
        <button
          class="self-start sm:self-auto flex items-center gap-2 px-5 py-3 rounded-2xl bg-indigo-500 text-white text-sm font-bold shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 active:scale-95 transition-all"
          @click="openUpload"
        >
          <Plus :size="18" /> Add e-book
        </button>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 p-1 rounded-xl bg-zinc-900/60 border border-zinc-800 w-fit mb-6">
        <button
          :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all', tab === 'mine' ? 'bg-indigo-500 text-white shadow' : 'text-zinc-400 hover:text-white']"
          @click="tab = 'mine'"
        >
          <Library :size="15" /> My e-books
        </button>
        <button
          :class="['flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all', tab === 'classics' ? 'bg-indigo-500 text-white shadow' : 'text-zinc-400 hover:text-white']"
          @click="tab = 'classics'"
        >
          <Landmark :size="15" /> Free classics
        </button>
      </div>

      <PublicDomainCatalog v-if="tab === 'classics'" @imported="handleImported" @open="(id) => router.push(`/ebooks/${id}/read`)" />

      <template v-else>
      <div v-if="offline" class="flex items-center gap-2 mb-4 px-4 py-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-sm text-amber-300">
        <CloudOff :size="16" class="shrink-0" />
        You're offline. Books you've opened on this device can still be read - your place, quotes and notes sync when you're back online.
      </div>

      <!-- Search + storage -->
      <div v-if="ebooks.length" class="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6 mb-6">
        <div class="relative flex-1 max-w-md">
          <Search :size="16" class="absolute left-3.5 top-1/2 -translate-y-1/2 text-zinc-500" />
          <input
            v-model="searchQuery"
            placeholder="Search title or author…"
            class="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
        <div v-if="usage" class="sm:w-56">
          <div class="flex justify-between text-[11px] text-zinc-500 mb-1">
            <span>Storage</span>
            <span>{{ formatSize(usage.used_bytes) }} / {{ formatSize(usage.quota_bytes) }}</span>
          </div>
          <div class="h-1.5 rounded-full bg-zinc-800 overflow-hidden">
            <div class="h-full bg-indigo-500" :style="{ width: `${usagePercent}%` }" />
          </div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 lg:gap-6">
        <div v-for="i in 6" :key="i" class="aspect-[2/3] rounded-xl bg-zinc-900/60 animate-pulse" />
      </div>

      <!-- Empty -->
      <div v-else-if="!ebooks.length" class="max-w-lg mx-auto text-center py-16 lg:py-24">
        <div class="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto mb-6 text-indigo-400">
          <Tablet :size="28" />
        </div>
        <h3 class="text-xl font-bold text-white mb-2">No e-books yet</h3>
        <p class="text-sm text-zinc-500 mb-6">
          Add an EPUB or PDF and read it here, with your own font size, theme and margins. Your place is saved on every device.
        </p>
        <div class="flex flex-wrap justify-center gap-3">
          <button class="px-5 py-2.5 rounded-xl bg-indigo-500 text-white text-sm font-bold hover:bg-indigo-400 transition-all" @click="openUpload">
            Add your first e-book
          </button>
          <button class="px-5 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm font-bold hover:text-white hover:border-zinc-500 transition-all" @click="tab = 'classics'">
            Browse free classics
          </button>
        </div>
      </div>

      <!-- No search results -->
      <p v-else-if="!filtered.length" class="text-center text-sm text-zinc-500 py-16">No e-books match "{{ searchQuery }}".</p>

      <!-- Grid -->
      <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-x-4 gap-y-6 lg:gap-x-6 lg:gap-y-8">
        <div v-for="ebook in filtered" :key="ebook.id" class="group">
          <button
            class="relative block w-full aspect-[2/3] rounded-xl overflow-hidden shadow-lg ring-1 ring-white/5 hover:ring-indigo-500/50 transition-all"
            @click="openReader(ebook)"
          >
            <EBookCover :ebook="ebook" />
            <span class="absolute top-2 left-2 px-1.5 py-0.5 rounded-md bg-black/70 text-[9px] font-black uppercase tracking-wider text-white">
              {{ ebook.format }}
            </span>
            <div v-if="ebook.progress > 0" class="absolute bottom-0 inset-x-0 h-1 bg-black/50">
              <div class="h-full bg-indigo-500" :style="{ width: `${progressPercent(ebook)}%` }" />
            </div>
          </button>

          <div class="mt-2.5 flex items-start gap-1">
            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-white leading-snug line-clamp-2">{{ ebook.title }}</p>
              <p class="text-xs text-zinc-500 truncate mt-0.5">{{ ebook.author }}</p>
              <p class="text-[11px] text-zinc-600 mt-1">
                <CheckCircle2 v-if="ebook.library_entry?.status === 'read'" :size="11" class="inline -mt-0.5 text-emerald-500" />
                <RefreshCw v-else-if="ebook.track_progress" :size="10" class="inline -mt-0.5 text-indigo-400" title="Progress syncs to your library" />
                {{ ebook.library_entry?.status === 'read' ? 'Finished' : ebook.progress > 0 ? `${progressPercent(ebook)}% read` : 'Not started' }}
                <router-link
                  v-if="ebook.book_detail"
                  :to="getBookUrl(ebook.book_detail)"
                  class="inline-flex items-center gap-0.5 ml-1 text-indigo-400/80 hover:text-indigo-300"
                  title="Linked catalog book"
                >
                  · <Link2 :size="10" /> book
                </router-link>
              </p>
            </div>
            <div class="flex shrink-0 lg:opacity-0 lg:group-hover:opacity-100 transition-opacity">
              <button class="p-1.5 rounded-lg text-zinc-500 hover:text-white hover:bg-zinc-800" title="Edit" @click="openEdit(ebook)">
                <Pencil :size="13" />
              </button>
              <button class="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10" title="Delete" @click="handleDelete(ebook)">
                <Trash2 :size="13" />
              </button>
            </div>
          </div>
        </div>
      </div>
      </template>
    </div>

    <EBookFormDialog
      v-model:open="dialogOpen"
      :ebook="editingEbook"
      :max-upload-bytes="usage?.max_upload_bytes"
      @saved="handleSaved"
    />
  </div>
</template>
