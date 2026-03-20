import { ref, onUnmounted } from 'vue'
import { createWorker } from 'tesseract.js'

export function useQuoteScanner() {
  const isScanning = ref(false)
  const scanProgress = ref(0)
  const scanError = ref(null)

  let worker = null

  async function getWorker() {
    if (!worker) {
      worker = await createWorker('eng', 1, {
        logger: (m) => {
          if (m.status === 'recognizing text') {
            scanProgress.value = Math.round(m.progress * 100)
          }
        },
      })
    }
    return worker
  }

  function pickImage() {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.capture = 'environment'

      input.onchange = (e) => {
        const file = e.target.files?.[0]
        if (file) {
          resolve(file)
        } else {
          reject(new Error('No file selected'))
        }
      }

      input.oncancel = () => reject(new Error('Cancelled'))
      input.click()
    })
  }

  async function scanImage() {
    isScanning.value = true
    scanProgress.value = 0
    scanError.value = null

    try {
      const file = await pickImage()
      const w = await getWorker()
      const { data } = await w.recognize(file)

      // Clean up: trim whitespace, collapse multiple blank lines
      const text = data.text
        .trim()
        .replace(/\n{3,}/g, '\n\n')

      return text
    } catch (err) {
      if (err.message === 'Cancelled' || err.message === 'No file selected') {
        return null
      }
      scanError.value = err.message
      return null
    } finally {
      isScanning.value = false
      scanProgress.value = 0
    }
  }

  onUnmounted(async () => {
    if (worker) {
      await worker.terminate()
      worker = null
    }
  })

  return {
    isScanning,
    scanProgress,
    scanError,
    scanImage,
  }
}
