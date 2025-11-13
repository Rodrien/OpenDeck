# Card Report Functionality Plan

## Overview
Add functionality for users to report flashcards that have incorrect, misleading, or unhelpful information. Users will provide a detailed reason for their report, which can be reviewed later by admins or the deck owner.

## Backend Changes

### 1. Database Schema (Alembic Migration)
Create a new `card_reports` table:

```sql
CREATE TABLE card_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT card_reports_status_check CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed'))
);

CREATE INDEX idx_card_reports_card_id ON card_reports(card_id);
CREATE INDEX idx_card_reports_user_id ON card_reports(user_id);
CREATE INDEX idx_card_reports_status ON card_reports(status);
```

**Migration command:**
```bash
cd backend
alembic revision --autogenerate -m "add card reports table"
```

### 2. Core Layer (`backend/app/core/`)

**Add to `models.py`:**
```python
from enum import Enum
from datetime import datetime
from uuid import UUID

class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

@dataclass
class CardReport:
    id: UUID
    card_id: UUID
    user_id: UUID
    reason: str
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
```

**Add to `interfaces.py`:**
```python
class ICardReportRepository(ABC):
    @abstractmethod
    def create_report(self, card_id: UUID, user_id: UUID, reason: str) -> CardReport:
        pass

    @abstractmethod
    def get_report_by_id(self, report_id: UUID) -> Optional[CardReport]:
        pass

    @abstractmethod
    def get_reports_by_card_id(self, card_id: UUID) -> List[CardReport]:
        pass

    @abstractmethod
    def get_reports_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[CardReport]:
        pass

    @abstractmethod
    def update_report_status(self, report_id: UUID, status: ReportStatus, reviewed_by: Optional[UUID] = None) -> CardReport:
        pass
```

### 3. Database Layer (`backend/app/db/`)

**Add to `models.py`:**
```python
class CardReportModel(Base):
    __tablename__ = "card_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    card_id = Column(UUID(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, server_default="pending")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    card = relationship("CardModel", back_populates="reports")
    reporter = relationship("UserModel", foreign_keys=[user_id])
    reviewer = relationship("UserModel", foreign_keys=[reviewed_by])
```

**Update `CardModel` in `models.py`:**
```python
# Add to CardModel class
reports = relationship("CardReportModel", back_populates="card", cascade="all, delete-orphan")
```

**Add to `postgres_repo.py`:**
```python
class CardReportRepository(ICardReportRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, card_id: UUID, user_id: UUID, reason: str) -> CardReport:
        db_report = CardReportModel(
            card_id=card_id,
            user_id=user_id,
            reason=reason,
            status=ReportStatus.PENDING
        )
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return self._to_domain(db_report)

    def get_report_by_id(self, report_id: UUID) -> Optional[CardReport]:
        db_report = self.db.query(CardReportModel).filter(CardReportModel.id == report_id).first()
        return self._to_domain(db_report) if db_report else None

    def get_reports_by_card_id(self, card_id: UUID) -> List[CardReport]:
        db_reports = self.db.query(CardReportModel).filter(CardReportModel.card_id == card_id).all()
        return [self._to_domain(r) for r in db_reports]

    def get_reports_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[CardReport]:
        db_reports = self.db.query(CardReportModel)\
            .filter(CardReportModel.user_id == user_id)\
            .order_by(CardReportModel.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        return [self._to_domain(r) for r in db_reports]

    def update_report_status(self, report_id: UUID, status: ReportStatus, reviewed_by: Optional[UUID] = None) -> CardReport:
        db_report = self.db.query(CardReportModel).filter(CardReportModel.id == report_id).first()
        if not db_report:
            raise ValueError(f"Report {report_id} not found")

        db_report.status = status
        if reviewed_by:
            db_report.reviewed_by = reviewed_by
            db_report.reviewed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_report)
        return self._to_domain(db_report)

    def _to_domain(self, db_report: CardReportModel) -> CardReport:
        return CardReport(
            id=db_report.id,
            card_id=db_report.card_id,
            user_id=db_report.user_id,
            reason=db_report.reason,
            status=ReportStatus(db_report.status),
            created_at=db_report.created_at,
            updated_at=db_report.updated_at,
            reviewed_by=db_report.reviewed_by,
            reviewed_at=db_report.reviewed_at
        )
```

