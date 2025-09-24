# 🎓 Scholarport Backend API Schema Documentation

## Overview

This document provides comprehensive API schema documentation for the **Scholarport Backend** - an AI-powered university recommendation chatbot system. This documentation is designed for frontend developers to easily integrate all backend endpoints.

### Base URL
```
http://127.0.0.1:8000/api/chat
```

### Authentication
Currently, all endpoints use `AllowAny` permission (no authentication required). In production, admin endpoints should be protected with proper authentication.

### Content Type
All requests and responses use `application/json` content type unless specified otherwise.

---

## 🏗️ System Architecture

### Core Components
1. **Chat API** - Conversation management and AI interactions with 7-step flow
2. **University API** - University data access and search (243+ universities)
3. **Admin API** - Professional Django admin with advanced filtering and exports
4. **Contact Collection** - Email and phone number collection for counselor outreach
5. **Firebase Integration** - Cloud data storage and export
6. **Consent Management** - User data consent handling

### Data Flow
```
Frontend → Chat API → AI Processing → University Matching → Profile Creation → Firebase Storage
```

### Database Models
- **ConversationSession** - Chat sessions with 7-question flow (includes email & phone collection)
- **ChatMessage** - Individual messages in conversations
- **University** - University database (243+ universities)
- **StudentProfile** - Finalized student profiles for counselor follow-up

---

## 📡 API Endpoints

### 1. Core Chat API

#### 1.1 Health Check
**GET** `/health/`

Check if the API is running and responsive.

**Response:**
```json
{
    "success": true,
    "message": "Scholarport Backend API is running",
    "timestamp": "2025-09-22T11:27:16.725650",
    "version": "1.0.0"
}
```

**Status Codes:**
- `200` - API is healthy
- `500` - Server error

---

#### 1.2 Start New Conversation
**POST** `/start/`

Creates a new conversation session and returns a unique session ID.

**Request Body:**
```json
{}
```
*Empty body - no parameters needed*

**Response:**
```json
{
    "success": true,
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "current_step": 1,
    "message": "Hello! Welcome to Scholarport - your personalized study abroad advisor. I'll help you find the perfect universities based on your preferences. Let's start with a few questions.",
    "question": "Hi! I'm Scholarport AI, your study abroad assistant. What is your name?",
    "total_steps": 7
}
```

**Status Codes:**
- `201` - Conversation created successfully
- `500` - Server error

---

#### 1.3 Send Message
**POST** `/send/`

Send a message in an existing conversation. Handles the 7-question flow and generates recommendations.

**Request Body:**
```json
{
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "message": "My name is John Smith"
}
```

**Parameters:**
- `session_id` (string, required) - UUID of the conversation session
- `message` (string, required) - User's message/response

**Response (Steps 1-4):**
```json
{
    "success": true,
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "current_step": 2,
    "bot_response": "Nice to meet you, John Smith! What is your education level?",
    "completed": false,
    "total_steps": 7,
    "next_question": "What is your education level? (e.g., High School, Bachelor's, Master's, etc.)"
}
```

**Response (Step 5 - Final):**
```json
{
    "success": true,
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "current_step": 6,
    "bot_response": "Perfect! Based on your profile, I've found 3 excellent universities in Canada that match your preferences.",
    "completed": true,
    "total_steps": 7,
    "recommendations": [
        {
            "name": "University of Toronto",
            "country": "Canada",
            "city": "Toronto",
            "tuition": "45000 CAD",
            "programs": ["Computer Science", "Engineering", "Business"],
            "ielts_requirement": 6.5,
            "toefl_requirement": 100,
            "ranking": "21",
            "why_selected": "Your IELTS 7.0 exceeds requirements; Strong computer science programs",
            "affordability": "Moderate",
            "region": "Ontario"
        },
        {
            "name": "University of British Columbia",
            "country": "Canada",
            "city": "Vancouver",
            "tuition": "42000 CAD",
            "programs": ["Computer Science", "Applied Science", "Commerce"],
            "ielts_requirement": 6.5,
            "toefl_requirement": 90,
            "ranking": "34",
            "why_selected": "Well within budget; Excellent computer science programs",
            "affordability": "Moderate",
            "region": "British Columbia"
        },
        {
            "name": "McGill University",
            "country": "Canada",
            "city": "Montreal",
            "tuition": "38000 CAD",
            "programs": ["Engineering", "Science", "Management"],
            "ielts_requirement": 6.5,
            "toefl_requirement": 90,
            "ranking": "31",
            "why_selected": "Highly ranked university; Great value for money",
            "affordability": "Affordable",
            "region": "Quebec"
        }
    ],
    "profile_created": true,
    "profile_id": 1
}
```

