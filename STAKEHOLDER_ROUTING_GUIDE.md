# Stakeholder Management System

## Overview

This module implements **Vectorized Responsibility Routing** for intelligent document routing to stakeholders based on semantic similarity.

## Architecture

### Philosophy: "Semantic Responsibility Matching"

Instead of hardcoding rules or keyword matching, we turn stakeholder responsibilities into a searchable vector database. When a document arrives, we semantically match it against all stakeholder responsibility descriptions.

### How It Works

```
Document Summary
    ↓
Embed using all-MiniLM-L6-v2
    ↓
Vector Search against Stakeholder Responsibilities
    ↓
Find Top Matches (ranked by similarity)
    ↓
Return Best Match or Fallback to Manager
```

## Database Schema

### Tables

1. **stakeholders**
   - Core stakeholder information
   - Includes `responsibilities` TEXT field (natural language description)
   - Supports soft deletion (`is_active`)
   - Multi-tenant support (`business_id`)

2. **stakeholder_vectors**
   - Vectorized representations of responsibilities
   - 384-dimensional embeddings (all-MiniLM-L6-v2)
   - Auto-updated when responsibilities change

### Functions

- `match_stakeholders()`: Semantic search for document routing
- `get_project_manager()`: Fallback when no match is found

## Setup

### 1. Deploy Database Schema

```bash
# Run the SQL schema in your Supabase SQL Editor
cat database/stakeholder_schema.sql
```

This creates:
- `stakeholders` table
- `stakeholder_vectors` table
- Indexes for performance
- Helper functions
- Sample data (5 stakeholders with non-overlapping responsibilities)

### 2. Verify Installation

The schema includes 5 sample stakeholders:
- **Bob Harrison** - Safety Officer (handles inspections, accidents, safety compliance)
- **Alice Chen** - Finance Manager (handles invoices, payments, procurement)
- **Carlos Rodriguez** - Engineering Lead (handles blueprints, designs, CAD)
- **Diana Foster** - Project Manager (handles coordination, timelines, oversight)
- **Edward Kim** - Quality Control Inspector (handles testing, inspections, certification)

### 3. Vectorize Sample Data

After deploying the schema, vectorize the sample stakeholders:

```python
from stakeholder.manager import get_stakeholder_manager

manager = get_stakeholder_manager()

# Get all stakeholders
stakeholders = manager.list_stakeholders()

# Re-vectorize each one (in case you need to refresh)
for stakeholder in stakeholders:
    manager._vectorize_responsibilities(
        stakeholder.id,
        stakeholder.responsibilities
    )
```

Or use the API endpoint to add new stakeholders (auto-vectorizes).

## API Usage

### Create Stakeholder

```bash
POST /stakeholders
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john.doe@company.com",
  "role": "Environmental Compliance Officer",
  "department": "Environmental",
  "phone": "+1-555-0100",
  "responsibilities": "I handle environmental compliance including waste disposal regulations, air quality monitoring, water treatment standards, environmental impact assessments, and green building certifications. I ensure EPA compliance and manage sustainability initiatives."
}
```

**Response**: Created stakeholder with auto-vectorized responsibilities

### Route Document

```bash
POST /stakeholders/route
Content-Type: application/json

{
  "document_summary": "Invoice for 50 tons of cement from supplier XYZ, total cost $15,000",
  "top_k": 3,
  "threshold": 0.6
}
```

**Response**:
```json
{
  "matches": [
    {
      "stakeholder_id": "uuid-here",
      "name": "Alice Chen",
      "email": "alice.chen@company.com",
      "role": "Finance Manager",
      "department": "Finance & Accounting",
      "similarity": 0.87,
      "confidence": "high"
    }
  ],
  "best_match": { ... },
  "fallback_used": false,
  "processing_time_ms": 45.2
}
```

### List Stakeholders

```bash
GET /stakeholders?active_only=true
```

### Update Stakeholder

```bash
PUT /stakeholders/{id}
Content-Type: application/json

{
  "responsibilities": "Updated responsibilities description..."
}
```

Note: Automatically re-vectorizes if responsibilities change.

### Delete Stakeholder

```bash
# Soft delete (mark inactive)
DELETE /stakeholders/{id}

# Permanent delete
DELETE /stakeholders/{id}?permanent=true
```

### Get Statistics

```bash
GET /stakeholders/stats/overview
```

**Response**:
```json
{
  "total_stakeholders": 5,
  "active_stakeholders": 5,
  "inactive_stakeholders": 0,
  "departments": ["Engineering & Design", "Finance & Accounting", ...],
  "roles": ["Engineering Lead", "Finance Manager", ...]
}
```

## Python Usage