### 4. Schemas (`backend/app/schemas/`)

**Create `card_report.py`:**
```python
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum

class ReportStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class CardReportCreate(BaseModel):
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for reporting the card")

class CardReportResponse(BaseModel):
    id: UUID
    card_id: UUID
    user_id: UUID
    reason: str
    status: ReportStatus
    created_at: datetime
    updated_at: datetime
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CardReportStatusUpdate(BaseModel):
    status: ReportStatus
```

### 5. API Routes (`backend/app/api/`)

**Create `reports.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.interfaces import ICardReportRepository
from app.db.postgres_repo import CardReportRepository
from app.schemas.card_report import CardReportCreate, CardReportResponse, CardReportStatusUpdate
from app.api.auth import get_current_user
from app.core.models import User
from app.db.database import get_db

router = APIRouter(prefix="/api/v1", tags=["reports"])

def get_report_repo(db: Session = Depends(get_db)) -> ICardReportRepository:
    return CardReportRepository(db)

@router.post("/cards/{card_id}/report", response_model=CardReportResponse, status_code=status.HTTP_201_CREATED)
def report_card(
    card_id: UUID,
    report_data: CardReportCreate,
    current_user: User = Depends(get_current_user),
    report_repo: ICardReportRepository = Depends(get_report_repo)
):
    """Report a card for review"""
    try:
        report = report_repo.create_report(
            card_id=card_id,
            user_id=current_user.id,
            reason=report_data.reason
        )
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/reports/card/{card_id}", response_model=List[CardReportResponse])
def get_card_reports(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    report_repo: ICardReportRepository = Depends(get_report_repo)
):
    """Get all reports for a specific card"""
    reports = report_repo.get_reports_by_card_id(card_id)
    return reports

@router.get("/reports/my-reports", response_model=List[CardReportResponse])
def get_my_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    report_repo: ICardReportRepository = Depends(get_report_repo)
):
    """Get all reports created by the current user"""
    reports = report_repo.get_reports_by_user_id(current_user.id, skip, limit)
    return reports

@router.put("/reports/{report_id}/status", response_model=CardReportResponse)
def update_report_status(
    report_id: UUID,
    status_update: CardReportStatusUpdate,
    current_user: User = Depends(get_current_user),
    report_repo: ICardReportRepository = Depends(get_report_repo)
):
    """Update the status of a report (future: admin only)"""
    try:
        report = report_repo.update_report_status(
            report_id=report_id,
            status=status_update.status,
            reviewed_by=current_user.id
        )
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
```

**Update `backend/app/main.py`:**
```python
from app.api import reports

app.include_router(reports.router)
```

---

## Frontend Changes

### 6. TypeScript Models (`opendeck-portal/src/app/models/`)

**Create `card-report.model.ts`:**
```typescript
export enum ReportStatus {
  PENDING = 'pending',
  REVIEWED = 'reviewed',
  RESOLVED = 'resolved',
  DISMISSED = 'dismissed'
}

export interface CardReport {
  id: string;
  cardId: string;
  userId: string;
  reason: string;
  status: ReportStatus;
  createdAt: Date;
  updatedAt: Date;
  reviewedBy?: string;
  reviewedAt?: Date;
}

export interface CardReportCreate {
  reason: string;
}
```

### 7. API Service (`opendeck-portal/src/app/services/`)

