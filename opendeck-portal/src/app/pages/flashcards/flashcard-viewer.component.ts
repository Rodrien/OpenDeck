import { Component, HostListener, OnInit, OnDestroy, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { trigger, transition, style, animate } from '@angular/animations';
import { forkJoin, Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
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
    loadingInitial = signal<boolean>(false);
    error = signal<string | null>(null);
    resumedFromProgress = signal<boolean>(false);

    // Pagination state
    pageSize = signal<number>(10);
    currentPage = signal<number>(0);
    totalCards = signal<number>(0);
    loadedPages = signal<Set<number>>(new Set());
    cardsCache = signal<Map<number, ApiCard[]>>(new Map());
    loadingPage = signal<boolean>(false);

    // Navigation queue to handle rapid navigation during page loads
    private navigationQueue: ('next' | 'prev')[] = [];

    // Computed values for pagination
    totalPages = computed(() => Math.ceil(this.totalCards() / this.pageSize()));
    globalCardIndex = computed(() => this.currentPage() * this.pageSize() + this.currentIndex());

    // Computed values
    currentCard = computed(() => this.cards()[this.currentIndex()]);
    progress = computed(() => {
        const total = this.totalCards();
        return total > 0 ? ((this.globalCardIndex() + 1) / total) * 100 : 0;
    });
    isFirstCard = computed(() => this.globalCardIndex() === 0);
    isLastCard = computed(() => this.globalCardIndex() === this.totalCards() - 1);
    cardCountText = computed(() => {
        const current = this.globalCardIndex() + 1;
        const total = this.totalCards();
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
     * Load deck metadata and cards from the API using pagination
     * First loads deck to get total card count, then loads appropriate page
     */
    private loadDeckAndCards(deckId: string): void {
        this.loadingInitial.set(true);
        this.error.set(null);

        // First, load deck metadata and initial page info to get total count
        forkJoin({
            deck: this.deckService.getById(deckId),
            initialPage: this.cardService.getCardsPage(deckId, 0, this.pageSize())
        }).subscribe({
            next: (result) => {
                this.deckTitle.set(result.deck.title);
                this.totalCards.set(result.initialPage.total);

                // If no cards, show error
                if (result.initialPage.total === 0) {
                    this.error.set(this.translate.instant('flashcard.noCards'));
                    this.loadingInitial.set(false);
                    return;
                }

                // Check for saved progress
                const savedProgress = this.progressService.getProgress(deckId);
                let targetPage = 0;
                let targetIndex = 0;

                if (savedProgress && savedProgress.currentCardIndex > 0) {
                    // Calculate which page contains the saved card
                    const savedCardIndex = Math.min(savedProgress.currentCardIndex, result.initialPage.total - 1);
                    targetPage = Math.floor(savedCardIndex / this.pageSize());
                    targetIndex = savedCardIndex % this.pageSize();
                }

                // Load the target page (either page 0 or the page with saved progress)
                this.loadPage(targetPage, deckId).subscribe({
                    next: () => {
                        this.currentPage.set(targetPage);
                        this.currentIndex.set(targetIndex);
                        this.updateCurrentCards();
                        this.loadingInitial.set(false);

                        // Set resumed flag if we loaded a non-zero position
                        if (savedProgress && savedProgress.currentCardIndex > 0) {
                            this.resumedFromProgress.set(true);
                        }

                        // Prefetch adjacent pages in background
                        this.prefetchAdjacentPages(deckId);
                    },
                    error: (err) => {
                        this.error.set(this.translate.instant('errors.loadFailed'));
                        this.loadingInitial.set(false);
                        console.error('Error loading page:', err);
                    }
                });
            },
            error: (err) => {
                this.error.set(this.translate.instant('errors.loadFailed'));
                this.loadingInitial.set(false);
                console.error('Error loading deck and cards:', err);

                // Clear progress for failed deck
                this.progressService.clearProgress(deckId);
            }
        });
    }

    /**
     * Load a specific page of cards and add to cache
     * @param page - Page number to load
     * @param deckId - Deck ID
     * @returns Observable that completes when page is loaded
     */
    private loadPage(page: number, deckId: string): Observable<void> {
        // Check if page is already loaded
        if (this.loadedPages().has(page)) {
            return of(void 0);
        }

        return this.cardService.getCardsPage(deckId, page, this.pageSize()).pipe(
            map(response => {
                // Add cards to cache
                const cache = new Map(this.cardsCache());
                cache.set(page, response.items);
                this.cardsCache.set(cache);

                // Mark page as loaded
                const loaded = new Set(this.loadedPages());
                loaded.add(page);
                this.loadedPages.set(loaded);

                // Evict old pages if cache is too large (LRU)
                this.evictOldPages();

                return void 0;
            }),
            catchError(err => {
                console.error(`Error loading page ${page}:`, err);
                throw err;
            })
        );
    }

    /**
     * Update the current cards signal with cards from the current page
     */
    private updateCurrentCards(): void {
        const cache = this.cardsCache();
        const page = this.currentPage();
        const pageCards = cache.get(page) || [];
        this.cards.set(pageCards);
    }

    /**
     * Prefetch adjacent pages in the background for smooth navigation
     * @param deckId - Deck ID
     */
    private prefetchAdjacentPages(deckId: string): void {
        const currentPage = this.currentPage();
        const totalPages = this.totalPages();
        const pagesToPrefetch: number[] = [];

        // Prefetch next page
        if (currentPage + 1 < totalPages && !this.loadedPages().has(currentPage + 1)) {
            pagesToPrefetch.push(currentPage + 1);
        }

        // Prefetch previous page
        if (currentPage - 1 >= 0 && !this.loadedPages().has(currentPage - 1)) {
            pagesToPrefetch.push(currentPage - 1);
        }

        // Load all pages in parallel
        if (pagesToPrefetch.length > 0) {
            const prefetchObservables = pagesToPrefetch.map(page =>
                this.loadPage(page, deckId).pipe(catchError(() => of(void 0)))
            );
            forkJoin(prefetchObservables).subscribe();
        }
    }

    /**
     * Evict old pages from cache to limit memory usage (LRU)
     * Keeps max 5 pages in cache, prioritizing pages near current page
     */
    private evictOldPages(): void {
        const maxCachePages = 5;
        const cache = this.cardsCache();
        const loaded = this.loadedPages();

        if (loaded.size > maxCachePages) {
            const currentPage = this.currentPage();
            const pages = Array.from(loaded).sort((a, b) => {
                // Sort by distance from current page (furthest first)
                const distA = Math.abs(a - currentPage);
                const distB = Math.abs(b - currentPage);
                return distB - distA;
            });

            // Remove pages furthest from current page
            const pagesToRemove = pages.slice(0, pages.length - maxCachePages);
            const newCache = new Map(cache);
            const newLoaded = new Set(loaded);

            pagesToRemove.forEach(page => {
                newCache.delete(page);
                newLoaded.delete(page);
            });

            this.cardsCache.set(newCache);
            this.loadedPages.set(newLoaded);
        }
    }

    /**
     * Save current progress to localStorage
     */
    private saveProgress(): void {
        const deckId = this.deckId();
        const totalCards = this.totalCards();
        const currentCard = this.currentCard();

        if (deckId && totalCards > 0) {
            this.progressService.saveProgress(
                deckId,
                this.globalCardIndex(),
                totalCards,
                this.deckTitle(),
                currentCard?.id
            );
        }
    }

    /**
     * Navigate to the next flashcard
     * Handles page transitions when reaching end of current page
     */
    nextCard(): void {
        if (this.isLastCard()) {
            return;
        }

        // If a page is loading, queue the navigation
        if (this.loadingPage()) {
            this.navigationQueue.push('next');
            return;
        }

        const currentPageSize = this.cards().length;
        const isLastCardInPage = this.currentIndex() === currentPageSize - 1;

        if (isLastCardInPage) {
            // Need to load next page
            const nextPage = this.currentPage() + 1;
            this.loadingPage.set(true);

            this.loadPage(nextPage, this.deckId()).subscribe({
                next: () => {
                    this.currentPage.set(nextPage);
                    this.currentIndex.set(0);
                    this.updateCurrentCards();
                    this.showAnswer.set(false);
                    this.animationTrigger.update(v => v + 1);
                    this.loadingPage.set(false);
                    this.saveProgress();

                    // Prefetch adjacent pages
                    this.prefetchAdjacentPages(this.deckId());

                    // Process queued navigation
                    this.processNavigationQueue();
                },
                error: (err) => {
                    this.loadingPage.set(false);
                    this.navigationQueue = []; // Clear queue on error
                    this.error.set(this.translate.instant('errors.loadFailed'));
                    console.error('Error loading next page:', err);
                }
            });
        } else {
            // Stay on current page, just move to next card
            this.currentIndex.update(i => i + 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v + 1);
            this.saveProgress();
        }
    }

    /**
     * Navigate to the previous flashcard
     * Handles page transitions when reaching start of current page
     */
    previousCard(): void {
        if (this.isFirstCard()) {
            return;
        }

        // If a page is loading, queue the navigation
        if (this.loadingPage()) {
            this.navigationQueue.push('prev');
            return;
        }

        const isFirstCardInPage = this.currentIndex() === 0;

        if (isFirstCardInPage) {
            // Need to load previous page
            const prevPage = this.currentPage() - 1;
            this.loadingPage.set(true);

            this.loadPage(prevPage, this.deckId()).subscribe({
                next: () => {
                    this.currentPage.set(prevPage);
                    // Get the cards from the previous page and set index to last card
                    const prevPageCards = this.cardsCache().get(prevPage) || [];
                    this.currentIndex.set(prevPageCards.length - 1);
                    this.updateCurrentCards();
                    this.showAnswer.set(false);
                    this.animationTrigger.update(v => v - 1);
                    this.loadingPage.set(false);
                    this.saveProgress();

                    // Prefetch adjacent pages
                    this.prefetchAdjacentPages(this.deckId());

                    // Process queued navigation
                    this.processNavigationQueue();
                },
                error: (err) => {
                    this.loadingPage.set(false);
                    this.navigationQueue = []; // Clear queue on error
                    this.error.set(this.translate.instant('errors.loadFailed'));
                    console.error('Error loading previous page:', err);
                }
            });
        } else {
            // Stay on current page, just move to previous card
            this.currentIndex.update(i => i - 1);
            this.showAnswer.set(false);
            this.animationTrigger.update(v => v - 1);
            this.saveProgress();
        }
    }

    /**
     * Process queued navigation actions after page load completes
     * Processes one navigation at a time to prevent overwhelming the system
     */
    private processNavigationQueue(): void {
        if (this.navigationQueue.length === 0) {
            return;
        }

        // Take only the last action from the queue (user's final intended direction)
        const action = this.navigationQueue[this.navigationQueue.length - 1];
        this.navigationQueue = [];

        // Execute the queued action
        if (action === 'next') {
            this.nextCard();
        } else {
            this.previousCard();
        }
    }

    /**
     * Reset progress and start from the beginning
     */
    resetProgress(): void {
        const deckId = this.deckId();
        if (deckId) {
            this.progressService.clearProgress(deckId);

            // If not on page 0, load it
            if (this.currentPage() !== 0) {
                this.loadingPage.set(true);
                this.loadPage(0, deckId).subscribe({
                    next: () => {
                        this.currentPage.set(0);
                        this.currentIndex.set(0);
                        this.updateCurrentCards();
                        this.showAnswer.set(false);
                        this.resumedFromProgress.set(false);
                        this.loadingPage.set(false);
                    },
                    error: (err) => {
                        this.loadingPage.set(false);
                        console.error('Error loading first page:', err);
                    }
                });
            } else {
                // Already on page 0, just reset index
                this.currentIndex.set(0);
                this.showAnswer.set(false);
                this.resumedFromProgress.set(false);
            }
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
