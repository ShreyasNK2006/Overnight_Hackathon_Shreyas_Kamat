"""
Role Manager
Core business logic for role management and document routing
"""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from database.supabase_client import get_supabase_client
from retrieval.embeddings import get_embedding_model
from stakeholder.models import (
    Role, RoleCreate, RoleUpdate,
    RoleMatch, DocumentRoutingRequest
)

logger = logging.getLogger(__name__)


class RoleManager:
    """
    Manages role operations and document routing using vectorized responsibilities
    """
    
    def __init__(self):
        """Initialize manager with database and embedding model"""
        self.db_client = get_supabase_client()
        self.embedding_model = get_embedding_model()
        logger.info("Role manager initialized")
    
    # ==================== CRUD Operations ====================
    
    def create_role(self, role_data: RoleCreate) -> Role:
        """
        Create a new role and vectorize its responsibilities
        
        Args:
            role_data: Role information including responsibilities
        
        Returns:
            Created role with ID
        """
        logger.info(f"Creating role: {role_data.role_name}")
        
        # 1. Insert role into database
        role_dict = role_data.model_dump()
        response = self.db_client.client.table("roles").insert(role_dict).execute()
        
        if not response.data:
            raise ValueError("Failed to create role")
        
        role = response.data[0]
        role_id = role["id"]
        
        # 2. Vectorize responsibilities
        self._vectorize_responsibilities(
            role_id=role_id,
            responsibilities=role_data.responsibilities
        )
        
        logger.info(f"✅ Created role: {role['role_name']} (ID: {role_id})")
        return Role(**role)
    
    def get_role(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID"""
        response = self.db_client.client.table("roles")\
            .select("*")\
            .eq("id", str(role_id))\
            .execute()
        
        if response.data:
            return Role(**response.data[0])
        return None
    
    def list_roles(
        self, 
        active_only: bool = True,
        business_id: Optional[UUID] = None
    ) -> List[Role]:
        """
        List all roles with optional filtering
        
        Args:
            active_only: Only return active roles
            business_id: Filter by business ID
        
        Returns:
            List of roles
        """
        query = self.db_client.client.table("roles").select("*")
        
        if active_only:
            query = query.eq("is_active", True)
        
        if business_id:
            query = query.eq("business_id", str(business_id))
        
        response = query.order("role_name").execute()
        
        return [Role(**r) for r in response.data]
    
    def update_role(
        self, 
        role_id: UUID, 
        update_data: RoleUpdate
    ) -> Role:
        """
        Update role information
        
        Args:
            role_id: ID of role to update
            update_data: Fields to update
        
        Returns:
            Updated role
        """
        logger.info(f"Updating role: {role_id}")
        
        # Get only non-None fields
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            raise ValueError("No fields to update")
        
        # Update role
        response = self.db_client.client.table("roles")\
            .update(update_dict)\
            .eq("id", str(role_id))\
            .execute()
        
        if not response.data:
            raise ValueError(f"Role not found: {role_id}")
        
        # If responsibilities changed, re-vectorize
        if "responsibilities" in update_dict:
            self._vectorize_responsibilities(
                role_id=role_id,
                responsibilities=update_dict["responsibilities"]
            )
            logger.info("Re-vectorized updated responsibilities")
        
        return Role(**response.data[0])
    
    def delete_role(self, role_id: UUID, soft_delete: bool = True) -> bool:
        """
        Delete role (soft delete by default)
        
        Args:
            role_id: ID of role to delete
            soft_delete: If True, mark as inactive. If False, permanently delete
        
        Returns:
            Success status
        """
        if soft_delete:
            response = self.db_client.client.table("roles")\
                .update({"is_active": False})\
                .eq("id", str(role_id))\
                .execute()
            logger.info(f"Soft deleted role: {role_id}")
        else:
            response = self.db_client.client.table("roles")\
                .delete()\
                .eq("id", str(role_id))\
                .execute()
            logger.info(f"Permanently deleted role: {role_id}")
        
        return bool(response.data)
    
    # ==================== Vectorization ====================
    
    def _vectorize_responsibilities(
        self, 
        role_id: UUID, 
        responsibilities: str
    ) -> str:
        """
        Vectorize role responsibilities for semantic search
        
        Args:
            role_id: ID of role
            responsibilities: Responsibility description text
        
        Returns:
            Vector ID
        """
        logger.debug(f"Vectorizing responsibilities for role: {role_id}")
        
        # 1. Generate embedding
        embedding = self.embedding_model.embed_text(responsibilities)
        
        # 2. Delete existing vectors for this role (for updates)
        self.db_client.client.table("role_vectors")\
            .delete()\
            .eq("role_id", str(role_id))\
            .execute()
        
        # 3. Insert new vector
        vector_data = {
            "role_id": str(role_id),
            "embedding": embedding,
            "responsibilities_text": responsibilities
        }
        
        response = self.db_client.client.table("role_vectors").insert(vector_data).execute()
        
        if not response.data:
            raise ValueError("Failed to vectorize responsibilities")
        
        vector_id = response.data[0]["id"]
        logger.debug(f"Created vector: {vector_id}")
        
        return vector_id
    
    # ==================== Document Routing ====================
    
    def route_document(
        self, 
        document_summary: str,
        business_id: Optional[UUID] = None,
        top_k: int = 3,
        threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        Find the best role(s) for a document using semantic matching
        
        Args:
            document_summary: Summary or content of document to route
            business_id: Filter by business ID
            top_k: Number of matches to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            Dict with matches, best_match, and metadata
        """
        logger.info(f"🔎 Routing document: '{document_summary[:100]}...'")
        
        # 1. Embed the document summary
        query_embedding = self.embedding_model.embed_text(document_summary)
        
        # 2. Vector search against role responsibilities
        params = {
            "query_embedding": query_embedding,
            "match_threshold": threshold,
            "match_count": top_k
        }
        
        if business_id:
            params["filter_business_id"] = str(business_id)
        
        response = self.db_client.client.rpc("match_roles", params).execute()
        
        matches = []
        for match_data in response.data:
            confidence = self._calculate_confidence(match_data["similarity"])
            match = RoleMatch(
                role_id=match_data["role_id"],
                role_name=match_data["role_name"],
                department=match_data["department"],
                responsibilities=match_data["responsibilities"],
                priority=match_data["priority"],
                similarity=match_data["similarity"],
                confidence=confidence
            )
            matches.append(match)
        
        # 3. Determine best match or fallback
        best_match = None
        fallback_used = False
        
        if matches:
            best_match = matches[0]
            logger.info(f"✅ Best match: {best_match.role_name} - {best_match.similarity:.2%} similarity")
        else:
            # Fallback: Get manager role
            logger.warning("⚠️ No matches found. Using fallback to manager role.")
            fallback_match = self._get_manager_role(business_id)
            if fallback_match:
                best_match = fallback_match
                matches = [best_match]
                fallback_used = True
        
        return {
            "matches": matches,
            "best_match": best_match,
            "fallback_used": fallback_used
        }
    
    def _get_manager_role(self, business_id: Optional[UUID] = None) -> Optional[RoleMatch]:
        """Get manager role as fallback"""
        params = {}
        if business_id:
            params["p_business_id"] = str(business_id)
        
        response = self.db_client.client.rpc("get_manager_role", params).execute()
        
        if response.data:
            manager = response.data[0]
            return RoleMatch(
                role_id=manager["role_id"],
                role_name=manager["role_name"],
                department=manager["department"],
                responsibilities=manager["responsibilities"],
                priority=manager["priority"],
                similarity=0.5,  # Fallback score
                confidence="medium"
            )
        
        return None
    
    def _calculate_confidence(self, similarity: float) -> str:
        """Calculate confidence level based on similarity score"""
        if similarity >= 0.8:
            return "high"
        elif similarity >= 0.65:
            return "medium"
        else:
            return "low"
    
    # ==================== Statistics ====================
    
    def get_stats(self, business_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get role statistics"""
        query = self.db_client.client.table("roles").select("*")
        
        if business_id:
            query = query.eq("business_id", str(business_id))
        
        response = query.execute()
        roles_data = response.data
        
        active = [r for r in roles_data if r.get("is_active", True)]
        inactive = [r for r in roles_data if not r.get("is_active", True)]
        
        departments = list(set(r.get("department") for r in roles_data if r.get("department")))
        roles_list = list(set(r.get("role_name") for r in roles_data if r.get("role_name")))
        
        return {
            "total_roles": len(roles_data),
            "active_roles": len(active),
            "inactive_roles": len(inactive),
            "departments": sorted(departments),
            "roles_list": sorted(roles_list)
        }


# Global manager instance
_role_manager: Optional[RoleManager] = None


def get_role_manager() -> RoleManager:
    """Get or create global role manager instance"""
    global _role_manager
    if _role_manager is None:
        _role_manager = RoleManager()
    return _role_manager
