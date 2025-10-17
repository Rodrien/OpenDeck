/**
 * Represents an individual flashcard with question, answer, and source attribution
 *
 * Source attribution is CRITICAL per OpenDeck requirements - it allows users
 * to verify and corroborate AI-generated content against original documents.
 */
export interface FlashCardData {
    id: number;
    question: string;
    answer: string;
    source: string; // Document name, page/section reference
    sourceUrl?: string; // Optional link to the actual document/section
}

/**
 * Represents the navigation direction for card animations
 */
export type CardDirection = -1 | 0 | 1;
