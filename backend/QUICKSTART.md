# OpenDeck Backend - Quick Start Guide

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## 🚀 Quick Start (Docker - Recommended)

```bash
# 1. Navigate to backend directory
cd /Users/kike/Repos/OpenDeck/backend

# 2. Create environment file
cp .env.example .env

# 3. Start all services (PostgreSQL + API)
docker-compose up -d

# 4. View logs
docker-compose logs -f app

# 5. Access the API
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health
```

## 🔧 Common Commands

### Docker Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Rebuild after code changes
docker-compose up -d --build

# Reset everything (⚠️ deletes data)
docker-compose down -v
docker-compose up -d
```

### Database Migrations

```bash
# Apply migrations (inside container)
docker-compose exec app alembic upgrade head

# Create new migration
docker-compose exec app alembic revision --autogenerate -m "description"

# Rollback last migration
docker-compose exec app alembic downgrade -1

# View migration history
docker-compose exec app alembic history
```

### Testing

```bash
# Run all tests
docker-compose exec app pytest

# Run with coverage
docker-compose exec app pytest --cov=app --cov-report=html

# Run specific test file
docker-compose exec app pytest tests/unit/test_auth_service.py

# Run integration tests only
docker-compose exec app pytest tests/integration/
```

### Code Quality

```bash
# Format code
docker-compose exec app black app/ tests/

# Lint code
docker-compose exec app ruff check app/

# Type check
docker-compose exec app mypy app/
```

## 🐍 Local Development (Without Docker)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env and set DATABASE_URL to your local PostgreSQL

# 4. Run migrations
alembic upgrade head

# 5. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📝 API Usage Examples

### Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "password": "testpassword123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

Save the `access_token` from the response for authenticated requests.

### Create Deck

```bash
curl -X POST http://localhost:8000/api/v1/decks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Biology 101",
    "description": "Introduction to Biology",
    "category": "Science",
    "difficulty": "beginner"
  }'
```

### List Decks

```bash
curl -X GET http://localhost:8000/api/v1/decks \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create Card

```bash
curl -X POST http://localhost:8000/api/v1/decks/{DECK_ID}/cards \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "question": "What is photosynthesis?",
    "answer": "The process by which plants convert light energy into chemical energy",
    "source": "Biology101.pdf - Page 42, Section 3.2"
  }'
```

## 🔍 Troubleshooting

### Database Connection Failed

```bash
# Check if database is running
docker-compose ps

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

### Import Errors

```bash
# Ensure you're in the correct directory
cd /Users/kike/Repos/OpenDeck/backend

# Reinstall dependencies
docker-compose down
docker-compose up -d --build
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000

# Or change port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Map host 8001 to container 8000
```

### Tests Failing

```bash
# Clear test cache
docker-compose exec app pytest --cache-clear

# Reinstall test dependencies
docker-compose exec app pip install -r requirements.txt
```

## 📚 Useful Endpoints

- **API Root**: http://localhost:8000/
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔑 Environment Variables

Key variables in `.env`:

```bash
# Application
ENV=development
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://opendeck_user:opendeck_pass@db:5432/opendeck

# CORS (add your frontend URL)
ALLOWED_ORIGINS=http://localhost:4200,http://localhost:3000
```

## 📖 Next Steps

1. ✅ Backend is running
2. Start the Angular frontend: `cd ../opendeck-portal && npm start`
3. Access frontend: http://localhost:4200
4. Register a user through the UI or API
5. Create decks and cards

## 🆘 Help

- **README**: `/backend/README.md` - Full documentation
- **Architecture**: `/backend/ARCHITECTURE.md` - Design decisions
- **Phase 1 Details**: `/backend/PHASE1_IMPLEMENTATION.md` - Implementation guide
- **API Docs**: http://localhost:8000/docs - Interactive API documentation

## 🐛 Common Issues

### "Module not found" errors
```bash
docker-compose down
docker-compose up -d --build
```

### Database migrations not applied
```bash
docker-compose exec app alembic upgrade head
```

### Permission denied errors
```bash
# On Linux/Mac, fix file permissions
sudo chown -R $USER:$USER .
```

---

**Quick Check**: Visit http://localhost:8000/health - should return `{"status": "healthy"}`
