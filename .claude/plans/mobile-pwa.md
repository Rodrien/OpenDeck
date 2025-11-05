# Implementation Plan: Mobile Progressive Web App (PWA)

## Overview
Transform the Angular app into a PWA with offline support, installability, and mobile-optimized UI for studying on the go.

## PWA Configuration

### Install Dependencies
```bash
cd opendeck-portal
ng add @angular/pwa
npm install workbox-webpack-plugin --save-dev
npm install idb --save  # IndexedDB wrapper for offline storage
```

### Service Worker Configuration

#### `opendeck-portal/ngsw-config.json`:
```json
{
  "$schema": "./node_modules/@angular/service-worker/config/schema.json",
  "index": "/index.html",
  "assetGroups": [
    {
      "name": "app",
      "installMode": "prefetch",
      "resources": {
        "files": [
          "/favicon.ico",
          "/index.html",
          "/manifest.webmanifest",
          "/*.css",
          "/*.js"
        ]
      }
    },
    {
      "name": "assets",
      "installMode": "lazy",
      "updateMode": "prefetch",
      "resources": {
        "files": [
          "/assets/**",
          "/*.(svg|cur|jpg|jpeg|png|apng|webp|avif|gif|otf|ttf|woff|woff2)"
        ]
      }
    }
  ],
  "dataGroups": [
    {
      "name": "api-cache",
      "urls": [
        "/api/v1/decks",
        "/api/v1/cards/*",
        "/api/v1/topics"
      ],
      "cacheConfig": {
        "strategy": "freshness",
        "maxSize": 100,
        "maxAge": "1h",
        "timeout": "5s"
      }
    },
    {
      "name": "offline-study",
      "urls": [
        "/api/v1/study/**"
      ],
      "cacheConfig": {
        "strategy": "performance",
        "maxSize": 50,
        "maxAge": "7d"
      }
    }
  ]
}
```

### Web App Manifest

#### `opendeck-portal/src/manifest.webmanifest`:
```json
{
  "name": "OpenDeck - AI Flashcards",
  "short_name": "OpenDeck",
  "theme_color": "#1976d2",
  "background_color": "#fafafa",
  "display": "standalone",
  "scope": "/",
  "start_url": "/",
  "orientation": "portrait",
  "icons": [
    {
      "src": "assets/icons/icon-72x72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-96x96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-128x128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-144x144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-152x152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-192x192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-384x384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "maskable any"
    },
    {
      "src": "assets/icons/icon-512x512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable any"
    }
  ],
  "shortcuts": [
    {
      "name": "Start Studying",
      "short_name": "Study",
      "description": "Jump into a study session",
      "url": "/study",
      "icons": [{ "src": "assets/icons/study-96x96.png", "sizes": "96x96" }]
    },
    {
      "name": "Browse Decks",
      "short_name": "Decks",
      "url": "/decks",
      "icons": [{ "src": "assets/icons/deck-96x96.png", "sizes": "96x96" }]
    }
  ],
  "categories": ["education", "productivity"],
  "description": "AI-powered flashcard generation for university students",
  "screenshots": [
    {
      "src": "assets/screenshots/mobile-1.png",
      "sizes": "540x720",
      "type": "image/png"
    },
    {
      "src": "assets/screenshots/desktop-1.png",
      "sizes": "1280x720",
      "type": "image/png"
    }
  ]
}
```

## Offline Functionality

### Offline Service

