import api from './api'

/**
 * Delfi.rs Book Scraping Service
 * Scrapes book information from Delfi.rs bookstore
 */

/**
 * Scrape book from Delfi.rs URL
 * @param {string} url - Full Delfi.rs book URL
 * @returns {Promise<Object>} - Formatted book object
 */
export async function scrapeBookByUrl(url) {
  try {
    const response = await api.post('/books/scrape_delfi/', { url })
    return formatBookData(response.data)
  } catch (error) {
    console.error('Delfi scraping error:', error)
    throw new Error(error.response?.data?.error || 'Failed to scrape book from Delfi.rs')
  }
}

/**
 * Search books on Delfi.rs (currently manual URL entry)
 * Since Delfi.rs is JavaScript-heavy, users will need to provide direct book URLs
 *
 * @param {string} query - Not used for now, kept for API consistency
 * @param {number} maxResults - Not used for now
 * @returns {Promise<Array>} - Empty array (search not implemented yet)
 */
export async function searchBooks(query, maxResults = 20) {
  // TODO: Implement search when Delfi search page is analyzed
  // For now, return empty array - users will use direct URL input
  console.warn('Delfi.rs search not yet implemented - use direct URL input')
  return []
}

/**
 * Search book by ISBN on Delfi.rs
 * @param {string} isbn - ISBN-10 or ISBN-13
 * @returns {Promise<Object|null>} - Formatted book object or null
 */
export async function searchByISBN(isbn) {
  // TODO: Implement ISBN search when available
  console.warn('Delfi.rs ISBN search not yet implemented')
  return null
}

/**
 * Format Delfi scraped data to match our standardized book format
 * @param {Object} delfiData - Raw data from Delfi scraper
 * @returns {Object} - Formatted book object
 */
function formatBookData(delfiData) {
  return {
    // IDs
    delfi_id: delfiData.delfi_id || null,
    delfi_link: delfiData.delfi_link || null,

    // Basic Info
    title: delfiData.title || '',
    subtitle: delfiData.subtitle || '',
    authors: Array.isArray(delfiData.authors) ? delfiData.authors : [],
    description: delfiData.description || '',

    // Publishing Info
    publisher: delfiData.publisher_name || delfiData.publisher || '',
    published_date: delfiData.published_date || '',

    // Identifiers
    isbn_13: delfiData.isbn_13 || '',
    isbn_10: delfiData.isbn_10 || '',

    // Physical
    page_count: delfiData.page_count || null,
    format: delfiData.format || '',
    language: delfiData.language || 'sr',

    // Visual
    cover_image_url: delfiData.cover_image_url || '',

    // Categorization
    categories: Array.isArray(delfiData.genres)
      ? delfiData.genres
      : (Array.isArray(delfiData.categories) ? delfiData.categories : []),

    // Delfi-specific
    price: delfiData.price || null,
    currency: delfiData.currency || 'RSD',

    // Source tracking
    source: 'delfi_scrape',
    source_id: delfiData.delfi_id || null,

    // Raw data for debugging
    raw_data: delfiData
  }
}

/**
 * Validate Delfi.rs URL
 * @param {string} url - URL to validate
 * @returns {boolean} - True if valid Delfi.rs URL
 */
export function isValidDelfiUrl(url) {
  try {
    const urlObj = new URL(url)
    return urlObj.hostname === 'delfi.rs' ||
           urlObj.hostname === 'www.delfi.rs'
  } catch {
    return false
  }
}

/**
 * Extract book ID from Delfi.rs URL
 * @param {string} url - Delfi.rs book URL
 * @returns {string|null} - Book ID or null
 */
export function extractDelfiBookId(url) {
  const match = url.match(/\/(\d+)-/)
  return match ? match[1] : null
}
