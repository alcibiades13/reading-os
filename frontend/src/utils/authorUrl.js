/**
 * Generate a URL path for an author detail page.
 * @param {Object} author - Author object with id and optional slug properties
 * @returns {string} URL path like "/authors/11-ivo-andric"
 */
export function getAuthorUrl(author) {
  if (!author || !author.id) return '/books'

  if (author.slug) {
    return `/authors/${author.id}-${author.slug}`
  }

  return `/authors/${author.id}`
}
