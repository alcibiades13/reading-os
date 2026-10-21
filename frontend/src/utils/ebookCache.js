/**
 * IndexedDB cache for downloaded e-book files, so reopening a book (especially on
 * mobile) doesn't re-download it. Keeps only the most recently opened books.
 * Every call fails soft - if IndexedDB is unavailable the reader just downloads.
 */
const DB_NAME = 'ebook-cache'
const STORE = 'files'
const MAX_ENTRIES = 5

let dbPromise = null

const openDb = () => {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1)
      req.onupgradeneeded = () => req.result.createObjectStore(STORE, { keyPath: 'id' })
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
    dbPromise.catch(() => { dbPromise = null })
  }
  return dbPromise
}

const run = async (mode, fn) => {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, mode)
    const result = fn(tx.objectStore(STORE))
    tx.oncomplete = () => resolve(result?.result)
    tx.onerror = () => reject(tx.error)
  })
}

export async function getCachedEbook(id, size) {
  try {
    const record = await run('readonly', (store) => store.get(id))
    if (!record || record.size !== size) return null
    run('readwrite', (store) => store.put({ ...record, accessedAt: Date.now() })).catch(() => {})
    return record.data
  } catch {
    return null
  }
}

export async function cacheEbook(id, size, data) {
  try {
    await run('readwrite', (store) => store.put({ id, size, data, accessedAt: Date.now() }))
    const all = await run('readonly', (store) => store.getAll())
    const stale = all.sort((a, b) => b.accessedAt - a.accessedAt).slice(MAX_ENTRIES)
    if (stale.length) {
      await run('readwrite', (store) => stale.forEach((r) => store.delete(r.id)))
    }
  } catch {
    // quota exceeded / private mode - caching is optional
  }
}

export async function removeCachedEbook(id) {
  try {
    await run('readwrite', (store) => store.delete(id))
  } catch {
    // ignore
  }
}
