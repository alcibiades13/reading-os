"""
ISBN lookup utility functions for Google Books and Open Library APIs
"""

import requests
from typing import Dict, Optional
from django.conf import settings


def lookup_isbn_google_books(isbn: str) -> Optional[Dict]:
    """
    Pretražuje knjigu preko Google Books API na osnovu ISBN-a

    Args:
        isbn: ISBN broj knjige

    Returns:
        Dictionary sa podacima knjige ili None ako nije pronađena
    """
    try:
        url = f"https://www.googleapis.com/books/v1/volumes"
        params = {"q": f"isbn:{isbn}", "maxResults": 1}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("totalItems", 0) == 0:
            return None

        volume_info = data["items"][0].get("volumeInfo", {})

        return {
            "title": volume_info.get("title"),
            "subtitle": volume_info.get("subtitle"),
            "authors": volume_info.get("authors", []),
            "publisher": volume_info.get("publisher"),
            "published_date": volume_info.get("publishedDate"),
            "description": volume_info.get("description"),
            "isbn_10": next(
                (
                    identifier.get("identifier")
                    for identifier in volume_info.get("industryIdentifiers", [])
                    if identifier.get("type") == "ISBN_10"
                ),
                None,
            ),
            "isbn_13": next(
                (
                    identifier.get("identifier")
                    for identifier in volume_info.get("industryIdentifiers", [])
                    if identifier.get("type") == "ISBN_13"
                ),
                None,
            ),
            "page_count": volume_info.get("pageCount"),
            "categories": volume_info.get("categories", []),
            "language": volume_info.get("language"),
            "preview_link": volume_info.get("previewLink"),
            "info_link": volume_info.get("infoLink"),
            "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail"),
            "small_thumbnail": volume_info.get("imageLinks", {}).get("smallThumbnail"),
        }
    except requests.RequestException as e:
        print(f"Error fetching from Google Books API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in Google Books lookup: {e}")
        return None


def lookup_isbn_open_library(isbn: str) -> Optional[Dict]:
    """
    Pretražuje knjigu preko Open Library API na osnovu ISBN-a

    Args:
        isbn: ISBN broj knjige

    Returns:
        Dictionary sa podacima knjige ili None ako nije pronađena
    """
    try:
        url = f"https://openlibrary.org/api/books"
        params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        isbn_key = f"ISBN:{isbn}"

        if isbn_key not in data:
            return None

        book_data = data[isbn_key]

        return {
            "title": book_data.get("title"),
            "authors": [author.get("name") for author in book_data.get("authors", [])],
            "publishers": [pub.get("name") for pub in book_data.get("publishers", [])],
            "publish_date": book_data.get("publish_date"),
            "number_of_pages": book_data.get("number_of_pages"),
            "subjects": [
                subject.get("name") for subject in book_data.get("subjects", [])
            ],
            "isbn_10": (
                book_data.get("identifiers", {}).get("isbn_10", [None])[0]
                if book_data.get("identifiers", {}).get("isbn_10")
                else None
            ),
            "isbn_13": (
                book_data.get("identifiers", {}).get("isbn_13", [None])[0]
                if book_data.get("identifiers", {}).get("isbn_13")
                else None
            ),
            "languages": [lang.get("key") for lang in book_data.get("languages", [])],
            "cover": book_data.get("cover", {}).get("large")
            or book_data.get("cover", {}).get("medium"),
            "open_library_url": book_data.get("url"),
        }
    except requests.RequestException as e:
        print(f"Error fetching from Open Library API: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in Open Library lookup: {e}")
        return None


def lookup_isbn(isbn: str, source: str = "google") -> Optional[Dict]:
    """
    Univerzalna funkcija za pretragu knjige preko ISBN-a

    Args:
        isbn: ISBN broj knjige
        source: 'google', 'openlibrary', ili 'both' - koji API da koristi

    Returns:
        Dictionary sa podacima knjige ili None ako nije pronađena
    """
    if source == "google":
        return lookup_isbn_google_books(isbn)
    elif source == "openlibrary":
        return lookup_isbn_open_library(isbn)
    elif source == "both":
        # Pokušaj prvo Google Books, pa Open Library kao fallback
        result = lookup_isbn_google_books(isbn)
        if result:
            return result
        return lookup_isbn_open_library(isbn)
    else:
        raise ValueError(
            f"Unknown source: {source}. Use 'google', 'openlibrary', or 'both'"
        )



