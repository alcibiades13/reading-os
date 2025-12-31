# Delfi.rs Integration - Quick Setup Guide

## 🚀 Brzo Pokretanje

### Backend Setup

1. **Instaliraj Playwright:**
```bash
cd backend
./venv/Scripts/pip install -r requirements.txt
./venv/Scripts/playwright install chromium
```

2. **Testiraj scraper:**
```bash
./venv/Scripts/python -c "
from utils.delfi_scraper import scrape_delfi_book
result = scrape_delfi_book('https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html')
print('✅ Success!' if result else '❌ Failed')
print(f\"Naslov: {result.get('title') if result else 'N/A'}\")
print(f\"Autor: {result.get('authors') if result else 'N/A'}\")
"
```

3. **Pokreni backend server:**
```bash
python manage.py runserver
```

### Frontend Setup

Nema dodatnih koraka - sve je već integrisano!

```bash
cd frontend
npm run dev
```

## 📖 Kako koristiti

1. Otvori `http://localhost:5173/import`
2. Klikni **"Delfi.rs 🇷🇸"** dugme (gore desno)
3. Klikni tab **"Delfi.rs URL"**
4. Paste URL knjige, npr:
   ```
   https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html
   ```
5. Klikni **"Scrape"** ili pritisni **Enter**
6. Importuj knjigu u biblioteku!

## 🔗 Gde naći Delfi.rs URL-ove?

1. Idi na https://delfi.rs
2. Pronađi knjigu koja te interesuje
3. Otvori stranicu knjige
4. Kopiraj URL iz address bara
5. Paste u Reading OS!

## ⚡ Test URL-ovi

Evo nekoliko URL-ova za testiranje:

```
https://delfi.rs/knjige/61030-slepilo-knjiga-delfi-knjizare.html
https://delfi.rs/knjige/83726-atomske-navike-james-clear-knjiga-delfi-knjizare.html
https://delfi.rs/knjige/77777-1984-dzordz-orvel-knjiga-delfi-knjizare.html
```

## 📊 Šta scraper izvlači?

✅ Naslov
✅ Autor(i)
✅ ISBN-13
✅ Opis
✅ Cover slika
✅ Cena (RSD)
✅ Kategorije
⚠️ Izdavač (ne uvek)
⚠️ Broj strana (ne uvek)

## 🐛 Problemi?

### Playwright Error
```bash
./venv/Scripts/playwright install chromium
```

### Import Error
Proveri da li je backend pokrenut na `http://localhost:8000`

### Timeout
- Sačekaj 5-10 sekundi
- Pokušaj ponovo
- Proveri internet konekciju

## 📚 Dokumentacija

Za detaljnu dokumentaciju, vidi [DELFI_INTEGRATION.md](./DELFI_INTEGRATION.md)
