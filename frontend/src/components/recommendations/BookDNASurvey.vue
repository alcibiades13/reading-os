<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { recommendationsService } from '@/services/recommendationsService'
import {
  Gauge,
  Heart,
  Brain,
  Users,
  Moon,
  Church,
  Lightbulb,
  Fingerprint,
  HeartCrack,
  Home,
  Hourglass,
  Sunrise,
  Crown,
  Leaf,
  TrendingUp,
  Sparkles,
  Check,
  X,
  UserX,
  Clock,
  Scale,
  Megaphone,
  Sprout,
} from 'lucide-vue-next'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  book: {
    type: Object,
    required: true,
  },
  userBookId: {
    type: Number,
    default: null,
  },
})

const emit = defineEmits(['close', 'submitted'])

const currentStep = ref(0) // 0 = sliders, 1 = themes, 2 = done
const submitting = ref(false)
const surveyConfig = ref(null)

// Responses state
const responses = ref({
  pace: 0.5,
  emotional_intensity: 0.5,
  complexity: 0.5,
  character_focus: 0.5,
  darkness: 0.5,
  introspection: 0.5,
})

const selectedThemes = ref([])

// Question configuration with icons
const questionIcons = {
  pace: Gauge,
  emotional_intensity: Heart,
  complexity: Brain,
  character_focus: Users,
  darkness: Moon,
  introspection: Sparkles,
}

// Theme icons
const themeIcons = {
  faith: Church,
  identity: Fingerprint,
  philosophy: Lightbulb,
  suffering: HeartCrack,
  love: Heart,
  family: Home,
  mortality: Hourglass,
  redemption: Sunrise,
  power: Crown,
  nature: Leaf,
  friendship: Users,
  growth: TrendingUp,
  alienation: UserX,
  memory: Clock,
  trauma: HeartCrack,
  moral_dilemma: Scale,
  social_critique: Megaphone,
  coming_of_age: Sprout,
}

// Default questions if API fails
const defaultQuestions = [
  { id: 'pace', question: 'What was the pacing like?', left_label: 'Slow, contemplative', right_label: 'Fast, page-turner' },
  { id: 'emotional_intensity', question: 'Emotional intensity?', left_label: 'Light, relaxing', right_label: 'Intense, emotional' },
  { id: 'complexity', question: 'How complex was it?', left_label: 'Accessible, straightforward', right_label: 'Dense, demanding' },
  { id: 'character_focus', question: 'Story focus?', left_label: 'Plot & events', right_label: 'Characters & relationships' },
  { id: 'darkness', question: 'Overall tone?', left_label: 'Light, hopeful', right_label: 'Dark, heavy' },
  { id: 'introspection', question: 'What drives the narrative?', left_label: 'External action & events', right_label: 'Inner world & reflection' },
]

const defaultThemes = [
  { id: 'faith', label: 'Faith & Spirituality' },
  { id: 'identity', label: 'Identity' },
  { id: 'philosophy', label: 'Philosophy' },
  { id: 'suffering', label: 'Suffering & Pain' },
  { id: 'love', label: 'Love' },
  { id: 'family', label: 'Family' },
  { id: 'redemption', label: 'Redemption' },
  { id: 'growth', label: 'Personal Growth' },
  { id: 'alienation', label: 'Alienation' },
  { id: 'memory', label: 'Memory & Nostalgia' },
  { id: 'trauma', label: 'Trauma' },
  { id: 'moral_dilemma', label: 'Moral Dilemma' },
]

const questions = computed(() => {
  return surveyConfig.value?.questions || defaultQuestions
})

const themeOptions = computed(() => {
  return surveyConfig.value?.theme_options || defaultThemes
})

onMounted(async () => {
  try {
    surveyConfig.value = await recommendationsService.getSurveyConfig()
  } catch (error) {
    console.error('Error loading survey config:', error)
  }
})

const toggleTheme = (themeId) => {
  const index = selectedThemes.value.indexOf(themeId)
  if (index === -1) {
    selectedThemes.value.push(themeId)
  } else {
    selectedThemes.value.splice(index, 1)
  }
}

const handleNext = () => {
  if (currentStep.value === 0) {
    currentStep.value = 1
  }
}

const handleBack = () => {
  if (currentStep.value === 1) {
    currentStep.value = 0
  }
}

const handleSubmit = async () => {
  submitting.value = true
  try {
    await recommendationsService.submitSurvey(
      props.book.id,
      props.userBookId,
      responses.value,
      selectedThemes.value
    )
    currentStep.value = 2

    // Auto close after success
    setTimeout(() => {
      emit('submitted')
      emit('close')
    }, 1500)
  } catch (error) {
    console.error('Error submitting survey:', error)
  } finally {
    submitting.value = false
  }
}

