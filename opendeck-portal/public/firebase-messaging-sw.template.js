// Firebase Cloud Messaging Service Worker
// This file must be in the public directory at the root of your app

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// TODO: Replace with actual Firebase config
// Initialize Firebase app in service worker
firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "opendeck.firebaseapp.com",
  projectId: "opendeck",
  storageBucket: "opendeck.appspot.com",
  messagingSenderId: "123456789",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages (when app is not in focus)
messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message:', payload);

  const { notification, data } = payload;

  if (!notification) {
    console.warn('No notification payload');
    return;
  }

  const notificationTitle = notification.title || 'OpenDeck';
  const notificationOptions = {
    body: notification.body,
    icon: notification.icon || '/assets/images/opendeck-icon.png',
    badge: '/assets/images/badge-icon.png',
    image: notification.image,
    tag: data?.notification_id || 'opendeck-notification',
    requireInteraction: false,
    data: {
      url: data?.action_url || '/dashboard',
      notification_id: data?.notification_id
    }
  };

  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  console.log('[firebase-messaging-sw.js] Notification click:', event);

  event.notification.close();

  const urlToOpen = event.notification.data?.url || '/dashboard';
  const fullUrl = self.location.origin + urlToOpen;

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    })
    .then((clientList) => {
      // Check if there's already a window open
      for (const client of clientList) {
        if (client.url === fullUrl && 'focus' in client) {
          return client.focus();
        }
      }

      // If no window found, open a new one
      if (clients.openWindow) {
        return clients.openWindow(fullUrl);
      }
    })
  );
});

// Handle service worker activation
self.addEventListener('activate', (event) => {
  console.log('[firebase-messaging-sw.js] Service worker activated');
});
