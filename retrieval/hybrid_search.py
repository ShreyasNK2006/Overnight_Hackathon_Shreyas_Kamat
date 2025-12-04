"""
Retrieval System - Hybrid Search
Combines vector search (child vectors) with parent document lookup
"""
import logging
from typing import List, Dict, Any, Optional
from retrieval.embeddings import EmbeddingModel
from database.supabase_client import SupabaseClient
from config.settings import settings

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid search combining:
    1. Vector search on child_vectors (summaries/chunks)
    2. Parent document retrieval (full content for LLM)
    """
    
    def __init__(self):
        """Initialize retriever with embeddings and database"""
        self.embedding_model = EmbeddingModel()
        self.db_client = SupabaseClient()
        logger.info("Hybrid retriever initialized")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using hybrid approach
        
        Args:
            query: User's search query
            top_k: Number of results to return
            similarity_threshold: Minimum cosine similarity (0-1)
            filters: Optional metadata filters (e.g., {"type": "table"})
        
        Returns:
            List of results with:
            - parent_id: ID of parent document
            - parent_content: Full content for LLM
            - child_content: Matching summary/chunk
            - similarity_score: Cosine similarity
            - metadata: Document metadata
        """
        logger.info(f"Searching for: '{query}' (top_k={top_k})")
        
        # Step 1: Embed the query
        query_embedding = self.embedding_model.embed_text(query)
        
        # Step 2: Vector search on child_vectors
        child_matches = self._vector_search(
            query_embedding=query_embedding,
            top_k=top_k * 2,  # Get more candidates
            similarity_threshold=similarity_threshold,
            filters=filters
        )
        
        if not child_matches:
            logger.warning("No matches found")
            return []
        
        # Step 3: Retrieve parent documents
        results = self._fetch_parent_documents(child_matches)
        
        # Step 4: Deduplicate by parent_id and keep top_k
        results = self._deduplicate_results(results, top_k)
        
        logger.info(f"Returning {len(results)} results")
        return results
    
    def _vector_search(
        self,
        query_embedding: List[float],
        top_k: int,
        similarity_threshold: float,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search on child_vectors
        
        Args:
            query_embedding: Embedded query vector
            top_k: Number of candidates to retrieve
            similarity_threshold: Minimum similarity score
            filters: Optional metadata filters
        
        Returns:
            List of matching child vectors with parent_id and similarity
        """
        try:
            # Build query
            query = self.db_client.client.rpc(
                'match_vectors',
                {
                    'query_embedding': query_embedding,
                    'match_count': top_k,
                    'match_threshold': similarity_threshold
                }
            )
            
            # Apply filters if provided
            if filters:
                for key, value in filters.items():
                    query = query.eq(f"metadata->>{key}", value)
            
            response = query.execute()
            
            logger.debug(f"Vector search found {len(response.data)} candidates")
            return response.data
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _fetch_parent_documents(
        self,
        child_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Fetch parent documents for matching child vectors
        
        Args:
            child_matches: List of matching child vectors
        
        Returns:
            List of results with both child and parent content
        """
        results = []
        
        for child in child_matches:
            try:
                parent_id = child.get('parent_id')
                
                # Fetch parent document
                parent_response = self.db_client.client.table("parent_documents")\
                    .select("*")\
                    .eq("id", parent_id)\
                    .execute()
                
                if not parent_response.data:
                    logger.warning(f"Parent document not found: {parent_id}")
                    continue
                
                parent = parent_response.data[0]
                
                # Combine child and parent info
                result = {
                    "parent_id": parent_id,
                    "parent_content": parent["content"],
                    "child_content": child.get("content", ""),
                    "similarity_score": child.get("similarity", 0.0),
                    "metadata": parent.get("metadata", {}),
                    "type": parent.get("metadata", {}).get("type", "unknown"),
                    "source": parent.get("metadata", {}).get("source", "unknown"),
                    "section": parent.get("metadata", {}).get("section_header", "N/A")
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error fetching parent document: {e}")
                continue
        
        return results
    
    def _deduplicate_results(
        self,
        results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Remove duplicate parents, keeping the highest scoring match per parent
        
        Args:
            results: List of results
            top_k: Number of unique results to return
        
        Returns:
            Deduplicated results sorted by similarity
        """
        # Group by parent_id, keep highest score
        seen_parents = {}
        
        for result in results:
            parent_id = result["parent_id"]
            score = result["similarity_score"]
            
            if parent_id not in seen_parents or score > seen_parents[parent_id]["similarity_score"]:
                seen_parents[parent_id] = result
        
        # Sort by similarity and take top_k
        deduplicated = sorted(
            seen_parents.values(),
            key=lambda x: x["similarity_score"],
            reverse=True
        )[:top_k]
        
        return deduplicated
    
    def search_by_type(
        self,
        query: str,
        doc_type: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for documents of a specific type
        
        Args:
            query: Search query
            doc_type: Type filter ("text", "table", or "image")
            top_k: Number of results
        
        Returns:
            Filtered results
        """
        return self.search(
            query=query,
            top_k=top_k,
            filters={"type": doc_type}
        )
    
    def search_tables(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Convenience method to search only tables"""
        return self.search_by_type(query, "table", top_k)
    
    def search_images(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Convenience method to search only images"""
        return self.search_by_type(query, "image", top_k)
    
    def search_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Convenience method to search only text sections"""
        return self.search_by_type(query, "text", top_k)
