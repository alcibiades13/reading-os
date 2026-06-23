import { Capacitor } from '@capacitor/core'
import { socialAPI } from '@/services/api'

let initialized = false

export async function initPushNotifications() {
  if (!Capacitor.isNativePlatform() || initialized) return
  initialized = true

  try {
    // Dynamic import hidden from Rollup's static analysis — the plugin
    // is only installed when Firebase google-services.json is configured.
    const moduleName = '@capacitor/push-notifications'
    const { PushNotifications } = await import(/* @vite-ignore */ moduleName)

    const permResult = await PushNotifications.requestPermissions()
    if (permResult.receive !== 'granted') return

    await PushNotifications.register()

    PushNotifications.addListener('registration', async ({ value: token }) => {
      try {
        await socialAPI.registerPushToken(token, Capacitor.getPlatform())
      } catch {
        // Silently fail — push is non-critical
      }
    })

    PushNotifications.addListener('pushNotificationReceived', (notification) => {
      console.log('Push received in foreground:', notification.title)
    })

    PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      console.log('Push tapped:', action.notification.data)
    })

  } catch {
    // Plugin not installed or Firebase not configured — skip silently
  }
}