#### `opendeck-portal/src/app/services/offline.service.ts`:
```typescript
import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

interface OfflineQueue {
  id: string;
  endpoint: string;
  method: string;
  data: any;
  timestamp: number;
}

@Injectable({ providedIn: 'root' })
export class OfflineService {
  private isOnline$ = new BehaviorSubject<boolean>(navigator.onLine);
  private offlineQueue: OfflineQueue[] = [];

  constructor() {
    window.addEventListener('online', () => this.handleOnline());
    window.addEventListener('offline', () => this.handleOffline());

    // Load queue from localStorage
    this.loadQueue();
  }

  get online$() {
    return this.isOnline$.asObservable();
  }

  get isOnline() {
    return this.isOnline$.value;
  }

  queueRequest(endpoint: string, method: string, data: any) {
    const request: OfflineQueue = {
      id: crypto.randomUUID(),
      endpoint,
      method,
      data,
      timestamp: Date.now()
    };

    this.offlineQueue.push(request);
    this.saveQueue();
  }

  private handleOnline() {
    console.log('Back online - syncing queued requests');
    this.isOnline$.next(true);
    this.syncQueue();
  }

  private handleOffline() {
    console.log('Offline mode - requests will be queued');
    this.isOnline$.next(false);
  }

  private async syncQueue() {
    if (!this.isOnline || this.offlineQueue.length === 0) return;

    const queue = [...this.offlineQueue];
    this.offlineQueue = [];

    for (const request of queue) {
      try {
        const token = localStorage.getItem('access_token');
        await fetch(request.endpoint, {
          method: request.method,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify(request.data)
        });
      } catch (error) {
        console.error('Failed to sync request:', error);
        // Re-queue failed requests
        this.offlineQueue.push(request);
      }
    }

    this.saveQueue();
  }

  private saveQueue() {
    localStorage.setItem('offline-queue', JSON.stringify(this.offlineQueue));
  }

  private loadQueue() {
    const saved = localStorage.getItem('offline-queue');
    if (saved) {
      this.offlineQueue = JSON.parse(saved);
    }
  }
}
```

### Offline Study Storage

#### `opendeck-portal/src/app/services/offline-study.service.ts`:
```typescript
import { Injectable } from '@angular/core';
import { openDB, DBSchema, IDBPDatabase } from 'idb';

interface StudyDB extends DBSchema {
  decks: {
    key: string;
    value: {
      id: string;
      name: string;
      description: string;
      cards: Card[];
      lastSynced: number;
    };
  };
  reviews: {
    key: string;
    value: {
      id: string;
      cardId: string;
      quality: number;
      timestamp: number;
      synced: boolean;
    };
  };
}

@Injectable({ providedIn: 'root' })
export class OfflineStudyService {
  private db: IDBPDatabase<StudyDB> | null = null;

  async init() {
    this.db = await openDB<StudyDB>('opendeck-study', 1, {
      upgrade(db) {
        db.createObjectStore('decks', { keyPath: 'id' });
        db.createObjectStore('reviews', { keyPath: 'id' });
      }
    });
  }

  async saveDeckForOffline(deck: any, cards: Card[]) {
    if (!this.db) await this.init();

    await this.db!.put('decks', {
      id: deck.id,
      name: deck.name,
      description: deck.description,
      cards,
      lastSynced: Date.now()
    });
  }

  async getOfflineDeck(deckId: string) {
    if (!this.db) await this.init();
    return await this.db!.get('decks', deckId);
  }

  async getAllOfflineDecks() {
    if (!this.db) await this.init();
    return await this.db!.getAll('decks');
  }

  async saveOfflineReview(cardId: string, quality: number) {
    if (!this.db) await this.init();

    await this.db!.put('reviews', {
      id: crypto.randomUUID(),
      cardId,
      quality,
      timestamp: Date.now(),
      synced: false
    });
  }

  async syncReviews(studyService: any) {
    if (!this.db) await this.init();

    const reviews = await this.db!.getAll('reviews');
    const unsynced = reviews.filter(r => !r.synced);

    for (const review of unsynced) {
      try {
        await studyService.recordReview({
          cardId: review.cardId,
          quality: review.quality
        });

        // Mark as synced
        await this.db!.put('reviews', { ...review, synced: true });
      } catch (error) {
        console.error('Failed to sync review:', error);
      }
    }

    return unsynced.length;
  }

  async clearSyncedReviews() {
    if (!this.db) await this.init();

    const reviews = await this.db!.getAll('reviews');
    const synced = reviews.filter(r => r.synced);

    for (const review of synced) {
      await this.db!.delete('reviews', review.id);
    }
  }
}
```