```python
from stakeholder.manager import get_stakeholder_manager
from stakeholder.models import StakeholderCreate

manager = get_stakeholder_manager()

# Create stakeholder
new_stakeholder = StakeholderCreate(
    name="Jane Smith",
    email="jane@company.com",
    role="Legal Counsel",
    responsibilities="I handle contract reviews, legal compliance, dispute resolution..."
)
stakeholder = manager.create_stakeholder(new_stakeholder)

# Route document
result = manager.route_document(
    document_summary="Contract amendment for construction project Phase 2",
    top_k=3,
    threshold=0.6
)

print(f"Best match: {result['best_match'].name}")
print(f"Confidence: {result['best_match'].confidence}")
print(f"Similarity: {result['best_match'].similarity:.2%}")
```

## Key Features

### 1. Semantic Matching
- No keyword rules needed
- Understands nuance (e.g., "Safety Invoice" → Finance, not Safety)
- Handles synonyms and context

### 2. Scalability
- Handles 500+ employees efficiently
- Vector search in milliseconds
- No context limits (unlike LLM-based routing)

### 3. Confidence Scoring
- **High** (≥80%): Strong match
- **Medium** (65-79%): Reasonable match
- **Low** (<65%): Weak match

### 4. Fallback Mechanism
- If no match meets threshold → Routes to Project Manager
- Prevents documents from being lost

### 5. Multi-Tenant Support
- Filter by `business_id` for organization isolation
- Share infrastructure across clients

## Best Practices

### Writing Good Responsibilities

✅ **Good**:
```
I handle all financial operations including invoices, vendor payments, 
procurement orders, budget tracking, expense reports, payroll processing, 
and financial reconciliation. I handle cement orders, material purchases, 
and supplier contracts.
```

❌ **Bad**:
```
Finance stuff
```

**Guidelines**:
- Be specific and detailed (min 20 characters, aim for 100-300)
- Include keywords that might appear in documents
- List concrete tasks and domains
- Use natural language (not just keywords)
- Avoid overlap with other stakeholders

### Threshold Selection

- **0.8+**: Very strict, only exact matches
- **0.6-0.7**: Recommended - balances accuracy and coverage
- **<0.5**: Too loose, may get irrelevant matches

### Performance Tips

1. **Batch Vectorization**: When adding many stakeholders, batch the vectorization
2. **Cache Results**: For frequent queries, consider caching
3. **Index Maintenance**: Rebuild indexes periodically for large datasets
4. **Monitor Fallbacks**: If fallback rate is high, improve responsibility descriptions

## Advantages Over LLM-Based Routing

| Feature | Vector Routing | LLM Routing |
|---------|---------------|-------------|
| **Speed** | <50ms | 1-5 seconds |
| **Cost** | Free (local) | $0.001-0.01 per query |
| **Scalability** | 50,000 employees | Limited by context |
| **Accuracy** | High (semantic) | Can hallucinate |
| **Maintenance** | Auto-updates | Needs prompt tuning |
| **Offline** | Yes | No (API required) |

## Troubleshooting

### No Matches Found
- Check if stakeholders exist and are active
- Lower the threshold (try 0.5)
- Improve document summaries (more context)
- Verify vectorization completed

### Wrong Matches
- Make responsibilities more specific
- Avoid overlapping descriptions
- Increase threshold for stricter matching
- Add more diverse stakeholders

### Slow Performance
- Check index creation (`idx_stakeholder_embedding`)
- Verify pgvector is enabled
- Reduce `top_k` parameter
- Monitor database load

## Future Enhancements

1. **Learning System**: Track routing accuracy and adjust
2. **Workload Balancing**: Distribute to less busy stakeholders
3. **Hierarchy Support**: Route to manager if stakeholder unavailable
4. **Audit Trail**: Log all routing decisions
5. **A/B Testing**: Compare vector vs LLM routing

## Integration Examples

### With Document Ingestion

```python
from ingestion.pipeline import IngestionPipeline
from stakeholder.manager import get_stakeholder_manager

# 1. Ingest document
pipeline = IngestionPipeline()
stats = pipeline.ingest_document("invoice.pdf")

# 2. Route to stakeholder
manager = get_stakeholder_manager()
result = manager.route_document(
    document_summary=f"New document ingested: {stats['source']}"
)

# 3. Send notification
best_match = result['best_match']
send_email(
    to=best_match.email,
    subject=f"New Document: {stats['source']}",
    body=f"Document routed to you based on: {best_match.responsibilities}"
)
```

### With Query System

```python
from retrieval.rag_query import RAGQuerySystem
from stakeholder.manager import get_stakeholder_manager

# User asks a question
rag = RAGQuerySystem()
answer = rag.query("What are the cement costs?")

# Route to expert for verification
manager = get_stakeholder_manager()
result = manager.route_document(
    document_summary=answer['answer']
)

# Show expert contact
print(f"For more details, contact: {result['best_match'].name}")
```

## License

Part of Infrastructure RAG System - MIT License
