import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { of, throwError } from 'rxjs';
import { FlashcardViewerComponent } from './flashcard-viewer.component';
import { DeckService } from '../../services/deck.service';
import { CardService } from '../../services/card.service';
import { DeckProgressService } from '../../services/deck-progress.service';
import { Card } from '../../models/card.model';
import { Deck } from '../../models/deck.model';
import { PaginatedResponse } from '../../models/api-response.model';
import { provideAnimations } from '@angular/platform-browser/animations';

describe('FlashcardViewerComponent', () => {
    let component: FlashcardViewerComponent;
    let fixture: ComponentFixture<FlashcardViewerComponent>;
    let deckService: jasmine.SpyObj<DeckService>;
    let cardService: jasmine.SpyObj<CardService>;
    let progressService: jasmine.SpyObj<DeckProgressService>;
    let router: jasmine.SpyObj<Router>;
    let translateService: jasmine.SpyObj<TranslateService>;

    const mockDeckId = 'test-deck-id';
    const mockDeck: Deck = {
        id: mockDeckId,
        title: 'Test Deck',
        description: 'Test Description',
        topic_id: 'topic-1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
    };

    const createMockCards = (count: number, startId: number = 0): Card[] => {
        return Array.from({ length: count }, (_, i) => ({
            id: `card-${startId + i}`,
            deck_id: mockDeckId,
            question: `Question ${startId + i + 1}`,
            answer: `Answer ${startId + i + 1}`,
            source: `Source ${startId + i + 1}`,
            source_url: '#',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
        }));
    };

    const createMockPaginatedResponse = (items: Card[], total: number, page: number = 0, pageSize: number = 10): PaginatedResponse<Card> => {
        return {
            items,
            total,
            limit: pageSize,
            offset: page * pageSize
        };
    };

    beforeEach(async () => {
        const deckServiceSpy = jasmine.createSpyObj('DeckService', ['getById']);
        const cardServiceSpy = jasmine.createSpyObj('CardService', ['getCardsPage']);
        const progressServiceSpy = jasmine.createSpyObj('DeckProgressService', ['getProgress', 'saveProgress', 'clearProgress']);
        const routerSpy = jasmine.createSpyObj('Router', ['navigate']);
        const translateServiceSpy = jasmine.createSpyObj('TranslateService', ['instant']);

        translateServiceSpy.instant.and.returnValue('Translated text');

        await TestBed.configureTestingModule({
            imports: [
                FlashcardViewerComponent,
                TranslateModule.forRoot()
            ],
            providers: [
                { provide: DeckService, useValue: deckServiceSpy },
                { provide: CardService, useValue: cardServiceSpy },
                { provide: DeckProgressService, useValue: progressServiceSpy },
                { provide: Router, useValue: routerSpy },
                { provide: TranslateService, useValue: translateServiceSpy },
                {
                    provide: ActivatedRoute,
                    useValue: {
                        snapshot: {
                            paramMap: {
                                get: (key: string) => key === 'deckId' ? mockDeckId : null
                            }
                        }
                    }
                },
                provideAnimations()
            ]
        }).compileComponents();

        deckService = TestBed.inject(DeckService) as jasmine.SpyObj<DeckService>;
        cardService = TestBed.inject(CardService) as jasmine.SpyObj<CardService>;
        progressService = TestBed.inject(DeckProgressService) as jasmine.SpyObj<DeckProgressService>;
        router = TestBed.inject(Router) as jasmine.SpyObj<Router>;
        translateService = TestBed.inject(TranslateService) as jasmine.SpyObj<TranslateService>;

        fixture = TestBed.createComponent(FlashcardViewerComponent);
        component = fixture.componentInstance;
    });

    describe('Initialization', () => {
        it('should create', () => {
            expect(component).toBeTruthy();
        });

        it('should load deck and first page on init', (done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                expect(deckService.getById).toHaveBeenCalledWith(mockDeckId);
                expect(cardService.getCardsPage).toHaveBeenCalledWith(mockDeckId, 0, 10);
                expect(component.deckTitle()).toBe('Test Deck');
                expect(component.totalCards()).toBe(25);
                expect(component.cards().length).toBe(10);
                expect(component.currentPage()).toBe(0);
                expect(component.currentIndex()).toBe(0);
                done();
            }, 100);
        });

        it('should navigate back if no deckId provided', () => {
            TestBed.resetTestingModule();
            TestBed.configureTestingModule({
                imports: [FlashcardViewerComponent, TranslateModule.forRoot()],
                providers: [
                    { provide: DeckService, useValue: deckService },
                    { provide: CardService, useValue: cardService },
                    { provide: DeckProgressService, useValue: progressService },
                    { provide: Router, useValue: router },
                    { provide: TranslateService, useValue: translateService },
                    {
                        provide: ActivatedRoute,
                        useValue: {
                            snapshot: {
                                paramMap: {
                                    get: () => null
                                }
                            }
                        }
                    },
                    provideAnimations()
                ]
            });

            const newFixture = TestBed.createComponent(FlashcardViewerComponent);
            newFixture.detectChanges();

            expect(router.navigate).toHaveBeenCalledWith(['/pages/flashcards']);
        });

        it('should show error when deck has no cards', (done) => {
            const mockResponse = createMockPaginatedResponse([], 0);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                expect(component.error()).toBeTruthy();
                expect(component.totalCards()).toBe(0);
                done();
            }, 100);
        });
    });

    describe('Progress Restoration', () => {
        it('should restore progress to correct page and card', (done) => {
            const mockCardsPage0 = createMockCards(10, 0);
            const mockCardsPage2 = createMockCards(10, 20);
            const mockResponsePage0 = createMockPaginatedResponse(mockCardsPage0, 50, 0);
            const mockResponsePage2 = createMockPaginatedResponse(mockCardsPage2, 50, 2);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.callFake((deckId, page) => {
                if (page === 0) return of(mockResponsePage0);
                if (page === 2) return of(mockResponsePage2);
                return of(mockResponsePage0);
            });

            // Saved progress at card index 25 (page 2, index 5)
            progressService.getProgress.and.returnValue({
                deckId: mockDeckId,
                currentCardIndex: 25,
                currentCardId: 'card-25',
                totalCards: 50,
                timestamp: Date.now(),
                deckTitle: 'Test Deck'
            });

            fixture.detectChanges();

            setTimeout(() => {
                expect(component.currentPage()).toBe(2);
                expect(component.currentIndex()).toBe(5);
                expect(component.resumedFromProgress()).toBe(true);
                done();
            }, 100);
        });

        it('should handle progress when total cards changed', (done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 30);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));

            // Saved progress has more cards than current deck
            progressService.getProgress.and.returnValue({
                deckId: mockDeckId,
                currentCardIndex: 50,
                totalCards: 60,
                timestamp: Date.now()
            });

            fixture.detectChanges();

            setTimeout(() => {
                // Should cap at last available card
                expect(component.globalCardIndex()).toBeLessThan(30);
                done();
            }, 100);
        });
    });

    describe('Pagination Logic', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => done(), 100);
        });

        it('should calculate total pages correctly', () => {
            expect(component.totalPages()).toBe(3); // 25 cards / 10 per page = 3 pages
        });

        it('should calculate global card index correctly', () => {
            component.currentPage.set(2);
            component.currentIndex.set(4);

            expect(component.globalCardIndex()).toBe(24); // (2 * 10) + 4 = 24
        });

        it('should identify first card correctly', () => {
            component.currentPage.set(0);
            component.currentIndex.set(0);

            expect(component.isFirstCard()).toBe(true);

            component.currentIndex.set(1);
            expect(component.isFirstCard()).toBe(false);
        });

        it('should identify last card correctly', () => {
            component.totalCards.set(25);
            component.currentPage.set(2);
            component.currentIndex.set(4); // Global index 24, which is the last card (0-indexed)

            expect(component.isLastCard()).toBe(true);

            component.currentIndex.set(3);
            expect(component.isLastCard()).toBe(false);
        });
    });

    describe('Navigation - Next Card', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => done(), 100);
        });

        it('should move to next card on same page', () => {
            const initialIndex = component.currentIndex();
            component.nextCard();

            expect(component.currentIndex()).toBe(initialIndex + 1);
            expect(component.currentPage()).toBe(0);
        });

        it('should load next page at page boundary', (done) => {
            const mockCardsPage1 = createMockCards(10, 10);
            const mockResponsePage1 = createMockPaginatedResponse(mockCardsPage1, 25, 1);

            cardService.getCardsPage.and.returnValue(of(mockResponsePage1));

            // Move to last card of page 0
            component.currentIndex.set(9);
            component.nextCard();

            setTimeout(() => {
                expect(component.currentPage()).toBe(1);
                expect(component.currentIndex()).toBe(0);
                done();
            }, 100);
        });

        it('should not navigate beyond last card', () => {
            component.currentPage.set(2);
            component.currentIndex.set(4);
            component.totalCards.set(25);

            const initialPage = component.currentPage();
            const initialIndex = component.currentIndex();

            component.nextCard();

            expect(component.currentPage()).toBe(initialPage);
            expect(component.currentIndex()).toBe(initialIndex);
        });

        it('should queue navigation when page is loading', (done) => {
            const mockCardsPage1 = createMockCards(10, 10);
            const mockResponsePage1 = createMockPaginatedResponse(mockCardsPage1, 25, 1);

            cardService.getCardsPage.and.returnValue(of(mockResponsePage1));

            // Move to last card to trigger page load
            component.currentIndex.set(9);
            component.nextCard();

            // Try to navigate again immediately (while loading)
            component.nextCard();

            setTimeout(() => {
                // Should be on page 1, card 1 (not card 0) because queued navigation was processed
                expect(component.currentPage()).toBe(1);
                expect(component.currentIndex()).toBe(1);
                done();
            }, 150);
        });
    });

    describe('Navigation - Previous Card', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                component.currentIndex.set(5);
                done();
            }, 100);
        });

        it('should move to previous card on same page', () => {
            const initialIndex = component.currentIndex();
            component.previousCard();

            expect(component.currentIndex()).toBe(initialIndex - 1);
            expect(component.currentPage()).toBe(0);
        });

        it('should load previous page at page boundary', (done) => {
            const mockCardsPage0 = createMockCards(10, 0);
            const mockCardsPage1 = createMockCards(10, 10);
            const mockResponsePage0 = createMockPaginatedResponse(mockCardsPage0, 25, 0);
            const mockResponsePage1 = createMockPaginatedResponse(mockCardsPage1, 25, 1);

            // Start on page 1
            cardService.getCardsPage.and.callFake((deckId, page) => {
                if (page === 0) return of(mockResponsePage0);
                if (page === 1) return of(mockResponsePage1);
                return of(mockResponsePage0);
            });

            component.currentPage.set(1);
            component.currentIndex.set(0);
            component.cards.set(mockCardsPage1);

            component.previousCard();

            setTimeout(() => {
                expect(component.currentPage()).toBe(0);
                expect(component.currentIndex()).toBe(9); // Last card of previous page
                done();
            }, 100);
        });

        it('should not navigate before first card', () => {
            component.currentPage.set(0);
            component.currentIndex.set(0);

            const initialPage = component.currentPage();
            const initialIndex = component.currentIndex();

            component.previousCard();

            expect(component.currentPage()).toBe(initialPage);
            expect(component.currentIndex()).toBe(initialIndex);
        });
    });

    describe('LRU Cache Management', () => {
        it('should evict old pages when cache exceeds limit', (done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 100);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                // Manually load 6 pages to trigger eviction
                const loadedPages = new Set([0, 1, 2, 3, 4, 5]);
                component.loadedPages.set(loadedPages);

                const cache = new Map();
                for (let i = 0; i <= 5; i++) {
                    cache.set(i, createMockCards(10, i * 10));
                }
                component.cardsCache.set(cache);

                component.currentPage.set(5);

                // Trigger eviction by calling the private method via component logic
                // This happens automatically in loadPage, but we can test the effect
                component['evictOldPages']();

                // Should keep max 5 pages
                expect(component.loadedPages().size).toBeLessThanOrEqual(5);

                // Should keep pages close to current page (5)
                expect(component.loadedPages().has(5)).toBe(true);

                done();
            }, 100);
        });
    });

    describe('Error Handling', () => {
        it('should handle deck load error', (done) => {
            deckService.getById.and.returnValue(throwError(() => new Error('Network error')));
            cardService.getCardsPage.and.returnValue(of(createMockPaginatedResponse([], 0)));

            fixture.detectChanges();

            setTimeout(() => {
                expect(component.error()).toBeTruthy();
                expect(component.loadingInitial()).toBe(false);
                done();
            }, 100);
        });

        it('should handle page load error and clear queue', (done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.callFake((deckId, page) => {
                if (page === 0) return of(mockResponse);
                return throwError(() => new Error('Page load error'));
            });

            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                component.currentIndex.set(9);
                component.nextCard();

                setTimeout(() => {
                    expect(component.error()).toBeTruthy();
                    expect(component.loadingPage()).toBe(false);
                    done();
                }, 100);
            }, 100);
        });
    });

    describe('Progress Saving', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => done(), 100);
        });

        it('should save progress with card ID when navigating', () => {
            component.nextCard();

            expect(progressService.saveProgress).toHaveBeenCalledWith(
                mockDeckId,
                jasmine.any(Number),
                jasmine.any(Number),
                jasmine.any(String),
                jasmine.any(String)
            );
        });

        it('should save progress on destroy', () => {
            progressService.saveProgress.calls.reset();

            component.ngOnDestroy();

            expect(progressService.saveProgress).toHaveBeenCalled();
        });
    });

    describe('Reset Progress', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => {
                component.currentPage.set(2);
                component.currentIndex.set(5);
                done();
            }, 100);
        });

        it('should reset to first card when on different page', (done) => {
            cardService.getCardsPage.and.returnValue(of(createMockPaginatedResponse(createMockCards(10), 25, 0)));

            component.resetProgress();

            setTimeout(() => {
                expect(progressService.clearProgress).toHaveBeenCalledWith(mockDeckId);
                expect(component.currentPage()).toBe(0);
                expect(component.currentIndex()).toBe(0);
                expect(component.resumedFromProgress()).toBe(false);
                done();
            }, 100);
        });

        it('should reset to first card when already on page 0', () => {
            component.currentPage.set(0);
            component.currentIndex.set(5);

            component.resetProgress();

            expect(progressService.clearProgress).toHaveBeenCalledWith(mockDeckId);
            expect(component.currentIndex()).toBe(0);
            expect(component.resumedFromProgress()).toBe(false);
        });
    });

    describe('Answer Toggle', () => {
        it('should toggle answer visibility', () => {
            expect(component.showAnswer()).toBe(false);

            component.toggleAnswer();
            expect(component.showAnswer()).toBe(true);

            component.toggleAnswer();
            expect(component.showAnswer()).toBe(false);
        });

        it('should hide answer when navigating to next card', () => {
            component.showAnswer.set(true);
            component.nextCard();

            expect(component.showAnswer()).toBe(false);
        });
    });

    describe('Keyboard Navigation', () => {
        beforeEach((done) => {
            const mockCards = createMockCards(10);
            const mockResponse = createMockPaginatedResponse(mockCards, 25);

            deckService.getById.and.returnValue(of(mockDeck));
            cardService.getCardsPage.and.returnValue(of(mockResponse));
            progressService.getProgress.and.returnValue(null);

            fixture.detectChanges();

            setTimeout(() => done(), 100);
        });

        it('should navigate to next card on ArrowRight', () => {
            const event = new KeyboardEvent('keydown', { key: 'ArrowRight' });
            spyOn(event, 'preventDefault');

            const initialIndex = component.currentIndex();
            component.handleKeyboardEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
            expect(component.currentIndex()).toBe(initialIndex + 1);
        });

        it('should navigate to previous card on ArrowLeft', () => {
            component.currentIndex.set(5);
            const event = new KeyboardEvent('keydown', { key: 'ArrowLeft' });
            spyOn(event, 'preventDefault');

            component.handleKeyboardEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
            expect(component.currentIndex()).toBe(4);
        });

        it('should toggle answer on Space', () => {
            const event = new KeyboardEvent('keydown', { key: ' ' });
            spyOn(event, 'preventDefault');

            component.handleKeyboardEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
            expect(component.showAnswer()).toBe(true);
        });

        it('should navigate back on Escape', () => {
            const event = new KeyboardEvent('keydown', { key: 'Escape' });
            spyOn(event, 'preventDefault');

            component.handleKeyboardEvent(event);

            expect(event.preventDefault).toHaveBeenCalled();
            expect(router.navigate).toHaveBeenCalledWith(['/pages/flashcards']);
        });
    });
});
