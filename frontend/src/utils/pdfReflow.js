/**
 * Turns a PDF page's positioned text fragments into reflowable paragraphs
 * (like the "reading mode" in mobile PDF viewers). Heuristic by nature:
 * works well for single-column prose, degrades gracefully for complex layouts.
 */

const median = (values) => {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  return sorted[Math.floor(sorted.length / 2)]
}

const startsLowercase = (text) => /^\p{Ll}/u.test(text)
const endsSentence = (text) => /[.!?…:;"»”)\]]$/.test(text)

// Group text items into visual lines
function buildLines(items) {
  const lines = []
  let line = null

  for (const item of items) {
    if (typeof item.str !== 'string') continue
    const [, , , d, x, y] = item.transform
    const height = Math.abs(d) || item.height || 10

    const sameLine = line && Math.abs(y - line.y) < height * 0.5
    if (!sameLine) {
      if (!item.str.trim() && !line) continue
      line = { y, x, height, endX: x, parts: [] }
      lines.push(line)
    }

    const last = line.parts[line.parts.length - 1]
    if (last !== undefined && x - line.endX > height * 0.15 && !/\s$/.test(last) && !/^\s/.test(item.str)) {
      line.parts.push(' ')
    }
    line.parts.push(item.str)
    line.endX = Math.max(line.endX, x + (item.width || 0))
    line.height = Math.max(line.height, height)
    if (item.hasEOL) line = null
  }

  return lines
    .map((l) => ({ ...l, text: l.parts.join('').replace(/\s+/g, ' ').trim() }))
    .filter((l) => l.text)
}

function joinLines(prev, next) {
  // Re-join words hyphenated across lines: "conti-" + "nued" -> "continued"
  if (/\p{L}-$/u.test(prev) && startsLowercase(next)) {
    return prev.slice(0, -1) + next
  }
  return `${prev} ${next}`
}

export function textContentToBlocks(textContent) {
  const lines = buildLines(textContent.items)
  if (!lines.length) return []

  // Drop a bare page number at the top or bottom of the page
  const isPageNumber = (l) => /^[\d\s\-–—]{1,7}$/.test(l.text)
  if (isPageNumber(lines[lines.length - 1])) lines.pop()
  if (lines.length && isPageNumber(lines[0])) lines.shift()
  if (!lines.length) return []

  const bodyHeight = median(lines.map((l) => l.height))
  const gaps = []
  for (let i = 1; i < lines.length; i++) {
    const gap = lines[i - 1].y - lines[i].y
    if (gap > 0) gaps.push(gap)
  }
  const lineGap = median(gaps) || bodyHeight * 1.2
  const leftEdge = median(lines.map((l) => l.x))
  const rightEdge = Math.max(...lines.map((l) => l.endX))

  const blocks = []
  let current = null

  lines.forEach((line, i) => {
    const prev = lines[i - 1]
    const isHeading = line.height > bodyHeight * 1.25 && line.text.length < 120

    let breakBefore = !prev
    if (prev) {
      const gap = prev.y - line.y
      const prevWasHeading = current?.type === 'h'
      const indented = line.x - leftEdge > bodyHeight * 0.8
      const prevShort = rightEdge - prev.endX > bodyHeight * 4 && endsSentence(prev.text)
      breakBefore =
        gap < 0 || // column/page jump
        gap > lineGap * 1.45 ||
        indented ||
        prevShort ||
        isHeading !== prevWasHeading
    }

    if (breakBefore || !current) {
      current = { type: isHeading ? 'h' : 'p', text: line.text }
      blocks.push(current)
    } else {
      current.text = joinLines(current.text, line.text)
    }
  })

  return blocks
}
