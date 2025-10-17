import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';

// PrimeNG Imports
import { Card } from 'primeng/card';
import { InputText } from 'primeng/inputtext';
import { IconField } from 'primeng/iconfield';
import { InputIcon } from 'primeng/inputicon';
import { Badge } from 'primeng/badge';
import { Button } from 'primeng/button';

// Models
import { Deck, DeckStats } from './models/deck.interface';

@Component({
    selector: 'app-flashcard-decks-list',
    imports: [
        CommonModule,
        FormsModule,
        Card,
        InputText,
        IconField,
        InputIcon,
        Badge,
        Button
    ],
    templateUrl: './flashcard-decks-list.component.html',
    styleUrls: ['./flashcard-decks-list.component.scss']
})
export class FlashcardDecksListComponent {
    // Signals for reactive state management
    searchQuery = signal<string>('');

    // Mock data - matches the Figma design
    readonly mockDecks: Deck[] = [
        {
            id: 1,
            title: 'Introduction to Computer Science',
            description: 'Fundamental concepts of programming, algorithms, and data structures.',
            cardCount: 25,
            category: 'Computer Science',
            difficulty: 'Beginner',
            icon: 'pi-code'
        },
        {
            id: 2,
            title: 'Organic Chemistry Basics',
            description: 'Essential organic chemistry concepts including functional groups and reactions.',
            cardCount: 30,
            category: 'Chemistry',
            difficulty: 'Intermediate',
            icon: 'pi-flask'
        },
        {
            id: 3,
            title: 'Calculus I: Derivatives',
            description: 'Understanding derivatives, limits, and their applications.',
            cardCount: 28,
            category: 'Mathematics',
            difficulty: 'Intermediate',
            icon: 'pi-calculator'
        },
        {
            id: 4,
            title: 'World History: Ancient Civilizations',
            description: 'Exploring ancient civilizations from Mesopotamia to Rome.',
            cardCount: 35,
            category: 'History',
            difficulty: 'Beginner',
            icon: 'pi-globe'
        },
        {
            id: 5,
            title: 'Microeconomics Principles',
            description: 'Supply and demand, market structures, and consumer behavior.',
            cardCount: 22,
            category: 'Economics',
            difficulty: 'Intermediate',
            icon: 'pi-chart-line'
        },
        {
            id: 6,
            title: 'Data Structures & Algorithms',
            description: 'Advanced data structures, sorting algorithms, and complexity analysis.',
            cardCount: 40,
            category: 'Computer Science',
            difficulty: 'Advanced',
            icon: 'pi-sitemap'
        }
    ];

    // Computed filtered decks based on search query
    filteredDecks = computed(() => {
        const query = this.searchQuery().toLowerCase().trim();

        if (!query) {
            return this.mockDecks;
        }

        return this.mockDecks.filter(deck =>
            deck.title.toLowerCase().includes(query) ||
            deck.category.toLowerCase().includes(query) ||
            deck.description.toLowerCase().includes(query)
        );
    });

    // Computed stats
    stats = computed<DeckStats>(() => {
        const decks = this.filteredDecks();
        const categories = new Map<string, number>();

        decks.forEach(deck => {
            categories.set(deck.category, (categories.get(deck.category) || 0) + 1);
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
            totalCards: decks.reduce((sum, deck) => sum + deck.cardCount, 0)
        };
    });

    constructor(private router: Router) {}

    /**
     * Navigate to the flashcard viewer for the selected deck
     */
    onDeckSelect(deck: Deck): void {
        this.router.navigate(['/pages/flashcards/viewer', deck.id]);
    }

    /**
     * Get the appropriate severity for the difficulty badge
     */
    getDifficultySeverity(difficulty: Deck['difficulty']): 'success' | 'warn' | 'danger' {
        switch (difficulty) {
            case 'Beginner':
                return 'success';
            case 'Intermediate':
                return 'warn';
            case 'Advanced':
                return 'danger';
            default:
                return 'success';
        }
    }

    /**
     * Get the appropriate icon for a category
     */
    getCategoryIcon(category: string): string {
        const deck = this.mockDecks.find(d => d.category === category);
        return deck?.icon || 'pi-book';
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
