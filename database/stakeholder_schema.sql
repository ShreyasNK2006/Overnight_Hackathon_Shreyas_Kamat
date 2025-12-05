-- ============================================
-- Stakeholder Management Schema (Role-Based Routing)
-- Vectorized Responsibility Routing System
-- ============================================

-- ============================================
-- Table 1: roles (Role Definitions)
-- ============================================
-- Stores role information with responsibilities for routing
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(255) NOT NULL UNIQUE,      -- e.g., "Safety Officer", "Finance Manager"
    department VARCHAR(255),                      -- e.g., "Safety", "Finance", "Engineering"
    responsibilities TEXT NOT NULL,               -- Natural language description of what this role handles
    priority INT DEFAULT 1,                       -- For tie-breaking (higher = more important)
    business_id UUID,                             -- For multi-tenant support (optional)
    is_active BOOLEAN DEFAULT TRUE,               -- For soft deletion
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table 2: role_vectors (Routing Engine)
-- ============================================
-- Stores vectorized responsibilities for semantic search
CREATE TABLE role_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    embedding vector(384),                        -- 384 dimensions for all-MiniLM-L6-v2
    responsibilities_text TEXT NOT NULL,          -- Copy of responsibilities for reference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Vector similarity search index for role routing
CREATE INDEX idx_role_embedding ON role_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- Index for role lookups
CREATE INDEX idx_role_id ON role_vectors(role_id);

-- Index for active roles filtering
CREATE INDEX idx_role_active ON roles(is_active) WHERE is_active = TRUE;

-- Index for business_id filtering (multi-tenant support)
CREATE INDEX idx_role_business ON roles(business_id) WHERE business_id IS NOT NULL;

-- Index for role name lookups
CREATE INDEX idx_role_name ON roles(role_name);

-- ============================================
-- Helper Functions
-- ============================================

