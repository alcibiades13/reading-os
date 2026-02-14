<script setup>
import { ref, computed, watch, onMounted } from 'vue'
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
  // Slider question icons
  Gauge, Heart, Brain, Users, Moon,
  // Theme icons — reused across categories
  Church, Lightbulb, Fingerprint, HeartCrack, Home, Hourglass,
  Sunrise, Crown, Leaf, TrendingUp, Sparkles, Check, UserX, Clock,
  Scale, Megaphone, Sprout, Target, EyeOff, AlertTriangle, Palette,
  Shield, Layers, Sword, Compass,
  // Relational icons
  ShieldOff, CloudRain, UserMinus, HeartHandshake, Flame, Gem, Baby,
  Handshake, Link2Off, HeartOff,
  // Psychological icons
  Activity, Cloud, Pill, Swords, Search, HelpCircle, ArrowUpDown,
  // Existential icons
  Infinity, Wind, Shuffle, Ban, Mountain, Timer,
  // Social/Political icons
  Lock, Flag, MapPin, Globe, Equal, Cpu,
  // Experience/Mood icons
  Sun, CloudDrizzle, Droplets, AlertOctagon, Coffee, CloudSun, Flower2, Smile,
  // Genre icons
  BookOpen, Rocket, Wand2, Zap, Skull, Landmark, User, FlaskConical,
  Scroll, Feather, RadioTower, Drama, Image, FileText, ShieldAlert, BookMarked,
  // Positive / Fun / Light icons
  PartyPopper, Gamepad2, ThumbsUp, Laugh,
  // Mystery / Action / Adventure icons
  Eye, Map, Plane,
  // Children / YA icons
  GraduationCap, Cat,
  // Extra
  Mail, Castle,
  // UI
  Star,
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
  existingVote: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'submitted'])

const isUpdate = computed(() => !!props.existingVote)
const currentStep = ref(0) // 0 = sliders, 1 = themes, 2 = done
const submitting = ref(false)
const surveyConfig = ref(null)

const MAX_PRIMARY = 3

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
const primaryThemes = ref([])
const selectedGenreTags = ref([])
const primaryGenreTag = ref(null)

// Question configuration with icons
const questionIcons = {
  pace: Gauge,
  emotional_intensity: Heart,
  complexity: Brain,
  character_focus: Users,
  darkness: Moon,
  introspection: Sparkles,
}

// Theme icons (mapped from survey.py icon strings to Vue components)
const themeIcons = {
  // Positive / Fun / Light
  hopeful: Sun,
  fun: PartyPopper,
  playful: Gamepad2,
  whimsical: Wand2,
  heartwarming: HeartHandshake,
  joy: Smile,
  optimism: Sunrise,
  humor: Laugh,
  lighthearted: Feather,
  cozy: Coffee,
  feel_good: ThumbsUp,
  uplifting: TrendingUp,
  // Relational & Emotional
  love: Heart,
  family: Home,
  friendship: Users,
  betrayal: ShieldOff,
  loss_grief: CloudRain,
  loneliness: UserMinus,
  belonging: HeartHandshake,
  jealousy: Flame,
  marriage: Gem,
  parenthood: Baby,
  brotherhood: Handshake,
  toxic_relationships: Link2Off,
  unrequited_love: HeartOff,
  // Romance
  romantic: Heart,
  slow_romance: HeartHandshake,
  passionate: Flame,
  tragic_love: HeartCrack,
  forbidden_love: Lock,
  // Psychological
  trauma: HeartCrack,
  alienation: UserX,
  obsession: Target,
  madness: Brain,
  guilt: Scale,
  anxiety: Activity,
  depression: Cloud,
  addiction: Pill,
  self_discovery: Search,
  identity_crisis: HelpCircle,
  manipulation: EyeOff,
  power_dynamics: ArrowUpDown,
  suffering: HeartCrack,
  revenge: Sword,
  deception: EyeOff,
  // Existential
  philosophy: Lightbulb,
  existentialism: Infinity,
  moral_dilemma: Scale,
  faith: Church,
  redemption: Sunrise,
  mortality: Hourglass,
  freedom: Wind,
  fate_free_will: Shuffle,
  absurdity: Ban,
  meaning_of_life: Compass,
  isolation: Mountain,
  time_impermanence: Timer,
  // Social & Political
  power: Crown,
  social_critique: Megaphone,
  war: Shield,
  class: Layers,
  oppression: Lock,
  revolution: Flag,
  migration: MapPin,
  colonialism: Globe,
  gender_roles: Equal,
  tech_society: Cpu,
  // Mystery / Action / Adventure
  mystery: Search,
  suspense: Eye,
  action: Swords,
  adventure: Compass,
  journey: Map,
  quest: Compass,
  travel: Plane,
  survival: Shield,
  danger: AlertTriangle,
  heros_journey: Sword,
  investigation: Fingerprint,
  conspiracy: Eye,
  crime: AlertTriangle,
  // Children / YA
  childhood: Baby,
  growing_up: Sprout,
  friendship_adventure: Users,
  school_life: GraduationCap,
  imagination: Lightbulb,
  fairy_tale: Crown,
  talking_animals: Cat,
  magic: Wand2,
  family_bonds: Home,
  moral_lesson: BookOpen,
  // Experience & Mood
  bleak: CloudDrizzle,
  cathartic: Droplets,
  disturbing: AlertOctagon,
  comforting: Coffee,
  bittersweet: CloudSun,
  wholesome: Flower2,
  dark_humor: Smile,
  satire: Drama,
  gothic: Castle,
  nature: Leaf,
  art: Palette,
  // Growth & Change
  coming_of_age: Sprout,
  growth: TrendingUp,
  memory: Clock,
  identity: Fingerprint,
  // Format / Type
  diary: BookOpen,
  memoir: User,
  autobiography: User,
  biography: User,
  letters: Mail,
  short_stories: Layers,
  essays_lit: FileText,
  self_help_lit: Compass,
  spiritual_guide: Church,
  classic_lit: BookMarked,
  modern_lit: Zap,
  experimental: FlaskConical,
}

