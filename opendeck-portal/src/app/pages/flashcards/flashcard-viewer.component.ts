import { Component, HostListener, OnInit, OnDestroy, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { trigger, transition, style, animate } from '@angular/animations';
import { forkJoin } from 'rxjs';
import { TranslateModule, TranslateService } from '@ngx-translate/core';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { Button } from 'primeng/button';
import { ProgressBar } from 'primeng/progressbar';
import { Tag } from 'primeng/tag';
import { ProgressSpinner } from 'primeng/progressspinner';
import { Message } from 'primeng/message';

// Services
import { DeckService } from '../../services/deck.service';
import { CardService } from '../../services/card.service';
import { DeckProgressService } from '../../services/deck-progress.service';

// Models
import { Card as ApiCard } from '../../models/card.model';
import { CardDirection } from './models/flashcard-data.interface';

@Component({
    selector: 'app-flashcard-viewer',
    imports: [
        CommonModule,
        TranslateModule,
        Card,
        Button,
        ProgressBar,
        Tag,
        ProgressSpinner,
        Message
    ],
    templateUrl: './flashcard-viewer.component.html',
    styleUrls: ['./flashcard-viewer.component.scss'],
    animations: [
        trigger('cardSlide', [
            transition(':increment', [
                style({ transform: 'translateX(100%)', opacity: 0 }),
                animate('300ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
            ]),
            transition(':decrement', [
                style({ transform: 'translateX(-100%)', opacity: 0 }),
                animate('300ms ease-out', style({ transform: 'translateX(0)', opacity: 1 }))
            ])
        ]),
        trigger('fadeIn', [
            transition(':enter', [
                style({ opacity: 0, transform: 'translateY(10px)' }),
                animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
            ])
        ])
    ]
})
export class FlashcardViewerComponent implements OnInit, OnDestroy {
    // Reactive state using signals
    deckId = signal<string>('');
    deckTitle = signal<string>('');
    cards = signal<ApiCard[]>([]);
    currentIndex = signal<number>(0);
    showAnswer = signal<boolean>(false);
    animationTrigger = signal<number>(0);
    loading = signal<boolean>(false);
    error = signal<string | null>(null);
    resumedFromProgress = signal<boolean>(false);

    // Computed values
    currentCard = computed(() => this.cards()[this.currentIndex()]);
    progress = computed(() => {
        const total = this.cards().length;
        return total > 0 ? ((this.currentIndex() + 1) / total) * 100 : 0;
    });
    isFirstCard = computed(() => this.currentIndex() === 0);
    isLastCard = computed(() => this.currentIndex() === this.cards().length - 1);
    cardCountText = computed(() => {
        const current = this.currentIndex() + 1;
        const total = this.cards().length;
        return this.translate.instant('flashcard.progress', { current, total });
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private deckService: DeckService,
        private cardService: CardService,
        private translate: TranslateService,
        private progressService: DeckProgressService
    ) {}

    ngOnInit(): void {
        // Get deck ID from route parameters
        const deckId = this.route.snapshot.paramMap.get('deckId');

        if (deckId) {
            this.deckId.set(deckId);
            this.loadDeckAndCards(deckId);
        } else {
            // No deck ID provided, navigate back to listing
            this.router.navigate(['/pages/flashcards']);
        }
    }

    ngOnDestroy(): void {
        // Save progress before component is destroyed
        this.saveProgress();
    }

    /**
     * Load deck metadata and cards from the API
     * Uses forkJoin to load both deck and cards in parallel
     */
    private loadDeckAndCards(deckId: string): void {
        this.loading.set(true);
        this.error.set(null);

        // Load deck metadata and cards in parallel
        forkJoin({
            deck: this.deckService.getById(deckId),
            cards: this.cardService.getCardsForDeck(deckId, 100) // Backend max limit is 100
        }).subscribe({
            next: (result) => {
                this.deckTitle.set(result.deck.title);
                this.cards.set(result.cards.items);
                this.loading.set(false);

                // If no cards, show error
                if (result.cards.items.length === 0) {
                    this.error.set(this.translate.instant('flashcard.noCards'));
                } else {
                    // Restore progress if available
                    this.restoreProgress(deckId, result.cards.items.length);
                }
            },
            error: (err) => {
                this.error.set(this.translate.instant('errors.loadFailed'));
                this.loading.set(false);
                console.error('Error loading deck and cards:', err);

                // Clear progress for failed deck
                this.progressService.clearProgress(deckId);
            }
        });
    }

    /**
     * Restore progress from localStorage if available
     */
    private restoreProgress(deckId: string, totalCards: number): void {
        const savedProgress = this.progressService.getProgress(deckId);

        if (savedProgress) {
            // Validate saved index is within bounds
            let restoredIndex = savedProgress.currentCardIndex;

            // Clamp index if deck size changed
            if (restoredIndex >= totalCards) {
                restoredIndex = totalCards - 1;
            }

            // Only restore if not at the beginning
            if (restoredIndex > 0) {
                this.currentIndex.set(restoredIndex);
                this.resumedFromProgress.set(true);
            }
        }
    }

    /**
     * Save current progress to localStorage
     */
    private saveProgress(): void {
        const deckId = this.deckId();
        const cards = this.cards();

        if (deckId && cards.length > 0) {
            this.progressService.saveProgress(
                deckId,
                this.currentIndex(),
                cards.length,
                this.deckTitle()
            );
        }
    }

    /**
     * Navigate to the next flashcard
     */
    nextCard(): void {
        if (!this.isLastCard()) {
            this.currentIndex.update(i => i + 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v + 1);
            this.saveProgress();
        }
    }

    /**
     * Navigate to the previous flashcard
     */
    previousCard(): void {
        if (!this.isFirstCard()) {
            this.currentIndex.update(i => i - 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v - 1);
            this.saveProgress();
        }
    }

    /**
     * Reset progress and start from the beginning
     */
    resetProgress(): void {
        const deckId = this.deckId();
        if (deckId) {
            this.progressService.clearProgress(deckId);
            this.currentIndex.set(0);
            this.showAnswer.set(false);
            this.resumedFromProgress.set(false);
        }
    }

    /**
     * Toggle answer visibility
     */
    toggleAnswer(): void {
        this.showAnswer.update(v => !v);
    }

    /**
     * Navigate back to the deck listing
     */
    backToDecks(): void {
        this.router.navigate(['/pages/flashcards']);
    }

    /**
     * Keyboard navigation support
     * - Arrow Left: Previous card
     * - Arrow Right: Next card
     * - Space/Enter: Toggle answer
     */
    @HostListener('document:keydown', ['$event'])
    handleKeyboardEvent(event: KeyboardEvent): void {
        switch (event.key) {
            case 'ArrowLeft':
                event.preventDefault();
                this.previousCard();
                break;
            case 'ArrowRight':
                event.preventDefault();
                this.nextCard();
                break;
            case ' ':
            case 'Enter':
                event.preventDefault();
                this.toggleAnswer();
                break;
            case 'Escape':
                event.preventDefault();
                this.backToDecks();
                break;
        }
    }

    /**
     * Open source URL in new tab
     */
    openSource(url: string): void {
        if (url && url !== '#') {
            window.open(url, '_blank', 'noopener,noreferrer');
        }
    }
}
