#!/usr/bin/env python
"""
Check Firebase data structure for Firebase Console debugging
"""

import firebase_admin
from firebase_admin import credentials, firestore
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholarport.settings')
django.setup()

def check_firebase_data():
    """Check what data is in Firebase"""
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json')
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        # Get all student profiles
        print('🔍 Your Firebase Data Structure:')
        print('=' * 50)

        profiles = db.collection('student_profiles').get()
        count = 0

        for doc in profiles:
            count += 1
            data = doc.to_dict()
            print(f'{count}. Document ID: {doc.id}')
            print(f'   Name: {data.get("name", "N/A")}')
            print(f'   Education: {data.get("education_level", "N/A")}')
            print(f'   Country: {data.get("preferred_country", "N/A")}')
            print(f'   Budget: {data.get("budget_amount", "N/A")} {data.get("budget_currency", "")}')
            print(f'   Test: {data.get("test_type", "N/A")} {data.get("test_score", "")}')
            print(f'   Created: {data.get("created_at", "N/A")}')
            print('-' * 30)

        print(f'\n📈 Total Profiles in Firebase: {count}')
        print(f'🌐 Firebase Console URL: https://console.firebase.google.com/project/scholorport/firestore/data')

        if count > 0:
            print('\n✅ Data found! You should see this in Firebase Console:')
            print('   1. Go to https://console.firebase.google.com/')
            print('   2. Click on "scholorport" project')
            print('   3. Click "Firestore Database" in left sidebar')
            print('   4. You should see "student_profiles" collection')
            print('   5. Click on it to view your data!')
        else:
            print('\n❌ No data found in Firebase.')

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_firebase_data()