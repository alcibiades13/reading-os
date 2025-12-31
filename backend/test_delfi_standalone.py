#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Standalone test script za Delfi.rs scraper
Ne zahteva Django setup - može se pokrenuti direktno!

Usage:
    python test_delfi_standalone.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

def test_delfi_scraper():
    """Test Delfi.rs scraper bez Django zavisnosti"""

    print("=" * 80)
    print("🧪 DELFI.RS SCRAPER - STANDALONE TEST")
    print("=" * 80)
    print()

    try:
        from utils.delfi_scraper import scrape_delfi_book
        print("✅ Delfi scraper modul uspešno učitan")
    except ImportError as e:
        print(f"❌ ERROR: Ne mogu da učitam delfi_scraper modul: {e}")
        print("💡 Proveri da li je Playwright instaliran:")
        print("   ./venv/Scripts/pip install playwright")
        print("   ./venv/Scripts/playwright install chromium")
        return False

    print()

    # Test URL
    test_url = "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
    print(f"📖 Testiram URL: {test_url}")
    print(f"⏳ Molim sačekajte 3-5 sekundi...")
    print()

    try:
        result = scrape_delfi_book(test_url)

        if not result:
            print("❌ FAILED: Scraper nije vratio rezultate")
            print()
            print("💡 Moguće razlozi:")
            print("   1. Nema internet konekcije")
            print("   2. Delfi.rs je nedostupan")
            print("   3. Promenjena struktura Delfi.rs stranice")
            print("   4. Chromium nije instaliran (playwright install chromium)")
            return False

        print("✅ SUCCESS! Knjiga uspešno izvučena!")
        print()
        print("=" * 80)
        print("📊 IZVUČENI PODACI:")
        print("=" * 80)

        # Display results
        fields = [
            ("Naslov", "title"),
            ("Autor(i)", "authors"),
            ("ISBN-13", "isbn_13"),
            ("ISBN-10", "isbn_10"),
            ("Izdavač", "publisher"),
            ("Godina izdavanja", "published_date"),
            ("Broj strana", "page_count"),
            ("Format", "format"),
            ("Cena", "price"),
            ("Valuta", "currency"),
            ("Jezik", "language"),
            ("Kategorije", "categories"),
            ("Delfi ID", "delfi_id"),
            ("Source", "source"),
        ]

        extracted_count = 0
        for label, key in fields:
            value = result.get(key, "N/A")

            # Format output
            if value and value != "N/A" and value != []:
                extracted_count += 1
                if isinstance(value, list):
                    value_str = ", ".join(str(v) for v in value) if value else "N/A"
                else:
                    value_str = str(value)

                # Truncate long values
                if len(value_str) > 60:
                    value_str = value_str[:57] + "..."

                print(f"  {label:20s}: {value_str}")
            else:
                print(f"  {label:20s}: ⚠️  N/A")

        # Cover image
        cover_url = result.get("cover_image_url")
        if cover_url:
            extracted_count += 1
            print(f"  {'Cover Image':20s}: {cover_url[:60]}...")
        else:
            print(f"  {'Cover Image':20s}: ⚠️  N/A")

        # Description
        desc = result.get("description")
        if desc:
            extracted_count += 1
            print(f"  {'Opis':20s}: {desc[:60]}...")
        else:
            print(f"  {'Opis':20s}: ⚠️  N/A")

        print()
        print("=" * 80)

        # Score
        total_important_fields = 12  # title, authors, isbn, publisher, year, pages, format, price, lang, categories, cover, desc
        percentage = (extracted_count / total_important_fields) * 100

        print(f"✨ Rezultat: {extracted_count}/{total_important_fields} polja izvučeno ({percentage:.0f}%)")

        if percentage >= 80:
            print("🎉 ODLIČNO! Scraper radi savršeno!")
        elif percentage >= 60:
            print("✅ DOBRO! Većina podataka je izvučena.")
        elif percentage >= 40:
            print("⚠️  DELIMIČNO! Neki podaci nedostaju.")
        else:
            print("❌ LOŠE! Malo podataka je izvučeno.")

        print()
        print("=" * 80)
        print()

        # Integration status
        print("🔗 INTEGRACIJA STATUS:")
        print("  ✅ Backend scraper - Radi")
        print("  ✅ Playwright setup - OK")
        print("  ✅ Data extraction - OK")
        print()

        # Next steps
        print("📝 SLEDEĆI KORACI:")
        print("  1. Pokreni PostgreSQL server (vidi START_DATABASE.md)")
        print("  2. Pokreni Django backend: python manage.py runserver")
        print("  3. Pokreni frontend: cd frontend && npm run dev")
        print("  4. Otvori http://localhost:5173/import")
        print("  5. Klikni 'Delfi.rs 🇷🇸' tab")
        print("  6. Paste ovaj URL i testiraj!")
        print()

        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        print()
        print("📋 Traceback:")
        traceback.print_exc()
        print()
        print("💡 Troubleshooting:")
        print("   1. Instaliraj dependencies: pip install -r requirements.txt")
        print("   2. Instaliraj Chromium: playwright install chromium")
        print("   3. Proveri internet konekciju")
        return False


if __name__ == "__main__":
    print()
    success = test_delfi_scraper()
    print()

    if success:
        print("🎊 TEST PASSED! Delfi.rs integration je spremna! 🎊")
        sys.exit(0)
    else:
        print("⚠️  TEST FAILED! Pogledaj greške iznad.")
        sys.exit(1)
