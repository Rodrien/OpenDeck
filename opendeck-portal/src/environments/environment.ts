export const environment = {
  production: true,
  apiBaseUrl: 'http://localhost:8000/api/v1',
  apiHealthUrl: 'http://localhost:8000/health',
  // TODO: Replace with actual Firebase configuration from Firebase Console
  // See: https://console.firebase.google.com/
  firebase: {
    apiKey: "YOUR_API_KEY",
    authDomain: "opendeck.firebaseapp.com",
    projectId: "opendeck",
    storageBucket: "opendeck.appspot.com",
    messagingSenderId: "123456789",
    appId: "YOUR_APP_ID",
    vapidKey: "YOUR_VAPID_KEY"  // For web push (found in Cloud Messaging settings)
  },
  // Google OAuth configuration
  // TODO: Replace with actual Google OAuth credentials from Google Cloud Console
  // See: https://console.cloud.google.com/apis/credentials
  google: {
    clientId: "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com",
    redirectUri: "http://localhost:4200/auth/google/callback"
  }
};
