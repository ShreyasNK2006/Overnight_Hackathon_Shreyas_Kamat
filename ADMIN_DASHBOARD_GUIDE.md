# 📊 Admin Dashboard API - Complete Guide

## Overview
Complete admin visualization system showing ALL documents, role assignments, analytics, and system overview. This gives administrators a bird's-eye view of the entire document routing system.

---

## 🎯 What Admin Can See

1. **All Documents** - Every document uploaded to the system
2. **Role Assignments** - Which documents are assigned to which roles
3. **System Statistics** - Document counts, role distribution, confidence scores
4. **Analytics** - Charts and trends over time
5. **Search & Filter** - Find specific documents or filter by role
6. **Management** - Delete incorrect assignments

---

## API Endpoints

### 1. 🏠 Complete Admin Dashboard
**GET** `/admin/dashboard`

**The main admin endpoint - returns everything in one call**

**Response:**
```json
{
  "overview": {
    "total_documents": 45,
    "total_assignments": 52,
    "total_roles": 5,
    "active_roles_with_documents": 5,
    "unassigned_roles": 0
  },
  "roles": [
    {
      "id": "uuid",
      "role_name": "Safety Officer",
      "department": "Safety & Compliance",
      "responsibilities": "Handles all safety matters...",
      "priority": 10,
      "document_count": 15
    }
  ],
  "all_documents": [
    {
      "id": "uuid",
      "document_name": "safety_report.pdf",
      "document_id": "doc-uuid",
      "role_id": "uuid",
      "role_name": "Safety Officer",
      "department": "Safety & Compliance",
      "page_number": 5,
      "total_pages": 20,
      "summary": "Safety incident report...",
      "confidence": 0.89,
      "routed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "recent_activity": [
    {
      "assignment_id": "uuid",
      "role_name": "Finance Manager",
      "document_name": "invoice.pdf",
      "confidence": 0.92,
      "routed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "role_distribution": [
    {
      "role_id": "uuid",
      "role_name": "Safety Officer",
      "department": "Safety & Compliance",
      "document_count": 15,
      "latest_assignment": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Use Case:**
- Main admin dashboard page
- Shows complete system overview
- All roles with document counts
- All documents with assignments
- Recent activity feed

---

### 2. 📄 All Documents with Filtering
**GET** `/admin/documents`

**Query Parameters:**
- `search` (string, optional) - Search in document names or summaries
- `role_id` (string, optional) - Filter by specific role
- `limit` (int, default: 100) - Max results
- `offset` (int, default: 0) - Pagination offset

**Examples:**

```bash
# Get all documents
GET /admin/documents

# Search for "safety" in document names/summaries
GET /admin/documents?search=safety

# Get documents for specific role
GET /admin/documents?role_id={uuid}

# Search within a specific role
GET /admin/documents?search=incident&role_id={uuid}

# Pagination
GET /admin/documents?limit=20&offset=40
```

**Response:**
```json
{
  "documents": [
    {
      "id": "uuid",
      "document_name": "safety_incident.pdf",
      "document_id": "doc-uuid",
      "role_id": "uuid",
      "roles": {
        "role_name": "Safety Officer",
        "department": "Safety & Compliance"
      },
      "page_number": 1,
      "total_pages": 10,
      "summary": "Incident report for construction site",
      "confidence": 0.89,
      "routed_at": "2024-01-15T10:30:00Z",
      "metadata": {
        "fallback_used": false,
        "confidence_level": "high"
      }
    }
  ],
  "count": 1,
  "filters": {
    "search": "safety",
    "role_id": null
  }
}
```

---

### 3. 🔍 Document Assignment Details
**GET** `/admin/documents/{document_id}/assignments`

Shows all roles that have been assigned a specific document.

**Response:**
```json
{
  "document_id": "doc-uuid",
  "assignments": [
    {
      "id": "assignment-uuid",
      "role_id": "uuid",
      "roles": {
        "role_name": "Safety Officer",
        "department": "Safety & Compliance"
      },
      "document_name": "incident_report.pdf",
      "confidence": 0.89,
      "routed_at": "2024-01-15T10:30:00Z",
      "summary": "Safety incident report..."
    }
  ],
  "total_roles_assigned": 1
}
```

**Use Case:**
- Document detail page
- See which roles have access to this document
- Audit document routing decisions

---

### 4. 📊 Analytics & Charts
**GET** `/admin/analytics`

**Complete analytics data for visualization charts**

**Response:**
```json
{
  "role_distribution": [
    {
      "role": "Safety Officer",
      "count": 15
    },
    {
      "role": "Finance Manager",
      "count": 12
    }
  ],
  "department_distribution": [
    {
      "department": "Safety & Compliance",
      "count": 15
    },
    {
      "department": "Finance",
      "count": 12
    }
  ],
  "confidence_stats": {
    "average": 0.847,
    "high": 35,
    "medium": 8,
    "low": 2,
    "total": 45
  },
  "temporal_trends": [
    {
      "date": "2024-01-09",
      "count": 3
    },
    {
      "date": "2024-01-10",
      "count": 5
    },
    {
      "date": "2024-01-11",
      "count": 8
    }
  ],
  "total_documents": 45,
  "total_assignments": 52
}
```

**Chart Ideas:**

**Bar Chart - Documents by Role:**
```javascript
data: analytics.role_distribution
x-axis: role
y-axis: count
```

**Pie Chart - Documents by Department:**
```javascript
data: analytics.department_distribution
labels: department
values: count
```

**Donut Chart - Confidence Distribution:**
```javascript
data: [
  { label: "High Confidence (≥0.8)", value: analytics.confidence_stats.high },
  { label: "Medium (0.6-0.8)", value: analytics.confidence_stats.medium },
  { label: "Low (<0.6)", value: analytics.confidence_stats.low }
]
```

**Line Chart - Documents Over Time:**
```javascript
data: analytics.temporal_trends
x-axis: date
y-axis: count
```

---

### 5. 🗑️ Delete Assignment (Admin Action)
**DELETE** `/admin/assignments/{assignment_id}`

Remove incorrect document-role assignments.

**Response:**
```json
{
  "status": "success",
  "message": "Assignment deleted successfully",
  "assignment_id": "uuid"
}
```

---

## 🎨 Frontend Integration Examples

### Dashboard Overview Page

```javascript
// Fetch complete dashboard data
const response = await fetch('http://localhost:8000/admin/dashboard');
const data = await response.json();

