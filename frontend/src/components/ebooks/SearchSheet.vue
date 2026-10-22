<script setup>
import { ref, watch, nextTick } from 'vue'
import { Search, X, Loader2 } from 'lucide-vue-next'

/**
 * Full-text search in the open book. Kept mounted (v-show) by the reader so
 * results survive jumping to a hit and coming back for the next one.
 */
const props = defineProps({
  open: { type: Boolean, default: false },
  reader: { type: Object, default: null }, // EpubReader / PdfReader instance (search, cancelSearch)
  format: { type: String, required: true },
  theme: { type: Object, required: true },
})

const emit = defineEmits(['close', 'go'])

const query = ref('')
const results = ref([])
const searching = ref(false)
const searchedFor = ref('')
const input = ref(null)
let timer = null
let run = 0

const runSearch = async () => {
  const q = query.value.trim()
  props.reader?.cancelSearch()
  results.value = []
  searchedFor.value = q
  if (q.length < 2 || !props.reader) {
    searching.value = false
    return
  }
  const current = ++run
  searching.value = true
  await props.reader.search(q, (batch) => {
    if (current === run) results.value = [...results.value, ...batch]
  })
  if (current === run) searching.value = false
}

watch(query, () => {
  clearTimeout(timer)
  timer = setTimeout(runSearch, 400)
})

watch(() => props.open, async (open) => {
  if (open) {
    await nextTick()
    input.value?.focus()
  }
})

const go = (result) => emit('go', result, searchedFor.value)
</script>

<template>
  <div
    v-show="open"
    class="absolute inset-0 z-50 flex items-end sm:items-start justify-center bg-black/30 sm:pt-16"
    @click="emit('close')"
  >
    <div
      class="w-full sm:w-[34rem] max-h-[85vh] sm:max-h-[75vh] flex flex-col rounded-t-2xl sm:rounded-2xl border shadow-2xl pb-[env(safe-area-inset-bottom)]"
      :style="{ background: theme.bg, color: theme.fg, borderColor: `${theme.muted}40` }"
      @click.stop
    >
      <div class="p-4 border-b flex items-center gap-2" :style="{ borderColor: `${theme.muted}33` }">
        <div class="relative flex-1">
          <Search :size="16" class="absolute left-3 top-1/2 -translate-y-1/2" :style="{ color: theme.muted }" />
          <input
            ref="input"
            v-model="query"
            type="search"
            placeholder="Search in this book…"
            class="w-full rounded-xl pl-9 pr-3 py-2.5 text-sm outline-none border focus:border-indigo-500"
            :style="{ background: `${theme.muted}1a`, borderColor: `${theme.muted}40`, color: theme.fg }"
            @keydown.esc.stop="emit('close')"
          />
        </div>
        <button class="p-2 rounded-lg hover:opacity-70" @click="emit('close')"><X :size="18" /></button>
      </div>

      <div class="px-4 py-2 text-[11px] flex items-center gap-2" :style="{ color: theme.muted }">
        <Loader2 v-if="searching" :size="12" class="animate-spin" />
        <template v-if="searchedFor.length >= 2">
          {{ results.length }}{{ results.length >= 500 ? '+' : '' }} result{{ results.length === 1 ? '' : 's' }}{{ searching ? '…' : '' }}
        </template>
        <template v-else>Ignores case, accents and Cyrillic/Latin - "blazeni" finds "Блажени".</template>
      </div>

      <ul class="flex-1 overflow-y-auto px-2 pb-3">
        <li v-for="(result, i) in results" :key="i">
          <button class="w-full text-left px-2 py-2.5 rounded-xl hover:bg-indigo-500/10" @click="go(result)">
            <p class="text-[11px] font-bold mb-0.5" :style="{ color: theme.muted }">
              {{ result.chapter || (format === 'pdf' ? '' : 'Beginning') }}<template v-if="format === 'pdf'">{{ result.chapter ? ' · ' : '' }}p. {{ result.page }}</template>
            </p>
            <p class="text-sm leading-snug">
              {{ result.excerpt.before }}<mark class="bg-yellow-400/40 rounded-sm px-px" style="color: inherit">{{ result.excerpt.match }}</mark>{{ result.excerpt.after }}
            </p>
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
