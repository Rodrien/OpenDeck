import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, throwError, timer, Subject } from 'rxjs';
import { catchError, map, switchMap, takeWhile, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  DeckMetadata,
  UploadResponse,
  DocumentStatus,
  FileUploadError
} from '../models/document.model';

/**
 * Document Service
 * Handles document upload and processing status tracking
 */
@Injectable({
  providedIn: 'root'
})
export class DocumentService {
  private readonly apiUrl = `${environment.apiBaseUrl}/documents`;
  private readonly POLL_INTERVAL = 2000; // 2 seconds

  // Subject for upload progress tracking
  private uploadProgress$ = new Subject<number>();

  constructor(private http: HttpClient) {}

  /**
   * Upload documents with metadata to create a new deck
   * @param files - Array of files to upload
   * @param metadata - Deck metadata (title, description, category, difficulty)
   * @returns Observable of upload response
   */
  uploadDocuments(files: File[], metadata: DeckMetadata): Observable<UploadResponse> {
    const formData = new FormData();

    // Append files
    files.forEach((file, index) => {
      formData.append('files', file, file.name);
    });

    // Append metadata as JSON
    formData.append('metadata', JSON.stringify(metadata));

    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData, {
      reportProgress: true,
      observe: 'events'
    }).pipe(
      map((event: HttpEvent<any>) => {
        switch (event.type) {
          case HttpEventType.UploadProgress:
            const progress = event.total
              ? Math.round((100 * event.loaded) / event.total)
              : 0;
            this.uploadProgress$.next(progress);
            return null;
          case HttpEventType.Response:
            this.uploadProgress$.next(100);
            return event.body as UploadResponse;
          default:
            return null;
        }
      }),
      // Filter out null values (progress events)
      map(response => response as UploadResponse),
      catchError(this.handleError)
    );
  }

  /**
   * Get current upload progress as observable
   */
  getUploadProgress(): Observable<number> {
    return this.uploadProgress$.asObservable();
  }

  /**
   * Get processing status for multiple documents
   * @param documentIds - Array of document IDs to check
   * @returns Observable of document status array
   */
  getProcessingStatus(documentIds: string[]): Observable<DocumentStatus[]> {
    const params = { document_ids: documentIds.join(',') };
    return this.http.get<DocumentStatus[]>(`${this.apiUrl}/status`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Poll processing status until all documents are completed or failed
   * @param documentIds - Array of document IDs to poll
   * @returns Observable that emits status updates every 2 seconds
   */
  pollProcessingStatus(documentIds: string[]): Observable<DocumentStatus[]> {
    return timer(0, this.POLL_INTERVAL).pipe(
      switchMap(() => this.getProcessingStatus(documentIds)),
      takeWhile((statuses) => {
        // Continue polling while any document is still pending or processing
        return statuses.some(status =>
          status.status === 'pending' || status.status === 'processing'
        );
      }, true), // Include the final emission
      catchError(this.handleError)
    );
  }

  /**
   * Validate file before upload
   * @param file - File to validate
   * @returns Error message if invalid, null if valid
   */
  validateFile(file: File): string | null {
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain'
    ];

    if (file.size > maxSize) {
      return `File "${file.name}" exceeds 10MB limit`;
    }

    if (!allowedTypes.includes(file.type) && !this.hasValidExtension(file.name)) {
      return `File "${file.name}" has unsupported format. Please use PDF, DOCX, PPTX, or TXT`;
    }

    return null;
  }

  /**
   * Check if file has valid extension (fallback when MIME type is not reliable)
   */
  private hasValidExtension(filename: string): boolean {
    const validExtensions = ['.pdf', '.docx', '.pptx', '.txt'];
    return validExtensions.some(ext => filename.toLowerCase().endsWith(ext));
  }

  /**
   * Validate total upload size
   * @param files - Array of files
   * @returns Error message if invalid, null if valid
   */
  validateTotalSize(files: File[]): string | null {
    const totalSize = files.reduce((sum, file) => sum + file.size, 0);
    const maxTotalSize = 50 * 1024 * 1024; // 50MB

    if (totalSize > maxTotalSize) {
      const sizeMB = (totalSize / (1024 * 1024)).toFixed(2);
      return `Total file size (${sizeMB}MB) exceeds 50MB limit`;
    }

    return null;
  }

  /**
   * Handle HTTP errors
   * @param error - HTTP error response
   * @returns Observable error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred while uploading documents';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.status === 0) {
        errorMessage = 'Unable to connect to server. Please check your connection.';
      } else if (error.status === 413) {
        errorMessage = 'Files are too large. Please reduce file sizes and try again.';
      } else if (error.status === 400) {
        errorMessage = error.error?.detail || 'Invalid request. Please check your files and try again.';
      } else if (error.status === 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (error.error?.detail) {
        errorMessage = error.error.detail;
      }
    }

    console.error('DocumentService Error:', errorMessage, error);
    return throwError(() => new Error(errorMessage));
  }
}
