# OpenDeck Backend - Phase 1

AI-first flashcard generation backend built with FastAPI, PostgreSQL, and clean architecture principles.

## Overview

OpenDeck backend is designed for dual deployment (on-premises Docker and AWS Lambda). Phase 1 implements the MVP with core functionality:

- User authentication with JWT
- CRUD operations for decks and flashcards
- PostgreSQL database with migrations
- RESTful API with OpenAPI documentation
- Docker-based local development environment

## Tech Stack

- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0
- **Authentication**: JWT tokens with bcrypt password hashing
- **Migrations**: Alembic
- **Testing**: pytest with coverage
- **Containerization**: Docker & docker-compose

## Project Structure

```
backend/
├── app/
│   ├── core/              # Domain models & interfaces (framework-agnostic)
│   │   ├── models.py      # User, Deck, Card, Document models
│   │   └── interfaces.py  # Repository interfaces
│   ├── api/               # FastAPI routes
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── decks.py       # Deck CRUD endpoints
│   │   ├── cards.py       # Card CRUD endpoints
│   │   ├── health.py      # Health check
│   │   └── dependencies.py # Dependency injection
│   ├── db/                # Data access layer
│   │   ├── base.py        # SQLAlchemy setup
│   │   ├── models.py      # Database models
│   │   └── postgres_repo.py # Repository implementations
│   ├── schemas/           # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── auth.py
│   │   ├── deck.py
│   │   ├── card.py
│   │   └── document.py
│   ├── services/          # Business logic services
│   │   └── auth_service.py # Authentication service
│   ├── config.py          # Configuration management
│   └── main.py            # FastAPI application
├── tests/
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── alembic/               # Database migrations
├── docker-compose.yml     # Local development setup
├── Dockerfile             # Multi-stage Docker build
├── requirements.txt       # Python dependencies
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (if running without Docker)

### 1. Clone and Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Run with Docker (Recommended)

```bash
# Start all services (PostgreSQL + API)
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

The API will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. Run Locally (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (ensure it's running)
# Update DATABASE_URL in .env

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## API Endpoints

### Authentication

```
POST   /api/v1/auth/register    # Register new user
POST   /api/v1/auth/login       # Login (get JWT tokens)
POST   /api/v1/auth/refresh     # Refresh access token
```

### Decks

```
GET    /api/v1/decks            # List user's decks (with filters)
GET    /api/v1/decks/{id}       # Get single deck
POST   /api/v1/decks            # Create new deck
PUT    /api/v1/decks/{id}       # Update deck
DELETE /api/v1/decks/{id}       # Delete deck
```

### Flashcards

```
GET    /api/v1/decks/{id}/cards      # List cards in deck
GET    /api/v1/cards/{id}            # Get single card
POST   /api/v1/decks/{id}/cards      # Create card
PUT    /api/v1/cards/{id}            # Update card
DELETE /api/v1/cards/{id}            # Delete card
```

### Health

```
GET    /health                   # Health check & database status
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py

# Run integration tests only
pytest tests/integration/
```

## Authentication Flow

1. **Register**: `POST /api/v1/auth/register`
   ```json
   {
     "email": "user@example.com",
     "name": "John Doe",
     "password": "securepassword"
   }
   ```

2. **Login**: `POST /api/v1/auth/login`
   ```json
   {
     "email": "user@example.com",
     "password": "securepassword"
   }
   ```

   Response:
   ```json
   {
     "access_token": "eyJ...",
     "refresh_token": "eyJ...",
     "token_type": "bearer",
     "expires_in": 1800
   }
   ```

3. **Use Access Token**: Add to request headers:
   ```
   Authorization: Bearer eyJ...
   ```

## Environment Variables

See `.env.example` for all configuration options:

```bash
# Application
ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/opendeck

# CORS
ALLOWED_ORIGINS=http://localhost:4200,http://localhost:3000
```

## Architecture Principles

### Clean Architecture

- **Core Layer**: Domain models and interfaces (no framework dependencies)
- **Data Layer**: Repository implementations (PostgreSQL)
- **API Layer**: FastAPI routes and dependencies
- **Service Layer**: Business logic (authentication, etc.)

### Repository Pattern

Abstract repository interfaces allow swapping database implementations (PostgreSQL ↔ DynamoDB) without changing business logic.

### Dependency Injection

FastAPI's dependency system provides repositories and services to route handlers, enabling testability and loose coupling.

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Update models/schemas as needed
   - Implement business logic in services
   - Add API endpoints in routes
   - Write tests (unit + integration)

3. **Run Tests**
   ```bash
   pytest
   black app/ tests/  # Format code
   ruff check app/    # Lint code
   ```

4. **Create Migration** (if database changes)
   ```bash
   alembic revision --autogenerate -m "Add new field"
   alembic upgrade head
   ```

5. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

## Next Steps (Phase 2)

- [ ] Document upload endpoint
- [ ] S3/local storage service
- [ ] Text extraction from PDF/DOCX
- [ ] OpenAI/Claude integration for flashcard generation
- [ ] Background processing with Celery
- [ ] Source attribution implementation

See `ARCHITECTURE.md` for complete roadmap.

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up -d
```

### Import Errors

```bash
# Ensure you're in the backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

### Migration Issues

```bash
# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

## Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Write docstrings for public functions/classes
4. Include unit tests for business logic
5. Add integration tests for API endpoints
6. Update README for new features

## License

[To be determined]

## Contact

For questions or support, please open an issue on GitHub.
