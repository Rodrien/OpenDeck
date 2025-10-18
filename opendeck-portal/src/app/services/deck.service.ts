import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Deck, CreateDeckDto, UpdateDeckDto, DeckFilterParams } from '../models/deck.model';
import { PaginatedResponse } from '../models/api-response.model';

/**
 * Deck Service
 * Handles all deck-related API operations
 */
@Injectable({
  providedIn: 'root'
})
export class DeckService {
  private readonly apiUrl = `${environment.apiBaseUrl}/decks`;

  constructor(private http: HttpClient) {}

  /**
   * Get all decks with optional filtering
   * @param filters - Optional filter parameters
   * @returns Observable of Paginated Deck response
   */
  getAll(filters?: DeckFilterParams): Observable<PaginatedResponse<Deck>> {
    let params = new HttpParams();

    if (filters) {
      if (filters.category) {
        params = params.set('category', filters.category);
      }
      if (filters.difficulty) {
        params = params.set('difficulty', filters.difficulty);
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

    return this.http.get<PaginatedResponse<Deck>>(this.apiUrl, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Get deck by ID
   * @param id - Deck ID (UUID string)
   * @returns Observable of Deck
   */
  getById(id: string): Observable<Deck> {
    return this.http.get<Deck>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Create new deck
   * @param deck - Create Deck DTO
   * @returns Observable of created Deck
   */
  create(deck: CreateDeckDto): Observable<Deck> {
    return this.http.post<Deck>(this.apiUrl, deck)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update existing deck
   * @param id - Deck ID (UUID string)
   * @param deck - Update Deck DTO
   * @returns Observable of updated Deck
   */
  update(id: string, deck: UpdateDeckDto): Observable<Deck> {
    return this.http.put<Deck>(`${this.apiUrl}/${id}`, deck)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete deck
   * @param id - Deck ID (UUID string)
   * @returns Observable of void
   */
  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get decks by category
   * @param category - Category name
   * @param limit - Optional limit
   * @param offset - Optional offset
   * @returns Observable of Paginated Deck response
   */
  getByCategory(category: string, limit?: number, offset?: number): Observable<PaginatedResponse<Deck>> {
    return this.getAll({ category, limit, offset });
  }

  /**
   * Get decks by difficulty
   * @param difficulty - Difficulty level
   * @param limit - Optional limit
   * @param offset - Optional offset
   * @returns Observable of Paginated Deck response
   */
  getByDifficulty(difficulty: 'beginner' | 'intermediate' | 'advanced', limit?: number, offset?: number): Observable<PaginatedResponse<Deck>> {
    return this.getAll({ difficulty, limit, offset });
  }

  /**
   * Get decks by topic
   * @param topicId - Topic ID (UUID string)
   * @param limit - Optional limit
   * @param offset - Optional offset
   * @returns Observable of Paginated Deck response
   */
  getByTopic(topicId: string, limit?: number, offset?: number): Observable<PaginatedResponse<Deck>> {
    return this.getAll({ topic_id: topicId, limit, offset });
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

    console.error('DeckService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
