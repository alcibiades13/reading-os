<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { useRouter } from 'vue-router'
  import { useUserBooksStore } from '@/stores/userBooksStore'
  import { useBooksStore } from '@/stores/booksStore'
  import {
    Trophy, BookOpen, BarChart3,
    Layers, Plus, Star, Sparkles,
    Library, ChevronRight, Settings, Layout, Trash2,
    X
  } from 'lucide-vue-next'
  import { getBookUrl } from '@/utils/bookUrl'
  
  const router = useRouter()
  const booksStore = useUserBooksStore()
  const bookDetailsStore = useBooksStore() // Dodajemo booksStore za detalje
  
  const activeGoal = ref({ current: 24, total: 50 })
  const customShelves = ref([])
  const selectedBook = ref(null)
  const isBookOpen = ref(false)
  
  // Konstante za kalkulaciju
  const MAX_SHELF_WIDTH = 1200
  const MIN_BOOK_WIDTH = 20
  const MAX_BOOK_WIDTH = 95
  const BOOK_SPACING = 4
  
  const initializeShelves = () => {
    customShelves.value = [
      {
        id: 'all-books',
        title: 'Complete Library',
        type: 'mahogany',
        bookIds: booksStore.books.map(b => b.id)
      },
      {
        id: 'favorites',
        title: 'Philosophy Gems',
        type: 'glass',
        bookIds: booksStore.books.filter(b => b.is_favorite).map(b => b.id)
      },
      {
        id: 'currently-reading',
        title: 'Active Expeditions',
        type: 'oak',
        bookIds: booksStore.books.filter(b => b.status === 'currently_reading').map(b => b.id)
      }
    ]
  }
  
  onMounted(async () => {
    await booksStore.fetchBooks()
    initializeShelves()
  })
  
  watch(() => booksStore.books, () => {
    initializeShelves()
  }, { deep: true })
  
  const stats = computed(() => {
    const totalPages = booksStore.books.reduce((acc, b) => acc + (b.book?.pages || b.book?.pageCount || 0), 0)
    const readBooks = booksStore.books.filter(b => b.status === 'read').length
    return {
      total: booksStore.books.length,
      totalPages,
      readBooks,
      progress: Math.round((readBooks / (booksStore.books.length || 1)) * 100),
      favoriteGenre: 'Science Fiction'
    }
  })
  
  const handleAddShelf = () => {
    const newShelf = {
      id: `shelf-${Date.now()}`,
      title: 'New Collection',
      type: 'minimal',
      bookIds: []
    }
    customShelves.value.push(newShelf)
  }
  
  const handleOpenBook = async (book) => {
    selectedBook.value = book
    
    // Fetch book details if needed
    if (book.book?.id) {
      await bookDetailsStore.fetchBook(book.book.id)
    }
    
    isBookOpen.value = true
  }
  
  const handleCloseBook = () => {
    isBookOpen.value = false
    setTimeout(() => {
      selectedBook.value = null
    }, 300)
  }
  
  const navigateToImporter = () => {
    router.push('/library')
  }
  
  const getShelfBooks = (shelf) => {
    return booksStore.books.filter(b => shelf.bookIds.includes(b.id))
  }
  
  // Funkcija za dobijanje URL-a korica - koristi ISTI format kao u drugoj komponenti
  const getCoverUrl = (book) => {
    if (!book) return ''
    
    // Prvo probaj iz userBook.book objekta
    if (book.book?.cover_image) {
      return book.book.cover_image
    }
    
    // Ako je knjiga već učitana u bookDetailsStore
    const bookDetails = bookDetailsStore.currentBook
    if (bookDetails?.cover_image) {
      return bookDetails.cover_image
    }
    
    // Fallback na placeholder
    const title = book.book?.title || book.title || 'Book'
    return `https://via.placeholder.com/400x600/1E293B/64748B?text=${encodeURIComponent(title.substring(0, 30))}`
  }
  
  // Funkcija za dobijanje naslova
  const getBookTitle = (book) => {
    return book.book?.title || book.title || 'Unknown Book'
  }
  
  // Funkcija za dobijanje autora
  const getBookAuthor = (book) => {
    return book.book?.authors?.[0]?.name || book.book?.author || book.author || 'Unknown Author'
  }
  
  // Funkcija za dobijanje broja strana
  const getBookPages = (book) => {
    return book.book?.pages || book.book?.pageCount || book.pageCount || 250
  }
  
  // Funkcija za izračunavanje širine knjige
  const calculateBookWidth = (book) => {
    const pages = getBookPages(book)
    return Math.max(20, Math.min(95, (pages / 250) * 45))
  }
  
  // Funkcija za izračunavanje visine knjige
  const calculateBookHeight = (book) => {
    const pages = getBookPages(book)
    return Math.max(210, Math.min(270, 230 + (pages / 60)))
  }
  
  // Modifikovana funkcija za grupisanje knjiga po policama
  const getShelfRows = (shelf) => {
    const books = getShelfBooks(shelf)
    const rows = []
    let currentRow = []
    let currentRowWidth = 0
    
    books.forEach((book) => {
      const bookWidth = calculateBookWidth(book)
      const totalWidthWithSpacing = currentRowWidth + bookWidth + 
        (currentRow.length > 0 ? BOOK_SPACING : 0)
      
      if (totalWidthWithSpacing <= MAX_SHELF_WIDTH) {
        currentRow.push(book)
        currentRowWidth = totalWidthWithSpacing
      } else {
        if (currentRow.length > 0) {
          rows.push(currentRow)
        }
        currentRow = [book]
        currentRowWidth = bookWidth
      }
    })
    
    if (currentRow.length > 0) {
      rows.push(currentRow)
    }
    
    return rows.length > 0 ? rows : [[]]
  }
  
  // Generate random spine color for each book
  const getSpineColor = (bookId) => {
    const colors = [
      'from-blue-700 via-blue-800 to-blue-950',
      'from-emerald-700 via-emerald-800 to-emerald-950',
      'from-amber-700 via-amber-800 to-amber-950',
      'from-rose-700 via-rose-800 to-rose-950',
      'from-purple-700 via-purple-800 to-purple-950',
      'from-cyan-700 via-cyan-800 to-cyan-950',
      'from-orange-700 via-orange-800 to-orange-950',
      'from-teal-700 via-teal-800 to-teal-950',
      'from-pink-700 via-pink-800 to-pink-950',
      'from-indigo-700 via-indigo-800 to-indigo-950',
      'from-red-700 via-red-800 to-red-950',
      'from-lime-700 via-lime-800 to-lime-950',
      'from-sky-700 via-sky-800 to-sky-950',
      'from-violet-700 via-violet-800 to-violet-950',
      'from-fuchsia-700 via-fuchsia-800 to-fuchsia-950',
      'from-slate-700 via-slate-800 to-slate-950'
    ]
  
    const idString = String(bookId)
    const hash = idString.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    return colors[hash % colors.length]
  }
  </script>
  
  <template>
    <div class="max-w-7xl mx-auto px-6 py-10 animate-in fade-in duration-1000 relative">
  
      <!-- PREMIUM DASHBOARD -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
        <!-- Reading Goal -->
        <div class="p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] relative overflow-hidden group hover:bg-white/[0.05] transition-all duration-500">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-500">
                <Trophy class="text-amber-400" :size="22" />
              </div>
              <span class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Reading Goal</span>
            </div>
            <p class="text-4xl font-black text-white mb-2 tracking-tighter">{{ activeGoal.current }}/{{ activeGoal.total }}</p>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Books in 2025</p>
  
            <div class="mt-6 w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(99,102,241,0.5)]"
                :style="{ width: `${(activeGoal.current / activeGoal.total) * 100}%` }"
              />
            </div>
          </div>
        </div>
  
        <!-- Library Progress -->
        <div class="p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] relative overflow-hidden group hover:bg-white/[0.05] transition-all duration-500">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-500">
                <BookOpen class="text-indigo-400" :size="22" />
              </div>
              <span class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Library Progress</span>
            </div>
            <p class="text-4xl font-black text-white mb-2 tracking-tighter">{{ stats.progress }}%</p>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Total catalog read</p>
  
            <div class="mt-6 w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
              <div
                class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 shadow-[0_0_12px_rgba(99,102,241,0.5)]"
                :style="{ width: `${stats.progress}%` }"
              />
            </div>
          </div>
        </div>
  
        <!-- Total Pages -->
        <div class="p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] relative overflow-hidden group hover:bg-white/[0.05] transition-all duration-500">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-500">
                <BarChart3 class="text-emerald-400" :size="22" />
              </div>
              <span class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Total Pages</span>
            </div>
            <p class="text-4xl font-black text-white mb-2 tracking-tighter">{{ stats.totalPages.toLocaleString() }}</p>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Physical pages owned</p>
          </div>
        </div>
  
        <!-- Top Genre -->
        <div class="p-8 rounded-[2.5rem] glass border-white/5 bg-white/[0.03] relative overflow-hidden group hover:bg-white/[0.05] transition-all duration-500">
          <div class="relative z-10">
            <div class="flex items-center justify-between mb-6">
              <div class="p-3 rounded-2xl bg-white/5 border border-white/10 group-hover:scale-110 transition-transform duration-500">
                <Sparkles class="text-purple-400" :size="22" />
              </div>
              <span class="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Top Genre</span>
            </div>
            <p class="text-4xl font-black text-white mb-2 tracking-tighter">{{ stats.favoriteGenre }}</p>
            <p class="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Based on your shelf</p>
          </div>
        </div>
      </div>
  
      <!-- HEADER -->
      <div class="flex flex-col md:flex-row items-center justify-between mb-12 gap-6">
        <div>
          <div class="flex items-center gap-2 mb-2">
            <div class="h-px w-8 bg-indigo-500"></div>
            <span class="text-[10px] font-black uppercase tracking-[0.4em] text-indigo-400">Physical Archive</span>
          </div>
          <h2 class="text-5xl font-black text-white tracking-tighter">My <span class="text-indigo-500">Personal</span> Sanctum</h2>
        </div>
  
        <div class="flex items-center gap-4">
          <button
            @click="handleAddShelf"
            class="flex items-center gap-2 px-6 py-4 rounded-2xl bg-white/5 border border-white/10 text-white font-bold text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all"
          >
            <Plus :size="16" /> New Collection
          </button>
          <button
            @click="navigateToImporter"
            class="flex items-center gap-2 px-8 py-4 rounded-2xl bg-indigo-500 text-white font-black text-[10px] uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-2xl shadow-indigo-500/20"
          >
            <Library :size="16" /> Add Volume
          </button>
        </div>
      </div>
  
      <!-- THE SHELVES -->
      <div class="space-y-28 pb-16">
        <div
          v-for="shelf in customShelves"
          :key="shelf.id"
          class="relative"
        >
          <!-- Shelf Labels -->
          <div class="flex items-center justify-between mb-6 px-4">
            <div class="flex items-center gap-4">
              <div class="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
              <h3 class="text-[12px] font-black text-white uppercase tracking-[0.4em]">{{ shelf.title }}</h3>
            </div>
            <div class="flex items-center gap-3">
              <span class="px-4 py-1.5 rounded-full bg-white/5 border border-white/10 text-[9px] font-black text-slate-400 uppercase tracking-widest">
                {{ getShelfBooks(shelf).length }} VOLUMES • {{ getShelfRows(shelf).length }} SHELVES
              </span>
              <button class="p-2 text-slate-600 hover:text-white transition-colors">
                <Settings :size="14" />
              </button>
            </div>
          </div>
  
          <!-- Multiple shelf rows for this shelf -->
          <div
            v-for="(bookRow, rowIndex) in getShelfRows(shelf)"
            :key="`${shelf.id}-row-${rowIndex}`"
            class="relative mb-28 min-h-[280px] perspective-shelf"
          >
            <!-- BOOKS STANDING ON TOP OF THE SHELF -->
            <div class="flex items-end gap-[4px] px-12 absolute bottom-[50px] left-0 right-0 z-20 overflow-visible">
              <div
                v-for="book in bookRow"
                :key="book.id"
                @click="handleOpenBook(book)"
                class="relative group cursor-pointer book-hover-effect flex flex-col items-center transition-all duration-300"
                :style="{ 
                  width: `${calculateBookWidth(book)}px`,
                  filter: selectedBook?.id === book.id && isBookOpen ? 'brightness(0.5)' : 'brightness(1)'
                }"
              >
                <!-- Premium Tooltip -->
                <div class="absolute -top-24 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-50 whitespace-nowrap bg-white text-slate-950 px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-white/20">
                  {{ getBookTitle(book) }}
                  <div class="flex flex-col items-center mt-1">
                    <span class="text-[8px] text-slate-600 font-normal">
                      {{ getBookPages(book) }} pages
                    </span>
                  </div>
                  <div class="absolute bottom-[-6px] left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45" />
                </div>
  
                <!-- The 3D Spine Surface -->
                <div
                  :class="[
                    'w-full relative rounded-t-md border-x border-t border-white/10 group-hover:border-white/30 shadow-[10px_0_30px_rgba(0,0,0,0.4)] overflow-hidden transition-all duration-500',
                    'bg-gradient-to-b',
                    getSpineColor(book.id)
                  ]"
                  :style="{ height: `${calculateBookHeight(book)}px` }"
                >
                  <div class="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-black/20 pointer-events-none" />
  
                  <div class="absolute inset-0 flex items-center justify-center p-3 [writing-mode:vertical-rl] rotate-180 pointer-events-none">
                    <span class="text-[10px] font-black text-white/95 uppercase tracking-[0.2em] line-clamp-1 max-h-[80%] drop-shadow-md">
                      {{ getBookTitle(book) }}
                    </span>
                  </div>
  
                  <div class="absolute top-0 left-0 right-0 h-[3px] bg-white/20 pointer-events-none" />
                  <div class="absolute top-8 left-0 right-0 h-[1px] bg-black/30 pointer-events-none" />
                  <div class="absolute bottom-8 left-0 right-0 h-[1px] bg-black/30 pointer-events-none" />
  
                  <div
                    v-if="book.status === 'currently_reading'"
                    class="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center pointer-events-none"
                  >
                    <div class="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_15px_#818cf8] animate-pulse" />
                  </div>
                </div>
  
                <!-- Contact Shadow on shelf surface -->
                <div class="absolute bottom-0 w-full h-3 bg-black/60 blur-[4px] opacity-40 group-hover:opacity-0 transition-opacity duration-500 pointer-events-none" />
              </div>
            </div>
  
            <!-- 3D SHELF BASE -->
            <div class="absolute bottom-0 left-0 right-0 z-10 h-[50px]">
              <!-- Top Surface -->
              <div
                :class="[
                  'h-[12px] w-full rounded-t-2xl bg-gradient-to-r border-t border-x border-white/10 relative z-20 shadow-[0_-5px_15px_rgba(0,0,0,0.5)]',
                  shelf.type === 'mahogany' ? 'from-amber-900 via-amber-950 to-stone-950 border-white/5 shadow-2xl' : '',
                  shelf.type === 'glass' ? 'from-indigo-500/20 via-white/10 to-indigo-500/20 border-white/20 shadow-xl backdrop-blur-md' : '',
                  shelf.type === 'oak' ? 'from-amber-700/40 via-amber-800/50 to-amber-950/40 border-amber-800/10 shadow-lg' : '',
                  shelf.type === 'minimal' ? 'from-white/5 to-white/[0.02] border-white/10 shadow-md' : ''
                ]"
              >
                <div class="absolute inset-0 bg-white/[0.02] rounded-t-2xl" />
              </div>
              <!-- Front Edge -->
              <div class="h-[38px] w-full rounded-b-2xl bg-gradient-to-b from-black/20 to-black/60 border-x border-b border-white/5 relative z-10 flex items-center justify-center">
                <div class="w-1/3 h-px bg-white/5"></div>
              </div>
            </div>
  
            <div
              v-if="bookRow.length === 0"
              class="absolute inset-0 flex items-center justify-center pointer-events-none opacity-20"
            >
              <p class="text-[9px] font-black uppercase tracking-[1em] text-slate-500">Vacant Workspace</p>
            </div>
          </div>
        </div>
      </div>
  
      <!-- SIMPLE BOOK MODAL -->
      <div
        v-if="selectedBook && isBookOpen"
        class="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/90 backdrop-blur-md"
          @click="handleCloseBook"
        />
  
        <!-- Book Modal Content -->
        <div class="relative z-10 w-full max-w-4xl bg-gradient-to-br from-slate-900 to-slate-950 rounded-3xl border border-slate-800 shadow-2xl overflow-hidden animate-scale-in">
          <!-- Close Button -->
          <button
            @click="handleCloseBook"
            class="absolute top-6 right-6 z-20 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-all backdrop-blur-sm border border-white/20"
          >
            <X :size="20" />
          </button>
  
          <div class="flex flex-col md:flex-row">
            <!-- Book Cover -->
            <div class="md:w-2/5 p-8 md:p-12 flex items-center justify-center bg-gradient-to-br from-slate-800 to-slate-900">
              <div class="w-full max-w-xs">
                <div class="aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl border-4 border-white/10">
                  <img
                    :src="getCoverUrl(selectedBook)"
                    :alt="getBookTitle(selectedBook)"
                    class="w-full h-full object-cover"
                    @error="(e) => e.target.src = `https://via.placeholder.com/400x600/1E293B/64748B?text=${encodeURIComponent(getBookTitle(selectedBook).substring(0, 30))}`"
                  />
                </div>
              </div>
            </div>
  
            <!-- Book Info -->
            <div class="md:w-3/5 p-8 md:p-12">
              <div class="mb-6">
                <div class="flex flex-wrap gap-2 mb-4">
                  <span
                    v-if="selectedBook.status === 'currently_reading'"
                    class="px-3 py-1 bg-emerald-500/20 text-emerald-300 rounded-full text-xs font-bold"
                  >
                    Currently Reading
                  </span>
                  <span
                    v-if="selectedBook.is_favorite"
                    class="px-3 py-1 bg-amber-500/20 text-amber-300 rounded-full text-xs font-bold"
                  >
                    ★ Favorite
                  </span>
                  <span class="px-3 py-1 bg-indigo-500/20 text-indigo-300 rounded-full text-xs font-bold">
                    {{ getBookPages(selectedBook) }} pages
                  </span>
                </div>
  
                <h2 class="text-4xl font-black text-white mb-3">{{ getBookTitle(selectedBook) }}</h2>
                <p class="text-xl text-slate-400 mb-6">{{ getBookAuthor(selectedBook) }}</p>
              </div>
  
              <!-- Book Details -->
              <div class="space-y-6">
                <div class="grid grid-cols-2 gap-4">
                  <div class="bg-slate-800/50 rounded-xl p-4">
                    <p class="text-sm text-slate-400 mb-1">Status</p>
                    <p class="text-lg font-bold text-white capitalize">
                      {{ selectedBook.status?.replace('_', ' ') || 'Not started' }}
                    </p>
                  </div>
                  <div class="bg-slate-800/50 rounded-xl p-4">
                    <p class="text-sm text-slate-400 mb-1">Added</p>
                    <p class="text-lg font-bold text-white">
                      {{ new Date(selectedBook.created_at).toLocaleDateString() }}
                    </p>
                  </div>
                </div>
  
                <!-- Action Buttons -->
                <div class="flex flex-wrap gap-4 pt-4">
                  <button
                    @click="handleCloseBook"
                    class="px-6 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-sm uppercase tracking-widest transition-all backdrop-blur-sm border border-white/20"
                  >
                    BACK TO SHELF
                  </button>
                  <button
                    @click="router.push(getBookUrl(selectedBook.book || selectedBook))"
                    class="px-6 py-3 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white font-bold text-sm uppercase tracking-widest transition-all shadow-lg shadow-indigo-500/25"
                  >
                    OPEN DETAILS
                  </button>
                  <button
                    v-if="selectedBook.status !== 'read'"
                    @click="router.push(`${getBookUrl(selectedBook.book || selectedBook)}/reading`)"
                    class="px-6 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-sm uppercase tracking-widest transition-all shadow-lg shadow-emerald-500/25"
                  >
                    CONTINUE READING
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <style scoped>
  /* Light mode adjustments */
  body.light .text-white {
    color: #0f172a !important;
  }
  
  body.light .text-slate-500 {
    color: #64748b !important;
  }
  
  body.light .text-slate-400 {
    color: #94a3b8 !important;
  }
  
  body.light .bg-white\/\[0\.03\],
  body.light .bg-white\/5 {
    background-color: rgba(255, 255, 255, 0.8) !important;
    border-color: rgba(0, 0, 0, 0.1) !important;
  }
  
  body.light .border-white\/10,
  body.light .border-white\/5 {
    border-color: rgba(0, 0, 0, 0.1) !important;
  }
  
  body.light .bg-slate-800 {
    background: linear-gradient(to bottom, #e2e8f0, #cbd5e1) !important;
  }
  
  body.light .shadow-\[10px_0_30px_rgba\(0\,0\,0\,0\.4\)\] {
    box-shadow: 10px 0 30px rgba(0, 0, 0, 0.15) !important;
  }
  
  /* Optimizacija za veće knjige */
  .book-hover-effect:hover {
    transform: translateY(-5px) scale(1.02);
    transition: transform 0.3s ease;
  }
  
  /* Animation */
  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.9);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }
  
  .animate-scale-in {
    animation: scaleIn 0.3s ease-out forwards;
  }
  </style>