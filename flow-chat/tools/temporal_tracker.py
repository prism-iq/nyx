"""
CIPHER Temporal Tracking Module

Tracks the evolution of scientific claims over time:
- Confidence decay for aging claims without confirmation
- Replication status tracking
- Supersession detection (newer claims replacing older ones)
- Evidence accumulation over time
- Paradigm shift detection

Inspired by:
- Bayesian belief updating (Psychology/Math)
- Evolutionary dynamics (Biology)
- Information decay in memory (Neuroscience)
"""

import asyncio
import logging
import math
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

import asyncpg

logger = logging.getLogger(__name__)


class ReplicationStatus(Enum):
    """Status of claim replication attempts"""
    UNREPLICATED = "unreplicated"      # No replication attempts
    REPLICATED = "replicated"          # Successfully replicated
    PARTIALLY_REPLICATED = "partially_replicated"  # Some replications succeeded
    FAILED_REPLICATION = "failed_replication"      # Replication attempts failed
    CONTESTED = "contested"            # Mixed results, ongoing debate


class ClaimStatus(Enum):
    """Lifecycle status of a claim"""
    ACTIVE = "active"                  # Current, valid claim
    SUPERSEDED = "superseded"          # Replaced by newer claim
    RETRACTED = "retracted"            # Withdrawn by authors
    DEPRECATED = "deprecated"          # No longer considered valid
    MERGED = "merged"                  # Combined with another claim


@dataclass
class TemporalState:
    """Temporal state of a claim"""
    claim_id: int
    first_seen: datetime
    last_confirmed: Optional[datetime]
    last_cited: Optional[datetime]
    original_confidence: float
    current_confidence: float
    confidence_trend: float  # Positive = increasing, negative = decreasing
    replication_status: ReplicationStatus
    replication_count: int
    failed_replication_count: int
    citation_count: int
    citation_velocity: float  # Citations per month
    status: ClaimStatus
    superseded_by: Optional[int]  # Claim ID that superseded this one
    age_days: int
    half_life_days: float  # Estimated confidence half-life


@dataclass
class EvidenceEvent:
    """An event that affects claim confidence"""
    event_type: str  # replication, citation, contradiction, support, retraction
    timestamp: datetime
    source_id: Optional[int]
    impact: float  # Positive or negative impact on confidence
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TemporalPattern:
    """A pattern detected in temporal evolution"""
    pattern_type: str  # paradigm_shift, emerging_consensus, declining_theory
    claims_involved: List[int]
    start_date: datetime
    description: str
    confidence: float


