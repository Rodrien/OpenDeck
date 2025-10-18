import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

/**
 * Auth Interceptor (Functional)
 * Adds JWT Bearer token to outgoing HTTP requests
 * Uses Angular 18+ functional interceptor pattern
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  // Skip token injection for auth endpoints
  const isAuthEndpoint = req.url.includes('/auth/login') || req.url.includes('/auth/register');

  // If token exists and not an auth endpoint, clone request and add Authorization header
  if (token && !isAuthEndpoint) {
    const clonedRequest = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(clonedRequest);
  }

  // Pass through original request
  return next(req);
};
