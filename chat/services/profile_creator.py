"""
Student Profile Creator for Scholarport.

This module creates comprehensive student profiles from conversation data
and manages saving profiles to both local database and Firebase.
"""

import uuid
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from django.conf import settings
from chat.models import ConversationSession, StudentProfile, University

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️  Firebase Admin SDK not available. Install with: pip install firebase-admin")


class ProfileCreator:
    """
    Creates and manages student profiles from conversation data.

    Responsibilities:
    - Convert conversation data into structured student profile
    - Save profile to local database
    - Prepare data for Firebase export
    - Generate profile summaries for admin dashboard
    """

    def __init__(self):
        """Initialize the profile creator and Firebase connection"""
        self.firebase_db = None
        if FIREBASE_AVAILABLE:
            self._initialize_firebase()

    def _initialize_firebase(self):
        """Initialize Firebase connection if credentials are available"""
        try:
            # Suppress Google Cloud ALTS warnings
            import logging
            logging.getLogger('google.auth.transport.grpc').setLevel(logging.ERROR)
            logging.getLogger('google.auth._default').setLevel(logging.ERROR)

            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Initialize Firebase if credentials exist
                if settings.FIREBASE_CREDENTIALS_PATH:
                    # Build full path from Django project root
                    from django.conf import settings as django_settings
                    credentials_path = os.path.join(django_settings.BASE_DIR, settings.FIREBASE_CREDENTIALS_PATH)

                    if os.path.exists(credentials_path):
                        cred = credentials.Certificate(credentials_path)
                        firebase_admin.initialize_app(cred)
                        self.firebase_db = firestore.client()
                        print(f"✅ Firebase initialized successfully with {settings.FIREBASE_CREDENTIALS_PATH}")
                    else:
                        print(f"⚠️  Firebase credentials file not found at: {credentials_path}")
                        print("⚠️  Student profiles will only be saved locally.")
                else:
                    print("⚠️  FIREBASE_CREDENTIALS_PATH not set in .env file")
                    print("⚠️  Student profiles will only be saved locally.")
            else:
                # Firebase already initialized
                self.firebase_db = firestore.client()
                print("✅ Firebase connection reused")
        except Exception as e:
            print(f"⚠️  Firebase initialization failed: {e}")
            self.firebase_db = None

    def create_profile(self, conversation: ConversationSession, recommended_universities: List[Dict]) -> StudentProfile:
        """
        Create a complete student profile from conversation and recommendations.

        Args:
            conversation: The completed conversation session
            recommended_universities: List of 3 recommended universities

        Returns:
            Created StudentProfile instance
        """
        # Extract profile data
        profile_data = self._extract_profile_data(conversation)

        # Create the profile in local database
        profile = StudentProfile.objects.create(
            conversation=conversation,
            name=profile_data['name'],
            email=profile_data['email'],
            phone=profile_data['phone'],
            education_level=profile_data['education'],
            budget_amount=profile_data['budget_amount'],
            budget_currency=profile_data['budget_currency'],
            test_type=profile_data['test_type'],
            test_score=profile_data['test_score'],
            preferred_country=profile_data['country'],
            recommended_universities=self._format_universities_for_storage(recommended_universities)
        )

        # Save to Firebase if available
        self._save_to_firebase(profile)

        return profile

    def _extract_profile_data(self, conversation: ConversationSession) -> Dict:
        """Extract structured profile data from conversation"""
        # Use processed data if available, fallback to raw responses
        name = conversation.processed_name or conversation.name_response or "Anonymous Student"
        education = conversation.processed_education or conversation.education_response or ""
        budget_text = conversation.processed_budget or conversation.budget_response or ""
        test_text = conversation.processed_test_score or conversation.test_score_response or ""
        country_text = conversation.processed_country or conversation.country_response or ""

        # Parse budget
        budget_info = self._parse_budget(budget_text)

        # Parse test score
        test_info = self._parse_test_score(test_text)

        # Parse country
        country = self._parse_country(country_text)

        # Extract email and phone
        email = conversation.processed_email or conversation.student_email or conversation.email_response or ""
        phone = conversation.processed_phone or conversation.student_phone or conversation.phone_response or ""

        return {
            'name': name,
            'education': education,
            'budget_amount': budget_info['amount'],
            'budget_currency': budget_info['currency'],
            'test_type': test_info['type'],
            'test_score': test_info['score'],
            'country': country,
            'email': email,
            'phone': phone
        }

    def _parse_budget(self, budget_text: str) -> Dict:
        """Parse budget from text"""
        import re

        if not budget_text.strip():
            return {'amount': 25000, 'currency': 'USD'}

        # Extract amount
        amount_match = re.search(r'(\d+(?:,\d+)*)', budget_text.replace(',', ''))
        amount = int(amount_match.group(1)) if amount_match else 25000

        # Extract currency
        currency = 'USD'  # Default
        budget_upper = budget_text.upper()

        if '£' in budget_text or 'GBP' in budget_upper or 'POUND' in budget_upper:
            currency = 'GBP'
        elif '€' in budget_text or 'EUR' in budget_upper or 'EURO' in budget_upper:
            currency = 'EUR'
        elif 'CAD' in budget_upper or 'CANADIAN' in budget_upper:
            currency = 'CAD'
        elif 'AUD' in budget_upper or 'AUSTRALIAN' in budget_upper:
            currency = 'AUD'
        elif 'SGD' in budget_upper or 'SINGAPORE' in budget_upper:
            currency = 'SGD'
        elif 'CHF' in budget_upper or 'SWISS' in budget_upper:
            currency = 'CHF'

        return {'amount': amount, 'currency': currency}

    def _parse_test_score(self, test_text: str) -> Dict:
        """Parse test score from text"""
        import re

        if not test_text.strip():
            return {'type': 'IELTS', 'score': 6.0}

        test_upper = test_text.upper()

        if 'IELTS' in test_upper:
            score_match = re.search(r'(\d+(?:\.\d+)?)', test_text)
            score = float(score_match.group(1)) if score_match else 6.0
            return {'type': 'IELTS', 'score': score}
        elif 'TOEFL' in test_upper:
            score_match = re.search(r'(\d+)', test_text)
            score = int(score_match.group(1)) if score_match else 80
            return {'type': 'TOEFL', 'score': score}
        else:
            # Guess from numbers
            score_match = re.search(r'(\d+(?:\.\d+)?)', test_text)
            if score_match:
                score_val = float(score_match.group(1))
                if score_val <= 9:
                    return {'type': 'IELTS', 'score': score_val}
                else:
                    return {'type': 'TOEFL', 'score': int(score_val)}

        return {'type': 'IELTS', 'score': 6.0}

    def _parse_country(self, country_text: str) -> str:
        """Parse and standardize country name"""
        if not country_text.strip():
            return 'USA'

        country_mapping = {
            'USA': ['usa', 'america', 'united states', 'us'],
            'UK': ['uk', 'britain', 'united kingdom', 'england'],
            'Canada': ['canada', 'canadian'],
            'Australia': ['australia', 'aussie', 'oz'],
            'Germany': ['germany', 'german'],
            'Singapore': ['singapore'],
            'Switzerland': ['switzerland', 'swiss'],
            'France': ['france', 'french'],
            'Netherlands': ['netherlands', 'holland', 'dutch'],
        }

        country_lower = country_text.lower()
        for standard_name, variations in country_mapping.items():
            if any(var in country_lower for var in variations):
                return standard_name

        return country_text.title()

    def _format_universities_for_storage(self, universities: List[Dict]) -> List[Dict]:
        """Format university data for database storage"""
        formatted = []

        for uni in universities:
            formatted.append({
                'name': uni.get('name', ''),
                'country': uni.get('country', ''),
                'city': uni.get('city', ''),
                'tuition': uni.get('tuition', ''),
                'programs': uni.get('programs', [])[:3],  # Limit to 3 programs
                'ielts_requirement': uni.get('ielts_requirement'),
                'toefl_requirement': uni.get('toefl_requirement'),
                'ranking': uni.get('ranking', ''),
                'why_selected': uni.get('why_selected', ''),
                'affordability': uni.get('affordability', ''),
                'region': uni.get('region', '')
            })

        return formatted

    def _generate_profile_summary(self, profile_data: Dict, universities: List[Dict]) -> str:
        """Generate a human-readable profile summary"""
        name = profile_data['name']
        education = profile_data['education']
        budget = f"{profile_data['budget_currency']} {profile_data['budget_amount']:,}"
        test_score = f"{profile_data['test_type']} {profile_data['test_score']}"
        country = profile_data['country']

        uni_names = [uni.get('name', '') for uni in universities]

        summary = f"""
Student Profile Summary:
- Name: {name}
- Education Background: {education}
- Budget: {budget}
- Test Score: {test_score}
- Preferred Country: {country}
- Recommended Universities: {', '.join(uni_names)}
- Profile Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""".strip()

        return summary

    def _generate_ai_insights(self, conversation: ConversationSession, universities: List[Dict]) -> str:
        """Generate AI insights about the student and recommendations"""
        insights = []

        # Budget insights
        budget_text = conversation.processed_budget or conversation.budget_response or ""
        if 'tight' in budget_text.lower() or 'limited' in budget_text.lower():
            insights.append("Student has budget constraints - focused on affordable options")
        elif 'flexible' in budget_text.lower() or 'no limit' in budget_text.lower():
            insights.append("Student has flexible budget - included premium universities")

        # Test score insights
        test_text = conversation.processed_test_score or conversation.test_score_response or ""
        if any(word in test_text.lower() for word in ['high', 'excellent', 'good']):
            insights.append("Strong test scores provide good university options")
        elif any(word in test_text.lower() for word in ['low', 'poor', 'weak']):
            insights.append("Test scores may need improvement for top universities")

        # University diversity insights
        countries = list(set(uni.get('country', '') for uni in universities))
        if len(countries) > 1:
            insights.append(f"Diverse geographic options across {len(countries)} countries")

        # Ranking insights
        rankings = []
        for uni in universities:
            ranking = uni.get('ranking', '')
            if ranking and ranking.isdigit():
                rankings.append(int(ranking))

        if rankings and min(rankings) <= 50:
            insights.append("Recommendations include top-tier universities")

        if not insights:
            insights.append("Well-rounded profile with good university matches")

        return "; ".join(insights)

    def prepare_firebase_data(self, profile: StudentProfile) -> Dict:
        """
        Prepare student profile data for Firebase export.

        Args:
            profile: StudentProfile instance

        Returns:
            Dictionary formatted for Firebase storage
        """
        return {
            'session_id': str(profile.conversation.session_id),
            'student_info': {
                'name': profile.name,
                'education_background': profile.education_level,
                'budget': {
                    'amount': profile.budget_amount,
                    'currency': profile.budget_currency
                },
                'test_score': {
                    'type': profile.test_type,
                    'score': profile.test_score
                },
                'preferred_country': profile.preferred_country
            },
            'conversation_data': {
                'name_response': profile.conversation.name_response,
                'education_response': profile.conversation.education_response,
                'budget_response': profile.conversation.budget_response,
                'test_score_response': profile.conversation.test_score_response,
                'country_response': profile.conversation.country_response,
                'processed_responses': {
                    'name': profile.conversation.processed_name,
                    'education': profile.conversation.processed_education,
                    'budget': profile.conversation.processed_budget,
                    'test_score': profile.conversation.processed_test_score,
                    'country': profile.conversation.processed_country
                }
            },
            'recommendations': {
                'universities': profile.recommended_universities,
                'ai_insights': 'AI insights not available',
                'profile_summary': 'Profile summary not available'
            },
            'metadata': {
                'created_at': profile.created_at.isoformat() if profile.created_at else None,
                'conversation_completed': profile.conversation.is_completed,
                'session_step': profile.conversation.current_step
            }
        }

    def _save_to_firebase(self, profile: StudentProfile) -> bool:
        """
        Save student profile to Firebase.

        Args:
            profile: StudentProfile instance to save

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.firebase_db:
            print("⚠️  Firebase not available. Profile saved locally only.")
            return False

        try:
            # Prepare data for Firebase
            firebase_data = self.prepare_firebase_data(profile)

            # Save to Firestore collection 'student_profiles'
            doc_ref = self.firebase_db.collection('student_profiles').document(str(profile.conversation.session_id))
            doc_ref.set(firebase_data)

            print(f"✅ Profile saved to Firebase: {profile.name} (Session: {profile.conversation.session_id})")
            return True

        except Exception as e:
            print(f"❌ Failed to save profile to Firebase: {e}")
            return False

    def generate_excel_row_data(self, profile: StudentProfile) -> Dict:
        """
        Generate data for Excel export row.

        Args:
            profile: StudentProfile instance

        Returns:
            Dictionary with data for one Excel row
        """
        universities = profile.recommended_universities or []
        uni_names = [uni.get('name', '') for uni in universities]

        return {
            'Session ID': str(profile.conversation.session_id),
            'Student Name': profile.name,
            'Education Background': profile.education_level,
            'Budget Amount': profile.budget_amount,
            'Budget Currency': profile.budget_currency,
            'Test Type': profile.test_type,
            'Test Score': profile.test_score,
            'Preferred Country': profile.preferred_country,
            'University 1': uni_names[0] if len(uni_names) > 0 else '',
            'University 2': uni_names[1] if len(uni_names) > 1 else '',
            'University 3': uni_names[2] if len(uni_names) > 2 else '',
            'AI Insights': 'AI insights not available',
            'Date Created': profile.created_at.strftime('%Y-%m-%d %H:%M:%S') if profile.created_at else '',
            'Conversation Status': 'Completed' if profile.conversation.is_completed else 'In Progress'
        }

    def get_profile_stats(self) -> Dict:
        """
        Get statistics about all student profiles.

        Returns:
            Dictionary with profile statistics
        """
        from django.db.models import Count, Avg

        profiles = StudentProfile.objects.all()

        if not profiles.exists():
            return {
                'total_profiles': 0,
                'completed_conversations': 0,
                'avg_budget': 0,
                'top_countries': [],
                'test_type_distribution': {},
                'recent_profiles': 0
            }

        # Basic stats
        total_profiles = profiles.count()
        completed = profiles.filter(conversation__is_completed=True).count()

        # Budget stats
        avg_budget = profiles.aggregate(avg=Avg('budget_amount'))['avg'] or 0

        # Country preferences
        country_counts = profiles.values('preferred_country').annotate(
            count=Count('preferred_country')
        ).order_by('-count')[:5]

        # Test type distribution
        test_type_counts = profiles.values('test_type').annotate(
            count=Count('test_type')
        )
        test_distribution = {item['test_type']: item['count'] for item in test_type_counts}

        # Recent profiles (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)
        recent = profiles.filter(created_at__gte=yesterday).count()

        return {
            'total_profiles': total_profiles,
            'completed_conversations': completed,
            'avg_budget': round(avg_budget, 2),
            'top_countries': [item['preferred_country'] for item in country_counts],
            'test_type_distribution': test_distribution,
            'recent_profiles': recent
        }