import { Capacitor } from '@capacitor/core'
import { socialAPI } from '@/services/api'

let initialized = false

export async function initPushNotifications() {
  if (!Capacitor.isNativePlatform() || initialized) return
  initialized = true

  try {
    const { PushNotifications } = await import('@capacitor/push-notifications')

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
      // App is in foreground — notification received but not shown by OS
      // Could show an in-app toast here if desired
      console.log('Push received in foreground:', notification.title)
    })

    PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      // User tapped a notification — handle navigation here if needed
      console.log('Push tapped:', action.notification.data)
    })

  } catch (err) {
    console.warn('Push notifications unavailable:', err)
  }
}