**Add to `card.service.ts`:**
```typescript
import { CardReport, CardReportCreate } from '../models/card-report.model';

// Add these methods to CardService class:

reportCard(cardId: string, reportData: CardReportCreate): Observable<CardReport> {
  return this.http.post<CardReport>(
    `${this.apiUrl}/cards/${cardId}/report`,
    reportData
  );
}

getCardReports(cardId: string): Observable<CardReport[]> {
  return this.http.get<CardReport[]>(
    `${this.apiUrl}/reports/card/${cardId}`
  );
}

getMyReports(): Observable<CardReport[]> {
  return this.http.get<CardReport[]>(
    `${this.apiUrl}/reports/my-reports`
  );
}
```

### 8. Report Dialog Component (`opendeck-portal/src/app/components/`)

**Create `report-card-dialog/` component:**

```bash
ng generate component components/report-card-dialog
```

**report-card-dialog.component.ts:**
```typescript
import { Component, EventEmitter, Input, Output, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DialogModule } from 'primeng/dialog';
import { ButtonModule } from 'primeng/button';
import { InputTextareaModule } from 'primeng/inputtextarea';
import { MessageModule } from 'primeng/message';
import { TranslateModule } from '@ngx-translate/core';
import { CardService } from '../../services/card.service';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-report-card-dialog',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    DialogModule,
    ButtonModule,
    InputTextareaModule,
    MessageModule,
    TranslateModule
  ],
  templateUrl: './report-card-dialog.component.html',
  styleUrls: ['./report-card-dialog.component.scss']
})
export class ReportCardDialogComponent {
  @Input() visible = false;
  @Input() cardId = '';
  @Output() visibleChange = new EventEmitter<boolean>();
  @Output() reportSubmitted = new EventEmitter<void>();

  reason = signal('');
  isSubmitting = signal(false);
  readonly MIN_REASON_LENGTH = 10;

  constructor(
    private cardService: CardService,
    private messageService: MessageService
  ) {}

  get isReasonValid(): boolean {
    return this.reason().trim().length >= this.MIN_REASON_LENGTH;
  }

  get remainingChars(): number {
    return this.MIN_REASON_LENGTH - this.reason().trim().length;
  }

  onHide(): void {
    this.reason.set('');
    this.visibleChange.emit(false);
  }

  onSubmit(): void {
    if (!this.isReasonValid || this.isSubmitting()) {
      return;
    }

    this.isSubmitting.set(true);

    this.cardService.reportCard(this.cardId, { reason: this.reason().trim() })
      .subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Success',
            detail: 'Card reported successfully'
          });
          this.reportSubmitted.emit();
          this.onHide();
          this.isSubmitting.set(false);
        },
        error: (error) => {
          console.error('Error reporting card:', error);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to report card. Please try again.'
          });
          this.isSubmitting.set(false);
        }
      });
  }
}
```

**report-card-dialog.component.html:**
```html
<p-dialog
  [(visible)]="visible"
  [modal]="true"
  [closable]="true"
  [draggable]="false"
  [resizable]="false"
  [style]="{ width: '500px' }"
  (onHide)="onHide()"
>
  <ng-template pTemplate="header">
    <h3 class="text-xl font-semibold">{{ 'report.title' | translate }}</h3>
  </ng-template>

  <div class="flex flex-col gap-4">
    <p class="text-surface-600 dark:text-surface-400">
      {{ 'report.description' | translate }}
    </p>

    <div class="flex flex-col gap-2">
      <label for="reason" class="font-medium">
        {{ 'report.reasonLabel' | translate }}
      </label>
      <textarea
        id="reason"
        pInputTextarea
        [(ngModel)]="reason"
        [rows]="5"
        [placeholder]="'report.reasonPlaceholder' | translate"
        [disabled]="isSubmitting()"
        class="w-full"
      ></textarea>

      <div class="text-sm" [class.text-red-500]="!isReasonValid && reason().length > 0">
        @if (!isReasonValid && reason().length > 0) {
          {{ 'report.minimumChars' | translate: { count: remainingChars } }}
        } @else if (isReasonValid) {
          <span class="text-green-600 dark:text-green-400">
            {{ 'report.reasonValid' | translate }}
          </span>
        }
      </div>
    </div>

    @if (!isReasonValid && reason().length > 0) {
      <p-message severity="warn" [text]="'report.validationMessage' | translate"></p-message>
    }
  </div>

  <ng-template pTemplate="footer">
    <div class="flex justify-end gap-2">
      <p-button
        [label]="'common.cancel' | translate"
        severity="secondary"
        [outlined]="true"
        (onClick)="onHide()"
        [disabled]="isSubmitting()"
      />
      <p-button
        [label]="'report.submit' | translate"
        severity="danger"
        (onClick)="onSubmit()"
        [disabled]="!isReasonValid || isSubmitting()"
        [loading]="isSubmitting()"
      />
    </div>
  </ng-template>
</p-dialog>
```

