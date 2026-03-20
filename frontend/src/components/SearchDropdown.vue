<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { booksAPI, quotesAPI, vocabularyAPI, socialAPI, authorsAPI } from '@/services/api'
import { useBookImportStore } from '@/stores/bookImportStore'
import { getBookUrl } from '@/utils/bookUrl'
import { getAuthorUrl } from '@/utils/authorUrl'
import { Search, BookOpen, Plus, ExternalLink, Quote, Brain, User, Feather } from 'lucide-vue-next'

const props = defineProps({
  searchQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:searchQuery'])

const router = useRouter()
const importStore = useBookImportStore()

const localQuery = ref(props.searchQuery)
const isOpen = ref(false)
const isLoadingLocal = ref(false)
const isLoadingExternal = ref(false)
const localResults = ref([])
const externalResults = ref([])
const quoteResults = ref([])
const authorResults = ref([])
const vocabularyResults = ref([])
const userResults = ref([])
const dropdownRef = ref(null)
const inputRef = ref(null)

let debounceTimeout = null

// Watch for prop changes
watch(() => props.searchQuery, (newVal) => {
  localQuery.value = newVal
})

// Debounced search
watch(localQuery, (newQuery) => {
  emit('update:searchQuery', newQuery)

  clearTimeout(debounceTimeout)

  if (!newQuery || newQuery.trim().length < 2) {
    clearAllResults()
    isOpen.value = false
    return
  }

  isOpen.value = true

  debounceTimeout = setTimeout(async () => {
    await performSearch(newQuery.trim())
  }, 500)
})

const clearAllResults = () => {
  localResults.value = []
  externalResults.value = []
  quoteResults.value = []
  authorResults.value = []
  vocabularyResults.value = []
  userResults.value = []
}

const performSearch = async (query) => {
  isLoadingLocal.value = true
  isLoadingExternal.value = true

  // Run all searches in parallel
  const [booksRes, quotesRes, authorsRes, vocabRes, usersRes] = await Promise.allSettled([
    booksAPI.list({ search: query }),
    quotesAPI.list({ search: query, page_size: 5 }),
    authorsAPI.list({ search: query, page_size: 5 }),
    vocabularyAPI.list({ search: query, page_size: 5 }),
    socialAPI.searchUsers(query),
  ])

  // Process books
  if (booksRes.status === 'fulfilled') {
    const data = booksRes.value.data?.results || booksRes.value.data || []
    localResults.value = Array.isArray(data) ? data.slice(0, 5) : []
  } else {
    localResults.value = []
  }

  // Process quotes
  if (quotesRes.status === 'fulfilled') {
    const data = quotesRes.value.data?.results || quotesRes.value.data || []
    quoteResults.value = Array.isArray(data) ? data.slice(0, 3) : []
  } else {
    quoteResults.value = []
  }

  // Process authors
  if (authorsRes.status === 'fulfilled') {
    const data = authorsRes.value.data?.results || authorsRes.value.data || []
    authorResults.value = Array.isArray(data) ? data.slice(0, 3) : []
  } else {
    authorResults.value = []
  }

  // Process vocabulary
  if (vocabRes.status === 'fulfilled') {
    const data = vocabRes.value.data?.results || vocabRes.value.data || []
    vocabularyResults.value = Array.isArray(data) ? data.slice(0, 3) : []
  } else {
    vocabularyResults.value = []
  }

  // Process users
  if (usersRes.status === 'fulfilled') {
    const data = usersRes.value.data?.results || usersRes.value.data || []
    userResults.value = Array.isArray(data) ? data.slice(0, 3) : []
  } else {
    userResults.value = []
  }

  isLoadingLocal.value = false

  // Search external APIs
  try {
    await importStore.searchBooks(query)
    externalResults.value = importStore.searchResults.slice(0, 5)
  } catch (error) {
    console.error('External search error:', error)
    externalResults.value = []
  } finally {
    isLoadingExternal.value = false
  }
}

const getAuthorsString = (book) => {
  if (book.authors && Array.isArray(book.authors)) {
    return book.authors.map(a => typeof a === 'string' ? a : a.name).join(', ')
  }
  return 'Unknown Author'
}

const viewLocalBook = (book) => {
  router.push(getBookUrl(book))
  closeDropdown()
}

const viewExternalBook = (book) => {
  importStore.selectBook(book)
  router.push('/import')
  closeDropdown()
}

const importExternalBook = (book, event) => {
  event.stopPropagation()
  importStore.selectBook(book)
  router.push('/import')
  closeDropdown()
}

const viewQuote = () => {
  router.push('/quotes')
  closeDropdown()
}

const viewAuthor = (author) => {
  router.push(getAuthorUrl(author))
  closeDropdown()
}

const viewVocabulary = () => {
  router.push('/vocabulary')
  closeDropdown()
}

const viewUser = (user) => {
  router.push(`/users/${user.id}`)
  closeDropdown()
}

const closeDropdown = () => {
  isOpen.value = false
  localQuery.value = ''
  clearAllResults()
}

const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    closeDropdown()
  }
}

