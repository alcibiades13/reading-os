#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

if 'utils.delfi_scraper' in sys.modules:
    del sys.modules['utils.delfi_scraper']

from utils.delfi_scraper import scrape_delfi_book

url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
print(f"Testing with Deklaracija tab: {url}\n")

result = scrape_delfi_book(url)

if result:
    print("=== EXTRACTED DATA ===")
    print(f"Title: {result.get('title')}")
    print(f"Authors: {result.get('authors')}")
    print(f"Publisher: {result.get('publisher')}")
    print(f"ISBN-13: {result.get('isbn_13')}")
    print(f"Page Count: {result.get('page_count')}")
    print(f"Published Date: {result.get('published_date')}")
    print(f"Format: {result.get('format')}")
    print(f"Price: {result.get('price')}")
    print()

    if result.get('page_count'):
        print("SUCCESS! Page count extracted from Deklaracija tab!")
    else:
        print("FAIL! Page count not found")

    if result.get('published_date'):
        print(f"SUCCESS! Published date extracted: {result.get('published_date')}")
    else:
        print("FAIL! Published date not found")
else:
    print("FAILED to scrape")
