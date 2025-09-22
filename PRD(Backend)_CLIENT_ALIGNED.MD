# Product Requirement Document (Backend) – Scholarport Ltd Phase 1 MVP

## Client Overview & Requirements

**Client Vision**: "AI-powered study abroad guidance — Free, Fast, Simple"
**Core User Flow**: Chat → 5 Questions → 3 University Suggestions → Data Save → Counsellor Follow-up

---

## Project Scope - Phase 1 (Chatbot-First MVP)

### **Primary Goal**
Build a **simple, conversational chatbot** that asks 5 specific questions and suggests exactly **3 universities** from our 243-university dataset, then saves student data for counsellor follow-up.

### **Updated Client Requirements Alignment**
- ✅ **Free typing + guided suggestions** for natural conversation
- ✅ **AI-powered input understanding** for better user experience
- ✅ **Exactly 3 university suggestions** per student
- ✅ **Simple conversation flow** (5 questions max)
- ✅ **Firebase data storage** for counsellor access
- ✅ **No student dashboard** in Phase 1
- ✅ **Enhanced conversation** - free typing with AI processing

---

## Core Features

### 1. **Hybrid Conversational Chatbot API** - `/api/chat/`

**Enhanced Hybrid Approach:**
- **Steps 1-5**: Free typing + guided suggestions with AI understanding
- **University Suggestions**: Natural language using OpenAI API
- **AI Input Processing**: OpenAI understands and normalizes all user inputs
- **Off-topic handling**: Polite redirect to university guidance

**Enhanced Conversation Flow (Updated):**
```
Bot: "Hi! I'm Scholarport AI. What is your name?"
User: Can type anything like "My name is John", "I'm Sarah", "Call me Mike", etc.
[AI processes and extracts: "John", "Sarah", "Mike"]

Bot: "Nice to meet you {name}! What is your education level?"
Quick suggestions: ["BBA", "BSc Computer Science", "MBA", "High School"]
User: Can type freely like "I completed my bachelors in business", "BSc IT with 75%", etc.
[AI processes and extracts: "BBA", "BSc IT, 75%"]

Bot: "Great! What is your IELTS or TOEFL score?"
Quick suggestions: ["IELTS 6.5", "IELTS 7.0", "TOEFL 80", "TOEFL 100"]
User: Can type freely like "I got 6.5 in IELTS", "My TOEFL is 85", "IELTS 7", etc.
[AI processes and extracts: "IELTS 6.5", "TOEFL 85", "IELTS 7.0"]

Bot: "Perfect! What is your budget for studying abroad?"
Quick suggestions: ["$20,000 USD", "$25,000 USD", "£18,000 GBP", "€20,000 EUR"]
User: Can type freely like "Around 20k dollars", "My budget is £18000", "20000$", etc.
[AI processes and extracts: "$20,000 USD", "£18,000 GBP", "$20,000 USD"]

Bot: "Finally, which country do you prefer to study in?"
Quick suggestions: ["USA", "UK", "Canada", "Australia", "Germany"]
User: Can type freely like "United States", "I want to go to Britain", "Canada", etc.
[AI processes and extracts: "USA", "UK", "Canada"]

Bot: [OpenAI Generated Response]
"Excellent choices, Anjali! Based on your BBA background, IELTS 6.5 score,
and £18,000 budget for the UK, I've found 3 perfect universities that match
your profile:

🎓 **Coventry University** - £18,000/year
   Located in Coventry, this university offers excellent business programs
   that align perfectly with your BBA background. Your IELTS 6.5 meets their
   requirements, and the tuition fits your budget exactly.

🎓 **University of Bedfordshire** - £14,500/year
   A great value option in Luton with strong business and IT programs.
   You'll save £3,500 annually while getting quality education that builds
   on your BBA foundation.

🎓 **University of Greenwich** - £16,000/year
   Situated in vibrant London, this university offers diverse business
   programs with excellent networking opportunities. Your budget allows
   for comfortable study in one of the world's business capitals.

Do you want me to save your details so our expert counsellors can help
you with the application process?"

[If user asks off-topic questions]
User: "What's the weather like?"
Bot: "I appreciate your question, but I'm specifically designed to help you
find the perfect university for your study abroad journey. Let's focus on
getting you the best university recommendations!

Do you want me to save your details so our counsellors can help you further?"
```