// Display overview stats
<div className="stats">
  <StatCard title="Total Documents" value={data.overview.total_documents} />
  <StatCard title="Total Assignments" value={data.overview.total_assignments} />
  <StatCard title="Active Roles" value={data.overview.total_roles} />
</div>

// Display roles with document counts
<RoleList roles={data.roles} />

// Display all documents in table
<DocumentTable documents={data.all_documents} />

// Display recent activity feed
<ActivityFeed activities={data.recent_activity} />
```

---

### Documents Page with Search

```javascript
const [search, setSearch] = useState('');
const [selectedRole, setSelectedRole] = useState(null);

// Fetch filtered documents
const fetchDocuments = async () => {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (selectedRole) params.append('role_id', selectedRole);
  
  const response = await fetch(`http://localhost:8000/admin/documents?${params}`);
  const data = await response.json();
  return data.documents;
};

// UI
<SearchBar value={search} onChange={setSearch} />
<RoleFilter roles={roles} selected={selectedRole} onChange={setSelectedRole} />
<DocumentTable documents={documents} />
```

---

### Analytics Dashboard

```javascript
// Fetch analytics
const response = await fetch('http://localhost:8000/admin/analytics');
const analytics = await response.json();

// Bar chart - Documents by Role
<BarChart
  data={analytics.role_distribution}
  xKey="role"
  yKey="count"
  title="Documents by Role"
/>

// Pie chart - By Department
<PieChart
  data={analytics.department_distribution}
  labelKey="department"
  valueKey="count"
  title="Department Distribution"
/>

// Line chart - Trends
<LineChart
  data={analytics.temporal_trends}
  xKey="date"
  yKey="count"
  title="Documents Over Time"
/>

// Confidence stats
<ConfidenceStats stats={analytics.confidence_stats} />
```

---

### Document Detail Page

```javascript
// Get specific document's assignments
const response = await fetch(`http://localhost:8000/admin/documents/${documentId}/assignments`);
const data = await response.json();

// Display document info + all assigned roles
<DocumentHeader document={data.assignments[0]} />
<AssignedRoles assignments={data.assignments} />

// Delete assignment button (admin only)
<Button onClick={() => deleteAssignment(assignmentId)}>
  Remove Assignment
