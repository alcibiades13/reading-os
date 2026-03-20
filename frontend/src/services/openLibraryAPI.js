import axios from 'axios'

const OPEN_LIBRARY_API_URL = 'https://openlibrary.org'

/**
 * Open Library API Service
 * Docs: https://openlibrary.org/developers/api
 */

/**
 * Search books by query (title, author, keywords)
 * @param {string} query - Search query
 * @param {number} limit - Maximum number of results (default: 20)
 * @returns {Promise<Array>} - Array of formatted book objects
 */
export async function searchBooks(query, limit = 20) {
  try {
    const response = await axios.get(`${OPEN_LIBRARY_API_URL}/search.json`, {
      params: {
        q: query,
        limit: limit,
        fields: 'key,title,subtitle,author_name,author_key,first_publish_year,publisher,language,isbn,number_of_pages_median,cover_i,subject,ratings_average,ratings_count',
      },
    })

    if (!response.data.docs || response.data.docs.length === 0) {
      return []
    }

    return response.data.docs.map(item => formatBookData(item))
  } catch (error) {
    throw new Error('Failed to search books from Open Library')
  }
}

/**
 * Search books by ISBN
 * @param {string} isbn - ISBN-10 or ISBN-13
 * @returns {Promise<Object|null>} - Formatted book object or null
 */
export async function searchByISBN(isbn) {
  try {
    const response = await axios.get(`${OPEN_LIBRARY_API_URL}/search.json`, {
      params: {
        isbn: isbn,
        fields: 'key,title,subtitle,author_name,author_key,first_publish_year,publisher,language,isbn,number_of_pages_median,cover_i,subject,ratings_average,ratings_count',
      },
    })

    if (!response.data.docs || response.data.docs.length === 0) {
      return null
    }

    // Return the first (most relevant) result
    return formatBookData(response.data.docs[0])
  } catch (error) {
    throw new Error('Failed to search book by ISBN')
  }
}

/**
 * Get book details by Open Library ID (work key)
 * @param {string} openLibraryId - Open Library work key (e.g., /works/OL45804W)
 * @returns {Promise<Object>} - Formatted book object
 */
export async function getBookById(openLibraryId) {
  try {
    // Normalize the ID to ensure it starts with /works/
    const workKey = openLibraryId.startsWith('/works/') ? openLibraryId : `/works/${openLibraryId}`

    const response = await axios.get(`${OPEN_LIBRARY_API_URL}${workKey}.json`)

    // Also fetch editions to get ISBN and other details
    const editionsResponse = await axios.get(`${OPEN_LIBRARY_API_URL}${workKey}/editions.json`, {
      params: { limit: 1 }
    })

    return formatWorkData(response.data, editionsResponse.data.entries?.[0])
  } catch (error) {
    throw new Error('Failed to fetch book details')
  }
}

/**
 * Format Open Library search result to our Book model
 * @param {Object} item - Open Library search result item
 * @returns {Object} - Formatted book object
 */
function formatBookData(item) {
  // Extract ISBNs
  const isbn13 = item.isbn?.find(isbn => isbn.length === 13) || null
  const isbn10 = item.isbn?.find(isbn => isbn.length === 10) || null

  // Cover image URL
  const coverImage = item.cover_i
    ? `https://covers.openlibrary.org/b/id/${item.cover_i}-L.jpg`
    : null

  // Language - Open Library uses ISO 639-2 (3 letter), convert to ISO 639-1 if possible
  const languageMap = {
    'eng': 'en',
    'srp': 'sr',
    'fra': 'fr',
    'deu': 'de',
    'spa': 'es',
    'ita': 'it',
    'rus': 'ru',
  }
  const language = item.language?.[0] ? (languageMap[item.language[0]] || item.language[0]) : 'en'

  return {
    // Open Library specific
    open_library_id: item.key, // e.g., /works/OL45804W
    open_library_link: `https://openlibrary.org${item.key}`,

    // Book details
    title: item.title || 'Unknown Title',
    subtitle: item.subtitle || null,
    authors: item.author_name || [], // Array of author names
    description: null, // Search API doesn't include description
    publisher: item.publisher?.[0] || null,
    published_date: item.first_publish_year ? `${item.first_publish_year}` : null,
    isbn_13: isbn13,
    isbn_10: isbn10,
    page_count: item.number_of_pages_median || null,
    language: language,
    cover_image_url: coverImage,

    // Categories/Genres (subjects)
    categories: item.subject?.slice(0, 5) || [], // Limit to 5 subjects

    // Additional info
    average_rating: item.ratings_average || null,
    ratings_count: item.ratings_count || null,
    preview_link: `https://openlibrary.org${item.key}`,

    // Source tracking
    source: 'open_library',
    source_id: item.key,

    // Raw data for debugging (optional)
    raw_data: item,
  }
}

