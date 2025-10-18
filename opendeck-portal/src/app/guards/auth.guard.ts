import { inject } from '@angular/core';
import { Router, CanActivateFn, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * Auth Guard (Functional)
 * Protects routes requiring authentication
 * Redirects to login page if user is not authenticated
 * Stores the attempted URL for redirecting after login
 * Uses Angular 18+ functional guard pattern
 */
export const authGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Check if user is authenticated
  if (authService.isLoggedIn()) {
    return true;
  }

  // Store the attempted URL for redirecting after login
  const returnUrl = state.url;
  console.warn('Unauthorized access attempt to:', returnUrl);

  // Redirect to login page with return URL
  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl }
  });
};

/**
 * Guest Guard (Functional)
 * Prevents authenticated users from accessing auth pages (login, register)
 * Redirects to dashboard if already authenticated
 * Renamed from loginGuard for clarity
 */
export const guestGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // If user is authenticated, redirect to dashboard
  if (authService.isLoggedIn()) {
    return router.createUrlTree(['/']);
  }

  // Allow access to auth pages
  return true;
};

/**
 * Legacy alias for backward compatibility
 * @deprecated Use guestGuard instead
 */
export const loginGuard = guestGuard;
