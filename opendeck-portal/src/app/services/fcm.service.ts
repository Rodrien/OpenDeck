/**
 * FCM Service
 * Handles FCM token registration and foreground message handling
 */

import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { FirebaseService } from './firebase.service';
import { environment } from '../../environments/environment';
import { FCMTokenCreate, FCMTokenResponse } from '../models/fcm-token.model';
import { MessageService } from 'primeng/api';

@Injectable({
  providedIn: 'root'
})
export class FCMService {
  private currentToken = signal<string | null>(null);
  private tokenRegistered = signal<boolean>(false);
  private initialized = signal<boolean>(false);

  constructor(
    private http: HttpClient,
    private firebase: FirebaseService,
    private messageService: MessageService
  ) {}

  /**
   * Initialize FCM (request permission and register token)
   */
  async initialize(): Promise<void> {
    if (this.initialized()) {
      console.log('FCM already initialized');
      return;
    }

    if (!this.firebase.isSupported()) {
      console.warn('Push notifications not supported on this device');
      return;
    }

    // Check if permission already granted
    const permissionStatus = this.firebase.getPermissionStatus();

    if (permissionStatus === 'granted') {
      await this.setupFCM();
    } else if (permissionStatus === 'default') {
      // Don't request permission immediately - wait for user action
      console.log('Notification permission not yet requested');
    }

    this.initialized.set(true);
  }

  /**
   * Request permission and setup FCM
   */
  async requestPermissionAndSetup(): Promise<boolean> {
    const granted = await this.firebase.requestPermission();

    if (!granted) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Notifications Disabled',
        detail: 'Enable notifications in your browser settings to receive updates'
      });
      return false;
    }

    await this.setupFCM();
    return true;
  }

  /**
   * Setup FCM (get token and register with backend)
   */
  private async setupFCM(): Promise<void> {
    // Get FCM token
    const token = await this.firebase.getToken();

    if (!token) {
      console.error('Failed to get FCM token');
      return;
    }

    this.currentToken.set(token);

    // Register token with backend
    await this.registerToken(token);

    // Listen for foreground messages
    this.firebase.onMessage((payload) => {
      this.handleForegroundMessage(payload);
    });
  }

  /**
   * Register FCM token with backend
   */
  private async registerToken(token: string): Promise<void> {
    const deviceName = this.getDeviceInfo();

    const tokenData: FCMTokenCreate = {
      fcm_token: token,
      device_type: 'web',
      device_name: deviceName
    };

    try {
      const response = await firstValueFrom(
        this.http.post<FCMTokenResponse>(
          `${environment.apiBaseUrl}/fcm-tokens`,
          tokenData
        )
      );

      this.tokenRegistered.set(true);
      console.log('FCM token registered successfully');

      this.messageService.add({
        severity: 'success',
        summary: 'Notifications Enabled',
        detail: 'You will now receive real-time updates',
        life: 3000
      });

    } catch (error) {
      console.error('Failed to register FCM token:', error);
      this.messageService.add({
        severity: 'error',
        summary: 'Registration Failed',
        detail: 'Could not enable notifications'
      });
    }
  }

  /**
   * Unregister FCM token (called on logout)
   */
  async unregisterToken(): Promise<void> {
    const token = this.currentToken();
    if (!token || !this.tokenRegistered()) return;

    try {
      // Clear local state
      this.currentToken.set(null);
      this.tokenRegistered.set(false);
      console.log('FCM token unregistered');
    } catch (error) {
      console.error('Failed to unregister FCM token:', error);
    }
  }

  /**
   * Handle foreground messages (show PrimeNG toast)
   */
  private handleForegroundMessage(payload: any): void {
    const { notification, data } = payload;

    if (!notification) return;

    // Show PrimeNG toast for foreground notifications
    const severity = this.getSeverityFromType(data?.type || 'info');

    this.messageService.add({
      severity: severity,
      summary: notification.title,
      detail: notification.body,
      life: 5000,
      data: { actionUrl: data?.action_url }
    });
  }

  /**
   * Convert notification type to PrimeNG severity
   */
  private getSeverityFromType(type: string): 'success' | 'info' | 'warn' | 'error' {
    switch (type) {
      case 'success': return 'success';
      case 'warning': return 'warn';
      case 'error': return 'error';
      default: return 'info';
    }
  }

  /**
   * Get device information for registration
   */
  private getDeviceInfo(): string {
    const ua = navigator.userAgent;
    if (ua.includes('Chrome')) return 'Chrome';
    if (ua.includes('Firefox')) return 'Firefox';
    if (ua.includes('Safari')) return 'Safari';
    if (ua.includes('Edge')) return 'Edge';
    return 'Web Browser';
  }

  /**
   * Check if token is registered
   */
  isTokenRegistered(): boolean {
    return this.tokenRegistered();
  }
}
