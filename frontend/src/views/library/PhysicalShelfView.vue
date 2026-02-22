<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { recommendationsService } from '@/services/recommendationsService'
import ReadingTaste from '@/components/recommendations/ReadingTaste.vue'
import { getBookUrl } from '@/utils/bookUrl'
import { getMediaUrl } from '@/utils/mediaUrl'
import {
  BookOpen, Library, Search, Package, CheckSquare, Square,
  X, BookMarked, Loader2, Home, Gift, Heart
} from 'lucide-vue-next'

const router = useRouter()
const store = useUserBooksStore()

const activeTab = ref('owned') // 'owned' | 'wishlist'
const searchQuery = ref('')
const statusFilter = ref('all')
const bulkMode = ref(false)
const selectedIds = ref(new Set())
const loading = ref(true)
const readingTaste = ref(null)

onMounted(async () => {
  await store.fetchBooks()
  loading.value = false
  // Fetch collection taste (non-blocking)
  recommendationsService.getReadingTaste('owned').then(taste => {
    readingTaste.value = taste
  })
})

const displayedBooks = computed(() => {
  let books = activeTab.value === 'wishlist'
    ? store.books.filter(b => b.is_wishlisted)
    : store.books.filter(b => b.is_owned)

  if (statusFilter.value !== 'all') {
    books = books.filter(b => b.status === statusFilter.value)
  }

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    books = books.filter(b => {
      const title = b.book?.title?.toLowerCase() || ''
      const authors = b.book?.authors?.map(a => a.name.toLowerCase()).join(' ') || ''
      return title.includes(q) || authors.includes(q)
    })
  }

  return books
})

const stats = computed(() => {
  const owned = store.books.filter(b => b.is_owned)
  const wishlisted = store.books.filter(b => b.is_wishlisted)
  const totalPages = owned.reduce((sum, b) => sum + (b.book?.pages || 0), 0)
  const readCount = owned.filter(b => b.status === 'read').length
  const readingCount = owned.filter(b => b.status === 'currently_reading').length
  const unreadCount = owned.filter(b => b.status === 'want_to_read').length
  return { total: owned.length, totalPages, readCount, readingCount, unreadCount, wishlistCount: wishlisted.length }
})

const statusFilters = [
  { key: 'all', label: 'All' },
  { key: 'read', label: 'Read' },
  { key: 'currently_reading', label: 'Reading' },
  { key: 'want_to_read', label: 'Unread' },
]

const getCoverUrl = (book) => {
  const cover = book.book?.cover_image
  if (!cover) return null
  if (cover.startsWith('http') && !cover.includes('/media/')) return cover
  return getMediaUrl(cover)
}

const getTitle = (book) => book.book?.title || 'Unknown'
const getAuthor = (book) => book.book?.authors?.[0]?.name || ''

