/**
 * Notification Panel Component
 * Displays notification list with actions
 */

import { Component, OnInit, Output, EventEmitter, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { ScrollPanelModule } from 'primeng/scrollpanel';
import { TranslateModule, TranslateService } from '@ngx-translate/core';
import { NotificationService } from '../../services/notification.service';
import { Notification } from '../../models/notification.model';

@Component({
  selector: 'app-notification-panel',
  standalone: true,
  imports: [
    CommonModule,
    ButtonModule,
    ScrollPanelModule,
    TranslateModule
  ],
  template: `
    <div class="notification-panel">
      <div class="panel-header flex justify-content-between align-items-center mb-3">
        <h3 class="m-0">{{ 'notifications.title' | translate }}</h3>
        <p-button
          *ngIf="hasUnreadNotifications()"
          [label]="'notifications.markAllRead' | translate"
          icon="pi pi-check"
          [text]="true"
          size="small"
          (onClick)="markAllAsRead()"
        />
      </div>

      <p-scrollPanel [style]="{ width: '100%', height: '400px' }">
        <div class="notifications-list">
          <div
            *ngFor="let notification of notifications()"
            class="notification-item"
            [class.unread]="!notification.read"
            [class]="'type-' + notification.type"
            (click)="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <i [class]="getNotificationIcon(notification.type)"></i>
            </div>

            <div class="notification-content flex-1">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatTime(notification.sentAt) }}</div>
            </div>

            <div class="notification-actions">
              <button
                *ngIf="!notification.read"
                class="action-btn"
                (click)="markAsRead($event, notification.id)"
                [attr.aria-label]="'Mark as read'"
              >
                <i class="pi pi-check"></i>
              </button>
              <button
                class="action-btn"
                (click)="deleteNotification($event, notification.id)"
                [attr.aria-label]="'Delete notification'"
              >
                <i class="pi pi-trash"></i>
              </button>
            </div>
          </div>

          <div *ngIf="notifications().length === 0" class="no-notifications">
            <i class="pi pi-bell text-4xl mb-3 text-400"></i>
            <p>{{ 'notifications.noNotifications' | translate }}</p>
          </div>
        </div>
      </p-scrollPanel>
    </div>
  `,
  styles: [`
    .notification-panel {
      padding: 1rem;
    }

    .panel-header h3 {
      font-size: 1.25rem;
      font-weight: 600;
    }

    .notifications-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .notification-item {
      display: flex;
      gap: 1rem;
      padding: 1rem;
      border-radius: 8px;
      background: var(--surface-50);
      cursor: pointer;
      transition: all 0.2s;
      border-left: 4px solid transparent;
    }

    .notification-item:hover {
      background: var(--surface-100);
    }

    .notification-item.unread {
      background: var(--primary-50);
      border-left-color: var(--primary-500);
    }

    .notification-item.type-success {
      border-left-color: var(--green-500);
    }

    .notification-item.type-error {
      border-left-color: var(--red-500);
    }

    .notification-item.type-warning {
      border-left-color: var(--orange-500);
    }

    .notification-item.type-info {
      border-left-color: var(--blue-500);
    }

    .notification-icon {
      display: flex;
      align-items: flex-start;
      font-size: 1.5rem;
    }

    .notification-content {
      min-width: 0;
    }

    .notification-title {
      font-weight: 600;
      margin-bottom: 0.25rem;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .notification-message {
      font-size: 0.875rem;
      color: var(--text-color-secondary);
      margin-bottom: 0.5rem;
      overflow: hidden;
      text-overflow: ellipsis;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
    }

    .notification-time {
      font-size: 0.75rem;
      color: var(--text-color-secondary);
    }

    .notification-actions {
      display: flex;
      gap: 0.5rem;
      align-items: flex-start;
    }

    .action-btn {
      background: none;
      border: none;
      padding: 0.5rem;
      cursor: pointer;
      border-radius: 4px;
      color: var(--text-color-secondary);
      transition: all 0.2s;
    }

    .action-btn:hover {
      background: var(--surface-200);
      color: var(--text-color);
    }

    .no-notifications {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 3rem 1rem;
      text-align: center;
      color: var(--text-color-secondary);
    }
  `]
})
export class NotificationPanelComponent implements OnInit {
  @Output() notificationRead = new EventEmitter<void>();
  @Output() closePanel = new EventEmitter<void>();

  notifications = signal<Notification[]>([]);

  constructor(
    private notificationService: NotificationService,
    private router: Router,
    private translate: TranslateService
  ) {}

  async ngOnInit() {
    await this.loadNotifications();
  }

  async loadNotifications() {
    await this.notificationService.loadNotifications(false, 20);
    this.notifications.set(this.notificationService.getNotificationsSignal()());
  }

  hasUnreadNotifications(): boolean {
    return this.notifications().some(n => !n.read);
  }

  async markAsRead(event: Event, notificationId: string) {
    event.stopPropagation();
    await this.notificationService.markAsRead(notificationId);
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async markAllAsRead() {
    await this.notificationService.markAllAsRead();
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async deleteNotification(event: Event, notificationId: string) {
    event.stopPropagation();
    await this.notificationService.deleteNotification(notificationId);
    await this.loadNotifications();
    this.notificationRead.emit();
  }

  async handleNotificationClick(notification: Notification) {
    if (!notification.read) {
      await this.notificationService.markAsRead(notification.id);
      this.notificationRead.emit();
    }

    if (notification.actionUrl) {
      this.router.navigate([notification.actionUrl]);
      this.closePanel.emit();
    }
  }

  getNotificationIcon(type: string): string {
    switch (type) {
      case 'success': return 'pi pi-check-circle';
      case 'error': return 'pi pi-times-circle';
      case 'warning': return 'pi pi-exclamation-triangle';
      default: return 'pi pi-info-circle';
    }
  }

  formatTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return this.translate.instant('notifications.time.justNow');
    if (diffMins < 60) return this.translate.instant('notifications.time.minutesAgo', { count: diffMins });

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return this.translate.instant('notifications.time.hoursAgo', { count: diffHours });

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return this.translate.instant('notifications.time.daysAgo', { count: diffDays });

    return date.toLocaleDateString();
  }
}
