#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug Delfi HTML structure to find correct publisher selector
"""

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
    html_content = page.content()
    browser.close()

soup = BeautifulSoup(html_content, 'html.parser')

# Save full HTML to file for inspection
with open('delfi_page.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("HTML saved to delfi_page.html")
print()

# Look for publisher in various ways
print("=== SEARCHING FOR PUBLISHER (Izdavac) ===")
print()

# Search in text for "Izdavac:" pattern
page_text = soup.get_text()
matches = re.finditer(r'(Izdava[cč]):?\s*([^\n]{1,100})', page_text, re.IGNORECASE)

print("Found 'Izdavac' patterns:")
for i, match in enumerate(matches, 1):
    print(f"{i}. {match.group(0)[:100]}")
    print()

# Look in tables
print("=== TABLES ===")
tables = soup.find_all('table')
for i, table in enumerate(tables, 1):
    table_text = table.get_text()
    if 'Izdava' in table_text or 'izdava' in table_text:
        print(f"Table {i}:")
        print(table_text[:500])
        print()

# Look in divs with class containing "detail", "info", "spec"
print("=== INFO DIVS ===")
info_divs = soup.find_all('div', class_=re.compile(r'(detail|info|spec|product)', re.I))
for i, div in enumerate(info_divs[:5], 1):  # First 5 only
    div_text = div.get_text()
    if 'Izdava' in div_text or 'izdava' in div_text:
        print(f"Info Div {i} (class={div.get('class')}):")
        print(div_text[:300])
        print()
