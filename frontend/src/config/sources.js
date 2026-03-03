export const SOURCE_LABELS = {
  google_books: 'Google Books',
  delfi_scrape: 'Delfi',
  vulkan_scrape: 'Vulkan',
  laguna_scrape: 'Laguna',
  open_library: 'OpenLibrary',
  manual: 'Manual',
}

export function sourceLabel(source) {
  return SOURCE_LABELS[source] || source || 'Unknown'
}

export function sourceColor(source) {
  if (source === 'google_books') return 'bg-sky-500/10 text-sky-400'
  if (source?.includes('scrape')) return 'bg-amber-500/10 text-amber-400'
  if (source === 'manual') return 'bg-emerald-500/10 text-emerald-400'
  return 'bg-slate-500/10 text-slate-400'
}
