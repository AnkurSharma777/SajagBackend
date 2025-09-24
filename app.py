from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
import firebase_admin
from firebase_admin import credentials, messaging
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)
# Use environment variable for secret key in production
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')


# Initialize Firebase Admin SDK
def init_firebase():
    try:
        # FOR RAILWAY: Check if Firebase credentials are in environment variable
        if os.environ.get('FIREBASE_CREDENTIALS'):
            # Parse Firebase credentials from environment variable
            firebase_credentials = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
            cred = credentials.Certificate(firebase_credentials)
            print("Using Firebase credentials from environment variable")
        else:
            # FOR LOCAL: Use service account key file
            cred = credentials.Certificate('serviceAccountKey.json')
            print("Using Firebase credentials from serviceAccountKey.json")

        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
        return True
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        return False


# Initialize database
def init_db():
    conn = sqlite3.connect('disaster_alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS alerts
                   (
                       id            INTEGER PRIMARY KEY AUTOINCREMENT,
                       disaster_type TEXT NOT NULL,
                       message       TEXT NOT NULL,
                       latitude      REAL,
                       longitude     REAL,
                       timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,
                       status        TEXT     DEFAULT 'sent'
                   )
                   ''')

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS user_tokens
                   (
                       id          INTEGER PRIMARY KEY AUTOINCREMENT,
                       token       TEXT UNIQUE NOT NULL,
                       device_info TEXT,
                       created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                   )
                   ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully")


# Initialize Firebase and Database on startup
firebase_initialized = init_firebase()
init_db()


@app.route('/')
def dashboard():
    """Admin Dashboard - Main page"""
    return render_template('dashboard.html')


@app.route('/send_alert', methods=['POST'])
def send_alert():
    """Send disaster alert via Firebase push notification"""
    try:
        # Get data from form or JSON
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()

        disaster_type = data.get('disaster_type')
        message = data.get('message')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Validate required fields
        if not disaster_type or not message:
            if request.is_json:
                return jsonify({'error': 'Disaster type and message are required'}), 400
            else:
                flash('Disaster type and message are required', 'error')
                return redirect(url_for('dashboard'))

        # Convert coordinates to float if provided
        try:
            if latitude:
                latitude = float(latitude)
            if longitude:
                longitude = float(longitude)
        except ValueError:
            if request.is_json:
                return jsonify({'error': 'Invalid coordinates format'}), 400
            else:
                flash('Invalid coordinates format', 'error')
                return redirect(url_for('dashboard'))

        # Store alert in database
        conn = sqlite3.connect('disaster_alerts.db')
        cursor = conn.cursor()
        cursor.execute('''
                       INSERT INTO alerts (disaster_type, message, latitude, longitude)
                       VALUES (?, ?, ?, ?)
                       ''', (disaster_type, message, latitude, longitude))
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Send Firebase push notification if initialized
        if firebase_initialized:
            try:
                # Create notification message
                notification_title = f"🚨 {disaster_type.upper()} ALERT"
                notification_body = message

                # Add location info if provided
                if latitude and longitude:
                    notification_body += f"\n📍 Safe Location: {latitude}, {longitude}"

                # Create the message (topic-based for all users)
                message_obj = messaging.Message(
                    notification=messaging.Notification(
                        title=notification_title,
                        body=notification_body[:100] + "..." if len(notification_body) > 100 else notification_body,
                    ),
                    data={
                        'disaster_type': disaster_type,
                        'full_message': message,
                        'latitude': str(latitude) if latitude else '',
                        'longitude': str(longitude) if longitude else '',
                        'alert_id': str(alert_id),
                        'timestamp': datetime.now().isoformat()
                    },
                    topic='disaster_alerts'  # Send to all subscribed users
                )

                # Send the message
                response = messaging.send(message_obj)
                print(f'Successfully sent message: {response}')

                # Update database with success status
                conn = sqlite3.connect('disaster_alerts.db')
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE alerts
                               SET status = 'sent_successfully'
                               WHERE id = ?
                               ''', (alert_id,))
                conn.commit()
                conn.close()

            except Exception as e:
                print(f'Error sending Firebase message: {e}')
                # Update database with error status
                conn = sqlite3.connect('disaster_alerts.db')
                cursor = conn.cursor()
                cursor.execute('''
                               UPDATE alerts
                               SET status = 'firebase_error'
                               WHERE id = ?
                               ''', (alert_id,))
                conn.commit()
                conn.close()

        # Return response
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Alert sent successfully',
                'alert_id': alert_id
            })
        else:
            flash('Alert sent successfully!', 'success')
            return redirect(url_for('dashboard'))

    except Exception as e:
        print(f'Error in send_alert: {e}')
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error sending alert: {str(e)}', 'error')
            return redirect(url_for('dashboard'))


