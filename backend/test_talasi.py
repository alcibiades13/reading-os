#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if 'utils.delfi_scraper' in sys.modules:
    del sys.modules['utils.delfi_scraper']

from utils.delfi_scraper import scrape_delfi_book

url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
print(f"Testing: {url}\n")

result = scrape_delfi_book(url)

if result:
    desc = result.get('description')
    print(f"Description length: {len(desc) if desc else 0} characters")

    if desc:
        with open('talasi_description.txt', 'w', encoding='utf-8') as f:
            f.write(desc)
        print("Description saved to talasi_description.txt")
        print(f"\nFirst 300 chars:\n{desc[:300]}")

    print(f"\nTitle: {result.get('title')}")
    print(f"Publisher: {result.get('publisher')}")
else:
    print("FAILED")