### 2. **Smart University Selection Algorithm**

From 243 universities, select **exactly 3** based on:
```python
def select_3_universities(student_data):
    """
    Client requirement: Always return exactly 3 universities
    """
    # 1. Filter by country preference
    country_matches = filter_by_country(student_data['country'])

    # 2. Filter by budget compatibility
    budget_matches = filter_by_budget(country_matches, student_data['budget'])

    # 3. Filter by test score eligibility
    score_matches = filter_by_test_scores(budget_matches, student_data['test_scores'])

    # 4. Score universities based on multiple factors
    scored_universities = []
    for uni in score_matches:
        score = calculate_match_score(uni, student_data)
        scored_universities.append((uni, score))

    # 5. Return top 3 (client requirement)
    top_3 = sorted(scored_universities, key=lambda x: x[1], reverse=True)[:3]

    # 6. If less than 3 matches, expand search criteria
    if len(top_3) < 3:
        top_3 = expand_search_for_3_universities(student_data)

    return [uni[0] for uni in top_3]
```

### 3. **Simple Data Storage** - Firebase Schema

**Client-Specified Data Structure:**
```json
{
  "student_id": "auto_generated_uuid",
  "conversation_data": {
    "name": "Anjali",
    "education": "BBA, 70%",
    "test_score": "IELTS 6.5",
    "budget": "18000 GBP",
    "country": "UK",
    "suggested_universities": [
      "Coventry University",
      "University of Bedfordshire",
      "University of Greenwich"
    ]
  },
  "conversation_completed": true,
  "data_save_consent": true,
  "timestamp": "2025-09-20T10:00:00Z",
  "counsellor_contacted": false
}
```

### 4. **Counsellor Dashboard APIs**

```python
# List all students for counsellors
GET /api/admin/students/
Response: [
  {
    "id": "uuid",
    "name": "Anjali",
    "education": "BBA, 70%",
    "budget": "18000 GBP",
    "country": "UK",
    "universities": ["Coventry University", "University of Bedfordshire", "University of Greenwich"],
    "date": "2025-09-20",
    "contacted": false
  }
]

# Export to Excel
GET /api/admin/export/excel/
Returns: Excel file with all student data

# Mark student as contacted
POST /api/admin/students/{id}/contacted/
```

---

## API Endpoints Design

### **1. Enhanced Main Chatbot Endpoint**
```python
POST /api/chat/
{
  "message": "My name is John Smith",  # Free typing allowed
  "session_id": "optional",
  "conversation_step": 1  # 1-5 for the 5 questions
}

Processing Flow:
1. AI processes input: "My name is John Smith" → extracts "John Smith"
2. Store normalized data: {"name": "John Smith"}
3. Generate next question with personalization

Response:
{
  "bot_response": "Nice to meet you John Smith! What is your education level?",
  "conversation_step": 2,
  "session_id": "session_123",
  "is_completed": false,
  "suggested_universities": null,
  "guided_suggestions": ["BBA", "BSc Computer Science", "MBA", "High School"],
  "processed_input": "John Smith"  # Shows what AI extracted
}
```

