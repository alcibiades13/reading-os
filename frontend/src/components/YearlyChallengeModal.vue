<script setup>
import { ref, watch } from 'vue'
import { X, Save, Target } from 'lucide-vue-next'

const props = defineProps({
  challenge: {
    type: Object,
    default: null,
  },
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'save'])

const currentYear = new Date().getFullYear()

// Form data
const formData = ref({
  title: `${currentYear} Reading Challenge`,
  target_books: 50,
  start_date: `${currentYear}-01-01`,
  end_date: `${currentYear}-12-31`,
  is_active: true,
  is_public: false,
})

// Watch for challenge changes (edit mode)
watch(() => props.challenge, (newChallenge) => {
  if (newChallenge) {
    formData.value = {
      title: newChallenge.title || `${currentYear} Reading Challenge`,
      target_books: newChallenge.target_books || 50,
      start_date: newChallenge.start_date || `${currentYear}-01-01`,
      end_date: newChallenge.end_date || `${currentYear}-12-31`,
      is_active: newChallenge.is_active !== undefined ? newChallenge.is_active : true,
      is_public: newChallenge.is_public !== undefined ? newChallenge.is_public : false,
    }
  } else {
    // Reset to defaults for new challenge
    formData.value = {
      title: `${currentYear} Reading Challenge`,
      target_books: 50,
      start_date: `${currentYear}-01-01`,
      end_date: `${currentYear}-12-31`,
      is_active: true,
      is_public: false,
    }
  }
}, { immediate: true })

const handleSave = () => {
  emit('save', formData.value)
}

const handleClose = () => {
  emit('close')
}

// Preset targets
const presets = [12, 24, 36, 50, 100, 150]

const setPreset = (value) => {
  formData.value.target_books = value
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-sm animate-in fade-in duration-300">
    <div class="relative w-full max-w-md glass rounded-3xl overflow-hidden shadow-2xl animate-in zoom-in-95 duration-300 ring-2 ring-indigo-500">

      <!-- Close Button -->
      <button
        @click="handleClose"
        class="absolute top-6 right-6 z-20 p-2 rounded-full bg-slate-900/50 hover:bg-slate-800 text-slate-300 transition-colors"
      >
        <X :size="20" />
      </button>

      <!-- Header -->
      <div class="p-8 pb-6 border-b border-slate-800">
        <div class="flex items-center gap-3 mb-2">
          <div class="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
            <Target :size="24" class="text-indigo-400" />
          </div>
          <h2 class="text-2xl font-black text-white">
            {{ challenge ? 'Edit Challenge' : 'Create Challenge' }}
          </h2>
        </div>
        <p class="text-sm text-slate-400">
          Set your reading goal for {{ currentYear }}
        </p>
      </div>

      <!-- Form -->
      <div class="p-8 space-y-6">
        <!-- Target Books -->
        <div>
          <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2 block">
            Books to Read
          </label>
          <input
            v-model.number="formData.target_books"
            type="number"
            min="1"
            max="999"
            class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-3 text-2xl font-bold text-white text-center focus:border-indigo-500 focus:outline-none"
          />

          <!-- Preset Buttons -->
          <div class="flex flex-wrap gap-2 mt-3">
            <button
              v-for="preset in presets"
              :key="preset"
              @click="setPreset(preset)"
              :class="formData.target_books === preset ? 'bg-indigo-500 text-white border-indigo-500' : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:border-indigo-500/50'"
              class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition-colors"
            >
              {{ preset }}
            </button>
          </div>
        </div>

        <!-- Challenge Title (Optional) -->
        <div>
          <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2 block">
            Challenge Title (Optional)
          </label>
          <input
            v-model="formData.title"
            type="text"
            placeholder="My Reading Challenge"
            class="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none"
          />
        </div>

        <!-- Date Range -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2 block">
              Start Date
            </label>
            <input
              v-model="formData.start_date"
              type="date"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <div>
            <label class="text-xs text-slate-400 font-bold uppercase tracking-wider mb-2 block">
              End Date
            </label>
            <input
              v-model="formData.end_date"
              type="date"
              class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-indigo-500 focus:outline-none"
            />
          </div>
        </div>

        <!-- Options -->
        <div class="space-y-3">
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              v-model="formData.is_active"
              type="checkbox"
              class="w-4 h-4 rounded bg-slate-800 border-slate-700 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
            />
            <div>
              <span class="text-sm font-semibold text-white">Active Challenge</span>
              <p class="text-xs text-slate-500">Track progress for this challenge</p>
            </div>
          </label>

          <label class="flex items-center gap-3 cursor-pointer">
            <input
              v-model="formData.is_public"
              type="checkbox"
              class="w-4 h-4 rounded bg-slate-800 border-slate-700 text-indigo-500 focus:ring-indigo-500 focus:ring-offset-0"
            />
            <div>
              <span class="text-sm font-semibold text-white">Public Challenge</span>
              <p class="text-xs text-slate-500">Let others see your progress</p>
            </div>
          </label>
        </div>
      </div>

      <!-- Footer Actions -->
      <div class="p-6 border-t border-slate-800 bg-slate-900/50 flex gap-3">
        <button
          @click="handleClose"
          class="flex-1 px-5 py-3 rounded-xl border border-slate-700 text-slate-300 text-sm font-semibold hover:bg-slate-800 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="handleSave"
          class="flex-[2] px-5 py-3 rounded-xl bg-indigo-500 text-white text-sm font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 hover:bg-indigo-400 active:scale-[0.98] transition-all"
        >
          <Save :size="18" />
          {{ challenge ? 'Update Challenge' : 'Create Challenge' }}
        </button>
      </div>
    </div>
  </div>
</template>
