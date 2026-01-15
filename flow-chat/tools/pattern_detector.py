"""
CIPHER Cross-Domain Pattern Detector

The synthesis engine that finds hidden connections across domains.
This is where the magic happens - discovering that a concept in mathematics
relates to a phenomenon in neuroscience, or that a pattern in art
reflects principles from biology.

Key insight: The most valuable knowledge often lies at the intersections
of disciplines. We actively seek these bridging patterns.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
import math

import asyncpg

from .cipher_brain import Domain, Claim, Connection, Pattern, STOPWORDS
from .hash_learning import HashLearning

logger = logging.getLogger(__name__)


@dataclass
class ConceptCluster:
    """A cluster of related concepts across domains"""
    name: str
    concepts: Set[str]
    domains: Set[Domain]
    claims: List[int]  # Claim IDs
    coherence_score: float  # How tightly related
    bridging_score: float   # How much it bridges domains


@dataclass
class CrossDomainInsight:
    """A significant cross-domain discovery"""
    title: str
    description: str
    source_domain: Domain
    target_domain: Domain
    mechanism: str  # How they connect
    confidence: float
    novelty: float
    implications: List[str]
    research_questions: List[str]
    supporting_claims: List[int]


class PatternDetector:
    """
    Detects patterns and connections across the 6 domains.

    Uses several strategies:
    1. Entity co-occurrence: Same entities appearing in different domains
    2. Structural analogy: Similar patterns in different contexts
    3. Causal chain bridging: Cause in one domain, effect in another
    4. Conceptual isomorphism: Same abstract structure, different instantiation
    5. Gap filling: Missing connection that would complete a pattern
    """

    def __init__(self, db_url: str):
        """
        Initialize the pattern detector.

        Args:
            db_url: PostgreSQL connection string
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
        self.hash_learner = HashLearning()

        # Cache for efficiency
        self._entity_index: Dict[str, List[int]] = {}  # entity -> claim_ids
        self._domain_claims: Dict[Domain, List[int]] = {}

        # Cross-domain concept mappings (known bridges)
        self.known_bridges = {
            'information': [Domain.MATHEMATICS, Domain.NEUROSCIENCES, Domain.BIOLOGY],
            'entropy': [Domain.MATHEMATICS, Domain.BIOLOGY, Domain.ART],
            'network': [Domain.MATHEMATICS, Domain.NEUROSCIENCES, Domain.BIOLOGY],
            'prediction': [Domain.NEUROSCIENCES, Domain.PSYCHOLOGY, Domain.MEDICINE],
            'optimization': [Domain.MATHEMATICS, Domain.BIOLOGY, Domain.NEUROSCIENCES],
            'learning': [Domain.NEUROSCIENCES, Domain.PSYCHOLOGY, Domain.MATHEMATICS],
            'complexity': [Domain.MATHEMATICS, Domain.BIOLOGY, Domain.ART],
            'emergence': [Domain.BIOLOGY, Domain.NEUROSCIENCES, Domain.ART],
            'pattern': [Domain.MATHEMATICS, Domain.NEUROSCIENCES, Domain.ART],
            'representation': [Domain.MATHEMATICS, Domain.NEUROSCIENCES, Domain.PSYCHOLOGY],
            'feedback': [Domain.BIOLOGY, Domain.NEUROSCIENCES, Domain.PSYCHOLOGY],
            'adaptation': [Domain.BIOLOGY, Domain.PSYCHOLOGY, Domain.MEDICINE],
            'hierarchy': [Domain.MATHEMATICS, Domain.BIOLOGY, Domain.NEUROSCIENCES],
            'symmetry': [Domain.MATHEMATICS, Domain.BIOLOGY, Domain.ART],
            'rhythm': [Domain.BIOLOGY, Domain.NEUROSCIENCES, Domain.ART],
        }

    async def connect(self):
        """Establish database connection."""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=2,
            max_size=10
        )
        await self._build_indices()

    async def close(self):
        """Close database connection."""
        if self.pool:
            await self.pool.close()

    async def _build_indices(self):
        """Build in-memory indices for fast lookup."""
        async with self.pool.acquire() as conn:
            # Index entities to claims
            rows = await conn.fetch('''
                SELECT id, entities, domains
                FROM synthesis.claims
                WHERE entities IS NOT NULL
            ''')

            for row in rows:
                entities = json.loads(row['entities']) if row['entities'] else []
                domains = [Domain(d) for d in (row['domains'] or [])]

                for entity in entities:
                    entity_lower = entity.lower().strip()
                    # Skip stopwords, short entities, and purely numeric entities
                    if (entity_lower in STOPWORDS or
                        len(entity_lower) < 3 or
                        entity_lower.isdigit()):
                        continue
                    if entity_lower not in self._entity_index:
                        self._entity_index[entity_lower] = []
                    self._entity_index[entity_lower].append(row['id'])

                for domain in domains:
                    if domain not in self._domain_claims:
                        self._domain_claims[domain] = []
                    self._domain_claims[domain].append(row['id'])

        logger.info(f"Built indices: {len(self._entity_index)} entities, "
                   f"{len(self._domain_claims)} domains")

    async def detect_all_patterns(self) -> List[CrossDomainInsight]:
        """
        Run all pattern detection strategies.

        Returns list of cross-domain insights discovered.
        """
        insights = []

        # Strategy 1: Entity bridging
        entity_insights = await self._detect_entity_bridges()
        insights.extend(entity_insights)

        # Strategy 2: Known concept bridges
        bridge_insights = await self._detect_concept_bridges()
        insights.extend(bridge_insights)

        # Strategy 3: Structural analogies
        analogy_insights = await self._detect_structural_analogies()
        insights.extend(analogy_insights)

        # Strategy 4: Gap analysis
        gap_insights = await self._detect_knowledge_gaps()
        insights.extend(gap_insights)

        # Deduplicate and rank
        unique_insights = self._deduplicate_insights(insights)
        ranked_insights = sorted(
            unique_insights,
            key=lambda x: x.novelty * x.confidence,
            reverse=True
        )

        return ranked_insights

    async def _detect_entity_bridges(self) -> List[CrossDomainInsight]:
        """
        Find entities that appear in multiple domains.

        These are natural bridges - the same concept manifesting
        in different fields.
        """
        insights = []

        for entity, claim_ids in self._entity_index.items():
            if len(claim_ids) < 2:
                continue

            # Skip stopwords, short entities, and purely numeric entities
            entity_lower = entity.lower().strip()
            if (entity_lower in STOPWORDS or
                len(entity_lower) < 3 or
                entity_lower.isdigit() or
                all(word in STOPWORDS for word in entity_lower.split())):
                continue

            # Get domains for these claims
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT id, claim_text, domains, confidence
                    FROM synthesis.claims
                    WHERE id = ANY($1)
                ''', claim_ids)

            domains = set()
            claims_by_domain: Dict[Domain, List[Dict]] = defaultdict(list)

            for row in rows:
                claim_domains = [Domain(d) for d in (row['domains'] or [])]
                for domain in claim_domains:
                    domains.add(domain)
                    claims_by_domain[domain].append({
                        'id': row['id'],
                        'text': row['claim_text'],
                        'confidence': row['confidence']
                    })

            # Only interested if entity spans 2+ domains
            if len(domains) < 2:
                continue

            # Create insight for significant bridges
            domain_list = list(domains)
            for i, source_domain in enumerate(domain_list):
                for target_domain in domain_list[i+1:]:
                    source_claims = claims_by_domain[source_domain]
                    target_claims = claims_by_domain[target_domain]

                    if not source_claims or not target_claims:
                        continue

                    # Calculate confidence based on claim quality
                    avg_confidence = (
                        sum(c['confidence'] for c in source_claims) / len(source_claims) +
                        sum(c['confidence'] for c in target_claims) / len(target_claims)
                    ) / 2

                    insights.append(CrossDomainInsight(
                        title=f"'{entity.title()}' bridges {source_domain.name} and {target_domain.name}",
                        description=(
                            f"The concept '{entity}' appears in both {source_domain.name} "
                            f"and {target_domain.name}, suggesting a potential cross-domain connection. "
                            f"Found {len(source_claims)} claims in {source_domain.name} and "
                            f"{len(target_claims)} claims in {target_domain.name}."
                        ),
                        source_domain=source_domain,
                        target_domain=target_domain,
                        mechanism=f"Shared entity: {entity}",
                        confidence=avg_confidence,
                        novelty=0.6 if len(domains) == 2 else 0.8,
                        implications=[
                            f"Investigate whether '{entity}' has the same meaning across domains",
                            f"Look for methodological transfer from {source_domain.name} to {target_domain.name}"
                        ],
                        research_questions=[
                            f"Is '{entity}' in {source_domain.name} causally related to '{entity}' in {target_domain.name}?",
                            f"Can insights about '{entity}' from {source_domain.name} inform {target_domain.name} research?"
                        ],
                        supporting_claims=[c['id'] for c in source_claims + target_claims]
                    ))

        return insights

    async def _detect_concept_bridges(self) -> List[CrossDomainInsight]:
        """
        Use known cross-domain concepts to find bridges.

        These are concepts known to span multiple fields.
        """
        insights = []

        for concept, expected_domains in self.known_bridges.items():
            # Search for claims mentioning this concept
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT id, claim_text, domains, confidence
                    FROM synthesis.claims
                    WHERE LOWER(claim_text) LIKE $1
                    LIMIT 100
                ''', f'%{concept}%')

            if len(rows) < 2:
                continue

            # Group by domain
            found_domains: Dict[Domain, List[Dict]] = defaultdict(list)
            for row in rows:
                claim_domains = [Domain(d) for d in (row['domains'] or [])]
                for domain in claim_domains:
                    if domain in expected_domains:
                        found_domains[domain].append({
                            'id': row['id'],
                            'text': row['claim_text'],
                            'confidence': row['confidence']
                        })

            # Create insights for domain pairs
            domains_found = list(found_domains.keys())
            if len(domains_found) >= 2:
                for i, source in enumerate(domains_found):
                    for target in domains_found[i+1:]:
                        claims = found_domains[source] + found_domains[target]
                        avg_confidence = sum(c['confidence'] for c in claims) / len(claims)

                        insights.append(CrossDomainInsight(
                            title=f"'{concept.title()}' as bridge between {source.name} and {target.name}",
                            description=(
                                f"The concept '{concept}' is known to bridge multiple domains. "
                                f"Found evidence in both {source.name} ({len(found_domains[source])} claims) "
                                f"and {target.name} ({len(found_domains[target])} claims)."
                            ),
                            source_domain=source,
                            target_domain=target,
                            mechanism=f"Known bridging concept: {concept}",
                            confidence=avg_confidence * 0.9,  # Slight discount for prior knowledge
                            novelty=0.5,  # Lower novelty since it's a known bridge
                            implications=[
                                f"Apply {source.name} understanding of '{concept}' to {target.name}",
                                f"Look for unified theory of '{concept}' across domains"
                            ],
                            research_questions=[
                                f"What distinguishes '{concept}' in {source.name} from {target.name}?",
                                f"Is there a more fundamental principle underlying '{concept}'?"
                            ],
                            supporting_claims=[c['id'] for c in claims]
                        ))

        return insights

    async def _detect_structural_analogies(self) -> List[CrossDomainInsight]:
        """
        Find structural analogies between domains.

        Look for claims with similar structure but different content.
        """
        insights = []

        # Get claims with high confidence
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT id, claim_text, claim_type, domains, entities, confidence
                FROM synthesis.claims
                WHERE confidence >= 0.6
                ORDER BY confidence DESC
                LIMIT 500
            ''')

        # Group by claim type
        by_type: Dict[str, List[Dict]] = defaultdict(list)
        for row in rows:
            by_type[row['claim_type']].append({
                'id': row['id'],
                'text': row['claim_text'],
                'domains': [Domain(d) for d in (row['domains'] or [])],
                'entities': json.loads(row['entities']) if row['entities'] else [],
                'confidence': row['confidence']
            })

        # Look for analogies within same claim type
        for claim_type, claims in by_type.items():
            if claim_type != 'finding':  # Focus on findings for now
                continue

            for i, claim1 in enumerate(claims):
                for claim2 in claims[i+1:]:
                    # Different domains?
                    domains1 = set(claim1['domains'])
                    domains2 = set(claim2['domains'])

                    if domains1 == domains2 or not domains1 or not domains2:
                        continue

                    # Check for structural similarity
                    similarity = self._compute_structural_similarity(
                        claim1['text'], claim2['text']
                    )

                    if similarity > 0.5:
                        insights.append(CrossDomainInsight(
                            title=f"Structural analogy between {list(domains1)[0].name} and {list(domains2)[0].name}",
                            description=(
                                f"Found structurally similar claims across domains:\n"
                                f"- {list(domains1)[0].name}: '{claim1['text'][:100]}...'\n"
                                f"- {list(domains2)[0].name}: '{claim2['text'][:100]}...'"
                            ),
                            source_domain=list(domains1)[0],
                            target_domain=list(domains2)[0],
                            mechanism=f"Structural similarity score: {similarity:.2f}",
                            confidence=(claim1['confidence'] + claim2['confidence']) / 2,
                            novelty=0.7 + similarity * 0.2,
                            implications=[
                                "This structural parallel may indicate a deeper principle",
                                "Methods from one domain may transfer to the other"
                            ],
                            research_questions=[
                                "What generates this structural similarity?",
                                "Are there other instances of this pattern?"
                            ],
                            supporting_claims=[claim1['id'], claim2['id']]
                        ))

        return insights[:20]  # Limit to top analogies

    def _compute_structural_similarity(self, text1: str, text2: str) -> float:
        """
        Compute structural similarity between two claim texts.

        Uses pattern matching to find similar sentence structures.
        """
        # Simple approach: compare word patterns
        # A more sophisticated version would use parse trees

        # Extract pattern words (verbs, relations)
        pattern_words = {'increase', 'decrease', 'cause', 'correlate', 'predict',
                        'affect', 'influence', 'lead', 'result', 'produce',
                        'enhance', 'reduce', 'modulate', 'regulate'}

        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        patterns1 = words1 & pattern_words
        patterns2 = words2 & pattern_words

        if not patterns1 or not patterns2:
            return 0.0

        # Jaccard similarity of pattern words
        intersection = len(patterns1 & patterns2)
        union = len(patterns1 | patterns2)

        return intersection / union if union > 0 else 0.0

    async def _detect_knowledge_gaps(self) -> List[CrossDomainInsight]:
        """
        Find knowledge gaps that could be filled by cross-domain transfer.

        Looks for:
        - Questions in one domain answered in another
        - Methods in one domain applicable to another's problems
        """
        insights = []

        # Get hypotheses (represent open questions)
        async with self.pool.acquire() as conn:
            hypotheses = await conn.fetch('''
                SELECT id, hypothesis_text, domains
                FROM synthesis.hypotheses
                WHERE status = 'proposed'
                LIMIT 100
            ''')

            # Get high-confidence findings (potential answers)
            findings = await conn.fetch('''
                SELECT id, claim_text, domains, entities
                FROM synthesis.claims
                WHERE claim_type = 'finding' AND confidence >= 0.7
                LIMIT 500
            ''')

        # For each hypothesis, look for relevant findings in OTHER domains
        for hyp in hypotheses:
            hyp_domains = set(Domain(d) for d in (hyp['domains'] or []))
            hyp_text = hyp['hypothesis_text'].lower()

            for finding in findings:
                finding_domains = set(Domain(d) for d in (finding['domains'] or []))

                # Only interested in cross-domain
                if hyp_domains & finding_domains:
                    continue

                # Check for conceptual relevance
                finding_text = finding['claim_text'].lower()
                entities = json.loads(finding['entities']) if finding['entities'] else []

                # Simple relevance: shared words
                hyp_words = set(hyp_text.split())
                finding_words = set(finding_text.split())
                common_words = hyp_words & finding_words

                # Filter out common stopwords
                stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be',
                            'to', 'of', 'and', 'in', 'that', 'this', 'for', 'with'}
                common_meaningful = common_words - stopwords

                if len(common_meaningful) >= 3:
                    source = list(finding_domains)[0] if finding_domains else Domain.BIOLOGY
                    target = list(hyp_domains)[0] if hyp_domains else Domain.BIOLOGY

                    insights.append(CrossDomainInsight(
                        title=f"Potential knowledge transfer: {source.name} -> {target.name}",
                        description=(
                            f"A finding in {source.name} may address a hypothesis in {target.name}:\n"
                            f"- Hypothesis: '{hyp['hypothesis_text'][:100]}...'\n"
                            f"- Finding: '{finding['claim_text'][:100]}...'"
                        ),
                        source_domain=source,
                        target_domain=target,
                        mechanism=f"Shared concepts: {', '.join(list(common_meaningful)[:5])}",
                        confidence=0.5,  # Speculative
                        novelty=0.8,  # High novelty if valid
                        implications=[
                            f"Finding from {source.name} may validate or inform {target.name} hypothesis",
                            "Cross-domain collaboration recommended"
                        ],
                        research_questions=[
                            f"Does the {source.name} finding apply in {target.name} context?",
                            "What modifications are needed for cross-domain transfer?"
                        ],
                        supporting_claims=[finding['id']]
                    ))

        return insights[:20]

    def _deduplicate_insights(self, insights: List[CrossDomainInsight]) -> List[CrossDomainInsight]:
        """Remove duplicate or highly similar insights."""
        unique = []
        seen_hashes = set()

        for insight in insights:
            # Hash based on key features
            key = f"{insight.source_domain}|{insight.target_domain}|{insight.mechanism[:50]}"
            hash_key = self.hash_learner.compute_shake256(key)[:16]

            if hash_key not in seen_hashes:
                seen_hashes.add(hash_key)
                unique.append(insight)

        return unique

    async def save_insights(self, insights: List[CrossDomainInsight]):
        """Save discovered insights to database."""
        async with self.pool.acquire() as conn:
            for insight in insights:
                await conn.execute('''
                    INSERT INTO synthesis.patterns
                    (pattern_name, pattern_type, description, domains, claim_ids,
                     confidence, novelty_score, implications, questions_raised, entropy_hash)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ''',
                    insight.title,
                    'cross_domain',
                    insight.description,
                    [insight.source_domain.value, insight.target_domain.value],
                    insight.supporting_claims,
                    insight.confidence,
                    insight.novelty,
                    '\n'.join(insight.implications),
                    insight.research_questions,
                    self.hash_learner.compute_shake256(insight.description)
                )

    async def get_domain_overlap_matrix(self) -> Dict[str, Dict[str, int]]:
        """
        Compute matrix showing how domains connect.

        Returns dict[domain1][domain2] = number of connections
        """
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT source_domain, target_domain, COUNT(*) as count
                FROM synthesis.connections
                WHERE cross_domain = TRUE
                GROUP BY source_domain, target_domain
            ''')

        matrix = defaultdict(lambda: defaultdict(int))
        for row in rows:
            if row['source_domain'] and row['target_domain']:
                source = Domain(row['source_domain']).name
                target = Domain(row['target_domain']).name
                matrix[source][target] = row['count']

        return dict(matrix)

    async def generate_synthesis_report(self) -> str:
        """Generate a report of cross-domain synthesis."""
        insights = await self.detect_all_patterns()
        matrix = await self.get_domain_overlap_matrix()

        report = ["# CIPHER Cross-Domain Synthesis Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Domain overlap section
        report.append("## Domain Interconnection Matrix")
        report.append("Showing number of cross-domain connections:")
        report.append("")

        domains = [d.name for d in Domain]
        report.append("| | " + " | ".join(domains) + " |")
        report.append("|" + "---|" * (len(domains) + 1))

        for d1 in domains:
            row = [d1]
            for d2 in domains:
                count = matrix.get(d1, {}).get(d2, 0)
                row.append(str(count) if count > 0 else "-")
            report.append("| " + " | ".join(row) + " |")

        report.append("")

        # Top insights section
        report.append("## Top Cross-Domain Insights")
        report.append("")

        for i, insight in enumerate(insights[:10], 1):
            report.append(f"### {i}. {insight.title}")
            report.append(f"**Confidence:** {insight.confidence:.2f} | **Novelty:** {insight.novelty:.2f}")
            report.append("")
            report.append(insight.description)
            report.append("")
            report.append("**Implications:**")
            for impl in insight.implications:
                report.append(f"- {impl}")
            report.append("")
            report.append("**Research Questions:**")
            for q in insight.research_questions:
                report.append(f"- {q}")
            report.append("")
            report.append("---")
            report.append("")

        return "\n".join(report)