**report-card-dialog.component.scss:**
```scss
:host ::ng-deep {
  .p-dialog {
    .p-dialog-header {
      padding: 1.5rem;
      border-bottom: 1px solid var(--surface-border);
    }

    .p-dialog-content {
      padding: 1.5rem;
    }

    .p-dialog-footer {
      padding: 1.5rem;
      border-top: 1px solid var(--surface-border);
    }
  }

  textarea {
    resize: vertical;
    min-height: 120px;
  }
}
```

### 9. Integration into Flashcard Viewer

**Update `flashcard-viewer.component.html`:**
```html
<!-- Add report button to card actions area -->
<div class="card-actions flex justify-between mt-4">
  <!-- Existing navigation buttons -->

  <p-button
    icon="pi pi-flag"
    [label]="'report.reportCard' | translate"
    severity="warning"
    [outlined]="true"
    size="small"
    (onClick)="openReportDialog()"
  />
</div>

<!-- Add report dialog -->
<app-report-card-dialog
  [(visible)]="showReportDialog"
  [cardId]="currentCard()?.id || ''"
  (reportSubmitted)="onCardReported()"
/>
```

**Update `flashcard-viewer.component.ts`:**
```typescript
import { ReportCardDialogComponent } from '../report-card-dialog/report-card-dialog.component';

// Add to imports array
imports: [
  // ... existing imports
  ReportCardDialogComponent
]

// Add properties
showReportDialog = signal(false);

// Add methods
openReportDialog(): void {
  this.showReportDialog.set(true);
}

onCardReported(): void {
  // Optional: Show feedback or refresh data
  console.log('Card reported successfully');
}
```

### 10. Integration into Study Session

**Update `study-session.component.html`:**
```html
<!-- Add report button near quality buttons -->
<div class="study-actions mt-6">
  <!-- Existing quality buttons -->

  <div class="flex justify-center mt-4">
    <p-button
      icon="pi pi-flag"
      [label]="'report.reportCard' | translate"
      severity="warning"
      [text]="true"
      size="small"
      (onClick)="openReportDialog()"
    />
  </div>
</div>

<!-- Add report dialog -->
<app-report-card-dialog
  [(visible)]="showReportDialog"
  [cardId]="currentCard()?.id || ''"
  (reportSubmitted)="onCardReported()"
/>
```

**Update `study-session.component.ts`:**
```typescript
import { ReportCardDialogComponent } from '../../components/report-card-dialog/report-card-dialog.component';

// Add to imports array
imports: [
  // ... existing imports
  ReportCardDialogComponent
]

// Add properties
showReportDialog = signal(false);

// Add methods
openReportDialog(): void {
  this.showReportDialog.set(true);
}

onCardReported(): void {
  // Optional: Track reported cards in session
  console.log('Card reported during study session');
}
```

### 11. Translations

