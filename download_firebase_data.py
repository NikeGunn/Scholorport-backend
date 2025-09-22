#!/usr/bin/env python
"""
Simple Firebase Data Downloader for Scholarport
Downloads data directly from Firebase and saves to local files
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import pandas as pd
from datetime import datetime
import os

def download_firebase_data():
    """Download Firebase data and save to files"""

    print("🔥 Firebase Data Downloader")
    print("=" * 40)

    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred_path = 'scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json'
            if not os.path.exists(cred_path):
                print(f"❌ Firebase credentials file not found: {cred_path}")
                return

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized successfully")

        db = firestore.client()

        # Get all student profiles
        print("📥 Downloading student profiles...")
        profiles_ref = db.collection('student_profiles')
        profiles = profiles_ref.stream()

        # Collect all data
        firebase_data = []
        count = 0
        for profile in profiles:
            count += 1
            profile_data = profile.to_dict()
            profile_data['firebase_id'] = profile.id
            firebase_data.append(profile_data)
            print(f"   Downloaded profile {count}: {profile.id}")

        if not firebase_data:
            print("❌ No data found in Firebase")
            return

        print(f"\n📊 Total profiles downloaded: {count}")

        # Save as JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_filename = f'firebase_data_{timestamp}.json'

        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(firebase_data, f, indent=2, default=str, ensure_ascii=False)

        print(f"✅ JSON saved: {json_filename}")

        # Save as Excel (flattened)
        print("📊 Creating Excel file...")
        flattened_data = []

        for item in firebase_data:
            flat_item = {
                'Firebase ID': item.get('firebase_id', ''),
                'Session ID': item.get('session_id', ''),
                'Student Name': item.get('student_info', {}).get('name', ''),
                'Education': item.get('student_info', {}).get('education_background', ''),
                'Budget Amount': item.get('student_info', {}).get('budget', {}).get('amount', ''),
                'Budget Currency': item.get('student_info', {}).get('budget', {}).get('currency', ''),
                'Test Type': item.get('student_info', {}).get('test_score', {}).get('type', ''),
                'Test Score': item.get('student_info', {}).get('test_score', {}).get('score', ''),
                'Preferred Country': item.get('student_info', {}).get('preferred_country', ''),
                'Universities': ', '.join([uni.get('name', '') for uni in item.get('recommendations', {}).get('universities', [])]),
                'Created Date': item.get('metadata', {}).get('created_at', ''),
                'Name Response': item.get('conversation_data', {}).get('name_response', ''),
                'Education Response': item.get('conversation_data', {}).get('education_response', ''),
                'Test Score Response': item.get('conversation_data', {}).get('test_score_response', ''),
                'Budget Response': item.get('conversation_data', {}).get('budget_response', ''),
                'Country Response': item.get('conversation_data', {}).get('country_response', '')
            }
            flattened_data.append(flat_item)

        # Create Excel file
        excel_filename = f'firebase_data_{timestamp}.xlsx'
        df = pd.DataFrame(flattened_data)

        with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Firebase Data', index=False)

            # Auto-adjust column widths
            worksheet = writer.sheets['Firebase Data']
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(length + 2, 50)

        print(f"✅ Excel saved: {excel_filename}")

        # Summary
        print(f"\n🎉 Download Complete!")
        print(f"   📄 JSON File: {json_filename} ({os.path.getsize(json_filename)} bytes)")
        print(f"   📊 Excel File: {excel_filename} ({os.path.getsize(excel_filename)} bytes)")
        print(f"   📈 Total Records: {count}")

        # Show first record preview
        if firebase_data:
            print(f"\n👤 Sample Record:")
            sample = firebase_data[0]
            print(f"   ID: {sample.get('firebase_id', 'N/A')}")
            print(f"   Name: {sample.get('student_info', {}).get('name', 'N/A')}")
            print(f"   Country: {sample.get('student_info', {}).get('preferred_country', 'N/A')}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    download_firebase_data()