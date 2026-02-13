"""
Management command to seed the database with books from OpenLibrary.

Uses OpenLibrary's Search API to pull popular books across various subjects,
creating Book, Author, and Genre records.

Usage:
    python manage.py seed_openlibrary                          # Default: ~2000 books
    python manage.py seed_openlibrary --limit 100              # 100 per subject
    python manage.py seed_openlibrary --subjects fiction poetry # Specific subjects only
    python manage.py seed_openlibrary --dry-run                # Preview without saving
    python manage.py seed_openlibrary --with-covers            # Download cover URLs (slower)
"""

import time
import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from apps.books.models import Book, Author, Genre, BookGroup

# Subjects to seed from OpenLibrary
DEFAULT_SUBJECTS = [
    # Major fiction
    'fiction',
    'literary_fiction',
    'classics',
    'historical_fiction',
    'science_fiction',
    'fantasy',
    'mystery',
    'thriller',
    'horror',
    'romance',
    # Non-fiction
    'biography',
    'autobiography',
    'history',
    'philosophy',
    'psychology',
    'science',
    'self_help',
    'essays',
    'travel',
    'true_crime',
    # Literary
    'poetry',
    'short_stories',
    'drama',
    # World literature
    'russian_literature',
    'french_literature',
    'japanese_literature',
    'latin_american_literature',
]

SUBJECT_TO_GENRE = {
    'fiction': 'Fiction',
    'literary_fiction': 'Literary Fiction',
    'classics': 'Classics',
    'historical_fiction': 'Historical Fiction',
    'science_fiction': 'Science Fiction',
    'fantasy': 'Fantasy',
    'mystery': 'Mystery',
    'thriller': 'Thriller',
    'horror': 'Horror',
    'romance': 'Romance',
    'biography': 'Biography',
    'autobiography': 'Autobiography',
    'history': 'History',
    'philosophy': 'Philosophy',
    'psychology': 'Psychology',
    'science': 'Science',
    'self_help': 'Self Help',
    'essays': 'Essays',
    'travel': 'Travel',
    'true_crime': 'True Crime',
    'poetry': 'Poetry',
    'short_stories': 'Short Stories',
    'drama': 'Drama',
    'russian_literature': 'Russian Literature',
    'french_literature': 'French Literature',
    'japanese_literature': 'Japanese Literature',
    'latin_american_literature': 'Latin American Literature',
}

OL_SEARCH_URL = 'https://openlibrary.org/search.json'
OL_COVER_URL = 'https://covers.openlibrary.org/b/id/{}-L.jpg'
REQUEST_DELAY = 1.0  # seconds between API calls (be respectful)


