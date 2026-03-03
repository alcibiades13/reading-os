<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  Library,
  Quote,
  Brain,
  Sparkles,
  PenTool,
  CircleDot,
  Trophy,
  Compass,
  BookOpen,
  Feather,
  MessageSquare,
  ArrowRight,
  ChevronDown,
  Dna,
  Heart,
  Users,
  Lightbulb,
  Star,
  BookMarked,
  Search,
  Play,
  Layers,
  TrendingUp,
  Shield,
  Bookmark,
  Hash,
  BarChart3,
  Cpu,
  Check
} from 'lucide-vue-next'

const router = useRouter()

// Scroll-based reveal
const revealedSections = ref(new Set())
let observer = null

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          revealedSections.value.add(entry.target.dataset.section)
          revealedSections.value = new Set(revealedSections.value)
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  )
  document.querySelectorAll('[data-section]').forEach((el) => observer.observe(el))
})

onUnmounted(() => observer?.disconnect())

const isRevealed = (id) => revealedSections.value.has(id)

const scrollToContent = () => {
  document.getElementById('showcase')?.scrollIntoView({ behavior: 'smooth' })
}

// Active feature tab
const activeTab = ref('vault')

const tabs = [
  { id: 'vault', label: 'Vault', icon: Library },
  { id: 'quotes', label: 'Quotes', icon: Quote },
  { id: 'lexicon', label: 'Lexicon', icon: Brain },
  { id: 'dna', label: 'Book DNA', icon: Dna },
  { id: 'circles', label: 'Circles', icon: CircleDot },
  { id: 'codex', label: 'Codex', icon: PenTool },
]

const tabContent = {
  vault: {
    title: 'Your entire reading life, in one place',
    description: 'Track every book — read, reading, or wishlist. Rate with precision, write reviews, manage editions, and see your library grow over time. Grid or list view, your choice.',
    features: ['Reading status & progress tracking', 'Half-star ratings (0.5–10)', 'Physical shelf & wishlist', 'Smart filtering & search'],
    mockup: 'vault'
  },
  quotes: {
    title: 'The passages that stopped you mid-sentence',
    description: 'Save quotes with page numbers, chapters, and personal notes. Tag them with custom colours. Design beautiful quote cards and share them with the world.',
    features: ['Page & chapter references', 'Colour-coded custom tags', 'Quote card designer', 'CSV, JSON & image export'],
    mockup: 'quotes'
  },
  lexicon: {
    title: 'Every book teaches you new words',
    description: 'Capture vocabulary as you read. Track mastery from "new" to "understood". Export to Anki for spaced repetition. Build a lexicon that grows with every book.',
    features: ['New → Learning → Mastered stages', 'Context & example sentences', 'Anki card export', 'Favourites & book links'],
    mockup: 'lexicon'
  },
  dna: {
    title: 'Books are more than their genre',
    description: 'Six dimensions map how a book feels — its pace, complexity, emotional weight, darkness, character focus, and introspection. Your taste profile emerges naturally over time.',
    features: ['Six-axis book profiling', 'Community-driven voting', 'Taste evolution tracking', 'DNA-based recommendations'],
    mockup: 'dna'
  },
  circles: {
    title: 'Read together, at your own pace',
    description: 'Create reading circles with friends. Discuss chapters with spoiler protection that unlocks based on each member\'s progress. Polls, events, and structured topics.',
    features: ['Progress-based spoiler locks', 'Discussion categories & topics', 'Reading progress tracking', 'Polls, events & reactions'],
    mockup: 'circles'
  },
  codex: {
    title: 'Where readers become writers',
    description: 'A personal journal with mood tracking — contemplative, inspired, energetic. A manuscript workspace with chapters and word count goals. Reading and writing, connected.',
    features: ['Journal with 5 mood types', 'Manuscript chapters', 'Word count goals', 'Shareable via link'],
    mockup: 'codex'
  },
}

const currentTab = computed(() => tabContent[activeTab.value])
</script>

