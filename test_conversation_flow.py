"""
Test complete conversation flow to verify profile creation works correctly.
"""

import requests
import json

# Base URL for testing
BASE_URL = "http://127.0.0.1:8000/api/chat"

def test_complete_conversation_with_profile():
    """Test a complete 5-step conversation to ensure profile is created"""

    print("🚀 Testing Complete Conversation Flow...")
    print("=" * 60)

    # Step 1: Start conversation
    print("\n1️⃣ Starting new conversation...")
    response = requests.post(f"{BASE_URL}/start/")
    if response.status_code == 201:
        data = response.json()
        session_id = data['session_id']
        print(f"✅ Session started: {session_id}")
    else:
        print(f"❌ Failed to start conversation: {response.text}")
        return

    # Step 2: Send name
    print("\n2️⃣ Sending name...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "My name is Alice Johnson"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Step: {data.get('current_step')}, Completed: {data.get('completed')}")
    else:
        print(f"❌ Error: {response.text}")

    # Step 3: Send education
    print("\n3️⃣ Sending education...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I have a Master's degree in Business Administration"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Step: {data.get('current_step')}, Completed: {data.get('completed')}")

    # Step 4: Send test score
    print("\n4️⃣ Sending test score...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I have IELTS 7.5"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Step: {data.get('current_step')}, Completed: {data.get('completed')}")

    # Step 5: Send budget
    print("\n5️⃣ Sending budget...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "My budget is $30,000 USD per year"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Step: {data.get('current_step')}, Completed: {data.get('completed')}")

    # Step 6: Send country (FINAL)
    print("\n6️⃣ Sending country preference (FINAL)...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "I want to study in Australia"
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Step: {data.get('current_step')}, Completed: {data.get('completed')}")
        if data.get('completed'):
            print(f"✅ CONVERSATION COMPLETED!")
            if 'recommendations' in data:
                print(f"📚 Got {len(data['recommendations'])} university recommendations")
                for i, uni in enumerate(data['recommendations'], 1):
                    print(f"   {i}. {uni.get('name')} in {uni.get('city')}")
            if data.get('profile_created'):
                print(f"👤 PROFILE CREATED! ID: {data.get('profile_id')}")
            else:
                print(f"❌ Profile NOT created!")
        else:
            print(f"❌ Conversation not completed yet")
    else:
        print(f"❌ Error: {response.text}")

    # Step 7: Check conversation history
    print("\n7️⃣ Checking conversation history...")
    response = requests.get(f"{BASE_URL}/conversation/{session_id}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ History retrieved: {len(data.get('messages', []))} messages")
        print(f"Conversation completed: {data.get('completed')}")

    # Step 8: Check admin profiles to see if profile was created
    print("\n8️⃣ Checking if profile appears in admin...")
    response = requests.get(f"{BASE_URL}/admin/profiles/")
    if response.status_code == 200:
        data = response.json()
        profile_count = len(data.get('profiles', []))
        print(f"✅ Total profiles in admin: {profile_count}")
        if profile_count > 0:
            latest_profile = data['profiles'][0]
            print(f"Latest profile: {latest_profile.get('student_name')} - {latest_profile.get('preferred_country')}")

    print("\n" + "=" * 60)
    print("🏁 Complete Conversation Test Finished!")

if __name__ == "__main__":
    test_complete_conversation_with_profile()