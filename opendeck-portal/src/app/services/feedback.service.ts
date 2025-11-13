import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';

/**
 * Feedback type options
 */
export enum FeedbackType {
  BUG = 'bug',
  FEATURE = 'feature',
  GENERAL = 'general',
  OTHER = 'other'
}

/**
 * Feedback submission request
 */
export interface FeedbackRequest {
  feedback_type: FeedbackType;
  message: string;
}

/**
 * Feedback submission response
 */
export interface FeedbackResponse {
  id: string;
  user_id: string | null;
  feedback_type: FeedbackType;
  message: string;
  status: string;
  created_at: string;
}

/**
 * Feedback Service
 * Handles user feedback and suggestion submissions
 */
@Injectable({
  providedIn: 'root'
})
export class FeedbackService {
  private readonly apiUrl = `${environment.apiBaseUrl}/feedback`;

  constructor(private http: HttpClient) {}

  /**
   * Submit user feedback
   * @param feedbackData The feedback data to submit
   * @returns Observable of the feedback response
   */
  submitFeedback(feedbackData: FeedbackRequest): Observable<FeedbackResponse> {
    return this.http
      .post<FeedbackResponse>(this.apiUrl, feedbackData)
      .pipe(catchError(this.handleError.bind(this)));
  }

  /**
   * Handle HTTP errors
   * @param error The HTTP error response
   * @returns An observable error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage: string = 'An error occurred while submitting feedback';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Client error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = error.error?.detail || errorMessage;
    }

    console.error('Feedback submission error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