class TemporalTracker:
    """
    Tracks temporal dynamics of scientific claims.

    Core principles:
    1. Claims decay without confirmation (half-life model)
    2. Replication strengthens confidence
    3. New evidence updates beliefs (Bayesian)
    4. Supersession follows logical structure
    """

    # Default confidence half-life in days (claims lose half confidence after this time without confirmation)
    DEFAULT_HALF_LIFE = 365 * 3  # 3 years

    # Minimum confidence (claims never go below this)
    MIN_CONFIDENCE = 0.05

    # Maximum confidence boost per evidence event
    MAX_BOOST = 0.15

    # Replication impact factors
    REPLICATION_SUCCESS_BOOST = 0.12
    REPLICATION_FAILURE_PENALTY = 0.18
    PARTIAL_REPLICATION_BOOST = 0.05

    # Citation impact (logarithmic)
    CITATION_BOOST_FACTOR = 0.02

    def __init__(self, db_url: str):
        """
        Initialize the temporal tracker.

        Args:
            db_url: PostgreSQL connection string
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establish database connection."""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=2,
            max_size=10
        )
        logger.info("Temporal tracker connected to database")

    async def close(self):
        """Close database connection."""
        if self.pool:
            await self.pool.close()

    def calculate_decay(
        self,
        original_confidence: float,
        age_days: int,
        half_life_days: float = None
    ) -> float:
        """
        Calculate confidence decay using exponential model.

        C(t) = C_0 * (0.5)^(t/half_life)

        Args:
            original_confidence: Initial confidence value
            age_days: Days since claim was made
            half_life_days: Custom half-life (default: 3 years)

        Returns:
            Decayed confidence value
        """
        if half_life_days is None:
            half_life_days = self.DEFAULT_HALF_LIFE

        if age_days <= 0 or half_life_days <= 0:
            return original_confidence

        decay_factor = math.pow(0.5, age_days / half_life_days)
        decayed = original_confidence * decay_factor

        return max(self.MIN_CONFIDENCE, decayed)

    def calculate_half_life(
        self,
        claim_type: str,
        domain: str,
        evidence_strength: str
    ) -> float:
        """
        Calculate appropriate half-life for a claim based on its characteristics.

        Different types of claims have different expected lifespans:
        - Definitions: Very long (rarely change)
        - Methods: Long (evolve slowly)
        - Findings: Medium (subject to replication)
        - Hypotheses: Short (need testing)
        """
        # Base half-life by claim type (in days)
        base_half_life = {
            'definition': 365 * 10,   # 10 years
            'method': 365 * 5,        # 5 years
            'finding': 365 * 3,       # 3 years
            'observation': 365 * 2,   # 2 years
            'hypothesis': 365 * 1,    # 1 year
            'conclusion': 365 * 2,    # 2 years
        }.get(claim_type, 365 * 3)

        # Adjust by evidence strength
        strength_multiplier = {
            'definitive': 2.0,
            'strong': 1.5,
            'moderate': 1.0,
            'weak': 0.5,
        }.get(evidence_strength, 1.0)

        # Adjust by domain (some fields move faster)
        domain_multiplier = {
            'NEUROSCIENCES': 0.8,    # Fast-moving field
            'BIOLOGY': 0.9,
            'PSYCHOLOGY': 0.85,
            'MEDICINE': 0.9,
            'MATHEMATICS': 1.5,      # Slower to change
            'ART': 1.2,
        }.get(domain, 1.0)

        return base_half_life * strength_multiplier * domain_multiplier

    async def get_temporal_state(self, claim_id: int) -> Optional[TemporalState]:
        """
        Get the current temporal state of a claim.

        Args:
            claim_id: ID of the claim

        Returns:
            TemporalState object or None if not found
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT
                    c.id,
                    c.created_at as first_seen,
                    c.last_confirmed,
                    c.last_cited,
                    c.confidence as original_confidence,
                    c.current_confidence,
                    c.confidence_trend,
                    c.replication_status,
                    c.replication_count,
                    c.failed_replication_count,
                    c.citation_count,
                    c.citation_velocity,
                    c.status,
                    c.superseded_by,
                    c.claim_type,
                    c.evidence_strength,
                    COALESCE(d.name, 'UNKNOWN') as domain
                FROM synthesis.claims c
                LEFT JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE c.id = $1
            ''', claim_id)

            if not row:
                return None

            first_seen = row['first_seen']
            age_days = (datetime.now() - first_seen).days if first_seen else 0

            # Calculate current confidence with decay
            original_conf = row['original_confidence'] or 0.5
            half_life = self.calculate_half_life(
                row['claim_type'] or 'finding',
                row['domain'],
                row['evidence_strength'] or 'moderate'
            )

            # Apply decay
            decayed_conf = self.calculate_decay(original_conf, age_days, half_life)

            # Apply replication adjustments
            current_conf = decayed_conf
            replication_status = ReplicationStatus(row['replication_status'] or 'unreplicated')

            if replication_status == ReplicationStatus.REPLICATED:
                current_conf = min(0.95, current_conf + self.REPLICATION_SUCCESS_BOOST * (row['replication_count'] or 0))
            elif replication_status == ReplicationStatus.FAILED_REPLICATION:
                current_conf = max(self.MIN_CONFIDENCE, current_conf - self.REPLICATION_FAILURE_PENALTY)

            # Apply citation boost (logarithmic)
            citation_count = row['citation_count'] or 0
            if citation_count > 0:
                citation_boost = self.CITATION_BOOST_FACTOR * math.log10(citation_count + 1)
                current_conf = min(0.95, current_conf + citation_boost)

            return TemporalState(
                claim_id=claim_id,
                first_seen=first_seen,
                last_confirmed=row['last_confirmed'],
                last_cited=row['last_cited'],
                original_confidence=original_conf,
                current_confidence=current_conf,
                confidence_trend=row['confidence_trend'] or 0.0,
                replication_status=replication_status,
                replication_count=row['replication_count'] or 0,
                failed_replication_count=row['failed_replication_count'] or 0,
                citation_count=citation_count,
                citation_velocity=row['citation_velocity'] or 0.0,
                status=ClaimStatus(row['status'] or 'active'),
                superseded_by=row['superseded_by'],
                age_days=age_days,
                half_life_days=half_life
            )

    async def record_evidence(
        self,
        claim_id: int,
        event_type: str,
        impact: float,
        source_id: Optional[int] = None,
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Record an evidence event that affects a claim's confidence.

        Args:
            claim_id: ID of the affected claim
            event_type: Type of evidence (replication, citation, contradiction, support)
            impact: Confidence impact (-1 to 1)
            source_id: Source paper ID if applicable
            details: Additional event details

        Returns:
            True if recorded successfully
        """
        async with self.pool.acquire() as conn:
            # Record the evidence event
            await conn.execute('''
                INSERT INTO synthesis.evidence_events
                (claim_id, event_type, impact, source_id, details, created_at)
                VALUES ($1, $2, $3, $4, $5, NOW())
            ''', claim_id, event_type, impact, source_id,
                json.dumps(details) if details else None)

            # Update claim's current confidence
            await conn.execute('''
                UPDATE synthesis.claims
                SET
                    current_confidence = GREATEST($2, LEAST(0.95,
                        COALESCE(current_confidence, confidence) + $3
                    )),
                    last_confirmed = CASE WHEN $4 IN ('replication', 'support') THEN NOW() ELSE last_confirmed END,
                    last_cited = CASE WHEN $4 = 'citation' THEN NOW() ELSE last_cited END,
                    confidence_trend = COALESCE(confidence_trend, 0) + $3,
                    updated_at = NOW()
                WHERE id = $1
            ''', claim_id, self.MIN_CONFIDENCE, impact, event_type)

            return True

    async def record_replication(
        self,
        claim_id: int,
        success: bool,
        source_id: Optional[int] = None,
        partial: bool = False,
        details: Dict[str, Any] = None
    ) -> bool:
        """
        Record a replication attempt for a claim.

        Args:
            claim_id: ID of the replicated claim
            success: Whether replication was successful
            source_id: Replication study source ID
            partial: Whether it was a partial replication
            details: Additional details

        Returns:
            True if recorded successfully
        """
        if success:
            if partial:
                impact = self.PARTIAL_REPLICATION_BOOST
                event_type = 'partial_replication'
            else:
                impact = self.REPLICATION_SUCCESS_BOOST
                event_type = 'replication'
        else:
            impact = -self.REPLICATION_FAILURE_PENALTY
            event_type = 'failed_replication'

        async with self.pool.acquire() as conn:
            # Update replication counts
            if success:
                await conn.execute('''
                    UPDATE synthesis.claims
                    SET
                        replication_count = COALESCE(replication_count, 0) + 1,
                        replication_status = CASE
                            WHEN replication_count >= 2 THEN 'replicated'
                            WHEN $2 THEN 'partially_replicated'
                            ELSE 'partially_replicated'
                        END,
                        updated_at = NOW()
                    WHERE id = $1
                ''', claim_id, partial)
            else:
                await conn.execute('''
                    UPDATE synthesis.claims
                    SET
                        failed_replication_count = COALESCE(failed_replication_count, 0) + 1,
                        replication_status = CASE
                            WHEN failed_replication_count >= 2 THEN 'failed_replication'
                            ELSE 'contested'
                        END,
                        updated_at = NOW()
                    WHERE id = $1
                ''', claim_id)

        # Record the evidence event
        return await self.record_evidence(
            claim_id, event_type, impact, source_id, details
        )

    async def mark_superseded(
        self,
        old_claim_id: int,
        new_claim_id: int,
        reason: str = None
    ) -> bool:
        """
        Mark a claim as superseded by a newer claim.

        Args:
            old_claim_id: ID of the superseded claim
            new_claim_id: ID of the superseding claim
            reason: Reason for supersession

        Returns:
            True if successful
        """
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE synthesis.claims
                SET
                    status = 'superseded',
                    superseded_by = $2,
                    supersession_reason = $3,
                    updated_at = NOW()
                WHERE id = $1
            ''', old_claim_id, new_claim_id, reason)

            # Record as connection
            await conn.execute('''
                INSERT INTO synthesis.connections
                (source_claim_id, target_claim_id, connection_type, strength, reasoning, created_at)
                VALUES ($1, $2, 'supersedes', 0.9, $3, NOW())
                ON CONFLICT DO NOTHING
            ''', new_claim_id, old_claim_id, reason)

            return True

    async def update_citation_count(
        self,
        claim_id: int,
        citation_count: int
    ):
        """Update citation count for a claim."""
        async with self.pool.acquire() as conn:
            # Get previous citation count to calculate velocity
            row = await conn.fetchrow('''
                SELECT citation_count, last_cited, created_at
                FROM synthesis.claims
                WHERE id = $1
            ''', claim_id)

            if row:
                old_count = row['citation_count'] or 0
                new_citations = citation_count - old_count

                # Calculate citation velocity (citations per month)
                if row['last_cited']:
                    days_since = (datetime.now() - row['last_cited']).days
                    if days_since > 0:
                        velocity = (new_citations / days_since) * 30
                    else:
                        velocity = 0
                else:
                    days_since = (datetime.now() - row['created_at']).days
                    velocity = (citation_count / max(1, days_since)) * 30

                await conn.execute('''
                    UPDATE synthesis.claims
                    SET
                        citation_count = $2,
                        citation_velocity = $3,
                        last_cited = NOW(),
                        updated_at = NOW()
                    WHERE id = $1
                ''', claim_id, citation_count, velocity)

    async def decay_all_claims(self) -> int:
        """
        Apply confidence decay to all claims.
        Should be run periodically (e.g., daily).

        Returns:
            Number of claims updated
        """
        async with self.pool.acquire() as conn:
            # Get all active claims
            rows = await conn.fetch('''
                SELECT
                    c.id,
                    c.confidence,
                    c.current_confidence,
                    c.created_at,
                    c.claim_type,
                    c.evidence_strength,
                    COALESCE(d.name, 'UNKNOWN') as domain
                FROM synthesis.claims c
                LEFT JOIN synthesis.domains d ON d.id = ANY(c.domains)
                WHERE c.status = 'active' OR c.status IS NULL
            ''')

            updated = 0
            for row in rows:
                age_days = (datetime.now() - row['created_at']).days
                half_life = self.calculate_half_life(
                    row['claim_type'] or 'finding',
                    row['domain'],
                    row['evidence_strength'] or 'moderate'
                )

                new_confidence = self.calculate_decay(
                    row['confidence'] or 0.5,
                    age_days,
                    half_life
                )

                # Only update if confidence changed significantly
                old_conf = row['current_confidence'] or row['confidence'] or 0.5
                if abs(new_confidence - old_conf) > 0.01:
                    await conn.execute('''
                        UPDATE synthesis.claims
                        SET
                            current_confidence = $2,
                            confidence_trend = $2 - COALESCE(current_confidence, confidence),
                            updated_at = NOW()
                        WHERE id = $1
                    ''', row['id'], new_confidence)
                    updated += 1

            logger.info(f"Decayed confidence for {updated} claims")
            return updated

    async def find_supersession_candidates(
        self,
        similarity_threshold: float = 0.8
    ) -> List[Tuple[int, int, float]]:
        """
        Find claims that might supersede older claims.

        Uses semantic similarity to find newer claims that may replace older ones.

        Returns:
            List of (old_claim_id, new_claim_id, similarity) tuples
        """
        candidates = []

        async with self.pool.acquire() as conn:
            # Find pairs of similar claims where one is significantly newer
            rows = await conn.fetch('''
                SELECT
                    c1.id as old_id,
                    c2.id as new_id,
                    c1.claim_text as old_text,
                    c2.claim_text as new_text,
                    c1.created_at as old_date,
                    c2.created_at as new_date,
                    c1.embedding as old_emb,
                    c2.embedding as new_emb
                FROM synthesis.claims c1
                JOIN synthesis.claims c2 ON c1.id < c2.id
                WHERE c1.embedding IS NOT NULL
                AND c2.embedding IS NOT NULL
                AND c2.created_at > c1.created_at + INTERVAL '30 days'
                AND c1.status != 'superseded'
                AND (c1.domains && c2.domains)  -- Same domain
                LIMIT 1000
            ''')

            for row in rows:
                # Calculate similarity
                if row['old_emb'] and row['new_emb']:
                    # Parse embeddings
                    old_emb = row['old_emb']
                    new_emb = row['new_emb']

                    if isinstance(old_emb, str):
                        old_vec = [float(x) for x in old_emb.strip('[]').split(',')]
                        new_vec = [float(x) for x in new_emb.strip('[]').split(',')]
                    else:
                        old_vec = list(old_emb)
                        new_vec = list(new_emb)

                    # Cosine similarity
                    import numpy as np
                    old_arr = np.array(old_vec)
                    new_arr = np.array(new_vec)
                    similarity = float(np.dot(old_arr, new_arr) / (
                        np.linalg.norm(old_arr) * np.linalg.norm(new_arr)
                    ))

                    if similarity >= similarity_threshold:
                        candidates.append((row['old_id'], row['new_id'], similarity))

        return candidates

    async def detect_paradigm_shifts(
        self,
        lookback_days: int = 365
    ) -> List[TemporalPattern]:
        """
        Detect potential paradigm shifts in the knowledge base.

        A paradigm shift is indicated by:
        - Multiple related claims being superseded
        - Cluster of failed replications
        - Rapid emergence of new claims in a topic

        Returns:
            List of detected paradigm shift patterns
        """
        patterns = []
        cutoff = datetime.now() - timedelta(days=lookback_days)

        async with self.pool.acquire() as conn:
            # Find clusters of superseded claims
            superseded = await conn.fetch('''
                SELECT
                    c.id,
                    c.claim_text,
                    c.domains,
                    c.updated_at,
                    c.superseded_by
                FROM synthesis.claims c
                WHERE c.status = 'superseded'
                AND c.updated_at > $1
                ORDER BY c.updated_at DESC
            ''', cutoff)

            # Find clusters of failed replications
            failed = await conn.fetch('''
                SELECT
                    c.id,
                    c.claim_text,
                    c.domains,
                    c.updated_at
                FROM synthesis.claims c
                WHERE c.replication_status = 'failed_replication'
                AND c.updated_at > $1
            ''', cutoff)

            # Group by domain
            from collections import defaultdict
            superseded_by_domain = defaultdict(list)
            for row in superseded:
                for domain_id in (row['domains'] or []):
                    superseded_by_domain[domain_id].append(row)

            failed_by_domain = defaultdict(list)
            for row in failed:
                for domain_id in (row['domains'] or []):
                    failed_by_domain[domain_id].append(row)

            # Detect patterns
            for domain_id, claims in superseded_by_domain.items():
                if len(claims) >= 3:
                    patterns.append(TemporalPattern(
                        pattern_type='paradigm_shift',
                        claims_involved=[c['id'] for c in claims],
                        start_date=min(c['updated_at'] for c in claims),
                        description=f"Multiple claims superseded in domain {domain_id}",
                        confidence=min(0.9, 0.3 + len(claims) * 0.1)
                    ))

            for domain_id, claims in failed_by_domain.items():
                if len(claims) >= 2:
                    patterns.append(TemporalPattern(
                        pattern_type='declining_theory',
                        claims_involved=[c['id'] for c in claims],
                        start_date=min(c['updated_at'] for c in claims),
                        description=f"Multiple failed replications in domain {domain_id}",
                        confidence=min(0.85, 0.4 + len(claims) * 0.15)
                    ))

        return patterns

    async def get_confidence_history(
        self,
        claim_id: int,
        days: int = 365
    ) -> List[Tuple[datetime, float]]:
        """
        Get confidence history for a claim over time.

        Returns:
            List of (timestamp, confidence) tuples
        """
        history = []

        async with self.pool.acquire() as conn:
            # Get evidence events
            events = await conn.fetch('''
                SELECT created_at, impact
                FROM synthesis.evidence_events
                WHERE claim_id = $1
                AND created_at > NOW() - INTERVAL '%s days'
                ORDER BY created_at ASC
            ''' % days, claim_id)

            # Get initial confidence
            claim = await conn.fetchrow('''
                SELECT confidence, created_at
                FROM synthesis.claims
                WHERE id = $1
            ''', claim_id)

            if claim:
                current_conf = claim['confidence'] or 0.5
                history.append((claim['created_at'], current_conf))

                for event in events:
                    current_conf = max(self.MIN_CONFIDENCE, min(0.95, current_conf + event['impact']))
                    history.append((event['created_at'], current_conf))

        return history

    async def get_aging_claims(
        self,
        min_age_days: int = 365,
        max_confidence: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find old claims with declining confidence that may need attention.

        Returns:
            List of claim dicts with temporal info
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT
                    c.id,
                    c.claim_text,
                    c.confidence as original_confidence,
                    c.current_confidence,
                    c.created_at,
                    c.replication_status,
                    EXTRACT(days FROM NOW() - c.created_at) as age_days
                FROM synthesis.claims c
                WHERE c.status = 'active' OR c.status IS NULL
                AND c.created_at < NOW() - INTERVAL '%s days'
                AND (c.current_confidence < $1 OR c.current_confidence IS NULL)
                ORDER BY c.current_confidence ASC NULLS FIRST
                LIMIT 50
            ''' % min_age_days, max_confidence)

            return [dict(row) for row in rows]


# Import json for serialization
import json


# Singleton instance
_tracker: Optional[TemporalTracker] = None


def get_temporal_tracker(db_url: str) -> TemporalTracker:
    """Get or create the global temporal tracker."""
    global _tracker
    if _tracker is None:
        _tracker = TemporalTracker(db_url)
    return _tracker