## Mobile-Optimized UI

### Touch Gesture Support

#### `opendeck-portal/src/app/components/flashcard-swipe/flashcard-swipe.component.ts`:
```typescript
import { Component, Input, Output, EventEmitter, HostListener } from '@angular/core';

@Component({
  selector: 'app-flashcard-swipe',
  template: `
    <div class="flashcard-swipe"
         (touchstart)="onTouchStart($event)"
         (touchmove)="onTouchMove($event)"
         (touchend)="onTouchEnd($event)"
         [style.transform]="'translateX(' + dragX + 'px) rotate(' + rotation + 'deg)'"
         [class.swiping]="isSwiping">
      <ng-content></ng-content>

      <!-- Swipe indicators -->
      <div class="swipe-indicator left" [class.active]="dragX < -50">
        <i class="pi pi-times"></i>
      </div>
      <div class="swipe-indicator right" [class.active]="dragX > 50">
        <i class="pi pi-check"></i>
      </div>
    </div>
  `,
  styles: [`
    .flashcard-swipe {
      position: relative;
      transition: transform 0.3s ease;
      touch-action: none;
    }

    .flashcard-swipe.swiping {
      transition: none;
    }

    .swipe-indicator {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      font-size: 3rem;
      opacity: 0;
      transition: opacity 0.2s;
    }

    .swipe-indicator.left {
      left: 2rem;
      color: var(--red-500);
    }

    .swipe-indicator.right {
      right: 2rem;
      color: var(--green-500);
    }

    .swipe-indicator.active {
      opacity: 0.8;
    }
  `]
})
export class FlashcardSwipeComponent {
  @Output() swipeLeft = new EventEmitter();
  @Output() swipeRight = new EventEmitter();
  @Output() tap = new EventEmitter();

  private touchStartX = 0;
  private touchStartTime = 0;
  dragX = 0;
  rotation = 0;
  isSwiping = false;

  onTouchStart(event: TouchEvent) {
    this.touchStartX = event.touches[0].clientX;
    this.touchStartTime = Date.now();
  }

  onTouchMove(event: TouchEvent) {
    const currentX = event.touches[0].clientX;
    this.dragX = currentX - this.touchStartX;
    this.rotation = this.dragX / 20;

    if (Math.abs(this.dragX) > 10) {
      this.isSwiping = true;
    }
  }

  onTouchEnd(event: TouchEvent) {
    const swipeThreshold = 100;
    const touchDuration = Date.now() - this.touchStartTime;

    // Tap detection (quick touch, minimal movement)
    if (touchDuration < 200 && Math.abs(this.dragX) < 10) {
      this.tap.emit();
    }
    // Swipe left (incorrect)
    else if (this.dragX < -swipeThreshold) {
      this.swipeLeft.emit();
    }
    // Swipe right (correct)
    else if (this.dragX > swipeThreshold) {
      this.swipeRight.emit();
    }

    // Reset
    this.dragX = 0;
    this.rotation = 0;
    this.isSwiping = false;
  }
}
```

### Mobile Study UI

