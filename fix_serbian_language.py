"""
Manually fix language for Serbian books based on known Serbian authors/publishers
"""
import os
import sys
import django

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.books.models import Book

print("=== FIXING SERBIAN BOOK LANGUAGES ===\n")

# Known Serbian publishers
serbian_publishers = [
    'Laguna',
    'Vulkan',
    'Alnari',
    'Dereta',
    'Booka',
    'Evro Giunti',
    'Prosveta',
    'Mono',
    'Mono & Manjana',
    'Paideia',
    'Geopoetika',
    'Plato',
    'Zavod',
    'Rad',
    'Nolit',
]

# Known Serbian/Balkan authors
serbian_authors = [
    'Danilo Kiš',
    'Milorad Pavić',
    'Ivo Andrić',
    'Mesa Selimovic',
    'Meša Selimović',
    'Aleksandar Tišma',
    'Borislav Pekić',
    'Miloš Crnjanski',
]

books_updated = 0

# Update by publisher (check both 'en' and empty string)
for pub_name in serbian_publishers:
    books = Book.objects.filter(publisher__name__icontains=pub_name).exclude(language='sr')
    count = books.count()
    if count > 0:
        books.update(language='sr')
        books_updated += count
        print(f"  Updated {count} books from publisher '{pub_name}'")

# Update by author (check both 'en' and empty string)
for author_name in serbian_authors:
    books = Book.objects.filter(authors__name__icontains=author_name).exclude(language='sr')
    count = books.count()
    if count > 0:
        books.update(language='sr')
        books_updated += count
        # Use ASCII-safe output
        author_safe = author_name.encode('ascii', 'ignore').decode('ascii')
        print(f"  Updated {count} books by author '{author_safe}'")

print(f"\n=== SUMMARY ===")
print(f"Total books updated to Serbian: {books_updated}")
print(f"\nDone!")
