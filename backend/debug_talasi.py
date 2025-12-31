#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
print(f"Fetching: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')

# Save HTML
with open('talasi_page.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML saved to talasi_page.html")
print()

# Look for description divs
desc_divs = soup.find_all('div', class_=lambda x: x and 'description' in x.lower())
print(f"Found {len(desc_divs)} divs with 'description' in class")

for i, div in enumerate(desc_divs[:3], 1):
    text = div.get_text(strip=True)
    print(f"\nDiv {i} (class={div.get('class')})")
    print(f"Length: {len(text)} chars")
    if len(text) > 300:
        print("This might be the full description!")
