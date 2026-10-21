<script setup>
import { ref } from 'vue'
import { useUserBooksStore } from '@/stores/userBooksStore'
import { useToast } from '@/composables/useToast'
import { booksAPI } from '@/services/api'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { FileUp, Upload } from 'lucide-vue-next'

const open = defineModel('open', { type: Boolean, default: false })

const booksStore = useUserBooksStore()
const { addToast } = useToast()

const importing = ref(false)
const importProgress = ref(null)
const selectedFile = ref(null)
const fileInputRef = ref(null)

const triggerFileInput = () => fileInputRef.value?.click()

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.name.endsWith('.csv')) {
    selectedFile.value = file
  } else {
    addToast('Please select a CSV file', 'error')
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    addToast('Please select a StoryGraph CSV file', 'error')
    return
  }

  importing.value = true
  importProgress.value = { current: 0, total: 0, status: 'Uploading...' }

  try {
    const response = await booksAPI.importStorygraphCSV(selectedFile.value)

    importProgress.value = {
      current: response.data.imported,
      total: response.data.imported + response.data.skipped,
      status: 'Completed'
    }

    addToast(`Imported ${response.data.imported} books (${response.data.created_books} new)`)
    await booksStore.fetchBooks()

    setTimeout(() => {
      open.value = false
      selectedFile.value = null
      importProgress.value = null
    }, 2000)

  } catch (error) {
    addToast(error.response?.data?.error || 'Failed to import CSV file', 'error')
    importProgress.value = null
  } finally {
    importing.value = false
  }
}

function resetState() {
  selectedFile.value = null
  importProgress.value = null
}
</script>

<template>
  <Dialog v-model:open="open" @update:open="resetState">
    <DialogContent class="glass border-zinc-700 max-w-[calc(100vw-2rem)] sm:max-w-md rounded-2xl max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="text-lg sm:text-xl font-bold flex items-center gap-2">
          <FileUp :size="20" class="text-violet-400" />
          Import from StoryGraph
        </DialogTitle>
      </DialogHeader>

      <div class="space-y-4 py-3">
        <p class="text-sm text-zinc-300 leading-relaxed">
          Import your reading history from The StoryGraph by uploading your library export CSV file.
        </p>

        <div class="bg-violet-500/10 border border-violet-500/20 rounded-lg p-3">
          <p class="text-xs text-violet-300 font-medium">📚 How to export from StoryGraph:</p>
          <ol class="text-xs text-zinc-400 mt-2 space-y-1 list-decimal list-inside">
            <li>Go to StoryGraph → Browse Books → Import/Export</li>
            <li>Click "Export your library" button</li>
            <li>Download the CSV file from your email</li>
          </ol>
        </div>

        <div class="bg-zinc-800/50 border border-zinc-700/50 rounded-lg p-3">
          <p class="text-xs text-zinc-400">
            <span class="text-zinc-300 font-medium">What gets imported:</span> Read status, star ratings, reviews, read dates, and owned status. New books are created automatically from your library.
          </p>
        </div>

        <div>
          <input
            ref="fileInputRef"
            type="file"
            accept=".csv"
            @change="handleFileSelect"
            class="hidden"
          />
          <button
            @click="triggerFileInput"
            :disabled="importing"
            class="w-full px-6 py-4 rounded-xl border-2 border-dashed border-zinc-700 hover:border-violet-500/50 bg-zinc-900/50 hover:bg-zinc-900 transition-all text-zinc-400 hover:text-white flex flex-col items-center justify-center gap-2"
          >
            <Upload :size="32" />
            <span class="text-sm font-medium">
              {{ selectedFile ? selectedFile.name : 'Click to select CSV file' }}
            </span>
          </button>
        </div>

        <div v-if="importProgress" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-zinc-400">{{ importProgress.status }}</span>
            <span v-if="importProgress.total > 0" class="text-violet-400 font-medium">
              {{ importProgress.current }} / {{ importProgress.total }}
            </span>
          </div>
          <div class="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
            <div
              v-if="importProgress.total > 0"
              class="bg-gradient-to-r from-violet-500 to-purple-500 h-full transition-all duration-500"
              :style="{ width: `${(importProgress.current / importProgress.total) * 100}%` }"
            />
            <div v-else class="bg-gradient-to-r from-violet-500 to-purple-500 h-full animate-pulse w-full" />
          </div>
        </div>

        <div class="flex justify-end gap-3 pt-2">
          <button
            @click="open = false"
            :disabled="importing"
            class="px-5 py-2.5 rounded-xl border border-zinc-700 text-zinc-300 text-sm font-semibold hover:bg-zinc-800 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            @click="handleImport"
            :disabled="!selectedFile || importing"
            class="px-6 py-2.5 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 text-white text-sm font-bold hover:from-violet-400 hover:to-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Upload :size="16" />
            {{ importing ? 'Importing...' : 'Import Books' }}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
