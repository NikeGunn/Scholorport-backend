#!/usr/bin/env python
"""
Debug conversation state to see what's happening.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

def debug_conversation():
    """Debug the conversation state"""

    print("🔍 Debugging Conversation State")
    print("=" * 50)

    # Check the last conversation from the database
    session_id = "45432651-b412-488e-bc56-0fdb2f9dc7df"

    print(f"\n📝 Getting conversation history for: {session_id}")
    response = requests.get(f"{BASE_URL}/conversation/{session_id}/")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Success")
        print(f"   Current Step: {data.get('current_step')}")
        print(f"   Completed: {data.get('completed')}")
        print(f"   Total Messages: {len(data.get('messages', []))}")

        # Show last few messages
        messages = data.get('messages', [])
        print(f"\n📨 Last 3 messages:")
        for msg in messages[-3:]:
            print(f"   {msg.get('type')}: {msg.get('content')[:80]}...")
            print(f"   Step: {msg.get('step_number')}")
    else:
        print(f"   ❌ Error: {response.text}")

    # Try sending another message to see what happens
    print(f"\n🧪 Testing message send...")
    response = requests.post(f"{BASE_URL}/send/", json={
        "session_id": session_id,
        "message": "test"
    })
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Current Step: {data.get('current_step')}")
        print(f"   Completed: {data.get('completed')}")
        print(f"   Recommendations: {len(data.get('recommendations', []))}")
    else:
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    debug_conversation()