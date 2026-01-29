# 🔧 PostgreSQL Database Setup (Linux)

## Reading OS Database Configuration

**Reading OS** uses **PostgreSQL 17** on **port 5433** to avoid conflicts with your main application.

- **Main Application:** PostgreSQL 16 on port 5432
- **Reading OS:** PostgreSQL 17 on port 5433

---

## ✅ Quick Start

### 1. Check PostgreSQL Clusters

```bash
pg_lsclusters
```

You should see:
```
Ver Cluster   Port Status
16  main      5432 online   # Main application
17  readingos 5433 online   # Reading OS
```

### 2. Start PostgreSQL 17 (if not running)

```bash
sudo pg_ctlcluster 17 readingos start
```

### 3. Verify Connection

```bash
# Connect to Reading OS database
psql -U postgres -h 127.0.0.1 -p 5433 -d reading_os_db
```

---

## 🔍 Common PostgreSQL Commands (Linux)

### Check Status
```bash
# List all clusters
pg_lsclusters

# Check if port 5433 is listening
sudo netstat -tlnp | grep 5433

# Or using ss
ss -tlnp | grep 5433
```

### Start/Stop Clusters
```bash
# Start reading-os cluster
sudo pg_ctlcluster 17 readingos start

# Stop reading-os cluster
sudo pg_ctlcluster 17 readingos stop

# Restart reading-os cluster
sudo pg_ctlcluster 17 readingos restart

# Check status
sudo pg_ctlcluster 17 readingos status
```

### Connect to Database
```bash
# Connect as postgres user
sudo -u postgres psql -p 5433

# Connect to specific database
sudo -u postgres psql -p 5433 -d reading_os_db

# Connect with password authentication
psql -U postgres -h 127.0.0.1 -p 5433 -d reading_os_db
```

---

## 🚀 Full Application Startup

### 1. Start PostgreSQL 17
```bash
sudo pg_ctlcluster 17 readingos start
```

### 2. Start Backend (new terminal)
```bash
cd ~/Projects/reading-os/backend
source venv/bin/activate
python manage.py runserver 8001
```

### 3. Start Frontend (new terminal)
```bash
cd ~/Projects/reading-os/frontend
npm run dev
```

### 4. Open Application
```
http://localhost:5175
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
