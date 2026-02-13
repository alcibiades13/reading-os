/**
 * Generate a URL path for an author detail page.
 * @param {Object} author - Author object with at least an id property
 * @returns {string} URL path like "/authors/42"
 */
export function getAuthorUrl(author) {
  if (!author || !author.id) return '/books'
  return `/authors/${author.id}`
}
