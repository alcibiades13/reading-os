/**
 * IndexedDB storage for reading without a connection:
 *  - kv:     cached API data (e-book list, e-book details, highlights, covers)
 *  - outbox: changes made offline, replayed in order when the connection returns
 * Every call fails soft - without IndexedDB the app simply behaves as before.
 */
const DB_NAME = 'reading-os-offline'
const DB_VERSION = 1

let dbPromise = null

const openDb = () => {
  if (!dbPromise) {
    dbPromise = new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION)
      req.onupgradeneeded = () => {
        const db = req.result
        if (!db.objectStoreNames.contains('kv')) db.createObjectStore('kv')
        if (!db.objectStoreNames.contains('outbox')) db.createObjectStore('outbox', { keyPath: 'seq', autoIncrement: true })
      }
      req.onsuccess = () => resolve(req.result)
      req.onerror = () => reject(req.error)
    })
    dbPromise.catch(() => { dbPromise = null })
  }
  return dbPromise
}

const tx = async (store, mode, fn) => {
  const db = await openDb()
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(store, mode)
    const request = fn(transaction.objectStore(store))
    transaction.oncomplete = () => resolve(request?.result)
    transaction.onerror = () => reject(transaction.error)
  })
}

/* ---------------- key/value cache ---------------- */

export async function kvGet(key) {
  try {
    return (await tx('kv', 'readonly', (s) => s.get(key))) ?? null
  } catch {
    return null
  }
}

export async function kvSet(key, value) {
  try {
    // Strip Vue proxies / non-cloneable values
    const plain = value instanceof Blob || value instanceof ArrayBuffer ? value : JSON.parse(JSON.stringify(value))
    await tx('kv', 'readwrite', (s) => s.put(plain, key))
  } catch {
    // caching is optional
  }
}

export async function kvDelete(key) {
  try {
    await tx('kv', 'readwrite', (s) => s.delete(key))
  } catch {
    // ignore
  }
}

/* ---------------- outbox ---------------- */

// entry: { method, url, data, dedupeKey? } - a newer entry with the same dedupeKey replaces the older one
export async function outboxAdd(entry) {
  try {
    const plain = JSON.parse(JSON.stringify({ ...entry, queuedAt: Date.now() }))
    if (plain.dedupeKey) {
      const all = (await tx('outbox', 'readonly', (s) => s.getAll())) || []
      const stale = all.filter((e) => e.dedupeKey === plain.dedupeKey)
      if (stale.length) await tx('outbox', 'readwrite', (s) => stale.forEach((e) => s.delete(e.seq)))
    }
    await tx('outbox', 'readwrite', (s) => s.add(plain))
    return true
  } catch {
    return false
  }
}

export async function outboxAll() {
  try {
    return ((await tx('outbox', 'readonly', (s) => s.getAll())) || []).sort((a, b) => a.seq - b.seq)
  } catch {
    return []
  }
}

export async function outboxRemove(seq) {
  try {
    await tx('outbox', 'readwrite', (s) => s.delete(seq))
  } catch {
    // ignore
  }
}
