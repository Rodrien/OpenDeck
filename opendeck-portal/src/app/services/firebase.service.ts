/**
 * Firebase Service
 * Handles Firebase initialization and messaging operations
 */

import { Injectable } from '@angular/core';
import { initializeApp, FirebaseApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, Messaging } from 'firebase/messaging';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class FirebaseService {
  private app: FirebaseApp | null = null;
  private messaging: Messaging | null = null;

  constructor() {
    this.initialize();
  }

  /**
   * Initialize Firebase app and messaging
   */
  private initialize(): void {
    if (!this.isSupported()) {
      console.warn('Firebase messaging not supported on this device');
      return;
    }

    try {
      this.app = initializeApp(environment.firebase);
      this.messaging = getMessaging(this.app);
    } catch (error) {
      console.error('Failed to initialize Firebase:', error);
    }
  }

  /**
   * Check if Firebase messaging is supported
   */
  isSupported(): boolean {
    return (
      typeof window !== 'undefined' &&
      'Notification' in window &&
      'serviceWorker' in navigator &&
      'PushManager' in window
    );
  }

  /**
   * Request notification permission from user
   */
  async requestPermission(): Promise<boolean> {
    if (!this.isSupported()) {
      console.warn('Notifications not supported');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  /**
   * Get FCM token for current device
   */
  async getToken(): Promise<string | null> {
    if (!this.messaging) {
      console.error('Firebase messaging not initialized');
      return null;
    }

    try {
      const token = await getToken(this.messaging, {
        vapidKey: environment.firebase.vapidKey
      });

      if (token) {
        console.log('FCM token obtained:', token.substring(0, 20) + '...');
        return token;
      } else {
        console.warn('No FCM token available');
        return null;
      }
    } catch (error) {
      console.error('Error getting FCM token:', error);
      return null;
    }
  }

  /**
   * Listen for foreground messages
   */
  onMessage(callback: (payload: any) => void): void {
    if (!this.messaging) {
      console.warn('Cannot listen for messages: Firebase messaging not initialized');
      return;
    }

    onMessage(this.messaging, (payload) => {
      console.log('Foreground message received:', payload);
      callback(payload);
    });
  }

  /**
   * Get current notification permission status
   */
  getPermissionStatus(): NotificationPermission {
    if (!this.isSupported()) {
      return 'denied';
    }
    return Notification.permission;
  }
}
