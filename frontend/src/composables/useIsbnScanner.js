import { ref } from 'vue'
import { Capacitor } from '@capacitor/core'

let scannerModule = null

async function loadScanner() {
  if (!scannerModule) {
    scannerModule = await import('@capacitor-mlkit/barcode-scanning')
  }
  return scannerModule
}

export function useIsbnScanner() {
  const isScanning = ref(false)
  const scanError = ref(null)

  const isNative = Capacitor.isNativePlatform()

  async function scanIsbn() {
    isScanning.value = true
    scanError.value = null

    try {
      if (!isNative) {
        scanError.value = 'Barcode scanning is available only in the mobile app.'
        return null
      }

      const { BarcodeScanner, BarcodeFormat } = await loadScanner()

      const { available } = await BarcodeScanner.isGoogleBarcodeScannerModuleAvailable()
      if (!available) {
        await BarcodeScanner.installGoogleBarcodeScannerModule()
        scanError.value = 'Scanner module is being installed. Please try again in a moment.'
        return null
      }

      const { barcodes } = await BarcodeScanner.scan({
        formats: [BarcodeFormat.Ean13, BarcodeFormat.Ean8],
      })

      if (!barcodes || barcodes.length === 0) return null

      // ISBN barcodes are EAN-13, usually starting with 978 or 979
      const barcode = barcodes[0]
      const rawValue = barcode.rawValue

      if (!rawValue) return null

      // Validate ISBN-13 (978/979 prefix) or ISBN-10
      const isIsbn13 = /^97[89]\d{10}$/.test(rawValue)
      const isIsbn10 = /^\d{9}[\dX]$/.test(rawValue)

      if (isIsbn13 || isIsbn10) {
        return rawValue
      }

      // Some book barcodes are EAN-13 but need stripping of check digit
      if (/^\d{13}$/.test(rawValue)) {
        return rawValue
      }

      scanError.value = 'Scanned code does not appear to be a valid ISBN.'
      return null

    } catch (err) {
      if (err?.message?.includes('cancelled') || err?.message?.includes('cancel')) {
        return null
      }
      scanError.value = err?.message || 'Scanning failed.'
      return null
    } finally {
      isScanning.value = false
    }
  }

  return {
    isNative,
    isScanning,
    scanError,
    scanIsbn,
  }
}