const toggleSelect = (id) => {
  const s = new Set(selectedIds.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  selectedIds.value = s
}

const selectAll = () => {
  if (selectedIds.value.size === displayedBooks.value.length) {
    selectedIds.value = new Set()
  } else {
    selectedIds.value = new Set(displayedBooks.value.map(b => b.id))
  }
}

const handleBulkRemove = async () => {
  if (selectedIds.value.size === 0) return
  await store.bulkToggleOwned([...selectedIds.value], false)
  selectedIds.value = new Set()
  bulkMode.value = false
}

const exitBulkMode = () => {
  bulkMode.value = false
  selectedIds.value = new Set()
}

const switchTab = (tab) => {
  activeTab.value = tab
  searchQuery.value = ''
  statusFilter.value = 'all'
  exitBulkMode()
}

const handleRemoveFromWishlist = async (bookId) => {
  await store.toggleWishlisted(bookId)
}

const getStatusBadge = (status) => {
  const map = {
    currently_reading: { label: 'Reading', class: 'bg-emerald-500/80' },
    read: { label: 'Read', class: 'bg-sky-500/80' },
    want_to_read: { label: 'Unread', class: 'bg-amber-500/80' },
    abandoned: { label: 'Abandoned', class: 'bg-slate-500/80' },
  }
  return map[status] || { label: status, class: 'bg-slate-500/80' }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 py-8">

    <!-- Header -->
    <div class="mb-8">
      <div class="flex items-center gap-2 mb-2">
        <div class="h-px w-8 bg-amber-500"></div>
        <span class="text-[10px] font-bold uppercase tracking-[0.3em] text-amber-500">Home Library</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black text-white tracking-tight">
        My Collection
      </h1>
      <p class="text-sm text-slate-400 mt-1">Books you physically own and wish to own</p>
    </div>

    <!-- Tab switcher: Owned / Wishlist -->
    <div class="flex items-center gap-1 mb-6 bg-slate-800/40 rounded-xl p-1 w-fit">
      <button
        @click="switchTab('owned')"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all',
          activeTab === 'owned'
            ? 'bg-amber-500/20 text-amber-400 shadow-sm'
            : 'text-slate-400 hover:text-slate-200'
        ]"
      >
        <Home :size="14" />
        Owned
        <span v-if="stats.total > 0" class="text-[10px] opacity-70">{{ stats.total }}</span>
      </button>
      <button
        @click="switchTab('wishlist')"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all',
          activeTab === 'wishlist'
            ? 'bg-rose-500/20 text-rose-400 shadow-sm'
            : 'text-slate-400 hover:text-slate-200'
        ]"
      >
        <Gift :size="14" />
        Wishlist
        <span v-if="stats.wishlistCount > 0" class="text-[10px] opacity-70">{{ stats.wishlistCount }}</span>
      </button>
    </div>

    <!-- Stats (only for Owned tab) -->
    <div v-if="activeTab === 'owned'" class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8" :class="{ 'hidden': stats.total === 0 }">
      <div class="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20">
        <p class="text-2xl font-black text-amber-100">{{ stats.total }}</p>
        <p class="text-[10px] font-bold uppercase tracking-wider text-amber-500">Books Owned</p>
      </div>
      <div class="p-4 rounded-2xl bg-slate-800/50 border border-slate-700/30">
        <p class="text-2xl font-black text-slate-100">{{ stats.totalPages.toLocaleString() }}</p>
        <p class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Pages</p>
      </div>
      <div class="p-4 rounded-2xl bg-sky-500/10 border border-sky-500/20">
        <p class="text-2xl font-black text-sky-100">{{ stats.readCount }}</p>
        <p class="text-[10px] font-bold uppercase tracking-wider text-sky-400">Read</p>
      </div>
      <div class="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
        <p class="text-2xl font-black text-emerald-100">{{ stats.readingCount }}</p>
        <p class="text-[10px] font-bold uppercase tracking-wider text-emerald-400">Reading Now</p>
      </div>
    </div>

    <!-- Collection Taste -->
    <ReadingTaste
      v-if="readingTaste && readingTaste.books_count >= 3 && activeTab === 'owned'"
      :taste="readingTaste"
      title="Collection Taste"
      accent-color="amber"
      class="mb-8"
    />

    <!-- Toolbar -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 mb-6">
      <!-- Search -->
      <div class="relative flex-1 max-w-sm">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" :size="16" />
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="activeTab === 'wishlist' ? 'Search wishlist...' : 'Search your collection...'"
          class="w-full pl-9 pr-4 py-2.5 rounded-xl bg-slate-800/40 border border-slate-700/50 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500/50"
        />
      </div>

      <!-- Status filters -->
      <div v-if="activeTab === 'owned'" class="flex items-center gap-1 bg-slate-800/40 rounded-xl p-1">
        <button
          v-for="f in statusFilters"
          :key="f.key"
          @click="statusFilter = f.key"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-bold transition-all',
            statusFilter === f.key
              ? 'bg-white/10 text-white shadow-sm'
              : 'text-slate-400 hover:text-slate-200'
          ]"
        >
          {{ f.label }}
        </button>
      </div>

      <!-- Bulk mode toggle (owned tab only) -->
      <button
        v-if="activeTab === 'owned'"
        @click="bulkMode ? exitBulkMode() : (bulkMode = true)"
        :class="[
          'flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all border',
          bulkMode
            ? 'bg-amber-500 text-white border-amber-500'
            : 'bg-slate-800/40 text-slate-400 border-slate-700/50 hover:border-amber-500/50 hover:text-slate-200'
        ]"
      >
        <CheckSquare :size="14" />
        {{ bulkMode ? 'Cancel' : 'Select' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-24">
      <Loader2 class="animate-spin text-amber-500" :size="32" />
    </div>

    <!-- OWNED TAB - Empty state: no owned books -->
    <div v-else-if="activeTab === 'owned' && stats.total === 0" class="text-center py-24">
      <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-amber-500/10 mb-6">
        <Home class="text-amber-400" :size="32" />
      </div>
      <h3 class="text-xl font-bold text-white mb-2">Your home library is empty</h3>
      <p class="text-sm text-slate-400 mb-6 max-w-md mx-auto">
        Start by marking books you own from your library. Open any book and toggle "I Own This" to add it here.
      </p>
      <button
        @click="router.push('/library')"
        class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-sm transition-all"
      >
        <Library :size="16" />
        Go to Library
      </button>
    </div>

    <!-- WISHLIST TAB - Empty state -->
    <div v-else-if="activeTab === 'wishlist' && stats.wishlistCount === 0" class="text-center py-24">
      <div class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-rose-500/10 mb-6">
        <Gift class="text-rose-400" :size="32" />
      </div>
      <h3 class="text-xl font-bold text-white mb-2">Your wishlist is empty</h3>
      <p class="text-sm text-slate-400 mb-6 max-w-md mx-auto">
        Browse books and add ones you'd love to own. Your friends can see your wishlist for gift ideas!
      </p>
      <button
        @click="router.push('/library')"
        class="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-sm transition-all"
      >
        <Library :size="16" />
        Browse Library
      </button>
    </div>

    <!-- Empty state: filter returns nothing -->
    <div v-else-if="displayedBooks.length === 0" class="text-center py-24">
      <p class="text-slate-400">No books match your filters.</p>
    </div>

    <!-- Book grid -->
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-3 sm:gap-4">
      <div
        v-for="book in displayedBooks"
        :key="book.id"
        @click="bulkMode ? toggleSelect(book.id) : router.push(getBookUrl(book.book || book))"
        class="group relative cursor-pointer"
      >
        <!-- Cover -->
        <div
          :class="[
            'aspect-[2/3] rounded-lg overflow-hidden border-2 transition-all duration-200',
            bulkMode && selectedIds.has(book.id)
              ? 'border-amber-500 ring-2 ring-amber-500/30 scale-[0.96]'
              : 'border-transparent group-hover:border-amber-500/30 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:shadow-black/40'
          ]"
        >
          <!-- Cover image -->
          <img
            v-if="getCoverUrl(book)"
            :src="getCoverUrl(book)"
            :alt="getTitle(book)"
            class="w-full h-full object-cover"
            loading="lazy"
            @error="(e) => e.target.style.display = 'none'"
          />

          <!-- Fallback when no cover -->
          <div
            v-if="!getCoverUrl(book)"
            :class="[
              'w-full h-full flex items-center justify-center p-3',
              activeTab === 'wishlist'
                ? 'bg-gradient-to-br from-rose-800 to-stone-900'
                : 'bg-gradient-to-br from-amber-800 to-stone-900'
            ]"
          >
            <span class="text-[11px] font-bold text-white/80 text-center leading-tight line-clamp-4">
              {{ getTitle(book) }}
            </span>
          </div>

          <!-- Hover overlay -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-2.5">
            <p class="text-[11px] font-bold text-white leading-tight line-clamp-2">{{ getTitle(book) }}</p>
            <p class="text-[10px] text-white/70 line-clamp-1 mt-0.5">{{ getAuthor(book) }}</p>
            <!-- Remove from wishlist button -->
            <button
              v-if="activeTab === 'wishlist'"
              @click.stop="handleRemoveFromWishlist(book.id)"
              class="mt-1.5 px-2 py-1 rounded-lg bg-rose-500/20 text-rose-300 text-[10px] font-bold hover:bg-rose-500/30 transition-colors pointer-events-auto"
            >
              Remove
            </button>
          </div>

          <!-- Status badge -->
          <div class="absolute top-1.5 left-1.5 pointer-events-none">
            <span
              :class="[
                'px-1.5 py-0.5 rounded text-[8px] font-bold text-white uppercase tracking-wider',
                getStatusBadge(book.status).class
              ]"
            >
              {{ getStatusBadge(book.status).label }}
            </span>
          </div>

          <!-- Wishlist badge (on owned tab, if book is also wishlisted - shouldn't happen normally) -->

          <!-- Bulk select checkbox -->
          <div v-if="bulkMode" class="absolute top-1.5 right-1.5">
            <div
              :class="[
                'w-5 h-5 rounded flex items-center justify-center transition-all',
                selectedIds.has(book.id)
                  ? 'bg-amber-500 text-white'
                  : 'bg-black/40 backdrop-blur-sm border border-white/30'
              ]"
            >
              <CheckSquare v-if="selectedIds.has(book.id)" :size="12" />
              <Square v-else :size="12" class="text-white/70" />
            </div>
          </div>
        </div>

        <!-- Title below cover (mobile) -->
        <div class="mt-1.5 sm:hidden">
          <p class="text-[11px] font-semibold text-slate-200 line-clamp-2 leading-tight">{{ getTitle(book) }}</p>
        </div>
      </div>
    </div>

    <!-- Bulk action bar -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div
        v-if="bulkMode && selectedIds.size > 0"
        class="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-6 py-3 rounded-2xl bg-slate-800/90 backdrop-blur-xl border border-slate-700/50 shadow-2xl"
      >
        <button
          @click="selectAll"
          class="text-xs font-bold text-slate-300 hover:text-white transition-colors"
        >
          {{ selectedIds.size === displayedBooks.length ? 'Deselect All' : 'Select All' }}
        </button>
        <div class="w-px h-5 bg-slate-600"></div>
        <span class="text-xs font-bold text-white">{{ selectedIds.size }} selected</span>
        <div class="w-px h-5 bg-slate-600"></div>
        <button
          @click="handleBulkRemove"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-red-500/20 hover:bg-red-500/30 text-red-300 text-xs font-bold transition-all"
        >
          <X :size="14" />
          Remove from Shelf
        </button>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
/* Light mode overrides */
body.light .text-white {
  color: #0f172a !important;
}
body.light .text-slate-400,
body.light .text-slate-500 {
  color: #64748b !important;
}
body.light .text-slate-200 {
  color: #334155 !important;
}
body.light .text-slate-300 {
  color: #475569 !important;
}
body.light .text-amber-100,
body.light .text-sky-100,
body.light .text-emerald-100,
body.light .text-slate-100 {
  color: #1e293b !important;
}
body.light .bg-slate-800\/40 {
  background-color: rgba(255, 255, 255, 0.8) !important;
  border-color: rgba(0, 0, 0, 0.1) !important;
}
body.light .bg-slate-800\/50 {
  background-color: rgba(241, 245, 249, 0.8) !important;
}
body.light .border-slate-700\/50,
body.light .border-slate-700\/30 {
  border-color: rgba(0, 0, 0, 0.1) !important;
}
</style>
