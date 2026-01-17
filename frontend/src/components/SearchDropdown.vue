<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { booksAPI } from '@/services/api'
import { useBookImportStore } from '@/stores/bookImportStore'
import { Search, BookOpen, Plus, Loader2, ExternalLink } from 'lucide-vue-next'

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
    localResults.value = []
    externalResults.value = []
    isOpen.value = false
    return
  }

  isOpen.value = true

  debounceTimeout = setTimeout(async () => {
    await performSearch(newQuery.trim())
  }, 500)
})

const performSearch = async (query) => {
  isLoadingLocal.value = true
  isLoadingExternal.value = true

  // Search local books directly from API
  try {
    const response = await booksAPI.list({ search: query })
    const data = response.data?.results || response.data || []
    localResults.value = Array.isArray(data) ? data.slice(0, 5) : []
  } catch (error) {
    console.error('Local search error:', error)
    localResults.value = []
  } finally {
    isLoadingLocal.value = false
  }

  // Search external APIs
  try {
    await importStore.searchBooks(query)
    externalResults.value = importStore.searchResults.slice(0, 5) // Limit to 5 results
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
  router.push(`/books/${book.id}`)
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

const closeDropdown = () => {
  isOpen.value = false
  localQuery.value = ''
  localResults.value = []
  externalResults.value = []
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
  return localResults.value.length > 0 || externalResults.value.length > 0
})

const isLoading = computed(() => {
  return isLoadingLocal.value || isLoadingExternal.value
})
</script>

<template>
  <div ref="dropdownRef" class="relative flex-1 max-w-2xl">
    <div class="relative group">
      <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-indigo-500 transition-colors" :size="18" />
      <input
        ref="inputRef"
        v-model="localQuery"
        type="text"
        placeholder="Search across the entire library..."
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
      <!-- Local Books Section -->
      <div v-if="localResults.length > 0 || isLoadingLocal" class="p-4 border-b border-slate-800/50">
        <div class="flex items-center gap-2 mb-3">
          <BookOpen :size="16" class="text-indigo-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Your Library</h3>
        </div>

        <div v-if="isLoadingLocal" class="space-y-2">
          <div v-for="n in 3" :key="n" class="flex gap-3 p-2 rounded-lg animate-pulse">
            <div class="w-12 h-16 bg-slate-800 rounded"></div>
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-slate-800 rounded w-3/4"></div>
              <div class="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
          </div>
        </div>

        <div v-else class="space-y-1">
          <button
            v-for="book in localResults"
            :key="book.id"
            @click="viewLocalBook(book)"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors text-left group"
          >
            <div class="w-12 h-16 bg-slate-800 rounded overflow-hidden flex-shrink-0 border border-slate-700/50">
              <img
                v-if="book.cover_image"
                :src="book.cover_image"
                :alt="book.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
                <BookOpen :size="16" class="text-slate-600" />
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

      <!-- External Books Section -->
      <div v-if="externalResults.length > 0 || isLoadingExternal" class="p-4">
        <div class="flex items-center gap-2 mb-3">
          <ExternalLink :size="16" class="text-emerald-400" />
          <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Import from Library</h3>
        </div>

        <div v-if="isLoadingExternal" class="space-y-2">
          <div v-for="n in 3" :key="n" class="flex gap-3 p-2 rounded-lg animate-pulse">
            <div class="w-12 h-16 bg-slate-800 rounded"></div>
            <div class="flex-1 space-y-2">
              <div class="h-4 bg-slate-800 rounded w-3/4"></div>
              <div class="h-3 bg-slate-800 rounded w-1/2"></div>
            </div>
          </div>
        </div>

        <div v-else class="space-y-1">
          <div
            v-for="(book, index) in externalResults"
            :key="book.google_books_id || book.open_library_id || `ext-${index}`"
            class="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-slate-800/50 transition-colors group cursor-pointer"
            @click="viewExternalBook(book)"
          >
            <div class="w-12 h-16 bg-slate-800 rounded overflow-hidden flex-shrink-0 border border-slate-700/50">
              <img
                v-if="book.cover_image_url"
                :src="book.cover_image_url"
                :alt="book.title"
                class="w-full h-full object-cover"
              />
              <div v-else class="w-full h-full flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
                <BookOpen :size="16" class="text-slate-600" />
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
        <p class="text-sm font-semibold text-slate-400 mb-1">No books found</p>
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
