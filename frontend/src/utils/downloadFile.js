/**
 * Download a blob response from the API as a file.
 * @param {Object} response - Axios response with blob data
 * @param {string} fallbackFilename - Filename if not in Content-Disposition header
 */
export function downloadBlob(response, fallbackFilename = 'download') {
  const disposition = response.headers?.['content-disposition']
  let filename = fallbackFilename
  if (disposition) {
    const match = disposition.match(/filename="?([^";\n]+)"?/)
    if (match) filename = match[1]
  }

  const blob = new Blob([response.data])
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Call an API function that returns a blob and trigger download.
 * @param {Function} apiCall - Async function returning an axios blob response
 * @param {string} filename - Fallback filename
 */
export async function downloadFromAPI(apiCall, filename) {
  const response = await apiCall()
  downloadBlob(response, filename)
}
