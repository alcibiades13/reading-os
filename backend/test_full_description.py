#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Force reload
if 'utils.delfi_scraper' in sys.modules:
    del sys.modules['utils.delfi_scraper']

from utils.delfi_scraper import scrape_delfi_book

url = "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
print(f"Testing FULL description extraction: {url}\n")

result = scrape_delfi_book(url)

if result:
    desc = result.get('description')

    print(f"Description length: {len(desc) if desc else 0} characters")
    print()

    if desc:
        # Write to file to avoid encoding issues
        with open('description_test.txt', 'w', encoding='utf-8') as f:
            f.write(desc)
        print("Full description saved to: description_test.txt")
        print()

        if len(desc) > 500:
            print("SUCCESS! Full description extracted!")
        else:
            print("FAIL! Description still truncated")
    else:
        print("FAIL! No description found")

    print()
    print(f"Title: {result.get('title')}")
    print(f"Authors: {result.get('authors')}")
    print(f"Publisher: {result.get('publisher')}")
else:
    print("FAILED to scrape book")
