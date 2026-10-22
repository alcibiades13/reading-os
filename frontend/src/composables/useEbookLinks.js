import { ref } from 'vue'
import { ebooksAPI } from '@/services/api'

const REFRESH_MS = 60 * 1000
const cache = {} // kind -> { links: ref(Map), loadedAt }

/**
 * "Open in e-book" links for quotes / study notes / vocabulary words that were
 * captured in the e-book reader. kind: 'quote' | 'note' | 'word'
 */
export function useEbookLinks(kind) {
  if (!cache[kind]) cache[kind] = { links: ref(new Map()), loadedAt: 0 }
  const entry = cache[kind]

  if (Date.now() - entry.loadedAt > REFRESH_MS) {
    entry.loadedAt = Date.now()
    ebooksAPI.annotationsIndex(kind)
      .then(({ data }) => {
        entry.links.value = new Map(data.map((a) => [a.object_id, a]))
      })
      .catch(() => {
        entry.loadedAt = 0
      })
  }

  const ebookLink = (objectId) => {
    const annotation = entry.links.value.get(objectId)
    return annotation ? `/ebooks/${annotation.ebook_id}/read?at=${encodeURIComponent(annotation.position)}` : null
  }

  return { ebookLink }
}
