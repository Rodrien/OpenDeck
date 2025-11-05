# Implementation Plan: Deck Analytics Dashboard

## Overview
Build comprehensive analytics to track study progress, identify weak areas, and motivate users with visual insights.

## Database Schema Changes

### New Table: `deck_statistics`
```sql
CREATE TABLE deck_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id UUID NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_cards INT DEFAULT 0,
    mastered_cards INT DEFAULT 0,  -- ease_factor > 2.5, repetitions >= 3
    learning_cards INT DEFAULT 0,
    difficult_cards INT DEFAULT 0,  -- ease_factor < 2.0
    total_study_time_seconds INT DEFAULT 0,
    total_reviews INT DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    last_studied_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(deck_id, user_id)
);

CREATE INDEX idx_deck_statistics_user ON deck_statistics(user_id);
```

### New Table: `user_statistics`
```sql
CREATE TABLE user_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    total_decks INT DEFAULT 0,
    total_cards_studied INT DEFAULT 0,
    total_study_time_seconds INT DEFAULT 0,
    current_streak_days INT DEFAULT 0,
    longest_streak_days INT DEFAULT 0,
    last_study_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### New Table: `daily_activity`
```sql
CREATE TABLE daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,
    cards_reviewed INT DEFAULT 0,
    study_time_seconds INT DEFAULT 0,
    sessions_completed INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, activity_date)
);

CREATE INDEX idx_daily_activity_user_date ON daily_activity(user_id, activity_date);
```

## Backend Implementation

### New API Endpoints

#### `backend/app/api/analytics.py`:
```python
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
from typing import List, Optional

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

