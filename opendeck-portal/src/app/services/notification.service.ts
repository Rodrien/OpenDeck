/**
 * Notification Service
 * Handles notification history and management operations
 */

import { Injectable, signal } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { Notification, UnreadCount } from '../models/notification.model';

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notifications = signal<Notification[]>([]);
  private unreadCount = signal<number>(0);

  constructor(private http: HttpClient) {}

  /**
   * Load notifications from backend
   */
  async loadNotifications(unreadOnly: boolean = false, limit: number = 50): Promise<void> {
    try {
      const notifications = await this.getNotifications(unreadOnly, limit);
      this.notifications.set(notifications);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  }

  /**
   * Load unread count from backend
   */
  async loadUnreadCount(): Promise<void> {
    try {
      const count = await this.getUnreadCount();
      this.unreadCount.set(count);
    } catch (error) {
      console.error('Failed to load unread count:', error);
    }
  }

  /**
   * Get notifications from API
   */
  getNotifications(unreadOnly: boolean = false, limit: number = 50, offset: number = 0): Promise<Notification[]> {
    let params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());

    if (unreadOnly) {
      params = params.set('unread_only', 'true');
    }

    return firstValueFrom(
      this.http.get<Notification[]>(
        `${environment.apiBaseUrl}/notifications`,
        { params }
      )
    );
  }

  /**
   * Get unread notification count
   */
  async getUnreadCount(): Promise<number> {
    const response = await firstValueFrom(
      this.http.get<UnreadCount>(`${environment.apiBaseUrl}/notifications/unread-count`)
    );
    return response.count;
  }

  /**
   * Mark notification as read
   */
  async markAsRead(notificationId: string): Promise<void> {
    await firstValueFrom(
      this.http.patch<void>(
        `${environment.apiBaseUrl}/notifications/${notificationId}/read`,
        {}
      )
    );

    // Update local state
    await this.loadUnreadCount();
    await this.loadNotifications();
  }

  /**
   * Mark all notifications as read
   */
  async markAllAsRead(): Promise<void> {
    await firstValueFrom(
      this.http.patch<void>(
        `${environment.apiBaseUrl}/notifications/read-all`,
        {}
      )
    );

    // Update local state
    this.unreadCount.set(0);
    await this.loadNotifications();
  }

  /**
   * Delete a notification
   */
  async deleteNotification(notificationId: string): Promise<void> {
    await firstValueFrom(
      this.http.delete<void>(
        `${environment.apiBaseUrl}/notifications/${notificationId}`
      )
    );

    // Update local state
    await this.loadNotifications();
    await this.loadUnreadCount();
  }

  /**
   * Get notifications signal (readonly)
   */
  getNotificationsSignal() {
    return this.notifications.asReadonly();
  }

  /**
   * Get unread count signal (readonly)
   */
  getUnreadCountSignal() {
    return this.unreadCount.asReadonly();
  }
}
