import { Component, OnInit, OnDestroy } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { MessageService } from 'primeng/api';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-google-callback',
  standalone: true,
  imports: [],
  template: `
    <div class="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div class="text-center">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p class="text-gray-600 dark:text-gray-400">Completing Google sign-in...</p>
      </div>
    </div>
  `
})
export class GoogleCallbackComponent implements OnInit, OnDestroy {
  private subscription: Subscription | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private authService: AuthService,
    private messageService: MessageService
  ) {}

  ngOnInit(): void {
    this.handleGoogleCallback();
  }

  ngOnDestroy(): void {
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  private handleGoogleCallback(): void {
    const code = this.route.snapshot.queryParamMap.get('code');
    const state = this.route.snapshot.queryParamMap.get('state');
    const error = this.route.snapshot.queryParamMap.get('error');

    if (error) {
      this.handleError(error);
      return;
    }

    if (!code) {
      this.handleError('missing_code');
      return;
    }

    this.subscription = this.authService.handleGoogleCallback(code).subscribe({
      next: (response: any) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Successfully signed in with Google'
        });
        
        // Redirect to dashboard or intended page
        const redirectUrl = sessionStorage.getItem('redirectUrl') || '/dashboard';
        sessionStorage.removeItem('redirectUrl');
        this.router.navigate([redirectUrl]);
      },
      error: (error: any) => {
        console.error('Google callback error:', error);
        this.messageService.add({
          severity: 'error',
          summary: 'Authentication Failed',
          detail: error.error?.detail || 'Failed to sign in with Google'
        });
        this.router.navigate(['/auth/login']);
      }
    });
  }

  private handleError(error: string): void {
    console.error('Google OAuth error:', error);
    
    let errorMessage = 'Authentication failed';
    if (error === 'access_denied') {
      errorMessage = 'Google sign-in was cancelled';
    } else if (error === 'missing_code') {
      errorMessage = 'Invalid authentication response';
    }

    this.messageService.add({
      severity: 'error',
      summary: 'Authentication Error',
      detail: errorMessage
    });
    
    this.router.navigate(['/auth/login']);
  }
}