-- ============================================
-- Supabase Database Schema for Infrastructure RAG
-- ============================================

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- Table 1: parent_documents (For Reading & Context)
-- ============================================
-- This table stores the full content that the LLM will read
-- Includes complete text sections, full tables, and image URL wrappers
CREATE TABLE parent_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,              -- Markdown Text, Table, or "![Image](url)"
    metadata JSONB NOT NULL,            -- {source, page, type, section_header, uploaded_at}
    source_created_at TIMESTAMPTZ,      -- For temporal conflict resolution
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table 2: child_vectors (For Searching)
-- ============================================
-- This table stores small, searchable snippets with embeddings
-- Includes text chunks, table summaries, and image captions
CREATE TABLE child_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,              -- Text snippet, table summary, or image caption
    embedding vector(384),              -- 384 dimensions for all-MiniLM-L6-v2
    parent_id UUID NOT NULL REFERENCES parent_documents(id) ON DELETE CASCADE,
    metadata JSONB NOT NULL,            -- Copies parent metadata for filtering
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Vector similarity search index using IVFFlat
-- IVFFlat is faster for large datasets with good recall
CREATE INDEX idx_child_embedding ON child_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for fast parent lookups from child nodes
CREATE INDEX idx_parent_id ON child_vectors(parent_id);

-- GIN index for metadata filtering (e.g., by source, page, type)
CREATE INDEX idx_parent_metadata ON parent_documents USING gin(metadata);
CREATE INDEX idx_child_metadata ON child_vectors USING gin(metadata);

-- Index for temporal queries
CREATE INDEX idx_source_created_at ON parent_documents(source_created_at);

-- ============================================
-- Helper Functions
-- ============================================

-- Function to search for similar vectors and return parent content
CREATE OR REPLACE FUNCTION match_parent_docs(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    parent_id UUID,
    parent_content TEXT,
    parent_metadata JSONB,
    child_content TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS parent_id,
        p.content AS parent_content,
        p.metadata AS parent_metadata,
        c.content AS child_content,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM child_vectors c
    JOIN parent_documents p ON c.parent_id = p.id
    WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE parent_documents IS 'Stores full content for LLM reading (text sections, complete tables, image URLs)';
COMMENT ON TABLE child_vectors IS 'Stores searchable snippets with embeddings (text chunks, table summaries, image captions)';
COMMENT ON COLUMN parent_documents.metadata IS 'JSON structure: {source, page, type, section_header, uploaded_at}';
COMMENT ON COLUMN child_vectors.embedding IS '384-dimensional vector from all-MiniLM-L6-v2 model';
COMMENT ON FUNCTION match_parent_docs IS 'Searches child vectors and returns parent content with similarity scores';
