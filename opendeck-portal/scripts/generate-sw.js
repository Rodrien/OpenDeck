#!/usr/bin/env node
/**
 * Generate Firebase Messaging Service Worker
 *
 * This script generates the firebase-messaging-sw.js file with actual
 * Firebase configuration from the environment file. Service workers
 * cannot access environment variables, so we inject the config at build time.
 *
 * Usage:
 *   node scripts/generate-sw.js [production|development]
 */

const fs = require('fs');
const path = require('path');

// Get environment from command line argument
const envArg = process.argv[2] || 'development';
const isProduction = envArg === 'production';

// Load environment configuration
let environment;
try {
  const envPath = isProduction
    ? '../src/environments/environment.ts'
    : '../src/environments/environment.development.ts';

  const envFile = fs.readFileSync(
    path.join(__dirname, envPath),
    'utf-8'
  );

  // Extract Firebase config from environment file
  // This is a simple regex-based extraction; in production, consider using a proper TypeScript parser
  const firebaseConfigMatch = envFile.match(/firebase:\s*{([^}]+)}/s);
  if (!firebaseConfigMatch) {
    throw new Error('Firebase config not found in environment file');
  }

  const firebaseConfigStr = firebaseConfigMatch[1];

  // Extract individual values
  const extractValue = (key) => {
    const match = firebaseConfigStr.match(new RegExp(`${key}:\\s*["']([^"']+)["']`));
    return match ? match[1] : null;
  };

  environment = {
    firebase: {
      apiKey: extractValue('apiKey'),
      authDomain: extractValue('authDomain'),
      projectId: extractValue('projectId'),
      storageBucket: extractValue('storageBucket'),
      messagingSenderId: extractValue('messagingSenderId'),
      appId: extractValue('appId')
    }
  };

  console.log('Loaded Firebase configuration from environment');

} catch (error) {
  console.error('Error loading environment:', error.message);
  process.exit(1);
}

// Validate Firebase config
const requiredKeys = ['apiKey', 'authDomain', 'projectId', 'messagingSenderId', 'appId'];
const missingKeys = requiredKeys.filter(key => !environment.firebase[key] || environment.firebase[key] === 'YOUR_API_KEY' || environment.firebase[key] === 'YOUR_APP_ID');

if (missingKeys.length > 0) {
  console.warn(`⚠️  Warning: Firebase config contains placeholder values for: ${missingKeys.join(', ')}`);
  console.warn('⚠️  The service worker will be generated but may not work correctly.');
  console.warn('⚠️  Update your environment file with actual Firebase credentials.');
}

// Service worker template
const serviceWorkerTemplate = `// Firebase Cloud Messaging Service Worker
// Auto-generated from scripts/generate-sw.js - DO NOT EDIT MANUALLY
// This file is generated during build with Firebase config from environment

importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js');

// Initialize Firebase app in service worker
// Configuration injected at build time from environment file
firebase.initializeApp({
  apiKey: "${environment.firebase.apiKey}",
  authDomain: "${environment.firebase.authDomain}",
  projectId: "${environment.firebase.projectId}",
  storageBucket: "${environment.firebase.storageBucket}",
  messagingSenderId: "${environment.firebase.messagingSenderId}",
  appId: "${environment.firebase.appId}"
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
`;

// Write the service worker file
const outputPath = path.join(__dirname, '../public/firebase-messaging-sw.js');

try {
  fs.writeFileSync(outputPath, serviceWorkerTemplate);
  console.log(`✅ Successfully generated service worker at: ${outputPath}`);
  console.log(`   Environment: ${isProduction ? 'production' : 'development'}`);
  console.log(`   Project ID: ${environment.firebase.projectId}`);
} catch (error) {
  console.error('❌ Error writing service worker file:', error.message);
  process.exit(1);
}
