<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { recommendationsAPI, userBooksAPI, quotesAPI, vocabularyAPI } from '@/services/api'
import { GoogleGenAI } from '@google/genai'
import {
  Sparkles, Brain, Send, Mic, ShieldCheck,
  BookOpen, Network
} from 'lucide-vue-next'

const STORAGE_KEY = 'intelligence_chat'

// Chat state
const messages = ref([])
const inputText = ref('')
const isProcessing = ref(false)
const chatContainerRef = ref(null)
const latency = ref(null)

// Context state
const libraryContext = ref(null)
const contextLoading = ref(true)

// Gemini client (module-level, not reactive — avoids Vue proxy issues with SDK)
let geminiAI = null

// Load persisted chat
const loadChat = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) messages.value = JSON.parse(saved)
  } catch { /* ignore corrupt data */ }
}

const saveChat = () => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages.value))
  } catch { /* storage full */ }
}

const clearChat = () => {
  messages.value = []
  latency.value = null
  localStorage.removeItem(STORAGE_KEY)
}

onMounted(async () => {
  loadChat()
  initializeGemini()
  await fetchLibraryContext()
})

// Auto-scroll on new messages + persist
watch(messages, async () => {
  await nextTick()
  if (chatContainerRef.value) {
    chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
  }
  saveChat()
}, { deep: true })

const initializeGemini = () => {
  const apiKey = import.meta.env.VITE_GEMINI_API_KEY
  if (!apiKey) {
    console.error('VITE_GEMINI_API_KEY is not set')
    return
  }
  geminiAI = new GoogleGenAI({ apiKey })
}

const fetchLibraryContext = async () => {
  contextLoading.value = true
  try {
    const [tasteRes, booksRes, quotesRes, vocabRes] = await Promise.all([
      recommendationsAPI.getReadingTaste('all'),
      userBooksAPI.list({ page_size: 20, ordering: '-updated_at' }),
      quotesAPI.list({ page_size: 500, ordering: '-created_at' }),
      vocabularyAPI.list({ page_size: 500, ordering: '-created_at' }),
    ])

    libraryContext.value = {
      taste: tasteRes.data,
      books: booksRes.data.results || booksRes.data,
      quotes: quotesRes.data.results || quotesRes.data,
      vocabulary: vocabRes.data.results || vocabRes.data,
    }
  } catch (error) {
    console.error('Error fetching library context:', error)
    libraryContext.value = { taste: null, books: [], quotes: [], vocabulary: [] }
  } finally {
    contextLoading.value = false
  }
}

const buildSystemPrompt = () => {
  const ctx = libraryContext.value
  if (!ctx) return 'You are a sophisticated literary advisor. Always respond in the same language the user writes in. Default to English.'

  let prompt = `You are a sophisticated literary advisor and intellectual companion for the app "Marginalia" — a personal reading tracker.

CRITICAL: Always respond in the same language the user writes in. If they write in Serbian, respond in Serbian (Latin script). If they write in English, respond in English. Default to English.

Here is context about the user's library:

`

  if (ctx.taste) {
    const t = ctx.taste
    if (t.books_count) prompt += `Total books: ${t.books_count}\n`
    if (t.top_genres?.length) prompt += `Favorite genres: ${t.top_genres.slice(0, 5).map(g => g.name || g).join(', ')}\n`
    if (t.top_authors?.length) prompt += `Favorite authors: ${t.top_authors.slice(0, 5).map(a => a.name || a).join(', ')}\n`
    if (t.top_themes?.length) prompt += `Key themes: ${t.top_themes.slice(0, 5).map(th => th.name || th).join(', ')}\n`
  }

  if (ctx.books?.length) {
    prompt += `\nRecent books:\n`
    ctx.books.slice(0, 10).forEach(ub => {
      const b = ub.book || ub
      const status = ub.status === 'currently_reading' ? '(reading)' :
                     ub.status === 'read' ? '(finished)' : ''
      const rating = ub.rating ? ` ★${ub.rating}` : ''
      const authors = b.authors?.map(a => a.name).join(', ') || ''
      prompt += `- ${b.title}${authors ? ' — ' + authors : ''}${rating} ${status}\n`
    })
  }

  if (ctx.quotes?.length) {
    prompt += `\nUser's saved quotes (${ctx.quotes.length} total):\n`
    ctx.quotes.forEach(q => {
      const text = q.text || ''
      const book = q.book_title || q.book?.title || ''
      prompt += `- "${text}" — ${book}\n`
    })
  }

  if (ctx.vocabulary?.length) {
    prompt += `\nVocabulary words the user is learning:\n`
    ctx.vocabulary.forEach(v => {
      const word = v.word || ''
      const definition = v.definition ? ` — ${v.definition.slice(0, 80)}` : ''
      const book = v.book_title || v.book?.title || ''
      const source = book ? ` (from: ${book})` : ''
      prompt += `- ${word}${definition}${source}\n`
    })
  }

  prompt += `\nRules:
- Match the user's language. Detect which language they write in and respond in the same one.
- Use an intellectual, analytical tone. Reference the user's library and reading habits when relevant.
- Be concise but thorough. Use markdown formatting for structure.
- You can recommend books, analyze themes, and provide insights about reading patterns.
- You have access to the user's vocabulary words — use them when asked about vocabulary.`

  return prompt
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isProcessing.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  isProcessing.value = true

  const startTime = Date.now()

  try {
    if (!geminiAI) throw new Error('Gemini not initialized — check API key')

    // Build conversation history for multi-turn
    const history = messages.value.slice(0, -1).map(m => ({
      role: m.role === 'user' ? 'user' : 'model',
      parts: [{ text: m.content }],
    }))

    const response = await geminiAI.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: [
        ...history,
        { role: 'user', parts: [{ text }] },
      ],
      config: {
        systemInstruction: buildSystemPrompt(),
        maxOutputTokens: 8192,
        temperature: 0.7,
      },
    })

    latency.value = Date.now() - startTime

    messages.value.push({
      role: 'ai',
      content: response.text || 'No response generated.',
    })
  } catch (error) {
    console.error('Gemini error:', error)
    messages.value.push({
      role: 'ai',
      content: 'An error occurred while processing your request. Please check your API key and internet connection.',
    })
  } finally {
    isProcessing.value = false
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

const handleSuggestion = (text) => {
  inputText.value = text
  sendMessage()
}

const formatMarkdown = (text) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-white">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
}

