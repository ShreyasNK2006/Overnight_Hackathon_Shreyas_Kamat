"""
Supabase client for database operations and storage management
"""
from supabase import create_client, Client
from typing import Optional, List, Dict, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Wrapper class for Supabase operations including:
    - Database queries (parent_docs, child_vectors)
    - Storage bucket operations (image uploads)
    - Vector similarity search
    """
    
    def __init__(self):
        """Initialize Supabase client"""
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.storage = self.client.storage
        self.bucket_name = settings.SUPABASE_STORAGE_BUCKET
        
        logger.info("Supabase client initialized successfully")
    
    # ==================== Parent Docs Operations ====================
    
    def insert_parent_doc(
        self, 
        content: str, 
        metadata: Dict[str, Any],
        source_created_at: Optional[str] = None
    ) -> str:
        """
        Insert a parent document (full content for LLM reading)
        
        Args:
            content: Full text, table markdown, or image URL wrapper
            metadata: {source, page, type, section_header, uploaded_at}
            source_created_at: Timestamp from source document for conflict resolution
            
        Returns:
            UUID of inserted parent document
        """
        data = {
            "content": content,
            "metadata": metadata
        }
        
        if source_created_at:
            data["source_created_at"] = source_created_at
        
        response = self.client.table("parent_docs").insert(data).execute()
        parent_id = response.data[0]["id"]
        
        logger.info(f"Inserted parent doc: {parent_id}, type: {metadata.get('type')}")
        return parent_id
    
    def get_parent_doc(self, parent_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a parent document by ID
        
        Args:
            parent_id: UUID of parent document
            
        Returns:
            Parent document with content and metadata
        """
        response = self.client.table("parent_docs")\
            .select("*")\
            .eq("id", parent_id)\
            .execute()
        
        if response.data:
            return response.data[0]
        return None
    
    # ==================== Child Vectors Operations ====================
    
    def insert_child_vector(
        self,
        content: str,
        embedding: List[float],
        parent_id: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Insert a child vector (searchable snippet with embedding)
        
        Args:
            content: Text chunk, table summary, or image caption
            embedding: 384-dim vector from all-MiniLM-L6-v2
            parent_id: Reference to parent document
            metadata: Copied from parent for filtering
            
        Returns:
            UUID of inserted child vector
        """
        data = {
            "content": content,
            "embedding": embedding,
            "parent_id": parent_id,
            "metadata": metadata
        }
        
        response = self.client.table("child_vectors").insert(data).execute()
        child_id = response.data[0]["id"]
        
        logger.debug(f"Inserted child vector: {child_id} -> parent: {parent_id}")
        return child_id
    
    def search_similar_vectors(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar child vectors and return parent content
        
        Args:
            query_embedding: 384-dim query vector
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
            
        Returns:
            List of dicts with parent_content, parent_metadata, similarity
        """
        # Use the custom match_parent_docs function
        response = self.client.rpc(
            "match_parent_docs",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k
            }
        ).execute()
        
        results = response.data
        logger.info(f"Found {len(results)} similar documents")
        
        return results
    
    # ==================== Storage Operations ====================
    
    def upload_image(
        self,
        file_path: str,
        file_bytes: bytes,
        content_type: str = "image/png"
    ) -> str:
        """
        Upload image to Supabase storage bucket
        
        Args:
            file_path: Path within bucket (e.g., "doc_id/image_1.png")
            file_bytes: Image binary data
            content_type: MIME type
            
        Returns:
            Public URL of uploaded image
        """
        # Upload to storage
        self.storage.from_(self.bucket_name).upload(
            file_path,
            file_bytes,
            {"content-type": content_type}
        )
        
        # Get public URL
        public_url = self.storage.from_(self.bucket_name).get_public_url(file_path)
        
        logger.info(f"Uploaded image: {file_path}")
        return public_url
    
    def create_storage_bucket(self) -> bool:
        """
        Create storage bucket for images if it doesn't exist
        
        Returns:
            True if created or already exists
        """
        try:
            # Try to create bucket (idempotent - won't fail if exists)
            self.storage.create_bucket(
                self.bucket_name,
                {"public": True}  # Make bucket public for image URLs
            )
            logger.info(f"Storage bucket '{self.bucket_name}' created/verified")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                logger.info(f"Storage bucket '{self.bucket_name}' already exists")
                return True
            logger.error(f"Error creating storage bucket: {e}")
            raise
    
    # ==================== Utility Operations ====================
    
    def delete_all_data(self) -> None:
        """
        Delete all data from parent_docs and child_vectors (for testing)
        WARNING: This is destructive!
        """
        self.client.table("child_vectors").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        self.client.table("parent_docs").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        logger.warning("Deleted all data from database")


# Global client instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """Get or create global Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