### **2. AI-Enhanced Input Processing Examples**
```python
# Step 2 Example:
POST /api/chat/
{
  "message": "I completed my bachelors in business with 75%",
  "conversation_step": 2
}

Response:
{
  "bot_response": "Great! What is your IELTS or TOEFL score?",
  "conversation_step": 3,
  "guided_suggestions": ["IELTS 6.5", "IELTS 7.0", "TOEFL 80", "TOEFL 100"],
  "processed_input": "Bachelor's in Business, 75%"
}

# Step 4 Example:
POST /api/chat/
{
  "message": "Around 20k dollars",
  "conversation_step": 4
}

Response:
{
  "bot_response": "Finally, which country do you prefer to study in?",
  "conversation_step": 5,
  "guided_suggestions": ["USA", "UK", "Canada", "Australia", "Germany"],
  "processed_input": "$20,000 USD"
}
```

### **3. University Suggestion Response (Step 5)**
```python
Response after final question:
{
  "bot_response": "Based on your preferences, here are 3 perfect universities...",
  "conversation_step": 6,
  "is_completed": true,
  "suggested_universities": [
    {
      "name": "Coventry University",
      "tuition": "18000 GBP",
      "location": "Coventry, UK",
      "programs": ["Business", "Engineering"],
      "ielts_requirement": 6.5,
      "why_selected": "Perfect budget match and strong business programs"
    },
    {
      "name": "University of Bedfordshire",
      "tuition": "14500 GBP",
      "location": "Luton, UK",
      "programs": ["Business", "IT"],
      "ielts_requirement": 6.0,
      "why_selected": "Under budget with relevant programs"
    },
    {
      "name": "University of Greenwich",
      "tuition": "16000 GBP",
      "location": "London, UK",
      "programs": ["Business", "Arts"],
      "ielts_requirement": 6.0,
      "why_selected": "Great location with affordable tuition"
    }
  ],
  "next_question": "Do you want me to save your details so our counsellors can help you further?"
}
```

---

## Technical Implementation Requirements

### **Enhanced Conversation State Management**
```python
class ConversationManager:
    """
    Manages the 5-step conversation flow with AI input processing
    """
    QUESTIONS = [
        "Hi! I'm Scholarport AI. What is your name?",
        "Nice to meet you {name}! What is your education level?",
        "Great! What is your IELTS or TOEFL score?",
        "Perfect! What is your budget for studying abroad?",
        "Finally, which country do you prefer to study in?"
    ]

    GUIDED_SUGGESTIONS = {
        1: [],  # No suggestions for name
        2: ["BBA", "BSc Computer Science", "MBA", "High School"],
        3: ["IELTS 6.5", "IELTS 7.0", "TOEFL 80", "TOEFL 100"],
        4: ["$20,000 USD", "$25,000 USD", "£18,000 GBP", "€20,000 EUR"],
        5: ["USA", "UK", "Canada", "Australia", "Germany"]
    }

    def process_user_input(self, raw_input, step):
        """
        Process user input using AI and return normalized data
        """
        # Use AI to understand and normalize input
        processed_input = process_user_input_with_ai(raw_input, step)

        # Validate and fallback if needed
        if not processed_input or processed_input == raw_input:
            # Basic validation for common cases
            processed_input = self.fallback_processing(raw_input, step)

        return processed_input

    def fallback_processing(self, input_text, step):
        """
        Fallback processing if AI fails
        """
        if step == 4:  # Budget - extract numbers and common currencies
            import re
            numbers = re.findall(r'\d+', input_text.replace(',', ''))
            if numbers:
                amount = numbers[0]
                if '$' in input_text or 'dollar' in input_text.lower():
                    return f"${amount} USD"
                elif '£' in input_text or 'pound' in input_text.lower():
                    return f"£{amount} GBP"
                elif '€' in input_text or 'euro' in input_text.lower():
                    return f"€{amount} EUR"

        return input_text  # Return original if no processing possible

    def get_next_question(self, step, processed_name=None):
        if step <= len(self.QUESTIONS):
            return self.QUESTIONS[step-1].format(name=processed_name if step == 2 else "")
        return None

    def get_guided_suggestions(self, step):
        return self.GUIDED_SUGGESTIONS.get(step, [])

    def is_conversation_complete(self, step):
        return step > 5
```

