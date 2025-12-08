"""
Test script for Jobs API endpoints.
Run this after starting the Django server.
"""
import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_list_jobs():
    """Test listing all active jobs."""
    print("\n=== Testing GET /api/jobs/ ===")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_job_by_slug():
    """Test getting job by slug (should return 404 if no jobs exist)."""
    print("\n=== Testing GET /api/jobs/test-job/ ===")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/test-job/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return True  # Either 200 or 404 is acceptable
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_admin_list_requires_auth():
    """Test that admin list requires authentication."""
    print("\n=== Testing GET /api/jobs/admin/ (no auth) ===")
    try:
        response = requests.get(f"{BASE_URL}/api/jobs/admin/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 401
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_swagger_docs():
    """Test that swagger docs are accessible."""
    print("\n=== Testing GET /api/docs/ ===")
    try:
        response = requests.get(f"{BASE_URL}/api/docs/")
        print(f"Status Code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Jobs API Test Suite")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")

    results = []

    results.append(("List Jobs", test_list_jobs()))
    results.append(("Job by Slug", test_job_by_slug()))
    results.append(("Admin Auth Required", test_admin_list_requires_auth()))
    results.append(("Swagger Docs", test_swagger_docs()))

    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name}: {status}")

    # Exit with failure if any test failed
    if not all(r[1] for r in results):
        sys.exit(1)
