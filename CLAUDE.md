# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

![OpenDeck Logo](images/opendeck_line_cropped.png)

## Project Overview

OpenDeck is an AI-first web application that automatically generates flashcards from university course documents. The app consists of a FastAPI backend with PostgreSQL database and an Angular frontend with PrimeNG components.

## Current Implementation Status

### Phase 1: MVP ✅ Complete
- User authentication with JWT tokens
- Deck and flashcard CRUD operations
- PostgreSQL database with Alembic migrations
- RESTful API with OpenAPI documentation
- Angular 20 frontend with PrimeNG 20
- Multi-language support (English, Spanish)
- Dark mode support
- User preferences page with theme customization

### Phase 2: AI Integration (Planned)
- Document upload and processing
- AI-powered flashcard generation
- Source attribution implementation
- Background processing

## Tech Stack

### Frontend
- **Framework**: Angular 20 (standalone components)
- **UI Library**: PrimeNG 20 with Aura theme
- **Styling**: TailwindCSS + SCSS
- **State Management**: Angular Signals
- **i18n**: ngx-translate (English, Spanish)
- **HTTP**: HttpClient with interceptors for auth
- **Routing**: Angular Router with guards

### Backend
- **Framework**: FastAPI 0.109+
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0
- **Authentication**: JWT tokens with bcrypt password hashing
- **Migrations**: Alembic
- **Testing**: pytest with coverage
- **Containerization**: Docker & docker-compose

### Infrastructure
- **Development**: Docker Compose for local environment
- **Future Hosting**: AWS (S3, Lambda, CloudFront, DynamoDB)

## Project Structure

```
OpenDeck/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes (auth, decks, cards, topics)
│   │   ├── core/              # Domain models & interfaces
│   │   ├── db/                # Database layer (SQLAlchemy)
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic services
│   ├── tests/                 # Backend tests
│   ├── docker-compose.yml     # Docker setup
│   └── README.md             # Backend documentation
│
├── opendeck-portal/           # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/   # Flashcard viewer, etc.
│   │   │   ├── pages/        # Dashboard, deck view, preferences, auth
│   │   │   ├── services/     # Auth, API services
│   │   │   ├── models/       # TypeScript models (User, Deck, Card)
│   │   │   ├── guards/       # Auth guards
│   │   │   ├── interceptors/ # Auth & error interceptors
│   │   │   └── layout/       # Topbar, sidebar, layout components
│   │   └── assets/
│   │       └── i18n/         # Translation files (en.json, es.json)
│   └── README.md             # Frontend documentation
```

## Core Architecture

### Backend Architecture (Clean Architecture)
- **Core Layer**: Domain models and interfaces (framework-agnostic)
- **Data Layer**: Repository implementations (PostgreSQL via SQLAlchemy)
- **API Layer**: FastAPI routes with dependency injection
- **Service Layer**: Business logic (authentication, etc.)

### Frontend Architecture
- **Standalone Components**: All components are standalone (no NgModules)
- **Signal-Based State**: Using Angular Signals for reactive state
- **Service Layer**: Centralized API communication via services
- **Guard Protection**: Auth guards for route protection
- **Interceptors**: Automatic token injection and refresh

### Authentication Flow
1. User logs in via `/api/v1/auth/login`
2. Backend returns access token (30min) and refresh token (7 days)
3. Frontend stores tokens in localStorage
4. Auth interceptor automatically adds Bearer token to requests
5. Error interceptor auto-refreshes expired tokens
6. Auth guard protects authenticated routes

### Document Processing Pipeline (Future)
The application will follow this workflow:
1. Users organize course materials into subfolders by class (e.g., `Biology101/`, `Calculus/`)
2. The system scans and processes documents (PDFs, Word docs, slides, notes)
3. AI extracts key concepts, definitions, and relationships
4. Flashcards are generated with source attribution
5. Users review and study the generated flashcards

### Source Attribution Requirement
**Critical**: All AI-generated responses and flashcards MUST include precise references to the source material (document name, page/section) so users can verify and corroborate the information.

## Development Commands

### Backend
```bash
cd backend

# Start with Docker (recommended)
docker-compose up -d

# View logs
docker-compose logs -f app

# Run tests
pytest

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

### Frontend
```bash
cd opendeck-portal

