#!/usr/bin/env python
"""
Create a complete conversation to test admin endpoints with data.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

def create_complete_conversation():
    """Create a complete 5-step conversation for testing"""

    print("🚀 Creating Complete Conversation for Admin Testing")
    print("=" * 60)

    # Step 1: Start conversation
    print("\n1. Starting new conversation...")
    response = requests.post(f"{BASE_URL}/start/")
    if response.status_code == 201:
        data = response.json()
        session_id = data['session_id']
        print(f"   ✅ Started: Session ID = {session_id}")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    # Step 2: Send name
    print("\n2. Sending name...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "My name is Sarah Johnson"
    })
    if response.status_code == 200:
        print("   ✅ Name sent successfully")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    # Step 3: Send education
    print("\n3. Sending education...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I have a Bachelor's degree in Engineering"
    })
    if response.status_code == 200:
        print("   ✅ Education sent successfully")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    # Step 4: Send test score
    print("\n4. Sending test score...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I have IELTS 7.5"
    })
    if response.status_code == 200:
        print("   ✅ Test score sent successfully")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    # Step 5: Send budget
    print("\n5. Sending budget...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "My budget is $30,000 USD per year"
    })
    if response.status_code == 200:
        print("   ✅ Budget sent successfully")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    # Step 6: Send country preference (Final step)
    print("\n6. Sending country preference (FINAL)...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I want to study in Australia"
    })
    if response.status_code == 200:
        data = response.json()
        print("   ✅ Conversation completed!")
        print(f"   Completed: {data.get('completed', False)}")
        print(f"   Recommendations: {len(data.get('recommendations', []))}")
        print(f"   Profile created: {data.get('profile_created', False)}")
    else:
        print(f"   ❌ Failed: {response.text}")
        return

    print(f"\n🎯 Complete conversation created with session: {session_id}")
    return session_id

def test_admin_with_data():
    """Test admin endpoints with the newly created data"""

    print("\n\n📊 Testing Admin Endpoints with Data")
    print("=" * 60)

    # Test profiles endpoint
    print("\n1. Testing admin profiles...")
    response = requests.get(f"{BASE_URL}/admin/profiles/?limit=10")
    if response.status_code == 200:
        data = response.json()
        total = data.get('pagination', {}).get('total_count', 0)
        profiles = data.get('profiles', [])
        print(f"   ✅ Success: Found {total} total profiles")
        print(f"   Profiles returned: {len(profiles)}")

        if profiles:
            profile = profiles[0]
            print(f"   Sample profile: {profile.get('student_name')} -> {profile.get('preferred_country')}")
    else:
        print(f"   ❌ Error: {response.text}")

    # Test export
    print("\n2. Testing Excel export...")
    response = requests.get(f"{BASE_URL}/admin/export/")
    if response.status_code == 200:
        print("   ✅ Excel export working!")
        print(f"   Content-Type: {response.headers.get('Content-Type')}")
    else:
        print(f"   ❌ Error: {response.text}")

if __name__ == "__main__":
    session_id = create_complete_conversation()
    if session_id:
        test_admin_with_data()