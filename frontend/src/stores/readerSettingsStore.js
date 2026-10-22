import { defineStore } from 'pinia'
import { reactive, watch } from 'vue'

// E-book reader appearance - saved per device, like the app theme
export const READER_THEMES = {
  dark: { label: 'Dark', bg: '#18181b', fg: '#e4e4e7', muted: '#71717a', link: '#818cf8' },
  black: { label: 'Black', bg: '#000000', fg: '#e4e4e7', muted: '#71717a', link: '#818cf8' },
  light: { label: 'Light', bg: '#fafafa', fg: '#27272a', muted: '#71717a', link: '#4f46e5' },
  sepia: { label: 'Sepia', bg: '#f4ecd8', fg: '#5b4636', muted: '#8a7560', link: '#9a5b2b' },
}

export const READER_FONTS = {
  serif: { label: 'Serif', css: "Georgia, 'Iowan Old Style', 'Palatino Linotype', 'Times New Roman', serif" },
  sans: { label: 'Sans', css: "Inter, system-ui, -apple-system, 'Segoe UI', sans-serif" },
  publisher: { label: 'Original', css: '' },
}

export const READER_MARGINS = {
  narrow: { label: 'Narrow', px: 12 },
  normal: { label: 'Normal', px: 28 },
  wide: { label: 'Wide', px: 56 },
}

export const FONT_SIZE_MIN = 70
export const FONT_SIZE_MAX = 220
export const FONT_SIZE_STEP = 10

const STORAGE_KEY = 'lumina_reader_settings'

const DEFAULTS = {
  theme: 'dark',
  fontSize: 100, // percent
  fontFamily: 'serif',
  lineHeight: 1.6,
  margin: 'normal',
  epubFlow: 'paginated', // 'paginated' | 'scrolled'
  pdfMode: 'reflow', // 'reflow' | 'page'
  pdfZoom: 1,
}

const load = () => {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }
  } catch {
    return { ...DEFAULTS }
  }
}

export const useReaderSettingsStore = defineStore('readerSettings', () => {
  const settings = reactive(load())

  watch(settings, (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
    } catch {
      // storage unavailable - settings still apply for this session
    }
  }, { deep: true })

  const changeFontSize = (delta) => {
    settings.fontSize = Math.min(FONT_SIZE_MAX, Math.max(FONT_SIZE_MIN, settings.fontSize + delta))
  }

  const reset = () => Object.assign(settings, DEFAULTS)

  return { settings, changeFontSize, reset }
})
