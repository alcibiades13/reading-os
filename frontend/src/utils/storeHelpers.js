/**
 * Wraps an async action with loading/error state management.
 * Use inside Pinia Options API actions.
 *
 * @param {Object} store - The Pinia store instance (this)
 * @param {Function} fn - Async function to execute. Return value becomes result.data
 * @param {string} errorMsg - Fallback error message
 * @returns {{ success: boolean, data?: any, error?: any }}
 */
export async function withLoading(store, fn, errorMsg = 'Operation failed') {
  store.loading = true
  store.error = null
  try {
    const data = await fn()
    return { success: true, data }
  } catch (error) {
    store.error = error.response?.data || errorMsg
    return { success: false, error: store.error }
  } finally {
    store.loading = false
  }
}

/**
 * Wraps an async action without loading/error state (lightweight).
 * Use for secondary actions that shouldn't show global loading state.
 *
 * @param {Function} fn - Async function to execute. Return value becomes result.data
 * @returns {{ success: boolean, data?: any, error?: any }}
 */
export async function tryCatch(fn) {
  try {
    const data = await fn()
    return { success: true, data }
  } catch (error) {
    return { success: false, error: error.response?.data }
  }
}
