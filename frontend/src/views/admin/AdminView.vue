<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { adminAPI, authorsAPI, booksAPI, contributionsAPI } from '@/services/api'
import { getBookUrl } from '@/utils/bookUrl'
import { tierClasses } from '@/config/tiers'
import { sourceLabel, sourceColor } from '@/config/sources'
import {
  Database, ShieldAlert, Link2, GitMerge, Plus,
  BarChart3, Settings, Search, Check, X, AlertTriangle,
  ChevronRight, ArrowRight, Filter, Download, Save,
  RefreshCw, Globe, BookCopy, Users, Layers,
  BookOpen, ChevronLeft, Unlink, Ban, Award, Trophy,
  Star, TrendingUp, Crown, Trash2
} from 'lucide-vue-next'

const router = useRouter()
const activeTab = ref('overview')
const searchQuery = ref('')

// Data
const stats = ref(null)
const dataIssues = ref(null)
const authorCandidates = ref(null)
const bookCandidates = ref(null)
const books = ref(null)
const reputationData = ref(null)
const loading = ref({ stats: true, issues: true, authors: true, books: true, bookSync: true, reputation: true })

// Filters
const issueFilter = ref('all')
const bookFilter = ref('all')
const booksPage = ref(1)
const issuesPage = ref(1)
const authorsPage = ref(1)

// Linking / dismissing state
const linkingAuthor = ref(null)
const dismissingAuthor = ref(null)
const linkingBook = ref(null)
const dismissingBook = ref(null)
const deletingBook = ref(null)
const bookSyncPage = ref(1)

onMounted(() => {
  fetchStats()
  fetchDataIssues()
  fetchAuthorCandidates()
  fetchBooks()
  fetchBookCandidates()
  fetchReputation()
})

const fetchStats = async () => {
  loading.value.stats = true
  try {
    const res = await adminAPI.stats()
    stats.value = res.data
  } catch (e) {
    console.error('Failed to fetch admin stats:', e)
  } finally {
    loading.value.stats = false
  }
}

const fetchDataIssues = async () => {
  loading.value.issues = true
  try {
    const res = await adminAPI.dataIssues({ type: issueFilter.value, page: issuesPage.value })
    dataIssues.value = res.data
  } catch (e) {
    console.error('Failed to fetch data issues:', e)
  } finally {
    loading.value.issues = false
  }
}

const fetchAuthorCandidates = async () => {
  loading.value.authors = true
  try {
    const res = await adminAPI.authorMergeCandidates({ page: authorsPage.value })
    authorCandidates.value = res.data
  } catch (e) {
    console.error('Failed to fetch author candidates:', e)
  } finally {
    loading.value.authors = false
  }
}

const fetchBooks = async () => {
  loading.value.books = true
  try {
    const res = await adminAPI.books({
      search: searchQuery.value,
      page: booksPage.value,
      filter: bookFilter.value,
    })
    books.value = res.data
  } catch (e) {
    console.error('Failed to fetch admin books:', e)
  } finally {
    loading.value.books = false
  }
}

const fetchReputation = async () => {
  loading.value.reputation = true
  try {
    const res = await contributionsAPI.dashboard()
    reputationData.value = res.data
  } catch (e) {
    console.error('Failed to fetch reputation dashboard:', e)
  } finally {
    loading.value.reputation = false
  }
}

const fetchBookCandidates = async () => {
  loading.value.bookSync = true
  try {
    const res = await adminAPI.bookMergeCandidates({ page: bookSyncPage.value })
    bookCandidates.value = res.data
  } catch (e) {
    console.error('Failed to fetch book candidates:', e)
  } finally {
    loading.value.bookSync = false
  }
}

const handleLinkBook = async (primaryId, variantId) => {
  linkingBook.value = variantId
  try {
    await booksAPI.linkEdition(primaryId, variantId)
    if (bookCandidates.value) {
      const candidate = bookCandidates.value.results.find(c => c.primary.id === primaryId)
      if (candidate) {
        candidate.variants = candidate.variants.filter(v => v.id !== variantId)
        if (candidate.variants.length === 0) {
          bookCandidates.value.results = bookCandidates.value.results.filter(c => c.primary.id !== primaryId)
          bookCandidates.value.count--
        }
      }
    }
  } catch (e) {
    console.error('Failed to link book:', e)
  } finally {
    linkingBook.value = null
  }
}

const handleDismissBook = async (primaryId, variantId) => {
  dismissingBook.value = variantId
  try {
    await adminAPI.dismissBookPair(primaryId, variantId)
    if (bookCandidates.value) {
      const candidate = bookCandidates.value.results.find(c => c.primary.id === primaryId)
      if (candidate) {
        candidate.variants = candidate.variants.filter(v => v.id !== variantId)
        if (candidate.variants.length === 0) {
          bookCandidates.value.results = bookCandidates.value.results.filter(c => c.primary.id !== primaryId)
          bookCandidates.value.count--
        }
      }
    }
  } catch (e) {
    console.error('Failed to dismiss book pair:', e)
  } finally {
    dismissingBook.value = null
  }
}

const handleUnlinkBook = async (bookId) => {
  try {
    await adminAPI.unlinkBook(bookId)
    fetchBookCandidates()
  } catch (e) {
    console.error('Failed to unlink book:', e)
  }
}

const handleDeleteBook = async (bookId, transferToId = null) => {
  if (!confirm('Are you sure you want to delete this book? This cannot be undone.')) return
  deletingBook.value = bookId
  try {
    await adminAPI.deleteBook(bookId, transferToId)
    fetchBookCandidates()
    fetchBooks()
    fetchStats()
  } catch (e) {
    console.error('Failed to delete book:', e)
  } finally {
    deletingBook.value = null
  }
}

const tierColor = (tier) => tierClasses(tier)

const handleIssueFilter = (type) => {
  issueFilter.value = type
  issuesPage.value = 1
  fetchDataIssues()
}

const handleBookFilter = (type) => {
  bookFilter.value = type
  booksPage.value = 1
  fetchBooks()
}

const handleBookSearch = () => {
  booksPage.value = 1
  fetchBooks()
}

const handleLinkAuthor = async (primaryId, variantId) => {
  linkingAuthor.value = variantId
  try {
    await authorsAPI.linkAuthor(primaryId, variantId)
    // Remove variant from local data instead of refetching
    if (authorCandidates.value) {
      const candidate = authorCandidates.value.results.find(c => c.primary.id === primaryId)
      if (candidate) {
        candidate.variants = candidate.variants.filter(v => v.id !== variantId)
        // If no variants left, remove the entire candidate card
        if (candidate.variants.length === 0) {
          authorCandidates.value.results = authorCandidates.value.results.filter(c => c.primary.id !== primaryId)
          authorCandidates.value.count--
        }
      }
    }
  } catch (e) {
    console.error('Failed to link author:', e)
  } finally {
    linkingAuthor.value = null
  }
}