**Status Codes:**
- `200` - Message processed successfully
- `400` - Missing required fields
- `404` - Invalid session ID
- `500` - Server error

**7-Question Flow:**
1. **Name** - Student's name
2. **Education** - Educational background
3. **Test Score** - IELTS/TOEFL scores
4. **Budget** - Budget amount and currency
5. **Country** - Preferred study destination
6. **Email** - Contact email address
7. **Phone** - Contact phone number

---

#### 1.4 Get Conversation History
**GET** `/conversation/{session_id}/`

Retrieve complete chat history for a conversation session.

**Parameters:**
- `session_id` (string, required) - UUID of the conversation session

**Response:**
```json
{
    "success": true,
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "messages": [
        {
            "type": "bot",
            "content": "Hello! Welcome to Scholarport - your personalized study abroad advisor.",
            "step_number": 0,
            "timestamp": "2025-09-22T11:27:16.725650"
        },
        {
            "type": "user",
            "content": "My name is John Smith",
            "step_number": 1,
            "timestamp": "2025-09-22T11:28:20.123456"
        },
        {
            "type": "bot",
            "content": "Nice to meet you, John Smith! What is your education level?",
            "step_number": 1,
            "timestamp": "2025-09-22T11:28:21.654321"
        }
    ],
    "current_step": 6,
    "completed": true,
    "created_at": "2025-09-22T11:27:16.725650"
}
```

**Status Codes:**
- `200` - History retrieved successfully
- `404` - Invalid session ID
- `500` - Server error

---

#### 1.5 Handle Data Consent
**POST** `/consent/`

Process user consent for data saving after receiving recommendations.

**Request Body:**
```json
{
    "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
    "consent": true
}
```

**Parameters:**
- `session_id` (string, required) - UUID of the conversation session
- `consent` (boolean, required) - User's consent choice

**Response (Consent Given):**
```json
{
    "success": true,
    "message": "Thank you! Your information has been saved securely. A counselor will contact you within 24-48 hours to assist with your university applications.",
    "data_saved": true,
    "profile_id": 123,
    "next_steps": "A counselor will contact you soon to discuss your university options and help with applications."
}
```

**Response (Consent Denied):**
```json
{
    "success": true,
    "message": "No problem! Your conversation data will not be saved. You can always come back and start a new conversation if you change your mind.",
    "data_saved": false,
    "recommendations_available": true
}
```

**Status Codes:**
- `200` - Consent processed successfully
- `400` - Missing required fields or invalid JSON
- `404` - Invalid session ID
- `500` - Server error

---

### 2. University Data API

#### 2.1 Get All Universities
**GET** `/universities/`

Retrieve list of universities with optional filtering and pagination.

**Query Parameters:**
- `country` (string, optional) - Filter by country name
- `search` (string, optional) - Search in university names
- `max_tuition` (string, optional) - Maximum tuition filter
- `limit` (integer, optional) - Number of results (default: 50)

**Examples:**
```
GET /universities/
GET /universities/?country=Canada&limit=10
GET /universities/?search=harvard&limit=5
```