@router.get("/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Get overall dashboard analytics"""
    user_stats = await repo.get_user_statistics(current_user.id)
    recent_activity = await repo.get_daily_activity(
        current_user.id,
        days=30
    )

    return {
        "total_decks": user_stats.total_decks,
        "total_cards_studied": user_stats.total_cards_studied,
        "total_study_time_seconds": user_stats.total_study_time_seconds,
        "current_streak": user_stats.current_streak_days,
        "longest_streak": user_stats.longest_streak_days,
        "recent_activity": recent_activity
    }

@router.get("/decks/{deck_id}")
async def get_deck_analytics(
    deck_id: uuid.UUID,
    period: str = Query("30d", regex="^(7d|30d|90d|all)$"),
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Get analytics for a specific deck"""
    deck_stats = await repo.get_deck_statistics(deck_id, current_user.id)

    # Get review history
    days = {"7d": 7, "30d": 30, "90d": 90, "all": 365}[period]
    reviews = await repo.get_card_reviews_for_deck(
        deck_id,
        current_user.id,
        since=datetime.utcnow() - timedelta(days=days)
    )

    # Calculate accuracy over time
    accuracy_by_day = calculate_accuracy_trend(reviews)

    # Get difficult cards
    difficult_cards = await repo.get_difficult_cards(deck_id, current_user.id, limit=10)

    return {
        "deck_id": deck_id,
        "total_cards": deck_stats.total_cards,
        "mastered_cards": deck_stats.mastered_cards,
        "learning_cards": deck_stats.learning_cards,
        "difficult_cards_count": deck_stats.difficult_cards,
        "mastery_percentage": (deck_stats.mastered_cards / deck_stats.total_cards * 100) if deck_stats.total_cards > 0 else 0,
        "total_study_time_seconds": deck_stats.total_study_time_seconds,
        "total_reviews": deck_stats.total_reviews,
        "average_accuracy": deck_stats.average_accuracy,
        "accuracy_trend": accuracy_by_day,
        "difficult_cards": difficult_cards,
        "last_studied_at": deck_stats.last_studied_at
    }

@router.get("/progress")
async def get_progress_over_time(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Get study progress over time"""
    activity = await repo.get_daily_activity(current_user.id, days=days)

    # Format for charting
    return {
        "dates": [a.activity_date.isoformat() for a in activity],
        "cards_reviewed": [a.cards_reviewed for a in activity],
        "study_time_minutes": [a.study_time_seconds // 60 for a in activity]
    }

@router.get("/heatmap")
async def get_study_heatmap(
    year: int = Query(2025),
    current_user: User = Depends(get_current_user),
    repo: Repository = Depends(get_repository)
):
    """Get GitHub-style contribution heatmap data"""
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)

    activity = await repo.get_daily_activity_range(
        current_user.id,
        start_date,
        end_date
    )

    # Format as [{date: '2025-01-01', count: 15}, ...]
    return [
        {
            "date": a.activity_date.isoformat(),
            "count": a.cards_reviewed
        }
        for a in activity
    ]
```

### Background Statistics Calculator

#### `backend/app/services/statistics_calculator.py`:
```python
class StatisticsCalculator:
    """Calculate and update statistics after each review"""

    @staticmethod
    async def update_deck_statistics(
        deck_id: uuid.UUID,
        user_id: uuid.UUID,
        repo: Repository
    ):
        """Recalculate deck statistics"""
        cards = await repo.get_cards_for_deck(deck_id)
        reviews = await repo.get_card_reviews_for_deck(deck_id, user_id)

        mastered = sum(1 for c in cards if c.ease_factor >= 2.5 and c.repetitions >= 3)
        learning = sum(1 for c in cards if c.is_learning)
        difficult = sum(1 for c in cards if c.ease_factor < 2.0)

        accuracy = calculate_accuracy(reviews)
        total_time = calculate_total_study_time(reviews)

        await repo.upsert_deck_statistics(
            deck_id=deck_id,
            user_id=user_id,
            total_cards=len(cards),
            mastered_cards=mastered,
            learning_cards=learning,
            difficult_cards=difficult,
            total_study_time_seconds=total_time,
            total_reviews=len(reviews),
            average_accuracy=accuracy,
            last_studied_at=datetime.utcnow()
        )

    @staticmethod
    async def update_user_statistics(user_id: uuid.UUID, repo: Repository):
        """Update overall user statistics"""
        decks = await repo.get_user_decks(user_id)
        all_reviews = await repo.get_user_reviews(user_id)

        # Calculate streak
        streak = calculate_study_streak(all_reviews)

        await repo.upsert_user_statistics(
            user_id=user_id,
            total_decks=len(decks),
            total_cards_studied=len(set(r.card_id for r in all_reviews)),
            total_study_time_seconds=sum(r.duration for r in all_reviews),
            current_streak_days=streak['current'],
            longest_streak_days=streak['longest'],
            last_study_date=datetime.utcnow().date()
        )

    @staticmethod
    async def update_daily_activity(
        user_id: uuid.UUID,
        cards_reviewed: int,
        study_time_seconds: int,
        repo: Repository
    ):
        """Update today's activity"""
        today = datetime.utcnow().date()
        await repo.upsert_daily_activity(
            user_id=user_id,
            activity_date=today,
            cards_reviewed=cards_reviewed,
            study_time_seconds=study_time_seconds,
            sessions_completed=1
        )

def calculate_accuracy(reviews: List[CardReview]) -> float:
    """Calculate overall accuracy percentage"""
    if not reviews:
        return 0.0
    correct = sum(1 for r in reviews if r.quality >= 3)
    return (correct / len(reviews)) * 100

def calculate_study_streak(reviews: List[CardReview]) -> dict:
    """Calculate current and longest study streak"""
    if not reviews:
        return {"current": 0, "longest": 0}

    # Group by date
    dates = sorted(set(r.review_date.date() for r in reviews))

    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    today = datetime.utcnow().date()

    for i, date in enumerate(dates):
        if i == 0 or (date - dates[i-1]).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)

        # Current streak only if includes today or yesterday
        if date == today or date == today - timedelta(days=1):
            current_streak = temp_streak

    return {"current": current_streak, "longest": longest_streak}

def calculate_accuracy_trend(reviews: List[CardReview]) -> List[dict]:
    """Calculate accuracy trend over time (by day)"""
    from collections import defaultdict

    by_day = defaultdict(lambda: {"correct": 0, "total": 0})

    for review in reviews:
        day = review.review_date.date().isoformat()
        by_day[day]["total"] += 1
        if review.quality >= 3:
            by_day[day]["correct"] += 1

    return [
        {
            "date": day,
            "accuracy": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        }
        for day, stats in sorted(by_day.items())
    ]
```

## Frontend Implementation

### Analytics Dashboard Component

#### `opendeck-portal/src/app/pages/analytics/analytics-dashboard.component.ts`:
```typescript
import { Component, OnInit, signal } from '@angular/core';
import { AnalyticsService } from '../../services/analytics.service';

@Component({
  selector: 'app-analytics-dashboard',
  templateUrl: './analytics-dashboard.component.html',
  styleUrls: ['./analytics-dashboard.component.scss']
})
export class AnalyticsDashboardComponent implements OnInit {
  // Overall stats
  totalDecks = signal(0);
  totalCardsStudied = signal(0);
  studyTimeHours = signal(0);
  currentStreak = signal(0);

  // Chart data
  studyProgressData = signal<any>(null);
  accuracyTrendData = signal<any>(null);
  deckComparisonData = signal<any>(null);

  // Heatmap
  heatmapData = signal<any[]>([]);

  // Chart options
  chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: 'var(--text-color)'
        }
      }
    },
    scales: {
      x: {
        ticks: {
          color: 'var(--text-color-secondary)'
        },
        grid: {
          color: 'var(--surface-border)'
        }
      },
      y: {
        ticks: {
          color: 'var(--text-color-secondary)'
        },
        grid: {
          color: 'var(--surface-border)'
        }
      }
    }
  };

  constructor(private analyticsService: AnalyticsService) {}

  ngOnInit() {
    this.loadDashboardData();
    this.loadStudyProgress();
    this.loadHeatmap();
  }

  async loadDashboardData() {
    const data = await this.analyticsService.getDashboardAnalytics();
    this.totalDecks.set(data.total_decks);
    this.totalCardsStudied.set(data.total_cards_studied);
    this.studyTimeHours.set(Math.round(data.total_study_time_seconds / 3600));
    this.currentStreak.set(data.current_streak);
  }

  async loadStudyProgress() {
    const data = await this.analyticsService.getProgressOverTime(30);

    this.studyProgressData.set({
      labels: data.dates,
      datasets: [
        {
          label: 'Cards Reviewed',
          data: data.cards_reviewed,
          borderColor: '#42A5F5',
          backgroundColor: 'rgba(66, 165, 245, 0.2)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'Study Time (min)',
          data: data.study_time_minutes,
          borderColor: '#66BB6A',
          backgroundColor: 'rgba(102, 187, 106, 0.2)',
          tension: 0.4,
          fill: true
        }
      ]
    });
  }

  async loadHeatmap() {
    const data = await this.analyticsService.getStudyHeatmap(2025);
    this.heatmapData.set(data);
  }
}
```

### Analytics Service

#### `opendeck-portal/src/app/services/analytics.service.ts`:
```typescript
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  constructor(private http: HttpClient) {}

  getDashboardAnalytics() {
    return firstValueFrom(
      this.http.get<any>('/api/v1/analytics/dashboard')
    );
  }

  getDeckAnalytics(deckId: string, period: '7d' | '30d' | '90d' | 'all' = '30d') {
    return firstValueFrom(
      this.http.get<any>(`/api/v1/analytics/decks/${deckId}`, {
        params: { period }
      })
    );
  }

  getProgressOverTime(days: number = 30) {
    return firstValueFrom(
      this.http.get<any>('/api/v1/analytics/progress', {
        params: { days: days.toString() }
      })
    );
  }

  getStudyHeatmap(year: number) {
    return firstValueFrom(
      this.http.get<any>('/api/v1/analytics/heatmap', {
        params: { year: year.toString() }
      })
    );
  }
}
```

### Analytics Template

#### `opendeck-portal/src/app/pages/analytics/analytics-dashboard.component.html`:
```html
<div class="analytics-dashboard p-4">
  <h1>{{ 'analytics.title' | translate }}</h1>

  <!-- Stats Cards -->
  <div class="grid mt-4">
    <div class="col-12 md:col-3">
      <p-card>
        <div class="stat-card">
          <i class="pi pi-book" style="font-size: 2rem; color: var(--primary-color)"></i>
          <h3>{{ totalDecks() }}</h3>
          <p>{{ 'analytics.totalDecks' | translate }}</p>
        </div>
      </p-card>
    </div>

    <div class="col-12 md:col-3">
      <p-card>
        <div class="stat-card">
          <i class="pi pi-check-circle" style="font-size: 2rem; color: var(--green-500)"></i>
          <h3>{{ totalCardsStudied() }}</h3>
          <p>{{ 'analytics.cardsStudied' | translate }}</p>
        </div>
      </p-card>
    </div>

    <div class="col-12 md:col-3">
      <p-card>
        <div class="stat-card">
          <i class="pi pi-clock" style="font-size: 2rem; color: var(--blue-500)"></i>
          <h3>{{ studyTimeHours() }}h</h3>
          <p>{{ 'analytics.totalStudyTime' | translate }}</p>
        </div>
      </p-card>
    </div>

    <div class="col-12 md:col-3">
      <p-card>
        <div class="stat-card">
          <i class="pi pi-bolt" style="font-size: 2rem; color: var(--orange-500)"></i>
          <h3>{{ currentStreak() }} 🔥</h3>
          <p>{{ 'analytics.dayStreak' | translate }}</p>
        </div>
      </p-card>
    </div>
  </div>

  <!-- Charts -->
  <div class="grid mt-4">
    <div class="col-12 lg:col-8">
      <p-card>
        <ng-template pTemplate="header">
          <h3 class="p-3">{{ 'analytics.studyProgress' | translate }}</h3>
        </ng-template>
        <p-chart type="line"
                 [data]="studyProgressData()"
                 [options]="chartOptions"
                 height="300px">
        </p-chart>
      </p-card>
    </div>

    <div class="col-12 lg:col-4">
      <p-card>
        <ng-template pTemplate="header">
          <h3 class="p-3">{{ 'analytics.deckMastery' | translate }}</h3>
        </ng-template>
        <p-chart type="doughnut" [data]="deckComparisonData()"></p-chart>
      </p-card>
    </div>
  </div>

  <!-- Study Heatmap (GitHub-style) -->
  <div class="mt-4">
    <p-card>
      <ng-template pTemplate="header">
        <h3 class="p-3">{{ 'analytics.studyActivity' | translate }}</h3>
      </ng-template>
      <app-study-heatmap [data]="heatmapData()"></app-study-heatmap>
    </p-card>
  </div>