// Genre tag icons
const genreIcons = {
  literary_fiction: BookOpen,
  science_fiction: Rocket,
  fantasy: Wand2,
  mystery: Search,
  thriller: Zap,
  horror: Skull,
  romance: Heart,
  historical_fiction: Landmark,
  dystopian: RadioTower,
  magical_realism: Sparkles,
  biography_memoir: User,
  philosophy_nf: Lightbulb,
  psychology_nf: Brain,
  science_nf: FlaskConical,
  history_nf: Scroll,
  poetry: Feather,
  essays: FileText,
  satire: Drama,
  young_adult: Sprout,
  graphic_novel: Image,
  self_help: Compass,
  true_crime: ShieldAlert,
  classics: BookMarked,
  childrens: Baby,
  religion: Church,
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

const questions = computed(() => {
  return surveyConfig.value?.questions || defaultQuestions
})

const themeCategories = computed(() => {
  return surveyConfig.value?.theme_categories || []
})

const genreTagOptions = computed(() => {
  return surveyConfig.value?.genre_tag_options || []
})

const themeCounts = computed(() => {
  return surveyConfig.value?.theme_popularity || {}
})

// Pre-populate with existing vote when dialog opens
watch(() => props.open, (isOpen) => {
  if (isOpen) {
    currentStep.value = 0
    if (props.existingVote) {
      responses.value = {
        pace: props.existingVote.pace ?? 0.5,
        emotional_intensity: props.existingVote.emotional_intensity ?? 0.5,
        complexity: props.existingVote.complexity ?? 0.5,
        character_focus: props.existingVote.character_focus ?? 0.5,
        darkness: props.existingVote.darkness ?? 0.5,
        introspection: props.existingVote.introspection ?? 0.5,
      }
      selectedThemes.value = [...(props.existingVote.themes || [])]
      primaryThemes.value = [...(props.existingVote.primary_themes || [])]
      selectedGenreTags.value = [...(props.existingVote.genre_tags || [])]
      primaryGenreTag.value = props.existingVote.primary_genre_tag || null
    } else {
      responses.value = {
        pace: 0.5,
        emotional_intensity: 0.5,
        complexity: 0.5,
        character_focus: 0.5,
        darkness: 0.5,
        introspection: 0.5,
      }
      selectedThemes.value = []
      primaryThemes.value = []
      selectedGenreTags.value = []
      primaryGenreTag.value = null
    }
  }
})

onMounted(async () => {
  try {
    surveyConfig.value = await recommendationsService.getSurveyConfig()
  } catch (error) {
    console.error('Error loading survey config:', error)
  }
})

// Theme toggle with auto-primary promotion
const toggleTheme = (themeId) => {
  const isThemeSelected = selectedThemes.value.includes(themeId)
  const isThemePrimary = primaryThemes.value.includes(themeId)

  if (isThemeSelected) {
    selectedThemes.value = selectedThemes.value.filter(t => t !== themeId)
    if (isThemePrimary) {
      primaryThemes.value = primaryThemes.value.filter(t => t !== themeId)
    }
  } else {
    selectedThemes.value.push(themeId)
    if (primaryThemes.value.length < MAX_PRIMARY) {
      primaryThemes.value.push(themeId)
    }
  }
}

const togglePrimary = (themeId) => {
  if (!selectedThemes.value.includes(themeId)) return
  const isPrim = primaryThemes.value.includes(themeId)
  if (isPrim) {
    primaryThemes.value = primaryThemes.value.filter(t => t !== themeId)
  } else if (primaryThemes.value.length < MAX_PRIMARY) {
    primaryThemes.value.push(themeId)
  }
}

const isThemeSelected = (id) => selectedThemes.value.includes(id)
const isThemePrimary = (id) => primaryThemes.value.includes(id)

const toggleGenreTag = (tagId) => {
  const idx = selectedGenreTags.value.indexOf(tagId)
  if (idx === -1) {
    selectedGenreTags.value.push(tagId)
    // Auto-set as primary if none set yet
    if (!primaryGenreTag.value) {
      primaryGenreTag.value = tagId
    }
  } else {
    selectedGenreTags.value.splice(idx, 1)
    // Clear primary if it was this one
    if (primaryGenreTag.value === tagId) {
      primaryGenreTag.value = selectedGenreTags.value.length > 0 ? selectedGenreTags.value[0] : null
    }
  }
}

const togglePrimaryGenre = (tagId) => {
  if (!selectedGenreTags.value.includes(tagId)) return
  if (primaryGenreTag.value === tagId) {
    primaryGenreTag.value = null
  } else {
    primaryGenreTag.value = tagId
  }
}

const isGenreSelected = (id) => selectedGenreTags.value.includes(id)
const isGenrePrimary = (id) => primaryGenreTag.value === id

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
      selectedThemes.value,
      primaryThemes.value,
      selectedGenreTags.value,
      primaryGenreTag.value
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
    <DialogContent class="max-w-[calc(100vw-2rem)] sm:max-w-md bg-slate-900 border-slate-800">
      <!-- Header -->
      <DialogHeader class="text-center pb-2">
        <div class="flex items-center justify-center gap-2 mb-2">
          <div class="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
            <Sparkles :size="20" class="text-indigo-400" />
          </div>
        </div>
        <DialogTitle class="text-xl font-black text-white">
          {{ currentStep === 2 ? 'Thank you!' : isUpdate ? 'Update your rating' : 'How would you describe this book?' }}
        </DialogTitle>
        <DialogDescription class="text-slate-400 text-sm">
          {{ currentStep === 2 ? 'Your vote helps everyone find their perfect book' : currentStep === 1 ? 'Select themes & genre' : isUpdate ? 'Adjust your previous responses' : 'Quick survey, 6 questions' }}
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
      <div v-if="currentStep === 0" class="space-y-4">
        <div v-for="q in questions" :key="q.id" class="space-y-1.5">
          <div class="flex items-center gap-2 text-sm">
            <component
              :is="questionIcons[q.id] || Sparkles"
              :size="16"
              class="text-indigo-400 flex-shrink-0"
            />
            <span class="text-white font-medium text-xs sm:text-sm">{{ q.question }}</span>
          </div>
          <div class="flex items-center gap-2 sm:gap-3">
            <span class="text-[9px] sm:text-[10px] text-slate-500 w-16 sm:w-24 text-right leading-tight">{{ q.left_label }}</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              v-model.number="responses[q.id]"
              class="flex-1 h-2 rounded-full appearance-none cursor-pointer slider-thumb"
              :style="{ background: getSliderBackground(responses[q.id]) }"
            />
            <span class="text-[9px] sm:text-[10px] text-slate-500 w-16 sm:w-24 leading-tight">{{ q.right_label }}</span>
          </div>
        </div>

        <div class="flex gap-3 pt-2">
          <Button
            variant="ghost"
            @click="handleSkip"
            class="flex-1 text-slate-400 hover:text-slate-300 hover:bg-white/5"
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

      <!-- Step 2: Theme & Genre Selection -->
      <div v-else-if="currentStep === 1" class="space-y-3">
        <!-- Primary theme hint -->
        <div class="flex items-center gap-2 text-[10px] text-slate-500">
          <Star :size="10" class="text-amber-400 flex-shrink-0" />
          <span>First 3 selected become <strong class="text-amber-400">primary</strong> (higher weight). Tap star to toggle.</span>
        </div>

        <!-- Scrollable theme container -->
        <div class="max-h-[320px] overflow-y-auto pr-1 space-y-3 survey-scrollbar">
          <!-- Theme categories -->
          <div v-for="category in themeCategories" :key="category.id">
            <h4 class="text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1.5">
              {{ category.label }}
            </h4>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="theme in category.themes"
                :key="theme.id"
                @click="toggleTheme(theme.id)"
                :class="[
                  'inline-flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-bold transition-all',
                  isThemePrimary(theme.id)
                    ? 'bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/50'
                    : isThemeSelected(theme.id)
                      ? 'bg-indigo-500/20 text-indigo-300 ring-1 ring-indigo-500/50'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-300'
                ]"
              >
                <Star
                  v-if="isThemePrimary(theme.id)"
                  :size="10"
                  class="text-amber-400 fill-amber-400 cursor-pointer"
                  @click.stop="togglePrimary(theme.id)"
                />
                <component
                  v-else-if="isThemeSelected(theme.id) && primaryThemes.length < MAX_PRIMARY"
                  :is="Star"
                  :size="10"
                  class="text-slate-500 cursor-pointer"
                  @click.stop="togglePrimary(theme.id)"
                />
                <component
                  v-else
                  :is="themeIcons[theme.id] || Sparkles"
                  :size="10"
                />
                {{ theme.label }}
              </button>
            </div>
          </div>

          <!-- Genre Tags Section -->
          <div class="border-t border-slate-700/50 pt-3">
            <h4 class="text-[10px] font-bold text-slate-600 uppercase tracking-wider mb-1 flex items-center gap-1.5">
              <BookOpen :size="10" />
              Genre
            </h4>
            <div class="flex items-center gap-2 text-[10px] text-slate-600 mb-2">
              <Star :size="9" class="text-emerald-400 flex-shrink-0" />
              <span>First selected becomes <strong class="text-emerald-400">primary genre</strong>. Tap star to change.</span>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="genre in genreTagOptions"
                :key="genre.id"
                @click="toggleGenreTag(genre.id)"
                :class="[
                  'inline-flex items-center gap-1 px-2 py-1 rounded-full text-[11px] font-bold transition-all',
                  isGenrePrimary(genre.id)
                    ? 'bg-emerald-500/25 text-emerald-300 ring-1 ring-emerald-400/60'
                    : isGenreSelected(genre.id)
                      ? 'bg-emerald-500/15 text-emerald-400 ring-1 ring-emerald-500/40'
                      : 'bg-white/5 text-slate-400 hover:bg-white/10 hover:text-slate-300'
                ]"
              >
                <Star
                  v-if="isGenrePrimary(genre.id)"
                  :size="10"
                  class="text-emerald-300 fill-emerald-300 cursor-pointer"
                  @click.stop="togglePrimaryGenre(genre.id)"
                />
                <component
                  v-else-if="isGenreSelected(genre.id)"
                  :is="Star"
                  :size="10"
                  class="text-slate-500 cursor-pointer"
                  @click.stop="togglePrimaryGenre(genre.id)"
                />
                <component
                  v-else
                  :is="genreIcons[genre.id] || BookOpen"
                  :size="10"
                />
                {{ genre.label }}
              </button>
            </div>
          </div>
        </div>

        <!-- Navigation buttons -->
        <div class="flex gap-3 pt-2">
          <Button
            variant="ghost"
            @click="handleBack"
            class="flex-1 text-slate-400 hover:text-slate-300 hover:bg-white/5"
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

/* Custom scrollbar */
.survey-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.survey-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.survey-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 2px;
}
.survey-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}

/* Light mode */
:global(body.light) .slider-thumb {
  background: linear-gradient(to right, #6366f1 var(--progress), #e2e8f0 var(--progress)) !important;
}
</style>