class Command(BaseCommand):
    help = 'Seed the database with books from OpenLibrary API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Number of books to fetch per subject (default: 100)'
        )
        parser.add_argument(
            '--subjects',
            nargs='+',
            default=None,
            help='Specific subjects to seed (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be created without saving'
        )
        parser.add_argument(
            '--with-covers',
            action='store_true',
            help='Include cover image URLs (enabled by default from search results)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between API requests in seconds (default: 1.0)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        subjects = options['subjects'] or list(DEFAULT_SUBJECTS)
        dry_run = options['dry_run']
        delay = options['delay']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f'\nOpenLibrary Seed {"(DRY RUN)" if dry_run else ""}'
        ))
        self.stdout.write(f'  Subjects: {len(subjects)}')
        self.stdout.write(f'  Limit per subject: {limit}')
        self.stdout.write(f'  Max potential books: {len(subjects) * limit}\n')

        stats = {
            'books_created': 0,
            'books_skipped': 0,
            'authors_created': 0,
            'genres_created': 0,
            'groups_created': 0,
            'errors': 0,
        }

        for i, subject in enumerate(subjects, 1):
            genre_name = SUBJECT_TO_GENRE.get(subject, subject.replace('_', ' ').title())
            self.stdout.write(
                f'[{i}/{len(subjects)}] Fetching "{genre_name}" ({subject})...'
            )

            try:
                books_data = self._fetch_subject(subject, limit, delay)
                self.stdout.write(f'  Got {len(books_data)} results')

                if not dry_run:
                    self._save_books(books_data, subject, genre_name, stats)
                else:
                    for book in books_data:
                        title = book.get('title', 'Unknown')
                        authors = ', '.join(book.get('author_name', [])[:2])
                        self.stdout.write(f'    [DRY] {title} — {authors}')
                        stats['books_created'] += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error: {e}'))
                stats['errors'] += 1

            # Small delay between subjects
            if i < len(subjects):
                time.sleep(delay)

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Books created:   {stats["books_created"]}'))
        self.stdout.write(f'Books skipped:   {stats["books_skipped"]}')
        self.stdout.write(f'Authors created: {stats["authors_created"]}')
        self.stdout.write(f'Genres created:  {stats["genres_created"]}')
        self.stdout.write(f'Groups created:  {stats["groups_created"]}')
        if stats['errors']:
            self.stdout.write(self.style.ERROR(f'Errors:          {stats["errors"]}'))
        self.stdout.write(self.style.SUCCESS('=' * 50))

    def _fetch_subject(self, subject, limit, delay):
        """Fetch books from OpenLibrary Search API for a given subject."""
        all_results = []
        page_size = min(limit, 100)  # OL max is 100 per request
        offset = 0

        while len(all_results) < limit:
            params = {
                'subject': subject.replace('_', ' '),
                'limit': page_size,
                'offset': offset,
                'fields': ','.join([
                    'key', 'title', 'author_name', 'author_key',
                    'first_publish_year', 'cover_i',
                    'isbn', 'number_of_pages_median',
                    'publisher', 'language', 'subject',
                    'edition_count',
                ]),
                'sort': 'editions',  # Most editions = most popular
            }

            response = requests.get(OL_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            docs = data.get('docs', [])
            if not docs:
                break

            all_results.extend(docs)
            offset += page_size

            if offset >= data.get('numFound', 0):
                break

            if len(all_results) < limit:
                time.sleep(delay)

        return all_results[:limit]

    def _get_or_create_genre(self, name):
        """Get or create a genre, matching by slug to avoid case duplicates."""
        slug = slugify(name)[:50]
        if not slug:
            return None
        genre, created = Genre.objects.get_or_create(
            slug=slug,
            defaults={'name': name}
        )
        return genre

    def _save_books(self, books_data, subject, genre_name, stats):
        """Save fetched books to the database."""
        genre = self._get_or_create_genre(genre_name)
        if genre:
            stats['genres_created'] += 1

        for book_data in books_data:
            try:
                with transaction.atomic():
                    self._save_single_book(book_data, genre, stats)
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'    Skip: {book_data.get("title", "?")} — {e}')
                )
                stats['errors'] += 1

    def _save_single_book(self, data, genre, stats):
        """Save a single book from OpenLibrary data."""
        title = data.get('title', '').strip()
        if not title:
            return

        author_names = data.get('author_name', [])
        if not author_names:
            return  # Skip books without authors

        # Extract ISBN (prefer ISBN-13)
        isbns = data.get('isbn', [])
        isbn = None
        for i in isbns:
            if len(i) == 13:
                isbn = i
                break
        if not isbn and isbns:
            isbn = isbns[0]

        # Check for duplicates by ISBN or title+author
        if isbn and Book.objects.filter(isbn=isbn).exists():
            stats['books_skipped'] += 1
            return

        primary_author = author_names[0] if author_names else ''
        if Book.objects.filter(
            title__iexact=title,
            authors__name__iexact=primary_author
        ).exists():
            stats['books_skipped'] += 1
            return

        # Create/get authors
        authors = []
        for name in author_names[:3]:  # Max 3 authors
            name = name.strip()
            if not name:
                continue
            author, created = Author.objects.get_or_create(name=name)
            if created:
                stats['authors_created'] += 1
            authors.append(author)

        if not authors:
            return

        # Cover image
        cover_id = data.get('cover_i')
        cover_url = OL_COVER_URL.format(cover_id) if cover_id else ''

        # Pages
        pages = data.get('number_of_pages_median')
        if pages and pages < 10:
            pages = None  # Likely bad data

        # Language (truncate to 10 chars max, OL sometimes returns long codes)
        languages = data.get('language', [])
        language = (languages[0] if languages else 'en')[:10]

        # Published year
        first_year = data.get('first_publish_year')
        published_date = None
        if first_year:
            try:
                from datetime import date
                published_date = date(int(first_year), 1, 1)
            except (ValueError, TypeError):
                pass

        # External IDs
        ol_key = data.get('key', '')  # e.g., "/works/OL123W"
        external_ids = {}
        if ol_key:
            external_ids['open_library_work'] = ol_key

        # Create BookGroup
        group = BookGroup.objects.create(canonical_title=title)
        group.canonical_authors.set(authors)
        stats['groups_created'] += 1

        # Create Book
        book = Book.objects.create(
            title=title,
            isbn=isbn if isbn else None,
            description='',  # Can be enriched later
            published_date=published_date,
            language=language,
            pages=pages,
            cover_image=cover_url,
            source='open_library',
            external_ids=external_ids,
            book_group=group,
            is_primary_edition=True,
        )
        book.authors.set(authors)
        book.genres.add(genre)

        stats['books_created'] += 1
        self.stdout.write(
            self.style.SUCCESS(f'    + {title} — {", ".join(a.name for a in authors)}')
        )