</div>
```

### Study Heatmap Component

#### `opendeck-portal/src/app/components/study-heatmap/study-heatmap.component.ts`:
```typescript
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-study-heatmap',
  template: `
    <div class="heatmap-container">
      <svg [attr.width]="width" [attr.height]="height">
        <g *ngFor="let week of weeks; let weekIdx = index">
          <rect *ngFor="let day of week; let dayIdx = index"
                [attr.x]="weekIdx * (cellSize + gap)"
                [attr.y]="dayIdx * (cellSize + gap)"
                [attr.width]="cellSize"
                [attr.height]="cellSize"
                [attr.fill]="getColor(day.count)"
                [attr.data-date]="day.date"
                [attr.data-count]="day.count"
                rx="2"
                class="heatmap-cell">
          </rect>
        </g>
      </svg>
    </div>
  `,
  styles: [`
    .heatmap-cell {
      cursor: pointer;
      transition: all 0.2s;
    }
    .heatmap-cell:hover {
      stroke: var(--primary-color);
      stroke-width: 2;
    }
  `]
})
export class StudyHeatmapComponent {
  @Input() data: any[] = [];

  cellSize = 12;
  gap = 3;
  weeks: any[][] = [];
  width = 800;
  height = 120;

  ngOnChanges() {
    this.buildHeatmap();
  }

