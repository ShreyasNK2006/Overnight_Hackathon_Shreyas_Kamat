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
from stakeholder.manager import get_role_manager
from stakeholder.document_manager import get_document_role_manager
from stakeholder.models import (
    RoleCreate, RoleUpdate, Role,
    DocumentRoutingRequest, DocumentRoutingResponse, RoleStats, RoleMatch
)

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
role_manager = None
doc_role_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize systems on startup"""
    global rag_system, role_manager, doc_role_manager
    logger.info("Initializing RAG system...")
    rag_system = RAGQuerySystem()
    logger.info("✅ RAG system initialized")
    
    logger.info("Initializing Role Manager...")
    role_manager = get_role_manager()
    logger.info("✅ Role Manager initialized")
    
    logger.info("Initializing Document-Role Manager...")
    doc_role_manager = get_document_role_manager()
    logger.info("✅ Document-Role Manager initialized")


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
        
        # Automatic document routing with smart multi-role assignment
        routing_results = []
        if role_manager and doc_role_manager:
            try:
                # Create document summary from filename and stats
                doc_summary = f"Document: {file.filename}. Contains {stats['text_sections']} text sections, {stats['tables_processed']} tables, {stats['images_uploaded']} images."
                routing = role_manager.route_document(doc_summary, top_k=3, threshold=0.4)
                
                if routing['matches']:
                    matches = routing['matches']
                    
                    # Always assign to top match
                    top_match = matches[0]
                    doc_role_manager.assign_document_to_role(
                        role_id=top_match.role_id,
                        document_name=file.filename,
                        document_id=stats.get('doc_id', stats['source']),
                        summary=doc_summary,
                        confidence=top_match.similarity,
                        total_pages=stats.get('total_pages'),
                        metadata={
                            'fallback_used': routing['fallback_used'],
                            'confidence_level': top_match.confidence,
                            'department': top_match.department,
                            'primary_assignment': True
                        }
                    )
                    routing_results.append({
                        "role": top_match.role_name,
                        "department": top_match.department,
                        "confidence": top_match.confidence,
                        "similarity": top_match.similarity,
                        "primary": True
                    })
                    
                    # If second match is close (within 0.1 similarity), assign to it too
                    if len(matches) > 1:
                        second_match = matches[1]
                        similarity_diff = top_match.similarity - second_match.similarity
                        
                        if similarity_diff < 0.1 and second_match.similarity > 0.5:
                            doc_role_manager.assign_document_to_role(
                                role_id=second_match.role_id,
                                document_name=file.filename,
                                document_id=stats.get('doc_id', stats['source']),
                                summary=doc_summary,
                                confidence=second_match.similarity,
                                total_pages=stats.get('total_pages'),
                                metadata={
                                    'fallback_used': routing['fallback_used'],
                                    'confidence_level': second_match.confidence,
                                    'department': second_match.department,
                                    'primary_assignment': False,
                                    'similarity_diff': similarity_diff
                                }
                            )
                            routing_results.append({
                                "role": second_match.role_name,
                                "department": second_match.department,
                                "confidence": second_match.confidence,
                                "similarity": second_match.similarity,
                                "primary": False,
                                "reason": f"Close similarity (diff: {similarity_diff:.3f})"
                            })
                    
                    logger.info(f"📍 Auto-routed to {len(routing_results)} role(s): {[r['role'] for r in routing_results]}")
            except Exception as e:
                logger.warning(f"Auto-routing/assignment failed: {e}")
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ Ingestion complete: {file.filename}")
        
        return {
            "status": "success",
            "message": "Document ingested successfully",
            "document_name": file.filename,
            "stats": stats,
            "processing_time_ms": processing_time,
            "routed_to": routing_results if routing_results else None
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


# ============================================
# Role Management Endpoints
# ============================================

@app.post("/roles", response_model=Role, tags=["Roles"], status_code=201)
async def create_role(role: RoleCreate):
    """
    Create a new role with vectorized responsibilities
    
    The responsibilities field should be a detailed description of the role's duties.
    This will automatically vectorize the responsibilities for semantic document routing.
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        logger.info(f"Creating role: {role.role_name}")
        created_role = role_manager.create_role(role)
        return created_role
    except Exception as e:
        logger.error(f"Error creating role: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create role: {str(e)}")


