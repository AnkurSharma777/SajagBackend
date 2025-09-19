import requests
import json

# Your Flask server URL
BASE_URL = "http://localhost:5000"

# Example: Send a disaster alert via API
def send_disaster_alert():
    url = f"{BASE_URL}/send_alert"
    
    data = {
        "disaster_type": "flood",
        "message": "Flash flood warning in downtown area. Move to higher ground immediately.",
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Alert sent successfully!")
        print(f"Alert ID: {result['alert_id']}")
        print(f"Message: {result['message']}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

# Call the function
send_disaster_alert()


