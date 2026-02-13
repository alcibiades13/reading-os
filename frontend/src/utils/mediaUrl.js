/**
 * Resolve a media URL to an absolute URL pointing to the correct backend.
 * DRF may return absolute URLs with the wrong host (e.g. http://127.0.0.1:8001/media/...)
 * which mobile devices can't reach. This function always rebuilds the URL
 * using VITE_API_URL as the base.
 */
export function getMediaUrl(url) {
  if (!url) return null

  // Strip /api from VITE_API_URL to get the backend base
  const apiUrl = import.meta.env.VITE_API_URL || ''
  const baseUrl = apiUrl.replace(/\/api\/?$/, '')

  // If URL is already absolute, extract just the path and rebuild
  if (url.startsWith('http')) {
    try {
      const parsed = new URL(url)
      return `${baseUrl}${parsed.pathname}`
    } catch {
      return url
    }
  }

  if (url.startsWith('/')) {
    return `${baseUrl}${url}`
  }
  return `${baseUrl}/${url}`
}
