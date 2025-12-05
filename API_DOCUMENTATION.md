# API Documentation - Document-Role Visualization Backend

## Overview
Backend API endpoints for the role-based document routing and visualization system. Documents are automatically routed to roles (job positions) based on semantic matching, and all assignments are stored for visualization.

## Base URL
```
http://localhost:8000
```

---

## Visualization Endpoints

### 1. Get All Roles
**GET** `/roles`

Returns list of all roles in the system.

**Query Parameters:**
- `active_only` (boolean, default: true) - Only return active roles

**Response:**
```json
[
  {
    "role_id": "uuid",
    "role_name": "Safety Officer",
    "department": "Safety & Compliance",
    "responsibilities": "Oversees all safety protocols...",
    "priority": 1,
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### 2. Get Documents for Specific Role
**GET** `/roles/{role_id}/documents`

Returns all documents assigned to a specific role with metadata.

**Path Parameters:**
- `role_id` (string, required) - UUID of the role

**Query Parameters:**
- `limit` (int, default: 100) - Max documents to return
- `offset` (int, default: 0) - Pagination offset

**Response:**
```json
{
  "role_id": "uuid",
  "documents": [
    {
      "assignment_id": "uuid",
      "document_name": "safety_report_2024.pdf",
      "document_id": "doc_uuid",
      "page_number": 5,
      "total_pages": 20,
      "summary": "Safety incident report for construction site",
      "confidence": 0.89,
      "routed_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "fallback_used": false,
        "confidence_level": "high",
        "department": "Safety & Compliance"
      }
    }
  ],
  "count": 1,
  "limit": 100,
  "offset": 0
}
```

---

### 3. Get Visualization Statistics
**GET** `/visualization/stats`

Returns overall statistics for the visualization dashboard.

**Response:**
```json
{
  "role_stats": [
    {
      "role_id": "uuid",
      "role_name": "Safety Officer",
      "department": "Safety & Compliance",
      "document_count": 15,
      "latest_assignment": "2024-01-15T10:30:00Z"
    },
    {
      "role_id": "uuid",
      "role_name": "Finance Manager",
      "department": "Finance",
      "document_count": 8,
      "latest_assignment": "2024-01-14T15:20:00Z"
    }
  ],
  "total_assignments": 23,
  "total_roles": 5
}
```

**Use Case:**
Perfect for dashboard overview showing:
- Which roles have the most documents
- Document distribution across departments
- Overall system activity

---

### 4. Get Recent Assignments
**GET** `/visualization/recent`

Returns the most recent document-role assignments.

**Query Parameters:**
- `limit` (int, default: 20) - Max assignments to return

**Response:**
```json
{
  "recent_assignments": [
    {
      "assignment_id": "uuid",
      "role_name": "Safety Officer",
      "document_name": "incident_report.pdf",
      "confidence": 0.92,
      "routed_at": "2024-01-15T10:30:00Z",
      "department": "Safety & Compliance"
    }
  ],
  "count": 20
}
```

**Use Case:**
Activity feed showing latest document routing actions.

---

### 5. Get Role Summary by Name
**GET** `/visualization/role/{role_name}`

Get comprehensive details for a specific role including all documents.

**Path Parameters:**
- `role_name` (string, required) - Name of the role (e.g., "Safety Officer")

**Response:**
```json
{
  "role": {
    "role_id": "uuid",
    "role_name": "Safety Officer",
    "department": "Safety & Compliance",
    "responsibilities": "Oversees all safety protocols...",
    "is_active": true
  },
  "documents": [
    {
      "document_name": "safety_report.pdf",
      "page_number": 5,
      "summary": "Safety incident report",
      "confidence": 0.89,
      "routed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total_documents": 15
}
```

**Use Case:**
Detailed role view page showing role info + all assigned documents.

---

## Document Ingestion Endpoint

### Upload & Auto-Route Document
**POST** `/ingest`

Upload a document (PDF/DOCX) for processing and automatic role routing.

**Request:**
- Form-data with `file` field containing the document

**Response:**
```json
{
  "status": "success",
  "message": "Document ingested successfully",
  "document_name": "safety_report.pdf",
  "stats": {
    "text_sections": 45,
    "tables_processed": 3,
    "images_uploaded": 2,
    "total_pages": 20
  },
  "processing_time_ms": 1234.56,
  "routed_to": {
    "role": "Safety Officer",
    "department": "Safety & Compliance",
    "confidence": "high",
    "similarity": 0.89
  }
}
```

**Note:** Documents are automatically routed and stored in `role_documents` table on upload.

---

## Role Management Endpoints

### Create Role
**POST** `/roles`

Create a new role with responsibilities (auto-vectorized for semantic matching).

**Request Body:**
```json
{
  "role_name": "Safety Officer",
  "department": "Safety & Compliance",
  "responsibilities": "Oversees all safety protocols, conducts site inspections...",
  "priority": 1
}
```

**Response:** Role object (see GET /roles response)

---

### Get Single Role
**GET** `/roles/{role_id}`

Get details of a specific role.

---

### Update Role
**PUT** `/roles/{role_id}`

Update role information (responsibilities will be re-vectorized).

---

### Delete Role
**DELETE** `/roles/{role_id}`

Delete a role (soft delete by default).

**Query Parameters:**
- `permanent` (boolean, default: false) - Hard delete if true

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message description"
}
```

**HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid parameters)
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Data Models

### RoleDocument
```typescript
interface RoleDocument {
  assignment_id: string;      // UUID
  document_name: string;       // Original filename
  document_id: string;         // UUID from ingestion
  page_number: number;         // Starting page
  total_pages: number;         // Total pages in document
  summary: string;             // Document summary
  confidence: number;          // Routing confidence (0-1)
  routed_at: string;          // ISO timestamp
  metadata: {
    fallback_used: boolean;
    confidence_level: string;  // "high", "medium", "low"
    department: string;
  };
}
```

### Role
```typescript
interface Role {
  role_id: string;            // UUID
  role_name: string;
  department: string;
  responsibilities: string;   // Detailed job description
  priority: number;           // For tie-breaking (higher = more priority)
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
```

---

## Frontend Integration Guide

### Example: Dashboard Statistics
```javascript
// Fetch overall stats
const response = await fetch('http://localhost:8000/visualization/stats');
const data = await response.json();

// data.role_stats contains array of {role_name, document_count, ...}
// Use for bar chart or pie chart visualization
```

### Example: Role-Specific Document List
```javascript
// Get all documents for Safety Officer role
const roleId = 'uuid-here';
const response = await fetch(`http://localhost:8000/roles/${roleId}/documents?limit=50`);
const data = await response.json();

// data.documents contains array of document assignments
// Display in table with columns: document_name, page_number, summary, confidence, routed_at
```

### Example: Recent Activity Feed
```javascript
// Get last 10 assignments
const response = await fetch('http://localhost:8000/visualization/recent?limit=10');
const data = await response.json();

// data.recent_assignments contains chronological list
// Display as timeline or activity feed
```

---

## Database Schema Reference

### Tables Used
1. **roles** - Stores role definitions
2. **role_vectors** - Vectorized responsibilities for semantic matching
3. **role_documents** - Document-role associations (the main data source for visualization)

### Key Indexes
- `idx_role_docs_role` - Fast lookup by role_id
- `idx_role_docs_document` - Fast lookup by document_id
- `idx_role_docs_routed_at` - Chronological ordering

---

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Test Document Upload
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@test_document.pdf"
```

### Get All Roles
```bash
curl http://localhost:8000/roles
```

---

## Notes for Frontend Team

1. **Authentication**: Currently no auth - add if needed
2. **CORS**: Configure CORS in FastAPI if frontend is on different port
3. **Pagination**: Use `limit` and `offset` for large document lists
4. **Real-time Updates**: Consider WebSocket for live routing notifications (future enhancement)
5. **Error Handling**: All endpoints return structured errors - display user-friendly messages
6. **Date Formatting**: All timestamps are ISO 8601 format - use date library for formatting

---

## Support

For backend issues, check:
- FastAPI logs: `python start_server.py` output
- Database connection: Verify Supabase credentials in `.env`
- Role initialization: Run `python initialize_stakeholders.py` to create sample roles
