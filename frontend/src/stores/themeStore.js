import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// Reading text size steps - multiplier applied to long-form content via --reading-scale
export const READING_SCALES = [
  { id: 'small', label: 'Small', value: 0.9 },
  { id: 'default', label: 'Default', value: 1 },
  { id: 'large', label: 'Large', value: 1.15 },
  { id: 'xlarge', label: 'Extra large', value: 1.3 },
]

const READING_SCALE_KEY = 'lumina_reading_scale'

const readStoredScale = () => {
  try {
    const stored = localStorage.getItem(READING_SCALE_KEY)
    return READING_SCALES.some((s) => s.id === stored) ? stored : 'default'
  } catch {
    return 'default'
  }
}

// Exported so main.js can apply it before mount (avoids a flash of default size)
export const applyReadingScale = (id = readStoredScale()) => {
  const scale = READING_SCALES.find((s) => s.id === id)?.value ?? 1
  document.documentElement.style.setProperty('--reading-scale', scale)
}

export const useThemeStore = defineStore('theme', () => {
  // Get initial theme from localStorage or default to 'dark'
  const theme = ref(localStorage.getItem('lumina_theme') || 'dark')

  // Apply theme class to body element
  const applyTheme = () => {
    if (theme.value === 'light') {
      document.body.classList.add('light')
    } else {
      document.body.classList.remove('light')
    }
  }

  // Toggle between light and dark themes
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  // Reading text size (per device - phone and desktop often want different sizes)
  const readingScale = ref(readStoredScale())

  const setReadingScale = (id) => {
    if (READING_SCALES.some((s) => s.id === id)) {
      readingScale.value = id
    }
  }

  watch(readingScale, (id) => {
    try {
      localStorage.setItem(READING_SCALE_KEY, id)
    } catch {
      // storage unavailable - setting still applies for this session
    }
    applyReadingScale(id)
  })

  // Set specific theme
  const setTheme = (newTheme) => {
    if (newTheme === 'light' || newTheme === 'dark') {
      theme.value = newTheme
    }
  }

  // Watch theme changes and apply them
  watch(theme, (newTheme) => {
    localStorage.setItem('lumina_theme', newTheme)
    applyTheme()
  })

  // Apply theme on initial load
  applyTheme()

  return {
    theme,
    toggleTheme,
    setTheme,
    readingScale,
    setReadingScale,
  }
})