#### `opendeck-portal/src/app/pages/mobile-study/mobile-study.component.ts`:
```typescript
import { Component, OnInit, signal } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-mobile-study',
  templateUrl: './mobile-study.component.html',
  styleUrls: ['./mobile-study.component.scss']
})
export class MobileStudyComponent implements OnInit {
  cards = signal<any[]>([]);
  currentIndex = signal(0);
  isFlipped = signal(false);
  sessionComplete = signal(false);

  get currentCard() {
    return this.cards()[this.currentIndex()];
  }

  get visibleCards() {
    // Show current card and next 2 for stack effect
    return this.cards().slice(this.currentIndex(), this.currentIndex() + 3);
  }

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private studyService: StudyService,
    private offlineService: OfflineStudyService
  ) {}

  async ngOnInit() {
    const deckId = this.route.snapshot.params['deckId'];
    await this.loadCards(deckId);
  }

  async loadCards(deckId: string) {
    try {
      // Try to load from server
      const cards = await this.studyService.getDueCards(deckId);
      this.cards.set(cards);
    } catch (error) {
      // Fallback to offline storage
      const offlineDeck = await this.offlineService.getOfflineDeck(deckId);
      if (offlineDeck) {
        this.cards.set(offlineDeck.cards);
      }
    }
  }

  flipCard() {
    this.isFlipped.set(!this.isFlipped());
  }

  async rateCard(quality: number) {
    const card = this.currentCard;

    // Save review (online or offline)
    try {
      await this.studyService.recordReview({
        cardId: card.id,
        quality
      });
    } catch (error) {
      // Queue for later sync
      await this.offlineService.saveOfflineReview(card.id, quality);
    }

    // Move to next card
    if (this.currentIndex() < this.cards().length - 1) {
      this.currentIndex.update(v => v + 1);
      this.isFlipped.set(false);
    } else {
      this.sessionComplete.set(true);
    }
  }

  exitStudy() {
    this.router.navigate(['/dashboard']);
  }
}
```

#### `opendeck-portal/src/app/pages/mobile-study/mobile-study.component.html`:
```html
<div class="mobile-study-container">
  <!-- Mobile Header -->
  <div class="mobile-header">
    <button pButton icon="pi pi-arrow-left" (click)="exitStudy()"
            class="p-button-text p-button-rounded"></button>
    <div class="progress-indicator">
      <span>{{ currentIndex() + 1 }} / {{ cards().length }}</span>
    </div>
    <button pButton icon="pi pi-ellipsis-v"
            class="p-button-text p-button-rounded"></button>
  </div>

  <!-- Flashcard Stack -->
  <div class="flashcard-stack" *ngIf="!sessionComplete()">
    <app-flashcard-swipe
      (swipeLeft)="rateCard(2)"
      (swipeRight)="rateCard(5)"
      (tap)="flipCard()">

      <div class="mobile-flashcard" [class.flipped]="isFlipped()">
        <div class="card-face front" *ngIf="!isFlipped()">
          <div class="card-content">
            <h2>{{ currentCard?.front }}</h2>
          </div>
          <div class="tap-hint">
            <i class="pi pi-hand-pointer"></i>
            <span>Tap to flip</span>
          </div>
        </div>

        <div class="card-face back" *ngIf="isFlipped()">
          <div class="card-content">
            <p>{{ currentCard?.back }}</p>
          </div>
        </div>
      </div>
    </app-flashcard-swipe>
  </div>

  <!-- Swipe Instructions -->
  <div class="swipe-instructions" *ngIf="!isFlipped() && !sessionComplete()">
    <div class="instruction left">
      <i class="pi pi-arrow-left"></i>
      <span>Swipe left if incorrect</span>
    </div>
    <div class="instruction right">
      <i class="pi pi-arrow-right"></i>
      <span>Swipe right if correct</span>
    </div>
  </div>

  <!-- Bottom Actions (after flip) -->
  <div class="bottom-actions" *ngIf="isFlipped() && !sessionComplete()">
    <button pButton label="Again" severity="danger"
            icon="pi pi-times"
            (click)="rateCard(0)"
            class="p-button-lg"></button>
    <button pButton label="Hard" severity="warning"
            icon="pi pi-exclamation-triangle"
            (click)="rateCard(3)"
            class="p-button-lg"></button>
    <button pButton label="Good" severity="info"
            icon="pi pi-check"
            (click)="rateCard(4)"
            class="p-button-lg"></button>
    <button pButton label="Easy" severity="success"
            icon="pi pi-check-circle"
            (click)="rateCard(5)"
            class="p-button-lg"></button>
  </div>

  <!-- Session Complete -->
  <div class="session-complete" *ngIf="sessionComplete()">
    <i class="pi pi-check-circle"></i>
    <h2>Great job!</h2>
    <p>You've completed this study session</p>
    <button pButton label="Back to Dashboard"
            (click)="exitStudy()"
            class="p-button-lg"></button>
  </div>
</div>
```

