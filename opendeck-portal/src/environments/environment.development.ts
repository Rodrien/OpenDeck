export const environment = {
  production: false,
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
  }
};
