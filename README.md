# Disaster Alert System

A Flask-based disaster management system with Firebase push notifications and admin dashboard.

## 🚀 Features

- **Admin Dashboard**: Web UI for sending disaster alerts
- **Firebase Integration**: Push notifications to all registered devices  
- **Multiple Disaster Types**: Flood, Fire, Earthquake, Hurricane, etc.
- **Location Support**: Include safe shelter coordinates
- **Alert History**: Track all sent alerts with status
- **API Endpoints**: RESTful API for integration
- **Database Storage**: SQLite database for alerts and user tokens

## 📋 Quick Start

### 1. Clone & Setup
```bash
git clone <repository>
cd SajagBackend
chmod +x setup.sh
./setup.sh
```

### 2. Configure Firebase
```bash
# Edit environment variables
cp .env.template .env
nano .env

# Add your Firebase service account key
# Download from Firebase Console → Project Settings → Service Accounts
# Save as: serviceAccountKey.json
```

### 3. Run Application
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

### 4. Access Dashboard
Open [http://localhost:5000](http://localhost:5000)

## 🔧 API Endpoints

### Send Alert
```http
POST /send_alert
Content-Type: application/json

{
    "disaster_type": "flood",
    "message": "Flash flood warning. Move to higher ground immediately.",
    "latitude": 40.7128,
    "longitude": -74.0060
}
```

### Register FCM Token
```http
POST /api/register_token
Content-Type: application/json

{
    "token": "fcm-token-here",
    "device_info": "Android 12, Chrome"
}
```

## 🧪 Testing with Postman

Import `disaster_alerts_postman.json` into Postman for pre-configured API tests.

## 📊 Database Schema

### Alerts Table
- `id`: Primary key
- `disaster_type`: Type of disaster
- `message`: Alert message
- `latitude`: Safe location latitude
- `longitude`: Safe location longitude  
- `timestamp`: When alert was sent
- `status`: Delivery status

### User Tokens Table
- `id`: Primary key
- `token`: FCM registration token
- `device_info`: Device information
- `created_at`: Registration timestamp

## 🔥 Firebase Setup

See [FIREBASE_SETUP.md](FIREBASE_SETUP.md) for detailed Firebase configuration instructions.

## 🛠️ Development

### Project Structure
```
SajagBackend/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── serviceAccountKey.json # Firebase credentials (not in repo)
├── .env                   # Environment variables (not in repo)
├── disaster_alerts.db     # SQLite database
├── templates/             # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   └── alerts_history.html
└── static/                # CSS, JS, images
```

### Adding New Disaster Types
Edit `dashboard.html` template and add new options to the disaster type dropdown:

```html
<option value="new_type">🌟 New Disaster Type</option>
```

## 📱 Client Integration

For mobile/web clients to receive notifications:

1. Initialize Firebase SDK
2. Subscribe to "disaster_alerts" topic
3. Register FCM tokens with `/api/register_token`
4. Handle incoming push notifications

## 🔒 Security Notes

- Change default secret key in production
- Use environment variables for sensitive config
- Implement rate limiting for API endpoints
- Add authentication for admin dashboard
- Use HTTPS in production

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.
