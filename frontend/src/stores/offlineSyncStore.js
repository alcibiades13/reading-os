import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'
import { outboxAdd, outboxAll, outboxRemove } from '@/utils/offlineStore'

// No response at all = no connection (as opposed to the server answering with an error)
export const isNetworkError = (err) => !!err && !err.response && (err.code === 'ERR_NETWORK' || err.code === 'ECONNABORTED' || err.message === 'Network Error')

const RETRY_MS = 30 * 1000

/**
 * Keeps changes made without a connection (reading position, sessions, quotes...)
 * and sends them, in order, once the connection is back.
 */
export const useOfflineSyncStore = defineStore('offlineSync', () => {
  const online = ref(typeof navigator === 'undefined' ? true : navigator.onLine)
  const pending = ref(0)
  const syncing = ref(false)
  let retryTimer = null
  let initialized = false

  const refreshPending = async () => {
    pending.value = (await outboxAll()).length
    clearInterval(retryTimer)
    retryTimer = pending.value ? setInterval(flush, RETRY_MS) : null
  }

  const queue = async (entry) => {
    online.value = false
    await outboxAdd(entry)
    await refreshPending()
  }

  const flush = async () => {
    if (syncing.value) return
    syncing.value = true
    try {
      for (const entry of await outboxAll()) {
        try {
          await api.request({ method: entry.method, url: entry.url, data: entry.data })
          online.value = true
          await outboxRemove(entry.seq)
        } catch (err) {
          if (isNetworkError(err)) {
            online.value = false
            break
          }
          if (err.response && err.response.status < 500) {
            // The server rejected it (e.g. the e-book was deleted meanwhile) - retrying won't help
            console.warn('Dropped offline change', entry.url, err.response.status)
            await outboxRemove(entry.seq)
          } else {
            break // server error - try again later
          }
        }
      }
    } finally {
      syncing.value = false
      await refreshPending()
    }
  }

  /**
   * Run a request; if there's no connection, queue `entry` to send later.
   * Returns the response, or { queued: true } when it was queued.
   */
  const run = async (request, entry) => {
    try {
      const response = await request()
      online.value = true
      return response
    } catch (err) {
      if (entry && isNetworkError(err)) {
        await queue(entry)
        return { queued: true }
      }
      if (isNetworkError(err)) online.value = false
      throw err
    }
  }

  const markOffline = () => { online.value = false }

  const init = () => {
    if (initialized) return
    initialized = true
    window.addEventListener('online', () => { online.value = true; flush() })
    window.addEventListener('offline', () => { online.value = false })
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') flush()
    })
    refreshPending().then(() => { if (pending.value) flush() })
  }

  return { online, pending, syncing, queue, flush, run, markOffline, init }
})
