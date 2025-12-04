-- Function for vector similarity search on child_vectors
-- Returns matching child vectors with parent_id for subsequent parent lookup
CREATE OR REPLACE FUNCTION match_vectors(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.3,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    parent_id UUID,
    metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.content,
        c.parent_id,
        c.metadata,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM child_vectors c
    WHERE 1 - (c.embedding <=> query_embedding) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMENT ON FUNCTION match_vectors IS 'Vector similarity search on child_vectors table, returns child vectors with parent_id';
