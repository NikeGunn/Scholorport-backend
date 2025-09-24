"""
AI-powered conversation management for Scholarport.

This module handles the 5-step conversation flow with OpenAI integration
for understanding user inputs and generating natural responses.
"""

import openai
import re
import json
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from chat.models import ConversationSession, ChatMessage, University


class ConversationManager:
    """
    Manages the 7-step conversation flow for university recommendations.

    The flow:
    1. Name
    2. Education level
    3. Test score (IELTS/TOEFL)
    4. Budget
    5. Country preference
    6. Email address (for counselor contact)
    7. Phone number (for counselor contact)
    8. Generate university suggestions
    """

    # The 7 conversation questions (added email & phone collection)
    QUESTIONS = [
        "Hi! I'm Scholarport AI, your study abroad assistant. What is your name?",
        "Nice to meet you {name}! What is your education level?",
        "Great! What is your IELTS or TOEFL score?",
        "Perfect! What is your budget for studying abroad per year?",
        "Finally, which country do you prefer to study in?",
        "To help our counselors contact you, what is your email address?",
        "And what is your phone number? (Include country code if international)"
    ]

    # Guided suggestions for each step
    GUIDED_SUGGESTIONS = {
        1: [],  # No suggestions for name
        2: ["BBA", "BSc Computer Science", "MBA", "High School", "Bachelor's Degree", "Master's Degree"],
        3: ["IELTS 6.5", "IELTS 7.0", "TOEFL 80", "TOEFL 100", "No test yet"],
        4: ["$20,000 USD", "$25,000 USD", "£18,000 GBP", "€20,000 EUR", "$15,000 USD"],
        5: ["USA", "UK", "Canada", "Australia", "Germany", "Singapore"],
        6: [],  # No suggestions for email
        7: ["+1 (555) 123-4567", "+44 20 1234 5678", "+91 98765 43210", "Skip phone number"]
    }

    def __init__(self):
        """Initialize with OpenAI configuration (v1.0+ compatible)"""
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    def get_welcome_message(self) -> Dict:
        """
        Get the welcome message and first question for starting conversation.

        Returns:
            Dictionary with welcome message and first question
        """
        return {
            'message': "Hello! Welcome to Scholarport - your personalized study abroad advisor. I'll help you find the perfect universities based on your preferences. Let's start with a few questions.",
            'question': self.QUESTIONS[0]
        }

    def start_conversation(self) -> ConversationSession:
        """Create a new conversation session"""
        conversation = ConversationSession.objects.create()

        # Add the first bot message
        ChatMessage.objects.create(
            conversation=conversation,
            sender='bot',
            message_text=self.QUESTIONS[0],
            step_number=1
        )

        return conversation

    def process_user_input(self, session_id: str, user_input: str) -> Dict:
        """
        Process user input and return appropriate response.

        Args:
            session_id: UUID of the conversation session
            user_input: Raw user input text

        Returns:
            Dict with bot response, suggestions, and conversation state
        """
        try:
            conversation = ConversationSession.objects.get(session_id=session_id)
        except ConversationSession.DoesNotExist:
            return {'error': 'Conversation not found'}

        current_step = conversation.current_step

        # Save user message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            sender='user',
            message_text=user_input,
            step_number=current_step,
            original_input=user_input
        )

        # Process user input with AI
        processed_input = self._process_with_ai(user_input, current_step)
        user_message.processed_output = processed_input
        user_message.save()

        # Store the processed response in conversation
        self._store_response(conversation, current_step, user_input, processed_input)

        # Check if conversation is complete (after collecting email and phone)
        if current_step >= 7:
            return self._complete_conversation(conversation)

        # Move to next step
        conversation.current_step += 1
        conversation.save()

        # Generate next question
        next_question = self._get_next_question(conversation.current_step, processed_input)

        # Save bot message
        ChatMessage.objects.create(
            conversation=conversation,
            sender='bot',
            message_text=next_question,
            step_number=conversation.current_step
        )

        return {
            'bot_response': next_question,
            'conversation_step': conversation.current_step,
            'session_id': str(conversation.session_id),
            'is_completed': False,
            'suggested_universities': None,
            'guided_suggestions': self.GUIDED_SUGGESTIONS.get(conversation.current_step, []),
            'processed_input': processed_input
        }

    def _process_with_ai(self, user_input: str, step: int) -> str:
        """
        Use OpenAI to understand and normalize user input.

        Args:
            user_input: Raw user input
            step: Current conversation step (1-5)

        Returns:
            Processed/normalized input
        """
        if not settings.OPENAI_API_KEY:
            # Fallback processing without AI
            return self._fallback_processing(user_input, step)

        prompts = {
            1: f"""Extract the person's name from this input: "{user_input}"

Examples:
"My name is John" -> "John"
"I'm Sarah Smith" -> "Sarah Smith"
"Call me Mike" -> "Mike"
"John" -> "John"

Return only the name, nothing else.""",

            2: f"""Extract and normalize the education information from: "{user_input}"

Examples:
"I completed my bachelors in business" -> "Bachelor's in Business"
"BSc IT with 75%" -> "BSc IT, 75%"
"I have MBA" -> "MBA"
"High school graduate" -> "High School"
"BBA" -> "BBA"
"Bachelor's degree in engineering" -> "Bachelor's in Engineering"

Return the normalized education format.""",

            3: f"""Extract and normalize the test score from: "{user_input}"

Examples:
"I got 6.5 in IELTS" -> "IELTS 6.5"
"My TOEFL is 85" -> "TOEFL 85"
"IELTS 7" -> "IELTS 7.0"
"I scored 100 in TOEFL" -> "TOEFL 100"
"I haven't taken any test yet" -> "No test yet"
"6.5 IELTS" -> "IELTS 6.5"

Return the normalized test score format.""",

            4: f"""Extract and normalize the budget from: "{user_input}"

Examples:
"Around 20k dollars" -> "$20,000 USD"
"My budget is £18000" -> "£18,000 GBP"
"20000$" -> "$20,000 USD"
"25000 pounds" -> "£25,000 GBP"
"€30000" -> "€30,000 EUR"
"20 thousand dollars" -> "$20,000 USD"

Return the normalized budget format with currency.""",

            5: f"""Extract and normalize the country preference from: "{user_input}"

Examples:
"United States" -> "USA"
"I want to go to Britain" -> "UK"
"Canada" -> "Canada"
"Australia" -> "Australia"
"Germany" -> "Germany"
"United Kingdom" -> "UK"
"America" -> "USA"

Return the standardized country name."""
        }

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompts[step]}],
                max_tokens=50,
                temperature=0.3
            )
            processed = response.choices[0].message.content
            if processed:
                processed = processed.strip()

            # Validate the response
            if processed and len(processed) < 200:  # Reasonable length check
                return processed
            else:
                return self._fallback_processing(user_input, step)

        except Exception as e:
            print(f"OpenAI processing error: {e}")
            return self._fallback_processing(user_input, step)

    def _fallback_processing(self, user_input: str, step: int) -> str:
        """
        Fallback processing when AI is not available.

        Args:
            user_input: Raw user input
            step: Current conversation step

        Returns:
            Basic processed input
        """
        user_input = user_input.strip()

        if step == 1:  # Name
            # Basic name extraction
            words = user_input.split()
            if len(words) >= 2 and words[0].lower() in ['my', 'name', 'i\'m', 'im', 'call']:
                return ' '.join(words[1:]).replace('is', '').strip()
            return user_input

        elif step == 4:  # Budget
            # Extract numbers and common currencies
            numbers = re.findall(r'\d+(?:,\d+)*', user_input.replace(',', ''))
            if numbers:
                amount = numbers[0]
                if '$' in user_input or 'dollar' in user_input.lower():
                    return f"${amount} USD"
                elif '£' in user_input or 'pound' in user_input.lower():
                    return f"£{amount} GBP"
                elif '€' in user_input or 'euro' in user_input.lower():
                    return f"€{amount} EUR"
                return f"${amount} USD"  # Default to USD

        elif step == 5:  # Country
            # Basic country name mapping
            country_mapping = {
                'usa': 'USA', 'america': 'USA', 'united states': 'USA',
                'uk': 'UK', 'britain': 'UK', 'united kingdom': 'UK', 'england': 'UK',
                'canada': 'Canada',
                'australia': 'Australia', 'aussie': 'Australia',
                'germany': 'Germany'
            }

            lower_input = user_input.lower()
            for key, value in country_mapping.items():
                if key in lower_input:
                    return value

        return user_input

    def _store_response(self, conversation: ConversationSession, step: int,
                       original: str, processed: str) -> None:
        """Store user response in the conversation model"""
        if step == 1:
            conversation.name_response = original
            conversation.processed_name = processed
            conversation.student_name = processed  # Store in main field too
        elif step == 2:
            conversation.education_response = original
            conversation.processed_education = processed
        elif step == 3:
            conversation.test_score_response = original
            conversation.processed_test_score = processed
        elif step == 4:
            conversation.budget_response = original
            conversation.processed_budget = processed
        elif step == 5:
            conversation.country_response = original
            conversation.processed_country = processed
        elif step == 6:
            conversation.email_response = original
            conversation.processed_email = processed
            conversation.student_email = processed  # Store in main field too
        elif step == 7:
            conversation.phone_response = original
            conversation.processed_phone = processed
            conversation.student_phone = processed  # Store in main field too

        conversation.save()

    def _get_next_question(self, step: int, previous_response: str = "") -> str:
        """Get the next question, personalizing with user's name if available"""
        if step <= len(self.QUESTIONS):
            if step == 2 and previous_response:  # Personalize with name
                return self.QUESTIONS[step-1].format(name=previous_response)
            return self.QUESTIONS[step-1]
        return ""

    def _complete_conversation(self, conversation: ConversationSession) -> Dict:
        """
        Complete the conversation by generating university suggestions.

        Args:
            conversation: The completed conversation session

        Returns:
            Final response with university suggestions
        """
        from chat.services.university_selector import UniversitySelector

        # Mark conversation as completed
        conversation.current_step = 8
        conversation.is_completed = True

        # Generate university suggestions
        selector = UniversitySelector()
        universities = selector.select_universities(conversation)

        # Store suggestions
        conversation.suggested_universities = universities
        conversation.save()

        # Generate AI-powered response
        ai_response = self._generate_final_response(conversation, universities)

        # Save final bot message
        ChatMessage.objects.create(
            conversation=conversation,
            sender='bot',
            message_text=ai_response,
            step_number=8
        )

        return {
            'bot_response': ai_response,
            'conversation_step': 8,
            'session_id': str(conversation.session_id),
            'is_completed': True,
            'suggested_universities': universities,
            'guided_suggestions': [],
            'next_question': "Thank you! Our counselors now have your contact details and will reach out to help with your application process."
        }

    def _generate_final_response(self, conversation: ConversationSession,
                                universities: List[Dict]) -> str:
        """
        Generate a natural, personalized final response with university suggestions.

        Args:
            conversation: The conversation session
            universities: List of recommended universities

        Returns:
            AI-generated response text
        """
        if not settings.OPENAI_API_KEY or len(universities) == 0:
            return self._fallback_final_response(conversation, universities)

        # Prepare university information for the prompt
        uni_info = []
        for i, uni in enumerate(universities, 1):
            uni_info.append(f"{i}. {uni['name']} - {uni['tuition']} - Programs: {', '.join(uni['programs'])}")

        universities_text = '\n'.join(uni_info)

        prompt = f"""
You are Scholarport AI, a friendly study abroad counselor. Create a warm,
personalized response suggesting these 3 universities to {conversation.processed_name}:

Student Profile:
- Name: {conversation.processed_name}
- Education: {conversation.processed_education}
- Test Score: {conversation.processed_test_score}
- Budget: {conversation.processed_budget}
- Country: {conversation.processed_country}

Universities to suggest:
{universities_text}

Requirements:
- Start with "Excellent choices, {conversation.processed_name}!"
- Explain why each university matches their profile
- Use friendly, encouraging tone
- Include specific details about programs and affordability
- Keep it concise but informative
- End with: "These universities are perfect matches for your profile! Would you like me to save your details so our expert counselors can help you with the application process?"

Format with clear structure and emojis.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            content = response.choices[0].message.content
            return content.strip() if content else self._fallback_final_response(conversation, universities)
        except Exception as e:
            print(f"Error generating final response: {e}")
            return self._fallback_final_response(conversation, universities)

    def _fallback_final_response(self, conversation: ConversationSession,
                                universities: List[Dict]) -> str:
        """Generate a simple final response without AI"""
        if not universities:
            return f"Thank you {conversation.processed_name}! I'm working on finding the perfect universities for you. Our counselors will help you with personalized recommendations."

        response = f"Excellent choices, {conversation.processed_name}! "
        response += f"Based on your {conversation.processed_education} background, "
        response += f"{conversation.processed_test_score} score, "
        response += f"and {conversation.processed_budget} budget for {conversation.processed_country}, "
        response += "I've found 3 perfect universities:\n\n"

        for i, uni in enumerate(universities, 1):
            response += f"🎓 **{uni['name']}** - {uni['tuition']}\n"
            response += f"   Programs: {', '.join(uni['programs'])}\n"
            response += f"   {uni.get('notes', 'Great choice for your profile!')}\n\n"

        response += "These universities are perfect matches for your profile! "
        response += "Would you like me to save your details so our expert counselors can help you with the application process?"

        return response

    def handle_data_consent(self, session_id: str, consent: bool) -> Dict:
        """
        Handle user's consent to save their data.

        Args:
            session_id: UUID of the conversation session
            consent: Whether user consents to save data

        Returns:
            Response about data saving
        """
        try:
            conversation = ConversationSession.objects.get(session_id=session_id)
        except ConversationSession.DoesNotExist:
            return {'error': 'Conversation not found'}

        conversation.data_save_consent = consent
        conversation.save()

        if consent:
            # Check if profile already exists, if not create one
            from chat.models import StudentProfile
            from chat.services.profile_creator import ProfileCreator

            try:
                profile = StudentProfile.objects.get(conversation=conversation)
                # Profile exists, just save to Firebase
                profile_creator = ProfileCreator()
                profile_creator._save_to_firebase(profile)
            except StudentProfile.DoesNotExist:
                # Create new profile
                profile_creator = ProfileCreator()
                profile = profile_creator.create_profile(conversation, [])

            response = f"Perfect! I've saved your details securely. Our expert counselors will contact you within 24 hours to help you with your application to these amazing universities. Thank you for choosing Scholarport, {conversation.processed_name}!"
        else:
            response = f"No problem, {conversation.processed_name}! Your conversation data won't be saved. Feel free to start a new conversation anytime you're ready. Good luck with your study abroad journey!"

        return {
            'bot_response': response,
            'data_saved': consent,
            'session_id': str(conversation.session_id)
        }

    def handle_off_topic(self, user_input: str) -> str:
        """Handle off-topic questions with polite redirect"""
        off_topic_keywords = [
            'weather', 'news', 'sports', 'food', 'music', 'movie', 'film',
            'game', 'politics', 'religion', 'health', 'medical'
        ]

        if any(keyword in user_input.lower() for keyword in off_topic_keywords):
            return """I appreciate your question, but I'm specifically designed to help you find the perfect university for your study abroad journey. Let's focus on getting you the best university recommendations!

Shall we continue with finding your ideal universities?"""

        return ""  # Not off-topic