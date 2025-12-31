#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Use a recent book URL - try to find from screenshot bar-kod
# Let's use a newer book that should have all fields
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

# Look for all text containing these keywords
keywords = ['Broj strana', 'Godina izdanja', 'Povez', 'Pismo', 'Format', 'Težina']

print("Searching for product details...")
for keyword in keywords:
    # Find all elements containing this keyword
    elements = soup.find_all(string=lambda text: text and keyword in text)
    if elements:
        print(f"\nFound '{keyword}':")
        for elem in elements[:2]:
            parent = elem.parent
            # Try to get the next sibling or value
            print(f"  Element: {elem.strip()}")
            print(f"  Parent tag: {parent.name}")
            print(f"  Parent class: {parent.get('class')}")

            # Try to find associated value
            next_elem = parent.find_next_sibling()
            if next_elem:
                print(f"  Next sibling: {next_elem.get_text(strip=True)[:50]}")
