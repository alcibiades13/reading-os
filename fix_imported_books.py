"""
Migration script to fix books imported from Goodreads CSV before fixes were applied:
1. Convert ratings from 5★ to 10★ scale
2. Add cover images from Goodreads using Book ID (stored in description temporarily)
"""
import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.books.models import Book
from apps.reading.models import UserBook
from django.contrib.auth import get_user_model
import csv
import io

User = get_user_model()

print("=== FIXING IMPORTED BOOKS ===\n")

# Get user
user = User.objects.first()
print(f"User: {user.email}\n")

# Load CSV to get Book IDs for cover extraction
csv_path = "frontend/lumina-library/goodreads/goodreads_library_export.csv"

# Allow override via command line
if len(sys.argv) > 1:
    csv_path = sys.argv[1].strip().strip('"')

print(f"Using CSV file: {csv_path}\n")

if not os.path.exists(csv_path):
    print(f"ERROR: File not found: {csv_path}")
    sys.exit(1)

# Read CSV and create mappings
print("Reading CSV file...")
book_id_map = {}  # ISBN/Title -> Goodreads ID
book_rating_map = {}  # ISBN/Title -> Rating
with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        title = row.get('Title', '').strip()
        isbn_raw = row.get('ISBN13', '') or row.get('ISBN', '')
        isbn = isbn_raw.replace('="', '').replace('"', '').strip()
        goodreads_id = row.get('Book Id', '').strip()
        rating_str = row.get('My Rating', '').strip()

        # Map Book ID
        if isbn and goodreads_id:
            book_id_map[isbn] = goodreads_id
        elif title and goodreads_id:
            book_id_map[title] = goodreads_id

        # Map Rating
        if rating_str and rating_str != '0':
            rating = float(rating_str) * 2  # Convert 5★ to 10★
            if isbn:
                book_rating_map[isbn] = rating
            elif title:
                book_rating_map[title] = rating

print(f"Found {len(book_id_map)} books with Goodreads IDs")
print(f"Found {len(book_rating_map)} books with ratings\n")

# Import/fix ratings from CSV
print("=== IMPORTING RATINGS FROM CSV ===")
all_user_books = UserBook.objects.filter(user=user).select_related('book')

ratings_added = 0
ratings_updated = 0

for ub in all_user_books:
    # Try to find rating from CSV
    rating_from_csv = None

    if ub.book.isbn and ub.book.isbn in book_rating_map:
        rating_from_csv = book_rating_map[ub.book.isbn]
    elif ub.book.title in book_rating_map:
        rating_from_csv = book_rating_map[ub.book.title]

    if rating_from_csv:
        old_rating = ub.rating
        ub.rating = rating_from_csv
        ub.save(update_fields=['rating'])

        if old_rating:
            print(f"  UPDATED: Book ID {ub.book.id}: {old_rating} -> {rating_from_csv}")
            ratings_updated += 1
        else:
            print(f"  ADDED: Book ID {ub.book.id}: -> {rating_from_csv}")
            ratings_added += 1

print(f"\nRatings added: {ratings_added}")
print(f"Ratings updated: {ratings_updated}\n")

# Fix covers
print("=== ADDING COVER IMAGES ===")
books_without_covers = Book.objects.filter(
    cover_image__in=['', None]
)

covers_added = 0
covers_failed = 0

import requests
from bs4 import BeautifulSoup

for book in books_without_covers:
    # Try to find Goodreads ID
    goodreads_id = None

    if book.isbn and book.isbn in book_id_map:
        goodreads_id = book_id_map[book.isbn]
    elif book.title in book_id_map:
        goodreads_id = book_id_map[book.title]

    if goodreads_id:
        try:
            gr_url = f'https://www.goodreads.com/book/show/{goodreads_id}'
            response = requests.get(gr_url, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                og_image = soup.find('meta', property='og:image')

                if og_image and og_image.get('content'):
                    cover_url = og_image['content']
                    book.cover_image = cover_url
                    book.save(update_fields=['cover_image'])
                    # Use ASCII-safe output
                    title_safe = book.title.encode('ascii', 'ignore').decode('ascii')
                    print(f"  [OK] {title_safe}: {cover_url[:60]}...")
                    covers_added += 1
                else:
                    print(f"  [FAIL] Book ID {book.id}: No og:image found")
                    covers_failed += 1
            else:
                print(f"  [FAIL] {book.title[:30]}: HTTP {response.status_code}")
                covers_failed += 1

        except Exception as e:
            print(f"  [FAIL] Book ID {book.id}: {str(e)[:60]}")
            covers_failed += 1
    else:
        # Skip message for books without Goodreads ID
        covers_failed += 1

print(f"\n=== SUMMARY ===")
print(f"Ratings added: {ratings_added}")
print(f"Ratings updated: {ratings_updated}")
print(f"Covers added: {covers_added}")
print(f"Covers failed: {covers_failed}")
print(f"\nDone!")
