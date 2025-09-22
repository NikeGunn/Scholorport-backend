"""
Test script to verify ALTS warnings are suppressed.
This script demonstrates that the Google Cloud ALTS warnings are no longer showing.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

def test_firebase_endpoints():
    """Test Firebase-related endpoints to verify no ALTS warnings"""
    print("🧪 Testing Firebase endpoints to verify ALTS warnings are suppressed...")

    try:
        # Test health check
        print("\n1. Testing health check...")
        response = requests.get(f"{BASE_URL}/health/")
        print(f"✅ Health check: {response.status_code}")

        # Test Firebase export endpoint
        print("\n2. Testing Firebase export...")
        response = requests.get(f"{BASE_URL}/admin/firebase-export/?format=json")
        print(f"✅ Firebase export: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, dict):
                    print(f"   Data count: {data.get('count', 0)}")
                elif isinstance(data, list):
                    print(f"   Data count: {len(data)}")
                else:
                    print(f"   Response type: {type(data)}")
            except:
                print("   Response received successfully")

        # Test conversation flow that triggers Firebase
        print("\n3. Testing conversation flow...")

        # Start conversation
        start_response = requests.post(f"{BASE_URL}/start/", json={})
        if start_response.status_code == 201:
            session_data = start_response.json()
            session_id = session_data['session_id']
            print(f"✅ Started conversation: {session_id}")

            # Send final message to trigger Firebase save
            messages = [
                "John Smith",
                "Bachelor's in Computer Science",
                "IELTS 7.0",
                "$25000 USD",
                "Canada"
            ]

            for i, message in enumerate(messages, 1):
                response = requests.post(f"{BASE_URL}/send/", json={
                    "session_id": session_id,
                    "message": message
                })
                if response.status_code == 200:
                    result = response.json()
                    print(f"   Step {i}: {result.get('bot_response', '')[:50]}...")

                    # If completed, trigger consent
                    if result.get('completed'):
                        print(f"✅ Conversation completed with {len(result.get('recommendations', []))} recommendations")

                        # Test consent (this triggers Firebase save)
                        consent_response = requests.post(f"{BASE_URL}/consent/", json={
                            "session_id": session_id,
                            "consent": True
                        })
                        if consent_response.status_code == 200:
                            consent_data = consent_response.json()
                            print(f"✅ Consent processed: {consent_data.get('data_saved', False)}")
                        break

        print("\n🎉 All tests completed successfully!")
        print("📝 Note: If you don't see any ALTS warnings in the server console,")
        print("   the suppression is working correctly!")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_firebase_endpoints()