#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

url = "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
print(f"Fetching: {url}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')

# Save for inspection
with open('delfi_details.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Looking for product details...")
print()

# Look for tables with product info
tables = soup.find_all('table')
print(f"Found {len(tables)} tables")

for i, table in enumerate(tables[:3], 1):
    print(f"\n=== TABLE {i} ===")
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all(['td', 'th'])
        if len(cols) >= 2:
            label = cols[0].get_text(strip=True)
            value = cols[1].get_text(strip=True)
            print(f"  {label}: {value}")

# Look for divs/sections with product info
print("\n=== Looking for product detail sections ===")
detail_sections = soup.find_all(['div', 'section'], class_=re.compile(r'detail|info|spec|product', re.I))
for i, section in enumerate(detail_sections[:5], 1):
    text = section.get_text(strip=True)
    if 'Broj strana' in text or 'Godina' in text or 'Povez' in text:
        print(f"\nSection {i} (class={section.get('class')})")
        print(f"Text preview: {text[:300]}")
