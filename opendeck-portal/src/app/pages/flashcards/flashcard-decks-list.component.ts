import { Component, computed, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { InputText } from 'primeng/inputtext';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { Badge } from 'primeng/badge';
import { Button } from 'primeng/button';
import { ProgressSpinner } from 'primeng/progressspinner';
import { Message } from 'primeng/message';

// Services
import { DeckService } from '../../services/deck.service';
import { TranslateService } from '@ngx-translate/core';

// Models
import { Deck as ApiDeck, DifficultyLevel } from '../../models/deck.model';
import { DeckStats } from './models/deck.interface';

@Component({
    selector: 'app-flashcard-decks-list',
    imports: [
        CommonModule,
        FormsModule,
        TranslateModule,
        Card,
        InputText,
        IconField,
        InputIcon,
        Badge,
        Button,
        ProgressSpinner,
        Message
    ],
    templateUrl: './flashcard-decks-list.component.html',
    styleUrls: ['./flashcard-decks-list.component.scss']
})
export class FlashcardDecksListComponent implements OnInit {
    // Signals for reactive state management
    searchQuery = signal<string>('');
    decks = signal<ApiDeck[]>([]);
    loading = signal<boolean>(false);
    error = signal<string | null>(null);

    // Computed filtered decks based on search query
    filteredDecks = computed(() => {
        const query = this.searchQuery().toLowerCase().trim();
        const allDecks = this.decks();

        if (!query) {
            return allDecks;
        }

        return allDecks.filter(deck =>
            deck.title.toLowerCase().includes(query) ||
            (deck.category && deck.category.toLowerCase().includes(query)) ||
            (deck.description && deck.description.toLowerCase().includes(query))
        );
    });

    // Computed stats
    stats = computed<DeckStats>(() => {
        const decks = this.filteredDecks();
        const categories = new Map<string, number>();

        decks.forEach(deck => {
            if (deck.category) {
                categories.set(deck.category, (categories.get(deck.category) || 0) + 1);
            }
        });

        let mostPopular = 'N/A';
        let maxCount = 0;
        categories.forEach((count, category) => {
            if (count > maxCount) {
                maxCount = count;
                mostPopular = category;
            }
        });

        return {
            availableDecks: decks.length,
            mostPopularCategory: mostPopular,
            categoryCount: categories.size,
            totalCards: decks.reduce((sum, deck) => sum + deck.card_count, 0)
        };
    });

    constructor(
        private router: Router,
        private deckService: DeckService,
        private translate: TranslateService
    ) {}

    ngOnInit(): void {
        this.loadDecks();
    }

    /**
     * Load all decks from the API
     * Public method to allow retry from template
     */
    loadDecks(): void {
        this.loading.set(true);
        this.error.set(null);

        this.deckService.getAll({ limit: 100 }).subscribe({
            next: (response) => {
                this.decks.set(response.items);
                this.loading.set(false);
            },
            error: (err) => {
                this.error.set(this.translate.instant('errors.loadFailed'));
                this.loading.set(false);
                console.error('Error loading decks:', err);
            }
        });
    }

    /**
     * Navigate to the flashcard viewer for the selected deck
     */
    onDeckSelect(deck: ApiDeck): void {
        this.router.navigate(['/pages/flashcards/viewer', deck.id]);
    }

    /**
     * Get the appropriate severity for the difficulty badge
     * Backend returns lowercase difficulty values
     */
    getDifficultySeverity(difficulty: DifficultyLevel | null): 'success' | 'warn' | 'danger' {
        if (!difficulty) {
            return 'success';
        }

        switch (difficulty.toLowerCase()) {
            case 'beginner':
                return 'success';
            case 'intermediate':
                return 'warn';
            case 'advanced':
                return 'danger';
            default:
                return 'success';
        }
    }

    /**
     * Format difficulty for display with translation
     */
    formatDifficulty(difficulty: DifficultyLevel | null): string {
        if (!difficulty) {
            return 'N/A';
        }

        const translationKey = `deck.difficulty.${difficulty.toLowerCase()}`;
        return this.translate.instant(translationKey);
    }

    /**
     * Get the appropriate icon for a category
     * Maps category names to PrimeIcons
     */
    getCategoryIcon(category: string | null): string {
        if (!category) {
            return 'pi-book';
        }

        const iconMap: { [key: string]: string } = {
            'Computer Science': 'pi-code',
            'Chemistry': 'pi-flask',
            'Mathematics': 'pi-calculator',
            'History': 'pi-globe',
            'Economics': 'pi-chart-line',
            'Physics': 'pi-bolt',
            'Biology': 'pi-leaf',
            'Literature': 'pi-book',
            'Art': 'pi-palette',
            'Music': 'pi-volume-up',
            'default': 'pi-book'
        };

        return iconMap[category] || iconMap['default'];
    }

    /**
     * Update search query
     */
    onSearchChange(event: Event): void {
        const input = event.target as HTMLInputElement;
        this.searchQuery.set(input.value);
    }

    /**
     * Clear search query
     */
    clearSearch(): void {
        this.searchQuery.set('');
    }
}
