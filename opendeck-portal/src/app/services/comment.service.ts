import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  DeckComment,
  CreateCommentDto,
  UpdateCommentDto,
  VoteCreateDto,
  VoteCountsResponse,
  CommentListResponse,
  CommentFilterParams
} from '../models/comment.model';

/**
 * Comment Service
 * Handles all comment-related API operations
 */
@Injectable({
  providedIn: 'root'
})
export class CommentService {
  private readonly apiUrl = `${environment.apiBaseUrl}/decks`;

  constructor(private http: HttpClient) {}

  /**
   * Get all comments for a deck with optional filtering
   * @param deckId - Deck ID
   * @param filters - Optional filter parameters
   * @returns Observable of CommentListResponse
   */
  getCommentsByDeck(deckId: string, filters?: CommentFilterParams): Observable<CommentListResponse> {
    let params = new HttpParams();

    if (filters) {
      if (filters.limit !== undefined) {
        params = params.set('limit', filters.limit.toString());
      }
      if (filters.offset !== undefined) {
        params = params.set('offset', filters.offset.toString());
      }
    }

    return this.http.get<CommentListResponse>(`${this.apiUrl}/${deckId}/comments`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Get comment by ID
   * @param deckId - Deck ID
   * @param commentId - Comment ID
   * @returns Observable of DeckComment
   */
  getCommentById(deckId: string, commentId: string): Observable<DeckComment> {
    return this.http.get<DeckComment>(`${this.apiUrl}/${deckId}/comments/${commentId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Create new comment
   * @param deckId - Deck ID
   * @param comment - Create Comment DTO
   * @returns Observable of created DeckComment
   */
  createComment(deckId: string, comment: CreateCommentDto): Observable<DeckComment> {
    return this.http.post<DeckComment>(`${this.apiUrl}/${deckId}/comments`, comment)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update existing comment
   * @param deckId - Deck ID
   * @param commentId - Comment ID
   * @param comment - Update Comment DTO
   * @returns Observable of updated DeckComment
   */
  updateComment(deckId: string, commentId: string, comment: UpdateCommentDto): Observable<DeckComment> {
    return this.http.put<DeckComment>(`${this.apiUrl}/${deckId}/comments/${commentId}`, comment)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete comment
   * @param deckId - Deck ID
   * @param commentId - Comment ID
   * @returns Observable of void
   */
  deleteComment(deckId: string, commentId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${deckId}/comments/${commentId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Vote on a comment
   * @param deckId - Deck ID
   * @param commentId - Comment ID
   * @param vote - Vote Create DTO
   * @returns Observable of VoteCountsResponse
   */
  voteOnComment(deckId: string, commentId: string, vote: VoteCreateDto): Observable<VoteCountsResponse> {
    return this.http.post<VoteCountsResponse>(`${this.apiUrl}/${deckId}/comments/${commentId}/vote`, vote)
      .pipe(catchError(this.handleError));
  }

  /**
   * Remove vote from a comment
   * @param deckId - Deck ID
   * @param commentId - Comment ID
   * @returns Observable of void
   */
  removeVote(deckId: string, commentId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${deckId}/comments/${commentId}/vote`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Handle HTTP errors
   * @param error - HTTP Error Response
   * @returns Observable that throws error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An unknown error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || `Server error: ${error.status} ${error.statusText}`;
    }

    console.error('CommentService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
