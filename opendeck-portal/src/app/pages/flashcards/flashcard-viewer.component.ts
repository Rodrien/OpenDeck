import { Component, HostListener, OnInit, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { trigger, transition, style, animate } from '@angular/animations';
import { forkJoin } from 'rxjs';

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

// Models
import { Card as ApiCard } from '../../models/card.model';
import { CardDirection } from './models/flashcard-data.interface';

@Component({
    selector: 'app-flashcard-viewer',
    imports: [
        CommonModule,
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
export class FlashcardViewerComponent implements OnInit {
    // Reactive state using signals
    deckTitle = signal<string>('');
    cards = signal<ApiCard[]>([]);
    currentIndex = signal<number>(0);
    showAnswer = signal<boolean>(false);
    animationTrigger = signal<number>(0);
    loading = signal<boolean>(false);
    error = signal<string | null>(null);

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
        return `Card ${current} of ${total}`;
    });

    constructor(
        private route: ActivatedRoute,
        private router: Router,
        private deckService: DeckService,
        private cardService: CardService
    ) {}

    ngOnInit(): void {
        // Get deck ID from route parameters
        const deckIdParam = this.route.snapshot.paramMap.get('deckId');

        if (deckIdParam) {
            const deckId = parseInt(deckIdParam, 10);
            if (!isNaN(deckId)) {
                this.loadDeckAndCards(deckId);
            } else {
                this.error.set('Invalid deck ID');
                console.error('Invalid deck ID:', deckIdParam);
            }
        } else {
            // No deck ID provided, navigate back to listing
            this.router.navigate(['/pages/flashcards']);
        }
    }

    /**
     * Load deck metadata and cards from the API
     * Uses forkJoin to load both deck and cards in parallel
     */
    private loadDeckAndCards(deckId: number): void {
        this.loading.set(true);
        this.error.set(null);

        // Load deck metadata and cards in parallel
        forkJoin({
            deck: this.deckService.getById(deckId),
            cards: this.cardService.getCardsForDeck(deckId, 1000) // Load up to 1000 cards
        }).subscribe({
            next: (result) => {
                this.deckTitle.set(result.deck.title);
                this.cards.set(result.cards.items);
                this.loading.set(false);

                // If no cards, show error
                if (result.cards.items.length === 0) {
                    this.error.set('This deck has no flashcards yet.');
                }
            },
            error: (err) => {
                this.error.set('Failed to load deck. Please try again later.');
                this.loading.set(false);
                console.error('Error loading deck and cards:', err);
            }
        });
    }

    /**
     * Navigate to the next flashcard
     */
    nextCard(): void {
        if (!this.isLastCard()) {
            this.currentIndex.update(i => i + 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v + 1);
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
