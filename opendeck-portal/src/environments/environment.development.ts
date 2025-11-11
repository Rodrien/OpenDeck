export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000/api/v1',
  apiHealthUrl: 'http://localhost:8000/health',
  // TODO: Replace with actual Firebase configuration from Firebase Console
  // See: https://console.firebase.google.com/
  firebase: {
    apiKey: "AIzaSyBK2_lyT8RFrD4XNJYlchNAIisN__A5loU",
    authDomain: "opendeck-59718.firebaseapp.com",
    projectId: "opendeck-59718",
    storageBucket: "opendeck-59718.firebasestorage.app",
    messagingSenderId: "1025215022520",
    appId: "1:1025215022520:web:d81e4a8911c13ad4d43b4d",
    measurementId: "G-KK0C1NT91G",
    vapidKey: "BA059KqD0PmLOqkJtzqgn5mjhrPOoS7sChq5fEp81R9BQI5Xkp-oNPULtMFgUYf6vkolrZF--VCtmJkpUhaAk00"  // For web push (found in Cloud Messaging settings)
  }
};
