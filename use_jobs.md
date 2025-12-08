# Jobs/Careers API - Frontend Implementation Guide

**Status:** ✅ Backend Implementation Complete
**Last Updated:** December 8, 2025
**Base URL:** `https://api.scholarport.co` (Production) | `http://localhost:8000` (Development)

---

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [Authentication](#-authentication)
3. [Public Endpoints](#-public-endpoints-no-auth-required)
4. [Admin Endpoints](#-admin-endpoints-auth-required)
5. [Data Models](#-data-models)
6. [Error Handling](#-error-handling)
7. [Code Examples](#-code-examples)
8. [FAQ](#-faq)
9. [Ready-to-Use API Examples](#-ready-to-use-api-examples-copy-paste)
10. [Test Scenarios](#-test-scenarios)

---

## 🚀 Quick Start

### Base Endpoints

| Type | Endpoint | Auth Required |
|------|----------|---------------|
| Public | `GET /api/jobs/` | ❌ No |
| Public | `GET /api/jobs/{slug}/` | ❌ No |
| Admin | `GET /api/jobs/admin/` | ✅ Yes |
| Admin | `GET /api/jobs/admin/{id}/` | ✅ Yes |
| Admin | `POST /api/jobs/admin/create/` | ✅ Yes |
| Admin | `PATCH /api/jobs/admin/{id}/update/` | ✅ Yes |
| Admin | `DELETE /api/jobs/admin/{id}/delete/` | ✅ Yes |

---

## 🔐 Authentication

Admin endpoints require JWT Bearer token authentication.

### Getting a Token

```http
POST /api/admin-panel/auth/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "your_password"
}
```

**Response:**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Using the Token

Add to all admin requests:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📋 Public Endpoints (No Auth Required)

### 1. List All Active Jobs

**Endpoint:** `GET /api/jobs/`

Returns all active, non-expired job postings. Featured jobs appear first.

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `department` | string | Filter by department | `?department=Engineering` |
| `location` | string | Filter by location | `?location=Remote` |
| `type` | string | Filter by job type | `?type=full-time` |
| `featured` | boolean | Filter featured jobs | `?featured=true` |
| `search` | string | Search title, description, requirements | `?search=software` |
| `limit` | number | Results per page (default: 20, max: 100) | `?limit=10` |
| `offset` | number | Skip N results | `?offset=20` |

#### Job Types

| Value | Description |
|-------|-------------|
| `full-time` | Full-time position |
| `part-time` | Part-time position |
| `contract` | Contract/temporary |
| `internship` | Internship position |

#### Request Example

```http
GET /api/jobs/?department=Engineering&type=full-time&limit=10
```

#### Response (200 OK)

```json
{
    "count": 15,
    "next": "http://localhost:8000/api/jobs/?limit=10&offset=10",
    "previous": null,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Senior Software Engineer",
            "slug": "senior-software-engineer",
            "department": "Engineering",
            "location": "Remote",
            "type": "full-time",
            "is_featured": true,
            "posted_at": "2025-01-01T00:00:00Z",
            "expires_at": "2025-06-01T00:00:00Z"
        },
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "title": "Frontend Developer",
            "slug": "frontend-developer",
            "department": "Engineering",
            "location": "Kathmandu, Nepal",
            "type": "full-time",
            "is_featured": false,
            "posted_at": "2025-01-05T00:00:00Z",
            "expires_at": null
        }
    ]
}
```

#### JavaScript/React Example

```javascript
// Fetch all active jobs
const fetchJobs = async (filters = {}) => {
    const params = new URLSearchParams(filters);
    const response = await fetch(`/api/jobs/?${params}`);

    if (!response.ok) throw new Error('Failed to fetch jobs');

    return response.json();
};

// Usage
const jobs = await fetchJobs({
    department: 'Engineering',
    type: 'full-time',
    limit: 10
});
```

---

### 2. Get Job by Slug

**Endpoint:** `GET /api/jobs/{slug}/`

Returns detailed information about a specific job. Use for job detail pages.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `slug` | string | Job URL slug (e.g., `senior-software-engineer`) |

#### Request Example

```http
GET /api/jobs/senior-software-engineer/
```

#### Response (200 OK)

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Senior Software Engineer",
    "slug": "senior-software-engineer",
    "department": "Engineering",
    "location": "Remote",
    "type": "full-time",
    "description": "<p>We are looking for a <strong>Senior Software Engineer</strong> to join our growing team.</p>",
    "requirements": "<ul><li>5+ years of experience in software development</li><li>Proficiency in Python, JavaScript</li></ul>",
    "responsibilities": "<ul><li>Design and implement new features</li><li>Write clean, maintainable code</li></ul>",
    "application_email": "careers@scholarport.co",
    "application_method": "<p>Please send your CV to careers@scholarport.co</p>",
    "is_active": true,
    "is_featured": true,
    "posted_at": "2025-01-01T00:00:00Z",
    "expires_at": "2025-06-01T00:00:00Z",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T12:00:00Z"
}
```

#### Response (404 Not Found)

```json
{
    "error": "Job not found or no longer available"
}
```

#### JavaScript/React Example

```javascript
// Fetch single job by slug
const fetchJobBySlug = async (slug) => {
    const response = await fetch(`/api/jobs/${slug}/`);

    if (response.status === 404) {
        throw new Error('Job not found');
    }

    if (!response.ok) throw new Error('Failed to fetch job');

    return response.json();
};

// Usage in React component
const JobDetailPage = ({ slug }) => {
    const [job, setJob] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchJobBySlug(slug)
            .then(setJob)
            .catch(err => setError(err.message))
            .finally(() => setLoading(false));
    }, [slug]);

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            <h1>{job.title}</h1>
            <div dangerouslySetInnerHTML={{ __html: job.description }} />
        </div>
    );
};
```

---

## 🔒 Admin Endpoints (Auth Required)

> ⚠️ **All admin endpoints require `Authorization: Bearer {token}` header**

### 3. List All Jobs (Admin)

**Endpoint:** `GET /api/jobs/admin/`

Returns ALL jobs including inactive and expired ones.

#### Additional Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `is_active` | boolean | Filter by active status (`true`/`false`) |

#### Request Example

```http
GET /api/jobs/admin/?is_active=false
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (200 OK)

Same structure as public list, but includes inactive jobs.

#### Response (401 Unauthorized)

```json
{
    "detail": "Authentication credentials were not provided."
}
```

---

### 4. Get Job by ID (Admin)

**Endpoint:** `GET /api/jobs/admin/{id}/`

Get job details by UUID. Returns job even if inactive.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Job ID (e.g., `550e8400-e29b-41d4-a716-446655440000`) |

#### Request Example

```http
GET /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### 5. Create Job (Admin)

**Endpoint:** `POST /api/jobs/admin/create/`

Create a new job posting.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ Yes | Job title |
| `description` | string (HTML) | ✅ Yes | Full job description |
| `application_email` | string | ✅ Yes | Email for applications |
| `slug` | string | ❌ No | URL slug (auto-generated from title if empty) |
| `department` | string | ❌ No | Department name |
| `location` | string | ❌ No | Job location |
| `type` | string | ❌ No | Job type (default: `full-time`) |
| `requirements` | string (HTML) | ❌ No | Job requirements |
| `responsibilities` | string (HTML) | ❌ No | Job responsibilities |
| `application_method` | string (HTML) | ❌ No | How to apply |
| `is_active` | boolean | ❌ No | Active status (default: `true`) |
| `is_featured` | boolean | ❌ No | Featured status (default: `false`) |
| `expires_at` | datetime | ❌ No | Expiration date (ISO 8601 format) |

#### Request Example

```http
POST /api/jobs/admin/create/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "location": "Remote",
    "type": "full-time",
    "description": "<p>We are looking for a talented engineer...</p>",
    "requirements": "<ul><li>5+ years experience</li></ul>",
    "responsibilities": "<ul><li>Design and implement features</li></ul>",
    "application_email": "careers@scholarport.co",
    "application_method": "<p>Send your CV to careers@scholarport.co</p>",
    "is_active": true,
    "is_featured": true,
    "expires_at": "2025-06-01T00:00:00Z"
}
```

#### Response (201 Created)

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Senior Software Engineer",
    "slug": "senior-software-engineer",
    "department": "Engineering",
    "location": "Remote",
    "type": "full-time",
    "description": "<p>We are looking for a talented engineer...</p>",
    "requirements": "<ul><li>5+ years experience</li></ul>",
    "responsibilities": "<ul><li>Design and implement features</li></ul>",
    "application_email": "careers@scholarport.co",
    "application_method": "<p>Send your CV to careers@scholarport.co</p>",
    "is_active": true,
    "is_featured": true,
    "posted_at": "2025-12-08T10:30:00Z",
    "expires_at": "2025-06-01T00:00:00Z",
    "created_at": "2025-12-08T10:30:00Z",
    "updated_at": "2025-12-08T10:30:00Z"
}
```

#### Response (400 Bad Request)

```json
{
    "title": ["This field is required."],
    "description": ["This field is required."],
    "application_email": ["Enter a valid email address."]
}
```

---

### 6. Update Job (Admin)

**Endpoint:** `PATCH /api/jobs/admin/{id}/update/`

Update an existing job. Only include fields you want to change (partial update).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Job ID to update |

#### Request Example - Update Title and Status

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
    "title": "Lead Software Engineer",
    "is_featured": true
}
```

#### Request Example - Deactivate Job

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
    "is_active": false
}
```

#### Response (200 OK)

Returns the full updated job object.

---

### 7. Delete Job (Admin)

**Endpoint:** `DELETE /api/jobs/admin/{id}/delete/`

Permanently delete a job posting.

> ⚠️ **Warning:** This action cannot be undone. Consider deactivating instead.

#### Request Example

```http
DELETE /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/delete/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Response (204 No Content)

Empty response body on success.

#### Response (404 Not Found)

```json
{
    "error": "Job not found"
}
```

---

## 📦 Data Models

### Job Object (Full)

```typescript
interface Job {
    id: string;                    // UUID
    title: string;                 // Job title
    slug: string;                  // URL-friendly slug
    department: string | null;     // Department name
    location: string | null;       // Job location
    type: 'full-time' | 'part-time' | 'contract' | 'internship';
    description: string;           // HTML content
    requirements: string | null;   // HTML content
    responsibilities: string | null; // HTML content
    application_email: string;     // Email for applications
    application_method: string | null; // HTML content
    is_active: boolean;            // Active status
    is_featured: boolean;          // Featured status
    posted_at: string;             // ISO 8601 datetime
    expires_at: string | null;     // ISO 8601 datetime or null
    created_at: string;            // ISO 8601 datetime
    updated_at: string;            // ISO 8601 datetime
}
```

### Job Object (List View)

```typescript
interface JobListItem {
    id: string;
    title: string;
    slug: string;
    department: string | null;
    location: string | null;
    type: string;
    is_featured: boolean;
    posted_at: string;
    expires_at: string | null;
}
```

### Paginated Response

```typescript
interface PaginatedResponse<T> {
    count: number;         // Total count
    next: string | null;   // Next page URL
    previous: string | null; // Previous page URL
    results: T[];          // Array of items
}
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Description | When |
|------|-------------|------|
| `200` | OK | Request successful |
| `201` | Created | Job created successfully |
| `204` | No Content | Job deleted successfully |
| `400` | Bad Request | Validation error |
| `401` | Unauthorized | Missing/invalid token |
| `404` | Not Found | Job doesn't exist or expired |
| `500` | Server Error | Backend error |

### Error Response Format

```json
{
    "error": "Error message here"
}
```

Or for validation errors:

```json
{
    "field_name": ["Error message 1", "Error message 2"],
    "another_field": ["Error message"]
}
```

### JavaScript Error Handling Example

```javascript
const apiRequest = async (url, options = {}) => {
    const token = localStorage.getItem('access_token');

    const config = {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
            ...options.headers,
        },
    };

    const response = await fetch(url, config);

    if (response.status === 401) {
        // Handle token expiration - redirect to login
        throw new Error('Session expired. Please login again.');
    }

    if (response.status === 404) {
        throw new Error('Resource not found');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Request failed');
    }

    // Handle 204 No Content
    if (response.status === 204) {
        return null;
    }

    return response.json();
};
```

---

## 💻 Code Examples

### React Hook Example

```javascript
import { useState, useEffect, useCallback } from 'react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Hook for fetching jobs
export const useJobs = (filters = {}) => {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({ count: 0, next: null, previous: null });

    const fetchJobs = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const params = new URLSearchParams(
                Object.entries(filters).filter(([_, v]) => v !== undefined && v !== '')
            );

            const response = await fetch(`${API_BASE}/api/jobs/?${params}`);

            if (!response.ok) throw new Error('Failed to fetch jobs');

            const data = await response.json();

            setJobs(data.results || data);
            setPagination({
                count: data.count || data.length,
                next: data.next,
                previous: data.previous,
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [JSON.stringify(filters)]);

    useEffect(() => {
        fetchJobs();
    }, [fetchJobs]);

    return { jobs, loading, error, pagination, refetch: fetchJobs };
};

// Usage
const JobsPage = () => {
    const [filters, setFilters] = useState({ type: '', department: '' });
    const { jobs, loading, error, pagination } = useJobs(filters);

    if (loading) return <Spinner />;
    if (error) return <Alert type="error">{error}</Alert>;

    return (
        <div>
            <h1>Jobs ({pagination.count})</h1>
            {jobs.map(job => (
                <JobCard key={job.id} job={job} />
            ))}
        </div>
    );
};
```

### Next.js Server Component Example

```javascript
// app/jobs/page.js
async function getJobs(searchParams) {
    const params = new URLSearchParams(searchParams);
    const res = await fetch(`${process.env.API_URL}/api/jobs/?${params}`, {
        next: { revalidate: 60 }, // Cache for 60 seconds
    });

    if (!res.ok) throw new Error('Failed to fetch jobs');

    return res.json();
}

export default async function JobsPage({ searchParams }) {
    const { results: jobs, count } = await getJobs(searchParams);

    return (
        <main>
            <h1>Careers at ScholarPort ({count} open positions)</h1>
            <JobList jobs={jobs} />
        </main>
    );
}

// app/jobs/[slug]/page.js
async function getJob(slug) {
    const res = await fetch(`${process.env.API_URL}/api/jobs/${slug}/`, {
        next: { revalidate: 60 },
    });

    if (res.status === 404) return null;
    if (!res.ok) throw new Error('Failed to fetch job');

    return res.json();
}

export default async function JobDetailPage({ params }) {
    const job = await getJob(params.slug);

    if (!job) {
        notFound();
    }

    return (
        <main>
            <h1>{job.title}</h1>
            <JobDetail job={job} />
        </main>
    );
}
```

### Admin Panel Example (React + Axios)

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: process.env.REACT_APP_API_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Admin Jobs Service
export const adminJobsService = {
    // List all jobs (including inactive)
    async list(filters = {}) {
        const { data } = await api.get('/api/jobs/admin/', { params: filters });
        return data;
    },

    // Get single job
    async get(id) {
        const { data } = await api.get(`/api/jobs/admin/${id}/`);
        return data;
    },

    // Create job
    async create(jobData) {
        const { data } = await api.post('/api/jobs/admin/create/', jobData);
        return data;
    },

    // Update job
    async update(id, jobData) {
        const { data } = await api.patch(`/api/jobs/admin/${id}/update/`, jobData);
        return data;
    },

    // Delete job
    async delete(id) {
        await api.delete(`/api/jobs/admin/${id}/delete/`);
    },

    // Toggle active status
    async toggleActive(id, isActive) {
        return this.update(id, { is_active: isActive });
    },

    // Toggle featured status
    async toggleFeatured(id, isFeatured) {
        return this.update(id, { is_featured: isFeatured });
    },
};

// Usage in Admin Component
const AdminJobsPage = () => {
    const [jobs, setJobs] = useState([]);

    useEffect(() => {
        adminJobsService.list().then(data => setJobs(data.results));
    }, []);

    const handleDelete = async (id) => {
        if (confirm('Are you sure?')) {
            await adminJobsService.delete(id);
            setJobs(jobs.filter(j => j.id !== id));
        }
    };

    const handleToggleActive = async (job) => {
        const updated = await adminJobsService.toggleActive(job.id, !job.is_active);
        setJobs(jobs.map(j => j.id === job.id ? updated : j));
    };

    return (
        <table>
            <thead>
                <tr>
                    <th>Title</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {jobs.map(job => (
                    <tr key={job.id}>
                        <td>{job.title}</td>
                        <td>{job.department}</td>
                        <td>
                            <button onClick={() => handleToggleActive(job)}>
                                {job.is_active ? '✅ Active' : '❌ Inactive'}
                            </button>
                        </td>
                        <td>
                            <button onClick={() => handleDelete(job.id)}>Delete</button>
                        </td>
                    </tr>
                ))}
            </tbody>
        </table>
    );
};
```

---

## ❓ FAQ

### Q: How do I handle HTML content safely?

**A:** Use `dangerouslySetInnerHTML` in React, but the backend already sanitizes HTML using the `bleach` library. Only safe HTML tags are allowed.

```jsx
<div dangerouslySetInnerHTML={{ __html: job.description }} />
```

### Q: How are slugs generated?

**A:** If you don't provide a slug, it's auto-generated from the title. For example:
- "Senior Software Engineer" → `senior-software-engineer`
- "UI/UX Designer (Remote)" → `ui-ux-designer-remote`

### Q: How does job expiration work?

**A:** Jobs with `expires_at` date in the past are automatically hidden from public endpoints. Admins can still see them.

### Q: What's the difference between `slug` and `id`?

**A:**
- `slug` - URL-friendly string for public pages (`/careers/senior-software-engineer`)
- `id` - UUID for admin operations (`550e8400-e29b-41d4-a716-446655440000`)

### Q: How do featured jobs work?

**A:** Featured jobs (`is_featured: true`) appear at the top of job listings, followed by non-featured jobs.

### Q: What happens if I don't provide optional fields?

**A:** They default to:
- `type` → `"full-time"`
- `is_active` → `true`
- `is_featured` → `false`
- All other optional fields → `null`

### Q: Can I use PUT instead of PATCH for updates?

**A:** No, only PATCH is supported for partial updates.

---

## 📦 Ready-to-Use API Examples (Copy-Paste)

This section contains all the same examples from the Postman collection. Copy-paste these directly!

---

### 🔐 1. Admin Login (Get Token)

```http
POST /api/admin-panel/auth/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "admin123"
}
```

**Response:**
```json
{
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### 📋 2. List Active Jobs (Public)

**Basic Request:**
```http
GET /api/jobs/
```

**Filter by Department:**
```http
GET /api/jobs/?department=Engineering
```

**Filter by Job Type:**
```http
GET /api/jobs/?type=full-time
```

**Filter by Location:**
```http
GET /api/jobs/?location=Remote
```

**Get Featured Jobs Only:**
```http
GET /api/jobs/?featured=true
```

**Search Jobs:**
```http
GET /api/jobs/?search=software
```

**With Pagination:**
```http
GET /api/jobs/?limit=10&offset=0
```

**Multiple Filters Combined:**
```http
GET /api/jobs/?department=Engineering&type=full-time&featured=true&limit=10
```

---

### 📋 3. Get Job by Slug (Public)

```http
GET /api/jobs/senior-software-engineer/
```

---

### 🔒 4. List All Jobs - Admin

**All Jobs (including inactive):**
```http
GET /api/jobs/admin/
Authorization: Bearer {your_token}
```

**Filter Inactive Jobs Only:**
```http
GET /api/jobs/admin/?is_active=false
Authorization: Bearer {your_token}
```

---

### 🔒 5. Create Job - Full Example (Senior Software Engineer)

```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Senior Software Engineer",
    "department": "Engineering",
    "location": "Remote",
    "type": "full-time",
    "description": "<p>We are looking for a <strong>Senior Software Engineer</strong> to join our growing team.</p><p>You will be responsible for designing, developing, and maintaining high-quality software solutions.</p>",
    "requirements": "<ul><li>5+ years of experience in software development</li><li>Proficiency in Python, JavaScript, or similar languages</li><li>Experience with RESTful APIs and microservices</li><li>Strong problem-solving skills</li><li>Excellent communication skills</li></ul>",
    "responsibilities": "<ul><li>Design and implement new features</li><li>Write clean, maintainable code</li><li>Participate in code reviews</li><li>Mentor junior developers</li><li>Collaborate with cross-functional teams</li></ul>",
    "application_email": "careers@scholarport.co",
    "application_method": "<p>Please send your CV and cover letter to <a href='mailto:careers@scholarport.co'>careers@scholarport.co</a></p><p>Include 'Senior Software Engineer Application' in the subject line.</p>",
    "is_active": true,
    "is_featured": true,
    "expires_at": "2025-06-01T00:00:00Z"
}
```

---

### 🔒 5a. Create Job - Minimal (Only Required Fields)

```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Marketing Intern",
    "description": "<p>Join our marketing team as an intern!</p>",
    "application_email": "hr@scholarport.co"
}
```

---

### 🔒 5b. Create Job - Part-Time Position

```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Part-Time Content Writer",
    "department": "Marketing",
    "location": "Kathmandu, Nepal",
    "type": "part-time",
    "description": "<p>We're looking for a talented content writer to create engaging articles about studying abroad.</p>",
    "requirements": "<ul><li>Excellent writing skills in English</li><li>Experience in content marketing</li><li>Knowledge of SEO best practices</li></ul>",
    "application_email": "content@scholarport.co",
    "is_active": true,
    "is_featured": false
}
```

---

### 🔒 5c. Create Job - Internship Position

```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Software Development Intern",
    "department": "Engineering",
    "location": "Hybrid - Kathmandu",
    "type": "internship",
    "description": "<p>Kickstart your career with our 3-month internship program!</p><p>Work alongside experienced developers and learn industry best practices.</p>",
    "requirements": "<ul><li>Currently pursuing a degree in Computer Science or related field</li><li>Basic knowledge of Python or JavaScript</li><li>Eager to learn and grow</li></ul>",
    "responsibilities": "<ul><li>Assist in developing new features</li><li>Write unit tests</li><li>Participate in team meetings</li><li>Document code and processes</li></ul>",
    "application_email": "internships@scholarport.co",
    "application_method": "<p>Apply via email with your resume and a brief introduction about yourself.</p>",
    "is_active": true,
    "is_featured": false,
    "expires_at": "2025-03-01T00:00:00Z"
}
```

---

### 🔒 5d. Create Job - Contract Position

```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "UI/UX Designer (6-Month Contract)",
    "department": "Design",
    "location": "Remote",
    "type": "contract",
    "description": "<p>We're seeking a talented UI/UX designer for a 6-month contract to redesign our student portal.</p>",
    "requirements": "<ul><li>3+ years of UI/UX design experience</li><li>Proficiency in Figma or Sketch</li><li>Portfolio demonstrating web/mobile design work</li><li>Understanding of user-centered design principles</li></ul>",
    "responsibilities": "<ul><li>Redesign the student portal interface</li><li>Create wireframes and prototypes</li><li>Conduct user research</li><li>Collaborate with developers</li></ul>",
    "application_email": "design@scholarport.co",
    "is_active": true,
    "is_featured": true
}
```

---

### 🔒 6. Get Job by ID (Admin)

```http
GET /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer {your_token}
```

---

### 🔒 7. Update Job - Change Title and Featured Status

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Lead Software Engineer",
    "is_featured": true,
    "description": "<p>Updated: We are now looking for a <strong>Lead Software Engineer</strong> to head our development team.</p>"
}
```

---

### 🔒 7a. Update Job - Deactivate (Hide from Public)

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "is_active": false
}
```

---

### 🔒 7b. Update Job - Activate (Show on Public)

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "is_active": true
}
```

---

### 🔒 7c. Update Job - Mark as Featured

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "is_featured": true
}
```

---

### 🔒 7d. Update Job - Set Expiration Date

```http
PATCH /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/update/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "expires_at": "2025-12-31T23:59:59Z"
}
```

---

### 🔒 8. Delete Job (Admin)

```http
DELETE /api/jobs/admin/550e8400-e29b-41d4-a716-446655440000/delete/
Authorization: Bearer {your_token}
```

**Response:** `204 No Content` (empty body on success)

---

## 🧪 Test Scenarios

### Test 1: Verify Admin Auth Required
```http
GET /api/jobs/admin/
```
**Expected:** `401 Unauthorized`

### Test 2: Public Access Works Without Auth
```http
GET /api/jobs/
```
**Expected:** `200 OK`

### Test 3: Invalid Job Type Rejected
```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Test Job",
    "description": "Test",
    "application_email": "test@test.com",
    "type": "invalid-type"
}
```
**Expected:** `400 Bad Request`

### Test 4: Missing Required Fields Rejected
```http
POST /api/jobs/admin/create/
Authorization: Bearer {your_token}
Content-Type: application/json

{
    "title": "Test Job"
}
```
**Expected:** `400 Bad Request` with validation errors

---

## 📚 Related Resources

- **Postman Collection:** `Scholarport_Jobs_API.postman_collection.json`
- **Swagger Documentation:** `/api/schema/swagger-ui/`
- **ReDoc Documentation:** `/api/schema/redoc/`
- **API Schema:** `/api/schema/`

---

## 📞 Support

For backend issues or questions, contact the backend team or raise an issue in the repository.
