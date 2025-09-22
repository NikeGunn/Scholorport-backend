"""
Debug API test to see detailed error messages.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

def debug_start_conversation():
    """Debug start conversation endpoint"""
    print("🔍 Debugging Start Conversation...")
    try:
        response = requests.post(f"{BASE_URL}/start/")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"JSON Response: {response.json()}")
    except Exception as e:
        print(f"Exception: {e}")

def debug_admin_dashboard():
    """Debug admin dashboard endpoint"""
    print("\n🔍 Debugging Admin Dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/admin/stats/")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"JSON Response: {response.json()}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_start_conversation()
    debug_admin_dashboard()