<template>
  <div class="landing-page min-h-screen bg-slate-950 text-slate-50 overflow-x-hidden">

    <!-- ===== NAVBAR ===== -->
    <nav class="fixed top-0 left-0 right-0 z-50 px-6 sm:px-10 lg:px-16 py-4 bg-slate-950/80 backdrop-blur-xl border-b border-white/[0.04]">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <BookOpen :size="16" class="text-white" />
          </div>
          <span class="font-black text-lg tracking-tight">Marginalia</span>
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="router.push('/login')"
            class="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-white/5"
          >
            Sign in
          </button>
          <button
            @click="router.push('/register')"
            class="px-5 py-2 text-sm font-semibold bg-indigo-500 hover:bg-indigo-400 text-white rounded-lg transition-all shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30"
          >
            Get Started
          </button>
        </div>
      </div>
    </nav>


    <!-- ===== HERO ===== -->
    <section class="relative min-h-screen flex items-center pt-20 overflow-hidden">
      <!-- Background -->
      <div class="absolute inset-0">
        <div class="absolute top-[-10%] left-[-5%] w-[50%] h-[50%] bg-indigo-900/25 blur-[160px] rounded-full" />
        <div class="absolute bottom-[10%] right-[-10%] w-[40%] h-[50%] bg-purple-900/15 blur-[140px] rounded-full" />
        <div class="absolute inset-0 opacity-[0.015]" style="background-image: radial-gradient(circle at 1px 1px, rgba(255,255,255,0.4) 1px, transparent 0); background-size: 40px 40px;" />
      </div>

      <div class="relative z-10 max-w-7xl mx-auto px-6 sm:px-10 lg:px-16 w-full grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center">
        <!-- Left: Copy -->
        <div>
          <div class="mb-6">
            <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-400">
              <Feather :size="11" />
              For thoughtful readers
            </span>
          </div>

          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black leading-[1.08] mb-6 tracking-tight">
            A place where your
            <span class="bg-gradient-to-r from-indigo-400 via-purple-400 to-sky-400 bg-clip-text text-transparent">reading lives.</span>
          </h1>

          <p class="text-base sm:text-lg text-slate-400 leading-relaxed max-w-md mb-8">
            Save the passages that move you. Track the words you discover.
            Discuss ideas with others who care. Let every book leave a trace.
          </p>

          <div class="flex flex-wrap items-center gap-3 mb-10">
            <button
              @click="router.push('/register')"
              class="group px-7 py-3 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 flex items-center gap-2 text-sm"
            >
              Start for free
              <ArrowRight :size="15" class="group-hover:translate-x-0.5 transition-transform" />
            </button>
            <button
              @click="scrollToContent"
              class="group px-7 py-3 text-slate-300 font-medium rounded-lg border border-slate-700 hover:border-slate-500 transition-all flex items-center gap-2 text-sm hover:bg-white/[0.03]"
            >
              <Play :size="14" class="text-indigo-400" />
              See how it works
            </button>
          </div>

          <!-- Mini stats -->
          <div class="flex items-center gap-6 text-xs text-slate-500">
            <div class="flex items-center gap-1.5">
              <Check :size="13" class="text-emerald-400" />
              Free to use
            </div>
            <div class="flex items-center gap-1.5">
              <Check :size="13" class="text-emerald-400" />
              No ads, ever
            </div>
            <div class="flex items-center gap-1.5">
              <Check :size="13" class="text-emerald-400" />
              Import from Goodreads
            </div>
          </div>
        </div>

        <!-- Right: App Mockup -->
        <div class="relative hidden lg:block">
          <div class="relative">
            <!-- Glow behind mockup -->
            <div class="absolute -inset-8 bg-indigo-500/10 blur-[60px] rounded-3xl" />

            <!-- Main mockup card -->
            <div class="relative rounded-2xl border border-slate-700/50 bg-slate-900/80 backdrop-blur-sm shadow-2xl overflow-hidden">
              <!-- Mockup header -->
              <div class="flex items-center gap-2 px-4 py-3 border-b border-slate-800/60">
                <div class="flex gap-1.5">
                  <div class="w-2.5 h-2.5 rounded-full bg-red-500/60" />
                  <div class="w-2.5 h-2.5 rounded-full bg-amber-500/60" />
                  <div class="w-2.5 h-2.5 rounded-full bg-emerald-500/60" />
                </div>
                <div class="flex-1 flex justify-center">
                  <div class="px-3 py-0.5 rounded bg-slate-800/60 text-[10px] text-slate-500">marginalia.app</div>
                </div>
              </div>

              <!-- Mockup body - Library view -->
              <div class="p-5 space-y-4">
                <!-- Sidebar + content layout -->
                <div class="flex gap-4">
                  <!-- Mini sidebar -->
                  <div class="w-10 space-y-3 flex-shrink-0">
                    <div class="w-7 h-7 rounded bg-indigo-500 mx-auto flex items-center justify-center">
                      <BookOpen :size="12" class="text-white" />
                    </div>
                    <div class="space-y-2 flex flex-col items-center">
                      <div class="w-5 h-5 rounded bg-slate-800 flex items-center justify-center">
                        <Library :size="10" class="text-indigo-400" />
                      </div>
                      <div class="w-5 h-5 rounded bg-slate-800/50 flex items-center justify-center">
                        <Quote :size="10" class="text-slate-500" />
                      </div>
                      <div class="w-5 h-5 rounded bg-slate-800/50 flex items-center justify-center">
                        <Brain :size="10" class="text-slate-500" />
                      </div>
                      <div class="w-5 h-5 rounded bg-slate-800/50 flex items-center justify-center">
                        <CircleDot :size="10" class="text-slate-500" />
                      </div>
                    </div>
                  </div>

                  <!-- Content area -->
                  <div class="flex-1 space-y-3">
                    <!-- Header row -->
                    <div class="flex items-center justify-between">
                      <div class="text-xs font-bold text-slate-200">My Library</div>
                      <div class="flex gap-1">
                        <div class="px-2 py-0.5 rounded text-[9px] bg-indigo-500/20 text-indigo-400 font-semibold">All</div>
                        <div class="px-2 py-0.5 rounded text-[9px] text-slate-500">Reading</div>
                        <div class="px-2 py-0.5 rounded text-[9px] text-slate-500">Finished</div>
                      </div>
                    </div>

                    <!-- Book grid -->
                    <div class="grid grid-cols-4 gap-2">
                      <div v-for="n in 8" :key="n" class="space-y-1.5">
                        <div
                          class="aspect-[2/3] rounded-md"
                          :class="[
                            n === 1 ? 'bg-gradient-to-br from-indigo-600 to-indigo-900' :
                            n === 2 ? 'bg-gradient-to-br from-emerald-600 to-emerald-900' :
                            n === 3 ? 'bg-gradient-to-br from-amber-600 to-amber-900' :
                            n === 4 ? 'bg-gradient-to-br from-rose-600 to-rose-900' :
                            n === 5 ? 'bg-gradient-to-br from-sky-600 to-sky-900' :
                            n === 6 ? 'bg-gradient-to-br from-purple-600 to-purple-900' :
                            n === 7 ? 'bg-gradient-to-br from-teal-600 to-teal-900' :
                            'bg-gradient-to-br from-orange-600 to-orange-900'
                          ]"
                        >
                          <div class="p-2 h-full flex flex-col justify-between">
                            <div class="w-full h-1 rounded bg-white/20" />
                            <div class="space-y-0.5">
                              <div class="w-3/4 h-0.5 rounded bg-white/15" />
                              <div class="w-1/2 h-0.5 rounded bg-white/10" />
                            </div>
                          </div>
                        </div>
                        <!-- Star rating -->
                        <div class="flex gap-px justify-center">
                          <Star v-for="s in 5" :key="s" :size="6" class="text-amber-400/60" :class="s <= (n % 3 + 3) ? 'fill-amber-400/60' : ''" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Floating quote card -->
            <div class="absolute -bottom-6 -left-8 w-56 rounded-xl border border-indigo-500/30 bg-slate-900/95 backdrop-blur-md p-4 shadow-2xl shadow-indigo-500/10 rotate-[-2deg]">
              <div class="flex items-center gap-1.5 mb-2">
                <Quote :size="10" class="text-indigo-400" />
                <span class="text-[9px] font-bold text-indigo-400 uppercase tracking-wider">Saved Quote</span>
              </div>
              <p class="text-[11px] text-slate-300 italic leading-relaxed mb-2">"One must still have chaos in oneself to give birth to a dancing star."</p>
              <p class="text-[9px] text-slate-500">— Nietzsche, <span class="text-slate-400">Thus Spoke Zarathustra</span></p>
            </div>

            <!-- Floating DNA card -->
            <div class="absolute -top-4 -right-6 w-48 rounded-xl border border-purple-500/30 bg-slate-900/95 backdrop-blur-md p-3 shadow-2xl shadow-purple-500/10 rotate-[3deg]">
              <div class="flex items-center gap-1.5 mb-2.5">
                <Dna :size="10" class="text-purple-400" />
                <span class="text-[9px] font-bold text-purple-400 uppercase tracking-wider">Book DNA</span>
              </div>
              <div class="space-y-2">
                <div v-for="bar in [
                  { label: 'Pace', value: 35, color: 'from-indigo-500 to-purple-500' },
                  { label: 'Complexity', value: 72, color: 'from-purple-500 to-pink-500' },
                  { label: 'Emotional', value: 85, color: 'from-pink-500 to-rose-500' },
                ]" :key="bar.label" class="space-y-0.5">
                  <div class="text-[8px] text-slate-500 font-medium">{{ bar.label }}</div>
                  <div class="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-gradient-to-r transition-all duration-1000" :class="bar.color" :style="{ width: bar.value + '%' }" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Scroll indicator -->
      <div class="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 animate-bounce opacity-30">
        <span class="text-[10px] uppercase tracking-widest text-slate-500">Scroll</span>
        <ChevronDown :size="16" />
      </div>
    </section>


    <!-- ===== VISUAL DIVIDER ===== -->
    <div class="relative h-px max-w-5xl mx-auto">
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-indigo-500/30 to-transparent" />
    </div>


    <!-- ===== FEATURE SHOWCASE WITH TABS ===== -->
    <section
      id="showcase"
      data-section="showcase"
      :class="['relative py-20 sm:py-28 px-6 transition-all duration-700', isRevealed('showcase') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']"
    >
      <div class="max-w-7xl mx-auto">
        <!-- Section header -->
        <div class="text-center mb-12">
          <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-400 mb-5">
            <Layers :size="11" />
            Everything you need
          </span>
          <h2 class="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight mb-4">
            Built for deep readers
          </h2>
          <p class="text-slate-500 max-w-lg mx-auto text-sm sm:text-base">
            Not just tracking — understanding, preserving, and sharing what you read.
          </p>
        </div>

        <!-- Tab navigation -->
        <div class="flex flex-wrap justify-center gap-2 mb-12">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              'flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all duration-300',
              activeTab === tab.id
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/25'
                : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent hover:border-slate-700'
            ]"
          >
            <component :is="tab.icon" :size="15" />
            {{ tab.label }}
          </button>
        </div>

        <!-- Tab content -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 items-center">
          <!-- Left: Info -->
          <div :key="activeTab" class="tab-content-enter">
            <h3 class="text-2xl sm:text-3xl font-bold mb-4 tracking-tight">
              {{ currentTab.title }}
            </h3>
            <p class="text-slate-400 leading-relaxed mb-8">
              {{ currentTab.description }}
            </p>
            <div class="space-y-3">
              <div
                v-for="feature in currentTab.features"
                :key="feature"
                class="flex items-center gap-3"
              >
                <div class="w-5 h-5 rounded-md bg-indigo-500/15 flex items-center justify-center flex-shrink-0">
                  <Check :size="11" class="text-indigo-400" />
                </div>
                <span class="text-sm text-slate-300">{{ feature }}</span>
              </div>
            </div>
          </div>

          <!-- Right: Mockup -->
          <div :key="activeTab + '-mock'" class="tab-content-enter">
            <!-- Vault mockup -->
            <div v-if="activeTab === 'vault'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Library :size="16" class="text-indigo-400" />
                  <span class="text-sm font-bold">My Vault</span>
                </div>
                <div class="flex gap-1">
                  <div class="px-2.5 py-1 rounded-md text-[10px] bg-indigo-500 text-white font-bold">All · 47</div>
                  <div class="px-2.5 py-1 rounded-md text-[10px] text-slate-400 bg-slate-800/60 font-medium">Reading · 3</div>
                  <div class="px-2.5 py-1 rounded-md text-[10px] text-slate-400 bg-slate-800/60 font-medium">Read · 31</div>
                </div>
              </div>
              <div class="grid grid-cols-5 gap-3">
                <div v-for="(book, idx) in [
                  { color: 'from-indigo-500 to-blue-700', rating: 9 },
                  { color: 'from-emerald-500 to-teal-700', rating: 8.5 },
                  { color: 'from-amber-500 to-orange-700', rating: 7 },
                  { color: 'from-rose-500 to-red-700', rating: 9.5 },
                  { color: 'from-purple-500 to-violet-700', rating: 8 },
                ]" :key="idx" class="space-y-2">
                  <div :class="'aspect-[2/3] rounded-lg bg-gradient-to-br ' + book.color + ' shadow-lg'" />
                  <div class="flex items-center gap-0.5 justify-center">
                    <Star :size="8" class="text-amber-400 fill-amber-400" />
                    <span class="text-[10px] text-slate-400 font-bold">{{ book.rating }}</span>
                  </div>
                </div>
              </div>
              <div class="flex items-center gap-4 pt-2 border-t border-slate-800/60">
                <div class="flex items-center gap-1.5 text-[10px] text-slate-500">
                  <BookMarked :size="11" class="text-emerald-400" />
                  <span><b class="text-slate-300">31</b> finished</span>
                </div>
                <div class="flex items-center gap-1.5 text-[10px] text-slate-500">
                  <TrendingUp :size="11" class="text-sky-400" />
                  <span><b class="text-slate-300">8,420</b> pages this year</span>
                </div>
              </div>
            </div>

            <!-- Quotes mockup -->
            <div v-else-if="activeTab === 'quotes'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Quote :size="16" class="text-indigo-400" />
                  <span class="text-sm font-bold">Commonplace</span>
                </div>
                <div class="flex gap-1.5">
                  <span class="px-2 py-0.5 rounded-full text-[9px] font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/20">Philosophy</span>
                  <span class="px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/20">Wisdom</span>
                  <span class="px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">Life</span>
                </div>
              </div>
              <div class="space-y-3">
                <div v-for="(q, qi) in [
                  { text: 'The only true wisdom is in knowing you know nothing.', author: 'Socrates', book: 'Apology', page: 42 },
                  { text: 'Until you make the unconscious conscious, it will direct your life and you will call it fate.', author: 'Carl Jung', book: 'Aion', page: 167 },
                  { text: 'He who has a why to live can bear almost any how.', author: 'Nietzsche', book: 'Twilight of the Idols', page: 33 },
                ]" :key="qi" class="rounded-xl bg-slate-800/40 p-4 border border-slate-700/30 hover:border-indigo-500/20 transition-colors">
                  <p class="text-xs text-slate-200 italic leading-relaxed mb-2">"{{ q.text }}"</p>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] text-indigo-400 font-semibold">— {{ q.author }}</span>
                    <span class="text-[9px] text-slate-600">p. {{ q.page }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Lexicon mockup -->
            <div v-else-if="activeTab === 'lexicon'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <Brain :size="16" class="text-emerald-400" />
                  <span class="text-sm font-bold">Lexicon</span>
                  <span class="text-[10px] text-slate-500">142 words</span>
                </div>
              </div>
              <div class="space-y-2.5">
                <div v-for="(word, wi) in [
                  { term: 'Saudade', def: 'A deep emotional state of melancholic longing for something absent', stage: 'Mastered', stageColor: 'text-emerald-400 bg-emerald-500/15', book: 'The Book of Disquiet' },
                  { term: 'Eudaimonia', def: 'Human flourishing or well-being; the highest human good', stage: 'Learning', stageColor: 'text-amber-400 bg-amber-500/15', book: 'Nicomachean Ethics' },
                  { term: 'Apophenia', def: 'The tendency to perceive meaningful connections between unrelated things', stage: 'New', stageColor: 'text-sky-400 bg-sky-500/15', book: 'The Unbearable Lightness of Being' },
                ]" :key="wi" class="rounded-xl bg-slate-800/40 p-4 border border-slate-700/30">
                  <div class="flex items-center justify-between mb-1.5">
                    <span class="text-sm font-bold text-slate-200">{{ word.term }}</span>
                    <span :class="'text-[9px] font-bold px-2 py-0.5 rounded-full ' + word.stageColor">{{ word.stage }}</span>
                  </div>
                  <p class="text-[11px] text-slate-400 leading-relaxed mb-1.5">{{ word.def }}</p>
                  <span class="text-[9px] text-slate-600">from <span class="text-slate-500">{{ word.book }}</span></span>
                </div>
              </div>
            </div>

            <!-- DNA mockup -->
            <div v-else-if="activeTab === 'dna'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-5">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <Dna :size="16" class="text-purple-400" />
                  <span class="text-sm font-bold">Book DNA</span>
                </div>
                <span class="text-[10px] text-slate-500">Based on 24 votes</span>
              </div>
              <div class="space-y-4">
                <div v-for="attr in [
                  { left: 'Contemplative', right: 'Page-turner', value: 30 },
                  { left: 'Accessible', right: 'Dense', value: 72 },
                  { left: 'Light', right: 'Intense', value: 85 },
                  { left: 'Hopeful', right: 'Bleak', value: 40 },
                  { left: 'Plot-driven', right: 'Character', value: 68 },
                  { left: 'Action', right: 'Introspective', value: 90 },
                ]" :key="attr.left" class="space-y-1">
                  <div class="flex justify-between text-[10px]">
                    <span class="text-slate-500">{{ attr.left }}</span>
                    <span class="text-slate-500">{{ attr.right }}</span>
                  </div>
                  <div class="relative h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      class="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-1000 ease-out"
                      :style="{ width: isRevealed('showcase') ? attr.value + '%' : '0%' }"
                    />
                    <div
                      class="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-white shadow-md border-2 border-indigo-500 transition-all duration-1000 ease-out"
                      :style="{ left: isRevealed('showcase') ? `calc(${attr.value}% - 6px)` : '0%' }"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- Circles mockup -->
            <div v-else-if="activeTab === 'circles'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-4">
              <div class="flex items-center gap-3 mb-2">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-black">PC</div>
                <div>
                  <div class="text-sm font-bold">Philosophy Circle</div>
                  <div class="text-[10px] text-slate-500">6 members · Reading: <span class="text-indigo-400">Meditations</span></div>
                </div>
              </div>
              <div class="space-y-2.5">
                <div class="rounded-xl bg-slate-800/40 p-3 border border-slate-700/30">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-[8px] text-emerald-400 font-bold">AK</div>
                    <span class="text-[10px] font-semibold text-slate-300">Ana K.</span>
                    <span class="text-[9px] text-slate-600">2h ago</span>
                  </div>
                  <p class="text-[11px] text-slate-400 leading-relaxed">Book IV is where Marcus really shifts from self-discipline to acceptance. The "river of time" metaphor changed how I see impermanence.</p>
                  <div class="flex items-center gap-2 mt-2">
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">❤️ 3</span>
                    <span class="text-[9px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-500">💡 1</span>
                  </div>
                </div>
                <div class="rounded-xl bg-amber-500/5 border border-amber-500/20 p-3 flex items-center gap-2">
                  <Shield :size="14" class="text-amber-400 flex-shrink-0" />
                  <p class="text-[10px] text-amber-400/80">Spoiler protection active — unlock at 60% progress</p>
                </div>
              </div>
            </div>

            <!-- Codex mockup -->
            <div v-else-if="activeTab === 'codex'" class="rounded-2xl border border-slate-700/50 bg-slate-900/60 p-6 space-y-4">
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2">
                  <PenTool :size="16" class="text-indigo-400" />
                  <span class="text-sm font-bold">Codex</span>
                </div>
                <div class="flex gap-1.5">
                  <span class="px-2.5 py-1 rounded-md text-[10px] bg-indigo-500 text-white font-bold">Journal</span>
                  <span class="px-2.5 py-1 rounded-md text-[10px] text-slate-400 bg-slate-800/60 font-medium">Manuscripts</span>
                </div>
              </div>
              <div class="rounded-xl bg-slate-800/40 border border-slate-700/30 p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold text-slate-200">February 28, 2026</span>
                  <span class="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/15 text-purple-400 font-medium">contemplative</span>
                </div>
                <p class="text-[11px] text-slate-400 leading-relaxed">
                  Finished rereading Stoner today. What strikes me this time is not the sadness — it's the quiet dignity.
                  Williams makes an argument that a life fully felt, even if small, carries meaning that outlasts everything...
                </p>
                <div class="flex items-center gap-3 pt-2 border-t border-slate-700/20">
                  <div class="flex items-center gap-1 text-[9px] text-slate-500">
                    <Bookmark :size="9" class="text-indigo-400" />
                    <span>Linked: <span class="text-slate-400">Stoner</span></span>
                  </div>
                </div>
              </div>
              <div class="rounded-xl bg-slate-800/20 border border-slate-700/20 p-3 flex items-center gap-3">
                <div class="w-8 h-10 rounded bg-gradient-to-br from-indigo-500/30 to-purple-500/30 flex items-center justify-center">
                  <Feather :size="12" class="text-indigo-400" />
                </div>
                <div class="flex-1">
                  <div class="text-[11px] font-bold text-slate-300">Reflections on Solitude</div>
                  <div class="text-[9px] text-slate-500">Manuscript · 12,400 / 30,000 words</div>
                </div>
                <div class="w-12 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div class="h-full w-[41%] rounded-full bg-indigo-500" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- ===== VISUAL DIVIDER ===== -->
    <div class="relative h-px max-w-5xl mx-auto">
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-purple-500/20 to-transparent" />
    </div>


    <!-- ===== NUMBERED FEATURES — ALTERNATING LAYOUT ===== -->
    <section
      data-section="numbered"
      :class="['relative py-20 sm:py-28 px-6 transition-all duration-700', isRevealed('numbered') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']"
    >
      <div class="max-w-6xl mx-auto space-y-20 sm:space-y-28">

        <!-- Feature 01: Commonplace -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-20 items-center">
          <div class="order-2 lg:order-1">
            <!-- Mini mockup -->
            <div class="rounded-2xl border border-slate-700/40 bg-slate-900/40 p-5 space-y-3">
              <div class="flex items-center gap-2 mb-1">
                <div class="w-3 h-3 rounded bg-indigo-500" />
                <div class="h-1.5 w-20 rounded bg-slate-700" />
              </div>
              <div v-for="n in 3" :key="n" class="rounded-lg bg-slate-800/50 p-3 border-l-2 border-indigo-500/40">
                <div class="h-1.5 w-full rounded bg-slate-700/60 mb-2" />
                <div class="h-1.5 w-4/5 rounded bg-slate-700/40 mb-2" />
                <div class="h-1.5 w-2/3 rounded bg-slate-700/30" />
                <div class="flex items-center gap-2 mt-3">
                  <div class="h-1 w-8 rounded bg-indigo-500/30" />
                  <div class="h-1 w-12 rounded bg-purple-500/30" />
                </div>
              </div>
              <p class="text-[11px] text-slate-600 italic text-center pt-2">"The ink flow of the digital age..."</p>
            </div>
          </div>
          <div class="order-1 lg:order-2">
            <div class="flex items-baseline gap-4 mb-4">
              <span class="text-5xl font-black text-indigo-500/20">01</span>
              <h3 class="text-2xl sm:text-3xl font-black tracking-tight">Commonplace Book</h3>
            </div>
            <p class="text-slate-400 leading-relaxed mb-6">
              The ancient practice, digitally reborn. Save passages from every book you read.
              Tag them by theme, mood, or whatever system makes sense to you.
              Design beautiful quote cards. Build your personal anthology.
            </p>
            <div class="flex flex-wrap gap-2">
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Quote :size="12" class="text-indigo-400" /> Quotes
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Hash :size="12" class="text-indigo-400" /> Tags
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Sparkles :size="12" class="text-indigo-400" /> Card Designer
              </span>
            </div>
          </div>
        </div>

        <!-- Feature 02: Reading Circles -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-20 items-center">
          <div>
            <div class="flex items-baseline gap-4 mb-4">
              <span class="text-5xl font-black text-purple-500/20">02</span>
              <h3 class="text-2xl sm:text-3xl font-black tracking-tight">Reading Circles</h3>
            </div>
            <p class="text-slate-400 leading-relaxed mb-6">
              Create intimate reading groups. Discuss chapters without spoilers — topics unlock
              based on each member's reading progress. Share reactions, run polls, set milestones.
              A book club that actually works.
            </p>
            <div class="flex flex-wrap gap-2">
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Shield :size="12" class="text-purple-400" /> Spoiler Protection
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <MessageSquare :size="12" class="text-purple-400" /> Discussions
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <BarChart3 :size="12" class="text-purple-400" /> Polls
              </span>
            </div>
          </div>
          <div>
            <!-- Circle mockup -->
            <div class="rounded-2xl border border-slate-700/40 bg-slate-900/40 p-5 space-y-3">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-[10px] text-white font-black">LC</div>
                <div>
                  <div class="text-xs font-bold">Literary Conversations</div>
                  <div class="text-[9px] text-slate-500">8 members · 3 unread</div>
                </div>
              </div>
              <div class="space-y-2">
                <div class="flex items-center gap-2 p-2 rounded-lg bg-white/[0.03] border border-white/[0.04]">
                  <MessageSquare :size="12" class="text-slate-500" />
                  <span class="text-[10px] text-slate-400 flex-1">Chapter 5 — The turning point</span>
                  <span class="text-[9px] text-indigo-400 font-bold">12 replies</span>
                </div>
                <div class="flex items-center gap-2 p-2 rounded-lg bg-white/[0.03] border border-white/[0.04]">
                  <MessageSquare :size="12" class="text-slate-500" />
                  <span class="text-[10px] text-slate-400 flex-1">Favourite quotes so far?</span>
                  <span class="text-[9px] text-indigo-400 font-bold">8 replies</span>
                </div>
                <div class="flex items-center gap-2 p-2 rounded-lg bg-amber-500/5 border border-amber-500/15">
                  <Shield :size="12" class="text-amber-400" />
                  <span class="text-[10px] text-amber-400/70 flex-1">Ending discussion</span>
                  <span class="text-[9px] text-amber-400/50 font-bold">🔒 80%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Feature 03: Intelligence & Discovery -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-20 items-center">
          <div class="order-2 lg:order-1">
            <!-- Discovery mockup -->
            <div class="rounded-2xl border border-slate-700/40 bg-slate-900/40 p-5 space-y-4">
              <div class="flex items-center gap-2">
                <Compass :size="14" class="text-sky-400" />
                <span class="text-xs font-bold">Discover</span>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <div v-for="(rec, ri) in [
                  { color: 'from-cyan-600 to-blue-800', match: '94%' },
                  { color: 'from-violet-600 to-purple-800', match: '89%' },
                  { color: 'from-rose-600 to-pink-800', match: '86%' },
                ]" :key="ri" class="space-y-1.5">
                  <div :class="'aspect-[2/3] rounded-lg bg-gradient-to-br ' + rec.color" />
                  <div class="flex items-center justify-center gap-1">
                    <Dna :size="8" class="text-indigo-400" />
                    <span class="text-[9px] font-bold text-indigo-400">{{ rec.match }} match</span>
                  </div>
                </div>
              </div>
              <div class="rounded-lg bg-slate-800/30 p-3 border border-slate-700/20">
                <div class="text-[9px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Why this matches</div>
                <div class="flex flex-wrap gap-1">
                  <span class="px-1.5 py-0.5 rounded text-[8px] bg-indigo-500/15 text-indigo-400">High introspection</span>
                  <span class="px-1.5 py-0.5 rounded text-[8px] bg-purple-500/15 text-purple-400">Dense complexity</span>
                  <span class="px-1.5 py-0.5 rounded text-[8px] bg-pink-500/15 text-pink-400">Emotional depth</span>
                </div>
              </div>
            </div>
          </div>
          <div class="order-1 lg:order-2">
            <div class="flex items-baseline gap-4 mb-4">
              <span class="text-5xl font-black text-sky-500/20">03</span>
              <h3 class="text-2xl sm:text-3xl font-black tracking-tight">Intelligence & Discovery</h3>
            </div>
            <p class="text-slate-400 leading-relaxed mb-6">
              AI that connects themes across your reading. DNA-based recommendations
              that understand <em>why</em> you loved a book, not just that you rated it highly.
              Discover by feeling — contemplative, intense, philosophical — not by genre alone.
            </p>
            <div class="flex flex-wrap gap-2">
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Cpu :size="12" class="text-sky-400" /> AI Insights
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <Dna :size="12" class="text-sky-400" /> DNA Matching
              </span>
              <span class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800/60 text-slate-400 border border-slate-700/40 flex items-center gap-1.5">
                <TrendingUp :size="12" class="text-sky-400" /> Taste Evolution
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>


    <!-- ===== VISUAL DIVIDER ===== -->
    <div class="relative h-px max-w-5xl mx-auto">
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-slate-700/50 to-transparent" />
    </div>


    <!-- ===== MORE FEATURES GRID ===== -->
    <section
      data-section="more"
      :class="['relative py-20 sm:py-28 px-6 transition-all duration-700', isRevealed('more') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']"
    >
      <div class="max-w-6xl mx-auto">
        <h2 class="text-2xl sm:text-3xl font-black tracking-tight text-center mb-12">And so much more</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
          <div v-for="item in [
            { icon: Trophy, label: 'Reading Challenges', desc: 'Set goals by count, genre, or pages', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
            { icon: MessageSquare, label: 'Correspondence', desc: 'Private messages with book attachments', color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
            { icon: Lightbulb, label: 'Study Notes', desc: 'Notes, questions, insights per book', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
            { icon: Layers, label: 'Reading Lists', desc: 'Curated lists, manual or smart', color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20' },
            { icon: Users, label: 'Social Feed', desc: 'See what friends are reading', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
            { icon: Star, label: 'Reviews', desc: 'Write and read community reviews', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
            { icon: Search, label: 'Book Search', desc: 'Multi-source: Google, OpenLibrary, Hardcover', color: 'text-sky-400 bg-sky-500/10 border-sky-500/20' },
            { icon: Heart, label: 'Contributions', desc: 'Earn reputation, badges, and tiers', color: 'text-rose-400 bg-rose-500/10 border-rose-500/20' },
          ]" :key="item.label" class="group rounded-xl border border-slate-800/50 bg-slate-900/30 p-4 hover:border-slate-700 transition-all hover:bg-slate-900/50">
            <div :class="'w-9 h-9 rounded-lg border flex items-center justify-center mb-3 ' + item.color">
              <component :is="item.icon" :size="16" />
            </div>
            <h4 class="text-xs font-bold mb-1">{{ item.label }}</h4>
            <p class="text-[10px] text-slate-500 leading-relaxed">{{ item.desc }}</p>
          </div>
        </div>
      </div>
    </section>


    <!-- ===== FINAL CTA ===== -->
    <section
      data-section="cta"
      :class="['relative py-24 sm:py-32 px-6 overflow-hidden transition-all duration-700', isRevealed('cta') ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8']"
    >
      <div class="absolute inset-0">
        <div class="absolute bottom-[-20%] left-[10%] w-[70%] h-[70%] bg-indigo-900/20 blur-[160px] rounded-full" />
      </div>

      <div class="relative max-w-3xl mx-auto text-center">
        <div class="w-14 h-14 rounded-2xl bg-indigo-500 flex items-center justify-center shadow-2xl shadow-indigo-500/30 mx-auto mb-8">
          <BookOpen :size="24" class="text-white" />
        </div>
        <h2 class="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight mb-5">
          Your reading deserves
          <span class="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">a place to live.</span>
        </h2>
        <p class="text-slate-400 leading-relaxed max-w-md mx-auto mb-8">
          Join Marginalia and start building your personal reading archive.
          Free. No ads. No tracking. Just you and your books.
        </p>
        <div class="flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            @click="router.push('/register')"
            class="group px-8 py-3.5 bg-indigo-500 hover:bg-indigo-400 text-white font-semibold rounded-lg transition-all shadow-xl shadow-indigo-500/25 hover:shadow-indigo-500/40 flex items-center gap-2"
          >
            Get Started — it's free
            <ArrowRight :size="16" class="group-hover:translate-x-0.5 transition-transform" />
          </button>
          <button
            @click="router.push('/login')"
            class="px-8 py-3.5 text-slate-400 hover:text-white font-medium rounded-lg border border-slate-700 hover:border-slate-500 transition-all"
          >
            I have an account
          </button>
        </div>
      </div>
    </section>


    <!-- ===== FOOTER ===== -->
    <footer class="border-t border-slate-800/40 py-10 px-6">
      <div class="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="flex items-center gap-2.5">
          <div class="w-6 h-6 rounded bg-indigo-500/20 flex items-center justify-center">
            <BookOpen :size="12" class="text-indigo-400" />
          </div>
          <span class="font-bold text-xs text-slate-500">Marginalia</span>
        </div>
        <p class="text-slate-600 text-[11px]">A place where your reading lives.</p>
        <div class="flex items-center gap-4 text-xs text-slate-500">
          <button @click="router.push('/login')" class="hover:text-slate-300 transition-colors">Sign in</button>
          <button @click="router.push('/register')" class="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">Get started</button>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.landing-page {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background-color: #0f172a !important;
  color: #f8fafc !important;
}

/* Tab content enter animation */
.tab-content-enter {
  animation: tabEnter 0.4s ease-out;
}

@keyframes tabEnter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
