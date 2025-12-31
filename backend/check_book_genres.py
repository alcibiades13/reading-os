"""Script to check if books have genres associated with them"""

import os
import sys
import django

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.books.models import Book, Genre

print("=" * 80)
print("CHECKING BOOK-GENRE ASSOCIATIONS")
print("=" * 80)

# Get all genres
genres = Genre.objects.all()
print(f"\nTotal genres in database: {genres.count()}")
for genre in genres:
    print(f"  - {genre.name} (ID: {genre.id})")

# Get all books
books = Book.objects.all()
print(f"\nTotal books in database: {books.count()}")

# Check books with genres
books_with_genres = Book.objects.filter(genres__isnull=False).distinct()
print(f"\nBooks with at least one genre: {books_with_genres.count()}")

# Check books without genres
books_without_genres = Book.objects.filter(genres__isnull=True)
print(f"Books without genres: {books_without_genres.count()}")

# Sample some books
print("\n" + "=" * 80)
print("SAMPLE BOOKS AND THEIR GENRES:")
print("=" * 80)

for book in books[:10]:
    book_genres = book.genres.all()
    genre_names = [g.name for g in book_genres]
    print(f"\nBook: {book.title}")
    print(f"  External IDs: {book.external_ids}")
    print(f"  Genres ({book_genres.count()}): {', '.join(genre_names) if genre_names else 'NONE'}")

# Check if "Ohridski prolog" book exists and has genres
print("\n" + "=" * 80)
print("SEARCHING FOR 'OHRIDSKI PROLOG':")
print("=" * 80)

ohridski = Book.objects.filter(title__icontains='ohridski').first()
if ohridski:
    print(f"\nFound: {ohridski.title}")
    print(f"  ID: {ohridski.id}")
    print(f"  External IDs: {ohridski.external_ids}")
    print(f"  Authors: {', '.join([a.name for a in ohridski.authors.all()])}")
    print(f"  Genres: {', '.join([g.name for g in ohridski.genres.all()])}")
    print(f"  Total genres: {ohridski.genres.count()}")
else:
    print("\nBook not found!")

# Check Delfi books specifically
print("\n" + "=" * 80)
print("CHECKING DELFI BOOKS:")
print("=" * 80)

delfi_books = Book.objects.filter(external_ids__has_key='delfi_id')
print(f"\nTotal Delfi books: {delfi_books.count()}")

for book in delfi_books[:5]:
    book_genres = book.genres.all()
    print(f"\n{book.title}")
    print(f"  Delfi ID: {book.external_ids.get('delfi_id')}")
    print(f"  Genres ({book_genres.count()}): {', '.join([g.name for g in book_genres])}")
