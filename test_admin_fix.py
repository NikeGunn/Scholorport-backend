#!/usr/bin/env python
"""
Test script to verify admin endpoints are working after field name fixes.
"""

import requests
import json

# Base URL for API
BASE_URL = "http://127.0.0.1:8000/api/chat"

def test_admin_endpoints():
    """Test all admin endpoints to verify fixes"""

    print("🔧 Testing Admin Endpoint Fixes")
    print("=" * 50)

    # Test 1: Admin profiles endpoint
    print("\n1. Testing admin profiles endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/admin/profiles/?limit=10&offset=0", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {data.get('pagination', {}).get('total_count', 0)} profiles")
            print(f"   Profiles returned: {len(data.get('profiles', []))}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

    # Test 2: Admin profiles with filters
    print("\n2. Testing admin profiles with filters...")
    try:
        response = requests.get(f"{BASE_URL}/admin/profiles/?country=Canada&completed_only=true", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Found {data.get('pagination', {}).get('total_count', 0)} Canada profiles")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

    # Test 3: Admin export endpoint
    print("\n3. Testing admin export endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/admin/export/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Success: Excel export working")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

    # Test 4: Admin stats endpoint
    print("\n4. Testing admin stats endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/admin/stats/", timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: Stats endpoint working")
            stats = data.get('stats', {})
            print(f"   Total conversations: {stats.get('total_conversations', 0)}")
            print(f"   Completed conversations: {stats.get('completed_conversations', 0)}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")

    print("\n" + "=" * 50)
    print("🎯 Admin endpoint testing completed!")

if __name__ == "__main__":
    test_admin_endpoints()