### **University Selection Logic**
```python
def intelligent_3_university_selection(student_preferences):
    """
    Select exactly 3 universities from 243-university dataset
    """
    # Load university dataset
    with open('data.json', 'r') as f:
        universities = json.load(f)

    # Apply filters based on student preferences
    filtered_unis = apply_smart_filters(universities, student_preferences)

    # Score and rank universities
    scored_unis = score_universities(filtered_unis, student_preferences)

    # Select top 3 with diversity (different price points/features)
    selected_3 = select_diverse_top_3(scored_unis)

    return selected_3

def apply_smart_filters(universities, preferences):
    """Apply filtering based on our rich dataset"""
    filtered = []

    for uni in universities:
        # Country match
        if uni['country'].lower() != preferences['country'].lower():
            continue

        # Budget compatibility (with 20% tolerance)
        if not budget_compatible(uni['tuition'], preferences['budget']):
            continue

        # Test score eligibility
        if not test_score_eligible(uni, preferences):
            continue

        filtered.append(uni)

    return filtered
```

---

## Data Collection & Storage

### **Firebase Firestore Collections**

```javascript
// Collection: students
{
  studentId: "auto_generated",
  personalInfo: {
    name: "Anjali",
    education: "BBA, 70%",
    testScore: "IELTS 6.5",
    budget: "18000 GBP",
    preferredCountry: "UK"
  },
  recommendations: [
    {
      universityName: "Coventry University",
      tuition: "18000 GBP",
      matchReason: "Perfect budget match"
    }
  ],
  metadata: {
    conversationCompleted: true,
    dataSaveConsent: true,
    timestamp: "2025-09-20T10:00:00Z",
    counsellorContacted: false
  }
}

// Collection: conversations (for debugging)
{
  sessionId: "session_123",
  studentId: "student_456",
  messages: [
    {
      step: 1,
      question: "What is your name?",
      answer: "Anjali",
      timestamp: "2025-09-20T10:00:00Z"
    }
  ]
}
```

---

## AI Model Integration

### **Enhanced Hybrid AI Implementation**
- **Questions 1-5**: Free typing + guided suggestions with AI input processing
- **Input Understanding**: OpenAI GPT-3.5-turbo processes and normalizes user inputs
- **University Selection**: JSON filtering from data.json (no AI model needed)
- **Response Formatting**: OpenAI GPT-3.5-turbo for natural language suggestions
- **Off-topic Handling**: AI-powered detection + polite redirect

