"""
Public-domain e-books from Project Gutenberg, via Gutenberg's own OPDS catalog
(the third-party Gutendex API proved too unreliable - uncached queries time out).
These are the only e-books shared across users - uploaded files always stay private.
"""
import hashlib
import re

import requests
from django.core.cache import cache
from lxml import etree

GUTENBERG = 'https://www.gutenberg.org'
SEARCH_URL = f'{GUTENBERG}/ebooks/search.opds/'
BOOK_URL = GUTENBERG + '/ebooks/{id}.opds'
EPUB_IMAGES_URL = GUTENBERG + '/ebooks/{id}.epub3.images'
EPUB_TEXT_URL = GUTENBERG + '/ebooks/{id}.epub.noimages'
COVER_URL = GUTENBERG + '/cache/epub/{id}/pg{id}.cover.medium.jpg'
HEADERS = {'User-Agent': 'ReadingOS/1.0 (personal reading app)'}

PAGE_SIZE = 25
SEARCH_TIMEOUT = 20
DOWNLOAD_TIMEOUT = 60
CACHE_SECONDS = 6 * 3600
# Illustrated editions can be huge; above this fall back to the text-only EPUB
MAX_ILLUSTRATED_BYTES = 15 * 1024 * 1024

NS = {'a': 'http://www.w3.org/2005/Atom', 'dc': 'http://purl.org/dc/terms/'}
XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
BOOK_ID_RE = re.compile(r'/ebooks/(\d+)\.opds$')
LANGUAGE_RE = re.compile(r'^[a-z]{2,3}$')


class CatalogUnavailable(Exception):
    """Project Gutenberg could not be reached."""


def display_name(name):
    """Catalog form 'Tolstoy, Leo, graf' -> 'Leo Tolstoy'."""
    parts = [p.strip() for p in name.split(',') if p.strip()]
    if len(parts) >= 2:
        return f'{parts[1]} {parts[0]}'
    return name.strip()


def _fetch(url, params=None, timeout=SEARCH_TIMEOUT, max_bytes=None):
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=timeout, stream=True)
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(64 * 1024):
            size += len(chunk)
            if max_bytes and size > max_bytes:
                return None
            chunks.append(chunk)
        return b''.join(chunks)
    except requests.RequestException as exc:
        raise CatalogUnavailable(str(exc)) from exc


def _fetch_feed(url, params=None):
    key = 'gutenberg-opds:' + hashlib.md5(f'{url}?{sorted((params or {}).items())}'.encode()).hexdigest()
    cached = cache.get(key)
    if cached is None:
        cached = _fetch(url, params)
        cache.set(key, cached, CACHE_SECONDS)
    try:
        return etree.fromstring(cached, parser=XML_PARSER)
    except etree.XMLSyntaxError as exc:
        raise CatalogUnavailable('Invalid catalog response') from exc


def _book_entry(entry):
    """Search-result entry -> dict, or None for navigation entries (Authors, Subjects...)."""
    match = BOOK_ID_RE.search(entry.findtext('a:id', '', NS))
    if not match:
        return None
    book_id = int(match.group(1))
    author = (entry.findtext('a:content', '', NS) or '').strip()
    if re.fullmatch(r'[\d,.]+ downloads?', author):  # shown in place of a missing author
        author = ''
    return {
        'id': book_id,
        'title': (entry.findtext('a:title', '', NS) or '').strip(),
        'authors': [author] if author else [],
        'cover_url': COVER_URL.format(id=book_id),
    }


def search(query='', language='', page=1):
    terms = query.strip()
    if language and LANGUAGE_RE.match(language):
        terms = f'{terms} l.{language}'.strip()

    params = {'start_index': (page - 1) * PAGE_SIZE + 1}
    if terms:
        params['query'] = terms
    else:
        params['sort_order'] = 'downloads'  # browse: most popular first

    feed = _fetch_feed(SEARCH_URL, params)
    results = [b for b in (_book_entry(e) for e in feed.findall('a:entry', NS)) if b]
    has_next = any(link.get('rel') == 'next' for link in feed.findall('a:link', NS))
    return {'results': results, 'has_next': has_next}


def get_book(book_id):
    """Full metadata for one book (author, language, EPUB availability)."""
    feed = _fetch_feed(BOOK_URL.format(id=int(book_id)))
    entry = feed.find('a:entry', NS)
    if entry is None:
        raise CatalogUnavailable('Book not found')
    links = entry.findall('a:link', NS)
    return {
        'id': int(book_id),
        'title': (entry.findtext('a:title', '', NS) or '').strip(),
        'authors': [display_name(a.findtext('a:name', '', NS)) for a in entry.findall('a:author', NS)],
        'languages': [(lang.text or '').strip() for lang in entry.findall('dc:language', NS) if lang.text],
        'cover_url': COVER_URL.format(id=int(book_id)),
        'has_epub': any((link.get('type') or '').startswith('application/epub') for link in links),
    }


def download_epub(book_id):
    """Illustrated EPUB when reasonably sized, otherwise the text-only edition."""
    data = _fetch(EPUB_IMAGES_URL.format(id=int(book_id)), timeout=DOWNLOAD_TIMEOUT, max_bytes=MAX_ILLUSTRATED_BYTES)
    if data is None:
        data = _fetch(EPUB_TEXT_URL.format(id=int(book_id)), timeout=DOWNLOAD_TIMEOUT)
    return data


def download_cover(url):
    if not url:
        return None
    try:
        return _fetch(url, max_bytes=2 * 1024 * 1024)
    except CatalogUnavailable:
        return None
