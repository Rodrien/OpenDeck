/**
 * Notification model and related types
 */

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  actionUrl?: string;
  metadata?: Record<string, any>;
  imageUrl?: string;
  read: boolean;
  sentAt: string;
  readAt?: string;
  createdAt: string;
}

export interface UnreadCount {
  count: number;
}
