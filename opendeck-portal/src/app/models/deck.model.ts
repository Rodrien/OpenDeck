import { Topic } from './topic.model';

/**
 * Difficulty Level
 * Represents the difficulty of a deck
 */
export type DifficultyLevel = 'beginner' | 'intermediate' | 'advanced';

/**
 * Deck Model
 * Represents a collection of flashcards
 */
export interface Deck {
  id: string;
  user_id: string;
  title: string;
  description: string | null;
  category: string | null;
  difficulty: DifficultyLevel | null;
  card_count: number;
  topics: Topic[];
  created_at: string;
  updated_at: string;
}

/**
 * Create Deck DTO
 * Used when creating a new deck
 */
export interface CreateDeckDto {
  title: string;
  description?: string;
  category?: string;
  difficulty?: DifficultyLevel;
  topic_ids?: string[];
}

/**
 * Update Deck DTO
 * Used when updating an existing deck
 */
export interface UpdateDeckDto {
  title?: string;
  description?: string;
  category?: string;
  difficulty?: DifficultyLevel;
  topic_ids?: string[];
}

/**
 * Deck Filter Params
 * Query parameters for filtering decks
 */
export interface DeckFilterParams {
  category?: string;
  difficulty?: DifficultyLevel;
  topic_id?: string;
  limit?: number;
  offset?: number;
}
