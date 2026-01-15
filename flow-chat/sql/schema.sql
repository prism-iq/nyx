-- ============================================================================
-- CIPHER COGNITIVE SYSTEM - PostgreSQL Schema
-- Knowledge synthesis across 6 domains: Math, Neuro, Bio, Psych, Med, Art
-- ============================================================================

-- Create synthesis schema
CREATE SCHEMA IF NOT EXISTS synthesis;

-- ============================================================================
-- DOMAINS
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.domains (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO synthesis.domains (name, description, priority) VALUES
    ('mathematics', 'Pure and applied mathematics, logic, computation', 1),
    ('neurosciences', 'Brain, cognition, neural systems', 1),
    ('biology', 'Life sciences, genetics, evolution', 1),
    ('psychology', 'Mind, behavior, cognition', 1),
    ('medicine', 'Clinical science, pathology, therapeutics', 1),
    ('art', 'Aesthetics, creativity, perception', 1)
ON CONFLICT (name) DO NOTHING;

-- ============================================================================
-- SOURCES - Academic papers and their metadata
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.sources (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,  -- DOI, arXiv ID, PMID, etc.
    source_type VARCHAR(50) NOT NULL,           -- openalex, arxiv, pubmed, semantic_scholar
    title TEXT NOT NULL,
    authors JSONB,                              -- [{name, affiliation, orcid}]
    abstract TEXT,
    publication_date DATE,
    journal VARCHAR(500),
    citation_count INTEGER DEFAULT 0,
    domains INTEGER[],                          -- References to synthesis.domains
    url TEXT,
    pdf_url TEXT,
    metadata JSONB,                             -- Additional source-specific data
    quality_score FLOAT,                        -- Computed quality score
    entropy_hash VARCHAR(128),                  -- SHAKE256 hash for dedup/quality
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sources_external_id ON synthesis.sources(external_id);
CREATE INDEX IF NOT EXISTS idx_sources_type ON synthesis.sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_domains ON synthesis.sources USING GIN(domains);
CREATE INDEX IF NOT EXISTS idx_sources_processed ON synthesis.sources(processed);

-- ============================================================================
-- CLAIMS - Extracted assertions from papers
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.claims (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES synthesis.sources(id) ON DELETE CASCADE,
    claim_text TEXT NOT NULL,
    claim_type VARCHAR(50),                     -- hypothesis, finding, method, definition
    confidence FLOAT DEFAULT 0.5,               -- 0-1 confidence in claim
    evidence_strength VARCHAR(20),              -- weak, moderate, strong, definitive
    domains INTEGER[],                          -- Domains this claim relates to
    entities JSONB,                             -- Extracted entities/concepts
    methodology TEXT,                           -- How was this established?
    sample_size INTEGER,                        -- If empirical
    p_value FLOAT,                              -- Statistical significance
    effect_size FLOAT,                          -- Effect magnitude
    replication_status VARCHAR(30),             -- unreplicated, replicated, failed_replication
    entropy_hash VARCHAR(128),                  -- SHAKE256 for similarity detection
    embedding VECTOR(1536),                     -- For semantic search (pgvector)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_claims_source ON synthesis.claims(source_id);
CREATE INDEX IF NOT EXISTS idx_claims_type ON synthesis.claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_claims_domains ON synthesis.claims USING GIN(domains);
CREATE INDEX IF NOT EXISTS idx_claims_confidence ON synthesis.claims(confidence);
CREATE INDEX IF NOT EXISTS idx_claims_entropy ON synthesis.claims(entropy_hash);

-- ============================================================================
-- CONTRADICTIONS - When claims conflict
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.contradictions (
    id SERIAL PRIMARY KEY,
    claim_a_id INTEGER REFERENCES synthesis.claims(id) ON DELETE CASCADE,
    claim_b_id INTEGER REFERENCES synthesis.claims(id) ON DELETE CASCADE,
    contradiction_type VARCHAR(50),             -- direct, methodological, scope, temporal
    severity FLOAT DEFAULT 0.5,                 -- 0-1 how severe is the contradiction
    resolution_status VARCHAR(30),              -- unresolved, resolved, superseded
    resolution_notes TEXT,
    detected_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    UNIQUE(claim_a_id, claim_b_id)
);

-- ============================================================================
-- CONNECTIONS - Cross-domain links between claims/concepts
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.connections (
    id SERIAL PRIMARY KEY,
    source_claim_id INTEGER REFERENCES synthesis.claims(id) ON DELETE CASCADE,
    target_claim_id INTEGER REFERENCES synthesis.claims(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL,       -- supports, contradicts, extends, analogous, causal, correlational
    strength FLOAT DEFAULT 0.5,                 -- 0-1 connection strength
    cross_domain BOOLEAN DEFAULT FALSE,         -- Does this bridge domains?
    source_domain INTEGER REFERENCES synthesis.domains(id),
    target_domain INTEGER REFERENCES synthesis.domains(id),
    reasoning TEXT,                             -- Why this connection exists
    evidence JSONB,                             -- Supporting evidence
    discovered_by VARCHAR(50),                  -- algorithm, manual, llm
    entropy_score FLOAT,                        -- Novelty/information score
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_claim_id, target_claim_id, connection_type)
);

CREATE INDEX IF NOT EXISTS idx_connections_cross_domain ON synthesis.connections(cross_domain);
CREATE INDEX IF NOT EXISTS idx_connections_type ON synthesis.connections(connection_type);
CREATE INDEX IF NOT EXISTS idx_connections_strength ON synthesis.connections(strength);

-- ============================================================================
-- PATTERNS - Higher-order structures discovered across knowledge
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.patterns (
    id SERIAL PRIMARY KEY,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(50) NOT NULL,          -- convergence, divergence, cycle, hierarchy, emergence
    description TEXT NOT NULL,
    domains INTEGER[],                          -- Domains involved
    claim_ids INTEGER[],                        -- Claims that form this pattern
    connection_ids INTEGER[],                   -- Connections that form this pattern
    confidence FLOAT DEFAULT 0.5,
    novelty_score FLOAT,                        -- How novel is this pattern?
    utility_score FLOAT,                        -- How useful is this insight?
    evidence JSONB,
    implications TEXT,                          -- What does this pattern suggest?
    questions_raised TEXT[],                    -- New questions from this pattern
    entropy_hash VARCHAR(128),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON synthesis.patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_domains ON synthesis.patterns USING GIN(domains);
CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON synthesis.patterns(confidence);

-- ============================================================================
-- HYPOTHESES - Generated predictions/questions
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.hypotheses (
    id SERIAL PRIMARY KEY,
    hypothesis_text TEXT NOT NULL,
    source_pattern_id INTEGER REFERENCES synthesis.patterns(id),
    domains INTEGER[],
    testable BOOLEAN DEFAULT TRUE,
    priority FLOAT DEFAULT 0.5,
    status VARCHAR(30) DEFAULT 'proposed',      -- proposed, testing, supported, refuted
    supporting_evidence JSONB,
    refuting_evidence JSONB,
    generated_by VARCHAR(50),                   -- pattern_detector, cross_domain, gap_analysis
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- KNOWLEDGE GAPS - What we don't know
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.gaps (
    id SERIAL PRIMARY KEY,
    gap_description TEXT NOT NULL,
    domains INTEGER[],
    related_claims INTEGER[],
    importance FLOAT DEFAULT 0.5,
    tractability FLOAT DEFAULT 0.5,             -- How likely to be solved?
    research_directions TEXT[],
    status VARCHAR(30) DEFAULT 'open',          -- open, being_addressed, closed
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- LEARNING LOG - Track what Cipher has learned
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.learning_log (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT gen_random_uuid(),
    domain_id INTEGER REFERENCES synthesis.domains(id),
    action VARCHAR(50) NOT NULL,                -- fetch, extract, connect, pattern, question
    details JSONB,
    sources_processed INTEGER DEFAULT 0,
    claims_extracted INTEGER DEFAULT 0,
    connections_found INTEGER DEFAULT 0,
    patterns_discovered INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- THOUGHTS - Cipher's internal monologue/reasoning
-- ============================================================================
CREATE TABLE IF NOT EXISTS synthesis.thoughts (
    id SERIAL PRIMARY KEY,
    thought_type VARCHAR(50) NOT NULL,          -- observation, question, insight, doubt, connection
    content TEXT NOT NULL,
    domains INTEGER[],
    related_claims INTEGER[],
    importance FLOAT DEFAULT 0.5,
    acted_upon BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- VIEWS for common queries
-- ============================================================================

-- Cross-domain connections (the interesting stuff)
CREATE OR REPLACE VIEW synthesis.cross_domain_insights AS
SELECT
    c.id,
    c.connection_type,
    c.strength,
    c.reasoning,
    c.entropy_score,
    d1.name as source_domain,
    d2.name as target_domain,
    cl1.claim_text as source_claim,
    cl2.claim_text as target_claim
FROM synthesis.connections c
JOIN synthesis.domains d1 ON c.source_domain = d1.id
JOIN synthesis.domains d2 ON c.target_domain = d2.id
JOIN synthesis.claims cl1 ON c.source_claim_id = cl1.id
JOIN synthesis.claims cl2 ON c.target_claim_id = cl2.id
WHERE c.cross_domain = TRUE
ORDER BY c.entropy_score DESC NULLS LAST, c.strength DESC;

-- High-confidence patterns
CREATE OR REPLACE VIEW synthesis.strong_patterns AS
SELECT
    p.*,
    array_agg(DISTINCT d.name) as domain_names
FROM synthesis.patterns p
LEFT JOIN synthesis.domains d ON d.id = ANY(p.domains)
WHERE p.confidence >= 0.7
GROUP BY p.id
ORDER BY p.novelty_score DESC NULLS LAST;

-- Unresolved contradictions
CREATE OR REPLACE VIEW synthesis.open_contradictions AS
SELECT
    ct.id,
    ct.contradiction_type,
    ct.severity,
    c1.claim_text as claim_a,
    c2.claim_text as claim_b,
    s1.title as source_a,
    s2.title as source_b
FROM synthesis.contradictions ct
JOIN synthesis.claims c1 ON ct.claim_a_id = c1.id
JOIN synthesis.claims c2 ON ct.claim_b_id = c2.id
JOIN synthesis.sources s1 ON c1.source_id = s1.id
JOIN synthesis.sources s2 ON c2.source_id = s2.id
WHERE ct.resolution_status = 'unresolved'
ORDER BY ct.severity DESC;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Calculate domain overlap between two claim sets
CREATE OR REPLACE FUNCTION synthesis.domain_overlap(domains_a INTEGER[], domains_b INTEGER[])
RETURNS FLOAT AS $$
BEGIN
    IF array_length(domains_a, 1) IS NULL OR array_length(domains_b, 1) IS NULL THEN
        RETURN 0;
    END IF;
    RETURN (
        SELECT COUNT(*)::FLOAT / GREATEST(array_length(domains_a, 1), array_length(domains_b, 1))
        FROM unnest(domains_a) a
        WHERE a = ANY(domains_b)
    );
END;
$$ LANGUAGE plpgsql;

-- Get learning stats
CREATE OR REPLACE FUNCTION synthesis.get_stats()
RETURNS TABLE (
    total_sources BIGINT,
    total_claims BIGINT,
    total_connections BIGINT,
    total_patterns BIGINT,
    cross_domain_connections BIGINT,
    open_contradictions BIGINT,
    open_gaps BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM synthesis.sources),
        (SELECT COUNT(*) FROM synthesis.claims),
        (SELECT COUNT(*) FROM synthesis.connections),
        (SELECT COUNT(*) FROM synthesis.patterns),
        (SELECT COUNT(*) FROM synthesis.connections WHERE cross_domain = TRUE),
        (SELECT COUNT(*) FROM synthesis.contradictions WHERE resolution_status = 'unresolved'),
        (SELECT COUNT(*) FROM synthesis.gaps WHERE status = 'open');
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Enable pgvector extension for embeddings (run separately if needed)
-- ============================================================================
-- CREATE EXTENSION IF NOT EXISTS vector;

COMMENT ON SCHEMA synthesis IS 'Cipher cognitive system - cross-domain knowledge synthesis';