const handleDismissAuthor = async (primaryId, variantId) => {
  dismissingAuthor.value = variantId
  try {
    await adminAPI.dismissAuthorPair(primaryId, variantId)
    // Remove variant from local data
    if (authorCandidates.value) {
      const candidate = authorCandidates.value.results.find(c => c.primary.id === primaryId)
      if (candidate) {
        candidate.variants = candidate.variants.filter(v => v.id !== variantId)
        if (candidate.variants.length === 0) {
          authorCandidates.value.results = authorCandidates.value.results.filter(c => c.primary.id !== primaryId)
          authorCandidates.value.count--
        }
      }
    }
  } catch (e) {
    console.error('Failed to dismiss author pair:', e)
  } finally {
    dismissingAuthor.value = null
  }
}

const handleUnlinkAuthor = async (authorId) => {
  try {
    await adminAPI.unlinkAuthor(authorId)
    // Refetch to update the candidates list (unlinked author may now appear)
    fetchAuthorCandidates()
  } catch (e) {
    console.error('Failed to unlink author:', e)
  }
}

const navigateToBook = (book) => {
  if (book.id) {
    router.push(`/books/${book.id}`)
  }
}

const issuesBadge = computed(() => {
  if (!dataIssues.value) return '...'
  return dataIssues.value.count.toString()
})

const severityColor = (severity) => {
  if (severity === 'high') return 'bg-rose-500/10 text-rose-500'
  if (severity === 'medium') return 'bg-amber-500/10 text-amber-500'
  return 'bg-slate-500/10 text-slate-400'
}

