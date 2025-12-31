#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from playwright.sync_api import sync_playwright

url = "https://delfi.rs/knjige/217445-talasi-knjiga-delfi-knjizare.html"
print(f"Fetching: {url}\n")
print("Monitoring all API/XHR requests...\n")

api_calls = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Show browser
    page = browser.new_page()

    # Intercept all requests
    def handle_request(request):
        if 'api' in request.url or 'json' in request.url or 'xhr' in request.url.lower():
            api_calls.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type
            })
            print(f"API Call: {request.method} {request.url}")

    page.on('request', handle_request)

    page.goto(url, wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(5000)  # Wait longer to see all requests

    # Try clicking tabs if they exist
    print("\nLooking for tabs...")
    tabs = page.query_selector_all('button, a[role="tab"], .tab')
    if tabs:
        print(f"Found {len(tabs)} potential tabs, clicking them...")
        for i, tab in enumerate(tabs[:5]):
            try:
                tab.click()
                page.wait_for_timeout(1000)
            except:
                pass

    browser.close()

print(f"\n\nTotal API calls captured: {len(api_calls)}")
for call in api_calls:
    print(f"  {call['method']} {call['url']}")
