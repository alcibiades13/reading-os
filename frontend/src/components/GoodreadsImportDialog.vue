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

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file && file.name.endsWith('.csv')) {
    selectedFile.value = file
  } else {
    addToast({
      title: 'Invalid File',
      description: 'Please select a CSV file',
      variant: 'destructive'
    })
  }
}

const handleImport = async () => {
  if (!selectedFile.value) {
    addToast({
      title: 'No File Selected',
      description: 'Please select a Goodreads CSV file',
      variant: 'destructive'
    })
    return
  }

  importing.value = true
  importProgress.value = { current: 0, total: 0, status: 'Uploading...' }

  try {
    const response = await booksAPI.importGoodreadsCSV(selectedFile.value)

    importProgress.value = {
      current: response.data.imported,
      total: response.data.imported + response.data.skipped,
      status: 'Completed'
    }

    addToast({
      title: 'Import Successful!',
      description: `Imported ${response.data.imported} books, ${response.data.created_books} new books created`,
      variant: 'default'
    })

    await booksStore.fetchBooks()

    setTimeout(() => {
      open.value = false
      selectedFile.value = null
      importProgress.value = null
    }, 2000)

  } catch (error) {
    console.error('Import error:', error)
    addToast({
      title: 'Import Failed',
      description: error.response?.data?.error || 'Failed to import CSV file',
      variant: 'destructive'
    })
    importProgress.value = null
  } finally {
    importing.value = false
  }
}

// Reset state when dialog opens
function resetState() {
  selectedFile.value = null
  importProgress.value = null
}
</script>

<template>
  <Dialog v-model:open="open" @update:open="resetState">
    <DialogContent class="glass border-slate-700 max-w-[calc(100vw-2rem)] sm:max-w-md rounded-2xl max-h-[85vh] overflow-y-auto">
      <DialogHeader>
        <DialogTitle class="text-lg sm:text-xl lg:text-2xl font-bold flex items-center gap-2 lg:gap-3">
          <FileUp :size="20" class="text-emerald-400 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
          Import from Goodreads
        </DialogTitle>
      </DialogHeader>

      <div class="space-y-4 lg:space-y-6 py-3 lg:py-4">
        <!-- Instructions -->
        <div class="space-y-3">
          <p class="text-sm text-slate-300 leading-relaxed">
            Import your reading history from Goodreads by uploading your library export CSV file.
          </p>
          <div class="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-3">
            <p class="text-xs text-indigo-300 font-medium">
              📚 How to export from Goodreads:
            </p>
            <ol class="text-xs text-slate-400 mt-2 space-y-1 list-decimal list-inside">
              <li>Go to Goodreads → My Books</li>
              <li>Click "Import and export"</li>
              <li>Download your library CSV</li>
            </ol>
          </div>
        </div>

        <!-- File Input -->
        <div class="space-y-3">
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
            class="w-full px-6 py-4 rounded-xl border-2 border-dashed border-slate-700 hover:border-indigo-500/50 bg-slate-900/50 hover:bg-slate-900 transition-all duration-300 text-slate-400 hover:text-white flex flex-col items-center justify-center gap-2"
          >
            <Upload :size="32" />
            <span class="text-sm font-medium">
              {{ selectedFile ? selectedFile.name : 'Click to select CSV file' }}
            </span>
          </button>
        </div>

        <!-- Progress -->
        <div v-if="importProgress" class="space-y-2">
          <div class="flex items-center justify-between text-sm">
            <span class="text-slate-400">{{ importProgress.status }}</span>
            <span v-if="importProgress.total > 0" class="text-indigo-400 font-medium">
              {{ importProgress.current }} / {{ importProgress.total }}
            </span>
          </div>
          <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              v-if="importProgress.total > 0"
              class="bg-gradient-to-r from-emerald-500 to-teal-500 h-full transition-all duration-500 ease-out"
              :style="{ width: `${(importProgress.current / importProgress.total) * 100}%` }"
            />
            <div
              v-else
              class="bg-gradient-to-r from-emerald-500 to-teal-500 h-full animate-pulse"
              style="width: 100%"
            />
          </div>
        </div>

        <!-- Actions -->
        <div class="flex justify-end gap-3 pt-4">
          <button
            @click="open = false"
            :disabled="importing"
            class="px-5 py-3 rounded-xl border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            @click="handleImport"
            :disabled="!selectedFile || importing"
            class="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white text-sm font-bold hover:from-emerald-400 hover:to-teal-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Upload :size="16" />
            {{ importing ? 'Importing...' : 'Import Books' }}
          </button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