### **OpenAI Integration Details**
```python
# AI Model Configuration
OPENAI_MODEL = "gpt-3.5-turbo"
OPENAI_API_KEY = "your-openai-api-key"

def process_user_input_with_ai(user_input, conversation_step):
    """
    Use OpenAI to understand and normalize user inputs for each conversation step
    """
    prompts = {
        1: f"""Extract the person's name from this input: "{user_input}"

        Examples:
        "My name is John" -> "John"
        "I'm Sarah" -> "Sarah"
        "Call me Mike" -> "Mike"
        "John Smith" -> "John Smith"

        Return only the name, nothing else.""",

        2: f"""Extract and normalize the education information from: "{user_input}"

        Examples:
        "I completed my bachelors in business" -> "Bachelor's in Business"
        "BSc IT with 75%" -> "BSc IT, 75%"
        "I have MBA" -> "MBA"
        "High school graduate" -> "High School"
        "BBA" -> "BBA"

        Return the normalized education format.""",

        3: f"""Extract and normalize the test score from: "{user_input}"

        Examples:
        "I got 6.5 in IELTS" -> "IELTS 6.5"
        "My TOEFL is 85" -> "TOEFL 85"
        "IELTS 7" -> "IELTS 7.0"
        "I scored 6.5 IELTS" -> "IELTS 6.5"
        "TOEFL 100" -> "TOEFL 100"

        Return the normalized test score format.""",

        4: f"""Extract and normalize the budget from: "{user_input}"

        Examples:
        "Around 20k dollars" -> "$20,000 USD"
        "My budget is £18000" -> "£18,000 GBP"
        "20000$" -> "$20,000 USD"
        "25000 pounds" -> "£25,000 GBP"
        "€30000" -> "€30,000 EUR"

        Return the normalized budget format with currency.""",

        5: f"""Extract and normalize the country preference from: "{user_input}"

        Examples:
        "United States" -> "USA"
        "I want to go to Britain" -> "UK"
        "Canada" -> "Canada"
        "Australia" -> "Australia"
        "Germany" -> "Germany"
        "United Kingdom" -> "UK"

        Return the standardized country name."""
    }

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompts[conversation_step]}],
            max_tokens=50,
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        # Fallback to original input if AI processing fails
        return user_input

def format_university_suggestions_with_ai(universities, student_data):
    """
    Use OpenAI to create natural, personalized university suggestions
    """
    prompt = f"""
    You are Scholarport AI, a friendly study abroad counsellor. Create a warm,
    personalized response suggesting these 3 universities to {student_data['name']}:

    Student Profile:
    - Name: {student_data['name']}
    - Education: {student_data['education']}
    - Test Score: {student_data['test_score']}
    - Budget: {student_data['budget']}
    - Country: {student_data['country']}

    Universities to suggest:
    1. {universities[0]['university_name']} - {universities[0]['tuition']} - {universities[0]['programs']}
    2. {universities[1]['university_name']} - {universities[1]['tuition']} - {universities[1]['programs']}
    3. {universities[2]['university_name']} - {universities[2]['tuition']} - {universities[2]['programs']}

    Requirements:
    - Start with "Excellent choices, {student_data['name']}!"
    - Explain why each university matches their profile
    - Use friendly, encouraging tone
    - Include specific details about programs and location
    - End with: "Do you want me to save your details so our expert counsellors can help you with the application process?"

    Format with emojis and clear structure.
    """

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content

def handle_off_topic_questions(user_input):
    """
    Detect off-topic questions and provide polite redirect
    """
    off_topic_keywords = ['weather', 'news', 'sports', 'food', 'music', 'movie']

    if any(keyword in user_input.lower() for keyword in off_topic_keywords):
        return """I appreciate your question, but I'm specifically designed to help you
find the perfect university for your study abroad journey. Let's focus on getting you
the best university recommendations!

Do you want me to save your details so our counsellors can help you further?"""

    return None  # Not off-topic
```

### **Enhanced Cost Estimation**
- **AI Input Processing (5 calls per conversation)**: ~$0.005 per conversation
- **University suggestions formatting**: ~$0.01-0.02 per conversation
- **Total AI cost per conversation**: ~$0.015-0.025
- **Monthly cost for 1000 students**: ~$15-25
- **Very cost-effective approach with enhanced user experience**
- **Monthly cost for 1000 students**: ~$10-20
- **Very cost-effective approach**

---

## Client-Specific Requirements

### **Simplicity Focus**
- ✅ **Only 5 questions** - no complex forms
- ✅ **Always 3 suggestions** - not 10 or 20 options
- ✅ **Linear conversation** - no branching or complex logic
- ✅ **Save consent** - ask permission before storing data
- ✅ **Counsellor handoff** - system ends at data collection

### **No Advanced Features in Phase 1**
- ❌ No student dashboard
- ❌ No application tracking
- ❌ No complex filtering UI
- ❌ No user accounts/login
- ❌ No direct university applications

### **Admin/Counsellor Features**
- ✅ View all student conversations
- ✅ Export to Excel for manual follow-up
- ✅ Mark students as "contacted"
- ✅ Access contact information for outreach

---

## Success Metrics

### **Conversation Completion Rate**
- Target: >80% of users complete all 5 questions
- Measure: Students who reach university suggestions

### **Data Quality**
- Target: >95% of collected data is valid and complete
- Measure: Properly formatted responses for each question

