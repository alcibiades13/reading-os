# Reading OS - Deployment Guide (Render.com)

Ovaj vodič objašnjava kako da deploy-uješ Reading OS aplikaciju na Render.com **besplatno**.

## Pre nego što počneš

### 1. Pripremi GitHub Repository

```bash
# Kreiraj .gitignore ako već ne postoji
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
dist/
build/

# Django
*.log
db.sqlite3
db.sqlite3-journal
/staticfiles/
/media/

# Environment variables
.env
.env.local

# Node
node_modules/
/frontend/dist/
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
EOL

# Initialize git (ako već nije)
git init
git add .
git commit -m "Prepare for deployment"

# Dodaj remote i push
git remote add origin https://github.com/YOUR-USERNAME/reading-os.git
git branch -M main
git push -u origin main
```

### 2. Kreiraj Render Account

1. Idi na [render.com](https://render.com)
2. Registruj se (možeš sa GitHub accountom)
3. Potvrdi email

## Deployment Steps

### Step 1: Deploy PostgreSQL Database

1. U Render Dashboard, klikni **"New +"** → **"PostgreSQL"**
2. Podesi:
   - **Name**: `reading-os-db`
   - **Database**: `reading_os`
   - **User**: `reading_os_user`
   - **Region**: `Frankfurt` (najbliže Srbiji)
   - **Plan**: **Free**
3. Klikni **"Create Database"**
4. Sačekaj da se database kreira (~2-3 minuta)
5. **VAŽNO**: Kopiraj **Internal Database URL** (trebаće ti za backend)

### Step 2: Deploy Django Backend

1. Klikni **"New +"** → **"Web Service"**
2. Konektuj GitHub repository: **"Connect Repository"**
3. Podesi:
   - **Name**: `reading-os-api`
   - **Region**: `Frankfurt`
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `gunicorn config.wsgi:application`
   - **Plan**: **Free**

4. **Environment Variables** - klikni "Advanced" i dodaj:

```
SECRET_KEY=<generate-random-string-here>
DEBUG=False
ALLOWED_HOSTS=reading-os-api.onrender.com
DB_NAME=reading_os
DB_USER=reading_os_user
DB_PASSWORD=<from-database-internal-url>
DB_HOST=<from-database-internal-url>
DB_PORT=5432
CORS_ALLOWED_ORIGINS=https://reading-os-frontend.onrender.com
MEDIA_URL=/media/
MEDIA_ROOT=media
```

**Kako da nađeš database credentials:**
- Idi na tvoju PostgreSQL database u Render
- Scroll do **"Connections"**
- Kopiraj **Internal Database URL**: `postgresql://user:password@host:5432/dbname`
- Izvuci: `user`, `password`, `host`

5. Klikni **"Create Web Service"**
6. Sačekaj ~5-10 minuta da se build-uje i deploy-uje
7. Kopiraj URL (npr. `https://reading-os-api.onrender.com`)

### Step 3: Deploy Vue Frontend

1. Klikni **"New +"** → **"Static Site"**
2. Konektuj isti GitHub repository
3. Podesi:
   - **Name**: `reading-os-frontend`
   - **Region**: `Frankfurt`
   - **Branch**: `main`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Plan**: **Free**

4. **Environment Variables** - dodaj:

```
VITE_API_URL=https://reading-os-api.onrender.com/api
```

5. Klikni **"Create Static Site"**
6. Sačekaj ~3-5 minuta
7. Kopiraj frontend URL (npr. `https://reading-os-frontend.onrender.com`)

### Step 4: Update Backend CORS Settings

Sada kada znaš frontend URL, moraš da ažuriraš backend:

1. Idi na backend service (`reading-os-api`)
2. Klikni **"Environment"** tab
3. Ažuriraj `CORS_ALLOWED_ORIGINS`:
   ```
   https://reading-os-frontend.onrender.com
   ```
4. Klikni **"Save Changes"**
5. Backend će se automatski restartovati

### Step 5: Migracija Baze Podataka

Moraš da prebacis lokalnu bazu na Render PostgreSQL:

#### Opcija A: Ručno kreiranje admin korisnika (brzo, za test)

1. U Render Dashboard → Backend Service → **"Shell"** tab
2. Pokreni:
```bash
python manage.py createsuperuser
```
3. Prati upute

#### Opcija B: Migracija postojeće baze (kompletno)

**Izvoz lokalne baze:**
```bash
cd backend
pg_dump -U postgres -h localhost -d reading_os -F c -b -v -f reading_os_backup.dump
```

**Uvoz na Render:**
```bash
# Preuzmi Render database credentials
# Idi na Render → Database → Connections → External Database URL

# Restore dump
pg_restore -U reading_os_user -h dpg-xxxxx.frankfurt-postgres.render.com -d reading_os -v reading_os_backup.dump
```

**Alternativno (JSON fixtures):**
```bash
# Lokalno
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 2 > data.json

# Upload data.json na backend (Shell u Render-u)
python manage.py loaddata data.json
```

## Provera Deployment-a

1. **Backend Test**: Idi na `https://reading-os-api.onrender.com/api/`
   - Trebalo bi da vidiš Django REST Framework API root

2. **Frontend Test**: Idi na `https://reading-os-frontend.onrender.com`
   - Trebalo bi da vidiš login stranicu

3. **Login Test**: Pokušaj da se uloguješ sa superuser account-om

## Važne Napomene

### Free Tier Limitations

- **Backend spava posle 15min neaktivnosti** - prvi request posle spavanja traje ~30-60s (cold start)
- **Database se briše posle 90 dana** - Render šalje email pre brisanja, samo klikni link da produžiš
- **750 sati runtime mesečno** - dovoljno ako spavas kad ne koristiš

### Maintenance

**Update aplikacije:**
```bash
git add .
git commit -m "Update feature X"
git push origin main
```
Render će automatski detektovati push i ponovo deploy-ovati.

**View Logs:**
- Render Dashboard → Service → **"Logs"** tab

**Database Backup:**
- Render Dashboard → Database → **"Backups"** (ručno ili automatski)

## Troubleshooting

### Backend vraća 500 error
- Proveri **Logs** u Render Dashboard
- Proveri da li su svi environment variables postavljeni
- Proveri database connection credentials

### Frontend ne može da se konektuje na backend
- Proveri `VITE_API_URL` u frontend environment variables
- Proveri `CORS_ALLOWED_ORIGINS` u backend environment variables
- Proveri browser konzolu za CORS greške

### Static files ne rade
```bash
# U backend shell na Render-u:
python manage.py collectstatic --no-input
```

### Database connection error
- Proveri da li Database service radi
- Proveri credentials (DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)
- Koristi **Internal Database URL** (brži, unutar Render network-a)

## Custom Domain (Opciono)

Ako imaš svoj domain (npr. `readingos.com`):

1. Render Dashboard → Service → **"Settings"**
2. Scroll do **"Custom Domain"**
3. Dodaj `readingos.com` i `www.readingos.com`
4. Podesi DNS records kod domain provider-a:
   - A record: `@` → `<render-ip>`
   - CNAME record: `www` → `<your-app>.onrender.com`

## Cena (Update na Paid Plan)

Ako ti treba production-ready hosting bez sleep mode-a:

- **Starter Plan**: $7/mesec po servisu (bez sleep-a)
- **PostgreSQL**: $7/mesec (više storage, automatski backups)

**Total**: ~$21/mesec za backend + frontend + database

---

**Gotovo!** 🎉 Tvoja aplikacija je live na Render-u!

Ako imaš problema, proveri [Render Documentation](https://render.com/docs) ili Logs.
