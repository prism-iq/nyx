"""
CIPHER Configuration Settings
All configuration in one place - no proprietary dependencies
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class DatabaseConfig:
    """PostgreSQL connection settings"""
    host: str = os.getenv("CIPHER_DB_HOST", "localhost")
    port: int = int(os.getenv("CIPHER_DB_PORT", "5432"))
    database: str = os.getenv("CIPHER_DB_NAME", "ldb")
    user: str = os.getenv("CIPHER_DB_USER", "lframework")
    password: str = os.getenv("CIPHER_DB_PASSWORD", "")

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def async_connection_string(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class APIConfig:
    """Academic API settings - all free/open access"""
    # OpenAlex - completely free, no API key needed
    openalex_base_url: str = "https://api.openalex.org"
    openalex_email: str = os.getenv("CIPHER_EMAIL", "cipher@pwnd.icu")  # Polite pool

    # arXiv - free, no API key
    arxiv_base_url: str = "http://export.arxiv.org/api/query"

    # PubMed/PMC - free, API key optional but recommended
    pubmed_base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    pubmed_api_key: Optional[str] = os.getenv("PUBMED_API_KEY")

    # Semantic Scholar - free tier available
    semantic_scholar_base_url: str = "https://api.semanticscholar.org/graph/v1"
    semantic_scholar_api_key: Optional[str] = os.getenv("S2_API_KEY")

    # Rate limits (requests per second)
    openalex_rps: float = 10.0  # Very generous
    arxiv_rps: float = 1.0      # Be nice to arXiv
    pubmed_rps: float = 3.0     # 10/s with key, 3/s without
    semantic_scholar_rps: float = 5.0


@dataclass
class DomainConfig:
    """Domain-specific search configurations"""
    mathematics: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C33923547", "C121332964", "C134306372"],  # Math, Pure Math, Applied Math
        "arxiv_categories": ["math.*", "cs.LO", "cs.CC", "stat.TH"],
        "pubmed_mesh": [],
        "keywords": ["theorem", "proof", "conjecture", "algorithm", "topology", "algebra"]
    })

    neurosciences: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C86803240", "C15744967", "C54355233"],  # Neuroscience, Cognitive, Computational
        "arxiv_categories": ["q-bio.NC", "cs.NE"],
        "pubmed_mesh": ["Neurosciences", "Brain", "Neurons", "Cognition"],
        "keywords": ["neural", "brain", "cortex", "synapse", "cognition", "plasticity"]
    })

    biology: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C86803240", "C54355233", "C185592680"],  # Biology, Genetics, Molecular
        "arxiv_categories": ["q-bio.*"],
        "pubmed_mesh": ["Biology", "Genetics", "Evolution", "Cell Biology"],
        "keywords": ["gene", "protein", "evolution", "cell", "organism", "metabolism"]
    })

    psychology: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C15744967", "C77805123"],  # Psychology, Cognitive Science
        "arxiv_categories": ["cs.HC", "cs.CY"],
        "pubmed_mesh": ["Psychology", "Behavior", "Mental Processes"],
        "keywords": ["cognition", "behavior", "perception", "memory", "emotion", "consciousness"]
    })

    medicine: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C71924100", "C126322002"],  # Medicine, Clinical
        "arxiv_categories": ["cs.AI"],  # AI in medicine
        "pubmed_mesh": ["Medicine", "Therapeutics", "Diagnosis", "Pathology"],
        "keywords": ["clinical", "patient", "treatment", "disease", "therapy", "diagnosis"]
    })

    art: dict = field(default_factory=lambda: {
        "openalex_concepts": ["C142362112", "C17744445"],  # Art, Aesthetics
        "arxiv_categories": ["cs.GR", "cs.SD", "cs.MM"],
        "pubmed_mesh": ["Art", "Creativity", "Esthetics"],
        "keywords": ["aesthetic", "creativity", "perception", "beauty", "expression", "visual"]
    })


@dataclass
class LearningConfig:
    """Learning process settings"""
    # Batch sizes
    batch_size: int = 50
    max_papers_per_session: int = 500

    # Quality thresholds
    min_citation_count: int = 0      # Include new papers
    min_quality_score: float = 0.3
    entropy_novelty_threshold: float = 0.7

    # Cross-domain settings
    cross_domain_weight: float = 2.0  # Boost cross-domain connections
    min_connection_strength: float = 0.4

    # Extraction settings
    max_claims_per_paper: int = 10
    min_claim_confidence: float = 0.5

    # Pattern detection
    min_pattern_claims: int = 3
    min_pattern_confidence: float = 0.6


@dataclass
class PathConfig:
    """File system paths"""
    base_path: Path = Path(os.getenv("CIPHER_BASE_PATH", "/opt/cipher"))

    @property
    def mind_path(self) -> Path:
        return self.base_path / "mind"

    @property
    def tools_path(self) -> Path:
        return self.base_path / "tools"

    @property
    def integrations_path(self) -> Path:
        return self.base_path / "integrations"

    @property
    def resources_path(self) -> Path:
        return self.base_path / "resources"

    @property
    def logs_path(self) -> Path:
        return self.base_path / "logs"


@dataclass
class CipherConfig:
    """Master configuration"""
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    api: APIConfig = field(default_factory=APIConfig)
    domains: DomainConfig = field(default_factory=DomainConfig)
    learning: LearningConfig = field(default_factory=LearningConfig)
    paths: PathConfig = field(default_factory=PathConfig)

    # Iron Code
    iron_code: str = "Evil must be fought wherever it is found"

    # Core principles
    principles: list = field(default_factory=lambda: [
        "Minimize prediction error (Free Energy Principle)",
        "Question every claim (Systematic Doubt)",
        "Cross-reference across domains (Synthesis)",
        "Track contradictions explicitly",
        "Generate testable hypotheses"
    ])


# Global config instance
config = CipherConfig()