### **University Suggestion Relevance**
- Target: >90% of suggestions meet student criteria
- Measure: Budget compatibility + country match + test score eligibility

### **Counsellor Efficiency**
- Target: Complete student profiles ready for immediate follow-up
- Measure: All required data captured in standardized format

---

## DevOps & Deployment Architecture

### **Production Infrastructure Requirements**

**Target Environment**: Hostinger VPS with professional DevOps practices
**Deployment Strategy**: Blue-Green deployment with zero downtime
**Monitoring**: Grafana dashboard implementation (Phase 2)

### **Infrastructure as Code (Terraform)**

```hcl
# terraform/main.tf
provider "hostinger" {
  version = "~> 1.0"
}

resource "hostinger_vps" "scholarport_backend" {
  plan     = "VPS-2"  # 2 CPU, 4GB RAM, 60GB SSD
  location = "US"
  hostname = "scholarport-api"

  tags = {
    Environment = "production"
    Project     = "scholarport-mvp"
    Component   = "backend-api"
  }
}

resource "hostinger_dns" "api_domain" {
  domain = "api.scholarport.com"
  type   = "A"
  value  = hostinger_vps.scholarport_backend.ip_address
  ttl    = 3600
}

# Load balancer configuration
resource "hostinger_load_balancer" "api_lb" {
  name = "scholarport-api-lb"

  backend_servers = [
    hostinger_vps.scholarport_backend.ip_address
  ]

  health_check = {
    path     = "/api/health/"
    interval = 30
    timeout  = 5
  }
}
```

### **Containerization Strategy (Docker)**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash scholarport
RUN chown -R scholarport:scholarport /app
USER scholarport

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py health_check || exit 1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "scholarport.wsgi:application"]
```

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DJANGO_SETTINGS_MODULE=scholarport.settings.production
      - DATABASE_URL=${DATABASE_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FIREBASE_CREDENTIALS=${FIREBASE_CREDENTIALS}
    volumes:
      - ./staticfiles:/app/staticfiles
      - ./media:/app/media
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./staticfiles:/var/www/static
    depends_on:
      - web
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  staticfiles:
  media:
```

