# Infrastructure RAG Project Architecture

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Core Architecture](#core-architecture)
4. [Database Schema](#database-schema)
5. [Ingestion Pipeline](#ingestion-pipeline)
6. [Retrieval & Generation](#retrieval--generation)
7. [Implementation Guidelines](#implementation-guidelines)
8. [Best Practices & Forbidden Patterns](#best-practices--forbidden-patterns)

---

## 🎯 Project Overview

### Role & Objective
**Senior RAG Architect** building an **Intelligent Document Processing System** for Infrastructure Operations.

### Goal
Build a robust retrieval pipeline that handles messy PDFs (blueprints, invoices, reports) containing:
- Text
- Tables
- Images

### Critical Requirements
1. **Traceability**: Always cite sources with page numbers
2. **Context Preservation**: Never split logical sections in half

---

## 🛠️ Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.10+ | Modern Python features |
| **LLM** | Google Gemini 1.5 Flash (`langchain-google-genai`) | • 1M token context<br>• Multimodal support<br>• Cost-effective |
| **Embeddings** | all-MiniLM-L6-v2 (`langchain-huggingface`) | • Free<br>• CPU-compatible<br>• Infinite rate limits<br>• 384 dimensions |
| **Ingestion** | Docling (IBM) | • Computer Vision layout preservation<br>• Table reconstruction to Markdown<br>• Image extraction |
| **Database** | Supabase (PostgreSQL + pgvector) | • Vector similarity search<br>• Storage buckets for images |
| **Orchestration** | LangChain | • RAG pipeline management |

---

## 🏗️ Core Architecture

### Parent-Child Hybrid Search

**Philosophy**: Separate "Searching" from "Reading"

```
┌─────────────────────────────────────────────────────────────┐
│                     Architecture Flow                        │
└─────────────────────────────────────────────────────────────┘

User Query 
    ↓
Vector Search (Child Nodes) ← Small, specific semantic vectors
    ↓
Find Match
    ↓
Get Parent_ID
    ↓
Retrieve Parent Content ← Full, readable content
    ↓
LLM Generation
```

### Node Types

#### 🔵 Parent Node (The Payload)
**Purpose**: What the LLM reads

**Contains**:
- Full section content
- Complete table Markdown
- Image URL wrapper

**Example**:
```markdown
## Safety Protocols

All workers must wear helmets in Zone A.
Emergency exits are marked in red.

![Safety Sign](https://supabase.../safety_sign.png)
```

#### 🔴 Child Node (The Hook)
**Purpose**: What gets searched in vector space

**Contains**:
- Small paragraph snippet (400 chars)
- Table summary (natural language)
- Image caption

**Example**:
```
"Text describing safety protocols for Zone A workers including helmet requirements"
"Table listing cement costs per kilogram for different suppliers"
"Image showing a yellow safety warning sign at construction entrance"
```

---

## 💾 Database Schema

### Supabase Tables

```sql
-- ============================================
-- Table 1: parent_docs (For Reading & Context)
-- ============================================
CREATE TABLE parent_docs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,         -- Markdown Text or "![Image](url)"
    metadata JSONB,                -- {source: "file.pdf", page: 5, type: "text|image"}
    created_at TIMESTAMP           -- For Temporal Conflict Resolution
);

-- ============================================
-- Table 2: child_vectors (For Searching)
-- ============================================
CREATE TABLE child_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,         -- Text proxy (Summary/Caption/Snippet)
    embedding vector(384),         -- 384 dim for all-MiniLM-L6-v2
    parent_id UUID REFERENCES parent_docs(id),
    metadata JSONB                 -- Copies parent metadata
);

-- ============================================
-- Indexes for Performance
-- ============================================
CREATE INDEX idx_child_embedding ON child_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX idx_parent_id ON child_vectors(parent_id);
CREATE INDEX idx_metadata ON parent_docs USING gin(metadata);
```

### Metadata Structure

```json
{
  "source": "construction_report_2024.pdf",
  "page": 5,
  "type": "text|table|image",
  "section_header": "Safety Protocols",
  "uploaded_at": "2025-12-05T10:30:00Z"
}
```

---

## 📥 Ingestion Pipeline

### The Router Architecture

```python
# Pseudocode Flow
def process_document(pdf_file):
    elements = docling.parse(pdf_file)  # Returns structured elements
    
    for element in elements:
        if element.type == "TEXT":
            handle_text(element)
        elif element.type == "TABLE":
            handle_table(element)
        elif element.type == "IMAGE":
            handle_image(element)
```

### 1️⃣ TEXT Handling

#### Parent Splitter
```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

# Split on headers to preserve logical sections
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)
```

**Why?** Keeps logical sections together (e.g., "Safety Protocols" with all sub-points)

#### Child Splitter
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Process**:
1. Split parent content into 400-char chunks
2. Embed each chunk
3. Store embeddings as child nodes with `parent_id` reference

---

### 2️⃣ TABLE Handling

#### Problem
Vector search fails on raw table grids.

#### Strategy: "Shadow Summary"

```
Raw Table (Parent):
| Material | Cost/kg | Supplier |
|----------|---------|----------|
| Cement   | $12.50  | ABC Corp |
| Steel    | $45.00  | XYZ Ltd  |

↓ (Gemini generates summary)

Summary (Child):
"Table listing construction material costs including cement at $12.50 per kg 
from ABC Corp and steel at $45.00 per kg from XYZ Ltd"
```

**Implementation**:
```python
# Parent: Store raw Markdown table
parent_content = """
| Material | Cost/kg | Supplier |
|----------|---------|----------|
| Cement   | $12.50  | ABC Corp |
| Steel    | $45.00  | XYZ Ltd  |
"""

# Child: Generate natural language summary
prompt = f"Summarize this table in natural language:\n{parent_content}"
summary = gemini.generate(prompt)

# Store parent with full table, child with summary
```

---

### 3️⃣ IMAGE Handling

#### Problem
Cannot embed pixels directly.

#### Strategy: "Image-as-Parent" Wrapper

**Step 1: Upload to Supabase Storage**
```python
# Upload image file
image_bytes = extract_image_from_pdf(page_num)
storage_client.upload(
    bucket="project_images",
    path=f"{doc_id}/image_{page_num}.png",
    file=image_bytes
)

# Get public URL
image_url = storage_client.get_public_url(
    "project_images", 
    f"{doc_id}/image_{page_num}.png"
)
```

**Step 2: Create Parent Node**
```python
# Store as Markdown image wrapper
parent_content = f"![Safety Warning Sign]({image_url})"

parent_docs.insert({
    "content": parent_content,
    "metadata": {
        "source": "safety_manual.pdf",
        "page": 12,
        "type": "image"
    }
})
```

**Step 3: Generate Caption (Child Node)**
```python
# Use Gemini to describe the image
caption_prompt = f"""
Describe this image in detail for search purposes.
Include: objects, text visible, context, purpose.
Image URL: {image_url}
"""

caption = gemini.generate_with_image(caption_prompt, image_url)
# Example: "Yellow triangular safety warning sign showing 
# hard hat requirement at construction site entrance"

# Embed caption as child
embedding = embed_model.embed(caption)
child_vectors.insert({
    "content": caption,
    "embedding": embedding,
    "parent_id": parent_id
})
```

---

## 🔍 Retrieval & Generation

### The "Dumb" Retriever

**Rule**: Do NOT put logic in the retriever. It simply finds Child and swaps for Parent.

```python
def retrieve(query: str, k: int = 5):
    # 1. Embed query
    query_embedding = embed_model.embed(query)
    
    # 2. Find similar child vectors
    results = child_vectors.similarity_search(
        query_embedding, 
        limit=k
    )
    
    # 3. Swap children for parents
    parent_contents = []
    for child in results:
        parent = parent_docs.get(child.parent_id)
        parent_contents.append({
            "content": parent.content,
            "metadata": parent.metadata,  # MUST preserve source & page
            "score": child.similarity_score
        })
    
    return parent_contents
```

**Traceability Rule**: Every chunk MUST retain:
- `metadata['source']`
- `metadata['page']`

---

### The "Smart" Generator (LLM Prompt)

#### System Prompt Template

```python
SYSTEM_PROMPT = """
You are an Infrastructure Operations Assistant analyzing technical documents.

RULES:
1. CITATIONS: Always cite sources with page numbers.
   Format: "According to [Document Name, Page X]..."
   
2. TEMPORAL AWARENESS: If documents conflict, the LATEST timestamp wins.
   Check metadata['created_at']. Explicitly state: 
   "Document A (Morning) says X, but Document B (Evening) updated this to Y."
   
3. VISUALS: If context contains ![...](url), display it with:
   "Relevant visual: [Image Description](url)"
   
4. NO HALLUCINATION: Only use provided context. If information is missing, say:
   "The provided documents do not contain information about..."
   
5. TABLES: If context contains Markdown tables, preserve formatting in response.

Context Documents:
{context}

User Question: {question}
"""
```

#### Generation Flow

```python
def generate_answer(query: str):
    # 1. Retrieve relevant parent docs
    retrieved_docs = retrieve(query, k=5)
    
    # 2. Build context with metadata
    context_parts = []
    for doc in retrieved_docs:
        source = doc['metadata']['source']
        page = doc['metadata']['page']
        content = doc['content']
        timestamp = doc['metadata'].get('created_at', 'Unknown')
        
        context_parts.append(f"""
[Source: {source}, Page: {page}, Timestamp: {timestamp}]
{content}
---
""")
    
    context = "\n".join(context_parts)
    
    # 3. Generate with Gemini
    prompt = SYSTEM_PROMPT.format(context=context, question=query)
    answer = gemini.generate(prompt)
    
    return answer
```

---

## 📐 Implementation Guidelines

### Directory Structure

```
project_root/
├── ingestion/
│   ├── __init__.py
│   ├── pdf_processor.py      # Docling integration
│   ├── text_handler.py       # TEXT routing
│   ├── table_handler.py      # TABLE routing
│   └── image_handler.py      # IMAGE routing
├── database/
│   ├── __init__.py
│   ├── supabase_client.py    # Connection management
│   └── schema.sql            # Table definitions
├── retrieval/
│   ├── __init__.py
│   ├── embeddings.py         # HuggingFace embeddings
│   ├── retriever.py          # Vector search
│   └── generator.py          # LLM generation
├── config/
│   ├── __init__.py
│   └── settings.py           # API keys, DB credentials
├── main.py                    # Orchestration
├── requirements.txt
└── PROJECT_ARCHITECTURE.md    # This file
```

### Key Configuration

```python
# config/settings.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "project_images"
    
    # Google Gemini
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # Chunking
    TEXT_CHUNK_SIZE: int = 400
    TEXT_CHUNK_OVERLAP: int = 50
    
    class Config:
        env_file = ".env"
```

---

## ✅ Best Practices & Forbidden Patterns

### ✅ DO

| Practice | Reason |
|----------|--------|
| ✅ Use Docling for PDF parsing | Preserves layout, reconstructs tables |
| ✅ Store full tables in Parent | Maintains data integrity |
| ✅ Upload images to Supabase Storage | Scalable, gets public URLs |
| ✅ Generate summaries for tables | Enables semantic search |
| ✅ Generate captions for images | Makes images searchable |
| ✅ Preserve metadata at all stages | Enables traceability |
| ✅ Use MarkdownHeaderTextSplitter | Keeps logical sections together |
| ✅ Check timestamps for conflicts | Resolves contradictions |

### ❌ FORBIDDEN

| Pattern | Why It's Wrong | Correct Alternative |
|---------|---------------|---------------------|
| ❌ `pypdf` for parsing | Destroys table layouts | ✅ Use Docling |
| ❌ Base64 images in DB | Bloats database, slow queries | ✅ Use Supabase Storage URLs |
| ❌ OpenAI embeddings | Costs money, rate limits | ✅ Use all-MiniLM-L6-v2 |
| ❌ Splitting tables in half | Loses meaning | ✅ Keep full table in Parent |
| ❌ Generic chunking for all content | Context loss | ✅ Use type-specific routing |
| ❌ Ignoring timestamps | Outdated information | ✅ Implement temporal awareness |
| ❌ No source citations | Untraceable answers | ✅ Always cite source + page |

---

## 🎯 Success Criteria

Your implementation is successful when:

1. **Query**: "What are the safety requirements for Zone A?"
   - **Returns**: Parent doc with full Safety Protocols section
   - **Cites**: "[Safety Manual, Page 5, Updated 2025-12-05]"

2. **Query**: "Show me the cost breakdown table"
   - **Returns**: Parent doc with full Markdown table
   - **Process**: Child summary matched → Parent table retrieved

3. **Query**: "What does the warning sign look like?"
   - **Returns**: Markdown image `![Warning Sign](https://supabase.../sign.png)`
   - **Process**: Caption matched → Parent image URL retrieved

4. **Temporal Test**: Document A says "Budget: $100K", Document B (later) says "Budget: $150K"
   - **Answer**: "According to [Budget Report, Page 3, Latest: 2025-12-05], the budget was updated to $150K."

---

## 📚 Key Concepts Recap

### Why Parent-Child?

| Problem | Parent-Child Solution |
|---------|----------------------|
| Search needs specificity | Child = Small, focused vectors |
| LLM needs context | Parent = Full, readable content |
| Tables aren't searchable | Child = Natural language summary |
| Images aren't embedable | Child = Descriptive caption |
| Splitting loses meaning | Parent = Complete logical units |

### The Golden Rules

1. **Never split a table**
2. **Always cite sources**
3. **Latest timestamp wins**
4. **Images live in Storage, not DB**
5. **Docling, not pypdf**
6. **all-MiniLM-L6-v2, not OpenAI**

---

## 🚀 Getting Started

### Step 1: Set up Environment
```bash
pip install langchain langchain-google-genai langchain-huggingface
pip install docling supabase sentence-transformers
pip install python-dotenv pydantic
```

### Step 2: Configure Supabase
```sql
-- Run schema.sql in Supabase SQL Editor
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables (see Database Schema section)
-- Create storage bucket for images
```

### Step 3: Implement Ingestion Pipeline
```python
# Follow the routing logic in Ingestion Pipeline section
# Start with text, then tables, then images
```

### Step 4: Build Retrieval System
```python
# Implement "Dumb" retriever
# Implement "Smart" generator with proper prompting
```

### Step 5: Test End-to-End
```python
# Upload test PDF with text, tables, images
# Query and verify:
#   - Correct parent retrieval
#   - Source citations
#   - Image URL display
```

---

## 📞 Architecture Decision Records

### Why Gemini over GPT-4?
- **Context**: 1M tokens vs 128K
- **Cost**: ~10x cheaper
- **Multimodal**: Native image understanding

### Why Local Embeddings?
- **Cost**: $0 vs $0.0001/1K tokens
- **Latency**: No API calls
- **Privacy**: Data stays local

### Why Parent-Child vs Standard RAG?
- **Standard RAG**: Search = Read (loses context)
- **Parent-Child**: Search ≠ Read (preserves context)

---

## 🔗 References

- [Docling Documentation](https://github.com/DS4SD/docling)
- [LangChain Parent Document Retriever](https://python.langchain.com/docs/modules/data_connection/retrievers/parent_document_retriever)
- [Supabase Vector Guide](https://supabase.com/docs/guides/ai/vector-columns)
- [all-MiniLM-L6-v2 Model Card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-05  
**Maintained By**: RAG Architecture Team
