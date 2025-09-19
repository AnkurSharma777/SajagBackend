# Firebase Setup Guide

## 1. Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name: `disaster-alert-system`
4. Follow the setup wizard

## 2. Enable Firebase Cloud Messaging (FCM)

1. In your Firebase project, go to "Project Settings" (gear icon)
2. Click on "Cloud Messaging" tab
3. Note down your "Server key" (you'll need this)

## 3. Generate Service Account Key

1. Go to Project Settings → Service Accounts
2. Click "Generate new private key"
3. Download the JSON file
4. Rename it to `serviceAccountKey.json`
5. Place it in your project root directory

## 4. Configure Environment Variables

Edit the `.env` file with your Firebase credentials from the service account JSON:

```
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
```

## 5. Test FCM

To test push notifications, you'll need a client app that:

1. Subscribes to the "disaster_alerts" topic
2. Registers FCM tokens with your backend
3. Handles incoming notifications

### Sample JavaScript (for web clients):

```javascript
// Initialize Firebase in your client app
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  // Your config
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Get FCM token
getToken(messaging, { vapidKey: 'your-vapid-key' }).then((currentToken) => {
  if (currentToken) {
    // Send token to your server
    fetch('/api/register_token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: currentToken })
    });
  }
});

// Handle incoming messages
onMessage(messaging, (payload) => {
  console.log('Message received:', payload);
  // Display notification to user
});
```

## 6. Troubleshooting

- Ensure service account has "Firebase Admin SDK" role
- Check that FCM is enabled in your Firebase project
- Verify that your service account key file is valid JSON
- Make sure your server can connect to Firebase APIs
