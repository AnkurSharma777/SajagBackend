#!/usr/bin/env python3
# test_api.py - Test script for disaster alert API

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
HEADERS = {"Content-Type": "application/json"}

def test_send_alert():
    """Test sending a disaster alert"""
    print("🧪 Testing Send Alert API...")

    test_data = {
        "disaster_type": "flood",
        "message": "Test flood alert - this is a drill. Please remain calm and follow evacuation procedures.",
        "latitude": 40.7128,
        "longitude": -74.0060
    }

    try:
        response = requests.post(
            f"{BASE_URL}/send_alert",
            headers=HEADERS,
            json=test_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Alert sent successfully!")
            print(f"   Alert ID: {result.get('alert_id')}")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to send alert: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_register_token():
    """Test registering FCM token"""
    print("\n🧪 Testing Register Token API...")

    test_data = {
        "token": f"test-fcm-token-{int(time.time())}",
        "device_info": "Test Device - Python Script"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/register_token",
            headers=HEADERS,
            json=test_data,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Token registered successfully!")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to register token: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def test_alerts_history():
    """Test getting alerts history"""
    print("\n🧪 Testing Alerts History...")

    try:
        response = requests.get(f"{BASE_URL}/alerts_history", timeout=10)

        if response.status_code == 200:
            print("✅ Alerts history retrieved successfully!")
            print(f"   Page length: {len(response.text)} characters")
            return True
        else:
            print(f"❌ Failed to get alerts history: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

def run_comprehensive_tests():
    """Run all API tests"""
    print("🚀 Starting Disaster Alert System API Tests")
    print(f"⏰ Timestamp: {datetime.now()}")
    print(f"🌐 Base URL: {BASE_URL}")
    print("-" * 50)

    tests = [
        test_register_token,
        test_send_alert, 
        test_alerts_history
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Brief pause between tests

    print("-" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    return passed == total

def send_sample_alerts():
    """Send various sample alerts for testing"""
    print("\n🔥 Sending sample disaster alerts...")

    sample_alerts = [
        {
            "disaster_type": "fire",
            "message": "Wildfire detected in Pine Valley area. Residents should evacuate immediately via Highway 101 North.",
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        {
            "disaster_type": "earthquake", 
            "message": "Magnitude 6.2 earthquake detected. Drop, Cover, and Hold On. Check for injuries and hazards.",
            "latitude": 34.0522,
            "longitude": -118.2437
        },
        {
            "disaster_type": "hurricane",
            "message": "Hurricane Sarah approaching. Category 3 storm expected to make landfall in 6 hours. Seek shelter immediately.",
            "latitude": 25.7617,
            "longitude": -80.1918
        }
    ]

    success_count = 0

    for i, alert in enumerate(sample_alerts, 1):
        print(f"\n📡 Sending sample alert {i}/3: {alert['disaster_type'].title()}")

        try:
            response = requests.post(
                f"{BASE_URL}/send_alert",
                headers=HEADERS,
                json=alert,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Alert {result.get('alert_id')} sent successfully")
                success_count += 1
            else:
                print(f"   ❌ Failed: {response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Error: {e}")

        time.sleep(2)  # Pause between alerts

    print(f"\n📈 Sample alerts sent: {success_count}/3")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test Disaster Alert System API")
    parser.add_argument("--samples", action="store_true", help="Send sample alerts")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for API")

    args = parser.parse_args()
    BASE_URL = args.url

    if args.samples:
        send_sample_alerts()
    else:
        run_comprehensive_tests()
