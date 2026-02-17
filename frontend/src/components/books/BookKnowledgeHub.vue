<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userBooksAPI } from '@/services/api'
import { BookOpen, PenTool, Brain, Quote, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  bookId: { type: [String, Number], required: true },
  bookTitle: { type: String, default: '' },
})

const router = useRouter()
const loading = ref(true)
const knowledge = ref(null)

const totalItems = computed(() => {
  if (!knowledge.value) return 0
  return (
    knowledge.value.quotes.count +
    knowledge.value.study_notes.count +
    knowledge.value.vocabulary.count +
    knowledge.value.journal_entries.count
  )
})

onMounted(async () => {
  try {
    const response = await userBooksAPI.bookKnowledge(props.bookId)
    knowledge.value = response.data
  } catch (error) {
    console.error('Error loading book knowledge:', error)
  } finally {
    loading.value = false
  }
})

const navigateToQuotes = () => {
  router.push({ name: 'Quotes', query: { book: props.bookId } })
}

const navigateToStudy = () => {
  router.push({ name: 'BookStudy', params: { id: props.bookId }, query: { title: props.bookTitle } })
}

const navigateToVocabulary = () => {
  router.push({ name: 'Vocabulary', query: { book: props.bookId } })
}

const navigateToCodex = () => {
  router.push({ name: 'Codex' })
}
</script>

<template>
  <section v-if="!loading && totalItems > 0">
    <h2 class="text-sm font-bold text-slate-500 uppercase tracking-[0.15em] flex items-center gap-2 mb-6">
      <Brain :size="14" class="text-indigo-400" />
      Knowledge Hub
    </h2>

    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <!-- Quotes -->
      <button
        v-if="knowledge.quotes.count > 0"
        @click="navigateToQuotes"
        class="p-4 rounded-2xl bg-amber-500/5 border border-amber-500/10 text-left hover:border-amber-500/30 transition-all group"
      >
        <div class="flex items-center gap-2 mb-2">
          <Quote :size="14" class="text-amber-400" />
          <span class="text-[10px] font-black text-amber-400 uppercase tracking-widest">Quotes</span>
        </div>
        <p class="text-2xl font-black text-white mb-2">{{ knowledge.quotes.count }}</p>
        <div v-if="knowledge.quotes.recent.length" class="space-y-1">
          <p
            v-for="q in knowledge.quotes.recent.slice(0, 2)"
            :key="q.id"
            class="text-[10px] text-slate-500 line-clamp-1 italic"
          >
            "{{ q.text }}"
          </p>
        </div>
        <div class="mt-2 flex items-center gap-1 text-[10px] font-bold text-amber-400/60 group-hover:text-amber-400 transition-colors">
          View All <ChevronRight :size="10" />
        </div>
      </button>

      <!-- Study Notes -->
      <button
        v-if="knowledge.study_notes.count > 0"
        @click="navigateToStudy"
        class="p-4 rounded-2xl bg-indigo-500/5 border border-indigo-500/10 text-left hover:border-indigo-500/30 transition-all group"
      >
        <div class="flex items-center gap-2 mb-2">
          <BookOpen :size="14" class="text-indigo-400" />
          <span class="text-[10px] font-black text-indigo-400 uppercase tracking-widest">Study Notes</span>
        </div>
        <p class="text-2xl font-black text-white mb-2">{{ knowledge.study_notes.count }}</p>
        <div v-if="knowledge.study_notes.recent.length" class="space-y-1">
          <p
            v-for="n in knowledge.study_notes.recent.slice(0, 2)"
            :key="n.id"
            class="text-[10px] text-slate-500 line-clamp-1"
          >
            {{ n.content }}
          </p>
        </div>
        <div class="mt-2 flex items-center gap-1 text-[10px] font-bold text-indigo-400/60 group-hover:text-indigo-400 transition-colors">
          View All <ChevronRight :size="10" />
        </div>
      </button>

      <!-- Vocabulary -->
      <button
        v-if="knowledge.vocabulary.count > 0"
        @click="navigateToVocabulary"
        class="p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10 text-left hover:border-emerald-500/30 transition-all group"
      >
        <div class="flex items-center gap-2 mb-2">
          <Brain :size="14" class="text-emerald-400" />
          <span class="text-[10px] font-black text-emerald-400 uppercase tracking-widest">Vocabulary</span>
        </div>
        <p class="text-2xl font-black text-white mb-2">{{ knowledge.vocabulary.count }}</p>
        <div v-if="knowledge.vocabulary.recent.length" class="space-y-1">
          <p
            v-for="w in knowledge.vocabulary.recent.slice(0, 2)"
            :key="w.id"
            class="text-[10px] text-slate-500 line-clamp-1"
          >
            <span class="font-bold text-slate-400">{{ w.word }}</span> — {{ w.definition }}
          </p>
        </div>
        <div class="mt-2 flex items-center gap-1 text-[10px] font-bold text-emerald-400/60 group-hover:text-emerald-400 transition-colors">
          View All <ChevronRight :size="10" />
        </div>
      </button>

      <!-- Journal Entries -->
      <button
        v-if="knowledge.journal_entries.count > 0"
        @click="navigateToCodex"
        class="p-4 rounded-2xl bg-rose-500/5 border border-rose-500/10 text-left hover:border-rose-500/30 transition-all group"
      >
        <div class="flex items-center gap-2 mb-2">
          <PenTool :size="14" class="text-rose-400" />
          <span class="text-[10px] font-black text-rose-400 uppercase tracking-widest">Journal</span>
        </div>
        <p class="text-2xl font-black text-white mb-2">{{ knowledge.journal_entries.count }}</p>
        <div v-if="knowledge.journal_entries.recent.length" class="space-y-1">
          <p
            v-for="e in knowledge.journal_entries.recent.slice(0, 2)"
            :key="e.id"
            class="text-[10px] text-slate-500 line-clamp-1"
          >
            {{ e.title }}
          </p>
        </div>
        <div class="mt-2 flex items-center gap-1 text-[10px] font-bold text-rose-400/60 group-hover:text-rose-400 transition-colors">
          View All <ChevronRight :size="10" />
        </div>
      </button>
    </div>
  </section>
</template>
