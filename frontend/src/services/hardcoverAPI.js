import api from './api'

/**
 * Hardcover.app Book Search Service
 * Searches books via backend proxy (token stays server-side)
 */

/**
 * Search books on Hardcover
 * @param {string} query - Search query (title, author, ISBN)
 * @param {number} maxResults - Maximum results to return
 * @returns {Promise<Array>} - Array of formatted book objects
 */
export async function searchBooks(query, maxResults = 20) {
  try {
    const response = await api.get('/books/search_hardcover/', {
      params: { q: query, per_page: maxResults }
    })
    return (response.data || []).map(formatBookData)
  } catch (error) {
    console.error('Hardcover search error:', error)
    throw new Error(error.response?.data?.error || 'Failed to search Hardcover')
  }
}

/**
 * Search book by ISBN on Hardcover
 * @param {string} isbn - ISBN-10 or ISBN-13
 * @returns {Promise<Object|null>} - Formatted book object or null
 */
export async function searchByISBN(isbn) {
  try {
    const results = await searchBooks(isbn, 5)
    return results.length > 0 ? results[0] : null
  } catch {
    return null
  }
}

/**
 * Get full book details from Hardcover (includes publisher, editions, ISBNs)
 * @param {string|number} hardcoverId - Hardcover book ID
 * @returns {Promise<Object|null>} - Formatted book object with full details
 */
export async function getBookDetails(hardcoverId) {
  try {
    const response = await api.get('/books/hardcover_details/', {
      params: { id: hardcoverId }
    })
    return response.data ? formatBookData(response.data) : null
  } catch (error) {
    console.error('Hardcover details error:', error)
    return null
  }
}

/**
 * Format Hardcover data to match our standardized book format
 * @param {Object} data - Raw data from Hardcover API
 * @returns {Object} - Formatted book object
 */
function formatBookData(data) {
  return {
    // IDs
    hardcover_id: data.hardcover_id || null,

    // Basic Info
    title: data.title || '',
    subtitle: data.subtitle || '',
    authors: Array.isArray(data.authors) ? data.authors : [],
    description: data.description || '',

    // Publishing Info
    publisher: data.publisher_name || '',
    published_date: data.published_date || '',

    // Identifiers
    isbn_13: data.isbn_13 || '',
    isbn_10: data.isbn_10 || '',

    // Physical
    page_count: data.page_count || null,
    language: data.language || 'en',

    // Visual
    cover_image_url: data.cover_image_url || '',

    // Categorization
    categories: Array.isArray(data.genres) ? data.genres : [],

    // Source tracking
    source: 'hardcover',
    source_id: data.hardcover_id || null,
  }
}