# Install dependencies
npm install

# Start development server
npm start  # or: ng serve

# Build for production
ng build

# Run tests
ng test

# Lint code
ng lint
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (get JWT tokens)
- `POST /api/v1/auth/refresh` - Refresh access token

### Topics
- `GET /api/v1/topics` - List all topics (with pagination)
- `GET /api/v1/topics/{id}` - Get single topic

### Decks
- `GET /api/v1/decks` - List user's decks (with filters)
- `GET /api/v1/decks/{id}` - Get single deck
- `POST /api/v1/decks` - Create new deck
- `PUT /api/v1/decks/{id}` - Update deck
- `DELETE /api/v1/decks/{id}` - Delete deck

### Flashcards
- `GET /api/v1/decks/{id}/cards` - List cards in deck
- `GET /api/v1/cards/{id}` - Get single card
- `POST /api/v1/decks/{id}/cards` - Create card
- `PUT /api/v1/cards/{id}` - Update card
- `DELETE /api/v1/cards/{id}` - Delete card

### Health
- `GET /health` - Health check & database status

## Key Features Implemented

### User Interface
- Login/Register pages with form validation
- Dashboard displaying available decks by topic
- Deck detail view with flashcard list
- Interactive flashcard viewer with keyboard navigation
- User preferences page (language, dark mode, theme customization)
- Responsive topbar with user menu
- Dark mode toggle with persistent settings
- Multi-language UI (English/Spanish) with persistent language selection
- **PrimeNG ConfirmDialog**: Logout confirmation with translated messages

### PrimeNG Components Used
- ConfirmDialog - For logout and reset confirmations
- Card - For deck and content cards
- Button - Throughout the app
- Select - For language and preference selections
- Menu - For user menu dropdown
- Avatar - For user profile display
- Message - For success/error feedback
- Dialog - For modals (future use)

### Authentication & Authorization
- JWT-based authentication
- Automatic token refresh
- Auth guards for protected routes
- Error interceptor with user feedback

## Development Guidelines

### Frontend Development
1. Use standalone components (no NgModules)
2. Use Angular Signals for state management
3. Use PrimeNG components for UI consistency
4. Add translations for all user-facing text to both `en.json` and `es.json`
5. Support dark mode in all new components
6. Use TailwindCSS utility classes for styling
7. Follow Angular style guide and naming conventions

### Backend Development
1. Follow clean architecture principles
2. Add type hints to all functions
3. Write Pydantic schemas for all API inputs/outputs
4. Create Alembic migrations for database changes
5. Write unit and integration tests
6. Follow PEP 8 style guide
7. Use dependency injection via FastAPI

### Code Review Checklist
- [ ] All user-facing text is translated (en.json, es.json)
- [ ] Dark mode compatibility verified
- [ ] Type safety maintained (TypeScript/Python type hints)
- [ ] Error handling implemented
- [ ] Loading states for async operations
- [ ] Responsive design tested
- [ ] Tests written for new features

## Environment Variables

### Backend (.env)
```bash
ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
DATABASE_URL=postgresql://user:pass@localhost:5432/opendeck
ALLOWED_ORIGINS=http://localhost:4200
```

### Frontend (environment.ts)
```typescript
apiBaseUrl: 'http://localhost:8000'
production: false
```

## Testing

### Backend Tests
```bash
cd backend
pytest                           # Run all tests
pytest --cov=app                # With coverage
pytest tests/unit/              # Unit tests only
```

### Frontend Tests
```bash
cd opendeck-portal
ng test                         # Run tests
ng test --code-coverage         # With coverage
```

## Future Enhancements (Phase 2+)

### Document Processing
- Document upload endpoint
- S3/local storage service
- Text extraction from PDF/DOCX
- Metadata extraction and indexing

### AI Integration
- OpenAI/Claude integration for flashcard generation
- Natural language processing for concept identification
- Question-answer pair generation from source material
- Background processing with Celery

### Enhanced Features
- Study statistics and progress tracking
- Spaced repetition algorithm
- Deck sharing functionality
- Export/import decks
- Mobile app (React Native)

### Infrastructure
- AWS Lambda deployment
- DynamoDB integration
- CloudFront CDN
- Advanced caching strategies
