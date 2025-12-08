# Jobs/Careers API Specification

**Status:** Frontend Requirement - Backend Implementation Required
**Date:** January 4, 2025
**Priority:** High
**Note:** Frontend sets requirements, backend implements accordingly.

## Overview

The Jobs/Careers API enables job posting management for the ScholarPort platform. This API allows public users to view active job postings and administrators to manage job listings.

## API Endpoints

### Public Endpoints (No Authentication Required)

#### 1. Get All Active Jobs

**Endpoint:** `GET /api/jobs/`

**Description:** Returns a list of all active job postings. Only jobs with `is_active=true` should be returned.

**Query Parameters:**
- `department` (string, optional) - Filter by department
- `location` (string, optional) - Filter by location
- `type` (string, optional) - Filter by job type: 'full-time', 'part-time', 'contract', 'internship'
- `featured` (boolean, optional) - Filter by featured status
- `search` (string, optional) - Search in title, description, requirements
- `limit` (number, optional) - Number of results per page
- `offset` (number, optional) - Pagination offset

**Response:**
```json
[
  {
    "id": "job-uuid-123",
    "title": "Senior Software Engineer",
    "slug": "senior-software-engineer",
    "department": "Engineering",
    "location": "Remote",
    "type": "full-time",
    "description": "<p>We are looking for...</p>",
    "requirements": "<ul><li>5+ years experience</li></ul>",
    "responsibilities": "<ul><li>Develop features</li></ul>",
    "application_email": "careers@scholarport.co",
    "application_method": "<p>Please email your CV...</p>",
    "is_active": true,
    "is_featured": true,
    "posted_at": "2025-01-01T00:00:00Z",
    "expires_at": "2025-03-01T00:00:00Z",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

**Status Codes:**
- `200 OK`: Success

---

#### 2. Get Job by Slug

**Endpoint:** `GET /api/jobs/{slug}/`

**Description:** Get detailed information about a specific job posting by its slug.

**Path Parameters:**
- `slug` (string, required) - Job slug

**Response:**
```json
{
  "id": "job-uuid-123",
  "title": "Senior Software Engineer",
  "slug": "senior-software-engineer",
  "department": "Engineering",
  "location": "Remote",
  "type": "full-time",
  "description": "<p>We are looking for...</p>",
  "requirements": "<ul><li>5+ years experience</li></ul>",
  "responsibilities": "<ul><li>Develop features</li></ul>",
  "application_email": "careers@scholarport.co",
  "application_method": "<p>Please email your CV...</p>",
  "is_active": true,
  "is_featured": true,
  "posted_at": "2025-01-01T00:00:00Z",
  "expires_at": "2025-03-01T00:00:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Job not found or inactive

---

### Admin Endpoints (Require JWT Authentication)

All admin endpoints require `Authorization: Bearer {token}` header.

#### 3. List All Jobs (Admin)

**Endpoint:** `GET /api/jobs/admin/`

**Description:** Get all jobs including inactive ones. Used for admin management.

**Query Parameters:**
- `is_active` (boolean, optional) - Filter by active status
- `department` (string, optional) - Filter by department
- `location` (string, optional) - Filter by location
- `type` (string, optional) - Filter by job type
- `featured` (boolean, optional) - Filter by featured status
- `search` (string, optional) - Search in title, description
- `limit` (number, optional) - Number of results per page
- `offset` (number, optional) - Pagination offset

**Response:**
```json
[
  {
    "id": "job-uuid-123",
    "title": "Senior Software Engineer",
    "slug": "senior-software-engineer",
    // ... (same structure as public endpoint)
    "is_active": false,  // Can be false in admin view
  }
]
```

**Status Codes:**
- `200 OK`: Success
- `401 Unauthorized`: Missing or invalid token

---

#### 4. Get Job by ID (Admin)

**Endpoint:** `GET /api/jobs/admin/{id}/`

**Description:** Get job details by ID (admin view, includes inactive jobs).

**Path Parameters:**
- `id` (string, required) - Job ID (UUID)

**Response:**
```json
{
  "id": "job-uuid-123",
  "title": "Senior Software Engineer",
  // ... (same structure as public endpoint)
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Job not found
- `401 Unauthorized`: Missing or invalid token

---

#### 5. Create Job (Admin)

**Endpoint:** `POST /api/jobs/admin/`

**Description:** Create a new job posting.

**Request Body:**
```json
{
  "title": "Senior Software Engineer",
  "slug": "senior-software-engineer",  // Optional, auto-generated from title if not provided
  "department": "Engineering",
  "location": "Remote",
  "type": "full-time",
  "description": "<p>We are looking for...</p>",
  "requirements": "<ul><li>5+ years experience</li></ul>",
  "responsibilities": "<ul><li>Develop features</li></ul>",
  "application_email": "careers@scholarport.co",
  "application_method": "<p>Please email your CV...</p>",
  "is_active": true,
  "is_featured": false,
  "expires_at": "2025-03-01T00:00:00Z"
}
```

**Response:**
```json
{
  "id": "job-uuid-123",
  "title": "Senior Software Engineer",
  "slug": "senior-software-engineer",
  // ... (full job object with created_at, updated_at)
}
```

**Status Codes:**
- `201 Created`: Job created successfully
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Missing or invalid token

---

#### 6. Update Job (Admin)

**Endpoint:** `PATCH /api/jobs/admin/{id}/`

**Description:** Update an existing job posting. All fields are optional.

**Path Parameters:**
- `id` (string, required) - Job ID (UUID)

**Request Body:**
```json
{
  "title": "Updated Job Title",
  "is_active": false,
  "is_featured": true,
  // ... (any fields to update)
}
```

**Response:**
```json
{
  "id": "job-uuid-123",
  "title": "Updated Job Title",
  // ... (updated job object)
}
```

**Status Codes:**
- `200 OK`: Job updated successfully
- `400 Bad Request`: Validation error
- `404 Not Found`: Job not found
- `401 Unauthorized`: Missing or invalid token

---

#### 7. Delete Job (Admin)

**Endpoint:** `DELETE /api/jobs/admin/{id}/`

**Description:** Delete a job posting permanently.

**Path Parameters:**
- `id` (string, required) - Job ID (UUID)

**Response:**
- `204 No Content`: Job deleted successfully
- `404 Not Found`: Job not found
- `401 Unauthorized`: Missing or invalid token

---

## Data Models

### Job Object

```typescript
interface Job {
  id: string;                    // UUID, unique identifier
  title: string;                 // Job title
  slug: string;                  // URL-friendly identifier (auto-generated from title if not provided)
  department?: string;           // Department name (optional)
  location?: string;             // Job location (optional)
  type?: 'full-time' | 'part-time' | 'contract' | 'internship';  // Job type (optional)
  description: string;            // HTML content - Job description
  requirements?: string;          // HTML content - Job requirements (optional)
  responsibilities?: string;     // HTML content - Job responsibilities (optional)
  application_email: string;     // Email address for applications
  application_method?: string;   // HTML content - Custom application instructions (optional)
  is_active: boolean;             // Whether job is active/visible
  is_featured?: boolean;         // Whether job is featured (optional)
  posted_at?: string;            // ISO 8601 date - When job was posted (optional)
  expires_at?: string;           // ISO 8601 date - When job expires (optional)
  created_at: string;           // ISO 8601 date - Creation timestamp
  updated_at: string;           // ISO 8601 date - Last update timestamp
}
```

### JobCreateRequest

```typescript
interface JobCreateRequest {
  title: string;                 // Required
  slug?: string;                 // Optional, auto-generated if not provided
  department?: string;
  location?: string;
  type?: 'full-time' | 'part-time' | 'contract' | 'internship';
  description: string;            // Required
  requirements?: string;
  responsibilities?: string;
  application_email: string;     // Required
  application_method?: string;
  is_active?: boolean;           // Default: true
  is_featured?: boolean;         // Default: false
  expires_at?: string;          // ISO 8601 date
}
```

### JobUpdateRequest

All fields are optional (partial update).

---

## Business Rules

1. **Slug Generation:** If `slug` is not provided in create/update requests, it should be auto-generated from the `title` field (lowercase, replace spaces with hyphens, remove special characters).

2. **Active Jobs:** Public endpoints (`GET /api/jobs/`, `GET /api/jobs/{slug}/`) should only return jobs where `is_active=true`.

3. **Expired Jobs:** Jobs with `expires_at` in the past should be automatically excluded from public endpoints, even if `is_active=true`.

4. **Featured Jobs:** Featured jobs should appear first in listings when `featured=true` filter is used.

5. **HTML Content:** Fields `description`, `requirements`, `responsibilities`, and `application_method` accept HTML content. Backend should sanitize HTML to prevent XSS attacks.

6. **Email Validation:** `application_email` must be a valid email address.

---

## Pagination

For list endpoints, if pagination is implemented:

**Response Format:**
```json
{
  "count": 100,
  "next": "https://api.scholarport.co/api/jobs/?limit=20&offset=20",
  "previous": null,
  "results": [
    // ... array of Job objects
  ]
}
```

**Query Parameters:**
- `limit` (number, default: 20) - Number of results per page
- `offset` (number, default: 0) - Number of results to skip

---

## Error Responses

All error responses should follow this format:

```json
{
  "detail": "Error message here",
  "errors": {
    "field_name": ["Error message for this field"]
  }
}
```

**Common Status Codes:**
- `400 Bad Request`: Validation error
- `401 Unauthorized`: Authentication required or invalid token
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Frontend Implementation

The frontend implementation is complete and ready in:
- **Service:** `lib/services/adminApi.ts` → `jobsApi`
- **Types:** `lib/types/job.ts`
- **Pages:**
  - Public: `/careers` (list), `/careers/[slug]` (detail)
  - Admin: `/admin/jobs` (list), `/admin/jobs/[id]` (edit)

---

## Testing Checklist

- [ ] `GET /api/jobs/` returns only active jobs
- [ ] `GET /api/jobs/{slug}/` returns job details
- [ ] `GET /api/jobs/{slug}/` returns 404 for inactive jobs
- [ ] `GET /api/jobs/admin/` returns all jobs (including inactive)
- [ ] `GET /api/jobs/admin/{id}/` returns job by ID
- [ ] `POST /api/jobs/admin/` creates new job
- [ ] `POST /api/jobs/admin/` auto-generates slug if not provided
- [ ] `PATCH /api/jobs/admin/{id}/` updates job
- [ ] `DELETE /api/jobs/admin/{id}/` deletes job
- [ ] Admin endpoints require authentication
- [ ] Public endpoints work without authentication
- [ ] Expired jobs are excluded from public endpoints
- [ ] HTML content is sanitized
- [ ] Email validation works
- [ ] Pagination works (if implemented)
- [ ] Filtering by department, location, type works
- [ ] Search functionality works

---

## Notes

- **Frontend-Driven Development:** This API specification is defined by frontend requirements. Backend should implement according to this specification.
- **Flexibility:** During UI/UX and UAT testing, features may be added or removed. Backend will be updated accordingly.
- **Priority:** Public endpoints (`GET /api/jobs/`, `GET /api/jobs/{slug}/`) are high priority as they are required for the careers page functionality.
