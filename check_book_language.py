"""
Check specific book language and publisher
"""
import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.books.models import Book

# Search for "Pisma iz Norveške"
books = Book.objects.filter(title__icontains='Pisma iz Norveške')

if books.exists():
    for book in books:
        print(f"Title: {book.title}")
        print(f"Language: '{book.language}'")
        print(f"Publisher: {book.publisher.name if book.publisher else 'None'}")
        print(f"Authors: {', '.join([a.name for a in book.authors.all()])}")
        print()
else:
    print("Book not found!")

# Also check all books with empty or 'en' language
print("\n=== Books with non-Serbian language ===")
non_sr_books = Book.objects.exclude(language='sr')[:10]
for book in non_sr_books:
    pub_name = book.publisher.name if book.publisher else 'None'
    authors = ', '.join([a.name for a in book.authors.all()])
    print(f"{book.title} | Lang: '{book.language}' | Pub: {pub_name} | Author: {authors}")
