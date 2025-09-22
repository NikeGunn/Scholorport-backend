"""
Demo script to show the difference between JSON and Excel endpoints
and how to properly handle the Excel export.
"""

import requests
import json

# Base URL for testing
BASE_URL = "http://127.0.0.1:8000/api/chat"

def demonstrate_endpoint_differences():
    """Show the difference between profiles JSON and Excel export"""

    print("🎓 Understanding Endpoint Differences")
    print("=" * 60)

    # 1. Test JSON Profiles Endpoint
    print("\n📄 1. JSON Profiles Endpoint (/admin/profiles/)")
    print("-" * 40)

    try:
        response = requests.get(f"{BASE_URL}/admin/profiles/?limit=1")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Response Type: JSON (Text Data)")

        if response.status_code == 200:
            data = response.json()
            print(f"Data Structure: Dictionary with 'profiles' array")
            print(f"Profile Count: {len(data.get('profiles', []))}")
            if data.get('profiles'):
                profile = data['profiles'][0]
                print(f"Sample Data: Name='{profile.get('student_name')}', Country='{profile.get('preferred_country')}'")

    except Exception as e:
        print(f"Error: {str(e)}")

    # 2. Test Excel Export Endpoint
    print(f"\n📊 2. Excel Export Endpoint (/admin/export/)")
    print("-" * 40)

    try:
        response = requests.get(f"{BASE_URL}/admin/export/")
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content-Disposition: {response.headers.get('Content-Disposition')}")
        print(f"Response Type: Binary File (Excel)")

        if response.status_code == 200:
            print(f"File Size: {len(response.content)} bytes")
            print(f"Data Format: Excel Spreadsheet (.xlsx)")

            # Save the Excel file
            filename = "student_profiles_demo.xlsx"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ Excel file saved as: {filename}")
            print(f"📂 You can now open this file in Excel/Google Sheets!")

        else:
            print(f"Error Response: {response.text}")

    except Exception as e:
        print(f"Error: {str(e)}")

    print(f"\n" + "=" * 60)
    print("💡 KEY DIFFERENCES:")
    print("1. JSON endpoint (/admin/profiles/) = Text data for web apps")
    print("2. Excel endpoint (/admin/export/) = Binary file for download")
    print("3. Postman shows binary as weird text - that's normal!")
    print("4. To view Excel data: Save response as .xlsx file")

if __name__ == "__main__":
    demonstrate_endpoint_differences()