@app.route('/alerts_history')
def alerts_history():
    """View sent alerts history"""
    conn = sqlite3.connect('disaster_alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
                   SELECT id, disaster_type, message, latitude, longitude, timestamp, status
                   FROM alerts
                   ORDER BY timestamp DESC
                   LIMIT 50
                   ''')
    alerts = cursor.fetchall()
    conn.close()

    return render_template('alerts_history.html', alerts=alerts)


@app.route('/api/register_token', methods=['POST'])
def register_token():
    """Register FCM token for a device"""
    try:
        data = request.get_json()
        token = data.get('token')
        device_info = data.get('device_info', '')

        if not token:
            return jsonify({'error': 'Token is required'}), 400

        conn = sqlite3.connect('disaster_alerts.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_tokens (token, device_info)
            VALUES (?, ?)
        ''', (token, device_info))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Token registered successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ADDED FOR RAILWAY: Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'firebase_initialized': firebase_initialized
    })


@app.route('/api/emergency_assistance', methods=['POST'])
def emergency_assistance():
    """Handle user emergency assistance requests with location"""
    try:
        data = request.get_json()
        user_token = data.get('token', 'anonymous')
        user_name = data.get('user_name', 'Unknown User')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        message = data.get('message', 'Emergency assistance needed')
        device_info = data.get('device_info', '')

        # Validate required fields
        if not latitude or not longitude:
            return jsonify({'error': 'Location coordinates are required'}), 400

        # Convert coordinates to float
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return jsonify({'error': 'Invalid coordinates format'}), 400

        # Store assistance request in database
        conn = sqlite3.connect('disaster_alerts.db')
        cursor = conn.cursor()

        # Create assistance_requests table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assistance_requests
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_token TEXT,
                user_name TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                message TEXT,
                device_info TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'high'
            )
        ''')

        # Insert assistance request
        cursor.execute('''
            INSERT INTO assistance_requests
            (user_token, user_name, latitude, longitude, message, device_info)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_token, user_name, latitude, longitude, message, device_info))

        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        print(f'Emergency assistance request received: ID {request_id}, Location: {latitude}, {longitude}')

        return jsonify({
            'success': True,
            'message': 'Emergency assistance request received',
            'request_id': request_id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        print(f'Error handling assistance request: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/assistance_requests')
def view_assistance_requests():
    """Admin view for assistance requests"""
    conn = sqlite3.connect('disaster_alerts.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_name, latitude, longitude, message, device_info, timestamp, status
        FROM assistance_requests
        ORDER BY timestamp DESC
        LIMIT 100
    ''')
    requests = cursor.fetchall()
    conn.close()

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emergency Assistance Requests</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #dc3545; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .request-card {{
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 10px 0;
                background: #f8f9fa;
            }}
            .urgent {{ border-left: 5px solid #dc3545; }}
            .map-link {{
                background: #007bff;
                color: white;
                padding: 5px 10px;
                text-decoration: none;
                border-radius: 4px;
                margin: 5px;
            }}
            .status-pending {{ color: #dc3545; font-weight: bold; }}
            .timestamp {{ color: #6c757d; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚨 Emergency Assistance Requests</h1>
            <p>Real-time rescue requests from users</p>
        </div>

        {"".join([f'''
        <div class="request-card urgent">
            <h3>📍 Request #{req[0]} - {req[1]}</h3>
            <p><strong>Message:</strong> {req[4]}</p>
            <p><strong>Location:</strong> {req[2]}, {req[3]}</p>
            <p><strong>Device:</strong> {req[5]}</p>
            <p class="timestamp"><strong>Time:</strong> {req[6]}</p>
            <p class="status-pending">Status: {req[7].upper()}</p>
            <div>
                <a href="https://www.google.com/maps?q={req[2]},{req[3]}" target="_blank" class="map-link">🗺️ View on Google Maps</a>
                <a href="https://www.google.com/maps/dir/{req[2]},{req[3]}" target="_blank" class="map-link">🚗 Get Directions</a>
            </div>
        </div>
        ''' for req in requests]) if requests else '<p>No assistance requests yet.</p>'}

        <hr>
        <p><a href="/">← Back to Dashboard</a> | <a href="/alerts_history">📊 Alert History</a></p>
    </body>
    </html>
    '''


if __name__ == '__main__':
    # FOR RAILWAY: Use PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    # FOR RAILWAY: Bind to 0.0.0.0 and disable debug in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
    