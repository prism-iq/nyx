"""
Base classes for academic API integrations
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Academic source types"""
    OPENALEX = "openalex"
    ARXIV = "arxiv"
    PUBMED = "pubmed"
    SEMANTIC_SCHOLAR = "semantic_scholar"


@dataclass
class Author:
    """Paper author"""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None


@dataclass
class Paper:
    """
    Normalized paper representation across all sources.
    This is the common format Cipher works with internally.
    """
    # Identifiers
    external_id: str              # DOI, arXiv ID, PMID, etc.
    source_type: SourceType

    # Core metadata
    title: str
    abstract: Optional[str] = None
    authors: List[Author] = field(default_factory=list)
    publication_date: Optional[datetime] = None
    journal: Optional[str] = None

    # Metrics
    citation_count: int = 0

    # Classification
    domains: List[str] = field(default_factory=list)  # Cipher domains
    concepts: List[str] = field(default_factory=list)  # Source concepts/keywords
    mesh_terms: List[str] = field(default_factory=list)  # PubMed MeSH

    # URLs
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None

    # Raw metadata (source-specific)
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion."""
        return {
            'external_id': self.external_id,
            'source_type': self.source_type.value,
            'title': self.title,
            'abstract': self.abstract,
            'authors': [
                {'name': a.name, 'affiliation': a.affiliation, 'orcid': a.orcid}
                for a in self.authors
            ],
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'journal': self.journal,
            'citation_count': self.citation_count,
            'domains': self.domains,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'metadata': {
                'doi': self.doi,
                'concepts': self.concepts,
                'mesh_terms': self.mesh_terms,
                **self.raw_metadata
            }
        }


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    """

    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.tokens = requests_per_second
        self.last_update = asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request can be made."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class AcademicSource(ABC):
    """
    Abstract base class for academic paper sources.

    All API clients inherit from this and implement the search/fetch methods.
    """

    def __init__(
        self,
        base_url: str,
        requests_per_second: float = 1.0,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.rate_limiter = RateLimiter(requests_per_second)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    @abstractmethod
    def source_type(self) -> SourceType:
        """Return the source type enum."""
        pass

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                headers=self._default_headers()
            )
        return self._session

    def _default_headers(self) -> Dict[str, str]:
        """Default HTTP headers. Override in subclasses."""
        return {
            'User-Agent': 'Cipher/1.0 (https://github.com/prism-iq/cipher; mailto:cipher@pwnd.icu)'
        }

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a rate-limited GET request.
        """
        await self.rate_limiter.acquire()
        session = await self.get_session()

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {url} - {e}")
            raise

    async def _get_xml(self, url: str, params: Optional[Dict] = None) -> str:
        """
        Make a rate-limited GET request expecting XML response.
        """
        await self.rate_limiter.acquire()
        session = await self.get_session()

        try:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"API request failed: {url} - {e}")
            raise

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        **kwargs
    ) -> List[Paper]:
        """
        Search for papers matching a query.

        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Pagination offset
            **kwargs: Source-specific parameters

        Returns:
            List of Paper objects
        """
        pass

    @abstractmethod
    async def fetch(self, paper_id: str) -> Optional[Paper]:
        """
        Fetch a single paper by ID.

        Args:
            paper_id: The paper identifier (DOI, arXiv ID, etc.)

        Returns:
            Paper object or None if not found
        """
        pass

    async def stream(
        self,
        query: str,
        max_results: int = 1000,
        batch_size: int = 100,
        **kwargs
    ) -> AsyncIterator[Paper]:
        """
        Stream papers matching a query (handles pagination).

        This is the preferred method for large-scale fetching.
        Yields papers one at a time to minimize memory usage.

        Args:
            query: Search query
            max_results: Maximum total results
            batch_size: Results per API call
            **kwargs: Source-specific parameters

        Yields:
            Paper objects
        """
        offset = 0
        total_yielded = 0

        while total_yielded < max_results:
            try:
                papers = await self.search(
                    query=query,
                    limit=min(batch_size, max_results - total_yielded),
                    offset=offset,
                    **kwargs
                )

                if not papers:
                    break

                for paper in papers:
                    yield paper
                    total_yielded += 1

                    if total_yielded >= max_results:
                        break

                offset += len(papers)

            except Exception as e:
                logger.error(f"Stream error at offset {offset}: {e}")
                break

    async def search_by_concepts(
        self,
        concepts: List[str],
        operator: str = 'AND',
        **kwargs
    ) -> List[Paper]:
        """
        Search by concept list.

        Args:
            concepts: List of concepts/keywords
            operator: 'AND' or 'OR' for combining concepts
            **kwargs: Additional parameters

        Returns:
            List of Paper objects
        """
        if operator.upper() == 'AND':
            query = ' AND '.join(f'"{c}"' for c in concepts)
        else:
            query = ' OR '.join(f'"{c}"' for c in concepts)

        return await self.search(query, **kwargs)

    async def search_recent(
        self,
        query: str,
        days: int = 30,
        **kwargs
    ) -> List[Paper]:
        """
        Search for recent papers.

        Args:
            query: Search query
            days: How far back to search
            **kwargs: Additional parameters

        Returns:
            List of Paper objects
        """
        # Default implementation - subclasses may override with native date filtering
        papers = await self.search(query, **kwargs)

        if days > 0:
            cutoff = datetime.now().timestamp() - (days * 86400)
            papers = [
                p for p in papers
                if p.publication_date and p.publication_date.timestamp() >= cutoff
            ]

        return papers

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} base_url={self.base_url}>"
