#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if 'utils.delfi_scraper' in sys.modules:
    del sys.modules['utils.delfi_scraper']

from utils.delfi_scraper import DelfiScraper

scraper = DelfiScraper()

# Test date parsing
test_dates = [
    "6. septembar 2024.",
    "15. januar 2023.",
    "2024",
    "1. decembar 2022."
]

print("Testing Serbian date parsing:\n")
for date_str in test_dates:
    parsed = scraper._parse_serbian_date(date_str)
    print(f"'{date_str}' -> '{parsed}'")

print("\n\nNow testing full scrape:")
url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
result = scraper.scrape_book_by_url(url)

if result:
    print(f"\nPublished Date: {result.get('published_date')}")
    print(f"Format: YYYY-MM-DD? {bool(result.get('published_date') and '-' in result.get('published_date'))}")
else:
    print("FAILED")
