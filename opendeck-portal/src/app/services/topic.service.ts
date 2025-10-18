import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { Topic, CreateTopicDto, UpdateTopicDto } from '../models/topic.model';

/**
 * Topic Service
 * Handles all topic-related API operations
 */
@Injectable({
  providedIn: 'root'
})
export class TopicService {
  private readonly apiUrl = `${environment.apiBaseUrl}/topics`;

  constructor(private http: HttpClient) {}

  /**
   * Get all topics
   * @returns Observable of Topic array
   */
  getAll(): Observable<Topic[]> {
    return this.http.get<Topic[]>(this.apiUrl)
      .pipe(catchError(this.handleError));
  }

  /**
   * Get topic by ID
   * @param id - Topic ID (UUID string)
   * @returns Observable of Topic
   */
  getById(id: string): Observable<Topic> {
    return this.http.get<Topic>(`${this.apiUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Create new topic
   * @param topic - Create Topic DTO
   * @returns Observable of created Topic
   */
  create(topic: CreateTopicDto): Observable<Topic> {
    return this.http.post<Topic>(this.apiUrl, topic)
      .pipe(catchError(this.handleError));
  }

  /**
   * Update existing topic
   * @param id - Topic ID (UUID string)
   * @param topic - Update Topic DTO
   * @returns Observable of updated Topic
   */
  update(id: string, topic: UpdateTopicDto): Observable<Topic> {
    return this.http.put<Topic>(`${this.apiUrl}/${id}`, topic)
      .pipe(catchError(this.handleError));
  }

  /**
   * Delete topic
   * @param id - Topic ID (UUID string)
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

    console.error('TopicService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