const handleSkip = () => {
  emit('close')
}

const getSliderBackground = (value) => {
  const percentage = value * 100
  return `linear-gradient(to right, #6366f1 0%, #6366f1 ${percentage}%, #1e293b ${percentage}%, #1e293b 100%)`
}
</script>

<template>
  <Dialog :open="open" @update:open="$emit('close')">
    <DialogContent class="max-w-md bg-slate-900 border-slate-800">
      <!-- Header -->
      <DialogHeader class="text-center pb-2">
        <div class="flex items-center justify-center gap-2 mb-2">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Sparkles :size="20" class="text-indigo-400" />
          </div>
        </div>
        <DialogTitle class="text-xl font-black text-white">
          {{ currentStep === 2 ? 'Thank you!' : 'How would you describe this book?' }}
        </DialogTitle>
        <DialogDescription class="text-slate-400 text-sm">
          {{ currentStep === 2 ? 'Your vote helps everyone find their perfect book' : 'Quick survey, 6 questions' }}
        </DialogDescription>
      </DialogHeader>

      <!-- Book Preview -->
      <div v-if="currentStep !== 2" class="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5 mb-4">
        <img
          v-if="book.cover_image"
          :src="book.cover_image"
          :alt="book.title"
          class="w-12 h-16 object-cover rounded-lg"
        />
        <div class="flex-1 min-w-0">
          <h4 class="font-bold text-white text-sm truncate">{{ book.title }}</h4>
          <p class="text-xs text-slate-500 truncate">{{ book.author_names || book.authors?.map(a => a.name).join(', ') }}</p>
        </div>
      </div>

      <!-- Step 1: Slider Questions -->
      <div v-if="currentStep === 0" class="space-y-5">
        <div v-for="q in questions" :key="q.id" class="space-y-2">
          <div class="flex items-center gap-2 text-sm">
            <component
              :is="questionIcons[q.id] || Sparkles"
              :size="16"
              class="text-indigo-400 flex-shrink-0"
            />
            <span class="text-white font-medium">{{ q.question }}</span>
          </div>
          <div class="flex items-center gap-3">
            <span class="text-[10px] text-slate-500 w-24 text-right">{{ q.left_label }}</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              v-model.number="responses[q.id]"
              class="flex-1 h-2 rounded-full appearance-none cursor-pointer slider-thumb"
              :style="{ background: getSliderBackground(responses[q.id]) }"
            />
            <span class="text-[10px] text-slate-500 w-24">{{ q.right_label }}</span>
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <Button
            variant="ghost"
            @click="handleSkip"
            class="flex-1 text-slate-400 hover:text-white"
          >
            Skip
          </Button>
          <Button
            @click="handleNext"
            class="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white font-bold"
          >
            Next
          </Button>
        </div>
      </div>

      <!-- Step 2: Theme Selection -->
      <div v-else-if="currentStep === 1" class="space-y-4">
        <p class="text-sm text-slate-400">What themes are prominent? (optional)</p>

        <div class="flex flex-wrap gap-2">
          <button
            v-for="theme in themeOptions"
            :key="theme.id"
            @click="toggleTheme(theme.id)"
            :class="[
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all',
              selectedThemes.includes(theme.id)
                ? 'bg-indigo-500 text-white ring-2 ring-indigo-500/50'
                : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-white'
            ]"
          >
            <component
              :is="themeIcons[theme.id] || Sparkles"
              :size="12"
            />
            {{ theme.label }}
          </button>
        </div>

        <div class="flex gap-3 pt-2">
          <Button
            variant="ghost"
            @click="handleBack"
            class="flex-1 text-slate-400 hover:text-white"
          >
            Back
          </Button>
          <Button
            @click="handleSubmit"
            :disabled="submitting"
            class="flex-1 bg-indigo-500 hover:bg-indigo-600 text-white font-bold"
          >
            <span v-if="submitting">Saving...</span>
            <span v-else>Save</span>
          </Button>
        </div>
      </div>

      <!-- Step 3: Success -->
      <div v-else class="py-8 text-center">
        <div class="w-16 h-16 mx-auto rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mb-4">
          <Check :size="32" class="text-emerald-400" />
        </div>
        <p class="text-slate-400 text-sm">Your reading profile has been updated</p>
      </div>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
/* Custom slider thumb styling */
.slider-thumb::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

.slider-thumb::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #6366f1;
  cursor: pointer;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

/* Light mode */
:global(body.light) .slider-thumb {
  background: linear-gradient(to right, #6366f1 var(--progress), #e2e8f0 var(--progress)) !important;
}
</style>
