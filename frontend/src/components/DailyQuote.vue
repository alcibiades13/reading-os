<script setup>
import { ref, computed } from 'vue'
import { Quote, Lightbulb } from 'lucide-vue-next'

const props = defineProps({
  quote: { type: Object, default: null },
  compact: { type: Boolean, default: false },
})

const expanded = ref(false)

const truncateLength = computed(() => props.compact ? 150 : 350)
const isLong = computed(() => props.quote?.text?.length > truncateLength.value)

const displayText = computed(() => {
  if (!props.quote?.text) return ''
  if (expanded.value || !isLong.value) return props.quote.text
  return props.quote.text.substring(0, truncateLength.value) + '...'
})
</script>

<template>
  <div v-if="quote" :class="compact ? 'px-4 py-4 lg:hidden' : 'lg:col-span-5'">
    <div
      class="relative rounded-[2rem] glass border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/5 overflow-hidden"
      :class="compact ? 'p-4 rounded-2xl' : 'p-5 sm:p-7 group shadow-2xl'"
    >
      <div class="absolute top-0 right-0 opacity-[0.03] text-indigo-400" :class="compact ? 'p-3' : 'p-6 group-hover:scale-110 transition-transform duration-1000'">
        <Quote :size="compact ? 48 : 80" />
      </div>
      <div class="relative z-10">
        <span
          class="inline-flex items-center rounded-full bg-indigo-500/10 border border-indigo-500/20 font-black uppercase text-indigo-400 tracking-widest"
          :class="compact ? 'gap-1.5 px-2 py-0.5 text-[8px] mb-3' : 'gap-2 px-2.5 py-1 text-[9px] mb-5'"
        >
          <Lightbulb :size="compact ? 10 : 12" />
          {{ compact ? 'Daily Musing' : 'Musing of the Day' }}
        </span>

        <div :class="compact ? 'mb-2' : 'mb-5'">
          <p
            class="font-serif italic text-slate-200 leading-relaxed"
            :class="compact ? 'text-sm' : 'text-quote'"
          >
            "{{ displayText }}"
          </p>
          <button
            v-if="isLong && !compact"
            @click="expanded = !expanded"
            class="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition-colors mt-2"
          >
            {{ expanded ? 'show less' : 'more...' }}
          </button>
        </div>

        <div :class="compact ? 'flex items-center justify-between' : ''">
          <p class="text-indigo-400 font-bold" :class="compact ? 'text-[10px]' : 'text-xs'">
            — {{ quote.book_author }}
          </p>
          <button
            v-if="isLong && compact"
            @click.stop="expanded = !expanded"
            class="text-[10px] font-bold text-indigo-400/70 hover:text-indigo-400 py-1 px-2"
          >
            {{ expanded ? 'less' : 'more...' }}
          </button>
          <p v-if="!compact" class="text-slate-500 text-[10px] font-medium uppercase tracking-wider">
            {{ quote.book_title }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>
