#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bs4 import BeautifulSoup

with open('delfi_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Look for description in various places
print("=== SEARCHING FOR FULL DESCRIPTION ===\n")

# 1. Check itemprop="description"
desc_itemprop = soup.find(attrs={'itemprop': 'description'})
if desc_itemprop:
    text = desc_itemprop.get_text(strip=True)
    print(f"1. [itemprop='description'] - Length: {len(text)}")
    print(f"   Text: {text[:200]}...\n")

# 2. Check class containing "description"
desc_divs = soup.find_all('div', class_=lambda x: x and 'description' in x.lower())
for i, div in enumerate(desc_divs[:3], 1):
    text = div.get_text(strip=True)
    print(f"2.{i} div[class*='description'] - Length: {len(text)}")
    print(f"    Class: {div.get('class')}")
    print(f"    Text: {text[:200]}...\n")

# 3. Look for "O knjizi" or similar headings
headings = soup.find_all(['h2', 'h3', 'h4'])
for heading in headings:
    text = heading.get_text(strip=True).lower()
    if 'o knjizi' in text or 'opis' in text or 'about' in text:
        print(f"3. Found heading: '{heading.get_text(strip=True)}'")
        # Get next sibling
        next_elem = heading.find_next_sibling()
        if next_elem:
            desc_text = next_elem.get_text(strip=True)
            print(f"   Next sibling: {next_elem.name}")
            print(f"   Length: {len(desc_text)}")
            print(f"   Text: {desc_text[:300]}...\n")

# 4. Check meta og:description
og_desc = soup.find('meta', property='og:description')
if og_desc:
    text = og_desc.get('content', '')
    print(f"4. meta[og:description] - Length: {len(text)}")
    print(f"   Text: {text[:200]}...\n")

# 5. Look for paragraphs with long text
print("5. Long paragraphs (>500 chars):")
paragraphs = soup.find_all('p')
for i, p in enumerate(paragraphs):
    text = p.get_text(strip=True)
    if len(text) > 500:
        print(f"   {i}. <p> Length: {len(text)}")
        print(f"      Parent: {p.parent.name if p.parent else 'None'}")
        print(f"      Parent class: {p.parent.get('class') if p.parent else 'None'}")
        print(f"      Text: {text[:200]}...\n")
