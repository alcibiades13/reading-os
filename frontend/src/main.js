import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { App as CapApp } from '@capacitor/app'
import router from './router'
import App from './App.vue'
import './assets/index.css'

const app = createApp(App)
const pinia = createPinia()

// Register plugins
app.use(pinia)
app.use(router)

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