# Reading OS - Start Servers

## Port Configuration
- **Frontend (Vue + Vite):** http://localhost:5175
- **Backend (Django):** http://localhost:8001
- **Database (PostgreSQL):** localhost:5432

---

## How to Start

### 1. Start Backend (Django)
```bash
cd D:\projects\reading-os\backend
python manage.py runserver 8001
```

### 2. Start Frontend (Vue)
```bash
cd D:\projects\reading-os\frontend
npm run dev
```

Frontend will automatically open at: **http://localhost:5175**

---

## Notes
- These ports are different from your other project to avoid conflicts
- Backend API is proxied through Vite: `/api/*` → `http://127.0.0.1:8001`
- CORS is configured to allow requests from `http://localhost:5175`

---

## Quick Start (PowerShell)
```powershell
# Terminal 1 - Backend
cd D:\projects\reading-os\backend; python manage.py runserver 8001

# Terminal 2 - Frontend
cd D:\projects\reading-os\frontend; npm run dev
```
