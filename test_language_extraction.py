"""
Test language extraction from Goodreads
"""
import requests
from bs4 import BeautifulSoup

# Test with a known Serbian book - Seobe (Book ID from your CSV)
goodreads_book_id = "9266094"  # Veronika decides to die

gr_url = f'https://www.goodreads.com/book/show/{goodreads_book_id}'
print(f"Fetching: {gr_url}\n")

response = requests.get(gr_url, timeout=10, headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

print(f"Status: {response.status_code}\n")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try to find language
    print("=== Looking for language ===")

    # New method: Look for DescList
    desc_list = soup.find('dl', class_='DescList')
    if desc_list:
        print("Found DescList")
        items = desc_list.find_all('div', class_='DescListItem')
        print(f"Found {len(items)} DescListItem elements\n")

        for item in items:
            dt = item.find('dt')
            if dt:
                dt_text = dt.get_text(strip=True)
                print(f"  Label: {dt_text}")

                if dt_text == 'Language':
                    dd = item.find('dd')
                    if dd:
                        content_div = dd.find('div', {'data-testid': 'contentContainer'})
                        if content_div:
                            lang_text = content_div.get_text(strip=True)
                            print(f"  -> ✅ Language found: '{lang_text}'")
    else:
        print("DescList NOT FOUND")

    # Save HTML for inspection
    with open('goodreads_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nSaved HTML to goodreads_page.html for inspection")
