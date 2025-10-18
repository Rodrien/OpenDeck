import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import {
  User,
  LoginRequest,
  RegisterRequest,
  AuthTokenResponse,
  AuthState
} from '../models/user.model';

/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */
@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly apiUrl = `${environment.apiBaseUrl}/auth`;
  private readonly TOKEN_KEY = 'opendeck_token';
  private readonly USER_KEY = 'opendeck_user';

  // Signal to track authentication state
  private isAuthenticatedSignal = signal<boolean>(false);

  // BehaviorSubject for current user
  private currentUserSubject = new BehaviorSubject<User | null>(null);

  // Public readonly signal
  public isAuthenticated = this.isAuthenticatedSignal.asReadonly();

  // Public observable for current user
  public currentUser$ = this.currentUserSubject.asObservable();

  constructor(
    private http: HttpClient,
    private router: Router
  ) {
    // Check if user is already logged in
    this.checkAuthStatus();
  }

  /**
   * Check authentication status on init
   * Restores auth state from localStorage
   */
  private checkAuthStatus(): void {
    const token = this.getToken();
    const userJson = localStorage.getItem(this.USER_KEY);

    if (token && userJson && userJson !== 'undefined' && userJson !== 'null') {
      try {
        const user = JSON.parse(userJson) as User;
        this.isAuthenticatedSignal.set(true);
        this.currentUserSubject.next(user);
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        this.clearAuthData();
      }
    } else {
      // Clear invalid data
      this.clearAuthData();
    }
  }

  /**
   * Login with email and password
   * @param email - User email
   * @param password - User password
   * @returns Observable of AuthTokenResponse
   */
  login(email: string, password: string): Observable<AuthTokenResponse> {
    const loginData: LoginRequest = { email, password };

    return this.http.post<AuthTokenResponse>(`${this.apiUrl}/login`, loginData)
      .pipe(
        tap(response => this.handleAuthSuccess(response)),
        catchError(this.handleError)
      );
  }

  /**
   * Register new user
   * @param email - User email
   * @param name - User name
   * @param password - User password
   * @returns Observable of AuthTokenResponse
   */
  register(email: string, name: string, password: string): Observable<AuthTokenResponse> {
    const registerData: RegisterRequest = { email, name, password };

    return this.http.post<AuthTokenResponse>(`${this.apiUrl}/register`, registerData)
      .pipe(
        tap(response => this.handleAuthSuccess(response)),
        catchError(this.handleError)
      );
  }

  /**
   * Handle successful authentication
   * Stores token and user data
   * @param response - Auth token response
   */
  private handleAuthSuccess(response: AuthTokenResponse): void {
    this.setToken(response.access_token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(response.user));
    this.isAuthenticatedSignal.set(true);
    this.currentUserSubject.next(response.user);
  }

  /**
   * Get stored JWT token
   * @returns Token string or null
   */
  getToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  /**
   * Store JWT token
   * @param token - JWT token string
   */
  setToken(token: string): void {
    localStorage.setItem(this.TOKEN_KEY, token);
  }

  /**
   * Clear authentication data
   */
  private clearAuthData(): void {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    this.isAuthenticatedSignal.set(false);
    this.currentUserSubject.next(null);
  }

  /**
   * Logout and clear authentication
   * Redirects to login page
   */
  logout(): void {
    this.clearAuthData();
    this.router.navigate(['/auth/login']);
  }

  /**
   * Check if user is authenticated
   * @returns boolean - Authentication status
   */
  isLoggedIn(): boolean {
    return this.isAuthenticatedSignal();
  }

  /**
   * Get current user
   * @returns Current user or null
   */
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  /**
   * Get current auth state
   * @returns AuthState object
   */
  getAuthState(): AuthState {
    return {
      isAuthenticated: this.isLoggedIn(),
      user: this.getCurrentUser(),
      token: this.getToken()
    };
  }

  /**
   * Handle HTTP errors
   * @param error - HTTP error response
   * @returns Observable error
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred during authentication';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      if (error.status === 401) {
        errorMessage = 'Invalid credentials';
      } else if (error.status === 409) {
        errorMessage = 'User already exists';
      } else if (error.error?.detail) {
        errorMessage = error.error.detail;
      } else {
        errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      }
    }

    console.error('AuthService Error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }
}
