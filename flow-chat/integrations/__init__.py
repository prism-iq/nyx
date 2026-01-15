"""
CIPHER API Integrations
Academic paper sources: OpenAlex, arXiv, PubMed, Semantic Scholar
"""

from .base import AcademicSource, Paper
from .openalex import OpenAlexClient
from .arxiv import ArxivClient
from .pubmed import PubMedClient
from .semantic_scholar import SemanticScholarClient

__all__ = [
    'AcademicSource',
    'Paper',
    'OpenAlexClient',
    'ArxivClient',
    'PubMedClient',
    'SemanticScholarClient',
]