**Update `opendeck-portal/src/assets/i18n/en.json`:**
```json
{
  "report": {
    "title": "Report Card",
    "description": "Help us improve by reporting cards with incorrect, misleading, or unhelpful information.",
    "reasonLabel": "Why are you reporting this card?",
    "reasonPlaceholder": "Please describe the issue with this card (e.g., incorrect information, unclear question, typo)...",
    "minimumChars": "Please provide at least {{count}} more characters",
    "reasonValid": "Your reason looks good",
    "validationMessage": "Please provide a detailed reason for reporting this card",
    "submit": "Submit Report",
    "reportCard": "Report Card",
    "successMessage": "Card reported successfully",
    "errorMessage": "Failed to report card. Please try again."
  }
}
```

**Update `opendeck-portal/src/assets/i18n/es.json`:**
```json
{
  "report": {
    "title": "Reportar Tarjeta",
    "description": "Ayúdanos a mejorar reportando tarjetas con información incorrecta, engañosa o poco útil.",
    "reasonLabel": "¿Por qué estás reportando esta tarjeta?",
    "reasonPlaceholder": "Por favor describe el problema con esta tarjeta (ej: información incorrecta, pregunta poco clara, error tipográfico)...",
    "minimumChars": "Por favor proporciona al menos {{count}} caracteres más",
    "reasonValid": "Tu razón se ve bien",
    "validationMessage": "Por favor proporciona una razón detallada para reportar esta tarjeta",
    "submit": "Enviar Reporte",
    "reportCard": "Reportar Tarjeta",
    "successMessage": "Tarjeta reportada exitosamente",
    "errorMessage": "Error al reportar la tarjeta. Por favor intenta de nuevo."
  }
}
```

---

## Implementation Steps

### Phase 1: Backend Foundation
1. ✅ Create Alembic migration for `card_reports` table
2. ✅ Add domain models and interfaces to core layer
3. ✅ Implement SQLAlchemy model and repository
4. ✅ Create Pydantic schemas
5. ✅ Add API endpoints and register router
6. ✅ Test API endpoints manually with curl/Postman

### Phase 2: Frontend UI
7. ✅ Create TypeScript models
8. ✅ Add service methods to CardService
9. ✅ Generate and implement report dialog component
10. ✅ Add translations (English & Spanish)
11. ✅ Test dialog component standalone

### Phase 3: Integration
12. ✅ Integrate report button into flashcard viewer
13. ✅ Integrate report button into study session
14. ✅ Add Toast/Message service for feedback
15. ✅ Test full flow end-to-end

### Phase 4: Polish & Testing
16. ✅ Verify dark mode styling
17. ✅ Test form validation
18. ✅ Test error handling
19. ✅ Write backend unit tests
20. ✅ Write frontend component tests

---

## Future Enhancements

### Admin Dashboard (Phase 2+)
- View all pending reports
- Filter reports by status, card, user
- Resolve/dismiss reports
- Edit cards directly from report view
- Batch actions for reports

### Notifications
- Notify deck owners of reports on their cards
- Notify users when their reports are reviewed

### Analytics
- Track most reported cards
- Identify problematic content patterns
- Generate quality metrics for decks

---

## Testing Checklist

### Backend Tests
- [ ] Test creating a report with valid data
- [ ] Test validation (minimum reason length)
- [ ] Test getting reports by card ID
- [ ] Test getting user's reports
- [ ] Test updating report status
- [ ] Test cascade delete (card deleted → reports deleted)
- [ ] Test authentication requirements

### Frontend Tests
- [ ] Test dialog opens/closes correctly
- [ ] Test form validation (min 10 chars)
- [ ] Test character counter
- [ ] Test submit button disabled state
- [ ] Test loading state during submission
- [ ] Test success message display
- [ ] Test error handling
- [ ] Test dark mode styling
- [ ] Test translations (EN/ES)

### Integration Tests
- [ ] Test report from flashcard viewer
- [ ] Test report from study session
- [ ] Test report appears in backend
- [ ] Test multiple reports on same card
- [ ] Test report by different users
