/**
 * Notification Bell Component
 * Displays notification icon with unread count badge
 */

import { Component, OnInit, OnDestroy, signal, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BadgeModule } from 'primeng/badge';
import { OverlayPanel, OverlayPanelModule } from 'primeng/overlaypanel';
import { NotificationService } from '../../services/notification.service';
import { NotificationPanelComponent } from '../notification-panel/notification-panel.component';

@Component({
  selector: 'app-notification-bell',
  standalone: true,
  imports: [
    CommonModule,
    BadgeModule,
    OverlayPanelModule,
    NotificationPanelComponent
  ],
  template: `
    <div
      class="notification-bell relative cursor-pointer"
      (click)="togglePanel($event)"
      [class.has-notifications]="unreadCount() > 0"
    >
      <i class="pi pi-bell text-2xl"></i>
      <span
        *ngIf="unreadCount() > 0"
        class="notification-badge"
        [attr.aria-label]="unreadCount() + ' unread notifications'"
      >
        {{ unreadCount() > 99 ? '99+' : unreadCount() }}
      </span>
    </div>

    <p-overlayPanel #op [style]="{ width: '400px', maxWidth: '90vw' }">
      <app-notification-panel
        (notificationRead)="onNotificationRead()"
        (closePanel)="op.hide()">
      </app-notification-panel>
    </p-overlayPanel>
  `,
  styles: [`
    .notification-bell {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      transition: background-color 0.2s;
    }

    .notification-bell:hover {
      background-color: var(--surface-hover);
    }

    .notification-badge {
      position: absolute;
      top: 2px;
      right: 2px;
      background-color: var(--red-500);
      color: white;
      font-size: 0.75rem;
      font-weight: bold;
      padding: 2px 6px;
      border-radius: 10px;
      min-width: 20px;
      text-align: center;
      line-height: 1;
    }

    .notification-bell.has-notifications i {
      animation: bell-ring 0.5s ease-in-out;
    }

    @keyframes bell-ring {
      0%, 100% { transform: rotate(0deg); }
      10%, 30% { transform: rotate(-10deg); }
      20%, 40% { transform: rotate(10deg); }
    }
  `]
})
export class NotificationBellComponent implements OnInit, OnDestroy {
  @ViewChild('op') overlayPanel!: OverlayPanel;

  unreadCount = signal<number>(0);
  private refreshIntervalId?: number;

  constructor(private notificationService: NotificationService) {}

  async ngOnInit() {
    await this.loadUnreadCount();

    // Refresh count every 30 seconds as backup
    this.refreshIntervalId = setInterval(() => this.loadUnreadCount(), 30000) as unknown as number;
  }

  ngOnDestroy() {
    // Clear the interval to prevent memory leak
    if (this.refreshIntervalId) {
      clearInterval(this.refreshIntervalId);
    }
  }

  async loadUnreadCount() {
    await this.notificationService.loadUnreadCount();
    this.unreadCount.set(this.notificationService.getUnreadCountSignal()());
  }

  togglePanel(event: Event) {
    this.overlayPanel.toggle(event);
  }

  onNotificationRead() {
    this.loadUnreadCount();
  }
}
