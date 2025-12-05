"""
Document-Role Association Manager
Handles linking documents to roles and retrieving role-specific documents
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class DocumentRoleManager:
    """
    Manages document-role associations for visualization
    """
    
    def __init__(self):
        """Initialize manager with database client"""
        self.db_client = get_supabase_client()
        logger.info("DocumentRole manager initialized")
    
    def assign_document_to_role(
        self,
        role_id: UUID,
        document_name: str,
        document_id: UUID,
        summary: str,
        confidence: float,
        page_number: Optional[int] = None,
        total_pages: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Assign a document to a role after automatic routing
        
        Args:
            role_id: ID of the role
            document_name: Original filename
            document_id: Document ID from parent_documents
            summary: AI-generated summary
            confidence: Routing confidence score (0-1)
            page_number: Specific page if relevant
            total_pages: Total pages in document
            metadata: Additional metadata
        
        Returns:
            Assignment ID
        """
        logger.info(f"Assigning document '{document_name}' to role {role_id}")
        
        assignment_data = {
            "role_id": str(role_id),
            "document_name": document_name,
            "document_id": str(document_id),
            "summary": summary,
            "confidence": confidence,
            "page_number": page_number,
            "total_pages": total_pages,
            "metadata": metadata or {}
        }
        
        response = self.db_client.client.table("role_documents").insert(assignment_data).execute()
        
        if not response.data:
            raise ValueError("Failed to assign document to role")
        
        assignment_id = response.data[0]["id"]
        logger.info(f"✅ Document assigned: {assignment_id}")
        
        return assignment_id
    
    def get_role_documents(
        self,
        role_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all documents assigned to a specific role
        
        Args:
            role_id: ID of the role
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of document assignments
        """
        logger.info(f"Fetching documents for role: {role_id}")
        
        response = self.db_client.client.rpc(
            "get_role_documents",
            {
                "p_role_id": str(role_id),
                "p_limit": limit,
                "p_offset": offset
            }
        ).execute()
        
        return response.data if response.data else []
    
    def get_documents_by_role_name(
        self,
        role_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get all documents for a role by role name
        
        Args:
            role_name: Name of the role
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of document assignments with role info
        """
        logger.info(f"Fetching documents for role name: {role_name}")
        
        # First, get the role
        role_response = self.db_client.client.table("roles")\
            .select("id")\
            .eq("role_name", role_name)\
            .eq("is_active", True)\
            .execute()
        
        if not role_response.data:
            logger.warning(f"Role not found: {role_name}")
            return []
        
        role_id = role_response.data[0]["id"]
        return self.get_role_documents(role_id, limit, offset)
    
    def get_all_role_document_stats(self) -> List[Dict[str, Any]]:
        """
        Get document statistics for all roles
        
        Returns:
            List with role names and document counts
        """
        logger.info("Fetching role document statistics")
        
        response = self.db_client.client.rpc("get_role_document_stats").execute()
        
        return response.data if response.data else []
    
    def get_document_assignments(
        self,
        document_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all document-role assignments
        
        Args:
            document_id: Optional - filter by specific document ID
            limit: Maximum results
        
        Returns:
            List of all assignments or assignments for specific document
        """
        if document_id:
            logger.info(f"Fetching role assignments for document: {document_id}")
            
            response = self.db_client.client.table("role_documents")\
                .select("*, roles(role_name, department)")\
                .eq("document_id", str(document_id))\
                .order("confidence", desc=True)\
                .execute()
        else:
            logger.info("Fetching all document assignments")
            
            response = self.db_client.client.table("role_documents")\
                .select("*, roles(role_name, department)")\
                .order("routed_at", desc=True)\
                .limit(limit)\
                .execute()
        
        return response.data if response.data else []
    
    def search_role_documents(
        self,
        query: str,
        role_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search documents across all roles or specific role
        
        Args:
            query: Search term for document name or summary
            role_id: Optional - filter by specific role
            limit: Maximum results
        
        Returns:
            Matching documents
        """
        logger.info(f"Searching documents: '{query}'" + (f" for role {role_id}" if role_id else ""))
        
        query_builder = self.db_client.client.table("role_documents")\
            .select("*, roles(role_name, department)")
        
        if role_id:
            query_builder = query_builder.eq("role_id", str(role_id))
        
        response = query_builder\
            .or_(f"document_name.ilike.%{query}%,summary.ilike.%{query}%")\
            .order("routed_at", desc=True)\
            .limit(limit)\
            .execute()

        
        return response.data if response.data else []
    
    def get_recent_assignments(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recently assigned documents across all roles
        
        Args:
            limit: Maximum results
        
        Returns:
            Recent document assignments with role info
        """
        logger.info("Fetching recent document assignments")
        
        response = self.db_client.client.table("role_documents")\
            .select("*, roles(role_name, department)")\
            .order("routed_at", desc=True)\
            .limit(limit)\
            .execute()
        
        return response.data if response.data else []
    
    def delete_assignment(self, assignment_id: UUID) -> bool:
        """
        Delete a document-role assignment
        
        Args:
            assignment_id: ID of the assignment
        
        Returns:
            Success status
        """
        logger.info(f"Deleting assignment: {assignment_id}")
        
        response = self.db_client.client.table("role_documents")\
            .delete()\
            .eq("id", str(assignment_id))\
            .execute()
        
        return bool(response.data)
    
    def get_role_summary(self, role_id: UUID) -> Dict[str, Any]:
        """
        Get summary statistics for a specific role
        
        Args:
            role_id: ID of the role
        
        Returns:
            Summary with counts and recent documents
        """
        logger.info(f"Generating summary for role: {role_id}")
        
        # Get role info
        role_response = self.db_client.client.table("roles")\
            .select("*")\
            .eq("id", str(role_id))\
            .execute()
        
        if not role_response.data:
            return {}
        
        role = role_response.data[0]
        
        # Count documents
        count_response = self.db_client.client.table("role_documents")\
            .select("id", count="exact")\
            .eq("role_id", str(role_id))\
            .execute()
        
        document_count = count_response.count or 0
        
        # Get recent documents (last 5)
        recent_docs = self.get_role_documents(role_id, limit=5)
        
        return {
            "role_id": role_id,
            "role_name": role["role_name"],
            "department": role["department"],
            "document_count": document_count,
            "recent_documents": recent_docs,
            "responsibilities": role["responsibilities"]
        }


# Global instance
_document_role_manager: Optional[DocumentRoleManager] = None


def get_document_role_manager() -> DocumentRoleManager:
    """Get or create global document-role manager instance"""
    global _document_role_manager
    if _document_role_manager is None:
        _document_role_manager = DocumentRoleManager()
    return _document_role_manager
