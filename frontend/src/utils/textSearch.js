/**
 * Forgiving full-text matching for the e-book search:
 * case-, diacritic- and script-insensitive, so "blazeni" finds "Блажени" and "blaženi".
 */

const CYRILLIC = {
  а: 'a', б: 'b', в: 'v', г: 'g', д: 'd', ђ: 'dj', е: 'e', ж: 'z', з: 'z', и: 'i', ј: 'j',
  к: 'k', л: 'l', љ: 'lj', м: 'm', н: 'n', њ: 'nj', о: 'o', п: 'p', р: 'r', с: 's', т: 't',
  ћ: 'c', у: 'u', ф: 'f', х: 'h', ц: 'c', ч: 'c', џ: 'dz', ш: 's',
  // Russian / older texts
  ё: 'e', й: 'j', щ: 's', ъ: '', ы: 'y', ь: '', э: 'e', ю: 'ju', я: 'ja', і: 'i', ѣ: 'e',
}
const LATIN_EXTRA = { đ: 'dj', dž: 'dz', ß: 'ss', æ: 'ae', œ: 'oe', ø: 'o' }

const normalizeChar = (ch) => {
  const lower = ch.toLowerCase()
  if (CYRILLIC[lower] !== undefined) return CYRILLIC[lower]
  if (LATIN_EXTRA[lower] !== undefined) return LATIN_EXTRA[lower]
  return lower.normalize('NFD').replace(/[̀-ͯ]/g, '')
}

/**
 * Normalized text plus, for every normalized character, the index of the
 * original character it came from (so matches can be mapped back).
 */
export function buildIndex(text) {
  let norm = ''
  const map = []
  for (let i = 0; i < text.length; i++) {
    const ch = text[i]
    if (/\s/.test(ch)) {
      if (norm && !norm.endsWith(' ')) {
        norm += ' '
        map.push(i)
      }
      continue
    }
    const out = normalizeChar(ch)
    for (const c of out) {
      norm += c
      map.push(i)
    }
  }
  return { norm, map }
}

export const normalizeQuery = (query) => buildIndex(query.trim()).norm

/** All matches of an already-normalized query in `text`, as [start, end) original offsets. */
export function findAll(text, normalizedQuery, limit = 200) {
  if (!normalizedQuery) return []
  const { norm, map } = buildIndex(text)
  const matches = []
  let from = 0
  while (matches.length < limit) {
    const at = norm.indexOf(normalizedQuery, from)
    if (at < 0) break
    const last = at + normalizedQuery.length - 1
    matches.push({ start: map[at], end: map[last] + 1 })
    from = at + normalizedQuery.length
  }
  return matches
}

/** A short snippet around a match: { before, match, after } */
export function excerpt(text, start, end, radius = 60) {
  const from = Math.max(0, start - radius)
  const to = Math.min(text.length, end + radius)
  return {
    before: (from > 0 ? '…' : '') + text.slice(from, start).replace(/\s+/g, ' ').trimStart(),
    match: text.slice(start, end),
    after: text.slice(end, to).replace(/\s+/g, ' ').trimEnd() + (to < text.length ? '…' : ''),
  }
}
