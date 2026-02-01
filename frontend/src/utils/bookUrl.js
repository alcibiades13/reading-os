/**
 * Generate a URL-friendly book path with slug
 * @param {Object} book - Book object with id and slug properties
 * @returns {string} URL path like "/books/14-orkanski-visovi"
 */
export function getBookUrl(book) {
  if (!book || !book.id) return '/books'

  if (book.slug) {
    return `/books/${book.id}-${book.slug}`
  }

  return `/books/${book.id}`
}

/**
 * Generate a URL-friendly book path for nested routes
 * @param {Object} book - Book object with id and slug properties
 * @param {string} suffix - Route suffix like "review" or "study"
 * @returns {string} URL path like "/books/14-orkanski-visovi/review"
 */
export function getBookUrlWithSuffix(book, suffix) {
  const baseUrl = getBookUrl(book)
  return `${baseUrl}/${suffix}`
}
