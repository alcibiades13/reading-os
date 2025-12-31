"""Test genre filtering in API"""

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
print("TESTING GENRE FILTERING")
print("=" * 80)

# Get genre ID 8 (mitologija)
genre = Genre.objects.filter(id=8).first()
if genre:
    print(f"\nGenre ID 8: {genre.name}")

    # Test the filter
    books = Book.objects.filter(genres__id=8).distinct()
    print(f"Books with genre ID 8: {books.count()}")

    for book in books:
        print(f"  - {book.title}")
else:
    print("\nGenre ID 8 not found!")

# Try with genre name 'mitologija'
print("\n" + "=" * 80)
print("FILTERING BY NAME 'mitologija':")
print("=" * 80)

genre = Genre.objects.filter(name='mitologija').first()
if genre:
    print(f"\nFound genre: {genre.name} (ID: {genre.id})")
    books = Book.objects.filter(genres__id=genre.id).distinct()
    print(f"Books with this genre: {books.count()}")

    for book in books:
        genres_list = ', '.join([g.name for g in book.genres.all()])
        print(f"  - {book.title} (Genres: {genres_list})")
else:
    print("\nGenre 'mitologija' not found!")

# List all Genre IDs and names
print("\n" + "=" * 80)
print("ALL GENRES:")
print("=" * 80)

for g in Genre.objects.all():
    book_count = Book.objects.filter(genres__id=g.id).count()
    print(f"  ID {g.id}: {g.name} ({book_count} books)")
