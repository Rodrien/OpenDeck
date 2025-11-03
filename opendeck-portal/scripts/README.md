# Service Worker Generation Scripts

## Overview

This directory contains scripts for generating build-time files that require configuration injection.

## Firebase Messaging Service Worker

### Problem

Firebase Cloud Messaging service workers run in a separate context and cannot access environment variables or Angular's environment configuration. The service worker needs Firebase credentials to initialize the messaging instance.

### Solution

The `generate-sw.js` script generates the Firebase messaging service worker (`public/firebase-messaging-sw.js`) at build time by:

1. Reading the Firebase configuration from the appropriate environment file
2. Injecting the configuration into the service worker template
3. Writing the generated file to `public/firebase-messaging-sw.js`

### Usage

The script is automatically run before `npm start` and `npm run build` via npm's `prebuild` and `prestart` hooks.

**Manual generation:**
```bash
# Generate for development
npm run generate-sw development

# Generate for production
npm run generate-sw production
```

### Files

- `generate-sw.js` - Script that generates the service worker
- `../public/firebase-messaging-sw.template.js` - Template file (optional reference)
- `../public/firebase-messaging-sw.js` - **Generated file** (gitignored)

### Configuration

Firebase credentials are read from:
- **Development**: `src/environments/environment.development.ts`
- **Production**: `src/environments/environment.ts`

**Important**: Update these files with your actual Firebase project credentials from the [Firebase Console](https://console.firebase.google.com/).

### Warnings

The script will warn you if placeholder values are detected in the Firebase configuration:
```
⚠️  Warning: Firebase config contains placeholder values for: apiKey, appId
⚠️  The service worker will be generated but may not work correctly.
⚠️  Update your environment file with actual Firebase credentials.
```

### Git

The generated `firebase-messaging-sw.js` file is gitignored because it contains environment-specific configuration. Each developer/environment must generate their own version using the script.

### Adding Real Firebase Credentials

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select or create your project
3. Go to Project Settings > General
4. Under "Your apps", select or add a Web app
5. Copy the Firebase configuration object
6. Update `src/environments/environment.ts` and `src/environments/environment.development.ts`
7. Run `npm run generate-sw` to regenerate the service worker

Example configuration:
```typescript
firebase: {
  apiKey: "AIzaSyC...",
  authDomain: "opendeck-xxxxx.firebaseapp.com",
  projectId: "opendeck-xxxxx",
  storageBucket: "opendeck-xxxxx.appspot.com",
  messagingSenderId: "1234567890",
  appId: "1:1234567890:web:abcdef...",
  vapidKey: "BNxxx..."  // From Cloud Messaging > Web Push certificates
}
```

## Future Scripts

Additional build-time generation scripts can be added to this directory following the same pattern.