  buildHeatmap() {
    // Group data by week
    // Implementation details...
  }

  getColor(count: number): string {
    if (count === 0) return 'var(--surface-100)';
    if (count < 5) return 'var(--green-200)';
    if (count < 10) return 'var(--green-400)';
    if (count < 20) return 'var(--green-600)';
    return 'var(--green-800)';
  }
}
```

## Implementation Steps

### Phase 1: Database & Backend (Week 1)
- [ ] Create statistics tables migration
- [ ] Build analytics repository methods
- [ ] Implement StatisticsCalculator service
- [ ] Create analytics API endpoints
- [ ] Add helper functions for streak and accuracy calculations

### Phase 2: Data Collection (Week 2)
- [ ] Hook statistics updates into review endpoints
- [ ] Implement streak calculation logic
- [ ] Create background job for daily statistics
- [ ] Add triggers to update stats on card review
- [ ] Test data integrity and accuracy

### Phase 3: Frontend Charts (Week 3)
- [ ] Install PrimeNG Chart (`primeng/chart`)
- [ ] Build analytics dashboard component
- [ ] Create line charts for progress
- [ ] Build doughnut chart for deck mastery
- [ ] Add date range filters

### Phase 4: Advanced Visualizations (Week 4)
- [ ] GitHub-style heatmap component
- [ ] Difficult cards list view
- [ ] Export analytics to PDF (optional)
- [ ] Add tooltips and interactive elements
- [ ] Add translations for analytics UI

## Key Features

1. **Dashboard Overview**: High-level stats at a glance
2. **Progress Charts**: Visual study progress over time
3. **Study Heatmap**: GitHub-style activity visualization
4. **Deck Analytics**: Detailed per-deck statistics
5. **Streak Tracking**: Current and longest study streaks
6. **Difficult Cards**: Identify problem cards needing focus
7. **Mastery Percentage**: Track learning progress per deck

## Success Metrics

- User engagement with analytics page
- Correlation between viewing analytics and study frequency
- Streak maintenance rate
- Time spent on analytics dashboard

## Technical Considerations

- **Performance**: Use database indexes for fast queries
- **Caching**: Cache statistics that don't need real-time updates
- **Chart Library**: PrimeNG Chart.js for consistent theming
- **Responsive Design**: Mobile-friendly charts and layouts
- **Real-time Updates**: Update stats immediately after study sessions

## Future Enhancements

- Compare with other users (anonymized)
- Weekly/monthly email reports
- Predicted exam readiness scores
- Study goal setting and tracking
- AI-powered study recommendations
