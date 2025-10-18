import { Topic } from './topic.model';

/**
 * Card/FlashCard Model
 * Represents an individual flashcard with question and answer
 */
export interface Card {
  id: number;
  deck_id: number;
  question: string;
  answer: string;
  source: string | null;
  source_url: string | null;
  topics: Topic[];
  created_at: string;
  updated_at: string;
}

/**
 * FlashCard alias
 * Alternative name for Card model
 */
export type FlashCard = Card;

/**
 * Create Card DTO
 * Used when creating a new card
 */
export interface CreateCardDto {
  deck_id: number;
  question: string;
  answer: string;
  source?: string;
  source_url?: string;
  topic_ids?: number[];
}

/**
 * Update Card DTO
 * Used when updating an existing card
 */
export interface UpdateCardDto {
  question?: string;
  answer?: string;
  source?: string;
  source_url?: string;
  topic_ids?: number[];
}

/**
 * Card Filter Params
 * Query parameters for filtering cards
 */
export interface CardFilterParams {
  deck_id?: number;
  topic_id?: number;
  limit?: number;
  offset?: number;
}