**Response:**
```json
{
    "success": true,
    "universities": [
        {
            "id": 1,
            "name": "Harvard University",
            "country": "USA",
            "city": "Cambridge",
            "tuition": "55000 USD",
            "programs": ["Business", "Law", "Medicine", "Engineering", "Computer Science"],
            "ranking": "1",
            "ielts_requirement": 7.0,
            "toefl_requirement": 100,
            "affordability": "Very Expensive",
            "region": "Massachusetts"
        },
        {
            "id": 2,
            "name": "University of Toronto",
            "country": "Canada",
            "city": "Toronto",
            "tuition": "45000 CAD",
            "programs": ["Computer Science", "Engineering", "Business"],
            "ranking": "21",
            "ielts_requirement": 6.5,
            "toefl_requirement": 100,
            "affordability": "Moderate",
            "region": "Ontario"
        }
    ],
    "total_count": 2
}
```

**Status Codes:**
- `200` - Universities retrieved successfully
- `500` - Server error

---

#### 2.2 Get University Details
**GET** `/universities/{university_id}/`

Get detailed information about a specific university.

**Parameters:**
- `university_id` (integer, required) - University ID

**Response:**
```json
{
    "success": true,
    "university": {
        "id": 1,
        "name": "Harvard University",
        "country": "USA",
        "city": "Cambridge",
        "tuition": "55000 USD",
        "programs": ["Business Administration", "Law", "Medicine", "Engineering", "Computer Science", "Psychology", "Economics"],
        "ranking": "1",
        "ielts_requirement": 7.0,
        "toefl_requirement": 100,
        "affordability": "Very Expensive",
        "region": "Massachusetts",
        "notes": "World's leading university with exceptional programs across all disciplines. Highly competitive admission process."
    }
}
```

**Status Codes:**
- `200` - University found
- `404` - University not found
- `500` - Server error

---

### 3. Admin Dashboard API

#### 3.1 Get Dashboard Statistics
**GET** `/admin/stats/`

Retrieve comprehensive statistics for the admin dashboard.

**Response:**
```json
{
    "success": true,
    "stats": {
        "total_conversations": 25,
        "completed_conversations": 18,
        "total_profiles": 18,
        "completion_rate": 72.0,
        "popular_countries": ["Canada", "USA", "UK", "Australia", "Germany"],
        "recent_activity": 5,
        "profile_stats": {
            "total_profiles": 18,
            "completed_conversations": 18,
            "avg_budget": 28500.50,
            "top_countries": ["Canada", "USA", "UK"],
            "test_type_distribution": {
                "IELTS": 12,
                "TOEFL": 6
            },
            "recent_profiles": 3
        }
    }
}
```

**Status Codes:**
- `200` - Statistics retrieved successfully
- `500` - Server error

---

#### 3.2 Get Student Profiles
**GET** `/admin/profiles/`

Get paginated list of student profiles for admin dashboard.

**Query Parameters:**
- `limit` (integer, optional) - Number of profiles (default: 50)
- `offset` (integer, optional) - Pagination offset (default: 0)
- `country` (string, optional) - Filter by preferred country
- `completed_only` (boolean, optional) - Show only completed conversations

**Examples:**
```
GET /admin/profiles/
GET /admin/profiles/?limit=10&offset=0
GET /admin/profiles/?country=Canada&completed_only=true
```

**Response:**
```json
{
    "success": true,
    "profiles": [
        {
            "id": 1,
            "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
            "student_name": "John Smith",
            "education_background": "Bachelor's degree in Computer Science",
            "budget": "USD 25,000",
            "test_score": "IELTS 7.0",
            "preferred_country": "Canada",
            "recommended_universities": ["University of Toronto", "University of British Columbia", "McGill University"],
            "ai_insights": "Strong test scores provide good university options; Diverse geographic options across 1 countries",
            "created_at": "2025-09-22T11:27:16.725650",
            "conversation_completed": true
        }
    ],
    "pagination": {
        "total_count": 1,
        "limit": 10,
        "offset": 0,
        "has_more": false
    }
}
```

**Status Codes:**
- `200` - Profiles retrieved successfully
- `500` - Server error

---

#### 3.3 Export Profiles to Excel
**GET** `/admin/export/`

Export all completed student profiles to Excel file for download.

