# Implementation Plan: Spaced Repetition + Study Sessions

## Overview
Implement the SM-2 (SuperMemo 2) algorithm to optimize flashcard review timing and create an engaging study session interface.

## Database Schema Changes

### New Table: `card_reviews`
```sql
CREATE TABLE card_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_date TIMESTAMP NOT NULL DEFAULT NOW(),
    quality INT NOT NULL CHECK (quality >= 0 AND quality <= 5),  -- 0-5 rating
    ease_factor DECIMAL(4,2) NOT NULL,  -- SM-2 ease factor (default 2.5)
    interval_days INT NOT NULL,  -- Days until next review
    repetitions INT NOT NULL DEFAULT 0,  -- Number of successful reviews
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_card_reviews_card_user ON card_reviews(card_id, user_id);
CREATE INDEX idx_card_reviews_next_review ON card_reviews(user_id, review_date);
```

### New Table: `study_sessions`
```sql
CREATE TABLE study_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    deck_id UUID NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP,
    cards_reviewed INT DEFAULT 0,
    cards_correct INT DEFAULT 0,
    cards_incorrect INT DEFAULT 0,
    total_duration_seconds INT,
    session_type VARCHAR(50) DEFAULT 'review',  -- 'review', 'learn_new', 'cram'
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_study_sessions_user ON study_sessions(user_id);
CREATE INDEX idx_study_sessions_deck ON study_sessions(deck_id);
```

### Extend `flashcards` table:
```sql
ALTER TABLE flashcards ADD COLUMN ease_factor DECIMAL(4,2) DEFAULT 2.5;
ALTER TABLE flashcards ADD COLUMN interval_days INT DEFAULT 0;
ALTER TABLE flashcards ADD COLUMN repetitions INT DEFAULT 0;
ALTER TABLE flashcards ADD COLUMN next_review_date TIMESTAMP;
ALTER TABLE flashcards ADD COLUMN is_learning BOOLEAN DEFAULT TRUE;
```

## Backend Implementation

### New Files

#### `backend/app/core/models.py` - Add domain models:
```python
@dataclass
class CardReview:
    id: uuid.UUID
    card_id: uuid.UUID
    user_id: uuid.UUID
    review_date: datetime
    quality: int  # 0-5
    ease_factor: float
    interval_days: int
    repetitions: int

@dataclass
class StudySession:
    id: uuid.UUID
    user_id: uuid.UUID
    deck_id: uuid.UUID
    started_at: datetime
    ended_at: Optional[datetime]
    cards_reviewed: int
    cards_correct: int
    cards_incorrect: int
    total_duration_seconds: Optional[int]
    session_type: str
```

#### `backend/app/services/spaced_repetition.py` - SM-2 algorithm:
```python
from datetime import datetime, timedelta
from typing import Tuple

class SM2Algorithm:
    """SuperMemo 2 spaced repetition algorithm"""

    @staticmethod
    def calculate_next_interval(
        quality: int,  # 0-5 rating
        ease_factor: float,
        interval_days: int,
        repetitions: int
    ) -> Tuple[float, int, int]:
        """
        Returns: (new_ease_factor, new_interval_days, new_repetitions)
        quality: 0-2 = incorrect, 3-5 = correct
        """
        # Update ease factor
        new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_ease = max(1.3, new_ease)  # Minimum ease factor

        # Calculate interval
        if quality < 3:
            # Incorrect answer - reset
            new_reps = 0
            new_interval = 1
        else:
            # Correct answer
            new_reps = repetitions + 1
            if new_reps == 1:
                new_interval = 1
            elif new_reps == 2:
                new_interval = 6
            else:
                new_interval = int(interval_days * new_ease)

        return new_ease, new_interval, new_reps

    @staticmethod
    def get_next_review_date(interval_days: int) -> datetime:
        """Calculate next review date from interval"""
        return datetime.utcnow() + timedelta(days=interval_days)
```

### New API Endpoints

#### `backend/app/api/study_sessions.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from app.schemas.study_session import *
from app.services.spaced_repetition import SM2Algorithm

router = APIRouter(prefix="/api/v1/study", tags=["study"])

