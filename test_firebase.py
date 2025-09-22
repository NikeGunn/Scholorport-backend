#!/usr/bin/env python
"""
Test Firebase connection directly
"""
import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
sys.path.append(str(Path(__file__).parent))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scholarport_backend.settings')
django.setup()

# Test Firebase
from chat.services.profile_creator import ProfileCreator

def test_firebase_connection():
    """Test Firebase connection"""
    print("🔥 Testing Firebase Connection...")

    try:
        # Create profile creator (this initializes Firebase)
        creator = ProfileCreator()

        if creator.firebase_db:
            print("✅ Firebase database connection successful!")

            # Test writing to Firebase
            test_doc = creator.firebase_db.collection('test').document('connection_test')
            test_doc.set({
                'message': 'Firebase is working!',
                'timestamp': '2025-09-22',
                'test': True
            })
            print("✅ Test data written to Firebase successfully!")

            # Read it back
            doc = test_doc.get()
            if doc.exists:
                print(f"✅ Test data read from Firebase: {doc.to_dict()}")

            return True
        else:
            print("❌ Firebase database connection failed")
            return False

    except Exception as e:
        print(f"❌ Firebase test error: {e}")
        return False

if __name__ == "__main__":
    test_firebase_connection()