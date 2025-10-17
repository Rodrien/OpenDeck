import { Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    // Signal to track authentication state
    private isAuthenticatedSignal = signal<boolean>(false);

    // Public readonly signal
    isAuthenticated = this.isAuthenticatedSignal.asReadonly();

    // Test credentials
    private readonly TEST_USERNAME = 'admin';
    private readonly TEST_PASSWORD = 'admin';

    private readonly AUTH_KEY = 'opendeck_auth';

    constructor(private router: Router) {
        // Check if user is already logged in
        this.checkAuthStatus();
    }

    /**
     * Check authentication status on init
     */
    private checkAuthStatus(): void {
        const authStatus = localStorage.getItem(this.AUTH_KEY);
        if (authStatus === 'true') {
            this.isAuthenticatedSignal.set(true);
        }
    }

    /**
     * Login with username and password
     * @param username - Username
     * @param password - Password
     * @returns boolean - Success status
     */
    login(username: string, password: string): boolean {
        // Check credentials
        if (username === this.TEST_USERNAME && password === this.TEST_PASSWORD) {
            this.isAuthenticatedSignal.set(true);
            localStorage.setItem(this.AUTH_KEY, 'true');
            return true;
        }
        return false;
    }

    /**
     * Logout and clear authentication
     */
    logout(): void {
        this.isAuthenticatedSignal.set(false);
        localStorage.removeItem(this.AUTH_KEY);
        this.router.navigate(['/auth/login']);
    }

    /**
     * Check if user is authenticated (for guards)
     */
    isLoggedIn(): boolean {
        return this.isAuthenticatedSignal();
    }
}
