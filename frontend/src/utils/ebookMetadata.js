/**
 * Reads title/author/ISBN/cover from an EPUB or PDF in the browser, before upload,
 * so the user only has to confirm (or fix) the pre-filled form.
 */

const titleFromFilename = (name) =>
  name.replace(/\.(epub|pdf)$/i, '').replace(/[_]+/g, ' ').replace(/\s+/g, ' ').trim()

const extractIsbn = (value) => {
  const digits = String(value || '').replace(/[-\s]/g, '')
  const match = digits.match(/97[89]\d{10}|\d{9}[\dXx]/)
  return match ? match[0].toUpperCase() : ''
}

const isPdf = (buffer) => {
  const head = new Uint8Array(buffer, 0, 5)
  return String.fromCharCode(...head) === '%PDF-'
}

async function extractEpub(buffer, fileName) {
  const { default: ePub } = await import('epubjs')
  const book = ePub(buffer)
  try {
    await book.ready
    const meta = book.packaging?.metadata || {}

    let coverBlob = null
    try {
      const coverUrl = await book.coverUrl()
      if (coverUrl) coverBlob = await (await fetch(coverUrl)).blob()
    } catch {
      // no usable cover
    }

    return {
      format: 'epub',
      title: (meta.title || '').trim() || titleFromFilename(fileName),
      author: (meta.creator || '').trim(),
      language: (meta.language || '').trim().slice(0, 20),
      isbn: extractIsbn(meta.identifier),
      pageCount: null,
      hasText: true,
      coverBlob,
    }
  } finally {
    book.destroy()
  }
}

// Renders page 1 as a JPEG thumbnail to use as the cover
async function renderPdfCover(doc) {
  const page = await doc.getPage(1)
  const base = page.getViewport({ scale: 1 })
  const viewport = page.getViewport({ scale: 400 / base.width })
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(viewport.width)
  canvas.height = Math.round(viewport.height)
  await page.render({ canvasContext: canvas.getContext('2d'), viewport }).promise
  return new Promise((resolve) => canvas.toBlob(resolve, 'image/jpeg', 0.8))
}

export async function pdfHasTextLayer(doc) {
  const sample = Math.min(doc.numPages, 3)
  for (let i = 1; i <= sample; i++) {
    const content = await (await doc.getPage(i)).getTextContent()
    if (content.items.some((item) => item.str && item.str.trim())) return true
  }
  return false
}

async function extractPdf(buffer, fileName) {
  const { default: pdfjs } = await import('@/utils/pdfjs')
  // pdf.js takes ownership of the buffer it is given - pass a copy
  const doc = await pdfjs.getDocument({ data: buffer.slice(0) }).promise
  try {
    const { info } = await doc.getMetadata().catch(() => ({ info: {} }))
    let coverBlob = null
    try {
      coverBlob = await renderPdfCover(doc)
    } catch {
      // ignore
    }
    return {
      format: 'pdf',
      title: (info?.Title || '').trim() || titleFromFilename(fileName),
      author: (info?.Author || '').trim(),
      language: (info?.Language || '').trim().slice(0, 20),
      isbn: '',
      pageCount: doc.numPages,
      hasText: await pdfHasTextLayer(doc).catch(() => true),
      coverBlob,
    }
  } finally {
    doc.destroy()
  }
}

export async function extractEbookMetadata(file) {
  const buffer = await file.arrayBuffer()
  if (isPdf(buffer)) return extractPdf(buffer, file.name)
  return extractEpub(buffer, file.name)
}
