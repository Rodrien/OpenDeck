import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  StudySession,
  StudyCard,
  StartSessionDto,
  RecordReviewDto,
  StudyStats,
  SessionType
} from '../models/study.model';
import { Card } from '../models/card.model';

/**
 * Study Service
 * Handles all spaced repetition and study session operations
 */
@Injectable({
  providedIn: 'root'
})
export class StudyService {
  private readonly apiUrl = `${environment.apiBaseUrl}/study`;

  constructor(private http: HttpClient) {}

  /**
   * Start a new study session for a deck
   * @param deckId - Deck ID (UUID string)
   * @param sessionType - Type of session (review, learn_new, cram)
   * @param maxCards - Maximum number of cards to study (optional)
   * @returns Observable of StudySession
   */
  startSession(
    deckId: string,
    sessionType: SessionType = 'review',
    maxCards?: number
  ): Observable<StudySession> {
    const dto: StartSessionDto = {
      deck_id: deckId,
      session_type: sessionType,
      max_cards: maxCards
    };

    return this.http
      .post<StudySession>(`${this.apiUrl}/sessions`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get current active session for a deck
   * @param deckId - Deck ID (UUID string)
   * @returns Observable of StudySession or null
   */
  getActiveSession(deckId: string): Observable<StudySession | null> {
    return this.http
      .get<StudySession | null>(`${this.apiUrl}/sessions/active/${deckId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get session by ID
   * @param sessionId - Session ID (UUID string)
   * @returns Observable of StudySession
   */
  getSession(sessionId: string): Observable<StudySession> {
    return this.http
      .get<StudySession>(`${this.apiUrl}/sessions/${sessionId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get all cards that are due for review in a deck
   * @param deckId - Deck ID (UUID string)
   * @returns Observable of Card array
   */
  getDueCards(deckId: string): Observable<Card[]> {
    return this.http
      .get<{ cards: Card[] }>(`${this.apiUrl}/decks/${deckId}/due`)
      .pipe(
        map(response => response.cards),
        catchError(this.handleError)
      );
  }

  /**
   * Get study statistics for a deck
   * @param deckId - Deck ID (UUID string)
   * @returns Observable of StudyStats
   */
  getStudyStats(deckId: string): Observable<StudyStats> {
    return this.http
      .get<StudyStats>(`${this.apiUrl}/decks/${deckId}/stats`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Record a card review in the current session
   * @param sessionId - Session ID (UUID string)
   * @param cardId - Card ID (UUID string)
   * @param quality - Quality rating (0-5)
   * @param timeTakenSeconds - Time taken to review (optional)
   * @returns Observable of updated StudySession
   */
  recordReview(
    sessionId: string,
    cardId: string,
    quality: number,
    timeTakenSeconds?: number
  ): Observable<StudySession> {
    const dto: RecordReviewDto = {
      card_id: cardId,
      quality,
      time_taken_seconds: timeTakenSeconds
    };

    return this.http
      .post<StudySession>(
        `${this.apiUrl}/sessions/${sessionId}/reviews`,
        dto
      )
      .pipe(catchError(this.handleError));
  }

  /**
   * End the current study session
   * @param sessionId - Session ID (UUID string)
   * @returns Observable of completed StudySession
   */
  endSession(sessionId: string): Observable<StudySession> {
    return this.http
      .post<StudySession>(`${this.apiUrl}/sessions/${sessionId}/complete`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * Get card details with spaced repetition metadata
   * @param cardId - Card ID (UUID string)
   * @returns Observable of StudyCard
   */
  getStudyCard(cardId: string): Observable<StudyCard> {
    return this.http
      .get<StudyCard>(`${this.apiUrl}/cards/${cardId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Reset spaced repetition progress for a card
   * @param cardId - Card ID (UUID string)
   * @returns Observable of reset StudyCard
   */
  resetCardProgress(cardId: string): Observable<StudyCard> {
    return this.http
      .post<StudyCard>(`${this.apiUrl}/cards/${cardId}/reset`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * Reset all progress for a deck
   * @param deckId - Deck ID (UUID string)
   * @returns Observable of void
   */
  resetDeckProgress(deckId: string): Observable<void> {
    return this.http
      .post<void>(`${this.apiUrl}/decks/${deckId}/reset`, {})
      .pipe(catchError(this.handleError));
  }

  /**
   * Calculate next review date based on quality
   * This is a client-side helper for preview purposes
   * @param currentInterval - Current interval in days
   * @param currentEaseFactor - Current ease factor
   * @param quality - Quality rating (0-5)
   * @returns Next interval in days
   */
  calculateNextInterval(
    currentInterval: number,
    currentEaseFactor: number,
    quality: number
  ): number {
    // SM-2 algorithm implementation
    let newInterval: number;

    if (quality < 3) {
      // Again or Hard (with difficulty)
      newInterval = 1; // Reset to 1 day
    } else if (currentInterval === 0) {
      // First review
      newInterval = 1;
    } else if (currentInterval === 1) {
      // Second review
      newInterval = 6;
    } else {
      // Subsequent reviews
      newInterval = Math.round(currentInterval * currentEaseFactor);
    }

    return newInterval;
  }

  /**
   * Calculate new ease factor based on quality
   * @param currentEaseFactor - Current ease factor
   * @param quality - Quality rating (0-5)
   * @returns New ease factor (minimum 1.3)
   */
  calculateEaseFactor(currentEaseFactor: number, quality: number): number {
    const newEF =
      currentEaseFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
    return Math.max(1.3, newEF); // Minimum ease factor is 1.3
  }

  /**
   * Handle HTTP errors
   * @param error - HTTP error response
   * @returns Observable error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      if (error.error?.detail) {
        errorMessage = error.error.detail;
      }
    }

    console.error('StudyService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
