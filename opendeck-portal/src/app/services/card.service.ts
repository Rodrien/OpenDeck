import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Card, CreateCardDto, UpdateCardDto, CardFilterParams } from '../models/card.model';
import { PaginatedResponse } from '../models/api-response.model';

/**
 * Card Service
 * Handles all flashcard-related API operations
 */
@Injectable({
  providedIn: 'root'
})
export class CardService {
  private readonly apiUrl = `${environment.apiBaseUrl}/cards`;

  constructor(private http: HttpClient) {}

  /**
   * Get all cards with optional filtering
   * @param filters - Optional filter parameters
   * @returns Observable of Paginated Card response
   */
  getAll(filters?: CardFilterParams): Observable<PaginatedResponse<Card>> {
    let params = new HttpParams();

    if (filters) {
      if (filters.deck_id !== undefined) {
        params = params.set('deck_id', filters.deck_id.toString());
      }
      if (filters.topic_id !== undefined) {
        params = params.set('topic_id', filters.topic_id.toString());
      }
      if (filters.limit !== undefined) {
        params = params.set('limit', filters.limit.toString());
      }
      if (filters.offset !== undefined) {
        params = params.set('offset', filters.offset.toString());
      }
    }

    return this.http.get<PaginatedResponse<Card>>(this.apiUrl, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Get card by ID
   * @param id - Card ID
   * @returns Observable of Card
   */
  getById(id: string): Observable<Card> {
    return this.http.get<Card>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get all cards for a specific deck
   * @param deckId - Deck ID (UUID string)
   * @param limit - Optional limit
   * @param offset - Optional offset
   * @returns Observable of Paginated Card response
   */
  getCardsForDeck(deckId: string, limit?: number, offset?: number): Observable<PaginatedResponse<Card>> {
    let params = new HttpParams();

    if (limit !== undefined) {
      params = params.set('limit', limit.toString());
    }
    if (offset !== undefined) {
      params = params.set('offset', offset.toString());
    }

    // Use the correct backend endpoint: /decks/{deck_id}/cards
    const url = `${environment.apiBaseUrl}/decks/${deckId}/cards`;
    return this.http.get<PaginatedResponse<Card>>(url, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Get cards by topic
   * @param topicId - Topic ID (UUID string)
   * @param limit - Optional limit
   * @param offset - Optional offset
   * @returns Observable of Paginated Card response
   */
  getCardsByTopic(topicId: string, limit?: number, offset?: number): Observable<PaginatedResponse<Card>> {
    return this.getAll({ topic_id: topicId, limit, offset });
  }

  /**
   * Get a specific page of cards for a deck
   * @param deckId - Deck ID (UUID string)
   * @param page - Page number (zero-indexed)
   * @param pageSize - Number of cards per page (default: 10)
   * @returns Observable of Paginated Card response
   */
  getCardsPage(deckId: string, page: number, pageSize: number = 10): Observable<PaginatedResponse<Card>> {
    const offset = page * pageSize;
    return this.getCardsForDeck(deckId, pageSize, offset);
  }

  /**
   * Create new card
   * @param card - Create Card DTO
   * @returns Observable of created Card
   */
  create(card: CreateCardDto): Observable<Card> {
    return this.http.post<Card>(this.apiUrl, card)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update existing card
   * @param id - Card ID (UUID string)
   * @param card - Update Card DTO
   * @returns Observable of updated Card
   */
  update(id: string, card: UpdateCardDto): Observable<Card> {
    return this.http.put<Card>(`${this.apiUrl}/${id}`, card)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete card
   * @param id - Card ID (UUID string)
   * @returns Observable of void
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
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

    console.error('CardService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
