#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Reload the module to get the fix
import importlib
if 'utils.delfi_scraper' in sys.modules:
    del sys.modules['utils.delfi_scraper']

from utils.delfi_scraper import scrape_delfi_book

url = "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
print(f"Testing FIXED scraper: {url}\n")

result = scrape_delfi_book(url)

if result:
    publisher = result.get('publisher')
    print(f"Publisher: '{publisher}'")
    print(f"Length: {len(publisher) if publisher else 0} characters")
    print()

    if publisher and len(publisher) < 100:
        print("SUCCESS! Publisher field looks correct now!")
    else:
        print("FAIL! Publisher is still wrong")

    print()
    print("=== KEY FIELDS ===")
    print(f"Title: {result.get('title')}")
    print(f"Authors: {result.get('authors')}")
    print(f"ISBN-13: {result.get('isbn_13')}")
    print(f"Publisher: {result.get('publisher')}")
    print(f"Price: {result.get('price')}")
else:
    print("FAILED to scrape book")
