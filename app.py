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


if __name__ == '__main__':
    # FOR RAILWAY: Use PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    # FOR RAILWAY: Bind to 0.0.0.0 and disable debug in production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
