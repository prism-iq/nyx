"""
CIPHER Active Learner
Implements active learning strategies to prioritize what to learn next.

Unlike passive learning (fetch → extract → store), active learning:
1. Prioritizes domains/concepts with high uncertainty
2. Targets papers that could resolve contradictions
3. Seeks evidence for/against open hypotheses
4. Fills identified knowledge gaps
5. Balances exploration vs exploitation

Cross-domain bridge: Math (optimization, UCB) ↔ Neuro (attention) ↔ Psychology (curiosity)
"""

import asyncio
import logging
import math
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class LearningStrategy(Enum):
    """Active learning strategies"""
    UNCERTAINTY_SAMPLING = "uncertainty"      # Focus on high-uncertainty areas
    CONTRADICTION_RESOLUTION = "contradiction"  # Resolve conflicting claims
    HYPOTHESIS_TESTING = "hypothesis"         # Test open hypotheses
    GAP_FILLING = "gap"                       # Fill knowledge gaps
    EXPLORATION = "exploration"               # Explore new areas
    EXPLOITATION = "exploitation"             # Deep dive known areas
    UCB = "ucb"                              # Upper Confidence Bound (balance)


@dataclass
class LearningTarget:
    """A prioritized learning target"""
    target_type: str  # domain, concept, contradiction, hypothesis, gap
    target_id: Optional[int] = None
    target_name: str = ""
    priority: float = 0.0
    uncertainty: float = 0.0
    search_queries: List[str] = field(default_factory=list)
    rationale: str = ""
    strategy: LearningStrategy = LearningStrategy.UNCERTAINTY_SAMPLING
    domains: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainUncertainty:
    """Uncertainty metrics for a domain"""
    domain_id: int
    domain_name: str
    claim_count: int
    avg_confidence: float
    confidence_variance: float
    contradiction_count: int
    unreplicated_ratio: float
    staleness_days: float  # Days since last learning
    exploration_score: float = 0.0  # UCB exploration bonus
    priority_score: float = 0.0


@dataclass
class ActiveLearningPlan:
    """A plan for what to learn next"""
    created_at: datetime = field(default_factory=datetime.now)
    strategy: LearningStrategy = LearningStrategy.UCB
    targets: List[LearningTarget] = field(default_factory=list)
    total_priority: float = 0.0
    rationale: str = ""
    expected_value: float = 0.0