-- Function to find the best role for a document
CREATE OR REPLACE FUNCTION match_roles(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.6,
    match_count int DEFAULT 5,
    filter_business_id UUID DEFAULT NULL
)
RETURNS TABLE (
    role_id UUID,
    role_name VARCHAR,
    department VARCHAR,
    responsibilities TEXT,
    priority INT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id AS role_id,
        r.role_name,
        r.department,
        r.responsibilities,
        r.priority,
        1 - (rv.embedding <=> query_embedding) AS similarity
    FROM role_vectors rv
    JOIN roles r ON rv.role_id = r.id
    WHERE r.is_active = TRUE
        AND 1 - (rv.embedding <=> query_embedding) > match_threshold
        AND (filter_business_id IS NULL OR r.business_id = filter_business_id)
    ORDER BY 
        rv.embedding <=> query_embedding,
        r.priority DESC
    LIMIT match_count;
END;
$$;

-- Function to get project manager role (fallback)
CREATE OR REPLACE FUNCTION get_manager_role(
    p_business_id UUID DEFAULT NULL
)
RETURNS TABLE (
    role_id UUID,
    role_name VARCHAR,
    department VARCHAR,
    responsibilities TEXT,
    priority INT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id AS role_id,
        r.role_name,
        r.department,
        r.responsibilities,
        r.priority
    FROM roles r
    WHERE r.is_active = TRUE
        AND (r.role_name ILIKE '%manager%' OR r.role_name ILIKE '%supervisor%' OR r.role_name ILIKE '%director%')
        AND (p_business_id IS NULL OR r.business_id = p_business_id)
    ORDER BY 
        CASE 
            WHEN r.role_name ILIKE '%project manager%' THEN 1
            WHEN r.role_name ILIKE '%general manager%' THEN 2
            WHEN r.role_name ILIKE '%manager%' THEN 3
            ELSE 4
        END,
        r.priority DESC
    LIMIT 1;
END;
$$;

-- ============================================
-- Trigger to auto-update updated_at
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_roles_updated_at
    BEFORE UPDATE ON roles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_role_vectors_updated_at
    BEFORE UPDATE ON role_vectors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE roles IS 'Stores role definitions with natural language responsibility descriptions';
COMMENT ON TABLE role_vectors IS 'Stores vectorized responsibilities for semantic document routing';
-- ============================================
-- Sample Data (Optional - Remove in Production)
-- ============================================

-- Example roles with clear, non-overlapping responsibilities
INSERT INTO roles (role_name, department, responsibilities, priority) VALUES
(
    'Safety Officer',
    'Safety & Compliance',
    'Handles all safety-related matters including structural inspections, site accidents, hazard assessments, safety equipment compliance, worker injury reports, and emergency response procedures. Ensures OSHA compliance and conducts safety training sessions.',
    10
),
(
    'Finance Manager',
    'Finance & Accounting',
    'Manages all financial operations including invoices, vendor payments, procurement orders, budget tracking, expense reports, payroll processing, and financial reconciliation. Handles cement orders, material purchases, and supplier contracts.',
    9
),
(
    'Engineering Lead',
    'Engineering & Design',
    'Oversees engineering projects including blueprint reviews, structural design approvals, load calculations, material specifications, CAD drawings, architectural plans, and technical feasibility studies. Coordinates with architects and reviews construction drawings.',
    8
),
(
    'Project Manager',
    'Project Management',
    'Coordinates overall project execution including timelines, resource allocation, team coordination, client communication, progress reports, milestone tracking, and general project oversight. Serves as the primary point of contact for all project-related matters.',
    10
),
(
    'Quality Control Inspector',
    'Quality Assurance',
    'Ensures quality standards are met including material testing, concrete strength verification, weld inspections, construction defect identification, compliance testing, and quality documentation. Performs site inspections and certifies work completion.',
    7
);

-- ============================================
-- Important Notes
-- ============================================
-- 1. After inserting stakeholders, you MUST vectorize their responsibilities
-- ============================================
-- Table 3: role_documents (Document-Role Associations)
-- ============================================
-- Stores which documents are assigned to which roles with metadata
CREATE TABLE role_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    document_name VARCHAR(500) NOT NULL,          -- Original filename
    document_id UUID NOT NULL,                     -- Links to parent_documents metadata->doc_id
    page_number INT,                               -- Specific page if relevant
    total_pages INT,                               -- Total pages in document
    summary TEXT,                                  -- AI-generated summary of document
    confidence FLOAT,                              -- Routing confidence score (0-1)
    routed_at TIMESTAMPTZ DEFAULT NOW(),          -- When document was assigned
    metadata JSONB,                                -- Additional metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for role lookups (find all documents for a role)
CREATE INDEX idx_role_docs_role ON role_documents(role_id);

-- Index for document lookups (find which roles have this document)
CREATE INDEX idx_role_docs_document ON role_documents(document_id);

-- Index for recent documents
CREATE INDEX idx_role_docs_routed_at ON role_documents(routed_at DESC);

-- Composite index for role + date queries
CREATE INDEX idx_role_docs_role_date ON role_documents(role_id, routed_at DESC);

COMMENT ON TABLE role_documents IS 'Associates documents with roles after automatic routing, storing page numbers and summaries';
COMMENT ON COLUMN role_documents.summary IS 'AI-generated summary of what this document contains';
COMMENT ON COLUMN role_documents.confidence IS 'Routing confidence score from semantic matching (0-1)';

-- ============================================
-- Helper Functions for Document Management
-- ============================================

-- Function to get all documents for a specific role
CREATE OR REPLACE FUNCTION get_role_documents(
    p_role_id UUID,
    p_limit INT DEFAULT 100,
    p_offset INT DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    document_name VARCHAR,
    document_id UUID,
    page_number INT,
    total_pages INT,
    summary TEXT,
    confidence FLOAT,
    routed_at TIMESTAMPTZ,
    metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        rd.id,
        rd.document_name,
        rd.document_id,
        rd.page_number,
        rd.total_pages,
        rd.summary,
        rd.confidence,
        rd.routed_at,
        rd.metadata
    FROM role_documents rd
    WHERE rd.role_id = p_role_id
    ORDER BY rd.routed_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

-- Function to get document distribution across roles
CREATE OR REPLACE FUNCTION get_role_document_stats()
RETURNS TABLE (
    role_id UUID,
    role_name VARCHAR,
    department VARCHAR,
    document_count BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        r.id AS role_id,
        r.role_name,
        r.department,
        COUNT(rd.id) AS document_count
    FROM roles r
    LEFT JOIN role_documents rd ON r.id = rd.role_id
    WHERE r.is_active = TRUE
    GROUP BY r.id, r.role_name, r.department
    ORDER BY document_count DESC, r.role_name;
END;
$$;

COMMENT ON FUNCTION get_role_documents IS 'Retrieves all documents assigned to a specific role with pagination';
COMMENT ON FUNCTION get_role_document_stats IS 'Returns document count statistics for all roles';

-- ============================================
-- Important Notes
-- ============================================
-- 1. After inserting roles, you MUST vectorize their responsibilities
--    using the Python script (initialize_stakeholders.py)
-- 2. The match_roles function uses cosine similarity (0-1 scale)
-- 3. Threshold of 0.6 is recommended for accurate routing
-- 4. For multi-tenant systems, always pass business_id
-- 5. Keep responsibilities descriptive and keyword-rich for better matching
-- 6. Priority field is used for tie-breaking when similarities are equal
-- 7. Documents are routed to ROLES, not specific individuals
-- 8. role_documents table tracks all document assignments for visualization