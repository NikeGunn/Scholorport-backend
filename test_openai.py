#!/usr/bin/env python
"""
Quick test script to verify OpenAI integration is working
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

# Now we can import Django modules
from chat.services.conversation_manager import ConversationManager

def test_openai_integration():
    """Test OpenAI integration with a simple API call"""
    print("🔄 Testing OpenAI Integration...")

    try:
        # Initialize conversation manager
        manager = ConversationManager()
        print("✅ ConversationManager initialized successfully")

        # Test AI processing
        test_input = "John Smith"
        result = manager._process_user_input_with_ai(test_input, 1)

        print(f"📝 Input: '{test_input}'")
        print(f"🤖 AI Processed Output: '{result}'")

        if result and result != test_input:
            print("✅ OpenAI is working! AI processing successful.")
            return True
        else:
            print("⚠️  AI returned same input - might be using fallback")
            return False

    except Exception as e:
        print(f"❌ Error testing OpenAI: {e}")
        return False

if __name__ == "__main__":
    test_openai_integration()