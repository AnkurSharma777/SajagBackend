// firebase-messaging-sw.js - Service Worker for background notifications

importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Firebase configuration (replace with your config)
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com", 
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Received background message:', payload);

  const { notification, data } = payload;

  const notificationTitle = notification.title || 'Emergency Alert';
  const notificationOptions = {
    body: notification.body,
    icon: '/static/icon-192.png',
    badge: '/static/badge-72.png',
    tag: `disaster-alert-${data.alert_id}`,
    requireInteraction: true,
    actions: [
      {
        action: 'acknowledge',
        title: 'Acknowledge',
        icon: '/static/check-icon.png'
      },
      {
        action: 'view',
        title: 'View Details',
        icon: '/static/view-icon.png'
      }
    ],
    data: {
      disaster_type: data.disaster_type,
      alert_id: data.alert_id,
      latitude: data.latitude,
      longitude: data.longitude,
      timestamp: data.timestamp,
      url: '/'
    }
  };

  // Show notification
  return self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event);

  event.notification.close();

  const action = event.action;
  const data = event.notification.data;

  if (action === 'acknowledge') {
    // Send acknowledgment
    event.waitUntil(
      fetch('/api/acknowledge_alert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: data.alert_id })
      })
    );
  } else {
    // Open the app
    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // Focus existing window if open
        for (const client of clientList) {
          if (client.url === data.url && 'focus' in client) {
            return client.focus();
          }
        }

        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(data.url);
        }
      })
    );
  }
});
