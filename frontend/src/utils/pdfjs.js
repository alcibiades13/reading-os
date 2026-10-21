// pdf.js with its worker bundled by Vite. Import lazily (await import('@/utils/pdfjs'))
// so the ~1MB library only loads when a PDF is actually opened.
import * as pdfjsLib from 'pdfjs-dist'
import workerUrl from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = workerUrl

export default pdfjsLib
