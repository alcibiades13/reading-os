import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import googleBooksAPI from '@/services/googleBooksAPI'
import openLibraryAPI from '@/services/openLibraryAPI'
import * as delfiAPI from '@/services/delfiAPI'
import { booksAPI } from '@/services/api'

export const useBookImportStore = defineStore('bookImport', () => {
  // State
  const searchResults = ref([])
  const loading = ref(false)
  const error = ref(null)
  const searchQuery = ref('')
  const selectedBook = ref(null)
  const importSource = ref('both') // 'google_books', 'open_library', 'delfi_rs', 'both'
  const delfiUrl = ref('') // For direct Delfi.rs URL input

  // Computed
  const hasResults = computed(() => searchResults.value.length > 0)

  // Actions

  /**
   * Search books from selected source(s)
   * @param {string} query - Search query (title, author, keywords)
   */
  async function searchBooks(query) {
    if (!query || query.trim().length < 2) {
      error.value = 'Please enter at least 2 characters'
      return
    }

    loading.value = true
    error.value = null
    searchQuery.value = query

    try {
      let results = []

      if (importSource.value === 'google_books') {
        results = await googleBooksAPI.searchBooks(query, 40)
      } else if (importSource.value === 'open_library') {
        results = await openLibraryAPI.searchBooks(query, 40)
      } else if (importSource.value === 'both') {
        // Search both sources in parallel
        const [googleResults, openLibraryResults] = await Promise.all([
          googleBooksAPI.searchBooks(query, 20).catch(() => []),
          openLibraryAPI.searchBooks(query, 20).catch(() => [])
        ])

        // Merge and deduplicate by ISBN
        results = mergeAndDeduplicateResults([...googleResults, ...openLibraryResults])
      }

      searchResults.value = results

      if (results.length === 0) {
        error.value = 'No books found. Try a different search term.'
      }
    } catch (err) {
      error.value = err.message || 'Failed to search books'
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Search by ISBN
   * @param {string} isbn - ISBN-10 or ISBN-13
   */
  async function searchByISBN(isbn) {
    if (!isbn || isbn.trim().length < 10) {
      error.value = 'Please enter a valid ISBN (10 or 13 digits)'
      return
    }

    loading.value = true
    error.value = null
    searchQuery.value = isbn

    try {
      let results = []

      if (importSource.value === 'google_books') {
        const result = await googleBooksAPI.searchByISBN(isbn)
        if (result) results = [result]
      } else if (importSource.value === 'open_library') {
        const result = await openLibraryAPI.searchByISBN(isbn)
        if (result) results = [result]
      } else if (importSource.value === 'both') {
        // Search both sources in parallel
        const [googleResult, openLibraryResult] = await Promise.all([
          googleBooksAPI.searchByISBN(isbn).catch(() => null),
          openLibraryAPI.searchByISBN(isbn).catch(() => null)
        ])

        // Prefer result with more data
        if (googleResult && openLibraryResult) {
          results = [googleResult] // Prefer Google Books as it usually has more complete data
        } else if (googleResult) {
          results = [googleResult]
        } else if (openLibraryResult) {
          results = [openLibraryResult]
        }
      }

      if (results.length > 0) {
        searchResults.value = results
        selectedBook.value = results[0]
      } else {
        searchResults.value = []
        error.value = 'No book found with this ISBN'
      }
    } catch (err) {
      error.value = err.message || 'Failed to search by ISBN'
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Scrape book from Delfi.rs URL
   * @param {string} url - Delfi.rs book URL
   */
  async function scrapeDelfiBook(url) {
    if (!url || !delfiAPI.isValidDelfiUrl(url)) {
      error.value = 'Please enter a valid Delfi.rs book URL'
      return
    }

    loading.value = true
    error.value = null
    delfiUrl.value = url

    try {
      const result = await delfiAPI.scrapeBookByUrl(url)

      if (result) {
        searchResults.value = [result]
        selectedBook.value = result
      } else {
        searchResults.value = []
        error.value = 'Failed to scrape book from URL'
      }
    } catch (err) {
      error.value = err.message || 'Failed to scrape book from Delfi.rs'
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Advanced search with filters
   * @param {Object} filters - { title, author, isbn, publisher, subject }
   */
  async function advancedSearch(filters) {
    loading.value = true
    error.value = null

    try {
      let results = []

      if (importSource.value === 'google_books') {
        results = await googleBooksAPI.advancedSearch(filters)
      } else if (importSource.value === 'open_library') {
        results = await openLibraryAPI.advancedSearch(filters)
      } else if (importSource.value === 'both') {
        // Search both sources in parallel
        const [googleResults, openLibraryResults] = await Promise.all([
          googleBooksAPI.advancedSearch(filters).catch(() => []),
          openLibraryAPI.advancedSearch(filters).catch(() => [])
        ])

        // Merge and deduplicate
        results = mergeAndDeduplicateResults([...googleResults, ...openLibraryResults])
      }
      // Note: Delfi.rs doesn't support advanced search yet

      searchResults.value = results

      if (results.length === 0) {
        error.value = 'No books found matching your criteria'
      }
    } catch (err) {
      error.value = err.message || 'Advanced search failed'
      searchResults.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Merge and deduplicate book results from multiple sources by ISBN
   * @param {Array} books - Array of book objects from different sources
   * @returns {Array} - Deduplicated array of books
   */
  function mergeAndDeduplicateResults(books) {
    const isbnMap = new Map()
    const titleAuthorMap = new Map()
    const uniqueBooks = []

    for (const book of books) {
      const isbn = book.isbn_13 || book.isbn_10

      // If book has ISBN, use it as primary deduplication key
      if (isbn) {
        if (!isbnMap.has(isbn)) {
          isbnMap.set(isbn, book)
          uniqueBooks.push(book)
        } else {
          // Book with this ISBN already exists, prefer one with more data
          const existing = isbnMap.get(isbn)
          if (hasMoreCompleteData(book, existing)) {
            // Replace existing with more complete version
            const index = uniqueBooks.indexOf(existing)
            uniqueBooks[index] = book
            isbnMap.set(isbn, book)
          }
        }
      } else {
        // No ISBN, use title + first author as fallback key
        const key = `${book.title.toLowerCase()}_${book.authors[0]?.toLowerCase() || 'unknown'}`

        if (!titleAuthorMap.has(key)) {
          titleAuthorMap.set(key, book)
          uniqueBooks.push(book)
        }
      }
    }

    return uniqueBooks
  }

  /**
   * Check if book1 has more complete data than book2
   * @param {Object} book1 - First book
   * @param {Object} book2 - Second book
   * @returns {boolean} - True if book1 is more complete
   */
  function hasMoreCompleteData(book1, book2) {
    let score1 = 0
    let score2 = 0

    // Score based on available fields
    const fieldsToCheck = ['description', 'cover_image_url', 'page_count', 'publisher', 'published_date', 'categories']

    fieldsToCheck.forEach(field => {
      if (book1[field] && (!Array.isArray(book1[field]) || book1[field].length > 0)) score1++
      if (book2[field] && (!Array.isArray(book2[field]) || book2[field].length > 0)) score2++
    })

    return score1 > score2
  }

  /**
   * Set the import source
   * @param {string} source - 'google_books', 'open_library', or 'both'
   */
  function setImportSource(source) {
    importSource.value = source
  }

  /**
   * Select a book for preview/import
   * @param {Object} book - Book object from search results
   */
  function selectBook(book) {
    selectedBook.value = book
  }

  /**
   * Clear selected book
   */
  function clearSelectedBook() {
    selectedBook.value = null
  }

  /**
   * Import book to our database and optionally add to library
   * @param {Object} payload - { book, addToLibrary, libraryData }
   * @returns {Promise<Object>} - { success, book, error }
   */
  async function importBookToDatabase(payload) {
    loading.value = true
    error.value = null

    try {
      // Prepare data for our backend
      const bookPayload = prepareBookPayload(payload.book)

      // Build request payload
      const requestPayload = {
        book: bookPayload,
        addToLibrary: payload.addToLibrary || false,
        libraryData: payload.libraryData || null,
      }

      // Send to backend using import endpoint
      const response = await booksAPI.importBook(requestPayload)

      return {
        success: true,
        book: response.data,
        error: null,
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to import book'
      error.value = errorMsg

      return {
        success: false,
        book: null,
        error: errorMsg,
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Prepare book data for our backend API
   * @param {Object} bookData - Book data from external API (Google Books or Open Library)
   * @returns {Object} - Backend-compatible book object
   */
  function prepareBookPayload(bookData) {
    return {
      title: bookData.title,
      subtitle: bookData.subtitle || '',
      description: bookData.description || '',
      isbn_13: bookData.isbn_13 || null,
      isbn_10: bookData.isbn_10 || null,
      cover_image_url: bookData.cover_image_url || null,
      published_date: bookData.published_date || null,
      page_count: bookData.page_count || null,
      language: bookData.language || 'en',

      // External IDs for tracking
      google_books_id: bookData.google_books_id || null,
      open_library_id: bookData.open_library_id || null,
      delfi_id: bookData.delfi_id || null,

      // Source tracking
      source: bookData.source || 'google_books',

      // Authors - will be created/linked in backend
      authors: bookData.authors || [],

      // Publisher - will be created/linked in backend
      publisher_name: bookData.publisher || null,

      // Genres/categories - will be processed in backend
      genres: bookData.categories || [],
    }
  }

  /**
   * Clear all search results
   */
  function clearResults() {
    searchResults.value = []
    searchQuery.value = ''
    error.value = null
  }

  /**
   * Reset store to initial state
   */
  function resetStore() {
    searchResults.value = []
    loading.value = false
    error.value = null
    searchQuery.value = ''
    selectedBook.value = null
    importSource.value = 'both'
  }

  return {
    // State
    searchResults,
    loading,
    error,
    searchQuery,
    selectedBook,
    importSource,
    delfiUrl,

    // Computed
    hasResults,

    // Actions
    searchBooks,
    searchByISBN,
    scrapeDelfiBook,
    advancedSearch,
    selectBook,
    clearSelectedBook,
    importBookToDatabase,
    clearResults,
    resetStore,
    setImportSource,
  }
})