**Response:**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition:** `attachment; filename=student_profiles_YYYYMMDD_HHMMSS.xlsx`
- **Body:** Binary Excel file content

**Excel Columns:**
- Session ID
- Student Name
- Education Background
- Budget Amount & Currency
- Test Type & Score
- Preferred Country
- 3 Recommended Universities
- AI Insights
- Date Created
- Conversation Status

**Status Codes:**
- `200` - Excel file generated successfully
- `404` - No completed profiles to export
- `500` - Server error

**Usage Example:**
```javascript
// Download Excel file in browser
window.location.href = 'http://127.0.0.1:8000/api/chat/admin/export/';

// Or using fetch
fetch('/api/chat/admin/export/')
    .then(response => response.blob())
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'student_profiles.xlsx';
        a.click();
    });
```

---

### 4. Firebase Integration API

#### 4.1 Export Firebase Data
**GET** `/admin/firebase-export/`

Export data directly from Firebase Firestore in JSON or Excel format.

**Query Parameters:**
- `format` (string, optional) - `json` or `excel` (default: `json`)

**Examples:**
```
GET /admin/firebase-export/?format=json
GET /admin/firebase-export/?format=excel
```

**Response (JSON Format):**
```json
{
    "success": true,
    "data": [
        {
            "firebase_id": "doc123",
            "session_id": "b82e8c32-2f2b-4b6d-8628-01aa043808e4",
            "student_info": {
                "name": "John Smith",
                "education_level": "Bachelor's",
                "budget": {
                    "amount": 25000,
                    "currency": "USD"
                },
                "test_score": {
                    "type": "IELTS",
                    "score": "7.0"
                },
                "preferred_country": "Canada"
            },
            "recommendations": {
                "universities": [
                    {
                        "name": "University of Toronto",
                        "country": "Canada",
                        "ranking": "21"
                    }
                ]
            },
            "metadata": {
                "created_at": "2025-09-22T11:27:16.725650",
                "consent_given": true
            }
        }
    ],
    "count": 1,
    "exported_at": "2025-09-22T12:00:00.000000"
}
```

**Response (Excel Format):**
- **Content-Type:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition:** `attachment; filename=Firebase_Student_Data_YYYYMMDD_HHMMSS.xlsx`
- **Body:** Binary Excel file content

**Status Codes:**
- `200` - Data exported successfully
- `400` - Invalid format parameter
- `404` - No data found in Firebase
- `500` - Server error

---

## 🚨 Error Handling

### Standard Error Response Format
```json
{
    "success": false,
    "error": "Error description"
}
```

### Common Error Scenarios

#### Invalid Session ID
```json
{
    "success": false,
    "error": "Invalid session_id"
}
```
**Status Code:** `404`

#### Missing Required Fields
```json
{
    "success": false,
    "error": "session_id and message are required"
}
```
**Status Code:** `400`

#### University Not Found
```json
{
    "success": false,
    "error": "Failed to get university details: No University matches the given query."
}
```
**Status Code:** `404`

#### Server Error
```json
{
    "success": false,
    "error": "Failed to process message: Detailed error message"
}
```
**Status Code:** `500`

---

## 🛠️ Frontend Integration Guide

### 1. Starting a Conversation
```javascript
// Start new conversation
const startResponse = await fetch('/api/chat/start/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({})
});
const session = await startResponse.json();
const sessionId = session.session_id;
```

### 2. Sending Messages
```javascript
// Send user message
const sendMessage = async (sessionId, message) => {
    const response = await fetch('/api/chat/send/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            message: message
        })
    });
    return await response.json();
};
```

### 3. Handling Recommendations
```javascript
// Check if conversation is completed
if (response.completed && response.recommendations) {
    // Display university recommendations
    response.recommendations.forEach(uni => {
        console.log(`${uni.name} - ${uni.country} - ${uni.tuition}`);
    });

    // Show consent dialog
    showConsentDialog(sessionId);
}
```

### 4. Processing Consent
```javascript
const handleConsent = async (sessionId, consent) => {
    const response = await fetch('/api/chat/consent/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            session_id: sessionId,
            consent: consent
        })
    });
    return await response.json();
};
```

