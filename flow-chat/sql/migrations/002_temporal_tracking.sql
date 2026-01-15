-- ============================================================================
-- CIPHER Migration: Temporal Tracking Support
-- Version: 002
-- Date: 2026-01-10
-- Description: Add temporal tracking fields for claim evolution
-- ============================================================================

-- Add temporal tracking columns to claims table
ALTER TABLE synthesis.claims
    ADD COLUMN IF NOT EXISTS current_confidence FLOAT,
    ADD COLUMN IF NOT EXISTS confidence_trend FLOAT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_confirmed TIMESTAMP,
    ADD COLUMN IF NOT EXISTS last_cited TIMESTAMP,
    ADD COLUMN IF NOT EXISTS replication_status VARCHAR(30) DEFAULT 'unreplicated',
    ADD COLUMN IF NOT EXISTS replication_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS failed_replication_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS citation_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS citation_velocity FLOAT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS superseded_by INTEGER REFERENCES synthesis.claims(id),
    ADD COLUMN IF NOT EXISTS supersession_reason TEXT;

-- Initialize current_confidence from confidence
UPDATE synthesis.claims
SET current_confidence = confidence
WHERE current_confidence IS NULL;

-- Create evidence events table
CREATE TABLE IF NOT EXISTS synthesis.evidence_events (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER REFERENCES synthesis.claims(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- replication, citation, contradiction, support, retraction
    impact FLOAT NOT NULL,            -- Confidence impact (-1 to 1)
    source_id INTEGER REFERENCES synthesis.sources(id),
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_events_claim ON synthesis.evidence_events(claim_id);
CREATE INDEX IF NOT EXISTS idx_evidence_events_type ON synthesis.evidence_events(event_type);
CREATE INDEX IF NOT EXISTS idx_evidence_events_date ON synthesis.evidence_events(created_at);

-- Create temporal patterns table
CREATE TABLE IF NOT EXISTS synthesis.temporal_patterns (
    id SERIAL PRIMARY KEY,
    pattern_type VARCHAR(50) NOT NULL,  -- paradigm_shift, emerging_consensus, declining_theory
    claims_involved INTEGER[],
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    description TEXT,
    confidence FLOAT,
    domains INTEGER[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add indexes for temporal queries
CREATE INDEX IF NOT EXISTS idx_claims_status ON synthesis.claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_replication ON synthesis.claims(replication_status);
CREATE INDEX IF NOT EXISTS idx_claims_current_conf ON synthesis.claims(current_confidence);
CREATE INDEX IF NOT EXISTS idx_claims_superseded ON synthesis.claims(superseded_by);
CREATE INDEX IF NOT EXISTS idx_claims_created ON synthesis.claims(created_at);

-- View for claims needing attention (old, low confidence, unreplicated)
CREATE OR REPLACE VIEW synthesis.claims_needing_attention AS
SELECT
    c.id,
    c.claim_text,
    c.confidence as original_confidence,
    c.current_confidence,
    c.replication_status,
    c.citation_count,
    c.created_at,
    EXTRACT(days FROM NOW() - c.created_at) as age_days,
    s.title as source_title
FROM synthesis.claims c
LEFT JOIN synthesis.sources s ON c.source_id = s.id
WHERE (c.status = 'active' OR c.status IS NULL)
AND c.replication_status IN ('unreplicated', 'contested')
AND (c.current_confidence < 0.5 OR c.current_confidence IS NULL)
AND c.created_at < NOW() - INTERVAL '180 days'
ORDER BY c.current_confidence ASC NULLS FIRST;

-- View for recently superseded claims
CREATE OR REPLACE VIEW synthesis.recently_superseded AS
SELECT
    c.id,
    c.claim_text,
    c.status,
    c.superseded_by,
    c.supersession_reason,
    c.updated_at,
    c2.claim_text as superseding_claim
FROM synthesis.claims c
LEFT JOIN synthesis.claims c2 ON c.superseded_by = c2.id
WHERE c.status = 'superseded'
ORDER BY c.updated_at DESC
LIMIT 100;

-- View for replication status summary
CREATE OR REPLACE VIEW synthesis.replication_summary AS
SELECT
    replication_status,
    COUNT(*) as count,
    AVG(current_confidence) as avg_confidence,
    AVG(EXTRACT(days FROM NOW() - created_at)) as avg_age_days
FROM synthesis.claims
GROUP BY replication_status;

-- Function to calculate decayed confidence
CREATE OR REPLACE FUNCTION synthesis.calculate_decayed_confidence(
    original_conf FLOAT,
    created_at TIMESTAMP,
    half_life_days FLOAT DEFAULT 1095  -- 3 years default
)
RETURNS FLOAT AS $$
DECLARE
    age_days FLOAT;
    decay_factor FLOAT;
BEGIN
    age_days := EXTRACT(days FROM NOW() - created_at);
    IF age_days <= 0 THEN
        RETURN original_conf;
    END IF;
    decay_factor := POWER(0.5, age_days / half_life_days);
    RETURN GREATEST(0.05, original_conf * decay_factor);
END;
$$ LANGUAGE plpgsql;

-- Function to get claim temporal stats
CREATE OR REPLACE FUNCTION synthesis.get_claim_temporal_stats(p_claim_id INTEGER)
RETURNS TABLE (
    claim_id INTEGER,
    age_days INTEGER,
    original_confidence FLOAT,
    current_confidence FLOAT,
    confidence_change FLOAT,
    replication_status VARCHAR,
    total_replications INTEGER,
    failed_replications INTEGER,
    citation_count INTEGER,
    evidence_events_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        EXTRACT(days FROM NOW() - c.created_at)::INTEGER,
        c.confidence,
        c.current_confidence,
        COALESCE(c.current_confidence, c.confidence) - c.confidence,
        c.replication_status,
        c.replication_count,
        c.failed_replication_count,
        c.citation_count,
        (SELECT COUNT(*) FROM synthesis.evidence_events e WHERE e.claim_id = c.id)
    FROM synthesis.claims c
    WHERE c.id = p_claim_id;
END;
$$ LANGUAGE plpgsql;

-- Update get_stats to include temporal info
CREATE OR REPLACE FUNCTION synthesis.get_stats()
RETURNS TABLE (
    total_sources BIGINT,
    total_claims BIGINT,
    total_connections BIGINT,
    total_patterns BIGINT,
    cross_domain_connections BIGINT,
    open_contradictions BIGINT,
    open_gaps BIGINT,
    claims_with_embeddings BIGINT,
    replicated_claims BIGINT,
    failed_replications BIGINT,
    superseded_claims BIGINT,
    avg_claim_age_days FLOAT
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
        (SELECT COUNT(*) FROM synthesis.claims WHERE embedding IS NOT NULL),
        (SELECT COUNT(*) FROM synthesis.claims WHERE replication_status = 'replicated'),
        (SELECT COUNT(*) FROM synthesis.claims WHERE replication_status = 'failed_replication'),
        (SELECT COUNT(*) FROM synthesis.claims WHERE status = 'superseded'),
        (SELECT AVG(EXTRACT(days FROM NOW() - created_at)) FROM synthesis.claims);
END;
$$ LANGUAGE plpgsql;

-- Comments
COMMENT ON COLUMN synthesis.claims.current_confidence IS 'Confidence after temporal decay and evidence updates';
COMMENT ON COLUMN synthesis.claims.confidence_trend IS 'Recent trend in confidence (positive = increasing)';
COMMENT ON COLUMN synthesis.claims.replication_status IS 'Status: unreplicated, replicated, partially_replicated, failed_replication, contested';
COMMENT ON COLUMN synthesis.claims.status IS 'Lifecycle: active, superseded, retracted, deprecated, merged';
COMMENT ON TABLE synthesis.evidence_events IS 'Log of events affecting claim confidence over time';
COMMENT ON TABLE synthesis.temporal_patterns IS 'Detected patterns in temporal evolution (paradigm shifts, etc.)';

-- ============================================================================
-- Migration complete
-- ============================================================================
