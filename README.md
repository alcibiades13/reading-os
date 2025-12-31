# Reading OS 📚

A modern, full-stack reading management platform built with Django REST Framework and Vue 3.

## Features

- 📖 **Personal Library** - Track your reading progress, organize books
- 🔍 **Book Discovery** - Search and import books from Delfi.rs and other sources
- 💬 **Quotes & Vocabulary** - Save memorable quotes and build your lexicon
- 📊 **Reading Challenges** - Set and track reading goals
- 👥 **Social Features** - Connect with friends, share progress in circles
- 📝 **Book Reviews** - Write and read book reviews
- 🎯 **Reading Lists** - Create and manage custom book lists

## Tech Stack

### Backend
- Django 5.0 + Django REST Framework
- PostgreSQL database
- JWT authentication
- Beautiful Soup & Playwright for web scraping

### Frontend
- Vue 3 with Composition API
- Tailwind CSS for styling
- Pinia for state management
- Axios for API calls
- Vite for build tooling

## Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Install Playwright browsers (for scraping)
playwright install

# Run development server
python manage.py runserver
```

Backend will be available at: `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional for dev)
cp .env.example .env

# Run development server
npm run dev
```

Frontend will be available at: `http://localhost:5175`

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions to Render.com.

**Quick Deploy:**
1. Push code to GitHub
2. Create Render account
3. Create PostgreSQL database
4. Deploy backend (Web Service)
5. Deploy frontend (Static Site)

## Project Structure

```
reading-os/
├── backend/                # Django backend
│   ├── apps/              # Django apps
│   │   ├── users/         # User authentication
│   │   ├── books/         # Books, authors, genres
│   │   ├── reading/       # Reading progress, quotes
│   │   ├── lists/         # Book lists
│   │   ├── challenges/    # Reading challenges
│   │   └── social/        # Social features
│   ├── config/            # Django settings
│   └── utils/             # Utilities (scrapers)
├── frontend/              # Vue 3 frontend
│   ├── src/
│   │   ├── components/    # Vue components
│   │   ├── views/         # Page views
│   │   ├── stores/        # Pinia stores
│   │   ├── services/      # API services
│   │   └── router/        # Vue Router
│   └── public/            # Static assets
└── DEPLOYMENT.md          # Deployment guide
```

## API Documentation

Once the backend is running, visit:
- API Root: `http://localhost:8000/api/`
- Admin Panel: `http://localhost:8000/admin/`

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

This project is licensed under the MIT License.

## Author

Built with ❤️ by [Your Name]

---

**Happy Reading! 📚**
