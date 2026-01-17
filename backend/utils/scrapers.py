"""
Web scraping utility functions for extracting book information
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
import re
from urllib.parse import urljoin, urlparse


def scrape_goodreads_book(url: str) -> Optional[Dict]:
    """
    Skrejpuje podatke o knjizi sa Goodreads stranice

    Args:
        url: URL Goodreads stranice knjige

    Returns:
        Dictionary sa podacima knjige ili None ako nije uspešno
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Izvlačenje osnovnih informacija
        title_elem = soup.find("h1", {"id": "bookTitle"})
        title = title_elem.get_text(strip=True) if title_elem else None

        author_elem = soup.find("a", {"class": "authorName"})
        author = author_elem.get_text(strip=True) if author_elem else None

        description_elem = soup.find("div", {"id": "description"})
        description = None
        if description_elem:
            spans = description_elem.find_all("span")
            if spans:
                description = spans[-1].get_text(strip=True)

        rating_elem = soup.find("span", {"itemprop": "ratingValue"})
        rating = rating_elem.get_text(strip=True) if rating_elem else None

        ratings_count_elem = soup.find("meta", {"itemprop": "ratingCount"})
        ratings_count = (
            ratings_count_elem.get("content") if ratings_count_elem else None
        )

        isbn_elem = soup.find("span", string=re.compile("ISBN"))
        isbn = None
        if isbn_elem:
            isbn_text = isbn_elem.find_next_sibling("span")
            if isbn_text:
                isbn = isbn_text.get_text(strip=True).replace(" ", "").replace("-", "")

        cover_elem = soup.find("img", {"id": "coverImage"})
        cover_url = cover_elem.get("src") if cover_elem else None

        return {
            "title": title,
            "author": author,
            "description": description,
            "rating": float(rating) if rating else None,
            "ratings_count": int(ratings_count) if ratings_count else None,
            "isbn": isbn,
            "cover_url": cover_url,
            "source_url": url,
        }
    except requests.RequestException as e:
        print(f"Error fetching Goodreads page: {e}")
        return None
    except Exception as e:
        print(f"Error scraping Goodreads: {e}")
        return None


def scrape_book_info_generic(url: str) -> Optional[Dict]:
    """
    Generička funkcija za skrejpovanje osnovnih podataka o knjizi

    Args:
        url: URL stranice sa informacijama o knjizi

    Returns:
        Dictionary sa osnovnim podacima ili None
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Pokušaj da pronađeš meta tagove (najpouzdanije)
        title = None
        title_tag = soup.find("meta", property="og:title") or soup.find("title")
        if title_tag:
            title = title_tag.get("content") or title_tag.get_text(strip=True)

        description = None
        desc_tag = soup.find("meta", property="og:description") or soup.find(
            "meta", {"name": "description"}
        )
        if desc_tag:
            description = desc_tag.get("content")

        image = None
        image_tag = soup.find("meta", property="og:image")
        if image_tag:
            image = image_tag.get("content")

        # Pokušaj da pronađeš ISBN u tekstu
        isbn_pattern = re.compile(r"ISBN[:\-\s]*(978|979)?[0-9\-]{10,13}")
        page_text = soup.get_text()
        isbn_match = isbn_pattern.search(page_text)
        isbn = None
        if isbn_match:
            isbn = re.sub(r"[^0-9]", "", isbn_match.group())

        return {
            "title": title,
            "description": description,
            "image_url": image,
            "isbn": isbn,
            "source_url": url,
        }
    except requests.RequestException as e:
        print(f"Error fetching page: {e}")
        return None
    except Exception as e:
        print(f"Error scraping page: {e}")
        return None


def clean_isbn(isbn: str) -> Optional[str]:
    """
    Čisti i validira ISBN broj

    Args:
        isbn: ISBN broj koji treba očistiti

    Returns:
        Očišćen ISBN broj ili None ako nije validan
    """
    if not isbn:
        return None

    # Ukloni sve karaktere osim brojeva
    cleaned = re.sub(r"[^0-9]", "", str(isbn))

    # Validacija dužine (ISBN-10 ima 10 cifara, ISBN-13 ima 13)
    if len(cleaned) == 10 or len(cleaned) == 13:
        return cleaned

    return None



