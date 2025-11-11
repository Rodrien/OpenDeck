import { Component, OnInit, OnDestroy, signal, computed, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { Subject, takeUntil } from 'rxjs';

// PrimeNG Components
import { CardModule } from 'primeng/card';
import { ButtonModule } from 'primeng/button';
import { ProgressBarModule } from 'primeng/progressbar';
import { DividerModule } from 'primeng/divider';
import { ToastModule } from 'primeng/toast';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';

// Services & Models
import { StudyService } from '../../services/study.service';
import { CardService } from '../../services/card.service';
import { StudySession, QUALITY_RATINGS, QualityRating } from '../../models/study.model';
import { Card } from '../../models/card.model';

// Components
import { ReportCardDialog } from '../../components/report-card-dialog/report-card-dialog';

/**
 * Study Session Component
 * Implements spaced repetition study session with flashcard review
 */
@Component({
  selector: 'app-study-session',
  standalone: true,
  imports: [
    CommonModule,
    TranslateModule,
    CardModule,
    ButtonModule,
    ProgressBarModule,
    DividerModule,
    ToastModule,
    TooltipModule,
    ReportCardDialog
  ],
  providers: [MessageService],
  templateUrl: './study-session.component.html',
  styleUrls: ['./study-session.component.scss']
})
export class StudySessionComponent implements OnInit, OnDestroy {
  private destroy$ = new Subject<void>();
  private reviewStartTime?: number;

  // Signals for reactive state
  sessionId = signal<string | null>(null);
  deckId = signal<string | null>(null);
  cards = signal<Card[]>([]);
  currentCardIndex = signal<number>(0);
  isFlipped = signal<boolean>(false);
  cardsReviewed = signal<number>(0);
  cardsCorrect = signal<number>(0);
  isLoading = signal<boolean>(true);
  isSessionComplete = signal<boolean>(false);
  error = signal<string | null>(null);
  showReportDialog = signal<boolean>(false);

  // Computed values
  currentCard = computed(() => {
    const index = this.currentCardIndex();
    const cardsList = this.cards();
    return cardsList[index] || null;
  });

  progressPercentage = computed(() => {
    const total = this.cards().length;
    const reviewed = this.cardsReviewed();
    return total > 0 ? Math.round((reviewed / total) * 100) : 0;
  });

  accuracy = computed(() => {
    const reviewed = this.cardsReviewed();
    const correct = this.cardsCorrect();
    return reviewed > 0 ? Math.round((correct / reviewed) * 100) : 0;
  });

  hasMoreCards = computed(() => {
    return this.currentCardIndex() < this.cards().length - 1;
  });

  // Quality ratings
  readonly qualityRatings: QualityRating[] = QUALITY_RATINGS;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private studyService: StudyService,
    private cardService: CardService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    // Get deck ID from route
    const deckId = this.route.snapshot.paramMap.get('deckId');
    if (!deckId) {
      this.error.set('Invalid deck ID');
      this.isLoading.set(false);
      return;
    }

    this.deckId.set(deckId);
    this.checkForActiveSessionOrStart(deckId);
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Check for an active session first, then start a new one if needed
   */
  private checkForActiveSessionOrStart(deckId: string): void {
    this.isLoading.set(true);

    this.studyService
      .getActiveSession(deckId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (activeSession) => {
          if (activeSession) {
            // Resume existing active session
            console.log('Resuming active session:', activeSession.id);
            this.sessionId.set(activeSession.id);
            this.loadCardsForSession(activeSession);
          } else {
            // No active session, start a new one
            this.startStudySession(deckId);
          }
        },
        error: (err) => {
          console.error('Error checking for active session:', err);
          // If check fails, try to start a new session anyway
          this.startStudySession(deckId);
        }
      });
  }

  /**
   * Start a new study session
   */
  private startStudySession(deckId: string): void {
    this.studyService
      .startSession(deckId, 'review')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (session) => {
          this.sessionId.set(session.id);
          this.loadCardsForSession(session);
        },
        error: (err) => {
          console.error('Error starting session:', err);
          this.error.set('Failed to start study session');
          this.isLoading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to start study session. Please try again.'
          });
        }
      });
  }

  /**
   * Load cards for the session
   */
  private loadCardsForSession(session: StudySession): void {
    if (!session.card_ids || session.card_ids.length === 0) {
      this.isLoading.set(false);
      this.isSessionComplete.set(true);
      this.messageService.add({
        severity: 'info',
        summary: 'No Cards Due',
        detail: 'All cards are up to date! Great work!'
      });
      return;
    }

    // Load all cards for the session
    this.cardService
      .getCardsForDeck(session.deck_id, session.card_ids.length)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          // Filter to only include cards in this session
          const sessionCards = response.items.filter((card: Card) =>
            session.card_ids.includes(card.id)
          );
          this.cards.set(sessionCards);
          this.currentCardIndex.set(session.current_card_index || 0);
          this.cardsReviewed.set(session.cards_reviewed || 0);
          this.cardsCorrect.set(session.cards_correct || 0);
          this.isLoading.set(false);
          this.startReviewTimer();
        },
        error: (err) => {
          console.error('Error loading cards:', err);
          this.error.set('Failed to load flashcards');
          this.isLoading.set(false);
        }
      });
  }

  /**
   * Start timer for tracking review duration
   */
  private startReviewTimer(): void {
    this.reviewStartTime = Date.now();
  }

  /**
   * Calculate time spent on current card
   */
  private getReviewDuration(): number | undefined {
    if (this.reviewStartTime) {
      return Math.round((Date.now() - this.reviewStartTime) / 1000);
    }
    return undefined;
  }

  /**
   * Flip the current card
   */
  flipCard(): void {
    this.isFlipped.set(!this.isFlipped());
  }

  /**
   * Record a review with quality rating
   */
  recordReview(quality: number): void {
    const sessionIdValue = this.sessionId();
    const currentCardValue = this.currentCard();

    if (!sessionIdValue || !currentCardValue) {
      return;
    }

    const timeTaken = this.getReviewDuration();

    this.studyService
      .recordReview(sessionIdValue, currentCardValue.id, quality, timeTaken)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (updatedSession) => {
          // Update statistics
          this.cardsReviewed.set(updatedSession.cards_reviewed);
          this.cardsCorrect.set(updatedSession.cards_correct);

          // Move to next card or complete session
          if (this.hasMoreCards()) {
            this.moveToNextCard();
          } else {
            this.completeSession();
          }
        },
        error: (err) => {
          console.error('Error recording review:', err);
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Failed to record review. Please try again.'
          });
        }
      });
  }

  /**
   * Move to the next card
   */
  private moveToNextCard(): void {
    this.currentCardIndex.update(index => index + 1);
    this.isFlipped.set(false);
    this.startReviewTimer();
  }

  /**
   * Complete the study session
   */
  private completeSession(): void {
    const sessionIdValue = this.sessionId();
    if (!sessionIdValue) {
      return;
    }

    this.studyService
      .endSession(sessionIdValue)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.isSessionComplete.set(true);
          this.messageService.add({
            severity: 'success',
            summary: 'Session Complete',
            detail: 'Great work! You\'ve completed this study session.'
          });
        },
        error: (err) => {
          console.error('Error completing session:', err);
          // Still mark as complete on client side
          this.isSessionComplete.set(true);
        }
      });
  }

  /**
   * Return to dashboard
   */
  backToDashboard(): void {
    this.router.navigate(['/pages/flashcards']);
  }

  /**
   * Start a new session
   */
  startNewSession(): void {
    const deckIdValue = this.deckId();
    if (deckIdValue) {
      // Reset state
      this.isSessionComplete.set(false);
      this.currentCardIndex.set(0);
      this.cardsReviewed.set(0);
      this.cardsCorrect.set(0);
      this.isFlipped.set(false);
      this.startStudySession(deckIdValue);
    }
  }

  /**
   * Keyboard shortcuts handler
   */
  @HostListener('window:keydown', ['$event'])
  handleKeyboardEvent(event: KeyboardEvent): void {
    // Ignore if session is complete or loading
    if (this.isSessionComplete() || this.isLoading()) {
      return;
    }

    // Ignore keyboard shortcuts when user is typing in input fields
    // Check BOTH event.target (where the event originated) AND document.activeElement
    const target = event.target as HTMLElement;
    const activeElement = document.activeElement as HTMLElement;

    const isInputElement = (element: HTMLElement | null): boolean => {
      if (!element) return false;

      const tagName = element.tagName;
      return tagName === 'INPUT' ||
             tagName === 'TEXTAREA' ||
             tagName === 'SELECT' ||
             element.isContentEditable;
    };

    // If user is typing in any input field, completely ignore keyboard shortcuts
    if (isInputElement(target) || isInputElement(activeElement)) {
      return; // Don't interfere with normal typing behavior
    }

    switch (event.key) {
      case ' ':
      case 'Enter':
        event.preventDefault();
        this.flipCard();
        break;
      case '1':
        event.preventDefault();
        if (this.isFlipped()) {
          this.recordReview(0); // Again
        }
        break;
      case '2':
        event.preventDefault();
        if (this.isFlipped()) {
          this.recordReview(3); // Hard
        }
        break;
      case '3':
        event.preventDefault();
        if (this.isFlipped()) {
          this.recordReview(4); // Good
        }
        break;
      case '4':
        event.preventDefault();
        if (this.isFlipped()) {
          this.recordReview(5); // Easy
        }
        break;
    }
  }

  /**
   * Open the report card dialog
   */
  openReportDialog(): void {
    this.showReportDialog.set(true);
  }

  /**
   * Handle card report submission during study session
   */
  onCardReported(): void {
    // Optional: Track reported cards in session
    console.log('Card reported during study session');
  }
}
