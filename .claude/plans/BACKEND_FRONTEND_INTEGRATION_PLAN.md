# Backend-Frontend Integration Plan

## Overview
This plan outlines the steps to connect the OpenDeck Angular frontend to the FastAPI backend, enabling the application to use the PostgreSQL database for decks, topics, and flashcards data.

## Current State Analysis

### Backend (FastAPI)
- **Status**: ✅ Fully implemented
- **Location**: `/backend/`
- **API Base URL**: `http://localhost:8000/api/v1`
- **Running via**: Docker Compose (port 8000)
- **Database**: PostgreSQL (port 5432)
- **CORS**: Configured to allow frontend origins

**Available Endpoints**:
- **Topics**: `/api/v1/topics` (GET, POST, PUT, DELETE)
- **Decks**: `/api/v1/decks` (GET, POST, PUT, DELETE)
- **Cards**: `/api/v1/decks/{deck_id}/cards` and `/api/v1/cards/{card_id}`
- **Auth**: `/api/v1/auth/*` (login, register, etc.)
- **Health**: `/health`

### Frontend (Angular)
- **Status**: ⚠️ Using mock data
- **Location**: `/opendeck-portal/`
- **Current Components**:
  - `flashcard-decks-list.component.ts` - Lists decks with hardcoded data
  - `flashcard-viewer.component.ts` - Shows cards with hardcoded data
- **Missing**: API services, environment configuration, HTTP interceptors, auth state management

---

## Integration Plan

### Phase 1: Foundation Setup 🏗️
**Agent**: `python-backend-engineer`

#### 1.1 Update Backend CORS Configuration
- Verify CORS allows `http://localhost:4200` (Angular dev server)
- Ensure credentials are properly configured
- Test CORS with a simple preflight request

#### 1.2 Verify Backend Test Data
- Ensure database has test data loaded
- Run script: `/backend/scripts/load_test_data.py`
- Verify topics, decks, and cards exist via API

**Expected Output**: Backend ready to accept frontend requests

---

### Phase 2: Angular Services & Configuration 🔧
**Agent**: `angular-primeng-ui-engineer`

#### 2.1 Create Environment Configuration
**Files to create**:
- `opendeck-portal/src/environments/environment.ts`
- `opendeck-portal/src/environments/environment.development.ts`

```typescript
// environment.development.ts
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000/api/v1',
  apiHealthUrl: 'http://localhost:8000/health'
};
```

#### 2.2 Create TypeScript Models/Interfaces
**Location**: `opendeck-portal/src/app/models/`

**Files to create**:
- `topic.model.ts` - Topic interface matching backend schema
- `deck.model.ts` - Deck interface with topics array
- `card.model.ts` - Card/Flashcard interface with topics
- `api-response.model.ts` - Paginated response wrapper
- `user.model.ts` - User authentication model

**Example**:
```typescript
// deck.model.ts
export interface Topic {
  id: string;
  name: string;
  description?: string;
}

export interface Deck {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  category: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  card_count: number;
  topics: Topic[];
  created_at: string;
  updated_at: string;
}

export interface DeckListResponse {
  items: Deck[];
  total: number;
  limit: number;
  offset: number;
}
```

#### 2.3 Create Core Services
**Location**: `opendeck-portal/src/app/services/`

**Files to create**:
- `api.service.ts` - Base HTTP service with error handling
- `topic.service.ts` - Topic CRUD operations
- `deck.service.ts` - Deck CRUD operations
- `card.service.ts` - Card CRUD operations
- `auth.service.ts` - Authentication (enhance existing)