### 5. Loading Universities
```javascript
// Get universities with filters
const getUniversities = async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/chat/universities/?${params}`);
    return await response.json();
};

// Usage
const canadianUnis = await getUniversities({ country: 'Canada', limit: 10 });
```

### 6. Admin Dashboard Integration
```javascript
// Get dashboard stats
const getDashboardStats = async () => {
    const response = await fetch('/api/chat/admin/stats/');
    return await response.json();
};

// Get student profiles
const getProfiles = async (page = 0, limit = 10) => {
    const response = await fetch(`/api/chat/admin/profiles/?offset=${page * limit}&limit=${limit}`);
    return await response.json();
};

// Download Excel export
const downloadExcel = () => {
    window.location.href = '/api/chat/admin/export/';
};
```

---

## 📊 Data Models

### ConversationSession
```typescript
interface ConversationSession {
    session_id: string;
    student_name?: string;
    student_email?: string;
    student_phone?: string;
    current_step: number;
    is_completed: boolean;
    suggested_universities: University[];
    data_save_consent: boolean;
    email_response?: string;
    phone_response?: string;
    processed_email?: string;
    processed_phone?: string;
    created_at: string;
    updated_at: string;
}
```

### University
```typescript
interface University {
    id: number;
    name: string;
    country: string;
    city: string;
    tuition: string;
    programs: string[];
    ranking: string;
    ielts_requirement: number;
    toefl_requirement: number;
    affordability: string;
    region: string;
}
```

### StudentProfile
```typescript
interface StudentProfile {
    id: number;
    session_id: string;
    student_name: string;
    email?: string;
    phone?: string;
    education_background: string;
    budget: string;
    test_score: string;
    preferred_country: string;
    recommended_universities: string[];
    ai_insights: string;
    created_at: string;
    conversation_completed: boolean;
}
```

---

## 🔒 Security Considerations

### Current State
- All endpoints use `AllowAny` permission (development mode)
- No authentication required
- CORS enabled for cross-origin requests

### Production Recommendations
1. **Add Authentication** - Implement JWT tokens or session-based auth for admin endpoints
2. **Rate Limiting** - Add request rate limiting to prevent abuse
3. **Input Validation** - Enhanced validation for all user inputs
4. **HTTPS** - Use HTTPS in production
5. **Admin Protection** - Secure admin endpoints with proper role-based access

---

## 📈 Performance Notes

### Response Times
- Health check: ~50ms
- Start conversation: ~200ms
- Send message: ~500-1000ms (includes AI processing)
- Get universities: ~100-300ms
- Admin stats: ~200-500ms

### Database Queries
- University search is optimized with indexing
- Profile queries use select_related for efficiency
- Pagination implemented for large datasets

### File Exports
- Excel generation may take 1-3 seconds for large datasets
- Firebase exports depend on Firestore query performance

---

## 🧪 Testing

### API Testing Tools
- **Postman Collection:** Available at `Scholarport_API_Collection.postman_collection.json`
- **Test Scripts:** `test_api.py` and `debug_api.py`

### Testing Workflow
1. Start with health check
2. Create conversation session
3. Complete 7-question flow
4. Verify recommendations
5. Test consent handling
6. Validate admin endpoints

### Sample Test Data
```javascript
const testFlow = [
    "My name is John Smith",
    "I have a Bachelor's degree in Computer Science",
    "I have IELTS 7.0",
    "My budget is $25,000 USD per year",
    "I want to study in Canada"
];
```

---

## 📞 Support

### Development Team
- Backend API: Django REST Framework
- AI Processing: OpenAI GPT integration
- Database: SQLite (development) / PostgreSQL (production)
- Cloud Storage: Firebase Firestore

### Documentation Updates
This documentation is maintained alongside the codebase. For updates or questions, refer to:
- API source code in `chat/views.py`
- URL routing in `chat/urls.py`
- Models in `chat/models.py`

---

*Last Updated: September 22, 2025*
*API Version: 1.0.0*