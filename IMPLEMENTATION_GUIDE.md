# Infrastructure RAG System - Implementation Guide

## 🎯 Current Status: Foundation Complete ✅

### ✅ Completed Components

#### 1. **Project Structure**
```
cc/
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration management with Pydantic
├── database/
│   ├── __init__.py
│   ├── schema.sql           # Supabase schema (already deployed)
│   └── supabase_client.py   # Database operations
├── ingestion/
│   ├── __init__.py
│   ├── pdf_processor.py     # Docling integration
│   ├── markdown_splitter.py # Header-based parent node splitting
│   ├── text_chunker.py      # Recursive text splitting for children
│   ├── multimodal_handler.py # Gemini summaries for tables/images
│   └── pipeline.py          # Main orchestration
├── retrieval/
│   ├── __init__.py
│   └── embeddings.py        # HuggingFace embeddings
├── .env.example             # Environment template
├── requirements.txt         # All dependencies
└── PROJECT_ARCHITECTURE.md  # Full system documentation
```

#### 2. **Ingestion Pipeline** 
The complete workflow is implemented:

```
User uploads PDF
    ↓
Docling extracts images + creates Markdown
    ↓
MarkdownHeaderTextSplitter → Parent Nodes (text/table/image sections)
    ↓
    ├─→ TEXT: RecursiveTextSplitter → Child Chunks → Embed → Store
    ├─→ TABLE: Gemini Summary → Embed → Store (Parent = full table)
    └─→ IMAGE: Upload to Supabase Storage → Gemini Caption → Embed → Store
    ↓
All stored in Supabase (parent_docs + child_vectors)
```

**Key Features:**
- ✅ File reference tracking in metadata
- ✅ Upload timestamp for temporal conflict resolution
- ✅ Parent-child relationship maintained
- ✅ Type-specific processing (text/table/image)

### 📋 Next Steps (Retrieval Phase)

Still need to implement:

1. **Vector Retriever** (`retrieval/retriever.py`)
   - Search child vectors by query embedding
   - Swap children for parents
   - Return parent content with metadata

2. **LLM Generator** (`retrieval/generator.py`)
   - System prompt with citation rules
   - Temporal conflict resolution
   - Source + page number citations

3. **Query Interface** (`main.py` or `query.py`)
   - User query input
   - Orchestrate retrieval + generation
   - Display results with sources

4. **Testing** 
   - Test with sample PDF
   - Verify end-to-end workflow

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Install new dependencies (pydantic-settings added)
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Create .env file
cp .env.example .env
```

Edit `.env` with your values:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_STORAGE_BUCKET=project_images
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. Verify Supabase Setup
- ✅ Database tables created (parent_docs, child_vectors)
- ✅ pgvector extension enabled
- ✅ Storage bucket created (project_images)
- ✅ Bucket is public (for image URLs)

### 4. Test Ingestion (Once Setup Complete)
```python
from ingestion.pipeline import IngestionPipeline

# Create pipeline
pipeline = IngestionPipeline()

# Ingest a document
stats = pipeline.ingest_document("path/to/your/document.pdf")

print(f"Processed {stats['parent_nodes']} sections")
print(f"Created {stats['child_vectors']} searchable chunks")
print(f"Uploaded {stats['images_uploaded']} images")
```

## 📊 Workflow Details

### Parent Node Creation
**MarkdownHeaderTextSplitter** splits by headers:
- Preserves logical sections
- Each section becomes a parent node
- Metadata includes: `source`, `doc_id`, `section_header`, `type`, `uploaded_at`

### Child Node Creation

| Parent Type | Child Processing | Storage |
|-------------|------------------|---------|
| **TEXT** | RecursiveCharacterTextSplitter (400 chars, 50 overlap) | Multiple child vectors per parent |
| **TABLE** | Gemini generates natural language summary | Single child vector with summary |
| **IMAGE** | Upload to storage → Gemini generates caption | Single child vector with caption |

### Metadata Structure
Every node tracks:
```json
{
  "source": "construction_report.pdf",
  "doc_id": "uuid-here",
  "section_header": "Safety Protocols > Zone A",
  "type": "text|table|image",
  "uploaded_at": "2025-12-05T10:30:00Z",
  "processed_at": "2025-12-05T10:30:05Z"
}
```

## 🔍 How It Works

### 1. Document Upload
- User provides PDF path
- Docling parses PDF → Markdown + extracted images
- Images saved to Supabase Storage
- Markdown saved to temp directory

### 2. Parent Node Generation
- Markdown split by headers (H1, H2, H3)
- Each section identified as text/table/image
- Full content stored in `parent_docs` table
- Metadata preserved

### 3. Child Vector Generation

**For TEXT:**
```python
"## Safety Protocols\n\nAll workers must wear helmets..."
    ↓ [Recursive Splitter]
    ↓