const issueTypeLabel = (type) => {
  const map = {
    missing_cover: 'No Cover',
    missing_isbn: 'No ISBN',
    missing_authors: 'No Authors',
    duplicate_isbn: 'Duplicate',
  }
  return map[type] || type
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="h-full flex flex-col bg-[#02040a] overflow-hidden">

    <!-- Top Architect Bar -->
    <header class="border-b border-white/5 bg-slate-950/40 backdrop-blur-3xl shrink-0">
      <!-- Title Row -->
      <div class="h-14 lg:h-24 flex items-center justify-between px-4 lg:px-10">
        <div class="flex items-center gap-3 lg:gap-6">
          <div class="w-8 h-8 lg:w-12 lg:h-12 rounded-xl lg:rounded-2xl bg-indigo-500 flex items-center justify-center shadow-2xl shadow-indigo-500/20 ring-1 ring-white/20">
            <Database :size="16" class="lg:hidden text-white" />
            <Database :size="24" class="hidden lg:block text-white" />
          </div>
          <div>
            <h1 class="text-sm lg:text-2xl font-black text-white tracking-tighter uppercase">Architect <span class="text-indigo-500">Command</span></h1>
            <div class="flex items-center gap-2 lg:gap-3">
              <span class="text-[8px] lg:text-[10px] font-black text-slate-500 uppercase tracking-widest hidden sm:inline">System Core v8.4.1</span>
              <div class="flex items-center gap-1">
                <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                <span class="text-[8px] lg:text-[9px] font-black text-emerald-500/80 uppercase">Active</span>
              </div>
            </div>
          </div>
        </div>

        <div class="hidden lg:flex items-center gap-4">
          <button class="p-3 rounded-2xl bg-white/5 text-slate-500 hover:text-white transition-all">
            <Settings :size="18" />
          </button>
          <button class="p-3 rounded-2xl bg-indigo-500 text-white shadow-xl shadow-indigo-500/20 hover:bg-indigo-400 transition-all" title="Export Schema">
            <Download :size="18" />
          </button>
        </div>
      </div>

      <!-- Tab Nav — scrollable on mobile -->
      <nav class="flex items-center gap-1 lg:gap-2 px-3 lg:px-10 pb-3 lg:pb-4 overflow-x-auto scrollbar-hide -mx-0">
        <div class="flex items-center gap-1 lg:gap-2 p-1 lg:p-1.5 bg-white/5 rounded-xl lg:rounded-2xl border border-white/5">
          <button
            v-for="tab in [
              { id: 'overview', label: 'Insight', icon: BarChart3 },
              { id: 'conflicts', label: 'Conflicts', icon: ShieldAlert, badge: issuesBadge },
              { id: 'authors', label: 'Authors', icon: Users },
              { id: 'bookSync', label: 'Books', icon: BookCopy },
              { id: 'curation', label: 'Archive', icon: Layers },
              { id: 'reputation', label: 'Rep', icon: Award },
            ]"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'px-2.5 lg:px-5 py-2 lg:py-2.5 rounded-lg lg:rounded-xl text-[9px] lg:text-[10px] font-black uppercase tracking-widest transition-all flex items-center gap-1 lg:gap-2 whitespace-nowrap flex-shrink-0',
              activeTab === tab.id
                ? 'bg-indigo-500 text-white shadow-lg'
                : 'text-slate-500 hover:text-slate-300'
            ]"
          >
            <component :is="tab.icon" :size="13" class="lg:w-[14px] lg:h-[14px]" />
            <span>{{ tab.label }}</span>
            <span
              v-if="tab.badge"
              :class="[
                'px-1.5 py-0.5 rounded-md text-[8px]',
                activeTab === tab.id
                  ? 'bg-white text-indigo-500'
                  : 'bg-rose-500 text-white shadow-[0_0_10px_#f43f5e]'
              ]"
            >{{ tab.badge }}</span>
          </button>
        </div>
      </nav>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto custom-scrollbar p-3 lg:p-10">
      <div class="max-w-[1600px] mx-auto space-y-6 lg:space-y-12">

        <!-- ==================== INSIGHT TAB ==================== -->
        <div v-if="activeTab === 'overview'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">

          <!-- Loading -->
          <div v-if="loading.stats" class="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div v-for="n in 4" :key="n" class="h-40 rounded-[2.5rem] bg-white/[0.03] animate-pulse" />
          </div>

          <template v-else-if="stats">
            <!-- Stat Cards -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 lg:gap-6">
              <!-- Total Books -->
              <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2.5rem] glass border-white/5 bg-white/[0.03] hover:bg-white/[0.05] hover:border-indigo-500/20 transition-all group">
                <div class="flex items-center justify-between mb-2 lg:mb-6">
                  <div class="p-1.5 lg:p-3 rounded-lg lg:rounded-2xl bg-white/5 border border-white/10 text-indigo-400 group-hover:scale-110 transition-all">
                    <Globe :size="16" class="lg:w-5 lg:h-5" />
                  </div>
                  <span class="text-[7px] lg:text-[8px] font-black px-1.5 lg:px-2 py-0.5 rounded uppercase tracking-widest bg-emerald-500/10 text-emerald-500 hidden sm:inline">
                    +{{ stats.activity.books_added_this_week }} this week
                  </span>
                </div>
                <p class="text-[9px] lg:text-[10px] font-black text-slate-600 uppercase tracking-widest mb-0.5 lg:mb-1">Library</p>
                <p class="text-lg lg:text-3xl font-black text-white tracking-tighter">{{ stats.counts.total_books.toLocaleString() }}</p>
              </div>

              <!-- Data Issues -->
              <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2.5rem] glass border-white/5 bg-white/[0.03] hover:bg-white/[0.05] hover:border-rose-500/20 transition-all group">
                <div class="flex items-center justify-between mb-2 lg:mb-6">
                  <div class="p-1.5 lg:p-3 rounded-lg lg:rounded-2xl bg-white/5 border border-white/10 text-rose-500 group-hover:scale-110 transition-all">
                    <ShieldAlert :size="16" class="lg:w-5 lg:h-5" />
                  </div>
                  <span class="text-[7px] lg:text-[8px] font-black px-1.5 lg:px-2 py-0.5 rounded uppercase tracking-widest bg-rose-500/10 text-rose-500 hidden sm:inline">
                    Action
                  </span>
                </div>
                <p class="text-[9px] lg:text-[10px] font-black text-slate-600 uppercase tracking-widest mb-0.5 lg:mb-1">Issues</p>
                <p class="text-lg lg:text-3xl font-black text-white tracking-tighter">
                  {{ (stats.data_quality.books_without_cover + stats.data_quality.books_without_isbn + stats.data_quality.books_without_authors) }}
                </p>
              </div>

              <!-- Author Consistency -->
              <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2.5rem] glass border-white/5 bg-white/[0.03] hover:bg-white/[0.05] hover:border-indigo-500/20 transition-all group">
                <div class="flex items-center justify-between mb-2 lg:mb-6">
                  <div class="p-1.5 lg:p-3 rounded-lg lg:rounded-2xl bg-white/5 border border-white/10 text-indigo-400 group-hover:scale-110 transition-all">
                    <Link2 :size="16" class="lg:w-5 lg:h-5" />
                  </div>
                  <span class="text-[7px] lg:text-[8px] font-black px-1.5 lg:px-2 py-0.5 rounded uppercase tracking-widest bg-emerald-500/10 text-emerald-500 hidden sm:inline">
                    Consistency
                  </span>
                </div>
                <p class="text-[9px] lg:text-[10px] font-black text-slate-600 uppercase tracking-widest mb-0.5 lg:mb-1">Authors</p>
                <p class="text-lg lg:text-3xl font-black text-white tracking-tighter">{{ stats.data_quality.author_consistency }}%</p>
              </div>

              <!-- User Activity -->
              <div class="p-3 lg:p-8 rounded-xl lg:rounded-[2.5rem] glass border-white/5 bg-white/[0.03] hover:bg-white/[0.05] hover:border-indigo-500/20 transition-all group">
                <div class="flex items-center justify-between mb-2 lg:mb-6">
                  <div class="p-1.5 lg:p-3 rounded-lg lg:rounded-2xl bg-white/5 border border-white/10 text-indigo-400 group-hover:scale-110 transition-all">
                    <Users :size="16" class="lg:w-5 lg:h-5" />
                  </div>
                  <span class="text-[7px] lg:text-[8px] font-black px-1.5 lg:px-2 py-0.5 rounded uppercase tracking-widest bg-emerald-500/10 text-emerald-500 hidden sm:inline">
                    {{ stats.counts.total_users }} users
                  </span>
                </div>
                <p class="text-[9px] lg:text-[10px] font-black text-slate-600 uppercase tracking-widest mb-0.5 lg:mb-1">Knowledge</p>
                <p class="text-lg lg:text-3xl font-black text-white tracking-tighter">{{ (stats.counts.total_quotes + stats.counts.total_vocabulary).toLocaleString() }}</p>
              </div>
            </div>

            <!-- Recent Books + Schema Health -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
              <!-- Recent Books -->
              <div class="lg:col-span-2 glass rounded-2xl lg:rounded-[2.5rem] p-6 lg:p-10 border-white/5 space-y-6 lg:space-y-8">
                <div class="flex items-center justify-between">
                  <h3 class="text-lg lg:text-xl font-black text-white tracking-tight uppercase">Recent Additions</h3>
                  <button @click="activeTab = 'curation'" class="text-indigo-400 text-[10px] font-black uppercase tracking-widest hover:underline">View All</button>
                </div>
                <div class="space-y-3 lg:space-y-4">
                  <div
                    v-for="book in stats.recent_books"
                    :key="book.id"
                    @click="router.push(`/books/${book.id}`)"
                    class="flex items-center justify-between p-4 lg:p-5 rounded-xl lg:rounded-2xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all group cursor-pointer"
                  >
                    <div class="flex items-center gap-4 lg:gap-5 min-w-0">
                      <div class="w-8 h-12 lg:w-10 lg:h-14 rounded-lg bg-slate-900 border border-white/5 flex-shrink-0 overflow-hidden">
                        <img v-if="book.cover_image" :src="book.cover_image" class="w-full h-full object-cover" />
                        <div v-else class="w-full h-full flex items-center justify-center">
                          <BookOpen :size="14" class="text-slate-700" />
                        </div>
                      </div>
                      <div class="min-w-0">
                        <p class="text-sm font-bold text-white truncate">{{ book.title }}</p>
                        <p class="text-[10px] text-slate-500 font-bold uppercase">
                          <span :class="sourceColor(book.source)" class="px-1.5 py-0.5 rounded text-[8px]">{{ sourceLabel(book.source) }}</span>
                          <span class="ml-2">{{ formatDate(book.created_at) }}</span>
                        </p>
                      </div>
                    </div>
                    <ChevronRight :size="16" class="text-slate-700 group-hover:text-indigo-400 transition-all flex-shrink-0" />
                  </div>
                </div>
              </div>

              <!-- Schema Health -->
              <div class="glass rounded-2xl lg:rounded-[2.5rem] p-6 lg:p-10 border-white/5 space-y-6 self-start">
                <div>
                  <h3 class="text-lg lg:text-xl font-black text-white tracking-tight uppercase mb-2">Data Health</h3>
                  <p class="text-slate-500 text-sm font-medium">Coverage across covers, ISBNs, and author links.</p>
                </div>

                <div class="flex flex-col items-center py-4">
                  <div class="relative w-32 h-32">
                    <svg class="w-32 h-32 -rotate-90" viewBox="0 0 128 128">
                      <circle cx="64" cy="64" r="54" fill="none" stroke="rgba(99,102,241,0.1)" stroke-width="10" />
                      <circle
                        cx="64" cy="64" r="54" fill="none"
                        stroke="rgb(99,102,241)"
                        stroke-width="10"
                        stroke-linecap="round"
                        :stroke-dasharray="`${(stats.data_quality.health_percentage / 100) * 339.3} 339.3`"
                      />
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center">
                      <span class="text-2xl font-black text-white">{{ stats.data_quality.health_percentage }}%</span>
                      <span class="text-[8px] font-black text-slate-500 uppercase">Health</span>
                    </div>
                  </div>
                </div>

                <div class="space-y-2 text-[10px] font-bold">
                  <div class="flex justify-between text-slate-500"><span>Missing covers</span><span class="text-white">{{ stats.data_quality.books_without_cover }}</span></div>
                  <div class="flex justify-between text-slate-500"><span>Missing ISBNs</span><span class="text-white">{{ stats.data_quality.books_without_isbn }}</span></div>
                  <div class="flex justify-between text-slate-500"><span>No authors</span><span class="text-white">{{ stats.data_quality.books_without_authors }}</span></div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- ==================== CONFLICTS TAB ==================== -->
        <div v-if="activeTab === 'conflicts'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <header class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h2 class="text-xl lg:text-4xl font-black text-white tracking-tighter uppercase mb-1 lg:mb-2">Data <span class="text-rose-500">Issues</span></h2>
              <p class="text-slate-500 font-medium text-xs lg:text-sm">Books with missing or inconsistent data requiring attention.</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="f in [
                  { id: 'all', label: 'All' },
                  { id: 'missing_cover', label: 'No Cover' },
                  { id: 'missing_isbn', label: 'No ISBN' },
                  { id: 'missing_authors', label: 'No Authors' },
                  { id: 'duplicates', label: 'Duplicates' },
                ]"
                :key="f.id"
                @click="handleIssueFilter(f.id)"
                :class="[
                  'px-3 lg:px-4 py-1.5 lg:py-2 rounded-lg lg:rounded-xl text-[9px] lg:text-[10px] font-black uppercase tracking-widest transition-all',
                  issueFilter === f.id
                    ? 'bg-indigo-500 text-white shadow-lg'
                    : 'bg-white/5 border border-white/5 text-slate-400 hover:text-white'
                ]"
              >{{ f.label }}</button>
            </div>
          </header>

          <!-- Loading -->
          <div v-if="loading.issues" class="space-y-4">
            <div v-for="n in 3" :key="n" class="h-24 rounded-2xl bg-white/[0.03] animate-pulse" />
          </div>

          <!-- Summary badges -->
          <div v-else-if="dataIssues" class="space-y-6">
            <div class="flex flex-wrap gap-2">
              <div class="px-2.5 lg:px-4 py-1.5 lg:py-2 rounded-lg lg:rounded-xl bg-amber-500/10 border border-amber-500/20">
                <span class="text-amber-400 text-[10px] lg:text-xs font-black">{{ dataIssues.summary.missing_cover }}</span>
                <span class="text-slate-500 text-[9px] lg:text-[10px] ml-1">covers</span>
              </div>
              <div class="px-2.5 lg:px-4 py-1.5 lg:py-2 rounded-lg lg:rounded-xl bg-sky-500/10 border border-sky-500/20">
                <span class="text-sky-400 text-[10px] lg:text-xs font-black">{{ dataIssues.summary.missing_isbn }}</span>
                <span class="text-slate-500 text-[9px] lg:text-[10px] ml-1">ISBNs</span>
              </div>
              <div class="px-2.5 lg:px-4 py-1.5 lg:py-2 rounded-lg lg:rounded-xl bg-rose-500/10 border border-rose-500/20">
                <span class="text-rose-400 text-[10px] lg:text-xs font-black">{{ dataIssues.summary.missing_authors }}</span>
                <span class="text-slate-500 text-[9px] lg:text-[10px] ml-1">authors</span>
              </div>
              <div class="px-2.5 lg:px-4 py-1.5 lg:py-2 rounded-lg lg:rounded-xl bg-purple-500/10 border border-purple-500/20">
                <span class="text-purple-400 text-[10px] lg:text-xs font-black">{{ dataIssues.summary.duplicates }}</span>
                <span class="text-slate-500 text-[9px] lg:text-[10px] ml-1">dupes</span>
              </div>
            </div>

            <!-- Issues Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <div
                v-for="issue in dataIssues.results"
                :key="issue.id"
                class="flex items-end justify-between p-4 lg:p-5 rounded-2xl glass border-white/5 hover:bg-white/[0.04] transition-all group"
              >
                <div class="flex items-center gap-4 min-w-0 flex-1">
                  <div class="w-10 h-14 rounded-lg bg-slate-900 border border-white/10 flex-shrink-0 overflow-hidden">
                    <img v-if="issue.cover_image" :src="issue.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <BookOpen :size="14" class="text-slate-700" />
                    </div>
                  </div>
                  <div class="min-w-0">
                    <p class="text-sm font-bold text-white line-clamp-2">{{ issue.title }}</p>
                    <p class="text-[10px] text-slate-500 mt-0.5">{{ issue.description }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-3 flex-shrink-0 ml-3">
                  <span :class="[severityColor(issue.severity), 'text-[9px] font-black px-2 py-0.5 rounded uppercase tracking-widest']">
                    {{ issueTypeLabel(issue.issue_type) }}
                  </span>
                  <button
                    v-if="issue.book_id"
                    @click="router.push(`/books/${issue.book_id}`)"
                    class="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-[9px] font-black uppercase tracking-widest hover:bg-white/10 transition-all"
                  >
                    View
                  </button>
                </div>
              </div>
            </div>

            <!-- Pagination -->
            <div v-if="dataIssues.count > 20" class="flex items-center justify-center gap-4 pt-4">
              <button
                :disabled="issuesPage <= 1"
                @click="issuesPage--; fetchDataIssues()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronLeft :size="14" />
              </button>
              <span class="text-xs font-bold text-slate-500">Page {{ issuesPage }} <span class="text-slate-600">of {{ Math.ceil(dataIssues.count / 20) }}</span></span>
              <button
                :disabled="issuesPage * 20 >= dataIssues.count"
                @click="issuesPage++; fetchDataIssues()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronRight :size="14" />
              </button>
            </div>
          </div>
        </div>

        <!-- ==================== AUTHOR SYNC TAB ==================== -->
        <div v-if="activeTab === 'authors'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <header>
            <h2 class="text-xl lg:text-4xl font-black text-white tracking-tighter uppercase mb-1 lg:mb-2">Author <span class="text-indigo-500">Synchronizer</span></h2>
            <p class="text-slate-500 font-medium text-xs lg:text-sm">Merge name variations and link creators to their canonical records.</p>
          </header>

          <!-- Loading -->
          <div v-if="loading.authors" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div v-for="n in 4" :key="n" class="h-64 rounded-[2.5rem] bg-white/[0.03] animate-pulse" />
          </div>

          <template v-else-if="authorCandidates">
            <!-- Auto-linked notification -->
            <div v-if="authorCandidates.auto_linked > 0" class="flex items-center gap-3 px-5 py-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mb-2">
              <Check :size="18" class="text-emerald-400 flex-shrink-0" />
              <p class="text-sm text-emerald-300 font-medium">
                Auto-linked <span class="font-black text-emerald-200">{{ authorCandidates.auto_linked }}</span> identical author{{ authorCandidates.auto_linked > 1 ? 's' : '' }} (punctuation/spacing variants).
              </p>
            </div>

            <div v-if="authorCandidates.results.length === 0" class="py-20 text-center">
              <div class="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <Check :size="24" class="text-emerald-500" />
              </div>
              <h3 class="text-xl font-black text-white mb-2">All Clear</h3>
              <p class="text-slate-500 text-sm">No duplicate author variations detected.</p>
            </div>

            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
              <div
                v-for="auth in authorCandidates.results"
                :key="auth.primary.id"
                class="glass rounded-2xl lg:rounded-[2.5rem] border-white/5 p-4 lg:p-10 space-y-4 lg:space-y-8 group hover:border-indigo-500/20 transition-all"
              >
                <!-- Author Header -->
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3 lg:gap-6">
                    <div class="w-10 h-10 lg:w-14 lg:h-14 rounded-xl lg:rounded-2xl bg-gradient-to-tr from-indigo-500 to-purple-600 p-0.5 flex-shrink-0">
                      <div class="w-full h-full rounded-xl lg:rounded-2xl bg-slate-900 flex items-center justify-center font-black text-base lg:text-xl text-white overflow-hidden">
                        <img v-if="auth.primary.photo" :src="auth.primary.photo" class="w-full h-full object-cover" />
                        <span v-else>{{ auth.primary.name.charAt(0) }}</span>
                      </div>
                    </div>
                    <div>
                      <h3 class="text-base lg:text-xl font-black text-white">{{ auth.primary.name }}</h3>
                      <p class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">{{ auth.primary.book_count }} works</p>
                    </div>
                  </div>
                  <div class="text-right hidden sm:block">
                    <p class="text-[9px] font-black text-slate-600 uppercase tracking-widest">Total Books</p>
                    <p class="text-xs font-bold text-slate-400">{{ auth.total_books }}</p>
                  </div>
                </div>

                <!-- Variants -->
                <div class="p-3 lg:p-6 rounded-2xl bg-black/40 border border-white/5 space-y-2 lg:space-y-4">
                  <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-1 lg:mb-2">Duplicate Variations Detected:</p>
                  <div
                    v-for="variant in auth.variants"
                    :key="variant.id"
                    class="flex flex-col sm:flex-row sm:items-center sm:justify-between p-2.5 lg:p-3 rounded-xl bg-white/[0.02] border border-white/5 gap-2"
                  >
                    <div class="flex items-center gap-2 lg:gap-3 min-w-0">
                      <AlertTriangle :size="12" class="text-amber-500 flex-shrink-0" />
                      <span class="text-sm font-medium text-slate-300">{{ variant.name }}</span>
                      <span class="text-[9px] font-bold text-slate-600 flex-shrink-0">({{ variant.book_count }} books, {{ Math.round(variant.similarity * 100) }}%)</span>
                    </div>
                    <div class="flex items-center gap-3 flex-shrink-0 pl-5 sm:pl-0">
                      <button
                        @click="handleDismissAuthor(auth.primary.id, variant.id)"
                        :disabled="dismissingAuthor === variant.id"
                        class="text-[10px] sm:text-[9px] font-black text-slate-500 uppercase hover:text-rose-400 hover:underline disabled:opacity-50 transition-colors"
                        title="Not the same author"
                      >
                        {{ dismissingAuthor === variant.id ? '...' : 'Not Same' }}
                      </button>
                      <button
                        @click="handleLinkAuthor(auth.primary.id, variant.id)"
                        :disabled="linkingAuthor === variant.id"
                        class="text-[10px] sm:text-[9px] font-black text-indigo-500 uppercase hover:underline disabled:opacity-50"
                      >
                        {{ linkingAuthor === variant.id ? 'Linking...' : 'Link' }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- Actions -->
                <div class="flex gap-3 lg:gap-4">
                  <button
                    @click="router.push(`/authors/${auth.primary.id}`)"
                    class="flex-1 py-3 lg:py-4 rounded-xl lg:rounded-2xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all"
                  >
                    View Bibliography
                  </button>
                </div>
              </div>
            </div>

            <!-- Pagination -->
            <div v-if="authorCandidates.count > 20" class="flex items-center justify-center gap-4 pt-4">
              <button
                :disabled="authorsPage <= 1"
                @click="authorsPage--; fetchAuthorCandidates()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronLeft :size="14" />
              </button>
              <span class="text-xs font-bold text-slate-500">Page {{ authorsPage }} <span class="text-slate-600">of {{ Math.ceil(authorCandidates.count / 20) }}</span></span>
              <button
                :disabled="authorsPage * 20 >= authorCandidates.count"
                @click="authorsPage++; fetchAuthorCandidates()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronRight :size="14" />
              </button>
            </div>

            <!-- Linked Author Groups -->
            <div v-if="authorCandidates.linked_groups?.length > 0" class="mt-8 lg:mt-12">
              <h3 class="text-base lg:text-lg font-black text-white tracking-tight mb-1">Linked <span class="text-indigo-500">Groups</span></h3>
              <p class="text-slate-500 text-xs font-medium mb-4 lg:mb-6">Authors already linked as the same person. Unlink if linked by mistake.</p>

              <div class="space-y-3">
                <div
                  v-for="group in authorCandidates.linked_groups"
                  :key="group.group_id"
                  class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 lg:p-4 rounded-2xl bg-white/[0.02] border border-white/5"
                >
                  <div class="flex items-center gap-3 min-w-0 flex-wrap">
                    <Link2 :size="14" class="text-indigo-500 flex-shrink-0" />
                    <span class="text-sm font-bold text-white truncate">{{ group.canonical_name }}</span>
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span
                        v-for="member in group.members"
                        :key="member.id"
                        class="text-[9px] font-bold px-2 py-0.5 rounded-full border"
                        :class="member.is_primary ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' : 'bg-white/5 border-white/10 text-slate-400'"
                      >
                        {{ member.name }}
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <button
                      v-for="member in group.members.filter(m => !m.is_primary)"
                      :key="'unlink-' + member.id"
                      @click="handleUnlinkAuthor(member.id)"
                      class="text-[9px] font-black text-slate-500 uppercase hover:text-rose-400 hover:underline transition-colors flex items-center gap-1"
                      :title="`Unlink ${member.name}`"
                    >
                      <Unlink :size="10" />
                      {{ member.name }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- ==================== BOOK SYNC TAB ==================== -->
        <div v-if="activeTab === 'bookSync'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <header>
            <h2 class="text-xl lg:text-4xl font-black text-white tracking-tighter uppercase mb-1 lg:mb-2">Book <span class="text-indigo-500">Deduplication</span></h2>
            <p class="text-slate-500 font-medium text-xs lg:text-sm">Detect and merge duplicate book entries across different sources.</p>
          </header>

          <!-- Loading -->
          <div v-if="loading.bookSync" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div v-for="n in 4" :key="n" class="h-64 rounded-[2.5rem] bg-white/[0.03] animate-pulse" />
          </div>

          <template v-else-if="bookCandidates">
            <div v-if="bookCandidates.results.length === 0" class="py-20 text-center">
              <div class="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-4">
                <Check :size="24" class="text-emerald-500" />
              </div>
              <h3 class="text-xl font-black text-white mb-2">All Clear</h3>
              <p class="text-slate-500 text-sm">No duplicate books detected.</p>
            </div>

            <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
              <div
                v-for="pair in bookCandidates.results"
                :key="pair.primary.id"
                class="glass rounded-2xl lg:rounded-[2.5rem] border-white/5 p-6 lg:p-10 space-y-6 group hover:border-indigo-500/20 transition-all"
              >
                <!-- Primary Book -->
                <div class="flex items-center gap-4">
                  <div class="w-10 h-14 rounded-lg bg-slate-900 border border-white/5 flex-shrink-0 overflow-hidden">
                    <img v-if="pair.primary.cover_image" :src="pair.primary.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <BookOpen :size="14" class="text-slate-700" />
                    </div>
                  </div>
                  <div class="min-w-0">
                    <h3 class="text-base lg:text-lg font-black text-white truncate">{{ pair.primary.title }}</h3>
                    <p class="text-[10px] font-bold text-slate-500">{{ pair.primary.author_names || 'No author' }}</p>
                    <div class="flex items-center gap-2 mt-1">
                      <span :class="sourceColor(pair.primary.source)" class="px-1.5 py-0.5 rounded text-[8px]">{{ sourceLabel(pair.primary.source) }}</span>
                      <span v-if="pair.primary.isbn" class="text-[9px] text-slate-600 font-mono">{{ pair.primary.isbn }}</span>
                    </div>
                  </div>
                </div>

                <!-- Variants -->
                <div class="p-4 lg:p-6 rounded-2xl bg-black/40 border border-white/5 space-y-3">
                  <p class="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-2">Potential Duplicates:</p>
                  <div
                    v-for="variant in pair.variants"
                    :key="variant.id"
                    class="flex items-start justify-between gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/5"
                  >
                    <div class="flex items-center gap-3 min-w-0">
                      <div class="w-8 h-11 rounded-md bg-slate-900 border border-white/5 flex-shrink-0 overflow-hidden">
                        <img v-if="variant.cover_image" :src="variant.cover_image" class="w-full h-full object-cover" />
                        <div v-else class="w-full h-full flex items-center justify-center">
                          <BookOpen :size="10" class="text-slate-700" />
                        </div>
                      </div>
                      <div class="min-w-0">
                        <span class="text-sm font-medium text-slate-300 truncate block">{{ variant.title }}</span>
                        <span class="text-[9px] text-slate-500">{{ variant.author_names }} · {{ Math.round(variant.similarity * 100) }}%</span>
                        <div class="flex items-center gap-2 mt-0.5">
                          <span :class="sourceColor(variant.source)" class="px-1 py-0.5 rounded text-[7px]">{{ sourceLabel(variant.source) }}</span>
                          <span v-if="variant.isbn" class="text-[8px] text-slate-600 font-mono">{{ variant.isbn }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="flex items-center gap-2 flex-shrink-0 pt-1">
                      <button
                        @click="handleDismissBook(pair.primary.id, variant.id)"
                        :disabled="dismissingBook === variant.id"
                        class="text-[9px] font-black text-slate-500 uppercase hover:text-rose-400 hover:underline disabled:opacity-50 transition-colors"
                        title="Not the same book"
                      >
                        {{ dismissingBook === variant.id ? '...' : 'Not Same' }}
                      </button>
                      <button
                        @click="handleLinkBook(pair.primary.id, variant.id)"
                        :disabled="linkingBook === variant.id"
                        class="text-[9px] font-black text-indigo-500 uppercase hover:underline disabled:opacity-50"
                      >
                        {{ linkingBook === variant.id ? '...' : 'Link' }}
                      </button>
                      <button
                        @click="handleDeleteBook(variant.id, pair.primary.id)"
                        :disabled="deletingBook === variant.id"
                        class="text-[9px] font-black text-rose-500/60 uppercase hover:text-rose-400 hover:underline disabled:opacity-50 transition-colors"
                        title="Delete this book and transfer data to primary"
                      >
                        <Trash2 :size="11" />
                      </button>
                    </div>
                  </div>
                </div>

                <!-- View Book -->
                <button
                  @click="router.push(`/books/${pair.primary.id}`)"
                  class="w-full py-3 rounded-xl bg-white/5 border border-white/10 text-white font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all"
                >
                  View Book
                </button>
              </div>
            </div>

            <!-- Pagination -->
            <div v-if="bookCandidates.count > 20" class="flex items-center justify-center gap-4 pt-4">
              <button
                :disabled="bookSyncPage <= 1"
                @click="bookSyncPage--; fetchBookCandidates()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronLeft :size="14" />
              </button>
              <span class="text-xs font-bold text-slate-500">Page {{ bookSyncPage }} <span class="text-slate-600">of {{ Math.ceil(bookCandidates.count / 20) }}</span></span>
              <button
                :disabled="bookSyncPage * 20 >= bookCandidates.count"
                @click="bookSyncPage++; fetchBookCandidates()"
                class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
              >
                <ChevronRight :size="14" />
              </button>
            </div>

            <!-- Linked Book Groups -->
            <div v-if="bookCandidates.linked_groups?.length > 0" class="mt-8 lg:mt-12">
              <h3 class="text-base lg:text-lg font-black text-white tracking-tight mb-1">Linked <span class="text-indigo-500">Editions</span></h3>
              <p class="text-slate-500 text-xs font-medium mb-4 lg:mb-6">Books already linked as editions of the same work. Unlink if linked by mistake.</p>

              <div class="space-y-3">
                <div
                  v-for="group in bookCandidates.linked_groups"
                  :key="group.id"
                  class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 lg:p-4 rounded-2xl bg-white/[0.02] border border-white/5"
                >
                  <div class="flex items-center gap-3 min-w-0 flex-wrap">
                    <BookCopy :size="14" class="text-indigo-500 flex-shrink-0" />
                    <span class="text-sm font-bold text-white truncate">{{ group.canonical_title }}</span>
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span
                        v-for="ed in group.editions"
                        :key="ed.id"
                        class="text-[9px] font-bold px-2 py-0.5 rounded-full border"
                        :class="ed.is_primary ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' : 'bg-white/5 border-white/10 text-slate-400'"
                      >
                        {{ ed.title }} <span class="text-slate-600">({{ sourceLabel(ed.source) }})</span>
                      </span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <button
                      v-for="ed in group.editions.filter(e => !e.is_primary)"
                      :key="'unlink-' + ed.id"
                      @click="handleUnlinkBook(ed.id)"
                      class="text-[9px] font-black text-slate-500 uppercase hover:text-rose-400 hover:underline transition-colors flex items-center gap-1"
                      :title="`Unlink ${ed.title}`"
                    >
                      <Unlink :size="10" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

        <!-- ==================== ARCHIVE TAB ==================== -->
        <div v-if="activeTab === 'curation'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div class="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
            <div>
              <h2 class="text-xl lg:text-4xl font-black text-white tracking-tighter uppercase mb-1 lg:mb-2">Digital <span class="text-indigo-500">Archive</span></h2>
              <p class="text-slate-500 font-medium text-xs lg:text-sm">Browse, search, and manage all books in the system.</p>
            </div>
          </div>

          <div class="glass rounded-2xl lg:rounded-[2.5rem] border-white/5 overflow-hidden">
            <!-- Search & Filters -->
            <div class="p-4 lg:p-8 border-b border-white/5 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4 bg-white/[0.02]">
              <div class="flex items-center gap-4 flex-1">
                <Search class="text-slate-600 flex-shrink-0" :size="18" />
                <input
                  v-model="searchQuery"
                  @keyup.enter="handleBookSearch"
                  type="text"
                  placeholder="Search books by title, ISBN, or author..."
                  class="bg-transparent border-none text-white outline-none text-sm w-full"
                />
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-for="f in [
                    { id: 'all', label: 'All Books' },
                    { id: 'missing_data', label: 'Missing Data' },
                    { id: 'recent', label: 'Recent' },
                  ]"
                  :key="f.id"
                  @click="handleBookFilter(f.id)"
                  :class="[
                    'px-3 lg:px-4 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all',
                    bookFilter === f.id
                      ? 'bg-white/10 text-white'
                      : 'text-slate-600 hover:text-slate-400'
                  ]"
                >{{ f.label }}</button>
              </div>
            </div>

            <!-- Loading -->
            <div v-if="loading.books" class="divide-y divide-white/5">
              <div v-for="n in 6" :key="n" class="p-6 flex items-center gap-6">
                <div class="w-10 h-14 rounded bg-white/5 animate-pulse" />
                <div class="flex-1 space-y-2">
                  <div class="h-4 w-1/3 bg-white/5 animate-pulse rounded" />
                  <div class="h-3 w-1/4 bg-white/5 animate-pulse rounded" />
                </div>
              </div>
            </div>

            <!-- Books List -->
            <div v-else-if="books" class="divide-y divide-white/5">
              <div
                v-for="book in books.results"
                :key="book.id"
                @click="navigateToBook(book)"
                class="p-4 lg:p-6 flex items-center justify-between hover:bg-white/[0.02] transition-all cursor-pointer"
              >
                <div class="flex items-center gap-4 lg:gap-6 flex-1 min-w-0">
                  <div class="w-10 h-14 rounded bg-slate-900 border border-white/10 flex-shrink-0 overflow-hidden">
                    <img v-if="book.cover_image" :src="book.cover_image" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <BookOpen :size="12" class="text-slate-700" />
                    </div>
                  </div>
                  <div class="min-w-0">
                    <h4 class="text-sm font-bold text-white truncate">{{ book.title }}</h4>
                    <p class="text-xs text-slate-500 truncate">{{ book.authors?.map(a => a.name).join(', ') || 'No authors' }} • {{ book.publisher || 'Unknown publisher' }}</p>
                  </div>
                </div>
                <div class="hidden md:flex items-center gap-6 lg:gap-12 flex-shrink-0">
                  <div class="text-right">
                    <p class="text-[10px] font-black text-slate-600 uppercase tracking-widest">Source</p>
                    <p :class="[sourceColor(book.source), 'text-xs font-bold px-1.5 py-0.5 rounded inline-block']">{{ sourceLabel(book.source) }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-[10px] font-black text-slate-600 uppercase tracking-widest">Readers</p>
                    <p class="text-xs font-bold text-white">{{ book.readers_count }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-[10px] font-black text-slate-600 uppercase tracking-widest">Quotes</p>
                    <p class="text-xs font-bold text-white">{{ book.quotes_count }}</p>
                  </div>
                  <div v-if="book.book_group_id" class="text-right">
                    <p class="text-[10px] font-black text-slate-600 uppercase tracking-widest">Editions</p>
                    <p class="text-xs font-bold text-indigo-400">Linked</p>
                  </div>
                </div>
              </div>

              <!-- Empty state -->
              <div v-if="books.results.length === 0" class="py-16 text-center">
                <p class="text-slate-500 text-sm">No books found matching your criteria.</p>
              </div>
            </div>

            <!-- Pagination -->
            <div v-if="books && books.total_pages > 1" class="p-4 lg:p-6 border-t border-white/5 flex items-center justify-between">
              <span class="text-xs font-bold text-slate-500">{{ books.count }} books total</span>
              <div class="flex items-center gap-4">
                <button
                  :disabled="booksPage <= 1"
                  @click="booksPage--; fetchBooks()"
                  class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
                >
                  <ChevronLeft :size="14" />
                </button>
                <span class="text-xs font-bold text-slate-500">{{ booksPage }} / {{ books.total_pages }}</span>
                <button
                  :disabled="booksPage >= books.total_pages"
                  @click="booksPage++; fetchBooks()"
                  class="px-4 py-2 rounded-xl bg-white/5 text-slate-400 text-xs font-bold disabled:opacity-30"
                >
                  <ChevronRight :size="14" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================== REPUTATION TAB ==================== -->
        <div v-if="activeTab === 'reputation'" class="space-y-6 lg:space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <header>
            <h2 class="text-xl lg:text-4xl font-black text-white tracking-tighter uppercase mb-1 lg:mb-2">Community <span class="text-amber-500">Reputation</span></h2>
            <p class="text-slate-500 font-medium text-xs lg:text-sm">Contribution tracking, user tiers, and quality metrics.</p>
          </header>

          <!-- Loading -->
          <div v-if="loading.reputation" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div v-for="n in 4" :key="n" class="h-28 rounded-2xl bg-white/[0.03] animate-pulse" />
          </div>

          <template v-else-if="reputationData">
            <!-- Stat Cards -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-2 lg:gap-4">
              <div class="glass rounded-xl lg:rounded-2xl p-3 lg:p-5 border-white/5">
                <div class="flex items-center gap-2 mb-1.5 lg:mb-3">
                  <div class="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <Users :size="12" class="lg:w-3.5 lg:h-3.5 text-amber-400" />
                  </div>
                </div>
                <p class="text-lg lg:text-2xl font-black text-white">{{ reputationData.active_contributors_this_week }}</p>
                <p class="text-[9px] lg:text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5 lg:mt-1">Active This Week</p>
              </div>

              <div class="glass rounded-xl lg:rounded-2xl p-3 lg:p-5 border-white/5">
                <div class="flex items-center gap-2 mb-1.5 lg:mb-3">
                  <div class="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                    <TrendingUp :size="12" class="lg:w-3.5 lg:h-3.5 text-indigo-400" />
                  </div>
                </div>
                <p class="text-lg lg:text-2xl font-black text-white">{{ reputationData.total_contributions_all_time }}</p>
                <p class="text-[9px] lg:text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5 lg:mt-1">Contributions</p>
              </div>

              <div class="glass rounded-xl lg:rounded-2xl p-3 lg:p-5 border-white/5">
                <div class="flex items-center gap-2 mb-1.5 lg:mb-3">
                  <div class="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-rose-500/10 flex items-center justify-center">
                    <ShieldAlert :size="12" class="lg:w-3.5 lg:h-3.5 text-rose-400" />
                  </div>
                </div>
                <p class="text-lg lg:text-2xl font-black text-white">{{ reputationData.flagged_pending }}</p>
                <p class="text-[9px] lg:text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5 lg:mt-1">Flagged</p>
              </div>

              <div class="glass rounded-xl lg:rounded-2xl p-3 lg:p-5 border-white/5">
                <div class="flex items-center gap-2 mb-1.5 lg:mb-3">
                  <div class="w-6 h-6 lg:w-8 lg:h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <Check :size="12" class="lg:w-3.5 lg:h-3.5 text-emerald-400" />
                  </div>
                </div>
                <p class="text-lg lg:text-2xl font-black text-white">{{ Math.round(reputationData.average_quality * 100) }}%</p>
                <p class="text-[9px] lg:text-[10px] font-bold text-slate-500 uppercase tracking-widest mt-0.5 lg:mt-1">Avg Quality</p>
              </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <!-- Top Contributors -->
              <div class="lg:col-span-2 glass rounded-2xl lg:rounded-[2.5rem] p-6 lg:p-10 border-white/5">
                <h3 class="text-lg lg:text-xl font-black text-white tracking-tight uppercase mb-6">Top <span class="text-amber-500">Contributors</span></h3>

                <div v-if="reputationData.top_contributors.length === 0" class="py-12 text-center">
                  <p class="text-slate-500 text-sm">No contributions yet.</p>
                </div>

                <div v-else class="space-y-3">
                  <div
                    v-for="(user, idx) in reputationData.top_contributors"
                    :key="user.user_id"
                    class="flex items-center gap-4 p-3 lg:p-4 rounded-xl bg-white/[0.02] border border-white/5 hover:bg-white/[0.04] transition-all cursor-pointer group"
                    @click="router.push(`/users/${user.user_id}`)"
                  >
                    <!-- Rank -->
                    <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                      :class="idx === 0 ? 'bg-amber-500/20 text-amber-400' : idx === 1 ? 'bg-slate-400/20 text-slate-300' : idx === 2 ? 'bg-orange-500/20 text-orange-400' : 'bg-white/5 text-slate-500'"
                    >
                      <Crown v-if="idx === 0" :size="14" />
                      <span v-else class="text-xs font-black">{{ idx + 1 }}</span>
                    </div>

                    <!-- Avatar -->
                    <div class="w-9 h-9 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center overflow-hidden flex-shrink-0">
                      <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" />
                      <span v-else class="text-xs font-black text-slate-400">{{ user.name?.charAt(0)?.toUpperCase() }}</span>
                    </div>

                    <!-- Info -->
                    <div class="min-w-0 flex-1">
                      <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-white truncate">{{ user.name }}</span>
                        <span :class="[tierColor(user.tier), 'text-[9px] font-black px-2 py-0.5 rounded-full border uppercase']">
                          {{ user.tier_display }}
                        </span>
                      </div>
                      <div class="flex items-center gap-3 mt-0.5">
                        <span class="text-[10px] text-slate-500">{{ user.total_contributions }} contributions</span>
                      </div>
                    </div>

                    <!-- Points -->
                    <div class="text-right flex-shrink-0">
                      <p class="text-sm font-black text-amber-400">{{ user.total_points }}</p>
                      <p class="text-[9px] font-bold text-slate-600 uppercase">points</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Category Breakdown -->
              <div class="glass rounded-2xl lg:rounded-[2.5rem] p-6 lg:p-10 border-white/5">
                <h3 class="text-lg lg:text-xl font-black text-white tracking-tight uppercase mb-6">Category <span class="text-indigo-500">Breakdown</span></h3>

                <div class="space-y-5">
                  <div v-for="cat in [
                    { key: 'content', label: 'Content', color: 'bg-indigo-500' },
                    { key: 'community', label: 'Community', color: 'bg-sky-500' },
                    { key: 'curation', label: 'Curation', color: 'bg-amber-500' },
                    { key: 'reading', label: 'Reading', color: 'bg-emerald-500' },
                  ]" :key="cat.key" class="space-y-2">
                    <div class="flex justify-between text-[10px] font-bold">
                      <span class="text-slate-400 uppercase tracking-widest">{{ cat.label }}</span>
                      <span class="text-white">{{ reputationData.category_breakdown?.[cat.key] || 0 }} pts</span>
                    </div>
                    <div class="h-2 rounded-full bg-white/5 overflow-hidden">
                      <div
                        :class="[cat.color, 'h-full rounded-full transition-all duration-500']"
                        :style="{
                          width: Math.min(100, ((reputationData.category_breakdown?.[cat.key] || 0) / Math.max(1, Math.max(...Object.values(reputationData.category_breakdown || {})))) * 100) + '%'
                        }"
                      />
                    </div>
                  </div>
                </div>

                <!-- Tier Distribution -->
                <div class="mt-8 pt-6 border-t border-white/5">
                  <h4 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Tier Legend</h4>
                  <div class="space-y-2">
                    <div v-for="t in [
                      { tier: 'reader', label: 'Reader', desc: 'Default', pts: '0' },
                      { tier: 'contributor', label: 'Contributor', desc: '50+ pts, 2+ categories', pts: '50' },
                      { tier: 'curator', label: 'Curator', desc: '500+ pts, 10+ curations', pts: '500' },
                      { tier: 'moderator', label: 'Moderator', desc: 'Manual promotion', pts: '—' },
                    ]" :key="t.tier" class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span :class="[tierColor(t.tier), 'text-[9px] font-black px-2 py-0.5 rounded-full border']">{{ t.label }}</span>
                      </div>
                      <span class="text-[9px] text-slate-600">{{ t.pts }} pts</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Recent Activity -->
            <div class="glass rounded-2xl lg:rounded-[2.5rem] p-6 lg:p-10 border-white/5">
              <h3 class="text-lg lg:text-xl font-black text-white tracking-tight uppercase mb-6">Recent <span class="text-indigo-500">Activity</span></h3>

              <div v-if="reputationData.recent_contributions.length === 0" class="py-12 text-center">
                <p class="text-slate-500 text-sm">No contributions recorded yet.</p>
              </div>

              <div v-else class="space-y-2">
                <div
                  v-for="entry in reputationData.recent_contributions"
                  :key="entry.id"
                  class="flex items-center justify-between p-2.5 lg:p-3 rounded-xl bg-white/[0.02] border border-white/5"
                >
                  <div class="flex items-center gap-2 lg:gap-3 min-w-0">
                    <div class="w-6 h-6 lg:w-7 lg:h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                      :class="entry.category === 'curation' ? 'bg-amber-500/10' : entry.category === 'content' ? 'bg-indigo-500/10' : entry.category === 'community' ? 'bg-sky-500/10' : 'bg-emerald-500/10'"
                    >
                      <Star :size="11" :class="entry.category === 'curation' ? 'text-amber-400' : entry.category === 'content' ? 'text-indigo-400' : entry.category === 'community' ? 'text-sky-400' : 'text-emerald-400'" />
                    </div>
                    <div class="min-w-0 truncate">
                      <span class="text-[11px] lg:text-xs font-medium text-slate-300">{{ entry.user_name }}</span>
                      <span class="text-slate-600 mx-1">·</span>
                      <span class="text-[11px] lg:text-xs text-slate-500">{{ entry.action_display }}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 lg:gap-3 flex-shrink-0">
                    <span class="text-[11px] lg:text-xs font-black text-amber-400">+{{ entry.awarded_points }}</span>
                    <span class="text-[8px] lg:text-[9px] text-slate-600 hidden sm:inline">{{ new Date(entry.created_at).toLocaleDateString() }}</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>

      </div>
    </main>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
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
</style>
