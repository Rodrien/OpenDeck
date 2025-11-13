/**
 * Card Report Models
 * Models for reporting flashcards with incorrect, misleading, or unhelpful information
 */

/**
 * Report Status Enum
 * Tracks the lifecycle of a card report
 */
export enum ReportStatus {
  PENDING = 'pending',
  REVIEWED = 'reviewed',
  RESOLVED = 'resolved',
  DISMISSED = 'dismissed'
}

/**
 * Card Report Interface
 * Represents a report submitted by a user about a flashcard
 */
export interface CardReport {
  id: string;
  cardId: string;
  userId: string;
  reason: string;
  status: ReportStatus;
  createdAt: Date;
  updatedAt: Date;
  reviewedBy?: string;
  reviewedAt?: Date;
}

/**
 * Create Card Report DTO
 * Data required to create a new card report
 */
export interface CardReportCreate {
  reason: string;
}
