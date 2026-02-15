"""
Delfi.rs web scraper for book information
Uses Playwright for JavaScript-heavy pages
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re
from urllib.parse import urljoin
import time
from datetime import datetime


class DelfiScraper:
    """Scraper for Delfi.rs bookstore using Playwright"""

    BASE_URL = "https://delfi.rs"
    SEARCH_URL = f"{BASE_URL}/knjige"

    def __init__(self, rate_limit_delay: float = 1.5, headless: bool = True):
        """
        Initialize Delfi scraper

        Args:
            rate_limit_delay: Delay between requests in seconds (ethical scraping)
            headless: Run browser in headless mode
        """
        self.rate_limit_delay = rate_limit_delay
        self.headless = headless
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()

    def _extract_isbn(self, text: str) -> Dict[str, Optional[str]]:
        """
        Extract ISBN-10 and ISBN-13 from text

        Args:
            text: Text to search for ISBN

        Returns:
            Dictionary with isbn_10 and isbn_13 keys
        """
        isbn_13_pattern = r'(?:ISBN(?:-13)?:?\s*)?(?:978|979)[0-9\-\s]{10,17}'
        isbn_10_pattern = r'(?:ISBN(?:-10)?:?\s*)?[0-9\-\s]{10,13}(?!\d)'

        isbn_13 = None
        isbn_10 = None

        # Try to find ISBN-13
        isbn_13_match = re.search(isbn_13_pattern, text, re.IGNORECASE)
        if isbn_13_match:
            isbn_13 = re.sub(r'[^0-9]', '', isbn_13_match.group())
            if len(isbn_13) != 13:
                isbn_13 = None

        # Try to find ISBN-10
        isbn_10_match = re.search(isbn_10_pattern, text, re.IGNORECASE)
        if isbn_10_match:
            isbn_10 = re.sub(r'[^0-9]', '', isbn_10_match.group())
            if len(isbn_10) != 10 or isbn_10 == isbn_13:
                isbn_10 = None

        return {
            "isbn_13": isbn_13,
            "isbn_10": isbn_10
        }

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """Clean and normalize text"""
        if not text:
            return None
        return re.sub(r'\s+', ' ', text.strip())

    def _extract_number(self, text: str) -> Optional[int]:
        """Extract first number from text"""
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None

    def _parse_serbian_date(self, date_str: str) -> Optional[str]:
        """
        Parse Serbian date format to YYYY-MM-DD.
        Handles: "6. septembar 2024.", "5. 01 2018.", "5. 01. 2018.", "2018"

        Args:
            date_str: Date string in Serbian format

        Returns:
            Date in YYYY-MM-DD format or just year if can't parse
        """
        if not date_str:
            return None

        # Month name mapping (Serbian to number)
        months = {
            'januar': 1, 'januara': 1,
            'februar': 2, 'februara': 2,
            'mart': 3, 'marta': 3,
            'april': 4, 'aprila': 4,
            'maj': 5, 'maja': 5,
            'jun': 6, 'juna': 6,
            'jul': 7, 'jula': 7,
            'avgust': 8, 'avgusta': 8,
            'septembar': 9, 'septembra': 9,
            'oktobar': 10, 'oktobra': 10,
            'novembar': 11, 'novembra': 11,
            'decembar': 12, 'decembra': 12
        }

        # Try numeric format: "5. 01 2018." or "5. 01. 2018." or "05.01.2018"
        numeric_match = re.search(r'(\d{1,2})\.\s*(\d{1,2})\.?\s*(\d{4})', date_str)
        if numeric_match:
            day = int(numeric_match.group(1))
            month = int(numeric_match.group(2))
            year = int(numeric_match.group(3))
            if 1 <= month <= 12 and 1 <= day <= 31:
                try:
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except:
                    return f"{year:04d}-01-01"

        # Try Serbian month name format: "6. septembar 2024."
        match = re.search(r'(\d+)\.\s*(\w+)\s*(\d{4})', date_str)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))

            month = months.get(month_name)
            if month:
                try:
                    return f"{year:04d}-{month:02d}-{day:02d}"
                except:
                    return f"{year:04d}-01-01"

        # If just a year (4 digits), return as YYYY-01-01
        match = re.search(r'(\d{4})', date_str)
        if match:
            return f"{match.group(1)}-01-01"

        return None

    def _fetch_page_with_playwright(self, url: str, wait_for_selector: str = None) -> Optional[str]:
        """
        Fetch page content using Playwright (handles JavaScript)

        Args:
            url: URL to fetch
            wait_for_selector: Optional CSS selector to wait for

        Returns:
            HTML content as string or None if failed
        """
        try:
            self._rate_limit()

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="sr-RS"
                )
                page = context.new_page()

                # Navigate to page
                page.goto(url, wait_until='networkidle', timeout=30000)

                # Wait for specific selector if provided
                if wait_for_selector:
                    page.wait_for_selector(wait_for_selector, timeout=10000)
                else:
                    # Wait a bit for dynamic content to load
                    page.wait_for_timeout(2000)

                # Get initial HTML (with "Opis" tab content - description)
                html_with_description = page.content()

                # Try to click "Deklaracija" tab to load product details table
                html_with_details = None
                try:
                    # Try multiple selectors for the Deklaracija tab
                    tab_selectors = [
                        'text=/deklaracija/i',
                        'button:has-text("Deklaracija")',
                        'a:has-text("Deklaracija")',
                        '[role="tab"]:has-text("Deklaracija")',
                        'li:has-text("Deklaracija")',
                        '.tab:has-text("Deklaracija")',
                        '.nav-link:has-text("Deklaracija")',
                    ]
                    for selector in tab_selectors:
                        try:
                            tab = page.locator(selector).first
                            if tab.is_visible(timeout=1500):
                                tab.click()
                                page.wait_for_timeout(1500)
                                html_with_details = page.content()
                                break
                        except:
                            continue
                except:
                    pass  # Tab might not exist on all pages

                # Merge both HTMLs - combine description from first and details from second
                # We'll parse both and combine data in scrape_book_by_url
                html_content = {
                    'main': html_with_description,
                    'details': html_with_details
                }

                browser.close()
                return html_content

        except PlaywrightTimeout as e:
            print(f"Timeout fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching {url} with Playwright: {e}")
            return None

    def scrape_book_by_url(self, url: str) -> Optional[Dict]:
        """
        Scrape book information from a Delfi.rs book page

        Args:
            url: Full URL to the Delfi.rs book page

        Returns:
            Dictionary with book information or None if failed
        """
        # Fetch page with Playwright (returns dict with 'main' and 'details' HTML)
        html_data = self._fetch_page_with_playwright(url)
        if not html_data:
            return None

        # Parse main HTML (with description)
        soup = BeautifulSoup(html_data['main'], 'html.parser')

        # Also parse details HTML if available
        soup_details = None
        if html_data.get('details'):
            soup_details = BeautifulSoup(html_data['details'], 'html.parser')

        try:
            book_data = {
                "delfi_id": None,
                "delfi_link": url,
                "title": None,
                "subtitle": None,
                "authors": [],
                "description": None,
                "publisher": None,
                "published_date": None,
                "isbn_13": None,
                "isbn_10": None,
                "page_count": None,
                "language": "sr",  # Default to Serbian
                "cover_image_url": None,
                "categories": [],
                "format": None,
                "price": None,
                "currency": "RSD",
                "source": "delfi_scrape",
                "source_id": None,
                "raw_data": {}
            }

            # Extract ID from URL (e.g., 61030 from 61030-slepilo-knjiga-delfi-knjizare.html)
            url_match = re.search(r'/(\d+)-', url)
            if url_match:
                book_data["delfi_id"] = url_match.group(1)
                book_data["source_id"] = url_match.group(1)

            # Strategy 1: Look for structured data (JSON-LD)
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                import json
                try:
                    structured_data = json.loads(json_ld.string)
                    book_data["raw_data"]["json_ld"] = structured_data

                    if isinstance(structured_data, dict):
                        book_data["title"] = structured_data.get("name")
                        # Note: Don't use description from JSON-LD - it's truncated on Delfi.rs
                        # We'll extract full description from HTML later

                        if "author" in structured_data:
                            author = structured_data["author"]
                            if isinstance(author, str):
                                book_data["authors"] = [author]
                            elif isinstance(author, dict):
                                book_data["authors"] = [author.get("name")]
                            elif isinstance(author, list):
                                book_data["authors"] = [
                                    a.get("name") if isinstance(a, dict) else str(a)
                                    for a in author
                                ]

                        if "publisher" in structured_data:
                            publisher = structured_data["publisher"]
                            if isinstance(publisher, str):
                                book_data["publisher"] = publisher
                            elif isinstance(publisher, dict):
                                book_data["publisher"] = publisher.get("name")

                        if "isbn" in structured_data:
                            isbn_data = self._extract_isbn(str(structured_data["isbn"]))
                            book_data.update(isbn_data)

                        if "image" in structured_data:
                            img_url = structured_data["image"]
                            if isinstance(img_url, list) and img_url:
                                img_url = img_url[0]
                            book_data["cover_image_url"] = img_url

                        if "offers" in structured_data:
                            offers = structured_data["offers"]
                            if isinstance(offers, dict):
                                price = offers.get("price")
                                if price:
                                    book_data["price"] = str(price)
                except json.JSONDecodeError:
                    pass

            # Strategy 2: Meta tags
            og_title = soup.find('meta', property='og:title')
            if og_title and not book_data["title"]:
                book_data["title"] = self._clean_text(og_title.get('content'))

            # Note: Skip og:description - it's often truncated on Delfi.rs
            # We'll get full description from HTML div later

            og_image = soup.find('meta', property='og:image')
            if og_image and not book_data["cover_image_url"]:
                book_data["cover_image_url"] = og_image.get('content')

            # Strategy 3: Look for common HTML patterns
            # Title
            if not book_data["title"]:
                title_selectors = [
                    'h1.product-title',
                    'h1.book-title',
                    '.product-name h1',
                    '[itemprop="name"]',
                    'h1',
                    '.product-detail-title',
                    '.book-info h1'
                ]
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title_text = self._clean_text(title_elem.get_text())
                        if title_text and len(title_text) > 3:  # Reasonable title length
                            book_data["title"] = title_text
                            break

            # Author
            if not book_data["authors"]:
                author_selectors = [
                    '[itemprop="author"]',
                    '.product-author',
                    '.book-author',
                    'a[href*="autor"]',
                    '.author-name',
                    'span.author',
                ]
                for selector in author_selectors:
                    author_elems = soup.select(selector)
                    if author_elems:
                        authors = [
                            self._clean_text(elem.get_text())
                            for elem in author_elems
                            if elem.get_text().strip() and len(elem.get_text().strip()) > 2
                        ]
                        if authors:
                            book_data["authors"] = authors
                            break

            # Description
            if not book_data["description"]:
                desc_selectors = [
                    '[itemprop="description"]',
                    '.product-description',
                    '.book-description',
                    '#description',
                    '.description-content',
                    'div.description',
                ]
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        desc_text = self._clean_text(desc_elem.get_text())
                        if desc_text and len(desc_text) > 20:  # Reasonable description length
                            book_data["description"] = desc_text
                            break

            # Cover image
            if not book_data["cover_image_url"]:
                img_selectors = [
                    'img[itemprop="image"]',
                    '.product-image img',
                    '.book-cover img',
                    'img.main-image',
                    '.product-gallery img',
                    'img[alt*="naslovna"]',
                    'img[alt*="cover"]',
                ]
                for selector in img_selectors:
                    img_elem = soup.select_one(selector)
                    if img_elem:
                        img_url = img_elem.get('src') or img_elem.get('data-src') or img_elem.get('data-lazy')
                        if img_url:
                            # Make absolute URL
                            if not img_url.startswith('http'):
                                img_url = urljoin(self.BASE_URL, img_url)
                            book_data["cover_image_url"] = img_url
                            break

            # Product details - look in all text for key-value pairs
            page_text = soup.get_text()

            # Extract ISBN from page text if not found yet
            if not book_data["isbn_13"] or not book_data["isbn_10"]:
                isbn_data = self._extract_isbn(page_text)
                if isbn_data["isbn_13"]:
                    book_data["isbn_13"] = isbn_data["isbn_13"]
                if isbn_data["isbn_10"]:
                    book_data["isbn_10"] = isbn_data["isbn_10"]

            # Look for labeled information in tables/lists
            info_containers = soup.find_all(['table', 'dl', 'ul', 'div'])
            for container in info_containers:
                container_text = container.get_text()

                # Publisher
                if not book_data["publisher"]:
                    publisher_patterns = [
                        r'Izdavač:?\s*([^\n]+)',
                        r'Izdavac:?\s*([^\n]+)',
                        r'Publisher:?\s*([^\n]+)',
                    ]
                    for pattern in publisher_patterns:
                        match = re.search(pattern, container_text, re.IGNORECASE)
                        if match:
                            publisher = self._clean_text(match.group(1))
                            if publisher and len(publisher) > 2:
                                book_data["publisher"] = publisher
                                break

                # Pages
                if not book_data["page_count"]:
                    pages_patterns = [
                        r'Broj strana:?\s*(\d+)',
                        r'Strana:?\s*(\d+)',
                        r'Pages:?\s*(\d+)',
                    ]
                    for pattern in pages_patterns:
                        match = re.search(pattern, container_text, re.IGNORECASE)
                        if match:
                            book_data["page_count"] = int(match.group(1))
                            break

                # Year / Published Date
                if not book_data["published_date"]:
                    year_patterns = [
                        r'Godina izdanja:?\s*(\d{1,2}\.\s*\d{1,2}\.?\s*\d{4}\.?)',  # "5. 01 2018." or "5. 01. 2018."
                        r'Godina izdanja:?\s*(\d+\.\s*\w+\s*\d{4}\.?)',  # "6. septembar 2024."
                        r'Godina izdanja:?\s*(\d{4})',
                        r'Godina:?\s*(\d{4})',
                        r'Year:?\s*(\d{4})',
                    ]
                    for pattern in year_patterns:
                        match = re.search(pattern, container_text, re.IGNORECASE)
                        if match:
                            # Parse Serbian date format to YYYY-MM-DD
                            parsed_date = self._parse_serbian_date(match.group(1))
                            if parsed_date:
                                book_data["published_date"] = parsed_date
                                break

                # Format (dimension like "13x20 cm")
                if not book_data["format"]:
                    format_patterns = [
                        r'Format:?\s*(\d+x\d+\s*cm)',  # Specific pattern for dimensions
                        r'Povez:?\s*([^\n]{1,30})',
                        r'Binding:?\s*([^\n]{1,30})',
                    ]
                    for pattern in format_patterns:
                        match = re.search(pattern, container_text, re.IGNORECASE)
                        if match:
                            format_text = self._clean_text(match.group(1))
                            if format_text and len(format_text) < 50:
                                book_data["format"] = format_text
                                break

            # Also check details HTML (from Deklaracija tab) for product info
            if soup_details:
                details_containers = soup_details.find_all(['table', 'dl', 'ul', 'div'])
                for container in details_containers:
                    container_text = container.get_text()

                    # Publisher (if not found in main HTML)
                    if not book_data["publisher"]:
                        match = re.search(r'Izdavač:?\s*([^\n]+)', container_text, re.IGNORECASE)
                        if match:
                            publisher = self._clean_text(match.group(1))
                            if publisher and len(publisher) > 2 and len(publisher) < 100:
                                book_data["publisher"] = publisher

                    # Pages
                    if not book_data["page_count"]:
                        match = re.search(r'Broj strana:?\s*(\d+)', container_text, re.IGNORECASE)
                        if match:
                            book_data["page_count"] = int(match.group(1))

                    # Published Date
                    if not book_data["published_date"]:
                        match = re.search(r'Godina izdanja:?\s*(\d{1,2}\.\s*\d{1,2}\.?\s*\d{4}\.?)', container_text, re.IGNORECASE)
                        if not match:
                            match = re.search(r'Godina izdanja:?\s*(\d+\.\s*\w+\s*\d{4}\.?)', container_text, re.IGNORECASE)
                        if not match:
                            match = re.search(r'Godina izdanja:?\s*(\d{4})', container_text, re.IGNORECASE)
                        if match:
                            # Parse Serbian date format to YYYY-MM-DD
                            parsed_date = self._parse_serbian_date(match.group(1))
                            if parsed_date:
                                book_data["published_date"] = parsed_date

                    # Format
                    if not book_data["format"]:
                        match = re.search(r'Format:?\s*(\d+x\d+\s*cm)', container_text, re.IGNORECASE)
                        if match:
                            book_data["format"] = self._clean_text(match.group(1))

            # Full-text fallback: if page_count or published_date still missing,
            # try extracting from the entire page text (handles changed DOM structures)
            for fallback_soup in [soup_details, soup]:
                if fallback_soup and (not book_data["page_count"] or not book_data["published_date"]):
                    full_text = fallback_soup.get_text()
                    if not book_data["page_count"]:
                        match = re.search(r'Broj\s+strana:?\s*(\d+)', full_text, re.IGNORECASE)
                        if match:
                            book_data["page_count"] = int(match.group(1))
                    if not book_data["published_date"]:
                        match = re.search(r'Godina\s+izdanja:?\s*(\d{1,2}\.\s*\d{1,2}\.?\s*\d{4}\.?)', full_text, re.IGNORECASE)
                        if not match:
                            match = re.search(r'Godina\s+izdanja:?\s*(\d+\.\s*\w+\s*\d{4}\.?)', full_text, re.IGNORECASE)
                        if not match:
                            match = re.search(r'Godina\s+izdanja:?\s*(\d{4})', full_text, re.IGNORECASE)
                        if match:
                            parsed_date = self._parse_serbian_date(match.group(1))
                            if parsed_date:
                                book_data["published_date"] = parsed_date

            # Price
            if not book_data["price"]:
                price_selectors = [
                    '[itemprop="price"]',
                    '.product-price',
                    '.price',
                    'span.price-value',
                    '.current-price',
                    'div.price',
                ]
                for selector in price_selectors:
                    price_elem = soup.select_one(selector)
                    if price_elem:
                        price_text = price_elem.get_text()
                        # Extract number from price (e.g., "1.299,00 RSD" -> "1299.00")
                        price_clean = price_text.replace('.', '').replace(',', '.')
                        price_match = re.search(r'[\d.]+', price_clean)
                        if price_match:
                            book_data["price"] = price_match.group()
                            break

            # Categories - find genre links that appear BEFORE the h1 title
            # This prevents extracting category links from description text
            categories = []

            # Find the h1 title element
            h1_title = soup.find('h1')

            if h1_title:
                # Look for genre links in the container that holds the h1
                # They should be siblings or in parent container before h1
                parent_container = h1_title.find_parent()
                if parent_container:
                    # Find all genre links in the parent container
                    genre_links = parent_container.find_all('a', href=lambda h: h and '/Knjiga/zanr/' in h)

                    for link in genre_links:
                        # Check if this link appears BEFORE the h1 in DOM order
                        # We do this by checking if h1 is in the link's next siblings
                        is_before_h1 = False
                        current = link
                        while current:
                            current = current.find_next_sibling()
                            if current == h1_title:
                                is_before_h1 = True
                                break

                        # Also check if link is in a div that comes before h1
                        link_parent = link.find_parent('div')
                        if link_parent and h1_title in link_parent.find_all_next():
                            is_before_h1 = True

                        if is_before_h1:
                            cat_text = self._clean_text(link.get_text())
                            if cat_text and cat_text not in ['Početna', 'Knjige', 'Home', 'Naslovna', 'Knjiga']:
                                # Remove trailing comma if present
                                cat_text = cat_text.rstrip(',').strip()
                                # Split categories that have " i " in them
                                if ' i ' in cat_text:
                                    parts = [p.strip() for p in cat_text.split(' i ')]
                                    categories.extend(parts)
                                else:
                                    categories.append(cat_text)

            # If we didn't find categories above title, try breadcrumbs as fallback
            if not categories:
                category_selectors = [
                    '.breadcrumb a',
                    'nav.breadcrumb a',
                ]
                for selector in category_selectors:
                    cat_elems = soup.select(selector)
                    if cat_elems:
                        for elem in cat_elems:
                            cat_text = self._clean_text(elem.get_text())
                            if cat_text and cat_text not in ['Početna', 'Knjige', 'Home', 'Naslovna', 'Knjiga']:
                                cat_text = cat_text.rstrip(',').strip()
                                if ' i ' in cat_text:
                                    parts = [p.strip() for p in cat_text.split(' i ')]
                                    categories.extend(parts)
                                else:
                                    categories.append(cat_text)
                        if categories:
                            break

            # Remove duplicates while preserving order
            if categories:
                seen = set()
                unique_categories = []
                for cat in categories:
                    if cat not in seen:
                        seen.add(cat)
                        unique_categories.append(cat)
                book_data["categories"] = unique_categories[:10]  # Limit to 10

            # Clean up None values and empty lists
            book_data = {
                k: (v if v not in [None, [], ''] else None)
                for k, v in book_data.items()
            }

            # Ensure we have at least title to consider it successful
            if book_data["title"]:
                return book_data
            else:
                print(f"Could not extract title from {url}")
                return None

        except Exception as e:
            print(f"Error scraping book from {url}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def search_books(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search for books on Delfi.rs

        Note: Implementation depends on actual Delfi.rs search page structure

        Args:
            query: Search query (title, author, ISBN)
            limit: Maximum number of results

        Returns:
            List of book dictionaries
        """
        # TODO: Implement based on actual search page structure
        # This would require analyzing the search results page
        print("Search functionality not yet implemented - requires search page analysis")
        return []

    def scrape_book_by_isbn(self, isbn: str) -> Optional[Dict]:
        """
        Search and scrape book by ISBN

        Args:
            isbn: ISBN-10 or ISBN-13

        Returns:
            Book dictionary or None
        """
        results = self.search_books(isbn, limit=1)
        if results:
            return results[0]
        return None


# Convenience functions
def scrape_delfi_book(url: str) -> Optional[Dict]:
    """
    Scrape a single book from Delfi.rs

    Args:
        url: Full URL to book page

    Returns:
        Book data dictionary
    """
    scraper = DelfiScraper()
    return scraper.scrape_book_by_url(url)


def search_delfi(query: str, limit: int = 20) -> List[Dict]:
    """
    Search Delfi.rs for books

    Args:
        query: Search query
        limit: Max results

    Returns:
        List of book dictionaries
    """
    scraper = DelfiScraper()
    return scraper.search_books(query, limit)
