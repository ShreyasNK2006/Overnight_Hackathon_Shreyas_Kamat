# 🚀 Deployment Checklist - Document-Role Routing System

## Prerequisites
- [ ] Supabase account with project created
- [ ] Python 3.10+ installed
- [ ] Required packages installed (`pip install -r requirements.txt`)
- [ ] `.env` file configured with credentials

---

## Step 1: Environment Setup

### 1.1 Create .env file
```bash
# In project root: c:\Users\Sujal B\OneDrive\Desktop\cc\.env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
GEMINI_API_KEY=your-gemini-api-key
```

### 1.2 Verify credentials
```bash
python -c "from config.settings import get_settings; print(get_settings())"
```

**Expected output:** Settings object with your URLs/keys

---

## Step 2: Database Schema Deployment

### 2.1 Deploy schema to Supabase

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Create new query
4. Copy entire contents of `database/stakeholder_schema.sql`
5. Paste and run

**What this creates:**
- `roles` table (5 sample roles)
- `role_vectors` table (for embeddings)
- `role_documents` table (document-role associations)
- SQL functions: `match_roles()`, `get_role_documents()`, etc.
- Indexes for performance

### 2.2 Verify tables exist
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('roles', 'role_vectors', 'role_documents');
```

**Expected output:** 3 rows showing all three tables

### 2.3 Check sample data
```sql
SELECT role_name, department FROM roles;
```

**Expected output:** 5 roles
- Safety Officer
- Finance Manager
- Engineering Lead
- Project Manager
- Quality Control Inspector

---

## Step 3: Vectorize Role Responsibilities

### 3.1 Run initialization script
```powershell
cd "c:\Users\Sujal B\OneDrive\Desktop\cc"
python initialize_stakeholders.py
```

**Expected output:**
```
Starting role vectorization...
Found 5 roles to vectorize
Vectorizing: Safety Officer (Safety & Compliance)
✅ Vectorized: Safety Officer
...
✅ VECTORIZATION COMPLETE!
   Total roles: 5
```

### 3.2 Verify vectors created
```sql
SELECT COUNT(*) FROM role_vectors;
```

**Expected output:** 5 (one per role)

### 3.3 Test routing (optional)
```powershell
python initialize_stakeholders.py --test
```

**Expected output:** Sample documents routed to appropriate roles

---

## Step 4: Start Backend Server

### 4.1 Launch FastAPI server
```powershell
cd "c:\Users\Sujal B\OneDrive\Desktop\cc"
python start_server.py
```

**Expected output:**
```
INFO:     Initializing RAG system...
INFO:     ✅ RAG system initialized
INFO:     Initializing Role Manager...
INFO:     ✅ Role Manager initialized
INFO:     Initializing Document-Role Manager...
INFO:     ✅ Document-Role Manager initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4.2 Test health endpoint
```powershell
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "rag_initialized": true
}
```

---

## Step 5: Test API Endpoints

### 5.1 List all roles
```powershell
curl http://localhost:8000/roles
```

**Expected:** JSON array with 5 roles

### 5.2 Get visualization stats (should be empty initially)
```powershell
curl http://localhost:8000/visualization/stats
```

**Expected:**
```json
{
  "role_stats": [],
  "total_assignments": 0,
  "total_roles": 5
}
```

---

## Step 6: Test Document Upload & Auto-Routing

### 6.1 Upload a test PDF
```powershell
curl -X POST http://localhost:8000/ingest `
  -F "file=@path\to\your\test.pdf"