@app.get("/roles", response_model=List[Role], tags=["Roles"])
async def list_roles(active_only: bool = True):
    """
    List all roles
    
    Query Parameters:
    - active_only: Only return active roles (default: True)
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        roles = role_manager.list_roles(active_only=active_only)
        return roles
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list roles: {str(e)}")


@app.get("/roles/{role_id}", response_model=Role, tags=["Roles"])
async def get_role(role_id: str):
    """Get a specific role by ID"""
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        from uuid import UUID
        role = role_manager.get_role(UUID(role_id))
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role: {str(e)}")


@app.put("/roles/{role_id}", response_model=Role, tags=["Roles"])
async def update_role(role_id: str, update: RoleUpdate):
    """
    Update role information
    
    If responsibilities are updated, they will be automatically re-vectorized
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        from uuid import UUID
        updated_role = role_manager.update_role(UUID(role_id), update)
        return updated_role
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating role: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")


@app.delete("/roles/{role_id}", tags=["Roles"])
async def delete_role(role_id: str, permanent: bool = False):
    """
    Delete a role
    
    Query Parameters:
    - permanent: If False (default), soft delete (mark inactive). If True, permanently delete.
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        from uuid import UUID
        success = role_manager.delete_role(UUID(role_id), soft_delete=not permanent)
        
        if success:
            return {
                "status": "success",
                "message": f"Role {'deactivated' if not permanent else 'deleted'} successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Role not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete role: {str(e)}")


@app.post("/roles/route", response_model=DocumentRoutingResponse, tags=["Roles"])
async def route_document_to_role(request: DocumentRoutingRequest):
    """
    Find the best role(s) for a document using semantic matching
    
    This endpoint uses vector similarity to match document content against role responsibilities.
    
    Returns:
    - matches: Top matched roles ranked by relevance
    - best_match: The primary recipient (highest similarity)
    - fallback_used: Whether the system fell back to a manager role
    
    Example:
    ```json
    {
        "document_summary": "Safety incident report for construction site",
        "top_k": 3,
        "threshold": 0.6
    }
    ```
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    start_time = datetime.now()
    
    try:
        result = role_manager.route_document(
            document_summary=request.document_summary,
            top_k=request.top_k,
            threshold=request.threshold
        )
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return DocumentRoutingResponse(
            matches=result["matches"],
            best_match=result["best_match"],
            fallback_used=result["fallback_used"],
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error routing document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to route document: {str(e)}")


@app.get("/roles/stats/overview", response_model=RoleStats, tags=["Roles"])
async def get_role_stats():
    """
    Get statistics about roles in the system
    
    Returns counts by department and role types
    """
    if not role_manager:
        raise HTTPException(status_code=503, detail="Role manager not initialized")
    
    try:
        stats = role_manager.get_stats()
        return RoleStats(**stats)
    except Exception as e:
        logger.error(f"Error getting role stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================
# Visualization & Document-Role Association Endpoints
# ============================================

@app.get("/roles/{role_id}/documents", tags=["Visualization"])
async def get_role_documents(
    role_id: str,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all documents assigned to a specific role
    
    Returns documents with page numbers, summaries, and confidence scores
    for visualization purposes.
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        from uuid import UUID
        documents = doc_role_manager.get_role_documents(
            role_id=UUID(role_id),
            limit=limit,
            offset=offset
        )
        return {
            "role_id": role_id,
            "documents": documents,
            "count": len(documents),
            "limit": limit,
            "offset": offset
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error(f"Error getting role documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@app.get("/visualization/stats", tags=["Visualization"])
async def get_visualization_stats():
    """
    Get overall statistics for visualization dashboard
    
    Returns document counts per role, department distribution, etc.
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        stats = doc_role_manager.get_all_role_document_stats()
        return {
            "role_stats": stats,
            "total_assignments": sum(stat['document_count'] for stat in stats),
            "total_roles": len(stats)
        }
    except Exception as e:
        logger.error(f"Error getting visualization stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@app.get("/visualization/recent", tags=["Visualization"])
async def get_recent_assignments(limit: int = 20):
    """
    Get recent document-role assignments
    
    Returns the most recent document routing assignments for activity feed.
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        recent = doc_role_manager.get_recent_assignments(limit=limit)
        return {
            "recent_assignments": recent,
            "count": len(recent)
        }
    except Exception as e:
        logger.error(f"Error getting recent assignments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent assignments: {str(e)}")


@app.get("/visualization/role/{role_name}", tags=["Visualization"])
async def get_role_summary_by_name(role_name: str):
    """
    Get comprehensive summary for a role by name
    
    Includes role details and all assigned documents
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        summary = doc_role_manager.get_role_summary(role_name=role_name)
        if not summary:
            raise HTTPException(status_code=404, detail="Role not found")
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting role summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get role summary: {str(e)}")


# ============================================
# Admin Dashboard Endpoints
# ============================================

@app.get("/admin/dashboard", tags=["Admin"])
async def get_admin_dashboard():
    """
    Complete admin dashboard view with all documents and role assignments
    
    Returns:
    - All roles with document counts
    - All documents with their assigned roles
    - Overall system statistics
    - Recent activity
    """
    if not doc_role_manager or not role_manager:
        raise HTTPException(status_code=503, detail="Managers not initialized")
    
    try:
        # Get all roles
        roles = role_manager.list_roles(active_only=True)
        
        # Get document statistics per role
        role_stats = doc_role_manager.get_all_role_document_stats()
        
        # Get all document assignments (grouped by document)
        all_assignments = doc_role_manager.get_document_assignments()
        
        # Get recent activity
        recent = doc_role_manager.get_recent_assignments(limit=10)
        
        # Calculate overall stats
        total_documents = len(set(a['document_id'] for a in all_assignments))
        total_assignments = len(all_assignments)
        total_roles = len(roles)
        roles_with_docs = len([s for s in role_stats if s['document_count'] > 0])
        
        return {
            "overview": {
                "total_documents": total_documents,
                "total_assignments": total_assignments,
                "total_roles": total_roles,
                "active_roles_with_documents": roles_with_docs,
                "unassigned_roles": total_roles - roles_with_docs
            },
            "roles": [
                {
                    "id": str(role.id),
                    "role_name": role.role_name,
                    "department": role.department,
                    "responsibilities": role.responsibilities,
                    "priority": role.priority,
                    "document_count": next((s['document_count'] for s in role_stats if s['role_id'] == role.id), 0)
                }
                for role in roles
            ],
            "all_documents": all_assignments,
            "recent_activity": recent,
            "role_distribution": role_stats
        }
    except Exception as e:
        logger.error(f"Error getting admin dashboard: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard: {str(e)}")


@app.get("/admin/documents", tags=["Admin"])
async def get_all_documents(
    search: Optional[str] = None,
    role_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all documents with filtering and search
    
    Query Parameters:
    - search: Search in document names or summaries
    - role_id: Filter by specific role
    - limit: Max results to return
    - offset: Pagination offset
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        if search:
            # Search across all documents
            results = doc_role_manager.search_role_documents(
                query=search,
                role_id=role_id,
                limit=limit
            )
        elif role_id:
            # Filter by role
            from uuid import UUID
            results = doc_role_manager.get_role_documents(
                role_id=UUID(role_id),
                limit=limit,
                offset=offset
            )
        else:
            # Get all documents
            results = doc_role_manager.get_document_assignments(limit=limit)
        
        return {
            "documents": results,
            "count": len(results),
            "filters": {
                "search": search,
                "role_id": role_id
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role ID format")
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@app.get("/admin/documents/{document_id}/assignments", tags=["Admin"])
async def get_document_assignments(document_id: str):
    """
    Get all role assignments for a specific document
    
    Shows which roles have been assigned this document
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        assignments = doc_role_manager.get_document_assignments(document_id=document_id)
        
        if not assignments:
            raise HTTPException(status_code=404, detail="Document not found or has no assignments")
        
        return {
            "document_id": document_id,
            "assignments": assignments,
            "total_roles_assigned": len(assignments)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document assignments: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get assignments: {str(e)}")


@app.get("/admin/analytics", tags=["Admin"])
async def get_admin_analytics():
    """
    Get analytics data for admin visualization
    
    Returns:
    - Document distribution by role
    - Document distribution by department
    - Confidence score statistics
    - Temporal trends (documents over time)
    """
    if not doc_role_manager or not role_manager:
        raise HTTPException(status_code=503, detail="Managers not initialized")
    
    try:
        # Get all roles
        roles = role_manager.list_roles(active_only=True)
        
        # Get all assignments
        assignments = doc_role_manager.get_document_assignments()
        
        # Calculate analytics
        
        # 1. Documents by role
        role_distribution = {}
        for role in roles:
            role_docs = [a for a in assignments if a.get('role_id') == str(role.id)]
            role_distribution[role.role_name] = len(role_docs)
        
        # 2. Documents by department
        dept_distribution = {}
        for role in roles:
            role_docs = [a for a in assignments if a.get('role_id') == str(role.id)]
            dept_distribution[role.department] = dept_distribution.get(role.department, 0) + len(role_docs)
        
        # 3. Confidence score statistics
        confidences = [a.get('confidence', 0) for a in assignments if a.get('confidence')]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        high_confidence = len([c for c in confidences if c >= 0.8])
        medium_confidence = len([c for c in confidences if 0.6 <= c < 0.8])
        low_confidence = len([c for c in confidences if c < 0.6])
        
        # 4. Recent trends (last 7 days)
        from datetime import datetime, timedelta
        today = datetime.now()
        last_7_days = {}
        for i in range(7):
            date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
            last_7_days[date] = 0
        
        for assignment in assignments:
            if assignment.get('routed_at'):
                date_str = assignment['routed_at'][:10]  # Get YYYY-MM-DD
                if date_str in last_7_days:
                    last_7_days[date_str] += 1
        
        return {
            "role_distribution": [
                {"role": role, "count": count}
                for role, count in sorted(role_distribution.items(), key=lambda x: x[1], reverse=True)
            ],
            "department_distribution": [
                {"department": dept, "count": count}
                for dept, count in sorted(dept_distribution.items(), key=lambda x: x[1], reverse=True)
            ],
            "confidence_stats": {
                "average": round(avg_confidence, 3),
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
                "total": len(confidences)
            },
            "temporal_trends": [
                {"date": date, "count": count}
                for date, count in sorted(last_7_days.items())
            ],
            "total_documents": len(set(a.get('document_id') for a in assignments if a.get('document_id'))),
            "total_assignments": len(assignments)
        }
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@app.delete("/admin/assignments/{assignment_id}", tags=["Admin"])
async def delete_assignment(assignment_id: str):
    """
    Delete a document-role assignment
    
    Admin endpoint to remove incorrect assignments
    """
    if not doc_role_manager:
        raise HTTPException(status_code=503, detail="Document-Role manager not initialized")
    
    try:
        from uuid import UUID
        success = doc_role_manager.delete_assignment(UUID(assignment_id))
        
        if success:
            return {
                "status": "success",
                "message": "Assignment deleted successfully",
                "assignment_id": assignment_id
            }
        else:
            raise HTTPException(status_code=404, detail="Assignment not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid assignment ID format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assignment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete assignment: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
