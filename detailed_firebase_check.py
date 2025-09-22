#!/usr/bin/env python
"""
Check detailed Firebase document structure
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json

def check_document_details():
    """Check detailed structure of Firebase documents"""
    try:
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate('scholorport-firebase-adminsdk-fbsvc-b17f9acfbf.json')
            firebase_admin.initialize_app(cred)

        db = firestore.client()

        print('🔍 Detailed Firebase Document Analysis...')
        print('=' * 50)

        # Get the specific document you mentioned
        doc_id = '477e2e64-e0ef-4f56-ac8d-18f5f99dcfd9'
        doc_ref = db.collection('student_profiles').document(doc_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            print(f'📄 Document: {doc_id}')
            print('📋 Complete Data Structure:')
            print(json.dumps(data, indent=2, default=str))
            print()
            print('🔧 All Available Fields:')
            for key, value in data.items():
                print(f'   {key}: {value}')
        else:
            print(f'❌ Document {doc_id} not found')

        print('\n🔍 Checking all documents...')
        # Get all documents
        profiles = db.collection('student_profiles').get()

        for doc in profiles:
            data = doc.to_dict()
            print(f'📄 Latest Document: {doc.id}')
            print('📋 Data:')
            print(json.dumps(data, indent=2, default=str))
            break

    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == '__main__':
    check_document_details()