```

**Expected output:**
```json
{
  "status": "success",
  "message": "Document ingested successfully",
  "document_name": "test.pdf",
  "stats": {
    "text_sections": 10,
    "tables_processed": 2,
    "images_uploaded": 1,
    "doc_id": "uuid-here",
    "total_pages": 5
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

### 6.2 Verify document was stored
```powershell
curl http://localhost:8000/visualization/stats
```

**Expected:** `total_assignments` should now be 1

### 6.3 Check role documents
```powershell
# Replace {role_id} with actual UUID from GET /roles
curl "http://localhost:8000/roles/{role_id}/documents"
```

**Expected:** Array with your uploaded document

---

## Step 7: Frontend Integration

### 7.1 Verify CORS (if needed)
If frontend is on different port, add CORS middleware to `api.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 7.2 Share API documentation
Send `API_DOCUMENTATION.md` to frontend team

### 7.3 Test integration
Frontend should be able to:
- Fetch roles: `GET /roles`
- Get dashboard stats: `GET /visualization/stats`
- View role documents: `GET /roles/{role_id}/documents`
- See recent activity: `GET /visualization/recent`

---

## Step 8: Verification Checklist

### Database
- [ ] Schema deployed successfully
- [ ] 5 sample roles exist in `roles` table
- [ ] `role_vectors` table has 5 embeddings
- [ ] `role_documents` table exists (empty initially)
- [ ] SQL functions work (test `match_roles()`)

### Backend
- [ ] Server starts without errors
- [ ] Health check returns `healthy`
- [ ] GET /roles returns 5 roles
- [ ] Role manager initialized
- [ ] Document-role manager initialized

### Routing
- [ ] Document upload works
- [ ] Auto-routing assigns to correct role
- [ ] Assignment stored in `role_documents` table
- [ ] Visualization endpoints return data

### Integration
- [ ] Frontend can connect to backend
- [ ] CORS configured (if needed)
- [ ] API responses match expected format
- [ ] Document metadata includes page numbers and summaries

---

## Troubleshooting

### "Stakeholder manager not initialized"
**Issue:** Old variable name in code  
**Fix:** Already updated to `role_manager` - restart server

### "No roles found in database"
**Issue:** Schema not deployed or vectorization not run  
**Fix:**
1. Deploy `stakeholder_schema.sql` in Supabase
2. Run `python initialize_stakeholders.py`

### "Failed to assign document to role"
**Issue:** Database permission or schema issue  
**Fix:** Check Supabase logs, verify `role_documents` table exists

### Documents not appearing in visualization
**Issue:** Auto-routing might have failed  
**Fix:** Check server logs for routing errors, verify threshold settings

### Embeddings fail
**Issue:** Missing sentence-transformers or model download  
**Fix:**
```powershell
pip install sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### Gemini API errors
**Issue:** Invalid API key or quota exceeded  
**Fix:** Check `GEMINI_API_KEY` in .env, verify quota in Google AI Studio

---

## Quick Command Reference

```powershell
# Deploy and initialize
python initialize_stakeholders.py

# Test routing
python initialize_stakeholders.py --test

# Start server
python start_server.py

# Test health
curl http://localhost:8000/health

# List roles
curl http://localhost:8000/roles

# Upload document
curl -X POST http://localhost:8000/ingest -F "file=@test.pdf"

# Get stats
curl http://localhost:8000/visualization/stats

# Get recent assignments
curl http://localhost:8000/visualization/recent

# API docs (interactive)
# Open in browser: http://localhost:8000/docs
```

---

## Success Indicators

✅ **Database:** 5 roles with vectors  
✅ **Server:** Running on port 8000  
✅ **Upload:** Documents route automatically  
✅ **Storage:** Assignments in `role_documents`  
✅ **Visualization:** Endpoints return data  
✅ **Frontend:** Can fetch and display  

---

## Next Steps After Deployment

1. **Test with real documents**
   - Upload various PDF types
   - Verify correct routing
   - Check confidence scores

2. **Monitor performance**
   - Check database query speeds
   - Monitor API response times
   - Review routing accuracy

3. **Frontend development**
   - Build dashboard with stats
   - Create role detail pages
   - Add recent activity feed

4. **Production readiness**
   - Add authentication
   - Implement rate limiting
   - Set up logging/monitoring
   - Configure production database

---

## Support Files

- `API_DOCUMENTATION.md` - Complete API reference
- `IMPLEMENTATION_SUMMARY.md` - System overview
- `PROJECT_ARCHITECTURE.md` - Technical architecture
- `database/stakeholder_schema.sql` - Database schema
- `initialize_stakeholders.py` - Setup script

---

## Ready to Deploy? 🚀

Follow steps 1-8 in order. Each step builds on the previous one.

**Estimated Time:** 15-20 minutes

**Questions?** Check troubleshooting section or review implementation summary.
