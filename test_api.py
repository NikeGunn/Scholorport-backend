"""
Test script for Scholarport Backend API.

This script tests all the major API endpoints to ensure they work correctly.
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://127.0.0.1:8000/api/chat"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health/")
        print(f"✅ Health Check Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")
        return False

def test_start_conversation():
    """Test starting a new conversation"""
    print("\n🚀 Testing Start Conversation...")
    try:
        response = requests.post(f"{BASE_URL}/start/")
        print(f"✅ Start Conversation Status: {response.status_code}")
        data = response.json()
        print(f"   Session ID: {data.get('session_id')}")
        print(f"   Current Step: {data.get('current_step')}")
        print(f"   Message: {data.get('message')[:50]}...")
        return data.get('session_id')
    except Exception as e:
        print(f"❌ Start Conversation Failed: {e}")
        return None

def test_send_message(session_id):
    """Test sending a message in conversation"""
    print("\n💬 Testing Send Message...")
    try:
        # Send a name response
        payload = {
            "session_id": session_id,
            "message": "My name is John Smith"
        }
        response = requests.post(f"{BASE_URL}/send/", json=payload)
        print(f"✅ Send Message Status: {response.status_code}")
        data = response.json()
        print(f"   Current Step: {data.get('current_step')}")
        print(f"   Bot Response: {data.get('bot_response')[:50]}...")
        print(f"   Completed: {data.get('completed')}")
        return True
    except Exception as e:
        print(f"❌ Send Message Failed: {e}")
        return False

def test_get_universities():
    """Test getting universities list"""
    print("\n🏫 Testing Get Universities...")
    try:
        response = requests.get(f"{BASE_URL}/universities/?limit=5")
        print(f"✅ Get Universities Status: {response.status_code}")
        data = response.json()
        print(f"   Total Count: {data.get('total_count')}")
        universities = data.get('universities', [])
        if universities:
            print(f"   First University: {universities[0].get('name')}")
            print(f"   Country: {universities[0].get('country')}")
        return True
    except Exception as e:
        print(f"❌ Get Universities Failed: {e}")
        return False

def test_admin_dashboard():
    """Test admin dashboard stats"""
    print("\n📊 Testing Admin Dashboard...")
    try:
        response = requests.get(f"{BASE_URL}/admin/stats/")
        print(f"✅ Admin Dashboard Status: {response.status_code}")
        data = response.json()
        stats = data.get('stats', {})
        print(f"   Total Conversations: {stats.get('total_conversations')}")
        print(f"   Total Profiles: {stats.get('total_profiles')}")
        print(f"   Completion Rate: {stats.get('completion_rate')}%")
        return True
    except Exception as e:
        print(f"❌ Admin Dashboard Failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Scholarport Backend API Test Suite")
    print("=" * 50)

    # Track test results
    results = []

    # Test health check
    results.append(test_health_check())

    # Test start conversation
    session_id = test_start_conversation()
    results.append(session_id is not None)

    # Test send message (if we have a session)
    if session_id:
        results.append(test_send_message(session_id))
    else:
        results.append(False)

    # Test universities
    results.append(test_get_universities())

    # Test admin dashboard
    results.append(test_admin_dashboard())

    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Results Summary")
    print("=" * 50)

    test_names = [
        "Health Check",
        "Start Conversation",
        "Send Message",
        "Get Universities",
        "Admin Dashboard"
    ]

    passed = sum(results)
    total = len(results)

    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i+1}. {name:<20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()