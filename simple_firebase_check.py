#!/usr/bin/env python
"""
Simple Firebase data check without Django dependency
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json

def check_firebase_data():
    """Check what data is in Firebase"""
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json')
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        print('🔍 Checking Firebase Firestore Data...')
        print('=' * 50)

        # List all collections
        collections = db.collections()
        collection_names = [col.id for col in collections]
        print(f'📁 Collections found: {collection_names}')
        print()

        # Check student_profiles collection
        if 'student_profiles' in collection_names:
            profiles = db.collection('student_profiles').get()
            count = 0

            print('👥 Student Profiles:')
            print('-' * 30)

            for doc in profiles:
                count += 1
                data = doc.to_dict()
                print(f'{count}. ID: {doc.id}')
                print(f'   Name: {data.get("name", "N/A")}')
                print(f'   Education: {data.get("education_level", "N/A")}')
                print(f'   Country: {data.get("preferred_country", "N/A")}')
                print(f'   Budget: {data.get("budget_amount", "N/A")} {data.get("budget_currency", "")}')
                print(f'   Test: {data.get("test_type", "N/A")} {data.get("test_score", "")}')
                print(f'   Created: {data.get("created_at", "N/A")}')
                print()

            print(f'📈 Total Profiles: {count}')
        else:
            print('❌ No student_profiles collection found')

        print('\n🔗 Access your data in Firebase Console:')
        print('   URL: https://console.firebase.google.com/project/scholorport/firestore/data')
        print('\n📋 Steps to view in Firebase Console:')
        print('   1. Go to https://console.firebase.google.com/')
        print('   2. Click on "scholorport" project')
        print('   3. Click "Firestore Database" in left sidebar')
        print('   4. Look for "student_profiles" collection')
        print('   5. Click on documents to view details')

    except Exception as e:
        print(f'❌ Error accessing Firebase: {e}')
        print('\n🔧 Possible solutions:')
        print('   - Check if Firebase credentials file exists')
        print('   - Verify Firestore API is enabled')
        print('   - Ensure you have proper permissions')

if __name__ == '__main__':
    check_firebase_data()