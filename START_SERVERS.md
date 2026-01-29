# Reading OS - Start Servers

## Port Configuration
- **Frontend (Vue + Vite):** http://localhost:5175
- **Backend (Django):** http://localhost:8001
- **Database (PostgreSQL 17):** localhost:5433

---

## PostgreSQL Setup (Linux)

### Database Clusters:
- **PostgreSQL 16 (main):** Port 5432 - For main application
- **PostgreSQL 17 (readingos):** Port 5433 - For reading-os application

### Check PostgreSQL Status:
```bash
pg_lsclusters
```

### Start/Stop PostgreSQL Clusters:
```bash
# Start reading-os cluster
sudo pg_ctlcluster 17 readingos start

# Stop reading-os cluster
sudo pg_ctlcluster 17 readingos stop

# Restart reading-os cluster
sudo pg_ctlcluster 17 readingos restart
```

---

## How to Start

### 1. Ensure PostgreSQL 17 is Running
```bash
# Check status
pg_lsclusters

# If not running, start it
sudo pg_ctlcluster 17 readingos start
```

### 2. Start Backend (Django)
```bash
cd ~/Projects/reading-os/backend
source venv/bin/activate
python manage.py runserver 8001
```

### 3. Start Frontend (Vue)
```bash
# In a new terminal
cd ~/Projects/reading-os/frontend
npm run dev
```

Frontend will automatically open at: **http://localhost:5175**

---

## Notes
- These ports are different from your other project to avoid conflicts
- Backend API is proxied through Vite: `/api/*` → `http://127.0.0.1:8001`
- CORS is configured to allow requests from `http://localhost:5175`
- PostgreSQL 17 runs on port 5433 (different from main app's PostgreSQL 16 on 5432)

---

## Quick Start (Linux)
```bash
# Terminal 1 - Backend
cd ~/Projects/reading-os/backend && source venv/bin/activate && python manage.py runserver 8001

# Terminal 2 - Frontend
cd ~/Projects/reading-os/frontend && npm run dev
```

---

## Create Superuser (First Time Setup)
```bash
cd ~/Projects/reading-os/backend
source venv/bin/activate
python manage.py createsuperuser
```

Admin panel: http://localhost:8001/admin
