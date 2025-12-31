# 🔧 PostgreSQL Database Setup

## Problem: Connection Refused

```
django.db.utils.OperationalError: connection to server at "127.0.0.1", port 5432 failed: Connection refused
```

Ovo znači da PostgreSQL server nije pokrenut.

## ✅ Rešenje

### Opcija 1: Pokreni PostgreSQL Service (Windows)

1. **Otvori Services:**
   - Pritisni `Win + R`
   - Otkucaj: `services.msc`
   - Pritisni Enter

2. **Pronađi PostgreSQL servis:**
   - Traži "postgresql-x64-XX" (gde je XX verzija, npr. 14, 15, 16)

3. **Pokreni servis:**
   - Desni klik → Start
   - Ili dvostruki klik → Start

### Opcija 2: Command Line (Brže)

```bash
# Proveri status
pg_ctl status -D "C:\Program Files\PostgreSQL\XX\data"

# Pokreni server
pg_ctl start -D "C:\Program Files\PostgreSQL\XX\data"
```

### Opcija 3: Koristi pgAdmin

1. Otvori pgAdmin
2. Konekcija na server će automatski pokrenuti PostgreSQL

---

## 🚀 Quick Start - Kompletno Pokretanje Aplikacije

### 1. Pokreni PostgreSQL

```bash
# Windows Service
net start postgresql-x64-15  # Promeni broj verzije ako treba
```

### 2. Pokreni Backend

```bash
cd D:\projects\reading-os\backend
.\venv\Scripts\activate
python manage.py runserver
```

### 3. Pokreni Frontend (drugi terminal)

```bash
cd D:\projects\reading-os\frontend
npm run dev
```

### 4. Otvori aplikaciju

```
http://localhost:5173
```

---

## 🔍 Provera da li PostgreSQL radi

```bash
# Način 1: psql komanda
psql -U postgres -c "SELECT version();"

# Način 2: Proveri port
netstat -an | findstr "5432"

# Način 3: Test konekcija
psql -U postgres -h localhost -p 5432
```

---

## ⚙️ Backend Database Settings

Proveri `backend/.env` ili `backend/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'reading_os_db',      # Ime baze
        'USER': 'postgres',             # PostgreSQL user
        'PASSWORD': 'tvoja_lozinka',    # Tvoja lozinka
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

---

## 🆘 Ako i dalje ne radi

### Instalacija PostgreSQL

Ako nemaš PostgreSQL instaliran:

1. Download: https://www.postgresql.org/download/windows/
2. Instaliraj (default port 5432)
3. Zapamti lozinku za `postgres` usera!

### Kreiranje Baze

```bash
# Konektuj se na PostgreSQL
psql -U postgres

# Kreiraj bazu
CREATE DATABASE reading_os_db;

# Kreiraj usera (opciono)
CREATE USER reading_user WITH PASSWORD 'reading_pass';
GRANT ALL PRIVILEGES ON DATABASE reading_os_db TO reading_user;

# Izađi
\q
```

### Django Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Za admin pristup
```

---

## 📝 Auto-start PostgreSQL (Opciono)

Da PostgreSQL automatski startuje sa Windows-om:

1. Otvori Services (`services.msc`)
2. Desni klik na PostgreSQL servis
3. Properties
4. Startup type: **Automatic**
5. OK

---

## 🎉 Test da li sve radi

```bash
cd D:\projects\reading-os\backend
python manage.py check
python manage.py showmigrations
```

Ako nema grešaka - sve radi! 🚀
