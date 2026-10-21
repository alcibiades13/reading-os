/**
 * Helpers for text selected in the e-book reader.
 */

const SENTENCE_END = /[.!?…]+["'»”’)\]]*(?=\s|$)/g

/**
 * Returns the full sentence(s) around [start, end) in `text` - used as the
 * context sentence for vocabulary words.
 */
export function sentenceAround(text, start, end) {
  if (!text) return ''
  let sentenceStart = 0
  let sentenceEnd = text.length

  for (const match of text.matchAll(SENTENCE_END)) {
    const boundary = match.index + match[0].length
    if (boundary <= start) sentenceStart = boundary
    else if (boundary >= end) {
      sentenceEnd = boundary
      break
    }
  }
  return text.slice(sentenceStart, sentenceEnd).replace(/\s+/g, ' ').trim()
}

/**
 * Builds {text, context} from a DOM Range: `context` is the sentence the selection sits in,
 * taken from the nearest block element (paragraph, list item...).
 */
export function describeRange(range) {
  const text = range.toString().replace(/\s+/g, ' ').trim()
  if (!text) return null

  let node = range.commonAncestorContainer
  if (node.nodeType !== 1) node = node.parentElement
  const block = node?.closest?.('p, li, blockquote, dd, td, h1, h2, h3, h4, h5, h6, div') || node
  if (!block) return { text, context: text }

  const before = block.ownerDocument.createRange()
  before.selectNodeContents(block)
  before.setEnd(range.startContainer, range.startOffset)
  const start = before.toString().length
  const full = block.textContent || ''

  return { text, context: sentenceAround(full, start, start + range.toString().length) || text }
}

// A selected word without surrounding punctuation ("„rijeka," -> "rijeka")
export function cleanWord(text) {
  return text.trim().replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N}]+$/gu, '')
}
