#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
print(f"Fetching: {url}\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(2000)
    html = page.content()
    browser.close()

soup = BeautifulSoup(html, 'html.parser')

# Save HTML
with open('talasi_full.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("HTML saved. Looking for product details...\n")

# Strategy 1: Look for all dd/dt pairs (definition lists)
dls = soup.find_all('dl')
if dls:
    print(f"Found {len(dls)} definition lists")
    for i, dl in enumerate(dls[:3], 1):
        print(f"\nDL {i}:")
        dts = dl.find_all('dt')
        dds = dl.find_all('dd')
        for dt, dd in zip(dts, dds):
            print(f"  {dt.get_text(strip=True)}: {dd.get_text(strip=True)}")

# Strategy 2: Look for divs/spans with label-value pattern
print("\n=== Looking for label-value patterns ===")
all_text = soup.get_text()

# Check if detail keywords exist in page
if 'Broj strana' in all_text:
    print("'Broj strana' found in page!")
    # Find the element containing it
    elem = soup.find(string=re.compile(r'Broj strana', re.I))
    if elem:
        print(f"Element: {elem.strip()}")
        print(f"Parent: {elem.parent.name}, class={elem.parent.get('class')}")

if 'Godina izdanja' in all_text:
    print("'Godina izdanja' found in page!")

if '272' in all_text:
    print("'272' (page count) found in page!")

# Strategy 3: Look for structured data that might have these fields
print("\n=== Checking JSON-LD ===")
json_ld = soup.find('script', type='application/ld+json')
if json_ld:
    import json
    data = json.loads(json_ld.string)
    print(f"JSON-LD fields: {list(data.keys())}")
    if 'numberOfPages' in data:
        print(f"numberOfPages: {data['numberOfPages']}")