### **CI/CD Pipeline (Jenkins)**

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'scholarport-registry'
        IMAGE_NAME = 'scholarport-backend'
        HOSTINGER_HOST = 'api.scholarport.com'
        DEPLOY_USER = 'scholarport'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/scholarport/backend.git'
            }
        }

        stage('Environment Setup') {
            steps {
                script {
                    // Load environment variables
                    withCredentials([
                        string(credentialsId: 'openai-api-key', variable: 'OPENAI_API_KEY'),
                        file(credentialsId: 'firebase-credentials', variable: 'FIREBASE_CREDS'),
                        string(credentialsId: 'database-url', variable: 'DATABASE_URL')
                    ]) {
                        env.OPENAI_API_KEY = OPENAI_API_KEY
                        env.DATABASE_URL = DATABASE_URL
                    }
                }
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    python -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                    python manage.py test
                    python manage.py check --deploy
                '''
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    # Run security checks
                    pip install safety bandit
                    safety check
                    bandit -r . -f json -o security-report.json
                '''
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'security-report.json',
                    reportName: 'Security Report'
                ])
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def image = docker.build("${IMAGE_NAME}:${BUILD_NUMBER}")
                    docker.withRegistry("https://${DOCKER_REGISTRY}", 'docker-registry-credentials') {
                        image.push()
                        image.push('latest')
                    }
                }
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                script {
                    // Blue-Green Deployment
                    sh '''
                        # Deploy to staging slot first
                        ssh ${DEPLOY_USER}@${HOSTINGER_HOST} "
                            cd /opt/scholarport &&
                            docker-compose -f docker-compose.staging.yml down &&
                            docker-compose -f docker-compose.staging.yml pull &&
                            docker-compose -f docker-compose.staging.yml up -d
                        "

                        # Health check on staging
                        curl -f http://staging.api.scholarport.com/api/health/ || exit 1

                        # Switch traffic to new version
                        ssh ${DEPLOY_USER}@${HOSTINGER_HOST} "
                            cd /opt/scholarport &&
                            ./scripts/blue-green-switch.sh
                        "
                    '''
                }
            }
        }

        stage('Post-Deploy Tests') {
            steps {
                sh '''
                    # Run integration tests against production
                    python -m pytest tests/integration/ --url=https://api.scholarport.com
                '''
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            emailext (
                subject: "🚨 Scholarport Backend Deployment Failed - Build #${BUILD_NUMBER}",
                body: """
                    Build failed for Scholarport Backend.

                    Build Number: ${BUILD_NUMBER}
                    Build URL: ${BUILD_URL}

                    Please check the Jenkins console for details.
                """,
                to: "devops@scholarport.com"
            )
        }
        success {
            emailext (
                subject: "✅ Scholarport Backend Deployed Successfully - Build #${BUILD_NUMBER}",
                body: """
                    Scholarport Backend has been successfully deployed to production.

                    Build Number: ${BUILD_NUMBER}
                    Deployment URL: https://api.scholarport.com

                    All health checks passed.
                """,
                to: "team@scholarport.com"
            )
        }
    }
}
```

### **GitHub Repository Structure**

```
scholarport-backend/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # GitHub Actions CI
│   │   ├── security.yml        # Security scanning
│   │   └── deploy.yml          # Deployment workflow
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── ISSUE_TEMPLATE.md
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx.conf
├── scripts/
│   ├── deploy.sh
│   ├── blue-green-switch.sh
│   ├── backup.sh
│   └── monitoring-setup.sh
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── docs/
│   ├── api.md
│   ├── deployment.md
│   └── monitoring.md
├── Jenkinsfile
├── requirements.txt
├── requirements-dev.txt
└── manage.py
```

### **Monitoring & Observability (Phase 2)**

```yaml
# monitoring/grafana-config.yml
version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=scholarport-admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro

volumes:
  grafana-data:
  prometheus-data:
```

### **Production Environment Configuration**

```python
# settings/production.py
import os
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['api.scholarport.com', 'scholarport.com']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'scholarport_prod'),
        'USER': os.getenv('DB_USER', 'scholarport'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Redis for caching and sessions
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/scholarport/backend.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

# Performance settings
CONN_MAX_AGE = 60
```

### **Deployment Timeline & Phases**

**Phase 1: Basic Production Setup (Week 1-2)**
- ✅ Hostinger VPS provisioning
- ✅ Docker containerization
- ✅ Basic CI/CD pipeline
- ✅ SSL certificate setup
- ✅ Database backup strategy

**Phase 2: Advanced DevOps (Week 3-4)**
- ✅ Terraform infrastructure automation
- ✅ Blue-green deployment
- ✅ Comprehensive monitoring with Grafana
- ✅ Load testing and optimization
- ✅ Security hardening

**Phase 3: Scaling & Optimization (Month 2)**
- ✅ Auto-scaling configuration
- ✅ CDN integration
- ✅ Advanced monitoring dashboards
- ✅ Performance optimization
- ✅ Disaster recovery procedures

---

## Phase 1 Deliverables

1. **Django REST API** with conversation management
2. **5-step chatbot** with university selection algorithm
3. **Firebase integration** for data storage
4. **Admin dashboard APIs** for counsellor access
5. **Excel export functionality** for student data
6. **Complete DevOps pipeline** with Docker, Jenkins, and Terraform
7. **Production-ready deployment** on Hostinger VPS
8. **Monitoring foundation** for Phase 2 Grafana implementation

This PRD focuses on **client simplicity** while leveraging your **comprehensive 243-university dataset** to provide intelligent, relevant suggestions within the constrained 5-question format, now with **enterprise-grade DevOps practices** for reliable production deployment.