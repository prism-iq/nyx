-- ============================================================================
-- CIPHER Migration: Semantic Embeddings Support
-- Version: 001
-- Date: 2026-01-10
-- Description: Update embedding column and add vector search indexes
-- ============================================================================

-- Enable pgvector extension (required for vector operations)
CREATE EXTENSION IF NOT EXISTS vector;

-- Update the embedding column to support flexible dimensions
-- all-MiniLM-L6-v2: 384 dimensions
-- all-mpnet-base-v2: 768 dimensions
-- OpenAI ada-002: 1536 dimensions
-- We use 384 for the default model

-- Drop old column if exists with wrong dimensions
ALTER TABLE synthesis.claims
    DROP COLUMN IF EXISTS embedding;

-- Add new embedding column with correct dimensions for all-MiniLM-L6-v2
ALTER TABLE synthesis.claims
    ADD COLUMN IF NOT EXISTS embedding vector(384);

-- Create index for vector similarity search (IVFFlat for approximate nearest neighbor)
-- Note: This requires some data to be present. Run after initial embedding population.
-- CREATE INDEX IF NOT EXISTS idx_claims_embedding ON synthesis.claims
--     USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- For exact search (slower but works immediately)
CREATE INDEX IF NOT EXISTS idx_claims_embedding_hnsw ON synthesis.claims
    USING hnsw (embedding vector_cosine_ops);

-- Add metadata column to track embedding model
ALTER TABLE synthesis.claims
    ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100);

-- Create a view for claims with embeddings
CREATE OR REPLACE VIEW synthesis.embedded_claims AS
SELECT
    c.id,
    c.claim_text,
    c.claim_type,
    c.confidence,
    c.domains,
    c.embedding,
    c.embedding_model,
    s.title as source_title
FROM synthesis.claims c
LEFT JOIN synthesis.sources s ON c.source_id = s.id
WHERE c.embedding IS NOT NULL;

-- Function to find similar claims using vector similarity
CREATE OR REPLACE FUNCTION synthesis.find_similar_claims(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    claim_id int,
    claim_text text,
    claim_type varchar,
    confidence float,
    domains int[],
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.claim_text,
        c.claim_type::varchar,
        c.confidence::float,
        c.domains,
        (1 - (c.embedding <=> query_embedding))::float as similarity
    FROM synthesis.claims c
    WHERE c.embedding IS NOT NULL
    AND (1 - (c.embedding <=> query_embedding)) > match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Function to find cross-domain similar claims
CREATE OR REPLACE FUNCTION synthesis.find_cross_domain_similar(
    source_claim_id int,
    match_threshold float DEFAULT 0.75,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    claim_id int,
    claim_text text,
    source_domains int[],
    target_domains int[],
    similarity float
) AS $$
DECLARE
    source_embedding vector(384);
    source_domains int[];
BEGIN
    -- Get source claim embedding and domains
    SELECT embedding, domains
    INTO source_embedding, source_domains
    FROM synthesis.claims
    WHERE id = source_claim_id;

    IF source_embedding IS NULL THEN
        RETURN;
    END IF;

    RETURN QUERY
    SELECT
        c.id,
        c.claim_text,
        source_domains as source_domains,
        c.domains as target_domains,
        (1 - (c.embedding <=> source_embedding))::float as similarity
    FROM synthesis.claims c
    WHERE c.embedding IS NOT NULL
    AND c.id != source_claim_id
    AND NOT (c.domains && source_domains)  -- Different domains
    AND (1 - (c.embedding <=> source_embedding)) > match_threshold
    ORDER BY c.embedding <=> source_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Update statistics function to include embedding stats
CREATE OR REPLACE FUNCTION synthesis.get_stats()
RETURNS TABLE (
    total_sources BIGINT,
    total_claims BIGINT,
    total_connections BIGINT,
    total_patterns BIGINT,
    cross_domain_connections BIGINT,
    open_contradictions BIGINT,
    open_gaps BIGINT,
    claims_with_embeddings BIGINT
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
        (SELECT COUNT(*) FROM synthesis.gaps WHERE status = 'open'),
        (SELECT COUNT(*) FROM synthesis.claims WHERE embedding IS NOT NULL);
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON COLUMN synthesis.claims.embedding IS 'Semantic embedding vector (384d, all-MiniLM-L6-v2)';
COMMENT ON COLUMN synthesis.claims.embedding_model IS 'Model used to generate embedding';
COMMENT ON FUNCTION synthesis.find_similar_claims IS 'Find semantically similar claims using vector similarity';
COMMENT ON FUNCTION synthesis.find_cross_domain_similar IS 'Find similar claims from different domains';

-- ============================================================================
-- Migration complete
-- ============================================================================
