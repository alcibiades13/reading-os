import csv

with open('frontend/lumina-library/goodreads/goodreads_library_export.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    books_with_ratings = [r for r in reader if r.get('My Rating') and r.get('My Rating') != '0']

print(f'Books with ratings: {len(books_with_ratings)}')
print('\nSample ratings:')
for r in books_with_ratings[:10]:
    print(f"{r['Title'][:50]}: {r['My Rating']}")
