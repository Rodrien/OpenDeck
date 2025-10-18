import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Error Interceptor (Functional)
 * Global error handling for HTTP requests
 * Handles authentication errors and provides user-friendly error messages
 * Uses Angular 18+ functional interceptor pattern
 */
export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      let errorMessage = 'An error occurred';

      if (error.error instanceof ErrorEvent) {
        // Client-side or network error
        errorMessage = `Network Error: ${error.error.message}`;
        console.error('Client-side error:', errorMessage);
      } else {
        // Server-side error
        switch (error.status) {
          case 400:
            errorMessage = 'Bad Request: Please check your input';
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            }
            break;

          case 401:
            errorMessage = 'Unauthorized: Please log in again';
            console.warn('Unauthorized access - redirecting to login');
            // Clear auth data and redirect to login
            authService.logout();
            break;

          case 403:
            errorMessage = 'Forbidden: You do not have permission to access this resource';
            break;

          case 404:
            errorMessage = 'Not Found: The requested resource was not found';
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            }
            break;

          case 409:
            errorMessage = 'Conflict: The resource already exists';
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            }
            break;

          case 422:
            errorMessage = 'Validation Error: Please check your input';
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            }
            break;

          case 500:
            errorMessage = 'Server Error: Something went wrong on our end';
            break;

          case 503:
            errorMessage = 'Service Unavailable: The server is temporarily unavailable';
            break;

          default:
            errorMessage = `Error ${error.status}: ${error.message}`;
            if (error.error?.detail) {
              errorMessage = error.error.detail;
            }
        }

        console.error('HTTP Error:', {
          status: error.status,
          message: errorMessage,
          url: error.url,
          error: error.error
        });
      }

      // You can integrate a toast/notification service here to show user-friendly messages
      // Example: toastService.error(errorMessage);

      return throwError(() => new Error(errorMessage));
    })
  );
};
