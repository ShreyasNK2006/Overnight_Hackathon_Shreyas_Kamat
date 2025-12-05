"""
FastAPI Application - Infrastructure RAG System
REST API endpoints for document ingestion and querying with citations
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import tempfile
import os
import logging
from datetime import datetime

from ingestion.pipeline import IngestionPipeline
from retrieval.rag_query import RAGQuerySystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Infrastructure RAG System",
    description="Document ingestion and Q&A system with citations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
rag_system = None


@app.on_event("startup")
async def startup_event():
    """Initialize systems on startup"""
    global rag_system
    logger.info("Initializing RAG system...")
    rag_system = RAGQuerySystem()
    logger.info("✅ RAG system initialized")


# ============================================
# Request/Response Models
# ============================================

class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask the system")
    top_k: int = Field(5, ge=1, le=20, description="Number of relevant chunks to retrieve")
    include_tables: bool = Field(True, description="Include table results")
    include_images: bool = Field(True, description="Include image results")


class Source(BaseModel):
    source_number: int
    document: str
    page: str
    section: str
    type: str
    timestamp: str
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Generated answer with inline citations")
    sources: List[Source] = Field(..., description="List of source documents")
    retrieved_chunks_count: int = Field(..., description="Number of chunks retrieved")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class IngestionStats(BaseModel):
    parent_nodes: int
    child_vectors: int
    tables_processed: int
    text_sections: int
    images_uploaded: int

class IngestionResponse(BaseModel):
    status: str
    message: str
    document_name: str
    stats: IngestionStats
    processing_time_ms: float


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    rag_initialized: bool


# ============================================
# API Endpoints
# ============================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "message": "Infrastructure RAG System API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ingest": "/ingest",
            "query": "/query",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "rag_initialized": rag_system is not None
    }


@app.post("/ingest", response_model=IngestionResponse, tags=["Ingestion"])
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="PDF or DOCX file to ingest")
):
    """
    Ingest a document into the system
    
    Processes the document:
    1. Extracts text, tables, and images using Docling
    2. Splits into parent nodes (by headers)
    3. Creates child vectors (summaries/chunks with embeddings)
    4. Stores in database with metadata and timestamps
    
    Returns ingestion statistics
    """
    start_time = datetime.now()
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Save uploaded file to temporary location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"Processing document: {file.filename}")
        
        # Process document
        pipeline = IngestionPipeline()
        stats = pipeline.ingest_document(tmp_path)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ Ingestion complete: {file.filename}")
        
        return {
            "status": "success",
            "message": "Document ingested successfully",
            "document_name": file.filename,
            "stats": stats,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query_system(request: QueryRequest):
    """
    Query the RAG system with a question
    
    Process:
    1. Embeds the question
    2. Performs vector search on child_vectors
    3. Retrieves parent documents (full content)
    4. Generates answer using Gemini with context
    5. Includes inline citations [Source N, Page X]
    
    Returns answer with source attribution
    """
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    start_time = datetime.now()
    
    try:
        logger.info(f"Processing query: {request.question}")
        
        # Execute RAG query
        response = rag_system.query(
            question=request.question,
            top_k=request.top_k,
            include_tables=request.include_tables,
            include_images=request.include_images
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Format sources
        sources = [Source(**source) for source in response["sources"]]
        
        return {
            "answer": response["answer"],
            "sources": sources,
            "retrieved_chunks_count": len(response["retrieved_chunks"]),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@app.get("/stats", tags=["System"])
async def get_stats():
    """
    Get database statistics
    
    Returns counts of documents, chunks, and types
    """
    try:
        from database.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        
        # Count parent documents
        parents_response = client.client.table("parent_documents").select("id, metadata").execute()
        total_parents = len(parents_response.data)
        
        # Count by type
        type_counts = {}
        for doc in parents_response.data:
            doc_type = doc["metadata"].get("type", "unknown")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Count child vectors
        children_response = client.client.table("child_vectors").select("id").execute()
        total_children = len(children_response.data)
        
        return {
            "status": "success",
            "statistics": {
                "total_parent_documents": total_parents,
                "total_child_vectors": total_children,
                "documents_by_type": type_counts
            }
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
