import { Injectable } from '@angular/core';

export interface DeckProgress {
  deckId: string;
  currentCardIndex: number;
  currentCardId?: string; // Card ID for better restoration accuracy
  totalCards: number;
  timestamp: number;
  deckTitle?: string;
}

interface DeckProgressMap {
  [deckId: string]: DeckProgress;
}

@Injectable({
  providedIn: 'root'
})
export class DeckProgressService {
  private readonly STORAGE_KEY = 'opendeck-deck-progress';
  private readonly MAX_AGE_DAYS = 30;

  constructor() {}

  /**
   * Save progress for a specific deck
   */
  saveProgress(
    deckId: string,
    cardIndex: number,
    totalCards: number,
    deckTitle?: string,
    cardId?: string
  ): void {
    try {
      const progressMap = this.loadAllProgress();
      const progress: DeckProgress = {
        deckId,
        currentCardIndex: cardIndex,
        currentCardId: cardId,
        totalCards,
        timestamp: Date.now(),
        deckTitle
      };

      progressMap[deckId] = progress;
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(progressMap));
    } catch (error) {
      // Handle quota exceeded or other localStorage errors
      console.warn('Failed to save deck progress:', error);

      // Try to clean up old progress and retry
      try {
        this.cleanupOldProgress(this.MAX_AGE_DAYS);
        const progressMap = this.loadAllProgress();
        progressMap[deckId] = {
          deckId,
          currentCardIndex: cardIndex,
          currentCardId: cardId,
          totalCards,
          timestamp: Date.now(),
          deckTitle
        };
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(progressMap));
      } catch (retryError) {
        console.error('Failed to save deck progress after cleanup:', retryError);
      }
    }
  }

  /**
   * Get progress for a specific deck
   */
  getProgress(deckId: string): DeckProgress | null {
    const progressMap = this.loadAllProgress();
    const progress = progressMap[deckId];

    if (!progress) {
      return null;
    }

    // Check if progress is too old
    const ageInDays = (Date.now() - progress.timestamp) / (1000 * 60 * 60 * 24);
    if (ageInDays > this.MAX_AGE_DAYS) {
      this.clearProgress(deckId);
      return null;
    }

    return progress;
  }

  /**
   * Check if progress exists for a specific deck
   */
  hasProgress(deckId: string): boolean {
    return this.getProgress(deckId) !== null;
  }

  /**
   * Clear progress for a specific deck
   */
  clearProgress(deckId: string): void {
    try {
      const progressMap = this.loadAllProgress();
      delete progressMap[deckId];
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(progressMap));
    } catch (error) {
      console.error('Failed to clear deck progress:', error);
    }
  }

  /**
   * Clear all deck progress
   */
  clearAllProgress(): void {
    try {
      localStorage.removeItem(this.STORAGE_KEY);
    } catch (error) {
      console.error('Failed to clear all deck progress:', error);
    }
  }

  /**
   * Clean up old progress entries (older than specified days)
   */
  cleanupOldProgress(daysThreshold: number = 30): void {
    try {
      const progressMap = this.loadAllProgress();
      const cutoffTime = Date.now() - (daysThreshold * 24 * 60 * 60 * 1000);
      let hasChanges = false;

      for (const deckId in progressMap) {
        if (progressMap[deckId].timestamp < cutoffTime) {
          delete progressMap[deckId];
          hasChanges = true;
        }
      }

      if (hasChanges) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(progressMap));
      }
    } catch (error) {
      console.warn('Failed to cleanup old deck progress:', error);
    }
  }

  /**
   * Load all progress from localStorage
   */
  private loadAllProgress(): DeckProgressMap {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY);
      if (!data) {
        return {};
      }

      const parsed = JSON.parse(data);

      // Validate that the parsed data is an object
      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        console.warn('Invalid deck progress data format, resetting');
        localStorage.removeItem(this.STORAGE_KEY);
        return {};
      }

      return parsed as DeckProgressMap;
    } catch (error) {
      // Handle corrupted data
      console.warn('Failed to load deck progress, corrupted data:', error);
      localStorage.removeItem(this.STORAGE_KEY);
      return {};
    }
  }
}
