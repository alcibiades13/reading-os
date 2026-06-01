<script setup>
import { useIsbnScanner } from '@/composables/useIsbnScanner'
import { ScanLine, Loader2 } from 'lucide-vue-next'

const emit = defineEmits(['scanned', 'error'])

const { isNative, isScanning, scanError, scanIsbn } = useIsbnScanner()

const handleScan = async () => {
  const isbn = await scanIsbn()
  if (isbn) {
    emit('scanned', isbn)
  } else if (scanError.value) {
    emit('error', scanError.value)
  }
}
</script>

<template>
  <button
    v-if="isNative"
    @click="handleScan"
    :disabled="isScanning"
    type="button"
    class="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:border-indigo-500/60 hover:bg-indigo-500/20 text-xs font-bold transition-all disabled:opacity-50 active:scale-95"
  >
    <Loader2 v-if="isScanning" :size="14" class="animate-spin" />
    <ScanLine v-else :size="14" />
    {{ isScanning ? 'Scanning...' : 'Scan ISBN' }}
  </button>
</template>
