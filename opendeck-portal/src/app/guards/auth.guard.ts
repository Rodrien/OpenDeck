import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Auth Guard to protect routes
 * Redirects to login if user is not authenticated
 */
export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isLoggedIn()) {
        return true;
    }

    // Redirect to login page
    return router.createUrlTree(['/auth/login']);
};

/**
 * Login Guard to prevent authenticated users from accessing login page
 * Redirects to home if user is already authenticated
 */
export const loginGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (!authService.isLoggedIn()) {
        return true;
    }

    // Redirect to home page if already logged in
    return router.createUrlTree(['/']);
};
