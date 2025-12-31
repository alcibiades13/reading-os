#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from bs4 import BeautifulSoup

with open('delfi_page.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

json_ld = soup.find('script', type='application/ld+json')

if json_ld:
    data = json.loads(json_ld.string)

    # Write to file to avoid encoding issues
    with open('json_ld_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("JSON-LD data saved to json_ld_data.json")

    # Check for publisher
    if 'publisher' in data:
        print(f"\nPublisher in JSON-LD: {data['publisher']}")
    else:
        print("\nNo 'publisher' field in JSON-LD")
        print(f"\nAvailable fields: {list(data.keys())}")
else:
    print("No JSON-LD found")
