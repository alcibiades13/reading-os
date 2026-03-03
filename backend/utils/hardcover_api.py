"""
Hardcover.app GraphQL API client for book search and metadata.

Hardcover is a modern book tracking platform with comprehensive data
on recent English-language editions. Uses GraphQL API with bearer token auth.

API docs: https://docs.hardcover.app
Rate limit: 60 requests/minute
"""

import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

API_URL = 'https://api.hardcover.app/v1/graphql'

SEARCH_QUERY = """
query SearchBooks($query: String!, $per_page: Int) {
  search(query: $query, query_type: "books", per_page: $per_page) {
    results
  }
}
"""

BOOK_DETAILS_QUERY = """
query GetBook($id: Int!) {
  books(where: {id: {_eq: $id}}) {
    id
    title
    subtitle
    description
    pages
    release_date
    slug
    cached_tags
    image {
      url
    }
    contributions {
      author {
        name
      }
    }
    editions(order_by: {users_count: desc}, limit: 10) {
      isbn_10
      isbn_13
      pages
      release_date
      image {
        url
      }
      publisher {
        name
      }
    }
  }
}
"""


def _get_headers():
    token = getattr(settings, 'HARDCOVER_API_TOKEN', '')
    if not token:
        raise ValueError('HARDCOVER_API_TOKEN is not configured')
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }


def _graphql_request(query, variables=None):
    """Execute a GraphQL request against the Hardcover API."""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables

    response = requests.post(API_URL, json=payload, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    data = response.json()

    if 'errors' in data:
        logger.error('Hardcover GraphQL errors: %s', data['errors'])
        raise Exception(data['errors'][0].get('message', 'GraphQL error'))

    return data.get('data', {})


def search_books(query, per_page=20):
    """
    Search books on Hardcover.

    Returns a list of books in our common import format.
    """
    data = _graphql_request(SEARCH_QUERY, {
        'query': query,
        'per_page': per_page,
    })

    results = data.get('search', {}).get('results', {})
    hits = results.get('hits', []) if isinstance(results, dict) else []
    return [_transform_search_result(hit) for hit in hits if hit]


def get_book_details(book_id):
    """
    Get full book details by Hardcover book ID.

    Returns detailed book data including editions, ISBNs, and publisher info.
    """
    data = _graphql_request(BOOK_DETAILS_QUERY, {'id': int(book_id)})

    books = data.get('books', [])
    if not books:
        return None

    return _transform_book_details(books[0])


def _transform_search_result(hit):
    """Transform a Hardcover search hit to our common import format."""
    doc = hit.get('document', hit)

    # Authors
    authors = doc.get('author_names') or []
    if isinstance(authors, str):
        authors = [authors]

    # Cover image — doc.image is an object with 'url'
    cover_url = ''
    image = doc.get('image')
    if isinstance(image, dict) and image.get('url'):
        cover_url = image['url']

    # ISBNs — doc.isbns is a flat list of ISBN strings (10 and 13 mixed)
    isbn_13 = None
    isbn_10 = None
    for isbn in (doc.get('isbns') or []):
        if len(isbn) == 13 and not isbn_13:
            isbn_13 = isbn
        elif len(isbn) == 10 and not isbn_10:
            isbn_10 = isbn
        if isbn_13 and isbn_10:
            break

    # Release date
    release_date = doc.get('release_date') or ''
    if release_date and len(str(release_date)) >= 10:
        release_date = str(release_date)[:10]
    elif doc.get('release_year'):
        release_date = str(doc['release_year'])

    return {
        'title': doc.get('title', ''),
        'subtitle': doc.get('subtitle') or '',
        'description': doc.get('description') or '',
        'authors': authors,
        'publisher_name': None,
        'published_date': release_date,
        'isbn_13': isbn_13,
        'isbn_10': isbn_10,
        'page_count': doc.get('pages'),
        'language': doc.get('language') or 'en',
        'cover_image_url': cover_url,
        'genres': doc.get('genres') or [],
        'source': 'hardcover',
        'hardcover_id': str(doc.get('id', '')),
    }


def _transform_book_details(book):
    """Transform full Hardcover book details to our common import format."""
    # Authors from contributions
    authors = []
    for contrib in (book.get('contributions') or []):
        author = contrib.get('author', {})
        if author and author.get('name'):
            authors.append(author['name'])

    # Cover image
    cover_url = ''
    if book.get('image') and book['image'].get('url'):
        cover_url = book['image']['url']

    # Get ISBN and publisher from best edition
    isbn_13 = None
    isbn_10 = None
    publisher_name = None
    editions = book.get('editions') or []
    for edition in editions:
        if not isbn_13 and edition.get('isbn_13'):
            isbn_13 = edition['isbn_13']
        if not isbn_10 and edition.get('isbn_10'):
            isbn_10 = edition['isbn_10']
        if not publisher_name and edition.get('publisher', {}).get('name'):
            publisher_name = edition['publisher']['name']
        if isbn_13 and publisher_name:
            break

    # Release date
    release_date = book.get('release_date') or ''
    if release_date and len(release_date) >= 10:
        release_date = release_date[:10]  # YYYY-MM-DD

    # Extract genre names from cached_tags (nested dict with category keys)
    genres = []
    cached_tags = book.get('cached_tags') or {}
    if isinstance(cached_tags, dict):
        for tag_obj in cached_tags.get('Genre', []):
            if isinstance(tag_obj, dict) and tag_obj.get('tag'):
                genres.append(tag_obj['tag'])
    elif isinstance(cached_tags, list):
        genres = cached_tags

    return {
        'title': book.get('title', ''),
        'subtitle': book.get('subtitle') or '',
        'description': book.get('description') or '',
        'authors': authors,
        'publisher_name': publisher_name,
        'published_date': release_date,
        'isbn_13': isbn_13,
        'isbn_10': isbn_10,
        'page_count': book.get('pages'),
        'language': 'en',
        'cover_image_url': cover_url,
        'genres': genres,
        'source': 'hardcover',
        'hardcover_id': str(book.get('id', '')),
    }
