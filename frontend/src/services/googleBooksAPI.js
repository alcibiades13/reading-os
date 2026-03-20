import axios from 'axios'

const GOOGLE_BOOKS_API_URL = 'https://www.googleapis.com/books/v1/volumes'

/**
 * Google Books API Service
 * Docs: https://developers.google.com/books/docs/v1/using
 */

/**
 * Search books by query (title, author, keywords)
 * @param {string} query - Search query
 * @param {number} maxResults - Maximum number of results (default: 20)
 * @returns {Promise<Array>} - Array of formatted book objects
 */
export async function searchBooks(query, maxResults = 20) {
  try {
    const response = await axios.get(GOOGLE_BOOKS_API_URL, {
      params: {
        q: query,
        maxResults: maxResults,
        langRestrict: '', // Empty = all languages
        printType: 'books', // Only books, not magazines
      },
    })

    if (!response.data.items) {
      return []
    }

    return response.data.items.map(item => formatBookData(item))
  } catch (error) {
    throw new Error('Failed to search books from Google Books')
  }
}

/**
 * Search books by ISBN
 * @param {string} isbn - ISBN-10 or ISBN-13
 * @returns {Promise<Object|null>} - Formatted book object or null
 */
export async function searchByISBN(isbn) {
  try {
    const response = await axios.get(GOOGLE_BOOKS_API_URL, {
      params: {
        q: `isbn:${isbn}`,
      },
    })

    if (!response.data.items || response.data.items.length === 0) {
      return null
    }

    // Return the first (most relevant) result
    return formatBookData(response.data.items[0])
  } catch (error) {
    throw new Error('Failed to search book by ISBN')
  }
}

/**
 * Get book details by Google Books ID
 * @param {string} googleBooksId - Google Books volume ID
 * @returns {Promise<Object>} - Formatted book object
 */
export async function getBookById(googleBooksId) {
  try {
    const response = await axios.get(`${GOOGLE_BOOKS_API_URL}/${googleBooksId}`)
    return formatBookData(response.data)
  } catch (error) {
    throw new Error('Failed to fetch book details')
  }
}

/**
 * Format Google Books API response to our Book model
 * @param {Object} item - Google Books API volume item
 * @returns {Object} - Formatted book object
 */
function formatBookData(item) {
  const volumeInfo = item.volumeInfo || {}
  const saleInfo = item.saleInfo || {}

  // Extract ISBN (prefer ISBN-13, fallback to ISBN-10)
  const isbn13 = volumeInfo.industryIdentifiers?.find(
    (id) => id.type === 'ISBN_13'
  )?.identifier
  const isbn10 = volumeInfo.industryIdentifiers?.find(
    (id) => id.type === 'ISBN_10'
  )?.identifier

  // Extract cover image (prefer high-res)
  const coverImage =
    volumeInfo.imageLinks?.large ||
    volumeInfo.imageLinks?.medium ||
    volumeInfo.imageLinks?.thumbnail ||
    volumeInfo.imageLinks?.smallThumbnail ||
    null

  // Replace http with https for cover images
  const secureCoverImage = coverImage ? coverImage.replace('http://', 'https://') : null

  return {
    // Google Books specific
    google_books_id: item.id,
    google_books_link: volumeInfo.infoLink || null,

    // Book details
    title: volumeInfo.title || 'Unknown Title',
    subtitle: volumeInfo.subtitle || null,
    authors: volumeInfo.authors || [], // Array of author names
    description: volumeInfo.description || null,
    publisher: volumeInfo.publisher || null,
    published_date: volumeInfo.publishedDate || null, // Format: YYYY or YYYY-MM-DD
    isbn_13: isbn13 || null,
    isbn_10: isbn10 || null,
    page_count: volumeInfo.pageCount || null,
    language: volumeInfo.language || 'en', // ISO 639-1 code
    cover_image_url: secureCoverImage,

    // Categories/Genres
    categories: volumeInfo.categories || [], // Array of genre strings

    // Additional info
    average_rating: volumeInfo.averageRating || null,
    ratings_count: volumeInfo.ratingsCount || null,
    preview_link: volumeInfo.previewLink || null,

    // Source tracking
    source: 'google_books',
    source_id: item.id,

    // Raw data for debugging (optional)
    raw_data: item,
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
 * @param {number} filters.maxResults - Max results
 * @returns {Promise<Array>} - Array of formatted book objects
 */
export async function advancedSearch(filters) {
  const queryParts = []

  if (filters.title) {
    queryParts.push(`intitle:${filters.title}`)
  }
  if (filters.author) {
    queryParts.push(`inauthor:${filters.author}`)
  }
  if (filters.isbn) {
    queryParts.push(`isbn:${filters.isbn}`)
  }
  if (filters.publisher) {
    queryParts.push(`inpublisher:${filters.publisher}`)
  }
  if (filters.subject) {
    queryParts.push(`subject:${filters.subject}`)
  }

  if (queryParts.length === 0) {
    throw new Error('At least one search filter is required')
  }

  const query = queryParts.join('+')
  return searchBooks(query, filters.maxResults || 20)
}

export default {
  searchBooks,
  searchByISBN,
  getBookById,
  advancedSearch,
}
