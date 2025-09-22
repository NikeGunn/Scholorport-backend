#!/usr/bin/env python
"""
Test Firebase export endpoints
"""

import requests
import json

def test_firebase_endpoints():
    """Test both JSON and Excel endpoints"""

    base_url = "http://127.0.0.1:8000/api/chat/admin/firebase-export/"

    print("🔥 Testing Firebase Export Endpoints...")
    print("=" * 50)

    # Test JSON format
    print("\n1️⃣ Testing JSON format...")
    try:
        response = requests.get(f"{base_url}?format=json", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("✅ JSON export SUCCESS!")
            if 'application/json' in response.headers.get('content-type', ''):
                data = response.json()
                print(f"Records found: {len(data)}")
            else:
                print("Content is not JSON (probably downloadable file)")
        else:
            print(f"❌ JSON export FAILED: {response.text}")
    except Exception as e:
        print(f"❌ JSON export ERROR: {e}")

    # Test Excel format
    print("\n2️⃣ Testing Excel format...")
    try:
        response = requests.get(f"{base_url}?format=excel", timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Content-Length: {len(response.content)} bytes")

        if response.status_code == 200:
            print("✅ Excel export SUCCESS!")
        else:
            print(f"❌ Excel export FAILED: {response.text}")
    except Exception as e:
        print(f"❌ Excel export ERROR: {e}")

    # Test health check for comparison
    print("\n3️⃣ Testing Health Check (for comparison)...")
    try:
        response = requests.get("http://127.0.0.1:8000/api/chat/health/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health check SUCCESS!")
            data = response.json()
            print(f"Message: {data.get('message', 'No message')}")
        else:
            print(f"❌ Health check FAILED: {response.text}")
    except Exception as e:
        print(f"❌ Health check ERROR: {e}")

if __name__ == "__main__":
    test_firebase_endpoints()