class ActiveLearner:
    """
    Active Learning System for CIPHER.

    Implements various active learning strategies to maximize
    knowledge gain while minimizing wasted effort.

    Key algorithms:
    - Uncertainty Sampling: Focus on areas with low confidence
    - Upper Confidence Bound (UCB): Balance exploration/exploitation
    - Contradiction Resolution: Target conflicting claims
    - Gap Analysis: Fill identified knowledge gaps
    """

    # UCB exploration constant (higher = more exploration)
    UCB_C = 1.414  # sqrt(2), optimal for theoretical bounds

    # Minimum staleness threshold (days) before domain needs refresh
    STALENESS_THRESHOLD = 14

    # Weight factors for priority scoring
    WEIGHTS = {
        'uncertainty': 0.25,
        'contradiction_severity': 0.20,
        'staleness': 0.15,
        'gap_importance': 0.20,
        'cross_domain_potential': 0.20,
    }

    def __init__(self, db_connection_string: str):
        """
        Initialize the Active Learner.

        Args:
            db_connection_string: PostgreSQL connection string
        """
        self.db_connection_string = db_connection_string
        self._conn = None
        self._total_learning_rounds = 0
        self._domain_learning_counts: Dict[int, int] = {}

    async def connect(self):
        """Establish database connection."""
        import asyncpg
        self._conn = await asyncpg.connect(self.db_connection_string)
        await self._load_learning_history()

    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def _load_learning_history(self):
        """Load learning history for UCB calculations."""
        # Get total learning rounds
        self._total_learning_rounds = await self._conn.fetchval(
            "SELECT COUNT(DISTINCT session_id) FROM synthesis.learning_log"
        ) or 0

        # Get per-domain learning counts
        rows = await self._conn.fetch("""
            SELECT domain_id, COUNT(DISTINCT session_id) as count
            FROM synthesis.learning_log
            WHERE domain_id IS NOT NULL
            GROUP BY domain_id
        """)
        self._domain_learning_counts = {row['domain_id']: row['count'] for row in rows}

    async def compute_domain_uncertainty(self) -> List[DomainUncertainty]:
        """
        Compute uncertainty metrics for each domain.

        Returns:
            List of DomainUncertainty objects sorted by priority
        """
        uncertainties = []

        # Get domain-level stats
        rows = await self._conn.fetch("""
            SELECT
                d.id,
                d.name,
                COUNT(c.id) as claim_count,
                AVG(c.confidence) as avg_conf,
                VARIANCE(c.confidence) as var_conf,
                (
                    SELECT COUNT(*) FROM synthesis.contradictions ct
                    JOIN synthesis.claims c1 ON ct.claim_a_id = c1.id
                    WHERE d.id = ANY(c1.domains)
                    AND ct.resolution_status = 'unresolved'
                ) as contradiction_count,
                0.5 as unreplicated_ratio,
                (
                    SELECT EXTRACT(days FROM NOW() - MAX(ll.created_at))
                    FROM synthesis.learning_log ll
                    WHERE ll.domain_id = d.id
                ) as staleness
            FROM synthesis.domains d
            LEFT JOIN synthesis.claims c ON d.id = ANY(c.domains)
            GROUP BY d.id, d.name
            ORDER BY d.id
        """)

        for row in rows:
            domain_id = row['id']

            # Compute UCB exploration bonus
            n_total = max(1, self._total_learning_rounds)
            n_domain = max(1, self._domain_learning_counts.get(domain_id, 1))
            exploration_score = self.UCB_C * math.sqrt(math.log(n_total) / n_domain)

            # Compute overall priority score
            uncertainty = 1.0 - (row['avg_conf'] or 0.5)
            variance_score = min(1.0, (row['var_conf'] or 0) * 4)  # Scale variance
            contradiction_score = min(1.0, (row['contradiction_count'] or 0) / 10)
            staleness_score = min(1.0, float(row['staleness'] or 0) / 30)
            unreplicated_score = float(row['unreplicated_ratio'] or 0.5)

            priority = (
                self.WEIGHTS['uncertainty'] * uncertainty +
                self.WEIGHTS['uncertainty'] * variance_score +
                self.WEIGHTS['contradiction_severity'] * contradiction_score +
                self.WEIGHTS['staleness'] * staleness_score +
                self.WEIGHTS['uncertainty'] * unreplicated_score +
                exploration_score * 0.1  # UCB bonus
            )

            uncertainties.append(DomainUncertainty(
                domain_id=domain_id,
                domain_name=row['name'],
                claim_count=row['claim_count'] or 0,
                avg_confidence=row['avg_conf'] or 0.5,
                confidence_variance=row['var_conf'] or 0.0,
                contradiction_count=row['contradiction_count'] or 0,
                unreplicated_ratio=row['unreplicated_ratio'] or 0.5,
                staleness_days=row['staleness'] or 0,
                exploration_score=exploration_score,
                priority_score=priority
            ))

        # Sort by priority (descending)
        uncertainties.sort(key=lambda x: x.priority_score, reverse=True)
        return uncertainties

    async def get_unresolved_contradictions(
        self,
        limit: int = 20
    ) -> List[LearningTarget]:
        """
        Get unresolved contradictions as learning targets.

        Returns:
            List of LearningTarget objects for contradiction resolution
        """
        rows = await self._conn.fetch("""
            SELECT
                ct.id,
                ct.contradiction_type,
                c1.claim_text as claim_a,
                c2.claim_text as claim_b,
                c1.domains as domains_a,
                c2.domains as domains_b,
                s1.title as source_a,
                s2.title as source_b
            FROM synthesis.contradictions ct
            JOIN synthesis.claims c1 ON ct.claim_a_id = c1.id
            JOIN synthesis.claims c2 ON ct.claim_b_id = c2.id
            LEFT JOIN synthesis.sources s1 ON c1.source_id = s1.id
            LEFT JOIN synthesis.sources s2 ON c2.source_id = s2.id
            WHERE ct.resolution_status = 'unresolved'
            ORDER BY ct.created_at DESC
            LIMIT $1
        """, limit)

        targets = []
        for row in rows:
            # Generate search queries to find resolving papers
            claim_a_short = row['claim_a'][:100] if row['claim_a'] else ""
            claim_b_short = row['claim_b'][:100] if row['claim_b'] else ""

            # Extract key terms for search
            queries = self._generate_resolution_queries(claim_a_short, claim_b_short)

            # Combine domains
            domains = list(set(
                (row['domains_a'] or []) + (row['domains_b'] or [])
            ))

            targets.append(LearningTarget(
                target_type='contradiction',
                target_id=row['id'],
                target_name=f"Contradiction: {row['contradiction_type']}",
                priority=row['severity'] or 0.5,
                uncertainty=1.0,  # Contradictions are maximally uncertain
                search_queries=queries,
                rationale=f"Resolve conflict between: '{claim_a_short}...' and '{claim_b_short}...'",
                strategy=LearningStrategy.CONTRADICTION_RESOLUTION,
                domains=domains,
                metadata={
                    'claim_a': row['claim_a'],
                    'claim_b': row['claim_b'],
                    'source_a': row['source_a'],
                    'source_b': row['source_b'],
                }
            ))

        return targets

    async def get_open_hypotheses(
        self,
        limit: int = 20
    ) -> List[LearningTarget]:
        """
        Get open hypotheses that need testing.

        Returns:
            List of LearningTarget objects for hypothesis testing
        """
        rows = await self._conn.fetch("""
            SELECT
                h.id,
                h.hypothesis_text,
                h.domains,
                h.priority,
                h.status,
                h.testable,
                p.pattern_name
            FROM synthesis.hypotheses h
            LEFT JOIN synthesis.patterns p ON h.source_pattern_id = p.id
            WHERE h.status IN ('proposed', 'testing')
            AND h.testable = TRUE
            ORDER BY h.priority DESC
            LIMIT $1
        """, limit)

        targets = []
        for row in rows:
            # Generate search queries to test hypothesis
            queries = self._generate_hypothesis_queries(row['hypothesis_text'])

            targets.append(LearningTarget(
                target_type='hypothesis',
                target_id=row['id'],
                target_name=f"Hypothesis: {row['hypothesis_text'][:60]}...",
                priority=row['priority'] or 0.5,
                uncertainty=0.8,  # Hypotheses have high uncertainty
                search_queries=queries,
                rationale=f"Find evidence for/against: {row['hypothesis_text'][:100]}",
                strategy=LearningStrategy.HYPOTHESIS_TESTING,
                domains=row['domains'] or [],
                metadata={
                    'hypothesis': row['hypothesis_text'],
                    'status': row['status'],
                    'source_pattern': row['pattern_name'],
                }
            ))

        return targets

    async def get_knowledge_gaps(
        self,
        limit: int = 20
    ) -> List[LearningTarget]:
        """
        Get open knowledge gaps to fill.

        Returns:
            List of LearningTarget objects for gap filling
        """
        rows = await self._conn.fetch("""
            SELECT
                g.id,
                g.gap_description,
                g.domains,
                g.importance,
                g.tractability,
                g.research_directions
            FROM synthesis.gaps g
            WHERE g.status = 'open'
            ORDER BY (g.importance * g.tractability) DESC
            LIMIT $1
        """, limit)

        targets = []
        for row in rows:
            # Priority is importance × tractability
            priority = (row['importance'] or 0.5) * (row['tractability'] or 0.5)

            # Generate search queries from gap description and research directions
            queries = self._generate_gap_queries(
                row['gap_description'],
                row['research_directions'] or []
            )

            targets.append(LearningTarget(
                target_type='gap',
                target_id=row['id'],
                target_name=f"Gap: {row['gap_description'][:60]}...",
                priority=priority,
                uncertainty=0.9,  # Gaps represent missing knowledge
                search_queries=queries,
                rationale=f"Fill knowledge gap: {row['gap_description'][:100]}",
                strategy=LearningStrategy.GAP_FILLING,
                domains=row['domains'] or [],
                metadata={
                    'description': row['gap_description'],
                    'importance': row['importance'],
                    'tractability': row['tractability'],
                    'directions': row['research_directions'],
                }
            ))

        return targets

    async def get_low_confidence_concepts(
        self,
        threshold: float = 0.4,
        limit: int = 30
    ) -> List[LearningTarget]:
        """
        Get concepts/entities with low confidence claims.

        Returns:
            List of LearningTarget objects for uncertainty reduction
        """
        # Find entities that appear in low-confidence claims
        rows = await self._conn.fetch("""
            SELECT
                entity,
                COUNT(*) as claim_count,
                AVG(c.confidence) as avg_confidence,
                ARRAY_AGG(DISTINCT d) as domains
            FROM synthesis.claims c,
                 jsonb_array_elements_text(c.entities) as entity,
                 unnest(c.domains) as d
            WHERE c.confidence < $1
            AND c.entities IS NOT NULL
            AND jsonb_typeof(c.entities) = 'array'
            GROUP BY entity
            HAVING COUNT(*) >= 2 AND length(entity) > 3
            ORDER BY avg_confidence ASC, COUNT(*) DESC
            LIMIT $2
        """, threshold, limit)

        targets = []
        for row in rows:
            entity = row['entity']
            queries = [
                f'"{entity}" review',
                f'"{entity}" meta-analysis',
                f'"{entity}" replication',
                entity
            ]

            targets.append(LearningTarget(
                target_type='concept',
                target_id=None,
                target_name=f"Concept: {entity}",
                priority=1.0 - (row['avg_confidence'] or 0.5),
                uncertainty=1.0 - (row['avg_confidence'] or 0.5),
                search_queries=queries,
                rationale=f"Low confidence ({row['avg_confidence']:.2f}) across {row['claim_count']} claims",
                strategy=LearningStrategy.UNCERTAINTY_SAMPLING,
                domains=[int(d) for d in row['domains'] if d],
                metadata={
                    'claim_count': row['claim_count'],
                    'avg_confidence': row['avg_confidence'],
                }
            ))

        return targets

    async def create_learning_plan(
        self,
        strategy: LearningStrategy = LearningStrategy.UCB,
        max_targets: int = 10
    ) -> ActiveLearningPlan:
        """
        Create a prioritized learning plan.

        Args:
            strategy: Which strategy to use for prioritization
            max_targets: Maximum number of targets in plan

        Returns:
            ActiveLearningPlan with prioritized targets
        """
        all_targets: List[LearningTarget] = []

        if strategy == LearningStrategy.UCB:
            # UCB: Balance all strategies
            domain_uncertainties = await self.compute_domain_uncertainty()
            contradictions = await self.get_unresolved_contradictions(limit=5)
            hypotheses = await self.get_open_hypotheses(limit=5)
            gaps = await self.get_knowledge_gaps(limit=5)
            concepts = await self.get_low_confidence_concepts(limit=5)

            # Add domain-level targets
            for du in domain_uncertainties[:3]:
                all_targets.append(LearningTarget(
                    target_type='domain',
                    target_id=du.domain_id,
                    target_name=du.domain_name,
                    priority=du.priority_score,
                    uncertainty=1.0 - du.avg_confidence,
                    search_queries=[],  # Domain learner handles queries
                    rationale=f"Domain needs attention: conf={du.avg_confidence:.2f}, "
                             f"contradictions={du.contradiction_count}, "
                             f"staleness={du.staleness_days:.0f}d",
                    strategy=LearningStrategy.UCB,
                    domains=[du.domain_id],
                    metadata={
                        'claim_count': du.claim_count,
                        'exploration_score': du.exploration_score,
                    }
                ))

            all_targets.extend(contradictions)
            all_targets.extend(hypotheses)
            all_targets.extend(gaps)
            all_targets.extend(concepts)

        elif strategy == LearningStrategy.UNCERTAINTY_SAMPLING:
            concepts = await self.get_low_confidence_concepts(limit=max_targets)
            all_targets.extend(concepts)

        elif strategy == LearningStrategy.CONTRADICTION_RESOLUTION:
            contradictions = await self.get_unresolved_contradictions(limit=max_targets)
            all_targets.extend(contradictions)

        elif strategy == LearningStrategy.HYPOTHESIS_TESTING:
            hypotheses = await self.get_open_hypotheses(limit=max_targets)
            all_targets.extend(hypotheses)

        elif strategy == LearningStrategy.GAP_FILLING:
            gaps = await self.get_knowledge_gaps(limit=max_targets)
            all_targets.extend(gaps)

        elif strategy == LearningStrategy.EXPLORATION:
            # Prioritize domains with high exploration score (least visited)
            domain_uncertainties = await self.compute_domain_uncertainty()
            domain_uncertainties.sort(key=lambda x: x.exploration_score, reverse=True)

            for du in domain_uncertainties[:max_targets]:
                all_targets.append(LearningTarget(
                    target_type='domain',
                    target_id=du.domain_id,
                    target_name=du.domain_name,
                    priority=du.exploration_score,
                    uncertainty=1.0,
                    search_queries=[],
                    rationale=f"Exploration: domain underexplored (score={du.exploration_score:.2f})",
                    strategy=LearningStrategy.EXPLORATION,
                    domains=[du.domain_id],
                ))

        elif strategy == LearningStrategy.EXPLOITATION:
            # Prioritize domains with highest claim count but uncertainty
            domain_uncertainties = await self.compute_domain_uncertainty()
            domain_uncertainties.sort(
                key=lambda x: x.claim_count * (1 - x.avg_confidence),
                reverse=True
            )

            for du in domain_uncertainties[:max_targets]:
                all_targets.append(LearningTarget(
                    target_type='domain',
                    target_id=du.domain_id,
                    target_name=du.domain_name,
                    priority=du.claim_count * (1 - du.avg_confidence) / 100,
                    uncertainty=1.0 - du.avg_confidence,
                    search_queries=[],
                    rationale=f"Exploitation: deep dive into {du.domain_name} ({du.claim_count} claims)",
                    strategy=LearningStrategy.EXPLOITATION,
                    domains=[du.domain_id],
                ))

        # Sort all targets by priority and take top N
        all_targets.sort(key=lambda x: x.priority, reverse=True)
        selected_targets = all_targets[:max_targets]

        # Calculate expected value (sum of priority × uncertainty)
        expected_value = sum(t.priority * t.uncertainty for t in selected_targets)
        total_priority = sum(t.priority for t in selected_targets)

        # Build rationale
        target_types = {}
        for t in selected_targets:
            target_types[t.target_type] = target_types.get(t.target_type, 0) + 1

        type_summary = ", ".join(f"{v} {k}s" for k, v in target_types.items())
        rationale = f"Plan using {strategy.value} strategy: {type_summary}"

        return ActiveLearningPlan(
            strategy=strategy,
            targets=selected_targets,
            total_priority=total_priority,
            rationale=rationale,
            expected_value=expected_value
        )

    async def record_learning_round(
        self,
        domain_id: Optional[int],
        papers_processed: int,
        claims_extracted: int,
        connections_found: int
    ):
        """Record a learning round for UCB updates."""
        await self._conn.execute("""
            INSERT INTO synthesis.learning_log
            (domain_id, action, sources_processed, claims_extracted, connections_found)
            VALUES ($1, 'active_learning', $2, $3, $4)
        """, domain_id, papers_processed, claims_extracted, connections_found)

        self._total_learning_rounds += 1
        if domain_id:
            self._domain_learning_counts[domain_id] = \
                self._domain_learning_counts.get(domain_id, 0) + 1

    def _generate_resolution_queries(
        self,
        claim_a: str,
        claim_b: str
    ) -> List[str]:
        """Generate search queries to find papers that could resolve contradiction."""
        # Extract key nouns/concepts (simple approach)
        import re
        words_a = set(re.findall(r'\b[a-zA-Z]{4,}\b', claim_a.lower()))
        words_b = set(re.findall(r'\b[a-zA-Z]{4,}\b', claim_b.lower()))

        # Common words might be the core topic
        common = words_a & words_b
        diff_a = words_a - common
        diff_b = words_b - common

        queries = []

        # Search for meta-analyses/reviews on common topic
        if common:
            common_terms = ' '.join(list(common)[:3])
            queries.append(f'{common_terms} meta-analysis')
            queries.append(f'{common_terms} systematic review')

        # Search for both perspectives
        if diff_a and diff_b:
            queries.append(f'{" ".join(list(diff_a)[:2])} vs {" ".join(list(diff_b)[:2])}')

        # Replication studies
        if common:
            queries.append(f'{" ".join(list(common)[:2])} replication')

        return queries[:4]  # Limit to 4 queries

    def _generate_hypothesis_queries(self, hypothesis: str) -> List[str]:
        """Generate search queries to test a hypothesis."""
        import re
        words = re.findall(r'\b[a-zA-Z]{4,}\b', hypothesis.lower())
        key_terms = ' '.join(words[:4])

        return [
            f'{key_terms} evidence',
            f'{key_terms} experiment',
            f'{key_terms} study',
            key_terms,
        ]

    def _generate_gap_queries(
        self,
        description: str,
        directions: List[str]
    ) -> List[str]:
        """Generate search queries to fill a knowledge gap."""
        import re
        queries = []

        # From description
        words = re.findall(r'\b[a-zA-Z]{4,}\b', description.lower())
        if words:
            queries.append(' '.join(words[:4]))

        # From research directions
        for direction in directions[:2]:
            dir_words = re.findall(r'\b[a-zA-Z]{4,}\b', direction.lower())
            if dir_words:
                queries.append(' '.join(dir_words[:3]))

        # Recent reviews
        if words:
            queries.append(f'{" ".join(words[:2])} recent advances')

        return queries[:4]


# Convenience functions
async def get_active_learner(db_connection_string: str) -> ActiveLearner:
    """Get a connected ActiveLearner instance."""
    learner = ActiveLearner(db_connection_string)
    await learner.connect()
    return learner


async def create_learning_plan(
    db_connection_string: str,
    strategy: str = "ucb"
) -> ActiveLearningPlan:
    """Create a learning plan using the specified strategy."""
    strategy_map = {
        'ucb': LearningStrategy.UCB,
        'uncertainty': LearningStrategy.UNCERTAINTY_SAMPLING,
        'contradiction': LearningStrategy.CONTRADICTION_RESOLUTION,
        'hypothesis': LearningStrategy.HYPOTHESIS_TESTING,
        'gap': LearningStrategy.GAP_FILLING,
        'exploration': LearningStrategy.EXPLORATION,
        'exploitation': LearningStrategy.EXPLOITATION,
    }

    learner = await get_active_learner(db_connection_string)
    try:
        return await learner.create_learning_plan(
            strategy=strategy_map.get(strategy, LearningStrategy.UCB)
        )
    finally:
        await learner.close()
