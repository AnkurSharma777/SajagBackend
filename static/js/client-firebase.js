// Sample Client-Side Firebase Integration
// Save this as: static/js/client-firebase.js

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
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

// Your VAPID key from Firebase Console
const vapidKey = 'your-vapid-key-here';

class DisasterAlertClient {
    constructor() {
        this.init();
    }

    async init() {
        try {
            // Request notification permission
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Notification permission granted.');
                await this.setupFCM();
            } else {
                console.log('Notification permission denied.');
            }
        } catch (error) {
            console.error('Error initializing disaster alert client:', error);
        }
    }

    async setupFCM() {
        try {
            // Get FCM token
            const currentToken = await getToken(messaging, { vapidKey });

            if (currentToken) {
                console.log('FCM Token:', currentToken);

                // Register token with our backend
                await this.registerToken(currentToken);

                // Subscribe to disaster alerts topic
                await this.subscribeToTopic('disaster_alerts');

                // Listen for foreground messages
                this.setupMessageListener();

            } else {
                console.log('No registration token available.');
            }
        } catch (error) {
            console.error('An error occurred while retrieving token:', error);
        }
    }

    async registerToken(token) {
        try {
            const response = await fetch('/api/register_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token: token,
                    device_info: this.getDeviceInfo()
                })
            });

            if (response.ok) {
                console.log('Token registered successfully');
            } else {
                console.error('Failed to register token');
            }
        } catch (error) {
            console.error('Error registering token:', error);
        }
    }

    async subscribeToTopic(topic) {
        // Note: Topic subscription is handled server-side in this implementation
        console.log(`Subscribed to topic: ${topic}`);
    }

    setupMessageListener() {
        // Handle foreground messages
        onMessage(messaging, (payload) => {
            console.log('Message received in foreground:', payload);

            // Extract disaster alert data
            const { notification, data } = payload;

            // Display custom notification
            this.showDisasterAlert({
                title: notification.title,
                body: notification.body,
                disaster_type: data.disaster_type,
                coordinates: {
                    lat: parseFloat(data.latitude) || null,
                    lng: parseFloat(data.longitude) || null
                },
                alert_id: data.alert_id,
                timestamp: data.timestamp
            });
        });
    }

    showDisasterAlert(alertData) {
        // Create custom alert UI
        const alertContainer = document.createElement('div');
        alertContainer.className = 'disaster-alert-popup';
        alertContainer.innerHTML = `
            <div class="alert-content">
                <div class="alert-header">
                    <span class="alert-icon">${this.getDisasterIcon(alertData.disaster_type)}</span>
                    <h3>${alertData.title}</h3>
                    <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
                </div>
                <div class="alert-body">
                    <p>${alertData.body}</p>
                    ${alertData.coordinates.lat ? 
                        `<div class="coordinates">
                            <strong>Safe Location:</strong> 
                            <a href="https://maps.google.com/?q=${alertData.coordinates.lat},${alertData.coordinates.lng}" 
                               target="_blank">
                                ${alertData.coordinates.lat.toFixed(6)}, ${alertData.coordinates.lng.toFixed(6)}
                            </a>
                        </div>` : ''
                    }
                    <div class="alert-time">
                        <small>Received: ${new Date(alertData.timestamp).toLocaleString()}</small>
                    </div>
                </div>
                <div class="alert-actions">
                    <button class="btn-acknowledge" onclick="this.acknowledgeAlert('${alertData.alert_id}')">
                        Acknowledge
                    </button>
                    <button class="btn-share" onclick="this.shareAlert('${alertData.alert_id}')">
                        Share
                    </button>
                </div>
            </div>
        `;

        // Add CSS styles if not already present
        if (!document.querySelector('#disaster-alert-styles')) {
            this.addAlertStyles();
        }

        // Add to page
        document.body.appendChild(alertContainer);

        // Auto-remove after 30 seconds if not acknowledged
        setTimeout(() => {
            if (alertContainer.parentNode) {
                alertContainer.remove();
            }
        }, 30000);

        // Play alert sound
        this.playAlertSound();
    }

    getDisasterIcon(type) {
        const icons = {
            'flood': '🌊',
            'fire': '🔥',
            'earthquake': '🏗️',
            'hurricane': '🌪️',
            'tornado': '🌀',
            'tsunami': '🌊',
            'landslide': '⛰️',
            'volcanic': '🌋'
        };
        return icons[type] || '⚠️';
    }

    addAlertStyles() {
        const styles = document.createElement('style');
        styles.id = 'disaster-alert-styles';
        styles.textContent = `
            .disaster-alert-popup {
                position: fixed;
                top: 20px;
                right: 20px;
                max-width: 400px;
                background: linear-gradient(135deg, #ff4757, #ff3742);
                color: white;
                border-radius: 10px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                z-index: 10000;
                animation: slideIn 0.3s ease-out;
            }

            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }

            .alert-content {
                padding: 20px;
            }

            .alert-header {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }

            .alert-icon {
                font-size: 24px;
                margin-right: 10px;
            }

            .alert-header h3 {
                flex: 1;
                margin: 0;
                font-size: 18px;
            }

            .close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .close-btn:hover {
                background: rgba(255,255,255,0.2);
            }

            .alert-body p {
                margin: 0 0 15px 0;
                line-height: 1.4;
            }

            .coordinates {
                margin-bottom: 10px;
                padding: 10px;
                background: rgba(255,255,255,0.1);
                border-radius: 5px;
            }

            .coordinates a {
                color: #fff;
                text-decoration: underline;
            }

            .alert-time {
                opacity: 0.8;
            }

            .alert-actions {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }

            .alert-actions button {
                flex: 1;
                padding: 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                transition: opacity 0.2s;
            }

            .btn-acknowledge {
                background: #2ed573;
                color: white;
            }

            .btn-share {
                background: #1e90ff;
                color: white;
            }

            .alert-actions button:hover {
                opacity: 0.8;
            }

            @media (max-width: 480px) {
                .disaster-alert-popup {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                    max-width: none;
                }
            }
        `;
        document.head.appendChild(styles);
    }

    playAlertSound() {
        try {
            // Create audio context for alert sound
            const audioContext = new AudioContext();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime + 0.2);

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (error) {
            console.log('Could not play alert sound:', error);
        }
    }

    acknowledgeAlert(alertId) {
        // Send acknowledgment to server
        fetch('/api/acknowledge_alert', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: alertId })
        }).then(() => {
            console.log('Alert acknowledged:', alertId);
        });
    }

    shareAlert(alertId) {
        // Share alert using Web Share API if available
        if (navigator.share) {
            navigator.share({
                title: 'Emergency Alert',
                text: 'Important disaster alert - please stay safe!',
                url: window.location.href
            });
        } else {
            // Fallback to copying to clipboard
            navigator.clipboard.writeText(`Emergency Alert: ${window.location.href}`);
            alert('Alert link copied to clipboard!');
        }
    }

    getDeviceInfo() {
        return `${navigator.platform}, ${navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}`;
    }
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    new DisasterAlertClient();
});

// Service Worker registration for background notifications
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
        .then((registration) => {
            console.log('Service Worker registered:', registration);
        })
        .catch((error) => {
            console.error('Service Worker registration failed:', error);
        });
}