["All workers must wear helmets in Zone A...", 
 "Emergency exits are marked in red..."]
    ↓ [Embed each chunk]
    ↓
Store in child_vectors with parent_id reference
```

**For TABLES:**
```python
"| Material | Cost |\n|---|---|\n| Cement | $12.50 |"
    ↓ [Gemini Summary]
    ↓
"Table listing construction material costs including 
 cement at $12.50 per kg from ABC Corp..."
    ↓ [Embed summary]
    ↓
Store in child_vectors (parent still has full table)
```

**For IMAGES:**
```python
"![Safety Sign](uuid/image_0.png)"
    ↓ [Upload to Supabase Storage]
    ↓ [Get public URL]
    ↓ [Gemini generates caption]
    ↓
"Yellow triangular safety warning sign showing 
 hard hat requirement at construction entrance"
    ↓ [Embed caption]
    ↓
Store in child_vectors (parent has image URL)
```

## 🎓 Key Design Decisions

### Why Markdown First?
- Docling preserves document structure
- Headers indicate logical boundaries
- Tables reconstructed properly
- Images extracted with context

### Why Parent-Child?
- **Search** needs small, specific vectors (children)
- **LLM** needs full context (parents)
- Prevents losing meaning by splitting tables/images
- Enables source citation at section level

### Why Separate Table/Image Processing?
- Tables are not semantically searchable in raw format
- Images cannot be embedded as pixels
- Natural language summaries/captions bridge the gap
- Parent preserves original for LLM reading

## 🐛 Troubleshooting

### Common Issues

**ImportError: No module named 'pydantic_settings'**
```bash
pip install pydantic-settings
```

**Supabase connection error**
- Check `.env` file has correct credentials
- Verify Supabase project is active
- Test connection in Supabase dashboard

**Docling model download**
- First run will download models (~1GB)
- Requires internet connection
- Models cached for subsequent runs

**Embedding model download**
- all-MiniLM-L6-v2 downloads on first use (~80MB)
- Cached in `~/.cache/huggingface/`

## 📝 TODO: Retrieval Implementation

Next implementation phase:

```python
# retrieval/retriever.py
class ParentChildRetriever:
    def retrieve(self, query: str, top_k: int = 5):
        # 1. Embed query
        # 2. Search child_vectors
        # 3. Get parent_ids
        # 4. Fetch parent content
        # 5. Return with metadata
        pass

# retrieval/generator.py  
class RAGGenerator:
    def generate(self, query: str, context_docs: List):
        # 1. Build context with citations
        # 2. Apply system prompt
        # 3. Generate answer with Gemini
        # 4. Ensure source citations
        pass

# main.py or query.py
def query_system(question: str):
    retriever = ParentChildRetriever()
    generator = RAGGenerator()
    
    docs = retriever.retrieve(question)
    answer = generator.generate(question, docs)
    
    return answer
```

## 📚 References

- [Docling Documentation](https://github.com/DS4SD/docling)
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [HuggingFace Embeddings](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

---

**Status**: Foundation Phase Complete ✅  
**Next**: Retrieval & Generation Implementation  
**Last Updated**: December 5, 2025
