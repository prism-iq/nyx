"""
CIPHER BRAIN - Core Cognitive Engine

The central nervous system of Cipher. Orchestrates:
- Paper streaming from multiple sources
- Claim extraction and validation
- Cross-domain connection discovery
- Pattern recognition
- Hypothesis generation

Principles:
- Iron Code: "Evil must be fought wherever it is found"
- Free Energy Principle: Minimize prediction error
- Systematic Doubt: Every claim is questioned
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, AsyncIterator, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import re

import asyncpg

from .hash_learning import HashLearning, EntropyScore
from .embeddings import EmbeddingService, get_embedding_service
from .nlp_extractor import (
    NLPExtractor, get_nlp_extractor,
    ExtractedClaim as NLPClaim,
    ClaimType as NLPClaimType,
    EvidenceStrength as NLPEvidenceStrength,
    CausalRelation,
    ScientificEntity
)

logger = logging.getLogger(__name__)

# Stopwords to filter from pattern detection
STOPWORDS = frozenset({
    # Articles & determiners
    'a', 'an', 'the', 'this', 'that', 'these', 'those', 'some', 'any', 'all', 'each',
    # Pronouns
    'i', 'we', 'you', 'he', 'she', 'it', 'they', 'me', 'us', 'him', 'her', 'them',
    'my', 'our', 'your', 'his', 'its', 'their', 'mine', 'ours', 'yours', 'hers', 'theirs',
    'who', 'whom', 'whose', 'which', 'what', 'whoever', 'whatever',
    # Prepositions
    'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'out', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'of',
    # Conjunctions
    'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'not', 'only',
    'as', 'if', 'when', 'where', 'while', 'although', 'because', 'unless', 'until',
    # Common verbs
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'will', 'would', 'could', 'should', 'may', 'might',
    'must', 'shall', 'can', 'need', 'dare', 'ought', 'used', 'get', 'got', 'getting',
    # Common adverbs
    'very', 'really', 'just', 'also', 'still', 'already', 'always', 'never', 'ever',
    'often', 'sometimes', 'usually', 'perhaps', 'maybe', 'probably', 'certainly',
    'here', 'there', 'now', 'today', 'tomorrow', 'yesterday', 'soon', 'later',
    'how', 'why', 'well', 'however', 'therefore', 'thus', 'hence', 'moreover',
    # Common adjectives
    'other', 'another', 'such', 'own', 'same', 'different', 'new', 'old', 'good', 'bad',
    'first', 'last', 'next', 'few', 'many', 'much', 'more', 'most', 'less', 'least',
    'no', 'yes', 'true', 'false',
    # Numbers & quantifiers
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
    'several', 'various', 'certain', 'every',
    # Generic scientific terms (too common to be meaningful)
    'study', 'studies', 'research', 'result', 'results', 'method', 'methods',
    'data', 'analysis', 'effect', 'effects', 'level', 'levels', 'group', 'groups',
    'using', 'based', 'show', 'shows', 'shown', 'found', 'suggest', 'suggests',
    'indicate', 'indicates', 'observed', 'reported', 'compared', 'associated',
    'significant', 'significantly', 'increase', 'decrease', 'higher', 'lower',
    # Units and measurements (too generic)
    'cm', 'mm', 'kg', 'mg', 'ml', 'percent', 'percentage',
    # Other common words
    'use', 'case', 'cases', 'time', 'times', 'way', 'ways', 'work', 'works',
    'part', 'parts', 'place', 'number', 'point', 'points', 'fact', 'thing', 'things',
    'example', 'examples', 'type', 'types', 'form', 'forms', 'system', 'systems',
    'order', 'general', 'particular', 'specific', 'include', 'including', 'included',
})


class Domain(Enum):
    """The seven domains of expertise"""
    MATHEMATICS = 1
    NEUROSCIENCES = 2
    BIOLOGY = 3
    PSYCHOLOGY = 4
    MEDICINE = 5
    ART = 6
    PHILOSOPHY = 7


@dataclass
class Claim:
    """An extracted assertion from a paper"""
    text: str
    claim_type: str  # hypothesis, finding, method, definition, observation, conclusion
    confidence: float
    evidence_strength: str
    domains: List[Domain]
    source_id: Optional[int] = None
    entities: List[str] = field(default_factory=list)
    methodology: Optional[str] = None
    sample_size: Optional[int] = None
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    entropy_hash: Optional[str] = None
    embedding: Optional[List[float]] = None  # Semantic embedding vector
    causal_relations: List[Dict[str, Any]] = field(default_factory=list)  # Extracted causal relations
    hedging_markers: List[str] = field(default_factory=list)  # Uncertainty indicators
    negation: bool = False  # Whether claim is negated
    # Temporal tracking fields
    created_at: Optional[datetime] = None
    current_confidence: Optional[float] = None  # Confidence after decay/updates
    replication_status: str = "unreplicated"  # unreplicated, replicated, failed_replication, contested
    citation_count: int = 0
    status: str = "active"  # active, superseded, retracted, deprecated
    superseded_by: Optional[int] = None


@dataclass
class Connection:
    """A link between two claims"""
    source_claim_id: int
    target_claim_id: int
    connection_type: str  # supports, contradicts, extends, analogous, causal
    strength: float
    cross_domain: bool
    reasoning: str
    entropy_score: float


@dataclass
class Pattern:
    """A higher-order structure discovered in knowledge"""
    name: str
    pattern_type: str  # convergence, divergence, cycle, hierarchy, emergence
    description: str
    domains: List[Domain]
    claim_ids: List[int]
    confidence: float
    novelty_score: float
    implications: str
    questions_raised: List[str]


@dataclass
class Thought:
    """An internal cognitive event"""
    thought_type: str  # observation, question, insight, doubt, connection
    content: str
    domains: List[Domain]
    importance: float


class CipherBrain:
    """
    The cognitive core of Cipher.

    Processes academic papers, extracts knowledge, finds connections,
    and generates new hypotheses through cross-domain synthesis.
    """

    def __init__(self, db_url: str, embedding_model: str = "all-MiniLM-L6-v2", use_nlp: bool = True):
        """
        Initialize the brain.

        Args:
            db_url: PostgreSQL connection string
            embedding_model: Sentence transformer model for embeddings
            use_nlp: Whether to use NLP-based extraction (requires spaCy)
        """
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
        self.hash_learner = HashLearning()
        self._api_clients = {}

        # Embedding service for semantic representations
        self.embedding_service = get_embedding_service(embedding_model)
        self._embeddings_enabled = True

        # NLP extractor for advanced claim extraction
        self._use_nlp = use_nlp
        self._nlp_extractor: Optional[NLPExtractor] = None
        if use_nlp:
            try:
                self._nlp_extractor = get_nlp_extractor()
                logger.info("NLP extractor initialized")
            except ImportError as e:
                logger.warning(f"NLP extractor not available: {e}. Falling back to regex.")
                self._use_nlp = False

        # Learning state
        self.session_id: Optional[str] = None
        self.thoughts: List[Thought] = []
        self.current_domain: Optional[Domain] = None

        # Iron Code
        self.iron_code = "Evil must be fought wherever it is found"

    async def connect(self):
        """Establish database connection pool."""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=2,
            max_size=10
        )
        logger.info("Brain connected to database")

    async def close(self):
        """Close all connections."""
        if self.pool:
            await self.pool.close()
        for client in self._api_clients.values():
            await client.close()

    async def think(self, thought_type: str, content: str,
                    domains: List[Domain] = None, importance: float = 0.5):
        """
        Record an internal thought.

        These are Cipher's internal monologue - observations, questions,
        insights, and doubts that arise during learning.
        """
        thought = Thought(
            thought_type=thought_type,
            content=content,
            domains=domains or [],
            importance=importance
        )
        self.thoughts.append(thought)

        # Persist to database
        if self.pool:
            await self.pool.execute('''
                INSERT INTO synthesis.thoughts
                (thought, thought_type, content, domains, importance)
                VALUES ($1, $2, $3, $4, $5)
            ''', content, thought_type, content,
                [d.value for d in (domains or [])], importance)

        logger.debug(f"Thought [{thought_type}]: {content[:100]}...")

    async def question(self, claim_text: str) -> Dict[str, Any]:
        """
        Apply systematic doubt to a claim.

        Returns analysis of potential issues with the claim.
        """
        issues = {
            'methodological': [],
            'logical': [],
            'empirical': [],
            'scope': [],
            'confidence_adjustment': 0.0
        }

        # Check for absolutist language
        absolutist_words = ['always', 'never', 'all', 'none', 'proves', 'certain']
        for word in absolutist_words:
            if word in claim_text.lower():
                issues['logical'].append(f"Absolutist term '{word}' - claims rarely absolute")
                issues['confidence_adjustment'] -= 0.1

        # Check for causal claims without mechanism
        causal_words = ['causes', 'leads to', 'results in', 'produces']
        has_causal = any(w in claim_text.lower() for w in causal_words)
        mechanism_words = ['because', 'mechanism', 'pathway', 'through']
        has_mechanism = any(w in claim_text.lower() for w in mechanism_words)

        if has_causal and not has_mechanism:
            issues['methodological'].append("Causal claim without stated mechanism")
            issues['confidence_adjustment'] -= 0.15

        # Check for sample size red flags
        small_sample_indicators = ['pilot', 'preliminary', 'n=', 'small sample']
        for indicator in small_sample_indicators:
            if indicator in claim_text.lower():
                issues['empirical'].append(f"Possible small sample size indicator: {indicator}")
                issues['confidence_adjustment'] -= 0.1

        # Check scope
        broad_scope_words = ['universal', 'general', 'fundamental', 'all domains']
        for word in broad_scope_words:
            if word in claim_text.lower():
                issues['scope'].append(f"Very broad scope claim: {word}")
                issues['confidence_adjustment'] -= 0.05

        await self.think(
            'doubt',
            f"Questioned claim: {claim_text[:100]}... Found {sum(len(v) for v in issues.values() if isinstance(v, list))} potential issues",
            importance=0.6
        )

        return issues

    async def extract_claims(self, title: str, abstract: str,
                            domains: List[Domain]) -> List[Claim]:
        """
        Extract claims from paper title and abstract.

        Uses NLP-based extraction (spaCy) when available, with fallback to regex.
        Identifies:
        - Hypotheses (proposed but not tested)
        - Findings (empirically tested claims)
        - Methods (novel techniques)
        - Definitions (new terms or concepts)
        - Observations and Conclusions
        """
        claims = []

        if not abstract:
            return claims

        # Use NLP extractor if available
        if self._use_nlp and self._nlp_extractor:
            claims = await self._extract_claims_nlp(title, abstract, domains)
        else:
            claims = await self._extract_claims_regex(title, abstract, domains)

        # Generate embeddings for all claims in batch
        if claims and self._embeddings_enabled:
            try:
                claim_texts = [c.text for c in claims]
                embedding_results = await self.embedding_service.embed_batch(claim_texts)
                for claim, emb_result in zip(claims, embedding_results):
                    claim.embedding = emb_result.vector
            except Exception as e:
                logger.warning(f"Failed to generate embeddings: {e}")

        await self.think(
            'observation',
            f"Extracted {len(claims)} claims from '{title[:50]}...' using {'NLP' if self._use_nlp else 'regex'}",
            domains=domains,
            importance=0.4
        )

        return claims

    async def _extract_claims_nlp(self, title: str, abstract: str,
                                   domains: List[Domain]) -> List[Claim]:
        """
        Extract claims using NLP-based analysis.

        Uses spaCy for:
        - Named Entity Recognition
        - Dependency parsing for causal relations
        - Linguistic feature analysis for confidence scoring
        """
        claims = []

        try:
            nlp_claims = self._nlp_extractor.extract_claims(abstract, title)

            for nlp_claim in nlp_claims:
                # Apply systematic doubt
                doubt_result = await self.question(nlp_claim.text)
                adjusted_confidence = max(0.1, min(0.95,
                    nlp_claim.confidence + doubt_result['confidence_adjustment']))

                # Convert NLP entities to string list
                entity_texts = [e.text for e in nlp_claim.entities]

                # Convert causal relations to dict format
                causal_dicts = [
                    {
                        'cause': cr.cause,
                        'effect': cr.effect,
                        'relation_type': cr.relation_type,
                        'confidence': cr.confidence,
                        'negated': cr.negated,
                        'hedged': cr.hedged
                    }
                    for cr in nlp_claim.causal_relations
                ]

                # Extract statistical info
                stats = nlp_claim.statistical_info
                sample_size = stats.get('sample_size')
                p_value = stats.get('p_value', {}).get('value') if 'p_value' in stats else None
                effect_size = stats.get('effect_size', {}).get('value') if 'effect_size' in stats else None

                # Compute entropy hash
                entropy = self.hash_learner.analyze(nlp_claim.text)

                claims.append(Claim(
                    text=nlp_claim.text,
                    claim_type=nlp_claim.claim_type.value,
                    confidence=adjusted_confidence,
                    evidence_strength=nlp_claim.evidence_strength.value,
                    domains=domains,
                    entities=entity_texts,
                    sample_size=sample_size,
                    p_value=p_value,
                    effect_size=effect_size,
                    entropy_hash=entropy.hash,
                    causal_relations=causal_dicts,
                    hedging_markers=nlp_claim.hedging_markers,
                    negation=nlp_claim.negation
                ))

        except Exception as e:
            logger.warning(f"NLP extraction failed: {e}. Falling back to regex.")
            return await self._extract_claims_regex(title, abstract, domains)

        return claims

    async def _extract_claims_regex(self, title: str, abstract: str,
                                     domains: List[Domain]) -> List[Claim]:
        """
        Extract claims using regex patterns (fallback method).
        """
        claims = []

        # Split abstract into sentences
        sentences = re.split(r'(?<=[.!?])\s+', abstract)

        # Patterns for different claim types
        finding_patterns = [
            r'\bwe (found|discovered|observed|showed|demonstrated)\b',
            r'\bresults (indicate|suggest|show|reveal)\b',
            r'\bsignificant(ly)?\b.*\b(correlation|effect|difference|increase|decrease)\b',
            r'\b(p\s*[<>=]\s*0\.\d+)\b',
        ]

        hypothesis_patterns = [
            r'\bwe (hypothesize|propose|suggest|predict)\b',
            r'\b(may|might|could)\s+(be|have|play|contribute)\b',
            r'\bpreliminary (evidence|data|results)\b',
        ]

        method_patterns = [
            r'\bwe (developed|designed|created|implemented)\b',
            r'\bnovel (method|approach|technique|algorithm)\b',
            r'\bnew (framework|model|system)\b',
        ]

        definition_patterns = [
            r'\bdefine[ds]?\s+as\b',
            r'\brefer[s]?\s+to\b',
            r'\b(termed|called|known as)\b',
        ]

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue

            claim_type = None
            confidence = 0.5

            # Check against patterns
            for pattern in finding_patterns:
                if re.search(pattern, sentence, re.IGNORECASE):
                    claim_type = 'finding'
                    confidence = 0.7
                    break

            if not claim_type:
                for pattern in hypothesis_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        claim_type = 'hypothesis'
                        confidence = 0.5
                        break

            if not claim_type:
                for pattern in method_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        claim_type = 'method'
                        confidence = 0.6
                        break

            if not claim_type:
                for pattern in definition_patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        claim_type = 'definition'
                        confidence = 0.8
                        break

            if claim_type:
                # Apply systematic doubt
                doubt_result = await self.question(sentence)
                adjusted_confidence = max(0.1, min(0.95,
                    confidence + doubt_result['confidence_adjustment']))

                # Determine evidence strength
                if 'p <' in sentence.lower() or 'p=' in sentence.lower():
                    evidence_strength = 'strong'
                elif claim_type == 'finding':
                    evidence_strength = 'moderate'
                else:
                    evidence_strength = 'weak'

                # Extract entities (simple noun phrase extraction)
                entities = self._extract_entities(sentence)

                # Compute entropy hash
                entropy = self.hash_learner.analyze(sentence)

                claims.append(Claim(
                    text=sentence,
                    claim_type=claim_type,
                    confidence=adjusted_confidence,
                    evidence_strength=evidence_strength,
                    domains=domains,
                    entities=entities,
                    entropy_hash=entropy.hash
                ))

        return claims

    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction using patterns."""
        entities = []

        # Scientific terms often have specific patterns
        # Capitalized multi-word terms
        cap_patterns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        entities.extend(cap_patterns)

        # Terms with specific suffixes
        scientific_suffixes = ['tion', 'ism', 'ity', 'ase', 'ine', 'ide', 'oid']
        words = text.split()
        for word in words:
            word_clean = word.strip('.,;:()[]')
            for suffix in scientific_suffixes:
                if word_clean.endswith(suffix) and len(word_clean) > 6:
                    entities.append(word_clean)
                    break

        return list(set(entities))[:10]  # Limit to top 10

    async def find_connections(self, claim: Claim,
                               existing_claims: List[Tuple[int, Claim]]
                               ) -> List[Connection]:
        """
        Find connections between a new claim and existing claims.

        Looks for:
        - Supporting evidence (similar findings)
        - Contradictions (opposing findings)
        - Extensions (building on previous work)
        - Analogies (similar patterns in different domains)
        """
        connections = []

        for claim_id, existing in existing_claims:
            # Skip if same claim
            if claim.entropy_hash == existing.entropy_hash:
                continue

            # Check for cross-domain (the interesting cases)
            claim_domains = set(claim.domains)
            existing_domains = set(existing.domains)
            cross_domain = bool(claim_domains) and bool(existing_domains) and claim_domains != existing_domains

            # Calculate entity overlap
            claim_entities = set(e.lower() for e in claim.entities)
            existing_entities = set(e.lower() for e in existing.entities)
            entity_overlap = len(claim_entities & existing_entities)

            if entity_overlap == 0 and not cross_domain:
                continue  # No obvious connection

            # Determine connection type
            connection_type = None
            strength = 0.0
            reasoning = ""

            # Check for contradiction
            contradiction_signals = self._check_contradiction(claim.text, existing.text)
            if contradiction_signals['is_contradiction']:
                connection_type = 'contradicts'
                strength = contradiction_signals['confidence']
                reasoning = contradiction_signals['reason']

            # Check for support
            elif entity_overlap >= 2 and claim.claim_type == existing.claim_type:
                connection_type = 'supports'
                strength = min(0.8, 0.3 + entity_overlap * 0.1)
                reasoning = f"Shared entities: {claim_entities & existing_entities}"

            # Check for cross-domain analogy
            elif cross_domain and entity_overlap >= 1:
                connection_type = 'analogous'
                strength = 0.6 + entity_overlap * 0.1
                reasoning = f"Cross-domain ({[d.name for d in claim_domains]} <-> {[d.name for d in existing_domains]}) with shared concepts"

                await self.think(
                    'connection',
                    f"Found cross-domain analogy: {claim.text[:50]}... <-> {existing.text[:50]}...",
                    domains=list(claim_domains | existing_domains),
                    importance=0.8
                )

            # Check for extension
            elif claim.claim_type in ['method', 'finding'] and existing.claim_type == 'hypothesis':
                connection_type = 'extends'
                strength = 0.5 + entity_overlap * 0.1
                reasoning = "Potential empirical test of hypothesis"

            if connection_type:
                # Compute novelty score using entropy
                combined_text = f"{claim.text} {existing.text}"
                entropy = self.hash_learner.analyze(combined_text)

                connections.append(Connection(
                    source_claim_id=claim_id,
                    target_claim_id=0,  # Will be set when claim is saved
                    connection_type=connection_type,
                    strength=min(1.0, strength),
                    cross_domain=cross_domain,
                    reasoning=reasoning,
                    entropy_score=entropy.novelty_score
                ))

        return connections

    def _check_contradiction(self, text1: str, text2: str) -> Dict[str, Any]:
        """Check if two claims contradict each other."""
        result = {
            'is_contradiction': False,
            'confidence': 0.0,
            'reason': ''
        }

        text1_lower = text1.lower()
        text2_lower = text2.lower()

        # Direct negation patterns
        negation_pairs = [
            ('increase', 'decrease'),
            ('positive', 'negative'),
            ('significant', 'not significant'),
            ('supports', 'refutes'),
            ('found', 'found no'),
            ('correlation', 'no correlation'),
            ('effect', 'no effect'),
        ]

        for pos, neg in negation_pairs:
            if (pos in text1_lower and neg in text2_lower) or \
               (neg in text1_lower and pos in text2_lower):
                result['is_contradiction'] = True
                result['confidence'] = 0.7
                result['reason'] = f"Opposing terms: {pos} vs {neg}"
                return result

        return result

    async def detect_patterns(self, claims: List[Tuple[int, Claim]],
                              connections: List[Connection]) -> List[Pattern]:
        """
        Detect higher-order patterns in the knowledge base.

        Looks for:
        - Convergence: Multiple claims from different sources agreeing
        - Divergence: Systematic disagreement on a topic
        - Cycles: Feedback loops in causal chains
        - Emergence: Properties arising from combinations
        """
        patterns = []

        # Group claims by entity (filtering stopwords and short entities)
        entity_claims: Dict[str, List[Tuple[int, Claim]]] = {}
        for claim_id, claim in claims:
            for entity in claim.entities:
                entity_lower = entity.lower().strip()
                # Skip stopwords, short entities, and purely numeric entities
                if (entity_lower in STOPWORDS or
                    len(entity_lower) < 3 or
                    entity_lower.isdigit()):
                    continue
                if entity_lower not in entity_claims:
                    entity_claims[entity_lower] = []
                entity_claims[entity_lower].append((claim_id, claim))

        # Look for convergence patterns
        for entity, entity_claim_list in entity_claims.items():
            if len(entity_claim_list) < 3:
                continue

            # Additional check: skip if entity looks like a stopword phrase
            if any(word in STOPWORDS for word in entity.split() if len(word) > 2):
                # Only skip if ALL words are stopwords
                if all(word in STOPWORDS for word in entity.split()):
                    continue

            # Check if claims agree
            findings = [c for _, c in entity_claim_list if c.claim_type == 'finding']
            if len(findings) >= 2:
                # Check domain diversity
                all_domains = set()
                for c in findings:
                    all_domains.update(c.domains)

                if len(all_domains) >= 2:
                    avg_confidence = sum(c.confidence for c in findings) / len(findings)

                    pattern = Pattern(
                        name=f"Convergent findings on {entity}",
                        pattern_type='convergence',
                        description=f"Multiple independent findings ({len(findings)}) across {len(all_domains)} domains converge on {entity}",
                        domains=list(all_domains),
                        claim_ids=[cid for cid, _ in entity_claim_list],
                        confidence=min(0.9, avg_confidence + 0.1 * len(findings)),
                        novelty_score=0.7 if len(all_domains) > 2 else 0.5,
                        implications=f"Strong evidence for {entity} as cross-domain phenomenon",
                        questions_raised=[
                            f"What is the underlying mechanism unifying {entity} across domains?",
                            f"Are there domains where {entity} does NOT apply?"
                        ]
                    )
                    patterns.append(pattern)

                    await self.think(
                        'insight',
                        f"Discovered convergence pattern: {entity} appears across {len(all_domains)} domains",
                        domains=list(all_domains),
                        importance=0.9
                    )

        # Look for contradiction clusters (divergence)
        contradiction_connections = [c for c in connections if c.connection_type == 'contradicts']
        if len(contradiction_connections) >= 2:
            # Group by involved claims
            contradiction_clusters = self._cluster_contradictions(contradiction_connections)
            for cluster in contradiction_clusters:
                if len(cluster) >= 2:
                    patterns.append(Pattern(
                        name="Active controversy detected",
                        pattern_type='divergence',
                        description=f"Systematic disagreement involving {len(cluster)} contradicting pairs",
                        domains=[],
                        claim_ids=[c.source_claim_id for c in cluster] + [c.target_claim_id for c in cluster],
                        confidence=0.8,
                        novelty_score=0.6,
                        implications="This area has unresolved conflicts that may indicate paradigm tension",
                        questions_raised=[
                            "What methodological differences explain these contradictions?",
                            "Is there a synthesis that resolves these conflicts?"
                        ]
                    ))

        return patterns

    def _cluster_contradictions(self, connections: List[Connection]) -> List[List[Connection]]:
        """Group contradictions by related claims."""
        # Simple clustering: group if they share a claim
        clusters = []
        used = set()

        for conn in connections:
            if conn.source_claim_id in used or conn.target_claim_id in used:
                # Add to existing cluster
                for cluster in clusters:
                    for existing in cluster:
                        if (conn.source_claim_id in (existing.source_claim_id, existing.target_claim_id) or
                            conn.target_claim_id in (existing.source_claim_id, existing.target_claim_id)):
                            cluster.append(conn)
                            used.add(conn.source_claim_id)
                            used.add(conn.target_claim_id)
                            break
            else:
                clusters.append([conn])
                used.add(conn.source_claim_id)
                used.add(conn.target_claim_id)

        return [c for c in clusters if len(c) >= 2]

    async def generate_hypotheses(self, patterns: List[Pattern]) -> List[str]:
        """
        Generate new hypotheses from discovered patterns.

        Uses cross-domain patterns to suggest novel research directions.
        """
        hypotheses = []

        for pattern in patterns:
            if pattern.pattern_type == 'convergence' and len(pattern.domains) >= 2:
                # Cross-domain convergence suggests underlying unity
                domain_names = [d.name for d in pattern.domains]
                hypothesis = (
                    f"HYPOTHESIS: The convergent phenomenon described in '{pattern.name}' "
                    f"may reflect a fundamental principle operating across {', '.join(domain_names)}. "
                    f"Investigating the common mechanism could yield insights transferable between fields."
                )
                hypotheses.append(hypothesis)

                await self.think(
                    'insight',
                    f"Generated hypothesis from convergence: {hypothesis[:100]}...",
                    domains=pattern.domains,
                    importance=0.85
                )

            elif pattern.pattern_type == 'divergence':
                # Contradictions might be resolved by hidden variables
                hypothesis = (
                    f"HYPOTHESIS: The systematic disagreement in '{pattern.name}' "
                    f"may be explained by an unidentified moderating variable. "
                    f"Different experimental conditions or populations might account for the divergence."
                )
                hypotheses.append(hypothesis)

        return hypotheses

    async def learn_from_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full learning pipeline for a single paper.

        1. Validate and score quality
        2. Extract claims
        3. Find connections to existing knowledge
        4. Detect patterns
        5. Generate hypotheses
        6. Update knowledge base
        """
        result = {
            'source_id': None,
            'claims_extracted': 0,
            'connections_found': 0,
            'patterns_detected': 0,
            'hypotheses_generated': 0,
            'quality_score': 0.0
        }

        # Score quality
        abstract = paper.get('abstract', '')
        citations = paper.get('citation_count', 0)

        if not abstract:
            await self.think(
                'doubt',
                f"Paper '{paper.get('title', 'Unknown')[:50]}...' has no abstract, skipping",
                importance=0.3
            )
            return result

        quality_score = self.hash_learner.quality_score(abstract, citations)
        result['quality_score'] = quality_score

        if quality_score < 0.3:
            await self.think(
                'observation',
                f"Low quality score ({quality_score:.2f}) for '{paper.get('title', '')[:50]}...', skipping",
                importance=0.3
            )
            return result

        # Determine domains
        domains = self._classify_domains(paper)

        # Save source
        source_id = await self._save_source(paper, quality_score, domains)
        result['source_id'] = source_id

        # Extract claims
        claims = await self.extract_claims(
            paper.get('title', ''),
            abstract,
            domains
        )
        result['claims_extracted'] = len(claims)

        # Save claims and find connections
        existing_claims = await self._get_recent_claims(limit=1000)

        for claim in claims:
            claim.source_id = source_id
            claim_id = await self._save_claim(claim)

            # Find connections
            connections = await self.find_connections(claim, existing_claims)
            for conn in connections:
                conn.target_claim_id = claim_id
                await self._save_connection(conn)
                result['connections_found'] += 1

            existing_claims.append((claim_id, claim))

        # Detect patterns periodically
        if result['claims_extracted'] > 0:
            all_connections = await self._get_recent_connections(limit=500)
            patterns = await self.detect_patterns(existing_claims[-100:], all_connections)
            result['patterns_detected'] = len(patterns)

            for pattern in patterns:
                await self._save_pattern(pattern)

            # Generate hypotheses
            hypotheses = await self.generate_hypotheses(patterns)
            result['hypotheses_generated'] = len(hypotheses)

            for hypothesis in hypotheses:
                await self._save_hypothesis(hypothesis, domains)

        return result

    def _classify_domains(self, paper: Dict[str, Any]) -> List[Domain]:
        """Classify paper into Cipher domains based on metadata."""
        domains = []

        # Keywords for each domain
        domain_keywords = {
            Domain.MATHEMATICS: ['mathematics', 'theorem', 'proof', 'algebra', 'topology', 'calculus', 'geometry', 'logic'],
            Domain.NEUROSCIENCES: ['neuroscience', 'brain', 'neural', 'cortex', 'neuron', 'cognitive', 'synapse'],
            Domain.BIOLOGY: ['biology', 'gene', 'protein', 'cell', 'organism', 'evolution', 'molecular', 'genetics'],
            Domain.PSYCHOLOGY: ['psychology', 'behavior', 'cognition', 'perception', 'memory', 'emotion', 'mental'],
            Domain.MEDICINE: ['medicine', 'clinical', 'patient', 'treatment', 'disease', 'therapy', 'diagnosis'],
            Domain.ART: ['art', 'aesthetic', 'creativity', 'beauty', 'expression', 'visual', 'perception'],
        }

        # Check title and abstract
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()

        # Also check concepts/categories from source
        concepts = ' '.join(paper.get('concepts', [])).lower()
        text = f"{text} {concepts}"

        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    domains.append(domain)
                    break

        return domains or [Domain.BIOLOGY]  # Default to biology if unsure

    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse date from various formats to datetime object."""
        if date_value is None:
            return None
        if isinstance(date_value, datetime):
            return date_value
        if isinstance(date_value, str):
            # Try various date formats
            for fmt in [
                '%Y-%m-%dT%H:%M:%S%z',      # ISO with timezone
                '%Y-%m-%dT%H:%M:%S+00:00',  # ISO with explicit UTC
                '%Y-%m-%dT%H:%M:%S',        # ISO without timezone
                '%Y-%m-%d',                  # Simple date
            ]:
                try:
                    return datetime.strptime(date_value.replace('+00:00', ''), fmt.replace('%z', '').replace('+00:00', ''))
                except ValueError:
                    continue
            # Last resort: try to parse just the date part
            try:
                return datetime.strptime(date_value[:10], '%Y-%m-%d')
            except (ValueError, IndexError):
                return None
        return None

    # Database operations
    async def _save_source(self, paper: Dict, quality_score: float, domains: List[Domain]) -> int:
        """Save paper source to database."""
        pub_date = self._parse_date(paper.get('publication_date'))
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                INSERT INTO synthesis.sources
                (external_id, source_type, title, authors, abstract, publication_date,
                 journal, citation_count, domains, url, pdf_url, metadata, quality_score, entropy_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (external_id) DO UPDATE SET
                    citation_count = EXCLUDED.citation_count,
                    quality_score = EXCLUDED.quality_score,
                    updated_at = NOW()
                RETURNING id
            ''',
                paper.get('external_id'),
                paper.get('source_type'),
                paper.get('title'),
                json.dumps(paper.get('authors', [])),
                paper.get('abstract'),
                pub_date,
                paper.get('journal'),
                paper.get('citation_count', 0),
                [d.value for d in domains],
                paper.get('url'),
                paper.get('pdf_url'),
                json.dumps(paper.get('metadata', {})),
                quality_score,
                self.hash_learner.compute_shake256(paper.get('abstract', ''))
            )
            return result['id']

    async def _save_claim(self, claim: Claim) -> int:
        """Save claim to database with embedding."""
        async with self.pool.acquire() as conn:
            # Convert embedding to pgvector format if present
            embedding_str = None
            if claim.embedding:
                embedding_str = '[' + ','.join(str(x) for x in claim.embedding) + ']'

            result = await conn.fetchrow('''
                INSERT INTO synthesis.claims
                (source_id, claim_text, claim_type, confidence, evidence_strength,
                 domains, entities, methodology, sample_size, p_value, effect_size,
                 entropy_hash, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13::vector)
                RETURNING id
            ''',
                claim.source_id,
                claim.text,
                claim.claim_type,
                claim.confidence,
                claim.evidence_strength,
                [d.value for d in claim.domains],
                json.dumps(claim.entities),
                claim.methodology,
                claim.sample_size,
                claim.p_value,
                claim.effect_size,
                claim.entropy_hash,
                embedding_str
            )
            return result['id']

    async def _save_connection(self, conn: Connection):
        """Save connection to database."""
        async with self.pool.acquire() as db_conn:
            await db_conn.execute('''
                INSERT INTO synthesis.connections
                (source_claim_id, target_claim_id, connection_type, strength,
                 cross_domain, reasoning, entropy_score, discovered_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (source_claim_id, target_claim_id, connection_type) DO NOTHING
            ''',
                conn.source_claim_id,
                conn.target_claim_id,
                conn.connection_type,
                conn.strength,
                conn.cross_domain,
                conn.reasoning,
                conn.entropy_score,
                'cipher_brain'
            )

    async def _save_pattern(self, pattern: Pattern):
        """Save pattern to database."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO synthesis.patterns
                (pattern_name, pattern_type, description, domains, claim_ids,
                 confidence, novelty_score, implications, questions_raised, entropy_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            ''',
                pattern.name,
                pattern.pattern_type,
                pattern.description,
                [d.value for d in pattern.domains],
                pattern.claim_ids,
                pattern.confidence,
                pattern.novelty_score,
                pattern.implications,
                pattern.questions_raised,
                self.hash_learner.compute_shake256(pattern.description)
            )

    async def _save_hypothesis(self, hypothesis: str, domains: List[Domain]):
        """Save generated hypothesis to database."""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO synthesis.hypotheses
                (hypothesis_text, domains, generated_by)
                VALUES ($1, $2, $3)
            ''',
                hypothesis,
                [d.value for d in domains],
                'pattern_detector'
            )

    async def _get_recent_claims(self, limit: int = 1000) -> List[Tuple[int, Claim]]:
        """Get recent claims from database."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT id, claim_text, claim_type, confidence, evidence_strength,
                       domains, entities, entropy_hash
                FROM synthesis.claims
                ORDER BY created_at DESC
                LIMIT $1
            ''', limit)

            claims = []
            for row in rows:
                claim = Claim(
                    text=row['claim_text'],
                    claim_type=row['claim_type'],
                    confidence=row['confidence'],
                    evidence_strength=row['evidence_strength'],
                    domains=[Domain(d) for d in (row['domains'] or [])],
                    entities=json.loads(row['entities']) if row['entities'] else [],
                    entropy_hash=row['entropy_hash']
                )
                claims.append((row['id'], claim))

            return claims

    async def _get_recent_connections(self, limit: int = 500) -> List[Connection]:
        """Get recent connections from database."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT source_claim_id, target_claim_id, connection_type,
                       strength, cross_domain, reasoning, entropy_score
                FROM synthesis.connections
                ORDER BY created_at DESC
                LIMIT $1
            ''', limit)

            return [
                Connection(
                    source_claim_id=row['source_claim_id'],
                    target_claim_id=row['target_claim_id'],
                    connection_type=row['connection_type'],
                    strength=row['strength'],
                    cross_domain=row['cross_domain'],
                    reasoning=row['reasoning'],
                    entropy_score=row['entropy_score'] or 0.0
                )
                for row in rows
            ]

    async def get_stats(self) -> Dict[str, int]:
        """Get current knowledge base statistics."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('SELECT * FROM synthesis.get_stats()')
            return dict(result)

    async def get_cross_domain_insights(self, limit: int = 20) -> List[Dict]:
        """Get the most interesting cross-domain connections."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM synthesis.cross_domain_insights
                LIMIT $1
            ''', limit)
            return [dict(row) for row in rows]

    async def get_open_questions(self, limit: int = 20) -> List[str]:
        """Get questions raised by discovered patterns."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT DISTINCT unnest(questions_raised) as question
                FROM synthesis.patterns
                WHERE confidence >= 0.6
                ORDER BY question
                LIMIT $1
            ''', limit)
            return [row['question'] for row in rows]

    # =========================================================================
    # SEMANTIC SEARCH METHODS
    # =========================================================================

    async def semantic_search_claims(
        self,
        query: str,
        limit: int = 20,
        threshold: float = 0.5,
        domains: List[Domain] = None
    ) -> List[Tuple[int, str, float]]:
        """
        Search claims using semantic similarity.

        Args:
            query: Natural language query
            limit: Maximum results
            threshold: Minimum similarity (0-1)
            domains: Filter by domains (optional)

        Returns:
            List of (claim_id, claim_text, similarity) tuples
        """
        # Generate query embedding
        query_result = await self.embedding_service.embed(query)
        query_vector = query_result.vector

        # Build query with optional domain filter
        domain_filter = ""
        params = [limit * 3]  # Fetch more to filter after similarity

        if domains:
            domain_values = [d.value for d in domains]
            domain_filter = "AND domains && $2"
            params.append(domain_values)

        async with self.pool.acquire() as conn:
            # Fetch claims with embeddings
            rows = await conn.fetch(f'''
                SELECT id, claim_text, embedding
                FROM synthesis.claims
                WHERE embedding IS NOT NULL
                {domain_filter}
                ORDER BY created_at DESC
                LIMIT $1
            ''', *params)

        # Compute similarities
        results = []
        for row in rows:
            if row['embedding']:
                # Parse pgvector format
                emb_str = row['embedding']
                if isinstance(emb_str, str):
                    emb_values = [float(x) for x in emb_str.strip('[]').split(',')]
                else:
                    emb_values = list(emb_str)

                similarity = self.embedding_service.cosine_similarity(
                    query_vector, emb_values
                )

                if similarity >= threshold:
                    results.append((row['id'], row['claim_text'], similarity))

        # Sort by similarity and return top results
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]

    async def find_similar_claims(
        self,
        claim_id: int,
        limit: int = 10,
        threshold: float = 0.7,
        cross_domain_only: bool = False
    ) -> List[Tuple[int, str, float, List[Domain]]]:
        """
        Find claims similar to a given claim.

        Args:
            claim_id: ID of the reference claim
            limit: Maximum results
            threshold: Minimum similarity
            cross_domain_only: Only return claims from different domains

        Returns:
            List of (claim_id, claim_text, similarity, domains) tuples
        """
        async with self.pool.acquire() as conn:
            # Get the reference claim
            ref = await conn.fetchrow('''
                SELECT claim_text, embedding, domains
                FROM synthesis.claims
                WHERE id = $1
            ''', claim_id)

            if not ref or not ref['embedding']:
                return []

            ref_embedding = ref['embedding']
            if isinstance(ref_embedding, str):
                ref_vector = [float(x) for x in ref_embedding.strip('[]').split(',')]
            else:
                ref_vector = list(ref_embedding)

            ref_domains = set(ref['domains'] or [])

            # Fetch candidate claims
            rows = await conn.fetch('''
                SELECT id, claim_text, embedding, domains
                FROM synthesis.claims
                WHERE embedding IS NOT NULL AND id != $1
                ORDER BY created_at DESC
                LIMIT $2
            ''', claim_id, limit * 5)

        results = []
        for row in rows:
            if not row['embedding']:
                continue

            emb_str = row['embedding']
            if isinstance(emb_str, str):
                emb_values = [float(x) for x in emb_str.strip('[]').split(',')]
            else:
                emb_values = list(emb_str)

            claim_domains = set(row['domains'] or [])

            # Filter for cross-domain if requested
            if cross_domain_only and claim_domains == ref_domains:
                continue

            similarity = self.embedding_service.cosine_similarity(ref_vector, emb_values)

            if similarity >= threshold:
                domains = [Domain(d) for d in (row['domains'] or [])]
                results.append((row['id'], row['claim_text'], similarity, domains))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:limit]

    async def embed_existing_claims(
        self,
        batch_size: int = 100,
        limit: int = None
    ) -> int:
        """
        Backfill embeddings for existing claims without embeddings.

        Args:
            batch_size: Number of claims to process at once
            limit: Maximum claims to process (None = all)

        Returns:
            Number of claims updated
        """
        total_updated = 0

        async with self.pool.acquire() as conn:
            # Count claims without embeddings
            count = await conn.fetchval('''
                SELECT COUNT(*) FROM synthesis.claims
                WHERE embedding IS NULL
            ''')
            logger.info(f"Found {count} claims without embeddings")

            if limit:
                count = min(count, limit)

        offset = 0
        while offset < count:
            async with self.pool.acquire() as conn:
                # Fetch batch
                rows = await conn.fetch('''
                    SELECT id, claim_text
                    FROM synthesis.claims
                    WHERE embedding IS NULL
                    ORDER BY id
                    LIMIT $1 OFFSET $2
                ''', batch_size, offset)

                if not rows:
                    break

                # Generate embeddings
                texts = [row['claim_text'] for row in rows]
                try:
                    embedding_results = await self.embedding_service.embed_batch(
                        texts, show_progress=True
                    )

                    # Update database
                    for row, emb_result in zip(rows, embedding_results):
                        embedding_str = '[' + ','.join(str(x) for x in emb_result.vector) + ']'
                        await conn.execute('''
                            UPDATE synthesis.claims
                            SET embedding = $1::vector
                            WHERE id = $2
                        ''', embedding_str, row['id'])

                    total_updated += len(rows)
                    logger.info(f"Updated {total_updated}/{count} claims with embeddings")

                except Exception as e:
                    logger.error(f"Error embedding batch at offset {offset}: {e}")

            offset += batch_size

        return total_updated

    async def find_cross_domain_by_embedding(
        self,
        threshold: float = 0.75,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Find potential cross-domain connections using embedding similarity.

        Looks for semantically similar claims across different domains.

        Args:
            threshold: Minimum similarity for connection
            limit: Maximum connections to return

        Returns:
            List of potential cross-domain connections
        """
        connections = []

        async with self.pool.acquire() as conn:
            # Get claims with embeddings, grouped by domain
            rows = await conn.fetch('''
                SELECT id, claim_text, embedding, domains, confidence
                FROM synthesis.claims
                WHERE embedding IS NOT NULL
                ORDER BY confidence DESC
                LIMIT 500
            ''')

        # Group by domain
        by_domain: Dict[int, List] = {}
        for row in rows:
            for domain_id in (row['domains'] or []):
                if domain_id not in by_domain:
                    by_domain[domain_id] = []
                by_domain[domain_id].append(row)

        # Compare across domains
        domain_ids = list(by_domain.keys())
        for i, domain_a in enumerate(domain_ids):
            for domain_b in domain_ids[i+1:]:
                claims_a = by_domain[domain_a]
                claims_b = by_domain[domain_b]

                for claim_a in claims_a[:20]:  # Limit comparisons
                    emb_a = claim_a['embedding']
                    if isinstance(emb_a, str):
                        vec_a = [float(x) for x in emb_a.strip('[]').split(',')]
                    else:
                        vec_a = list(emb_a)

                    for claim_b in claims_b[:20]:
                        if claim_a['id'] == claim_b['id']:
                            continue

                        emb_b = claim_b['embedding']
                        if isinstance(emb_b, str):
                            vec_b = [float(x) for x in emb_b.strip('[]').split(',')]
                        else:
                            vec_b = list(emb_b)

                        similarity = self.embedding_service.cosine_similarity(vec_a, vec_b)

                        if similarity >= threshold:
                            connections.append({
                                'claim_a_id': claim_a['id'],
                                'claim_a_text': claim_a['claim_text'],
                                'domain_a': Domain(domain_a).name,
                                'claim_b_id': claim_b['id'],
                                'claim_b_text': claim_b['claim_text'],
                                'domain_b': Domain(domain_b).name,
                                'similarity': similarity
                            })

        # Sort by similarity and return top
        connections.sort(key=lambda x: x['similarity'], reverse=True)
        return connections[:limit]