const handleFocus = () => {
  if (localQuery.value && localQuery.value.trim().length >= 2) {
    isOpen.value = true
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const hasAnyResults = computed(() => {
  return localResults.value.length > 0 ||
    externalResults.value.length > 0 ||
    quoteResults.value.length > 0 ||
    authorResults.value.length > 0 ||
    vocabularyResults.value.length > 0 ||
    userResults.value.length > 0
})

const isLoading = computed(() => {
  return isLoadingLocal.value || isLoadingExternal.value
})

const truncateText = (text, max = 80) => {
  if (!text || text.length <= max) return text
  return text.substring(0, max) + '...'
}

const getUserName = (user) => {
  if (user.first_name || user.last_name) {
    return `${user.first_name || ''} ${user.last_name || ''}`.trim()
  }
  return user.email?.split('@')[0] || 'User'
}
</script>

<template>
  <div ref="dropdownRef" class="relative flex-1 max-w-2xl">
    <div class="relative group">
      <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" :size="18" />
      <input
        ref="inputRef"
        v-model="localQuery"
        type="text"
        placeholder="Search books, quotes, authors, people..."
        @focus="handleFocus"
        class="w-full bg-white/5 border border-slate-800/50 rounded-2xl pl-12 pr-4 py-2.5 text-sm text-slate-50 outline-none focus:border-indigo-500 transition-all placeholder-slate-600"
      />
      <div class="absolute right-4 top-1/2 -translate-y-1/2 hidden md:flex items-center gap-1 px-2 py-0.5 rounded-lg bg-white/5 border border-slate-800/50 text-[9px] font-black text-slate-500 uppercase tracking-widest">
        Cmd + K
      </div>
    </div>

    <!-- Dropdown Results -->
    <div
      v-if="isOpen && (hasAnyResults || isLoading)"
      class="absolute top-full left-0 right-0 mt-2 bg-slate-900/95 backdrop-blur-xl border border-slate-800/50 rounded-2xl shadow-2xl max-h-[70vh] overflow-y-auto custom-scrollbar z-50"
    >
      <!-- Loading skeleton -->
      <div v-if="isLoadingLocal && !hasAnyResults" class="p-4">
        <div class="space-y-2">
          <div v-for="n in 3" :key="n" class="flex gap-3 p-2 rounded-lg animate-pulse">
            <div class="w-10 h-10 bg-slate-800 rounded-lg"></div>
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-slate-800 rounded w-3/4"></div>
              <div class="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Local Books Section -->
      <div v-if="localResults.length > 0" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <BookOpen :size="14" class="text-indigo-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Your Library</h3>
        </div>

        <div class="space-y-1">
          <button
            v-for="book in localResults"
            :key="book.id"
            @click="viewLocalBook(book)"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-10 h-14 bg-slate-800 rounded overflow-hidden flex-shrink-0 border border-slate-700/50">
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <BookOpen :size="14" class="text-slate-600" />
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-white truncate group-hover:text-indigo-400 transition-colors">
                {{ book.title }}
              </h4>
              <p class="text-xs text-slate-400 truncate">
                {{ getAuthorsString(book) }}
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- Quotes Section -->
      <div v-if="quoteResults.length > 0" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <Quote :size="14" class="text-amber-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Quotes</h3>
        </div>

        <div class="space-y-1">
          <button
            v-for="quote in quoteResults"
            :key="quote.id"
            @click="viewQuote"
            class="w-full flex items-start gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
              <Quote :size="12" class="text-amber-400" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-sm text-slate-300 leading-snug group-hover:text-amber-300 transition-colors">
                "{{ truncateText(quote.text, 100) }}"
              </p>
              <p class="text-xs text-slate-500 mt-1">
                {{ quote.book_title || (quote.book && quote.book.title) || 'Unknown book' }}
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- Authors Section -->
      <div v-if="authorResults.length > 0" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <Feather :size="14" class="text-purple-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Authors</h3>
        </div>

        <div class="space-y-1">
          <button
            v-for="author in authorResults"
            :key="author.id"
            @click="viewAuthor(author)"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center flex-shrink-0">
              <Feather :size="12" class="text-purple-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-white truncate group-hover:text-purple-400 transition-colors">
                {{ author.name }}
              </h4>
              <p v-if="author.books_count" class="text-xs text-slate-500">
                {{ author.books_count }} book{{ author.books_count !== 1 ? 's' : '' }}
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- Vocabulary Section -->
      <div v-if="vocabularyResults.length > 0" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <Brain :size="14" class="text-emerald-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Vocabulary</h3>
        </div>

        <div class="space-y-1">
          <button
            v-for="word in vocabularyResults"
            :key="word.id"
            @click="viewVocabulary"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
              <Brain :size="12" class="text-emerald-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-white group-hover:text-emerald-400 transition-colors">
                {{ word.word }}
              </h4>
              <p class="text-xs text-slate-500 truncate">
                {{ truncateText(word.definition, 60) }}
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- Users Section -->
      <div v-if="userResults.length > 0" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <User :size="14" class="text-sky-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">People</h3>
        </div>

        <div class="space-y-1">
          <button
            v-for="user in userResults"
            :key="user.id"
            @click="viewUser(user)"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-8 h-8 rounded-full bg-sky-500/10 flex items-center justify-center flex-shrink-0 overflow-hidden">
              <img v-if="user.avatar" :src="user.avatar" class="w-full h-full object-cover" />
              <User v-else :size="12" class="text-sky-400" />
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-white truncate group-hover:text-sky-400 transition-colors">
                {{ getUserName(user) }}
              </h4>
              <p v-if="user.books_read_count" class="text-xs text-slate-500">
                {{ user.books_read_count }} books read
              </p>
            </div>
          </button>
        </div>
      </div>

      <!-- External Books Section -->
      <div v-if="externalResults.length > 0" class="p-4">
        <div class="flex items-center gap-2 mb-3">
          <ExternalLink :size="14" class="text-slate-500" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Import from Library</h3>
        </div>

        <div class="space-y-1">
          <div
            v-for="(book, index) in externalResults"
            :key="book.google_books_id || book.open_library_id || `ext-${index}`"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors group cursor-pointer"
            @click="viewExternalBook(book)"
          >
            <div class="w-10 h-14 bg-slate-800 rounded overflow-hidden flex-shrink-0 border border-slate-700/50">
              <img
                v-if="book.cover_image_url"
                :src="book.cover_image_url"
                :alt="book.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <BookOpen :size="14" class="text-slate-600" />
              </div>
            </div>
            <div class="flex-1 min-w-0">
              <h4 class="text-sm font-semibold text-white truncate group-hover:text-emerald-400 transition-colors">
                {{ book.title }}
              </h4>
              <p class="text-xs text-slate-400 truncate">
                {{ getAuthorsString(book) }}
              </p>
            </div>
            <button
              @click.stop="importExternalBook(book, $event)"
              class="px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold hover:bg-emerald-500 hover:text-white transition-all duration-300 flex items-center gap-1.5 flex-shrink-0 opacity-0 group-hover:opacity-100"
            >
              <Plus :size="14" />
              Import
            </button>
          </div>
        </div>
      </div>

      <!-- No Results Message -->
      <div v-if="!isLoading && !hasAnyResults && localQuery.trim().length >= 2" class="p-8 text-center">
        <div class="w-16 h-16 rounded-full bg-slate-800/50 border border-slate-700/50 flex items-center justify-center mx-auto mb-4">
          <Search :size="24" class="text-slate-600" />
        </div>
        <p class="text-sm font-semibold text-slate-400 mb-1">Nothing found</p>
        <p class="text-xs text-slate-500">Try a different search term</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgb(15 23 42);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgb(51 65 85);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgb(71 85 105);
}
</style>