const booksCount = computed(() => libraryContext.value?.taste?.books_count || 0)
const hasMessages = computed(() => messages.value.length > 0)
const latencyDisplay = computed(() => {
  if (!latency.value) return null
  return latency.value < 1000
    ? `${latency.value}ms`
    : `${(latency.value / 1000).toFixed(1)}s`
})
</script>

<template>
  <div class="h-full flex flex-col relative overflow-hidden">

    <!-- Background Neural Animation -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <div class="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-indigo-500/10 blur-[120px] rounded-full animate-pulse" />
      <div class="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-500/10 blur-[120px] rounded-full animate-pulse" style="animation-delay: 2s" />
    </div>

    <!-- Header -->
    <header class="flex-shrink-0 border-b border-slate-800/50 glass relative z-10">
      <div class="px-4 lg:px-6 py-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-fuchsia-500 p-0.5">
              <div class="w-full h-full rounded-xl bg-slate-900 flex items-center justify-center">
                <Sparkles :size="16" class="text-white animate-pulse" />
              </div>
            </div>
            <div>
              <h1 class="text-base font-black text-white tracking-tight uppercase">Intelligence</h1>
              <div class="flex items-center gap-2">
                <span class="text-[8px] font-black text-slate-500 uppercase tracking-[0.3em]">Core Synthesis v4.2</span>
                <div class="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-[7px] font-black text-emerald-400 uppercase tracking-wider">Free Tier</div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <div class="hidden lg:flex items-center gap-4 mr-2 text-right">
              <div>
                <p class="text-[7px] font-black text-slate-500 uppercase tracking-widest">Model</p>
                <p class="text-xs font-black text-white">Gemini Flash</p>
              </div>
              <div v-if="latencyDisplay">
                <p class="text-[7px] font-black text-slate-500 uppercase tracking-widest">Latency</p>
                <p class="text-xs font-black text-white">{{ latencyDisplay }}</p>
              </div>
            </div>
            <button
              v-if="hasMessages"
              @click="clearChat"
              class="px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/10 text-[10px] font-bold text-slate-400 hover:text-white transition-all"
            >
              Clear
            </button>
            <div class="relative group">
              <button class="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-400 hover:text-white transition-all">
                <ShieldCheck :size="15" />
              </button>
              <div class="absolute top-full mt-2 right-0 w-48 p-3 glass rounded-xl border border-white/5 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-[100] text-[10px] text-slate-400 leading-relaxed shadow-xl">
                Your data stays in your browser. Only reading context is sent to Google Gemini.
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Chat Area -->
    <main ref="chatContainerRef" class="flex-1 overflow-y-auto custom-scrollbar relative z-10">
      <div class="px-4 lg:px-6 py-4">

        <!-- Empty State -->
        <div v-if="!hasMessages" class="py-10 text-center space-y-4 animate-in fade-in duration-1000">
          <div class="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mx-auto">
            <Brain :size="28" class="text-indigo-400" />
          </div>
          <h2 class="text-2xl font-black text-white tracking-tighter">What shall we synthesize today?</h2>
          <p class="text-sm text-slate-500 max-w-md mx-auto">
            <template v-if="booksCount">{{ booksCount }} books indexed.</template>
            Ask about connections, themes, or recommendations.
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left max-w-lg mx-auto pt-2">
            <button
              @click="handleSuggestion('Connect the Stoic philosophy with modern habit-building concepts from my library.')"
              class="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-indigo-500/30 hover:bg-white/10 transition-all text-left flex items-center gap-3 group"
            >
              <div class="p-2 rounded-lg bg-slate-800 text-slate-500 group-hover:text-indigo-400 transition-colors flex-shrink-0">
                <Network :size="14" />
              </div>
              <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">Connect Stoicism with habit-building</span>
            </button>
            <button
              @click="handleSuggestion('Analyze my reading patterns and tell me what kind of reader I am based on my library.')"
              class="p-3 rounded-xl bg-white/5 border border-white/5 hover:border-indigo-500/30 hover:bg-white/10 transition-all text-left flex items-center gap-3 group"
            >
              <div class="p-2 rounded-lg bg-slate-800 text-slate-500 group-hover:text-indigo-400 transition-colors flex-shrink-0">
                <BookOpen :size="14" />
              </div>
              <span class="text-xs font-bold text-slate-400 group-hover:text-white transition-colors">Analyze my reading patterns</span>
            </button>
          </div>
        </div>

        <!-- Messages -->
        <div v-else class="space-y-3">
          <div
            v-for="(msg, i) in messages"
            :key="i"
            :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
          >
            <!-- User Message -->
            <div
              v-if="msg.role === 'user'"
              class="max-w-[85%] px-4 py-2.5 rounded-2xl rounded-br-sm bg-indigo-500/15 border border-indigo-500/20 text-sm text-indigo-100"
            >
              {{ msg.content }}
            </div>

            <!-- AI Message -->
            <div
              v-else
              class="max-w-[90%] flex gap-2"
            >
              <div class="flex-shrink-0 w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mt-0.5">
                <Sparkles :size="12" class="text-indigo-400" />
              </div>
              <div
                class="px-4 py-2.5 rounded-2xl rounded-bl-sm bg-slate-800/60 border border-white/5 text-sm text-slate-200 leading-relaxed ai-response"
                v-html="formatMarkdown(msg.content)"
              />
            </div>
          </div>

          <!-- Processing Indicator -->
          <div v-if="isProcessing" class="flex justify-start">
            <div class="flex gap-2">
              <div class="flex-shrink-0 w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Sparkles :size="12" class="text-indigo-400" />
              </div>
              <div class="px-4 py-2.5 rounded-2xl bg-slate-800/40 border border-white/5 flex items-center gap-1.5">
                <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0s" />
                <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.15s" />
                <div class="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style="animation-delay: 0.3s" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Input Bar -->
    <footer class="flex-shrink-0 relative z-10 glass border-t border-white/5">
      <div class="px-4 lg:px-6 py-3">
        <div class="flex items-center gap-3">
          <input
            v-model="inputText"
            @keydown="handleKeydown"
            type="text"
            placeholder="Ask about your reading..."
            :disabled="isProcessing || contextLoading"
            class="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder-slate-600 outline-none focus:border-indigo-500/50 transition-all"
          />
          <button
            @click="sendMessage"
            :disabled="!inputText.trim() || isProcessing"
            :class="[
              'w-10 h-10 rounded-xl flex items-center justify-center transition-all flex-shrink-0',
              inputText.trim() && !isProcessing
                ? 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30 hover:bg-indigo-400'
                : 'bg-slate-800/50 text-slate-600 cursor-not-allowed'
            ]"
          >
            <Send :size="16" />
          </button>
        </div>
        <p class="text-[9px] text-slate-700 text-center mt-2">AI may make mistakes. Always consult the original text.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.glass {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(20px);
}

.ai-response :deep(strong) {
  font-weight: 700;
  color: white;
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

.animate-in {
  animation: fadeIn 1s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
