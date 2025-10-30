/**
 * FCM Token model and related types
 */

export interface FCMTokenCreate {
  fcm_token: string;
  device_type: 'web' | 'ios' | 'android';
  device_name?: string;
}

export interface FCMTokenResponse {
  id: string;
  user_id: string;
  device_type: string;
  device_name?: string;
  is_active: boolean;
  created_at: string;
}
