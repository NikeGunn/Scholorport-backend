# Backend API Requests

This file contains requests for backend API endpoints and fixes needed for the frontend.

---

## Request 1
**Date:** December 3, 2025  
**Time:** 1:20 Nepal time

### Missing API Endpoints Required for Frontend

The frontend implementation requires the following API endpoints that are currently **missing** from the backend API documentation (`Scholarport API.yaml`). Please implement these endpoints to match the frontend implementation.

---

### 1. Partners API Endpoints

#### Public Endpoint (for homepage display):
- **`GET /api/partners/`** - Returns list of all active partners (no authentication required)
  - **Response:** Array of Partner objects
  - **Fields:**
    - `id` (string)
    - `name` (string)
    - `type` ('university' | 'agent')
    - `country` (string, optional)
    - `logo` (string, optional) - URL to logo image
    - `description` (string, optional)
    - `website` (string, optional)
    - `featured` (boolean)
    - `createdAt` (string, optional)
    - `updatedAt` (string, optional)

#### Admin Endpoints (require JWT authentication):
- **`GET /api/partners/admin/`** - List all partners (including inactive)
- **`POST /api/partners/admin/`** - Create a new partner
  - **Request Body:** Partner object (without id, createdAt, updatedAt)
- **`PATCH /api/partners/admin/{id}/`** - Update a partner
  - **Path Parameter:** `id` (string) - Partner ID
  - **Request Body:** Partial Partner object
- **`DELETE /api/partners/admin/{id}/`** - Delete a partner
  - **Path Parameter:** `id` (string) - Partner ID

**Partner Schema:**
```json
{
  "id": "string",
  "name": "string",
  "type": "university" | "agent",
  "country": "string (optional)",
  "logo": "string (optional)",
  "description": "string (optional)",
  "website": "string (optional)",
  "featured": "boolean",
  "createdAt": "string (optional)",
  "updatedAt": "string (optional)"
}
```

**Current Issue:** The frontend tries `/api/partners/` (public) first, then falls back to `/api/partners/admin/` (admin). Since the public endpoint doesn't exist, it fails with "Not authenticated" errors on the homepage.

---

### 2. Contact Form API Endpoints

#### Public Endpoint:
- **`POST /api/contact/`** - Submit contact form (no authentication required)
  - **Request Body:**
    ```json
    {
      "name": "string",
      "email": "string",
      "phone": "string (optional)",
      "message": "string",
      "type": "student" | "university" | "agent" | "other"
    }
    ```
  - **Response:** 201 Created or appropriate status code

#### Admin Endpoints (require JWT authentication):
- **`GET /api/contact/admin/`** - List all contact submissions
  - **Response:** Array of ContactFormSubmission objects
- **`PATCH /api/contact/admin/{id}/read/`** - Mark submission as read
  - **Path Parameter:** `id` (string) - Submission ID
- **`DELETE /api/contact/admin/{id}/`** - Delete a submission
  - **Path Parameter:** `id` (string) - Submission ID

**Contact Submission Schema:**
```json
{
  "id": "string",
  "name": "string",
  "email": "string",
  "phone": "string (optional)",
  "message": "string",
  "type": "student" | "university" | "agent" | "other",
  "read": "boolean",
  "createdAt": "string"
}
```

**Current Issue:** The contact form submission endpoint `/api/contact/` is missing, so form submissions will fail.

---

### Priority

**High Priority:**
- `GET /api/partners/` - Required for homepage to display partners without authentication errors
- `POST /api/contact/` - Required for contact form to work

**Medium Priority:**
- Admin endpoints for partners and contact management (needed for admin panel functionality)

---

### Notes

- All admin endpoints should require JWT authentication (Bearer token)
- Public endpoints should not require authentication
- Please update the API documentation (`/api/schema/`) once these endpoints are implemented
- The frontend has been updated to handle missing endpoints gracefully, but functionality will be limited until these are implemented

---

