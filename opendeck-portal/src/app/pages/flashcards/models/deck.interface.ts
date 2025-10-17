export interface Deck {
    id: number;
    title: string;
    description: string;
    cardCount: number;
    category: string;
    difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
    icon?: string; // PrimeIcons class name
}

export interface DeckStats {
    availableDecks: number;
    mostPopularCategory: string;
    categoryCount: number;
    totalCards: number;
}
