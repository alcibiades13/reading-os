"""Test script to find categories on Delfi book page"""

import requests
from bs4 import BeautifulSoup

url = 'https://delfi.rs/knjige/111117-ohridski-prolog-knjiga-delfi-knjizare.html'

# Fetch page
response = requests.get(url, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

soup = BeautifulSoup(response.text, 'html.parser')

# Try to find categories - look for common patterns
print("=" * 80)
print("SEARCHING FOR CATEGORIES")
print("=" * 80)

# Strategy 1: Look for links with category/kategorija in href
print("\n1. Links with 'kategorija' in href:")
cat_links = soup.find_all('a', href=lambda h: h and 'kategorija' in h.lower())
for link in cat_links[:10]:
    print(f"   - {link.get_text().strip()} -> {link.get('href')}")

# Strategy 2: Look for elements with common category class names
print("\n2. Elements with category-related classes:")
category_classes = ['category', 'categories', 'tag', 'tags', 'breadcrumb', 'genre']
for class_name in category_classes:
    elems = soup.find_all(class_=lambda c: c and class_name in str(c).lower())
    if elems:
        print(f"\n   Class '{class_name}':")
        for elem in elems[:3]:
            print(f"      {elem.name} - {elem.get_text().strip()[:100]}")

# Strategy 3: Look near the title
print("\n3. Looking near title (h1):")
h1 = soup.find('h1')
if h1:
    # Check siblings and parents
    parent = h1.find_parent()
    if parent:
        # Get all links before h1 in the same container
        all_links = parent.find_all('a')
        print(f"   Links in same container as h1:")
        for link in all_links[:15]:
            text = link.get_text().strip()
            href = link.get('href', '')
            if text and len(text) < 100:
                print(f"      - {text} -> {href}")

# Strategy 4: Save full HTML around title for manual inspection
print("\n4. HTML structure around title:")
if h1:
    parent = h1.find_parent()
    if parent and parent.find_parent():
        grandparent = parent.find_parent()
        print(f"\nGrandparent of h1 tag: {grandparent.name}")
        # Get first 2000 chars
        html_str = str(grandparent)[:2000]
        print(html_str)

# Strategy 5: Look for specific text patterns
print("\n\n5. Searching for specific category names:")
search_terms = ['Autobiografije', 'Domaći pisci', 'Religija', 'Teologija']
for term in search_terms:
    elems = soup.find_all(string=lambda text: text and term in text)
    if elems:
        print(f"\n   Found '{term}':")
        for elem in elems[:2]:
            parent = elem.find_parent()
            print(f"      Parent: {parent.name if parent else 'None'}, text: {str(elem).strip()[:100]}")
