"""
Database models for the Scholarport Chat application.

Models define the structure of our data in the database.
Each model represents a table in the database.
"""

from django.db import models
from django.contrib.auth.models import User
import uuid
import json


class ConversationSession(models.Model):
    """
    Represents a single chat session with a student.
    Each conversation follows the 5-question flow.
    """
    # Unique identifier for this conversation
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Basic student information
    student_name = models.CharField(max_length=255, blank=True, null=True)
    student_email = models.EmailField(blank=True, null=True)
    student_phone = models.CharField(max_length=20, blank=True, null=True)

    # 7-question responses (added email and phone collection)
    name_response = models.CharField(max_length=255, blank=True, null=True)
    education_response = models.TextField(blank=True, null=True)
    test_score_response = models.CharField(max_length=100, blank=True, null=True)
    budget_response = models.CharField(max_length=100, blank=True, null=True)
    country_response = models.CharField(max_length=100, blank=True, null=True)
    email_response = models.EmailField(blank=True, null=True)
    phone_response = models.CharField(max_length=20, blank=True, null=True)

    # Processed (AI-understood) versions of responses
    processed_name = models.CharField(max_length=255, blank=True, null=True)
    processed_education = models.TextField(blank=True, null=True)
    processed_test_score = models.CharField(max_length=100, blank=True, null=True)
    processed_budget = models.CharField(max_length=100, blank=True, null=True)
    processed_country = models.CharField(max_length=100, blank=True, null=True)
    processed_email = models.EmailField(blank=True, null=True)
    processed_phone = models.CharField(max_length=20, blank=True, null=True)

    # Conversation state
    current_step = models.IntegerField(default=1)  # 1-8 (1-7 questions, 8=completed)
    is_completed = models.BooleanField(default=False)

    # University suggestions (stored as JSON)
    suggested_universities = models.JSONField(default=list, blank=True)

    # Data consent and follow-up
    data_save_consent = models.BooleanField(default=False)
    counselor_contacted = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'chat_conversations'
        ordering = ['-created_at']

    def __str__(self):
        return f"Conversation {self.session_id} - {self.processed_name or 'Anonymous'}"

    def get_conversation_data(self):
        """Returns structured conversation data for export"""
        return {
            'session_id': str(self.session_id),
            'name': self.processed_name or self.name_response,
            'education': self.processed_education or self.education_response,
            'test_score': self.processed_test_score or self.test_score_response,
            'budget': self.processed_budget or self.budget_response,
            'country': self.processed_country or self.country_response,
            'universities': self.suggested_universities,
            'created_at': self.created_at.isoformat(),
            'completed': self.is_completed,
            'consent': self.data_save_consent,
            'contacted': self.counselor_contacted
        }


class ChatMessage(models.Model):
    """
    Individual messages in a conversation.
    Stores both bot questions and user responses.
    """
    SENDER_CHOICES = [
        ('bot', 'Bot'),
        ('user', 'User'),
    ]

    conversation = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=4, choices=SENDER_CHOICES)
    message_text = models.TextField()
    step_number = models.IntegerField()  # Which question/step this relates to

    # AI processing info
    original_input = models.TextField(blank=True, null=True)  # User's raw input
    processed_output = models.TextField(blank=True, null=True)  # AI-processed version

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender}: {self.message_text[:50]}..."


class University(models.Model):
    """
    University data from our JSON file.
    We'll load this from data.json into the database.
    """
    university_name = models.CharField(max_length=255, unique=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)

    # Tuition and costs
    tuition = models.CharField(max_length=50)  # e.g., "18000 GBP"

    # Test score requirements
    ielts_requirement = models.FloatField(null=True, blank=True)
    toefl_requirement = models.IntegerField(null=True, blank=True)

    # University info
    ranking = models.CharField(max_length=20, blank=True)
    programs = models.JSONField(default=list)  # List of programs offered
    notes = models.TextField(blank=True)

    # Additional fields from JSON
    affordability = models.CharField(max_length=50, blank=True)
    region = models.CharField(max_length=50, blank=True)
    name_variations = models.JSONField(default=list)
    program_categories = models.JSONField(default=list)
    searchable_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'universities'
        ordering = ['university_name']

    def __str__(self):
        return f"{self.university_name} ({self.country})"

    def matches_budget(self, budget_amount, currency):
        """Check if university tuition fits within budget"""
        try:
            # Extract amount and currency from tuition field
            import re
            tuition_match = re.search(r'(\d+(?:,\d+)*)\s*([A-Z]{3})', self.tuition)
            if tuition_match:
                tuition_amount = int(tuition_match.group(1).replace(',', ''))
                tuition_currency = tuition_match.group(2)

                # Simple currency conversion (in production, use real rates)
                conversion_rates = {
                    'USD': 1.0,
                    'GBP': 1.25,  # 1 GBP = 1.25 USD
                    'EUR': 1.1,   # 1 EUR = 1.1 USD
                    'CAD': 0.75,  # 1 CAD = 0.75 USD
                    'AUD': 0.65,  # 1 AUD = 0.65 USD
                }

                # Convert both to USD for comparison
                budget_usd = budget_amount * conversion_rates.get(currency, 1.0)
                tuition_usd = tuition_amount * conversion_rates.get(tuition_currency, 1.0)

                # Allow 20% tolerance
                return tuition_usd <= budget_usd * 1.2

        except (ValueError, AttributeError):
            pass

        return False

    def meets_test_requirements(self, test_type, score):
        """Check if student's test score meets requirements"""
        try:
            if test_type.upper() == 'IELTS' and self.ielts_requirement:
                return float(score) >= self.ielts_requirement
            elif test_type.upper() == 'TOEFL' and self.toefl_requirement:
                return int(score) >= self.toefl_requirement
        except (ValueError, TypeError):
            pass

        return True  # If no requirements or can't parse, assume it's OK


class StudentProfile(models.Model):
    """
    Stores finalized student profiles for counselor follow-up.
    Created when student consents to save data.
    """
    conversation = models.OneToOneField(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    # Contact information
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Academic background
    education_level = models.CharField(max_length=255)
    field_of_study = models.CharField(max_length=255, blank=True)
    gpa_percentage = models.CharField(max_length=50, blank=True)

    # Test scores
    test_type = models.CharField(max_length=10)  # IELTS/TOEFL
    test_score = models.CharField(max_length=10)

    # Preferences
    budget_amount = models.IntegerField()
    budget_currency = models.CharField(max_length=3)
    preferred_country = models.CharField(max_length=100)
    preferred_programs = models.JSONField(default=list)

    # University matches
    recommended_universities = models.JSONField(default=list)

    # Counselor management
    assigned_counselor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_students'
    )
    contact_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Contact'),
            ('contacted', 'Contacted'),
            ('in_progress', 'Application in Progress'),
            ('completed', 'Application Completed'),
        ],
        default='pending'
    )

    # Follow-up notes
    counselor_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.preferred_country}"

    def export_data(self):
        """Export student data for Excel/CSV"""
        return {
            'Name': self.name,
            'Email': self.email,
            'Education': self.education_level,
            'Test Score': f"{self.test_type} {self.test_score}",
            'Budget': f"{self.budget_amount} {self.budget_currency}",
            'Country': self.preferred_country,
            'Universities': ', '.join([uni.get('name', '') for uni in self.recommended_universities]),
            'Status': self.contact_status,
            'Date': self.created_at.strftime('%Y-%m-%d'),
            'Counselor': self.assigned_counselor.username if self.assigned_counselor else 'Unassigned'
        }
