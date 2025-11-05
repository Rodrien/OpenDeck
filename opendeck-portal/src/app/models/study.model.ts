import { Card } from './card.model';

/**
 * Session Type
 * Represents different types of study sessions
 */
export type SessionType = 'review' | 'learn_new' | 'cram';

/**
 * Study Card
 * Represents a card during a study session with spaced repetition metadata
 */
export interface StudyCard extends Card {
  // SM-2 algorithm fields
  ease_factor: number;
  interval: number;
  repetitions: number;
  last_review_date: string | null;
  next_review_date: string | null;

  // Study session specific
  is_new: boolean;
  is_due: boolean;
}

/**
 * Card Review
 * Represents a single review of a card during a study session
 */
export interface CardReview {
  card_id: string;
  quality: number; // 0-5 (0=Again, 3=Hard, 4=Good, 5=Easy)
  time_taken_seconds?: number;
  reviewed_at: string;
}

/**
 * Study Session
 * Represents an active or completed study session
 */
export interface StudySession {
  id: string;
  deck_id: string;
  user_id: string;
  session_type: SessionType;

  // Session metadata
  started_at: string;
  completed_at: string | null;

  // Session statistics
  cards_reviewed: number;
  cards_correct: number; // Quality >= 4
  cards_incorrect: number; // Quality < 4
  total_time_seconds: number;

  // Cards in session
  card_ids: string[];
  reviews: CardReview[];

  // Session state
  current_card_index: number;
  is_completed: boolean;
}

/**
 * Start Session Request DTO
 * Used when starting a new study session
 */
export interface StartSessionDto {
  deck_id: string;
  session_type?: SessionType;
  max_cards?: number;
}

/**
 * Record Review Request DTO
 * Used when recording a card review
 */
export interface RecordReviewDto {
  card_id: string;
  quality: number;
  time_taken_seconds?: number;
}

/**
 * Study Statistics
 * Summary statistics for a deck's study progress
 */
export interface StudyStats {
  deck_id: string;
  total_cards: number;
  new_cards: number;
  learning_cards: number;
  review_cards: number;
  due_cards: number;
  next_review_date: string | null;
  average_ease_factor: number;
  completion_rate: number; // Percentage of mastered cards
}

/**
 * Quality Rating
 * Represents the user's performance on a card review
 */
export interface QualityRating {
  value: number;
  label: string;
  icon: string;
  severity: 'danger' | 'warn' | 'info' | 'success';
  description: string;
}

/**
 * Available quality ratings for card reviews
 */
export const QUALITY_RATINGS: QualityRating[] = [
  {
    value: 0,
    label: 'study.again',
    icon: 'pi pi-times',
    severity: 'danger',
    description: 'Complete blackout. Need to relearn.'
  },
  {
    value: 3,
    label: 'study.hard',
    icon: 'pi pi-exclamation-triangle',
    severity: 'warn',
    description: 'Correct response but with difficulty.'
  },
  {
    value: 4,
    label: 'study.good',
    icon: 'pi pi-check',
    severity: 'info',
    description: 'Correct response with hesitation.'
  },
  {
    value: 5,
    label: 'study.easy',
    icon: 'pi pi-check-circle',
    severity: 'success',
    description: 'Perfect response with ease.'
  }
];
