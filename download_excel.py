"""
Download the Excel file directly and save it to Desktop for easy access.
"""

import requests
import os
from datetime import datetime

def download_excel_file():
    """Download the Excel export and save it to Desktop"""

    print("📊 Downloading Excel Export File...")
    print("=" * 50)

    # Your API endpoint
    url = "http://127.0.0.1:8000/api/chat/admin/export/"

    try:
        # Make the request
        print(f"🔗 Requesting: {url}")
        response = requests.get(url)

        print(f"📡 Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type')}")
        print(f"📁 Content-Disposition: {response.headers.get('Content-Disposition')}")

        if response.status_code == 200:
            # Get user's desktop path
            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Scholarport_Student_Data_{timestamp}.xlsx"
            filepath = os.path.join(desktop, filename)

            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"✅ SUCCESS!")
            print(f"📁 File saved to: {filepath}")
            print(f"📊 File size: {len(response.content)} bytes")
            print(f"🖱️  Double-click the file to open in Excel!")

            # Also show what's in the current directory for reference
            print(f"\n📂 Current directory files:")
            current_dir = os.getcwd()
            for file in os.listdir(current_dir):
                if file.endswith('.xlsx'):
                    print(f"   📄 {file}")

        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    download_excel_file()