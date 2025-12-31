# Delfi.rs Integration - Dokumentacija

## 📚 Pregled

Reading OS aplikacija sada podržava importovanje knjiga sa [Delfi.rs](https://delfi.rs) - najveće srpske knjižare. Pošto je Delfi.rs JavaScript SPA aplikacija, implementiran je scraper koji koristi Playwright headless browser za renderovanje stranica i izvlačenje informacija o knjigama.

## ✨ Šta je implementirano

### Backend

#### 1. **Delfi Scraper** (`backend/utils/delfi_scraper.py`)

Glavni scraper modul koji koristi Playwright za scraping:

**Ključne funkcije:**
- `scrape_book_by_url(url)` - Scrape-uje knjigu sa Delfi.rs URL-a
- `search_books(query, limit)` - Placeholder za pretragu (TODO)
- `scrape_book_by_isbn(isbn)` - Pretraga po ISBN-u (TODO)

**Šta scraper izvlači:**
- ✅ Naslov
- ✅ Autor(i)
- ✅ ISBN-13 i ISBN-10
- ✅ Opis knjige
- ✅ Cover slika (URL)
- ✅ Cena (RSD)
- ✅ Kategorije
- ✅ Jezik (default: 'sr')
- ⚠️ Izdavač (delimično - zavisi od strukture stranice)
- ⚠️ Broj strana (delimično - zavisi od strukture stranice)
- ✅ Format (tvrdi povez, meki povez, itd.)
- ✅ Godina izdavanja

**Etička razmatranja:**
- Rate limiting: 1.5 sekundi između zahteva
- Poštuje robots.txt
- Koristi realan User-Agent string
- Sav kod je transparentan i u skladu sa etičkim scraping pravilima

#### 2. **API Endpoint** (`backend/apps/books/views.py`)

Novi endpoint dodat u `BookViewSet`:

```python
POST /api/books/scrape_delfi/
{
  "url": "https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html"
}
```

**Response:**
```json
{
  "title": "Slepilo",
  "authors": ["Žoze Saramago"],
  "isbn_13": "9788652115723",
  "cover_image_url": "https://delfi.rs/_img/artikli/2014/07/slepilo_vv.jpg",
  "price": "899",
  "currency": "RSD",
  "source": "delfi_scrape",
  "delfi_id": "61030",
  ...
}
```

#### 3. **Instalacija zavisnosti**

Dodato u `requirements.txt`:
```
playwright==1.40.0  # Za JavaScript-heavy sajtove (Delfi.rs)
```

**Setup:**
```bash
cd backend
./venv/Scripts/pip install playwright==1.40.0
./venv/Scripts/playwright install chromium
```

### Frontend

#### 1. **Delfi API Service** (`frontend/src/services/delfiAPI.js`)

Frontend servis za komunikaciju sa backend Delfi scraper-om:

**Funkcije:**
- `scrapeBookByUrl(url)` - Scrape-uje knjigu sa URL-a
- `searchBooks(query, limit)` - Placeholder (TODO)
- `searchByISBN(isbn)` - Placeholder (TODO)
- `isValidDelfiUrl(url)` - Validacija Delfi.rs URL-a
- `extractDelfiBookId(url)` - Izvlači ID knjige iz URL-a
- `formatBookData(delfiData)` - Formatira podatke u standardni format

#### 2. **Book Import Store** (`frontend/src/stores/bookImportStore.js`)

Dodato:
- `delfiUrl` state - Čuva trenutni Delfi URL
- `scrapeDelfiBook(url)` action - Scrape-uje knjigu sa Delfi URL-a
- `importSource` proširen sa `'delfi_rs'` opcijom
- `delfi_id` dodat u `prepareBookPayload()`

#### 3. **Import Books View UI** (`frontend/src/views/import/ImportBooksView.vue`)

Dodato:
- **Delfi.rs source dugme** - U source selector sekciji
- **Delfi.rs URL tab** - Novi tab za unos URL-a
- **URL input polje** - Za paste Delfi.rs URL-a
- **"Scrape" dugme** - Za pokretanje scraping-a
- Enter key support za brži unos

## 🚀 Kako koristiti

### Korisničko iskustvo

1. **Otvori Import stranicu** (`/import`)
2. **Klikni na "Delfi.rs 🇷🇸" source dugme** (gore desno)
3. **Klikni na "Delfi.rs URL" tab**
4. **Paste URL knjige sa Delfi.rs**
   - Primer: `https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html`
5. **Klikni "Scrape"** ili pritisni **Enter**
6. **Sačekaj da se knjiga učita** (~3-5 sekundi)
7. **Klikni na knjigu** da vidiš preview
8. **Importuj u biblioteku!**

### URL Format

Delfi.rs knjige imaju sledeći format URL-a:
```
https://delfi.rs/knjige/{ID}-{slug}.html
```

Primeri:
- `https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html`
- `https://delfi.rs/knjige/12345-atomske-navike-james-clear.html`

## 📊 Model podataka

### Book Model (`backend/apps/books/models.py`)

Source opcije već podržavaju Delfi:
```python
SOURCE_CHOICES = [
    ('manual', 'Manual Entry'),
    ('google_books', 'Google Books API'),
    ('open_library', 'Open Library API'),
    ('delfi_scrape', 'Delfi Scrape'),      # ✅ Implementirano
    ('vulkan_scrape', 'Vulkan Scrape'),     # TODO
    ('laguna_scrape', 'Laguna Scrape'),     # TODO (već u Delfiju)
]
```

`external_ids` JSONField čuva:
```json
{
  "delfi_id": "61030",
  "google_books_id": null,
  "open_library_id": null
}
```

## 🔧 Tehnički detalji

### Playwright Setup

Delfi.rs koristi React/SPA koji zahteva JavaScript execution. Zato je neophodan headless browser.

**Kako radi:**
1. Playwright pokreće Chromium browser
2. Navigira na Delfi.rs stranicu
3. Čeka da se JavaScript renderuje (`wait_until='networkidle'`)
4. Izvlači HTML sadržaj nakon renderovanja
5. BeautifulSoup parsira HTML i izvlači podatke

### Scraping Strategije

Scraper koristi **multi-layer** pristup za maksimalnu pouzdanost:

1. **JSON-LD Structured Data** - Najpouzdaniji izvor
2. **Open Graph Meta Tags** - Backup za osnovne info
3. **HTML Selectors** - Fallback za pojedinačna polja
4. **Regex Pattern Matching** - Za izvlačenje ISBN, godina, itd.

### Performance

- **Prvi request:** ~3-5 sekundi (Playwright cold start + JS rendering)
- **Sledeći requestovi:** ~2-3 sekunde
- **Rate limiting:** 1.5s između requestova (etički scraping)

## ⚠️ Ograničenja

### Trenutno implementirano
- ✅ Scraping pojedinačne knjige sa URL-a
- ✅ Automatsko izvlačenje glavnih polja
- ✅ Validacija URL-a

### TODO - Buduća implementacija
- ❌ **Search funkcionalnost** - Delfi.rs search zahteva analizu search stranice
- ❌ **ISBN pretraga** - Zahteva implementaciju Delfi search-a
- ❌ **Bulk import** - Za importovanje više knjiga odjednom
- ❌ **Caching** - Za smanjenje load-a na Delfi.rs servere
- ❌ **Poboljšanje izvlačenja izdavača i broja strana**

## 🐛 Troubleshooting

### "Failed to scrape book data"
- Proverite da li je URL validan Delfi.rs link
- Proverite internet konekciju
- Pokušajte ponovo (može biti timeout)

### "Playwright not found"
Pokrenite:
```bash
cd backend
./venv/Scripts/playwright install chromium
```

### "Some fields are missing"
- Delfi.rs struktura se može menjati
- Scraper koristi fallback strategije
- Manjak nekih polja (publisher, pages) je trenutno moguć

### Charset/Encoding problemi
- Ćirilična slova mogu biti loše prikazana u terminalu
- U bazi se **pravilno** čuvaju kao UTF-8
- UI prikazuje ispravno

## 📝 Napomene za održavanje

### Ako Delfi.rs promeni strukturu stranice:

1. Otvori `backend/utils/delfi_scraper.py`
2. Ažuriraj selektore u `scrape_book_by_url()` metodi
3. Dodaj nove selektore u fallback strategije
4. Testiraj sa pravim URL-ovima

### Dodavanje novih srpskih knjižara:

Iskoristite `delfi_scraper.py` kao template za:
- **Vulkan.rs** - Srposka knjižara
- **Dereta.rs** - Srpski izdavač

## 🎉 Zaključak

Delfi.rs integracija omogućava korisnicima iz Srbije da lako importuju knjige sa najvećeg domaćeg sajta za knjige. Sistem je robustan, etičan i lako proširiv za buduće knjižare.

**Testiran primer:**
- URL: `https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html`
- Knjiga: "Slepilo" - Žoze Saramago
- Status: ✅ Uspešno izvučeno 10+ polja
