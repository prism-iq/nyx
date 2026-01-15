"""
CIPHER Domain Learner
Orchestrates parallel learning across the 6 domains of expertise.

Each domain has specific search strategies, sources, and concepts to explore.
The learner coordinates fetching, prioritizes based on cross-domain potential,
and manages the learning schedule.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import random

from .cipher_brain import CipherBrain, Domain
from .hash_learning import hash_learner

# Import integrations
import sys
sys.path.append('..')
from integrations import (
    OpenAlexClient, ArxivClient, PubMedClient, SemanticScholarClient,
    Paper
)

logger = logging.getLogger(__name__)


@dataclass
class DomainStrategy:
    """Learning strategy for a specific domain"""
    domain: Domain
    name: str
    description: str

    # Source priorities (1.0 = highest)
    openalex_weight: float = 1.0
    arxiv_weight: float = 0.5
    pubmed_weight: float = 0.5
    semantic_scholar_weight: float = 0.8

    # Search parameters
    openalex_concepts: List[str] = field(default_factory=list)
    arxiv_categories: List[str] = field(default_factory=list)
    pubmed_mesh: List[str] = field(default_factory=list)

    # Core keywords for this domain
    keywords: List[str] = field(default_factory=list)

    # Cross-domain bridge concepts (appear in multiple domains)
    bridge_concepts: List[str] = field(default_factory=list)


# Define strategies for each domain
DOMAIN_STRATEGIES = {
    Domain.MATHEMATICS: DomainStrategy(
        domain=Domain.MATHEMATICS,
        name="Mathematics",
        description="Pure and applied mathematics, logic, computation theory",
        openalex_weight=1.0,
        arxiv_weight=1.0,  # arXiv is primary for math
        pubmed_weight=0.2,
        semantic_scholar_weight=0.7,
        openalex_concepts=["C33923547", "C121332964", "C134306372"],
        arxiv_categories=["math.AG", "math.AT", "math.CA", "math.CO", "math.CT",
                         "math.DG", "math.DS", "math.FA", "math.GR", "math.GT",
                         "math.LO", "math.NA", "math.NT", "math.OC", "math.PR",
                         "math.RT", "math.ST", "cs.LO", "cs.CC"],
        keywords=["theorem", "proof", "conjecture", "algorithm", "topology",
                 "algebra", "geometry", "calculus", "optimization", "category theory"],
        bridge_concepts=["information", "entropy", "network", "optimization",
                        "complexity", "dynamical system", "graph"]
    ),

    Domain.NEUROSCIENCES: DomainStrategy(
        domain=Domain.NEUROSCIENCES,
        name="Neurosciences",
        description="Brain, cognition, neural systems, computational neuroscience",
        openalex_weight=1.0,
        arxiv_weight=0.6,
        pubmed_weight=1.0,  # PubMed is primary for neuro
        semantic_scholar_weight=0.9,
        openalex_concepts=["C86803240", "C15744967", "C54355233"],
        arxiv_categories=["q-bio.NC", "cs.NE", "cs.AI"],
        pubmed_mesh=["Neurosciences", "Brain", "Neurons", "Cognition",
                    "Synapses", "Neural Pathways", "Neuroplasticity"],
        keywords=["neural", "brain", "cortex", "synapse", "cognition",
                 "plasticity", "neurotransmitter", "action potential",
                 "hippocampus", "prefrontal cortex"],
        bridge_concepts=["information processing", "network", "learning",
                        "memory", "prediction", "representation", "computation"]
    ),

    Domain.BIOLOGY: DomainStrategy(
        domain=Domain.BIOLOGY,
        name="Biology",
        description="Life sciences, genetics, evolution, molecular biology",
        openalex_weight=1.0,
        arxiv_weight=0.4,
        pubmed_weight=1.0,
        semantic_scholar_weight=0.8,
        openalex_concepts=["C86803240", "C54355233", "C185592680"],
        arxiv_categories=["q-bio.BM", "q-bio.CB", "q-bio.GN", "q-bio.MN",
                         "q-bio.PE", "q-bio.SC"],
        pubmed_mesh=["Biology", "Genetics", "Evolution", "Cell Biology",
                    "Molecular Biology", "Genomics", "Proteomics"],
        keywords=["gene", "protein", "evolution", "cell", "organism",
                 "metabolism", "dna", "rna", "mutation", "selection"],
        bridge_concepts=["information", "network", "system", "regulation",
                        "adaptation", "complexity", "emergence"]
    ),

    Domain.PSYCHOLOGY: DomainStrategy(
        domain=Domain.PSYCHOLOGY,
        name="Psychology",
        description="Mind, behavior, cognition, emotion, social dynamics",
        openalex_weight=1.0,
        arxiv_weight=0.3,
        pubmed_weight=0.8,
        semantic_scholar_weight=1.0,  # S2 good for psychology
        openalex_concepts=["C15744967", "C77805123"],
        arxiv_categories=["cs.HC", "cs.CY"],
        pubmed_mesh=["Psychology", "Behavior", "Mental Processes",
                    "Cognition", "Emotions", "Social Behavior"],
        keywords=["cognition", "behavior", "perception", "memory", "emotion",
                 "consciousness", "attention", "decision making", "motivation"],
        bridge_concepts=["prediction", "learning", "representation",
                        "information", "uncertainty", "reward", "belief"]
    ),

    Domain.MEDICINE: DomainStrategy(
        domain=Domain.MEDICINE,
        name="Medicine",
        description="Clinical science, pathology, therapeutics, diagnosis",
        openalex_weight=0.9,
        arxiv_weight=0.2,
        pubmed_weight=1.0,  # PubMed is the primary source
        semantic_scholar_weight=0.8,
        openalex_concepts=["C71924100", "C126322002"],
        arxiv_categories=[],  # Medicine rarely on arXiv
        pubmed_mesh=["Medicine", "Therapeutics", "Diagnosis", "Pathology",
                    "Clinical Trials", "Treatment Outcome"],
        keywords=["clinical", "patient", "treatment", "disease", "therapy",
                 "diagnosis", "prognosis", "symptom", "efficacy", "safety"],
        bridge_concepts=["mechanism", "intervention", "outcome",
                        "prediction", "risk", "biomarker"]
    ),

    Domain.ART: DomainStrategy(
        domain=Domain.ART,
        name="Art",
        description="Aesthetics, creativity, perception, expression",
        openalex_weight=1.0,
        arxiv_weight=0.4,
        pubmed_weight=0.3,
        semantic_scholar_weight=0.9,
        openalex_concepts=["C142362112", "C17744445"],
        arxiv_categories=["cs.GR", "cs.SD", "cs.MM", "cs.CV"],
        pubmed_mesh=["Art", "Creativity", "Esthetics",
                    "Visual Perception", "Music"],
        keywords=["aesthetic", "creativity", "perception", "beauty",
                 "expression", "visual", "composition", "emotion",
                 "artistic", "design"],
        bridge_concepts=["perception", "emotion", "pattern", "complexity",
                        "information", "prediction", "surprise"]
    ),
}


@dataclass
class LearningSession:
    """Track a learning session"""
    session_id: str
    domain: Domain
    started_at: datetime
    papers_fetched: int = 0
    claims_extracted: int = 0
    connections_found: int = 0
    patterns_detected: int = 0
    errors: List[str] = field(default_factory=list)


class DomainLearner:
    """
    Orchestrates learning across all 6 domains.

    Key responsibilities:
    1. Initialize and manage API clients
    2. Execute domain-specific search strategies
    3. Parallelize learning across domains
    4. Prioritize cross-domain connections
    5. Track learning progress
    """

    def __init__(self, brain: CipherBrain, config: Dict[str, Any] = None):
        """
        Initialize the domain learner.

        Args:
            brain: CipherBrain instance for knowledge processing
            config: Optional configuration overrides
        """
        self.brain = brain
        self.config = config or {}

        # API clients (initialized lazily)
        self._openalex: Optional[OpenAlexClient] = None
        self._arxiv: Optional[ArxivClient] = None
        self._pubmed: Optional[PubMedClient] = None
        self._semantic_scholar: Optional[SemanticScholarClient] = None

        # Learning state
        self.sessions: List[LearningSession] = []
        self.seen_ids: Set[str] = set()  # Track seen paper IDs

        # Configuration
        self.max_papers_per_domain = self.config.get('max_papers_per_domain', 100)
        self.batch_size = self.config.get('batch_size', 50)
        self.cross_domain_boost = self.config.get('cross_domain_boost', 2.0)

    @property
    def openalex(self) -> OpenAlexClient:
        if self._openalex is None:
            self._openalex = OpenAlexClient(
                email=self.config.get('email', 'cipher@pwnd.icu')
            )
        return self._openalex

    @property
    def arxiv(self) -> ArxivClient:
        if self._arxiv is None:
            self._arxiv = ArxivClient()
        return self._arxiv

    @property
    def pubmed(self) -> PubMedClient:
        if self._pubmed is None:
            self._pubmed = PubMedClient(
                api_key=self.config.get('pubmed_api_key'),
                email=self.config.get('email', 'cipher@pwnd.icu')
            )
        return self._pubmed

    @property
    def semantic_scholar(self) -> SemanticScholarClient:
        if self._semantic_scholar is None:
            self._semantic_scholar = SemanticScholarClient(
                api_key=self.config.get('s2_api_key')
            )
        return self._semantic_scholar

    async def close(self):
        """Close all API clients."""
        if self._openalex:
            await self._openalex.close()
        if self._arxiv:
            await self._arxiv.close()
        if self._pubmed:
            await self._pubmed.close()
        if self._semantic_scholar:
            await self._semantic_scholar.close()

    async def learn_domain(
        self,
        domain: Domain,
        max_papers: int = None,
        days_back: int = 30
    ) -> LearningSession:
        """
        Learn from a single domain.

        Args:
            domain: Which domain to learn
            max_papers: Maximum papers to process
            days_back: How far back to search

        Returns:
            LearningSession with results
        """
        strategy = DOMAIN_STRATEGIES[domain]
        max_papers = max_papers or self.max_papers_per_domain

        session = LearningSession(
            session_id=f"{domain.name}_{datetime.now().isoformat()}",
            domain=domain,
            started_at=datetime.now()
        )
        self.sessions.append(session)

        logger.info(f"Starting learning session for {domain.name}")

        await self.brain.think(
            'observation',
            f"Beginning learning session for {domain.name}. Strategy: {strategy.description}",
            domains=[domain],
            importance=0.5
        )

        papers = []

        # Fetch from each source based on strategy weights
        try:
            # OpenAlex (if weighted)
            if strategy.openalex_weight > 0:
                openalex_papers = await self._fetch_openalex(
                    strategy,
                    limit=int(max_papers * strategy.openalex_weight),
                    days_back=days_back
                )
                papers.extend(openalex_papers)

            # arXiv (if weighted)
            if strategy.arxiv_weight > 0 and strategy.arxiv_categories:
                arxiv_papers = await self._fetch_arxiv(
                    strategy,
                    limit=int(max_papers * strategy.arxiv_weight * 0.5),
                    days_back=days_back
                )
                papers.extend(arxiv_papers)

            # PubMed (if weighted)
            if strategy.pubmed_weight > 0 and strategy.pubmed_mesh:
                pubmed_papers = await self._fetch_pubmed(
                    strategy,
                    limit=int(max_papers * strategy.pubmed_weight * 0.5),
                    days_back=days_back
                )
                papers.extend(pubmed_papers)

            # Semantic Scholar (for high-impact papers)
            if strategy.semantic_scholar_weight > 0:
                s2_papers = await self._fetch_semantic_scholar(
                    strategy,
                    limit=int(max_papers * strategy.semantic_scholar_weight * 0.3),
                    days_back=days_back
                )
                papers.extend(s2_papers)

        except Exception as e:
            error_msg = f"Error fetching papers for {domain.name}: {e}"
            logger.error(error_msg)
            session.errors.append(error_msg)

        # Deduplicate
        unique_papers = self._deduplicate_papers(papers)
        session.papers_fetched = len(unique_papers)

        logger.info(f"Fetched {len(unique_papers)} unique papers for {domain.name}")

        # Process each paper
        for paper in unique_papers[:max_papers]:
            try:
                result = await self.brain.learn_from_paper(paper.to_dict())
                session.claims_extracted += result['claims_extracted']
                session.connections_found += result['connections_found']
                session.patterns_detected += result['patterns_detected']

            except Exception as e:
                error_msg = f"Error processing paper {paper.external_id}: {e}"
                logger.error(error_msg)
                session.errors.append(error_msg)

        await self.brain.think(
            'observation',
            f"Completed {domain.name} session: {session.papers_fetched} papers, "
            f"{session.claims_extracted} claims, {session.connections_found} connections",
            domains=[domain],
            importance=0.6
        )

        return session

    async def learn_all_domains(
        self,
        max_papers_per_domain: int = None,
        parallel: bool = True
    ) -> List[LearningSession]:
        """
        Learn from all 6 domains.

        Args:
            max_papers_per_domain: Max papers per domain
            parallel: Whether to parallelize domain learning

        Returns:
            List of LearningSession results
        """
        max_papers = max_papers_per_domain or self.max_papers_per_domain

        await self.brain.think(
            'observation',
            f"Initiating full learning cycle across all 6 domains. "
            f"Target: {max_papers} papers per domain.",
            importance=0.7
        )

        if parallel:
            # Run all domains in parallel
            tasks = [
                self.learn_domain(domain, max_papers)
                for domain in Domain
            ]
            sessions = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            results = []
            for i, session in enumerate(sessions):
                if isinstance(session, Exception):
                    logger.error(f"Domain learning failed: {session}")
                else:
                    results.append(session)

            return results
        else:
            # Sequential learning
            sessions = []
            for domain in Domain:
                session = await self.learn_domain(domain, max_papers)
                sessions.append(session)
            return sessions

    async def learn_cross_domain(
        self,
        concepts: List[str],
        max_papers: int = 50
    ) -> LearningSession:
        """
        Specifically search for cross-domain content.

        Targets papers that bridge multiple domains.

        Args:
            concepts: Bridge concepts to search for
            max_papers: Maximum papers to fetch

        Returns:
            LearningSession with results
        """
        session = LearningSession(
            session_id=f"cross_domain_{datetime.now().isoformat()}",
            domain=None,  # Cross-domain
            started_at=datetime.now()
        )

        await self.brain.think(
            'observation',
            f"Searching for cross-domain papers on: {', '.join(concepts)}",
            importance=0.8
        )

        papers = []

        # Search each concept across multiple sources
        for concept in concepts:
            try:
                # OpenAlex search
                openalex_results = await self.openalex.search(
                    query=concept,
                    limit=max_papers // len(concepts)
                )
                papers.extend(openalex_results)

                # Semantic Scholar (often has cross-domain content)
                s2_results = await self.semantic_scholar.search(
                    query=concept,
                    limit=max_papers // len(concepts)
                )
                papers.extend(s2_results)

            except Exception as e:
                logger.error(f"Error searching for '{concept}': {e}")

        # Deduplicate and prioritize papers that span multiple domains
        unique_papers = self._deduplicate_papers(papers)

        # Score papers by domain diversity
        scored_papers = []
        for paper in unique_papers:
            domains = self._detect_domains(paper)
            if len(domains) >= 2:
                # Boost cross-domain papers
                score = len(domains) * self.cross_domain_boost
                scored_papers.append((score, paper))

        # Sort by score and take top
        scored_papers.sort(key=lambda x: x[0], reverse=True)
        top_papers = [p for _, p in scored_papers[:max_papers]]

        session.papers_fetched = len(top_papers)

        # Process
        for paper in top_papers:
            try:
                result = await self.brain.learn_from_paper(paper.to_dict())
                session.claims_extracted += result['claims_extracted']
                session.connections_found += result['connections_found']
                session.patterns_detected += result['patterns_detected']
            except Exception as e:
                session.errors.append(str(e))

        await self.brain.think(
            'insight',
            f"Cross-domain search found {session.papers_fetched} papers spanning multiple domains. "
            f"Extracted {session.claims_extracted} claims with {session.connections_found} connections.",
            importance=0.9
        )

        return session

    async def _fetch_openalex(
        self,
        strategy: DomainStrategy,
        limit: int,
        days_back: int
    ) -> List[Paper]:
        """Fetch papers from OpenAlex."""
        papers = []

        # Calculate date range
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        # Search by concepts
        for concept_id in strategy.openalex_concepts[:2]:  # Limit concepts
            try:
                results = await self.openalex.search(
                    query="",
                    concept_ids=[concept_id],
                    limit=limit // len(strategy.openalex_concepts),
                    from_date=from_date,
                    is_oa=True,  # Prefer open access
                    sort="cited_by_count"
                )
                papers.extend(results)
            except Exception as e:
                logger.error(f"OpenAlex search failed for concept {concept_id}: {e}")

        # Also search by keywords
        for keyword in strategy.keywords[:3]:
            try:
                results = await self.openalex.search(
                    query=keyword,
                    limit=limit // 10,
                    from_date=from_date
                )
                papers.extend(results)
            except Exception as e:
                logger.error(f"OpenAlex keyword search failed for '{keyword}': {e}")

        return papers

    async def _fetch_arxiv(
        self,
        strategy: DomainStrategy,
        limit: int,
        days_back: int
    ) -> List[Paper]:
        """Fetch papers from arXiv."""
        papers = []

        for category in strategy.arxiv_categories[:3]:
            try:
                results = await self.arxiv.search(
                    query=f"cat:{category}",
                    limit=limit // len(strategy.arxiv_categories),
                    sort_by="submittedDate",
                    sort_order="descending"
                )
                papers.extend(results)
            except Exception as e:
                logger.error(f"arXiv search failed for category {category}: {e}")

        return papers

    async def _fetch_pubmed(
        self,
        strategy: DomainStrategy,
        limit: int,
        days_back: int
    ) -> List[Paper]:
        """Fetch papers from PubMed."""
        papers = []

        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

        for mesh_term in strategy.pubmed_mesh[:3]:
            try:
                results = await self.pubmed.search(
                    query=f"{mesh_term}[MeSH Terms]",
                    limit=limit // len(strategy.pubmed_mesh),
                    from_date=from_date
                )
                papers.extend(results)
            except Exception as e:
                logger.error(f"PubMed search failed for MeSH term {mesh_term}: {e}")

        return papers

    async def _fetch_semantic_scholar(
        self,
        strategy: DomainStrategy,
        limit: int,
        days_back: int
    ) -> List[Paper]:
        """Fetch papers from Semantic Scholar."""
        papers = []

        # Search by keywords, filter for high-impact
        for keyword in strategy.keywords[:2]:
            try:
                results = await self.semantic_scholar.search(
                    query=keyword,
                    limit=limit // 2,
                    min_citation_count=10,  # Focus on impactful papers
                    open_access_only=True
                )
                papers.extend(results)
            except Exception as e:
                logger.error(f"Semantic Scholar search failed for '{keyword}': {e}")

        return papers

    def _deduplicate_papers(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicate papers based on ID and title similarity."""
        seen_ids = set()
        seen_titles = set()
        unique = []

        for paper in papers:
            # Check by ID
            if paper.external_id in seen_ids:
                continue
            if paper.external_id in self.seen_ids:
                continue

            # Check by normalized title
            title_normalized = paper.title.lower().strip()
            title_hash = hash_learner.compute_shake256(title_normalized)[:16]

            if title_hash in seen_titles:
                continue

            seen_ids.add(paper.external_id)
            seen_titles.add(title_hash)
            self.seen_ids.add(paper.external_id)
            unique.append(paper)

        return unique

    def _detect_domains(self, paper: Paper) -> List[Domain]:
        """Detect which domains a paper belongs to."""
        domains = []
        text = f"{paper.title} {paper.abstract or ''} {' '.join(paper.concepts)}".lower()

        for domain, strategy in DOMAIN_STRATEGIES.items():
            score = 0
            for keyword in strategy.keywords:
                if keyword in text:
                    score += 1

            if score >= 2:  # At least 2 keyword matches
                domains.append(domain)

        return domains

    async def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of all learning sessions."""
        total_papers = sum(s.papers_fetched for s in self.sessions)
        total_claims = sum(s.claims_extracted for s in self.sessions)
        total_connections = sum(s.connections_found for s in self.sessions)
        total_patterns = sum(s.patterns_detected for s in self.sessions)

        by_domain = {}
        for session in self.sessions:
            if session.domain:
                domain_name = session.domain.name
                if domain_name not in by_domain:
                    by_domain[domain_name] = {
                        'papers': 0, 'claims': 0,
                        'connections': 0, 'patterns': 0
                    }
                by_domain[domain_name]['papers'] += session.papers_fetched
                by_domain[domain_name]['claims'] += session.claims_extracted
                by_domain[domain_name]['connections'] += session.connections_found
                by_domain[domain_name]['patterns'] += session.patterns_detected

        return {
            'total_sessions': len(self.sessions),
            'total_papers': total_papers,
            'total_claims': total_claims,
            'total_connections': total_connections,
            'total_patterns': total_patterns,
            'by_domain': by_domain,
            'unique_papers_seen': len(self.seen_ids)
        }