@router.post("/sessions/start")
async def start_study_session(
    request: StartSessionRequest,
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Start a new study session"""
    session = StudySession(
        id=uuid.uuid4(),
        user_id=current_user.id,
        deck_id=request.deck_id,
        started_at=datetime.utcnow(),
        session_type=request.session_type
    )
    await repo.create_study_session(session)
    return session

@router.get("/sessions/{deck_id}/due-cards")
async def get_due_cards(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Get cards due for review"""
    cards = await repo.get_due_cards(deck_id, current_user.id)
    return cards

@router.post("/sessions/{session_id}/review")
async def record_review(
    session_id: uuid.UUID,
    request: RecordReviewRequest,
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Record a card review and update SM-2 parameters"""
    card = await repo.get_card(request.card_id)

    # Calculate new SM-2 values
    new_ease, new_interval, new_reps = SM2Algorithm.calculate_next_interval(
        quality=request.quality,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        repetitions=card.repetitions
    )

    next_review = SM2Algorithm.get_next_review_date(new_interval)

    # Update card
    card.ease_factor = new_ease
    card.interval_days = new_interval
    card.repetitions = new_reps
    card.next_review_date = next_review
    card.is_learning = new_reps == 0
    await repo.update_card(card)

    # Record review
    review = CardReview(
        id=uuid.uuid4(),
        card_id=request.card_id,
        user_id=current_user.id,
        review_date=datetime.utcnow(),
        quality=request.quality,
        ease_factor=new_ease,
        interval_days=new_interval,
        repetitions=new_reps
    )
    await repo.create_card_review(review)

    return {"next_interval_days": new_interval, "next_review_date": next_review}

@router.post("/sessions/{session_id}/end")
async def end_study_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """End a study session"""
    session = await repo.get_study_session(session_id)
    session.ended_at = datetime.utcnow()
    session.total_duration_seconds = int((session.ended_at - session.started_at).total_seconds())
    await repo.update_study_session(session)
    return session
```

## Frontend Implementation

### New Components

#### `opendeck-portal/src/app/pages/study-session/study-session.component.ts`:
```typescript
interface StudyCard {
  id: string;
  front: string;
  back: string;
  isFlipped: boolean;
  nextReviewDate?: Date;
}

@Component({
  selector: 'app-study-session',
  templateUrl: './study-session.component.html',
  styleUrls: ['./study-session.component.scss']
})
export class StudySessionComponent implements OnInit {
  sessionId = signal<string | null>(null);
  cards = signal<StudyCard[]>([]);
  currentCardIndex = signal(0);
  isFlipped = signal(false);
  cardsReviewed = signal(0);
  cardsCorrect = signal(0);

  // Quality ratings for SM-2
  qualityOptions = [
    { label: 'Again', value: 0, severity: 'danger', icon: 'pi-times' },
    { label: 'Hard', value: 3, severity: 'warning', icon: 'pi-exclamation-triangle' },
    { label: 'Good', value: 4, severity: 'info', icon: 'pi-check' },
    { label: 'Easy', value: 5, severity: 'success', icon: 'pi-check-circle' }
  ];

  async startSession(deckId: string) {
    const session = await this.studyService.startSession(deckId);
    this.sessionId.set(session.id);

    const dueCards = await this.studyService.getDueCards(deckId);
    this.cards.set(dueCards);
  }

  flipCard() {
    this.isFlipped.set(!this.isFlipped());
  }

  async rateCard(quality: number) {
    const card = this.cards()[this.currentCardIndex()];

    await this.studyService.recordReview({
      sessionId: this.sessionId()!,
      cardId: card.id,
      quality
    });

    this.cardsReviewed.update(v => v + 1);
    if (quality >= 3) {
      this.cardsCorrect.update(v => v + 1);
    }

    // Move to next card
    if (this.currentCardIndex() < this.cards().length - 1) {
      this.currentCardIndex.update(v => v + 1);
      this.isFlipped.set(false);
    } else {
      await this.endSession();
    }
  }

  async endSession() {
    await this.studyService.endSession(this.sessionId()!);
    // Show summary dialog
  }
}
```

### Study Session Service

#### `opendeck-portal/src/app/services/study.service.ts`:
```typescript
@Injectable({ providedIn: 'root' })
export class StudyService {
  constructor(private http: HttpClient) {}

  startSession(deckId: string, sessionType = 'review') {
    return this.http.post<StudySession>('/api/v1/study/sessions/start', {
      deck_id: deckId,
      session_type: sessionType
    });
  }

  getDueCards(deckId: string) {
    return this.http.get<Card[]>(`/api/v1/study/sessions/${deckId}/due-cards`);
  }

  recordReview(data: { sessionId: string; cardId: string; quality: number }) {
    return this.http.post(`/api/v1/study/sessions/${data.sessionId}/review`, {
      card_id: data.cardId,
      quality: data.quality
    });
  }

  endSession(sessionId: string) {
    return this.http.post(`/api/v1/study/sessions/${sessionId}/end`, {});
  }
}
```

### Study Session Template

#### `opendeck-portal/src/app/pages/study-session/study-session.component.html`:
```html
<div class="study-session-container p-4">
  <!-- Progress Header -->
  <div class="progress-header mb-4">
    <p-progressBar [value]="(cardsReviewed() / cards().length) * 100"></p-progressBar>
    <div class="flex justify-content-between mt-2">
      <span>{{ cardsReviewed() }} / {{ cards().length }} cards</span>
      <span>{{ cardsCorrect() }} correct</span>
    </div>
  </div>

  <!-- Flashcard Display -->
  <div class="flashcard-container" *ngIf="cards().length > 0">
    <p-card class="flashcard" (click)="flipCard()"
            [ngClass]="{'flipped': isFlipped()}">
      <div class="card-content" *ngIf="!isFlipped()">
        <h2>{{ cards()[currentCardIndex()].front }}</h2>
      </div>
      <div class="card-content" *ngIf="isFlipped()">
        <p>{{ cards()[currentCardIndex()].back }}</p>
      </div>
    </p-card>

    <!-- Rating Buttons (shown after flip) -->
    <div class="rating-buttons mt-4" *ngIf="isFlipped()">
      <p-button *ngFor="let option of qualityOptions"
                [label]="option.label"
                [severity]="option.severity"
                [icon]="option.icon"
                (onClick)="rateCard(option.value)"
                class="mr-2">
      </p-button>
    </div>
  </div>

  <!-- Session Complete -->
  <div *ngIf="cardsReviewed() === cards().length" class="text-center">
    <i class="pi pi-check-circle" style="font-size: 4rem; color: var(--green-500)"></i>
    <h2>{{ 'study.sessionComplete' | translate }}</h2>
    <p>{{ 'study.reviewedCards' | translate: {count: cardsReviewed()} }}</p>
    <p>{{ 'study.accuracy' | translate: {percent: (cardsCorrect() / cardsReviewed() * 100).toFixed(0)} }}</p>
  </div>
</div>
```

## Implementation Steps

### Phase 1: Database & Backend (Week 1)
- [ ] Create Alembic migration for new tables
- [ ] Implement `SM2Algorithm` service
- [ ] Create repository methods for reviews and sessions
- [ ] Build API endpoints for study sessions
- [ ] Write unit tests for SM-2 algorithm

### Phase 2: Frontend Core (Week 2)
- [ ] Create `StudySessionComponent` with card flipping
- [ ] Implement quality rating UI
- [ ] Build study service
- [ ] Add keyboard shortcuts (Space to flip, 1-4 for ratings)
- [ ] Create TypeScript models for session data

### Phase 3: Dashboard Integration (Week 3)
- [ ] Add "Study Now" button to deck cards
- [ ] Show due card count badges
- [ ] Display next review dates
- [ ] Add session history view
- [ ] Update dashboard to show study statistics

### Phase 4: Polish (Week 4)
- [ ] Session summary dialog with statistics
- [ ] Animations for card flips
- [ ] Sound effects (optional)
- [ ] Add translations for study session UI
- [ ] End-to-end testing

## Key Features

1. **SM-2 Algorithm**: Proven spaced repetition system
2. **Quality Ratings**: 4-button interface (Again, Hard, Good, Easy)
3. **Session Tracking**: Record all study sessions with timing
4. **Due Card Detection**: Smart identification of cards needing review
5. **Progress Tracking**: Real-time progress bar and accuracy
6. **Keyboard Support**: Space to flip, number keys for ratings

## Success Metrics

- Cards reviewed per session
- Average session duration
- User retention (daily active users)
- Accuracy improvement over time
- Time to mastery per deck

## Technical Considerations

- **Database Performance**: Index on `next_review_date` for efficient due card queries
- **Algorithm Accuracy**: SM-2 is well-tested and proven effective
- **User Experience**: Smooth animations and instant feedback
- **Data Integrity**: Reviews must be persisted even if session ends abruptly
- **Testing**: Comprehensive tests for SM-2 calculations

## Future Enhancements

- Multiple spaced repetition algorithms (Leitner, FSRS)
- Customizable ease factor settings
- "Bury card" feature to skip difficult cards temporarily
- Study goals and daily targets
- Leaderboards and social features
