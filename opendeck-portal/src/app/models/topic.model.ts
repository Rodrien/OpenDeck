/**
 * Topic Model
 * Represents a subject or category for organizing flashcards
 */
export interface Topic {
  id: string;
  name: string;
  description: string | null;
}

/**
 * Create Topic DTO
 * Used when creating a new topic
 */
export interface CreateTopicDto {
  name: string;
  description?: string;
}

/**
 * Update Topic DTO
 * Used when updating an existing topic
 */
export interface UpdateTopicDto {
  name?: string;
  description?: string;
}
