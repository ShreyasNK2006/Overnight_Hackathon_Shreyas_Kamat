"""
Configuration settings for the Infrastructure RAG System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_STORAGE_BUCKET: str = "project_images"
    
    # Google Gemini Configuration
    GOOGLE_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash-latest"
    
    # Embeddings Configuration
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    
    # Chunking Configuration
    TEXT_CHUNK_SIZE: int = 400
    TEXT_CHUNK_OVERLAP: int = 50
    
    # Retrieval Configuration
    TOP_K_RESULTS: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
