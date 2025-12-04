"""
Embedding Model for Vector Search
Uses all-MiniLM-L6-v2 for local, free embeddings
"""
import logging
from typing import List, Union
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Wrapper for HuggingFace embedding model
    Uses all-MiniLM-L6-v2 (384 dimensions, CPU-compatible, free)
    """
    
    def __init__(self):
        """Initialize embedding model"""
        self.model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info(f"Embedding model initialized: {settings.EMBEDDING_MODEL}")
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
        
        Returns:
            384-dimensional embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * settings.EMBEDDING_DIM
        
        embedding = self.model.embed_query(text)
        return embedding
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of 384-dimensional embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        
        if not valid_texts:
            logger.warning("No valid texts provided for embedding")
            return [[0.0] * settings.EMBEDDING_DIM] * len(texts)
        
        embeddings = self.model.embed_documents(valid_texts)
        return embeddings


# Global embedding model instance
_embedding_model = None


def get_embedding_model() -> EmbeddingModel:
    """Get or create global embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = EmbeddingModel()
    return _embedding_model