#### `opendeck-portal/src/app/pages/mobile-study/mobile-study.component.scss`:
```scss
.mobile-study-container {
  position: fixed;
  inset: 0;
  background: var(--surface-ground);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .mobile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--surface-border);
    background: var(--surface-card);
    z-index: 10;

    .progress-indicator {
      font-weight: 600;
      font-size: 1.1rem;
    }
  }

  .flashcard-stack {
    flex: 1;
    position: relative;
    padding: 2rem 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
  }

  .mobile-flashcard {
    width: 100%;
    max-width: 500px;
    height: 400px;
    background: var(--surface-card);
    border-radius: 1rem;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    position: relative;

    .card-face {
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .card-content {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        width: 100%;

        h2 {
          font-size: 1.5rem;
          margin: 0;
        }

        p {
          font-size: 1.2rem;
          margin: 0;
          line-height: 1.6;
        }
      }

      .tap-hint {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: var(--text-color-secondary);
        font-size: 0.9rem;
        margin-top: 1rem;

        i {
          font-size: 1.2rem;
        }
      }
    }
  }

  .swipe-instructions {
    padding: 1rem;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;

    .instruction {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 0.5rem;
      font-size: 0.9rem;
      color: var(--text-color-secondary);

      i {
        font-size: 2rem;
      }

      &.left i {
        color: var(--red-500);
      }

      &.right i {
        color: var(--green-500);
      }
    }
  }

  .bottom-actions {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid var(--surface-border);
    background: var(--surface-card);

    button {
      width: 100%;
    }

    @media (max-width: 768px) {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  .session-complete {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 2rem;
    text-align: center;

    i {
      font-size: 5rem;
      color: var(--green-500);
    }

    h2 {
      margin: 0;
      font-size: 2rem;
    }

    p {
      color: var(--text-color-secondary);
      font-size: 1.1rem;
    }
  }
}
```

## Push Notifications

### Backend Notification Service

#### `backend/app/services/notification_service.py`:
```python
from firebase_admin import messaging
from datetime import datetime, timedelta
from typing import Optional

class NotificationService:
    """Send push notifications using Firebase Cloud Messaging"""

    async def send_study_reminder(self, user: User, due_cards_count: int):
        """Send push notification for daily study reminder"""
        if not user.fcm_token:
            return

        message = messaging.Message(
            notification=messaging.Notification(
                title="Time to study! 📚",
                body=f"You have {due_cards_count} cards due for review"
            ),
            token=user.fcm_token,
            data={
                "type": "study_reminder",
                "url": "/study",
                "due_cards": str(due_cards_count)
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='notification_icon',
                    color='#1976d2'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=due_cards_count,
                        sound='default'
                    )
                )
            )
        )

        try:
            response = messaging.send(message)
            logger.info(f"Sent notification to {user.email}: {response}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def send_streak_milestone(self, user: User, streak_days: int):
        """Congratulate user on streak milestone"""
        if not user.fcm_token:
            return

        milestone_emojis = {
            7: "🔥",
            30: "💪",
            100: "🏆",
            365: "👑"
        }

        emoji = milestone_emojis.get(streak_days, "🎉")

        message = messaging.Message(
            notification=messaging.Notification(
                title=f"{emoji} {streak_days} Day Streak!",
                body=f"You've studied for {streak_days} days in a row!"
            ),
            token=user.fcm_token,
            data={
                "type": "streak_milestone",
                "streak_days": str(streak_days)
            }
        )

        try:
            messaging.send(message)
        except Exception as e:
            logger.error(f"Failed to send streak notification: {e}")
```

### Frontend Push Notification Setup