**Example Structure**:
```typescript
// deck.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import { Deck, DeckListResponse } from '../models/deck.model';

@Injectable({
  providedIn: 'root'
})
export class DeckService {
  private apiUrl = `${environment.apiBaseUrl}/decks`;

  constructor(private http: HttpClient) {}

  getDecks(params?: {
    category?: string;
    difficulty?: string;
    topic_id?: string;
    limit?: number;
    offset?: number;
  }): Observable<DeckListResponse> {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key]);
        }
      });
    }
    return this.http.get<DeckListResponse>(this.apiUrl, { params: httpParams });
  }

  getDeck(deckId: string): Observable<Deck> {
    return this.http.get<Deck>(`${this.apiUrl}/${deckId}`);
  }

  createDeck(deck: Partial<Deck>): Observable<Deck> {
    return this.http.post<Deck>(this.apiUrl, deck);
  }

  updateDeck(deckId: string, deck: Partial<Deck>): Observable<Deck> {
    return this.http.put<Deck>(`${this.apiUrl}/${deckId}`, deck);
  }

  deleteDeck(deckId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${deckId}`);
  }
}
```

#### 2.4 Create HTTP Interceptors
**Location**: `opendeck-portal/src/app/interceptors/`

**Files to create**:
- `auth.interceptor.ts` - Add JWT tokens to requests
- `error.interceptor.ts` - Global error handling
- `loading.interceptor.ts` - Loading state management (optional)

**Example**:
```typescript
// auth.interceptor.ts
import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  if (token) {
    const cloned = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`)
    });
    return next(cloned);
  }

  return next(req);
};
```

**Expected Output**: Complete service layer ready for component integration

---

### Phase 3: Component Integration 🎨
**Agent**: `angular-primeng-ui-engineer`

#### 3.1 Update Flashcard Decks List Component
**File**: `opendeck-portal/src/app/pages/flashcards/flashcard-decks-list.component.ts`

**Changes**:
1. Inject `DeckService`
2. Replace `mockDecks` with API call in `ngOnInit()`
3. Add loading state (PrimeNG ProgressSpinner)
4. Add error handling (PrimeNG Toast/Message)
5. Update data mapping to match backend schema

**Key Updates**:
```typescript
export class FlashcardDecksListComponent implements OnInit {
  searchQuery = signal<string>('');
  decks = signal<Deck[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);

  constructor(
    private router: Router,
    private deckService: DeckService
  ) {}

  ngOnInit(): void {
    this.loadDecks();
  }

  private loadDecks(): void {
    this.loading.set(true);
    this.deckService.getDecks({ limit: 100 }).subscribe({
      next: (response) => {
        this.decks.set(response.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load decks');
        this.loading.set(false);
        console.error('Error loading decks:', err);
      }
    });
  }
}
```

#### 3.2 Update Flashcard Viewer Component
**File**: `opendeck-portal/src/app/pages/flashcards/flashcard-viewer.component.ts`

**Changes**:
1. Inject `CardService` and `DeckService`
2. Load cards from API based on route `deckId`
3. Add loading/error states
4. Update card navigation to work with API data
5. Fix data mapping (backend uses `question`/`answer`, frontend might differ)

**Key Updates**:
```typescript
export class FlashcardViewerComponent implements OnInit {
  deckTitle = signal<string>('');
  cards = signal<Card[]>([]);
  loading = signal<boolean>(false);
  error = signal<string | null>(null);
  currentIndex = signal<number>(0);
  showAnswer = signal<boolean>(false);

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private deckService: DeckService,
    private cardService: CardService
  ) {}

  ngOnInit(): void {
    const deckId = this.route.snapshot.paramMap.get('deckId');
    if (deckId) {
      this.loadDeckAndCards(deckId);
    } else {
      this.router.navigate(['/pages/flashcards']);
    }
  }

  private loadDeckAndCards(deckId: string): void {
    this.loading.set(true);

    // Load deck details
    this.deckService.getDeck(deckId).subscribe({
      next: (deck) => {
        this.deckTitle.set(deck.title);
      },
      error: (err) => {
        console.error('Error loading deck:', err);
      }
    });

    // Load cards
    this.cardService.getCardsForDeck(deckId).subscribe({
      next: (response) => {
        this.cards.set(response.items);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set('Failed to load cards');
        this.loading.set(false);
        console.error('Error loading cards:', err);
      }
    });
  }
}
```

#### 3.3 Update Templates
**Files**:
- `flashcard-decks-list.component.html`
- `flashcard-viewer.component.html`

**Changes**:
- Add `<p-progressSpinner>` for loading states
- Add `<p-message>` for error states
- Update data bindings to match new models
- Add empty state when no decks/cards found

**Expected Output**: Components fully integrated with backend API

---

### Phase 4: Authentication Flow 🔐
**Agent**: `angular-primeng-ui-engineer`

#### 4.1 Enhance Auth Service
**File**: `opendeck-portal/src/app/services/auth.service.ts`

**Features to add**:
- Login/Register API calls
- JWT token storage (localStorage/sessionStorage)
- Token refresh logic
- Auth state management (RxJS BehaviorSubject)
- Route guards

#### 4.2 Create Auth Components (if not existing)
**Location**: `opendeck-portal/src/app/auth/`

**Components**:
- `login.component.ts` - Login form
- `register.component.ts` - Registration form

#### 4.3 Add Route Guards
**File**: `opendeck-portal/src/app/guards/auth.guard.ts`

**Purpose**: Protect flashcard routes, redirect to login if not authenticated

**Expected Output**: Full authentication flow with protected routes

---

### Phase 5: App Configuration & Providers 📦
**Agent**: `angular-primeng-ui-engineer`

#### 5.1 Update App Config
**File**: `opendeck-portal/src/app/app.config.ts`

**Add**:
- `provideHttpClient(withInterceptors([authInterceptor, errorInterceptor]))`
- Import services as providers
- Configure PrimeNG toast/message service

#### 5.2 Update Routing
**File**: `opendeck-portal/src/app/app.routes.ts`

**Verify**:
- Flashcard routes are properly configured
- Auth guards are applied
- Lazy loading if needed

**Expected Output**: App properly configured with all providers

---

### Phase 6: Testing & Validation ✅
**Agent**: `general-purpose`

#### 6.1 Backend Testing
**Tasks**:
1. Start Docker containers: `docker-compose up`
2. Verify health endpoint: `curl http://localhost:8000/health`
3. Load test data: `docker-compose exec app python scripts/load_test_data.py`
4. Test API endpoints with curl/Postman
5. Verify CORS headers

#### 6.2 Frontend Testing
**Tasks**:
1. Start Angular dev server: `cd opendeck-portal && ng serve`
2. Open browser: `http://localhost:4200`
3. Test deck listing loads from API
4. Test clicking a deck shows cards from API
5. Test search/filter functionality
6. Test authentication flow
7. Verify error handling (stop backend, check error messages)

#### 6.3 Integration Testing
**Tasks**:
1. Test full user flow: register → login → view decks → view cards
2. Test data persistence (reload page)
3. Test token expiration handling
4. Test network error scenarios

**Expected Output**: Fully functional integrated application

---

## Implementation Agent Assignment

### Agent 1: `python-backend-engineer`
**Responsibilities**:
- Phase 1.1: Update CORS configuration
- Phase 1.2: Verify test data script
- Phase 6.1: Backend testing

**Estimated Time**: 1-2 hours

---

### Agent 2: `angular-primeng-ui-engineer` (Primary)
**Responsibilities**:
- Phase 2: All Angular services and configuration
- Phase 3: Component integration
- Phase 4: Authentication flow
- Phase 5: App configuration
- Phase 6.2: Frontend testing

**Estimated Time**: 4-6 hours

---

### Agent 3: `general-purpose`
**Responsibilities**:
- Phase 6.3: Integration testing
- Documentation updates
- Troubleshooting

**Estimated Time**: 1-2 hours

---

## Parallel Execution Strategy

### Parallel Track 1 (Backend)
- Agent 1 handles Phase 1 independently

### Parallel Track 2 (Frontend Foundation)
- Agent 2 starts Phase 2 (services, models, config)
- Can begin while Agent 1 works on backend

### Sequential Track
- Phase 3 (component integration) requires Phase 2 completion
- Phase 4 (auth) can partially overlap with Phase 3
- Phase 5 (app config) requires Phase 2-4 completion
- Phase 6 (testing) requires all phases complete

---

## Data Model Mapping

### Backend → Frontend

| Backend Model | Frontend Model | Notes |
|--------------|----------------|-------|
| `Topic` (id, name, description) | `Topic` | Direct mapping |
| `Deck` (id, user_id, title, description, category, difficulty, card_count) | `Deck` | Add computed `topics` array |
| `Card` (id, deck_id, question, answer, source, source_url) | `Card` / `FlashCardData` | Add computed `topics` array |
| `DifficultyLevel` enum | `'beginner' \| 'intermediate' \| 'advanced'` | Lowercase in frontend |
| Pagination (items, total, limit, offset) | `ListResponse<T>` | Generic interface |

---

## Environment Variables

### Backend (.env)
```bash
ENV=development
DATABASE_URL=postgresql://opendeck_user:opendeck_pass@db:5432/opendeck
ALLOWED_ORIGINS=http://localhost:4200,http://localhost:4200/*
SECRET_KEY=dev-secret-key
JWT_SECRET_KEY=dev-jwt-secret-key
```

### Frontend (environment.ts)
```typescript
export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000/api/v1',
  apiHealthUrl: 'http://localhost:8000/health'
};
```

---

## Success Criteria

✅ **Phase 1 Complete**: Backend returns data, CORS works, test data loaded

✅ **Phase 2 Complete**: All services created, TypeScript compiles without errors

✅ **Phase 3 Complete**: Components display API data, no more mock data

✅ **Phase 4 Complete**: Users can login and access protected routes

✅ **Phase 5 Complete**: App runs without errors, all HTTP requests include auth

✅ **Phase 6 Complete**: Full integration tested, all features working

---

## Troubleshooting Guide

### Issue: CORS Errors
**Solution**:
1. Check backend `app/config.py` - ensure `http://localhost:4200` in `allowed_origins`
2. Verify CORS middleware in `app/main.py`
3. Check browser console for specific CORS error

### Issue: 401 Unauthorized
**Solution**:
1. Verify JWT token in localStorage
2. Check token expiration
3. Ensure `Authorization: Bearer <token>` header is set
4. Test auth endpoint directly

### Issue: Data Not Loading
**Solution**:
1. Check browser Network tab for API calls
2. Verify backend is running: `docker-compose ps`
3. Test API directly: `curl http://localhost:8000/api/v1/decks`
4. Check backend logs: `docker-compose logs app`

### Issue: TypeScript Errors
**Solution**:
1. Ensure models match backend schema exactly
2. Use optional chaining (`?.`) for nullable fields
3. Add proper type guards
4. Run `ng build` to see all compilation errors

---

## Next Steps After Integration

1. **Add Topic Management UI**: Create/edit/delete topics
2. **Add Deck Management UI**: Create/edit/delete decks
3. **Add Card Management UI**: Create/edit/delete individual cards
4. **Study Session Features**: Track progress, spaced repetition
5. **Document Upload**: Integrate AI for flashcard generation from PDFs
6. **User Profile**: Settings, preferences, statistics

---

## Notes

- This plan assumes the backend is fully functional and tested
- Frontend uses standalone components (Angular 14+)
- PrimeNG is already installed and configured
- JWT-based authentication is implemented in backend
- Test data should include at least 3-5 decks with 5-10 cards each

---

## Estimated Total Time

| Phase | Time Estimate |
|-------|---------------|
| Phase 1 | 1-2 hours |
| Phase 2 | 3-4 hours |
| Phase 3 | 2-3 hours |
| Phase 4 | 2-3 hours |
| Phase 5 | 1 hour |
| Phase 6 | 2-3 hours |
| **TOTAL** | **11-18 hours** |

---

## File Structure Overview

```
OpenDeck/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── api/                     # ✅ Complete
│   │   │   ├── topics.py
│   │   │   ├── decks.py
│   │   │   ├── cards.py
│   │   │   └── auth.py
│   │   ├── core/                    # ✅ Complete
│   │   ├── db/                      # ✅ Complete
│   │   └── schemas/                 # ✅ Complete
│   ├── docker-compose.yml           # ✅ Complete
│   └── scripts/load_test_data.py    # ✅ Complete
│
└── opendeck-portal/                  # Angular Frontend
    ├── src/
    │   ├── app/
    │   │   ├── models/              # ⚠️ TO CREATE
    │   │   │   ├── topic.model.ts
    │   │   │   ├── deck.model.ts
    │   │   │   ├── card.model.ts
    │   │   │   └── api-response.model.ts
    │   │   ├── services/            # ⚠️ TO CREATE/UPDATE
    │   │   │   ├── api.service.ts
    │   │   │   ├── topic.service.ts
    │   │   │   ├── deck.service.ts
    │   │   │   ├── card.service.ts
    │   │   │   └── auth.service.ts
    │   │   ├── interceptors/        # ⚠️ TO CREATE
    │   │   │   ├── auth.interceptor.ts
    │   │   │   └── error.interceptor.ts
    │   │   ├── guards/              # ⚠️ TO CREATE
    │   │   │   └── auth.guard.ts
    │   │   └── pages/
    │   │       └── flashcards/      # ⚠️ TO UPDATE
    │   │           ├── flashcard-decks-list.component.ts
    │   │           └── flashcard-viewer.component.ts
    │   └── environments/            # ⚠️ TO CREATE
    │       ├── environment.ts
    │       └── environment.development.ts
    └── angular.json
```

Legend:
- ✅ Complete and ready
- ⚠️ Needs creation or updates

---

**End of Integration Plan**
