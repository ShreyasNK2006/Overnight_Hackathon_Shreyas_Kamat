-- ============================================
-- Stakeholder Management Schema
-- Vectorized Responsibility Routing System
-- ============================================

-- ============================================
-- Table 1: stakeholders (Core Information)
-- ============================================
-- Stores stakeholder/employee information with their responsibilities
CREATE TABLE stakeholders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(255) NOT NULL,                  -- e.g., "Safety Officer", "Finance Manager"
    department VARCHAR(255),                      -- e.g., "Safety", "Finance", "Engineering"
    phone VARCHAR(50),
    responsibilities TEXT NOT NULL,               -- Natural language description of what they handle
    business_id UUID,                             -- For multi-tenant support (optional)
    is_active BOOLEAN DEFAULT TRUE,               -- For soft deletion
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Table 2: stakeholder_vectors (Routing Engine)
-- ============================================
-- Stores vectorized responsibilities for semantic search
CREATE TABLE stakeholder_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stakeholder_id UUID NOT NULL REFERENCES stakeholders(id) ON DELETE CASCADE,
    embedding vector(384),                        -- 384 dimensions for all-MiniLM-L6-v2
    responsibilities_text TEXT NOT NULL,          -- Copy of responsibilities for reference
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- Indexes for Performance
-- ============================================

-- Vector similarity search index for stakeholder routing
CREATE INDEX idx_stakeholder_embedding ON stakeholder_vectors 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- Index for stakeholder lookups
CREATE INDEX idx_stakeholder_id ON stakeholder_vectors(stakeholder_id);

-- Index for active stakeholders filtering
CREATE INDEX idx_stakeholder_active ON stakeholders(is_active) WHERE is_active = TRUE;

-- Index for business_id filtering (multi-tenant support)
CREATE INDEX idx_stakeholder_business ON stakeholders(business_id) WHERE business_id IS NOT NULL;

-- Index for email lookups
CREATE INDEX idx_stakeholder_email ON stakeholders(email);

-- ============================================
-- Helper Functions
-- ============================================

-- Function to find the best stakeholder for a document
CREATE OR REPLACE FUNCTION match_stakeholders(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.6,
    match_count int DEFAULT 5,
    filter_business_id UUID DEFAULT NULL
)
RETURNS TABLE (
    stakeholder_id UUID,
    name VARCHAR,
    email VARCHAR,
    role VARCHAR,
    department VARCHAR,
    phone VARCHAR,
    responsibilities TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS stakeholder_id,
        s.name,
        s.email,
        s.role,
        s.department,
        s.phone,
        s.responsibilities,
        1 - (sv.embedding <=> query_embedding) AS similarity
    FROM stakeholder_vectors sv
    JOIN stakeholders s ON sv.stakeholder_id = s.id
    WHERE s.is_active = TRUE
        AND 1 - (sv.embedding <=> query_embedding) > match_threshold
        AND (filter_business_id IS NULL OR s.business_id = filter_business_id)
    ORDER BY sv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get project manager (fallback)
CREATE OR REPLACE FUNCTION get_project_manager(
    p_business_id UUID DEFAULT NULL
)
RETURNS TABLE (
    stakeholder_id UUID,
    name VARCHAR,
    email VARCHAR,
    role VARCHAR,
    department VARCHAR,
    phone VARCHAR,
    responsibilities TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id AS stakeholder_id,
        s.name,
        s.email,
        s.role,
        s.department,
        s.phone,
        s.responsibilities
    FROM stakeholders s
    WHERE s.is_active = TRUE
        AND (s.role ILIKE '%manager%' OR s.role ILIKE '%supervisor%' OR s.role ILIKE '%director%')
        AND (p_business_id IS NULL OR s.business_id = p_business_id)
    ORDER BY 
        CASE 
            WHEN s.role ILIKE '%project manager%' THEN 1
            WHEN s.role ILIKE '%general manager%' THEN 2
            WHEN s.role ILIKE '%manager%' THEN 3
            ELSE 4
        END
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

CREATE TRIGGER update_stakeholders_updated_at
    BEFORE UPDATE ON stakeholders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stakeholder_vectors_updated_at
    BEFORE UPDATE ON stakeholder_vectors
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE stakeholders IS 'Stores stakeholder/employee information with natural language responsibility descriptions';
COMMENT ON TABLE stakeholder_vectors IS 'Stores vectorized responsibilities for semantic document routing';
COMMENT ON COLUMN stakeholders.responsibilities IS 'Natural language description of what this person handles (e.g., "I handle structural inspections, cracked beams, and site accidents")';
COMMENT ON COLUMN stakeholder_vectors.embedding IS '384-dimensional vector from all-MiniLM-L6-v2 model for semantic matching';
COMMENT ON FUNCTION match_stakeholders IS 'Finds the best stakeholder for a document using vector similarity on responsibilities';
COMMENT ON FUNCTION get_project_manager IS 'Returns the project manager as a fallback when no stakeholder matches';

-- ============================================
-- Sample Data (Optional - Remove in Production)
-- ============================================

-- Example stakeholders with clear, non-overlapping responsibilities
INSERT INTO stakeholders (name, email, role, department, responsibilities) VALUES
(
    'Bob Harrison',
    'bob.harrison@company.com',
    'Safety Officer',
    'Safety & Compliance',
    'I handle all safety-related matters including structural inspections, site accidents, hazard assessments, safety equipment compliance, worker injury reports, and emergency response procedures. I ensure OSHA compliance and conduct safety training sessions.'
),
(
    'Alice Chen',
    'alice.chen@company.com',
    'Finance Manager',
    'Finance & Accounting',
    'I manage all financial operations including invoices, vendor payments, procurement orders, budget tracking, expense reports, payroll processing, and financial reconciliation. I handle cement orders, material purchases, and supplier contracts.'
),
(
    'Carlos Rodriguez',
    'carlos.rodriguez@company.com',
    'Engineering Lead',
    'Engineering & Design',
    'I oversee engineering projects including blueprint reviews, structural design approvals, load calculations, material specifications, CAD drawings, architectural plans, and technical feasibility studies. I coordinate with architects and review construction drawings.'
),
(
    'Diana Foster',
    'diana.foster@company.com',
    'Project Manager',
    'Project Management',
    'I coordinate overall project execution including timelines, resource allocation, team coordination, client communication, progress reports, milestone tracking, and general project oversight. I serve as the primary point of contact for all project-related matters.'
),
(
    'Edward Kim',
    'edward.kim@company.com',
    'Quality Control Inspector',
    'Quality Assurance',
    'I ensure quality standards are met including material testing, concrete strength verification, weld inspections, construction defect identification, compliance testing, and quality documentation. I perform site inspections and certify work completion.'
);

-- ============================================
-- Important Notes
-- ============================================
-- 1. After inserting stakeholders, you MUST vectorize their responsibilities
--    using the Python script (stakeholder_manager.py)
-- 2. The match_stakeholders function uses cosine similarity (0-1 scale)
-- 3. Threshold of 0.6 is recommended for accurate routing
-- 4. For multi-tenant systems, always pass business_id
-- 5. Keep responsibilities descriptive and keyword-rich for better matching