#### `opendeck-portal/src/app/services/push-notification.service.ts`:
```typescript
import { Injectable } from '@angular/core';
import { SwPush } from '@angular/service-worker';
import { HttpClient } from '@angular/common/http';

@Injectable({ providedIn: 'root' })
export class PushNotificationService {
  constructor(
    private swPush: SwPush,
    private http: HttpClient
  ) {}

  async requestPermission() {
    if (!this.swPush.isEnabled) {
      console.warn('Service Worker not enabled');
      return false;
    }

    try {
      const sub = await this.swPush.requestSubscription({
        serverPublicKey: environment.vapidPublicKey
      });

      // Send subscription to backend
      await this.http.post('/api/v1/notifications/subscribe', {
        subscription: sub
      }).toPromise();

      return true;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      return false;
    }
  }

  listenForMessages() {
    this.swPush.messages.subscribe((message: any) => {
      console.log('Received push notification:', message);
      // Handle notification click
    });

    this.swPush.notificationClicks.subscribe((click: any) => {
      console.log('Notification clicked:', click);
      // Navigate to relevant page
      if (click.notification.data?.url) {
        window.location.href = click.notification.data.url;
      }
    });
  }
}
```

## Implementation Steps

### Phase 1: PWA Setup (Week 1)
- [ ] Run `ng add @angular/pwa`
- [ ] Configure service worker (`ngsw-config.json`)
- [ ] Create and configure `manifest.webmanifest`
- [ ] Generate app icons using tool (realfavicongenerator.net)
- [ ] Test installability on Chrome, Safari, Edge
- [ ] Add "Install App" prompt in UI
- [ ] Test offline fallback page

### Phase 2: Offline Support (Week 2)
- [ ] Install and configure IndexedDB (idb library)
- [ ] Implement OfflineService for queue management
- [ ] Build OfflineStudyService for deck caching
- [ ] Add "Download for Offline" button to decks
- [ ] Implement sync logic when back online
- [ ] Show offline indicator in UI
- [ ] Test offline study sessions thoroughly

### Phase 3: Mobile UI (Week 3)
- [ ] Create swipe gesture component
- [ ] Build mobile-optimized study interface
- [ ] Add touch-friendly buttons and spacing
- [ ] Implement haptic feedback (vibration)
- [ ] Add responsive breakpoints
- [ ] Test on iOS and Android devices
- [ ] Optimize for different screen sizes

### Phase 4: Push Notifications (Week 4)
- [ ] Set up Firebase Cloud Messaging
- [ ] Implement notification permissions UI
- [ ] Create backend notification service
- [ ] Build daily study reminder scheduler
- [ ] Add streak milestone notifications
- [ ] Test notifications on mobile devices
- [ ] Add notification preferences page

## Key Features

1. **Installable**: Add to home screen on mobile/desktop
2. **Offline First**: Download decks for offline study
3. **Background Sync**: Automatically sync reviews when back online
4. **Push Notifications**: Daily reminders and streak milestones
5. **Touch Gestures**: Swipe to rate cards (Tinder-style)
6. **App Shortcuts**: Quick actions from home screen
7. **Mobile Optimized**: Large buttons, readable text, smooth animations

## Success Metrics

- PWA installation rate
- Offline usage sessions
- Push notification opt-in rate
- Mobile vs desktop usage ratio
- Time spent in app

## Technical Considerations

- **Service Worker Caching**: Balance between freshness and performance
- **IndexedDB Storage**: Limit size to prevent quota issues
- **Battery Usage**: Optimize for minimal battery drain
- **iOS Limitations**: Some PWA features limited on iOS
- **Network Detection**: Handle flaky connections gracefully
- **Security**: Ensure offline data is secure

## Testing Checklist

- [ ] Test PWA installation on Chrome (Android/Desktop)
- [ ] Test PWA installation on Safari (iOS)
- [ ] Test offline functionality
- [ ] Test background sync
- [ ] Test push notifications
- [ ] Test on slow 3G network
- [ ] Test app shortcuts
- [ ] Lighthouse PWA audit (score > 90)

## Future Enhancements

- iOS native app wrapper (Capacitor)
- Android native app (Capacitor)
- Biometric authentication
- Widget support
- Wear OS integration
- Voice input for creating cards
