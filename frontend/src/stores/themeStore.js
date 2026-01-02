import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

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
  }
})
