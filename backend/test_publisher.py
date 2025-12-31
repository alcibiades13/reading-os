#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick test to see publisher field extraction
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils.delfi_scraper import scrape_delfi_book

url = "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
print(f"Testing: {url}")
print("Please wait 3-5 seconds...")
print()

result = scrape_delfi_book(url)

if result:
    print("=== PUBLISHER FIELD ===")
    publisher = result.get('publisher')
    if publisher:
        print(f"Length: {len(publisher)} characters")
        print(f"Content: {publisher[:500]}")  # First 500 chars
    else:
        print("Publisher: NOT FOUND")

    print()
    print("=== ALL FIELDS ===")
    for key, value in result.items():
        if value and key != 'raw_data':
            if isinstance(value, str) and len(value) > 100:
                print(f"{key}: {value[:100]}...")
            else:
                print(f"{key}: {value}")
else:
    print("FAILED to scrape book")