</Button>
```

---

## 📱 Sample Admin Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│                     ADMIN DASHBOARD                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📊 Overview Stats                                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐             │
│  │   Total    │ │   Total    │ │   Active   │             │
│  │ Documents  │ │Assignments │ │   Roles    │             │
│  │     45     │ │     52     │ │      5     │             │
│  └────────────┘ └────────────┘ └────────────┘             │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  📈 Analytics                                               │
│  ┌──────────────────────────┐ ┌────────────────────────┐  │
│  │ Documents by Role        │ │ Confidence Distribution│  │
│  │ [Bar Chart]              │ │ [Donut Chart]          │  │
│  │                          │ │                        │  │
│  └──────────────────────────┘ └────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Documents Over Time [Line Chart]                    │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  🔍 Search & Filter                                         │
│  [Search: ________] [Filter by Role: ▼ All Roles]          │
│                                                             │
│  📄 All Documents                                           │
│  ┌───────────────────────────────────────────────────────┐ │
│  │ Document Name     | Role         | Confidence | Date  │ │
│  ├───────────────────────────────────────────────────────┤ │
│  │ safety_report.pdf | Safety Off.  | 89%       | 1/15  │ │
│  │ invoice_2024.pdf  | Finance Mgr  | 92%       | 1/15  │ │
│  │ blueprint_v2.pdf  | Eng. Lead    | 85%       | 1/14  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⚡ Recent Activity                                         │
│  • invoice.pdf → Finance Manager (92%) - 2 mins ago        │
│  • safety_report.pdf → Safety Officer (89%) - 5 mins ago   │
│  • blueprint.pdf → Engineering Lead (85%) - 10 mins ago    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Considerations

**Important:** These are admin-only endpoints!

### Recommended Security:
1. **Add Authentication**
   ```python
   from fastapi import Depends, HTTPException, status
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   async def verify_admin(token: str = Depends(security)):
       # Verify JWT token, check admin role
       if not is_admin(token):
           raise HTTPException(status_code=403, detail="Admin access required")
   
   @app.get("/admin/dashboard", dependencies=[Depends(verify_admin)])
   async def get_admin_dashboard():
       ...
   ```

2. **Add CORS restrictions**
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-admin-domain.com"],
       allow_credentials=True,
       allow_methods=["GET", "DELETE"],
       allow_headers=["*"],
   )
   ```

3. **Rate Limiting**
   - Limit admin API calls to prevent abuse
   - Use Redis or in-memory store for rate limiting

4. **Audit Logging**
   - Log all admin actions (especially deletions)
   - Track who accessed what and when

---

## 🧪 Testing Endpoints

### 1. Test Dashboard
```bash
curl http://localhost:8000/admin/dashboard
```

### 2. Test Document Search
```bash
# Search for "safety"
curl "http://localhost:8000/admin/documents?search=safety"

# Filter by role
curl "http://localhost:8000/admin/documents?role_id={uuid}"
```

### 3. Test Analytics
```bash
curl http://localhost:8000/admin/analytics
```

### 4. Test Delete Assignment
```bash
curl -X DELETE http://localhost:8000/admin/assignments/{assignment_id}
```

---

## 📊 Data Flow Summary

```
Admin Dashboard Flow:
┌─────────────────┐
│ Admin Opens     │
│ Dashboard       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GET /admin/     │
│ dashboard       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│ Backend Fetches │────▶│ roles table      │
│ Data from:      │     │ role_documents   │
│                 │     │ Calculate stats  │
└────────┬────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│ Returns JSON    │
│ with:           │
│ • Overview      │
│ • All Roles     │
│ • All Documents │
│ • Recent Activity│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Frontend        │
│ Displays:       │
│ • Stats cards   │
│ • Charts        │
│ • Document table│
│ • Activity feed │
└─────────────────┘
```

---

## 🎯 Key Features

✅ **Complete Overview** - See entire system at a glance  
✅ **All Documents** - Every document with assignments  
✅ **Search & Filter** - Find specific documents or filter by role  
✅ **Analytics** - Charts showing distribution and trends  
✅ **Recent Activity** - Track latest system actions  
✅ **Management** - Delete incorrect assignments  
✅ **Performance** - Optimized queries with indexes  

---

## 💡 Pro Tips

1. **Cache Dashboard Data** - Update every 30 seconds instead of real-time
2. **Lazy Load Documents** - Load first 20, then paginate
3. **Export to CSV** - Add export button for admin reports
4. **Notifications** - Alert admin when confidence < 0.6
5. **Bulk Actions** - Select multiple assignments to delete
6. **Document Preview** - Show thumbnail or first page
7. **Role Management** - Link to role CRUD from dashboard

---

## 🚀 Quick Start

1. **Start server** (endpoints already added)
   ```bash
   python start_server.py
   ```

2. **Test admin dashboard**
   ```bash
   curl http://localhost:8000/admin/dashboard
   ```

3. **Build frontend** using the response structure above

4. **Add authentication** before production deployment

---

## 📖 Related Documentation

- `API_DOCUMENTATION.md` - All API endpoints
- `IMPLEMENTATION_SUMMARY.md` - System overview
- `DEPLOYMENT_CHECKLIST.md` - Deployment guide

---

**Admin Dashboard is ready to use! 🎉**

All endpoints are live and returning data. Just build your frontend to consume these APIs.
