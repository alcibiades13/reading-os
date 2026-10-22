import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { App as CapApp } from '@capacitor/app'
import router from './router'
import App from './App.vue'
import { applyReadingScale } from './stores/themeStore'
import { useOfflineSyncStore } from './stores/offlineSyncStore'
import './assets/index.css'

// Apply saved reading text size before first render
applyReadingScale()

const app = createApp(App)
const pinia = createPinia()

// Register plugins
app.use(pinia)
app.use(router)

// Send changes made while offline (reading position, quotes...) once connected
useOfflineSyncStore(pinia).init()

// Android back button handler
CapApp.addListener('backButton', ({ canGoBack }) => {
  if (router.currentRoute.value.path !== '/library' && window.history.length > 1) {
    router.back()
  } else {
    CapApp.minimizeApp()
  }
})

// Mount app
app.mount('#app')