/**
 * Format Open Library work data (from /works endpoint)
 * @param {Object} work - Work data
 * @param {Object} edition - Edition data (optional)
 * @returns {Object} - Formatted book object
 */
function formatWorkData(work, edition = null) {
  // Extract ISBNs from edition if available
  const isbn13 = edition?.isbn_13?.[0] || null
  const isbn10 = edition?.isbn_10?.[0] || null

  // Cover image - try edition cover first, then work cover
  let coverImage = null
  if (edition?.covers?.[0]) {
    coverImage = `https://covers.openlibrary.org/b/id/${edition.covers[0]}-L.jpg`
  } else if (work.covers?.[0]) {
    coverImage = `https://covers.openlibrary.org/b/id/${work.covers[0]}-L.jpg`
  }

  // Extract author names from author objects
  const authorNames = work.authors?.map(a => a.author?.name || 'Unknown') || []

  // Description - can be string or object with value
  const description = typeof work.description === 'string'
    ? work.description
    : work.description?.value || null

  return {
    // Open Library specific
    open_library_id: work.key,
    open_library_link: `https://openlibrary.org${work.key}`,

    // Book details
    title: work.title || 'Unknown Title',
    subtitle: work.subtitle || null,
    authors: authorNames,
    description: description,
    publisher: edition?.publishers?.[0] || null,
    published_date: edition?.publish_date || work.first_publish_year || null,
    isbn_13: isbn13,
    isbn_10: isbn10,
    page_count: edition?.number_of_pages || null,
    language: edition?.languages?.[0]?.key?.split('/')?.pop() || 'en',
    cover_image_url: coverImage,

    // Categories/Genres
    categories: work.subjects?.slice(0, 5) || [],

    // Additional info
    average_rating: null,
    ratings_count: null,
    preview_link: `https://openlibrary.org${work.key}`,

    // Source tracking
    source: 'open_library',
    source_id: work.key,

    // Raw data for debugging
    raw_data: { work, edition },
  }
}

/**
 * Search books with advanced filters
 * @param {Object} filters - Search filters
 * @param {string} filters.title - Book title
 * @param {string} filters.author - Author name
 * @param {string} filters.isbn - ISBN
 * @param {string} filters.publisher - Publisher name
 * @param {string} filters.subject - Subject/genre
 * @param {number} filters.limit - Max results
 * @returns {Promise<Array>} - Array of formatted book objects
 */
export async function advancedSearch(filters) {
  const params = {
    limit: filters.limit || 20,
    fields: 'key,title,subtitle,author_name,author_key,first_publish_year,publisher,language,isbn,number_of_pages_median,cover_i,subject,ratings_average,ratings_count',
  }

  // Build query - Open Library supports field-specific search
  if (filters.title) params.title = filters.title
  if (filters.author) params.author = filters.author
  if (filters.isbn) params.isbn = filters.isbn
  if (filters.publisher) params.publisher = filters.publisher
  if (filters.subject) params.subject = filters.subject

  // If no specific fields, require at least a general query
  if (!filters.title && !filters.author && !filters.isbn && !filters.publisher && !filters.subject) {
    throw new Error('At least one search filter is required')
  }

  try {
    const response = await axios.get(`${OPEN_LIBRARY_API_URL}/search.json`, { params })

    if (!response.data.docs || response.data.docs.length === 0) {
      return []
    }

    return response.data.docs.map(item => formatBookData(item))
  } catch (error) {
    throw new Error('Failed to perform advanced search')
  }
}

export default {
  searchBooks,
  searchByISBN,
  getBookById,
  advancedSearch,
}
