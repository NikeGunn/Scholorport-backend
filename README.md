# 🎓 Scholarport Backend

![Scholarport Logo](https://img.shields.io/badge/Scholarport-AI_University_Advisor-blue?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-4.2.7-green?style=flat-square&logo=django)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)
![Firebase](https://img.shields.io/badge/Firebase-Integrated-orange?style=flat-square&logo=firebase)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-purple?style=flat-square&logo=openai)

**Scholarport** is an AI-powered university recommendation chatbot backend that helps students find their perfect study abroad destination through intelligent conversation and personalized recommendations.

---

## 🌟 Features

### 🤖 **AI-Powered Conversations**
- **5-Question Flow**: Intelligent chatbot that guides students through structured conversations
- **OpenAI Integration**: GPT-4 powered natural language processing
- **Smart Data Extraction**: Automatically parses and understands user responses
- **Context Awareness**: Maintains conversation state and context throughout the session

### 🏫 **University Matching Engine**
- **243+ Universities**: Comprehensive database covering major study destinations
- **Smart Filtering**: Budget, test scores, location, and program-based matching
- **Multi-Country Support**: USA, Canada, UK, Australia, Germany, and more
- **Personalized Recommendations**: AI-generated university suggestions with explanations

### 📊 **Admin Dashboard & Analytics**
- **Real-time Statistics**: Conversation completion rates, popular destinations
- **Student Profile Management**: Complete student data with university recommendations
- **Export Functionality**: Excel and JSON exports for counselor follow-up
- **Performance Metrics**: Comprehensive analytics for business intelligence

### 🔥 **Firebase Cloud Integration**
- **Real-time Data Sync**: Automatic cloud storage of student profiles
- **Scalable Architecture**: Cloud-first design for enterprise scalability
- **Data Export**: Multiple format exports (JSON, Excel) from cloud storage
- **Consent Management**: GDPR-compliant data handling and user consent

### 🛡️ **Security & Compliance**
- **Data Consent System**: User-controlled data saving with clear consent flow
- **Secure API Design**: RESTful APIs with proper error handling
- **Environment-based Configuration**: Secure credential management
- **CORS Support**: Frontend integration ready

---

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Django API     │    │   Firebase      │
│   (React/Vue)   │◄──►│   Backend        │◄──►│   Firestore     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   OpenAI GPT-4   │
                       │   AI Engine      │
                       └──────────────────┘
```

### **Core Components**
- **Chat API**: Conversation management and AI interactions
- **University API**: 243+ university database with advanced search
- **Admin API**: Dashboard analytics and data exports
- **Firebase Service**: Cloud storage and real-time sync
- **AI Service**: OpenAI integration for natural language processing

---

## 🚀 Quick Start

### **Prerequisites**
- Python 3.8+
- pip (Python package manager)
- Git
- OpenAI API key
- Firebase project (optional, for cloud features)

### **1. Clone & Setup**
```bash
# Clone the repository
git clone <repository-url>
cd scholarport-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required:
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_django_secret_key

# Optional (for Firebase):
FIREBASE_CREDENTIALS_PATH=path_to_firebase_credentials.json
```

### **3. Database Setup**
```bash
# Run database migrations
python manage.py migrate

# Load university data
python manage.py load_universities

# Create admin user (optional)
python manage.py createsuperuser
```

### **4. Start Development Server**
```bash
# Start the Django development server
python manage.py runserver

# API will be available at:
# http://127.0.0.1:8000/api/chat/
```

### **5. Test the API**
```bash
# Test health endpoint
curl http://127.0.0.1:8000/api/chat/health/

# Or run comprehensive tests
python test_api.py
```

---

## 📡 API Endpoints

### **Base URL**: `http://127.0.0.1:8000/api/chat/`

### **🔥 Core Chat API**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health/` | Health check |
| `POST` | `/start/` | Start new conversation |
| `POST` | `/send/` | Send message (7-question flow) |
| `POST` | `/consent/` | Handle data consent |
| `GET` | `/conversation/{session_id}/` | Get chat history |

### **🏫 University Data API**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/universities/` | List universities (with filters) |
| `GET` | `/universities/{id}/` | Get university details |

### **📊 Admin Dashboard API**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/stats/` | Dashboard statistics |
| `GET` | `/admin/profiles/` | Student profiles (paginated) |
| `GET` | `/admin/export/` | Export profiles to Excel |

### **🔥 Firebase Integration API**
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/admin/firebase-export/` | Export Firebase data (JSON/Excel) |

> 📖 **Complete API Documentation**: See [`api-schema.md`](./api-schema.md) for detailed request/response examples

---

## 💻 Usage Examples

### **Start a Conversation**
```python
import requests

# Start new conversation
response = requests.post('http://127.0.0.1:8000/api/chat/start/')
session_data = response.json()
session_id = session_data['session_id']

# Send messages through 7-question flow
messages = [
    "John Smith",                           # Step 1: Name
    "Bachelor's in Computer Science",       # Step 2: Education
    "IELTS 7.0",                           # Step 3: Test Score
    "$25,000 USD per year",                # Step 4: Budget
    "Canada",                              # Step 5: Country
    "john.smith@email.com",                # Step 6: Email
    "+1 (555) 123-4567"                    # Step 7: Phone
]

for message in messages:
    response = requests.post('http://127.0.0.1:8000/api/chat/send/', json={
        'session_id': session_id,
        'message': message
    })
    result = response.json()
    print(f"Bot: {result['bot_response']}")

    # Check if completed
    if result.get('completed'):
        print(f"Recommendations: {len(result['recommendations'])} universities")
        break
```

### **Search Universities**
```python
# Get universities in Canada with budget filter
response = requests.get('http://127.0.0.1:8000/api/chat/universities/', params={
    'country': 'Canada',
    'limit': 10
})
universities = response.json()['universities']

for uni in universities:
    print(f"{uni['name']} - {uni['tuition']} - Ranking: {uni['ranking']}")
```

### **Admin Dashboard Data**
```python
# Get dashboard statistics
response = requests.get('http://127.0.0.1:8000/api/chat/admin/stats/')
stats = response.json()['stats']

print(f"Total Conversations: {stats['total_conversations']}")
print(f"Completion Rate: {stats['completion_rate']}%")
print(f"Popular Countries: {stats['popular_countries']}")
```

---

## 🗄️ Database Models

### **ConversationSession**
- Manages chat sessions and 5-question flow
- Stores processed user responses and AI analysis
- Tracks conversation state and completion

### **University**
- 243+ university database with comprehensive details
- Smart filtering by budget, test scores, location
- JSON fields for programs and additional metadata

### **StudentProfile**
- Finalized student profiles for counselor follow-up
- Links to conversation sessions and recommendations
- Export-ready data structure

### **ChatMessage**
- Individual messages in conversations
- Tracks bot questions and user responses
- Timestamped for conversation flow analysis

---

## 🔧 Configuration

### **Environment Variables**
```bash
# Core Django Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development, PostgreSQL for production)
DATABASE_URL=sqlite:///db.sqlite3

# AI Integration
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Firebase (Optional)
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json

# CORS Settings (for frontend integration)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### **Django Settings Highlights**
- **REST Framework**: Configured for API development
- **CORS Headers**: Frontend integration ready
- **Firebase Admin**: Cloud storage integration
- **OpenAI**: GPT-4 AI processing
- **Pagination**: Optimized for large datasets

---

## 🧪 Testing

### **Run All Tests**
```bash
# Health check and basic functionality
python test_api.py

# Complete system test
python test_complete_system.py

# Firebase integration test
python test_firebase.py

# ALTS warning suppression test
python test_alts_suppression.py
```

### **API Testing with Postman**
Import the included Postman collection:
```
Scholarport_API_Collection.postman_collection.json
```

### **Test Coverage**
- ✅ All API endpoints
- ✅ 5-question conversation flow
- ✅ University matching algorithm
- ✅ Firebase integration
- ✅ Excel export functionality
- ✅ Error handling and edge cases

---

## 📁 Project Structure

```
scholarport-backend/
├── 📁 chat/                          # Main chatbot application
│   ├── 📁 services/                  # Business logic services
│   │   ├── conversation_manager.py   # AI conversation handling
│   │   ├── university_selector.py    # University matching engine
│   │   └── profile_creator.py        # Student profile creation & Firebase
│   ├── 📁 migrations/               # Database migrations
│   ├── models.py                    # Database models
│   ├── views.py                     # API endpoints
│   └── urls.py                      # URL routing
├── 📁 admin_panel/                  # Admin dashboard app
├── 📁 scholarport_backend/          # Django project settings
│   ├── settings.py                  # Main configuration
│   ├── urls.py                      # Root URL configuration
│   └── wsgi.py                      # WSGI application
├── 📁 venv/                         # Virtual environment
├── 📄 manage.py                     # Django management script
├── 📄 requirements.txt              # Python dependencies
├── 📄 data.json                     # University database (243+ universities)
├── 📄 .env                          # Environment variables
├── 📄 .gitignore                    # Git ignore rules
├── 📄 api-schema.md                 # Complete API documentation
└── 📄 README.md                     # This file
```

---

## 🚀 Deployment

### **Development**
```bash
# Standard Django development server
python manage.py runserver 0.0.0.0:8000
```

### **Production**
```bash
# Using Gunicorn WSGI server
gunicorn --bind 0.0.0.0:8000 --workers 3 scholarport_backend.wsgi:application
```

### **Docker Deployment**
```dockerfile
# Dockerfile included for containerization
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "scholarport_backend.wsgi:application"]
```

### **Environment-Specific Settings**
- **Development**: SQLite, Debug enabled, Local OpenAI
- **Staging**: PostgreSQL, Debug disabled, Rate limiting
- **Production**: PostgreSQL, Full security, Load balancing

---

## 🔍 Monitoring & Analytics

### **Built-in Analytics**
- **Conversation Metrics**: Completion rates, popular destinations
- **Performance Tracking**: Response times, error rates
- **User Behavior**: Question flow analysis, drop-off points
- **Business Intelligence**: Export data for deeper analysis

### **Health Monitoring**
```bash
# Health check endpoint
GET /api/chat/health/

# Response includes:
{
    "success": true,
    "message": "Scholarport Backend API is running",
    "timestamp": "2025-09-22T14:00:00",
    "version": "1.0.0"
}
```

---

## 🛠️ Development

### **Adding New Features**
1. **Models**: Add database models in `chat/models.py`
2. **Services**: Implement business logic in `chat/services/`
3. **Views**: Create API endpoints in `chat/views.py`
4. **URLs**: Register routes in `chat/urls.py`
5. **Tests**: Add tests in `test_*.py` files

### **Code Style**
- **PEP 8**: Python code style compliance
- **Django Best Practices**: Follow Django conventions
- **API Design**: RESTful API principles
- **Documentation**: Comprehensive docstrings and comments

### **Git Workflow**
```bash
# Feature development
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature
```

---

## 📚 Dependencies

### **Core Dependencies**
```python
Django==4.2.7                    # Web framework
djangorestframework==3.14.0      # API framework
django-cors-headers==4.3.1       # CORS support
openai==1.3.3                    # AI integration
firebase-admin==6.2.0            # Firebase integration
openpyxl==3.1.2                 # Excel export
requests==2.31.0                # HTTP client
python-dotenv==1.0.0            # Environment variables
```

### **Development Dependencies**
```python
pytest==7.4.3                   # Testing framework
pytest-django==4.5.2            # Django testing integration
```

### **Production Dependencies**
```python
gunicorn==21.2.0                # WSGI server
psycopg2-binary==2.9.7          # PostgreSQL adapter
```

---

## 🤝 Contributing

### **Getting Started**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-django

# Run tests before committing
python test_api.py
pytest

# Check code style
flake8 .
```

---

## 📄 License

This project is proprietary software owned by **Scholarport Ltd**.

### **Development License**
- ✅ Use for development and testing
- ✅ Modify for internal purposes
- ❌ Redistribute or share publicly
- ❌ Use for commercial purposes without authorization

### **Contact**
For licensing inquiries or commercial use, contact: **Scholarport Ltd**

---

## 🆘 Support & Troubleshooting

### **Common Issues**

#### **OpenAI API Errors**
```bash
# Check your API key
python -c "import openai; print('OpenAI configured correctly')"
```

#### **Firebase Connection Issues**
```bash
# Test Firebase connection
python test_firebase.py
```

#### **Database Issues**
```bash
# Reset database
python manage.py migrate --run-syncdb
python manage.py load_universities
```

#### **ALTS Warnings (Google Cloud)**
The project includes automatic suppression of Google Cloud ALTS warnings. If you see warnings, they're cosmetic and don't affect functionality.

### **Getting Help**
1. **Check Documentation**: Review `api-schema.md` for complete API docs
2. **Run Tests**: Use `test_api.py` to verify functionality
3. **Check Logs**: Review Django server logs for detailed error information
4. **Environment**: Verify `.env` file configuration

---

## 📊 Performance & Scalability

### **Current Performance**
- **Response Times**: 50-1000ms per API call
- **Concurrent Users**: 100+ simultaneous conversations
- **Database**: Optimized queries with select_related
- **Caching**: Django built-in caching for university data

### **Scalability Options**
- **Database**: PostgreSQL for production
- **Caching**: Redis for session and query caching
- **Load Balancing**: Multiple server instances
- **CDN**: Static file delivery optimization

---

## 🎯 Roadmap

### **Phase 1 - MVP** ✅
- ✅ 7-question conversation flow (includes contact collection)
- ✅ University recommendation engine
- ✅ Admin dashboard and exports
- ✅ Firebase cloud integration

### **Phase 2 - Enhancement** 🚧
- 🔄 Advanced filtering and search
- 🔄 Multi-language support
- 🔄 Email notifications for counselors
- 🔄 Enhanced AI conversation abilities

### **Phase 3 - Scale** 📋
- 📋 Real-time chat functionality
- 📋 Advanced analytics dashboard
- 📋 Integration with external university APIs
- 📋 Mobile app backend support

---

## 🏆 Acknowledgments

- **Django Community**: For the robust web framework
- **OpenAI**: For powerful GPT-4 AI capabilities
- **Firebase**: For scalable cloud infrastructure
- **Django REST Framework**: For excellent API development tools

---

<div align="center">

**🎓 Scholarport - Empowering Students, One Conversation at a Time**

[![API Status](https://img.shields.io/badge/API-Online-green?style=for-the-badge)](http://127.0.0.1:8000/api/chat/health/)
[![Firebase](https://img.shields.io/badge/Firebase-Connected-orange?style=for-the-badge&logo=firebase)](https://firebase.google.com/)
[![AI Powered](https://img.shields.io/badge/AI-GPT--4-purple?style=for-the-badge&logo=openai)](https://openai.com/)

*Built with ❤️ by the Scholarport Team*

</div>