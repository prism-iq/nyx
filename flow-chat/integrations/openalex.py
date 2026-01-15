"""
OpenAlex API Client
https://docs.openalex.org/

OpenAlex is a free, open catalog of 250M+ scholarly works.
No API key required. Very generous rate limits (10+ rps with polite email).
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import AcademicSource, Paper, Author, SourceType

logger = logging.getLogger(__name__)


class OpenAlexClient(AcademicSource):
    """
    OpenAlex API client.

    OpenAlex provides:
    - Works (papers)
    - Authors
    - Venues (journals)
    - Institutions
    - Concepts (topics)

    All data is free and openly licensed (CC0).
    """

    def __init__(
        self,
        email: str = "cipher@pwnd.icu",
        requests_per_second: float = 10.0
    ):
        """
        Initialize OpenAlex client.

        Args:
            email: Contact email for polite pool (faster rate limits)
            requests_per_second: Rate limit
        """
        super().__init__(
            base_url="https://api.openalex.org",
            requests_per_second=requests_per_second
        )
        self.email = email

    @property
    def source_type(self) -> SourceType:
        return SourceType.OPENALEX

    def _default_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': f'Cipher/1.0 (mailto:{self.email})',
            'Accept': 'application/json'
        }

    def _parse_work(self, work: Dict[str, Any]) -> Paper:
        """Parse OpenAlex work into Paper object."""
        # Parse authors
        authors = []
        for authorship in work.get('authorships', []):
            author_data = authorship.get('author', {})
            institution = None
            if authorship.get('institutions'):
                institution = authorship['institutions'][0].get('display_name')

            authors.append(Author(
                name=author_data.get('display_name', 'Unknown'),
                affiliation=institution,
                orcid=author_data.get('orcid')
            ))

        # Parse publication date
        pub_date = None
        if work.get('publication_date'):
            try:
                pub_date = datetime.fromisoformat(work['publication_date'])
            except ValueError:
                pass

        # Parse concepts
        concepts = [
            c.get('display_name')
            for c in work.get('concepts', [])
            if c.get('display_name')
        ]

        # Get PDF URL from open access info
        pdf_url = None
        oa_info = work.get('open_access', {})
        if oa_info.get('is_oa'):
            pdf_url = oa_info.get('oa_url')

        # Get primary location
        primary_location = work.get('primary_location', {}) or {}
        source = primary_location.get('source', {}) or {}

        return Paper(
            external_id=work.get('id', '').replace('https://openalex.org/', ''),
            source_type=self.source_type,
            title=work.get('title', 'Untitled'),
            abstract=self._reconstruct_abstract(work.get('abstract_inverted_index')),
            authors=authors,
            publication_date=pub_date,
            journal=source.get('display_name'),
            citation_count=work.get('cited_by_count', 0),
            concepts=concepts,
            url=work.get('id'),
            pdf_url=pdf_url,
            doi=work.get('doi'),
            raw_metadata={
                'openalex_id': work.get('id'),
                'type': work.get('type'),
                'is_oa': oa_info.get('is_oa', False),
                'cited_by_api_url': work.get('cited_by_api_url')
            }
        )

    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
        """
        Reconstruct abstract from OpenAlex's inverted index format.

        OpenAlex stores abstracts as {word: [positions]} to save space.
        """
        if not inverted_index:
            return None

        # Find max position to size the array
        max_pos = max(
            pos
            for positions in inverted_index.values()
            for pos in positions
        )

        # Reconstruct
        words = [''] * (max_pos + 1)
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word

        return ' '.join(words)

    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        concept_ids: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        is_oa: Optional[bool] = None,
        sort: str = "relevance_score:desc"
    ) -> List[Paper]:
        """
        Search OpenAlex works.

        Args:
            query: Search query (searches title, abstract)
            limit: Max results (max 200 per request)
            offset: Pagination offset
            concept_ids: Filter by OpenAlex concept IDs
            from_date: Filter by publication date (YYYY-MM-DD)
            to_date: Filter by publication date (YYYY-MM-DD)
            is_oa: Filter to open access only
            sort: Sort order (relevance_score:desc, cited_by_count:desc, publication_date:desc)

        Returns:
            List of Paper objects
        """
        # Build filter string
        filters = []
        search_query = None

        if query:
            # Use search parameter for full-text search (not filter)
            search_query = query

        if concept_ids:
            concept_filter = '|'.join(concept_ids)
            filters.append(f'concepts.id:{concept_filter}')

        if from_date:
            filters.append(f'from_publication_date:{from_date}')

        if to_date:
            filters.append(f'to_publication_date:{to_date}')

        if is_oa is not None:
            filters.append(f'is_oa:{"true" if is_oa else "false"}')

        params = {
            'per_page': min(limit, 200),
            'page': (offset // min(limit, 200)) + 1,
            'sort': sort,
            'mailto': self.email
        }

        if search_query:
            params['search'] = search_query

        if filters:
            params['filter'] = ','.join(filters)

        url = f"{self.base_url}/works"

        try:
            data = await self._get(url, params)
            works = data.get('results', [])
            return [self._parse_work(w) for w in works]
        except Exception as e:
            logger.error(f"OpenAlex search failed: {e}")
            return []

    async def fetch(self, paper_id: str) -> Optional[Paper]:
        """
        Fetch a single work by OpenAlex ID or DOI.

        Args:
            paper_id: OpenAlex ID (W1234567890) or DOI

        Returns:
            Paper object or None
        """
        # Handle DOI
        if paper_id.startswith('10.') or paper_id.startswith('https://doi.org/'):
            url = f"{self.base_url}/works/doi:{paper_id}"
        elif paper_id.startswith('W'):
            url = f"{self.base_url}/works/{paper_id}"
        else:
            url = f"{self.base_url}/works/{paper_id}"

        params = {'mailto': self.email}

        try:
            data = await self._get(url, params)
            return self._parse_work(data)
        except Exception as e:
            logger.error(f"OpenAlex fetch failed for {paper_id}: {e}")
            return None

    async def get_citations(self, paper_id: str, limit: int = 100) -> List[Paper]:
        """
        Get papers that cite a given work.

        Args:
            paper_id: OpenAlex ID of the work
            limit: Max results

        Returns:
            List of citing papers
        """
        params = {
            'filter': f'cites:{paper_id}',
            'per_page': min(limit, 200),
            'mailto': self.email
        }

        url = f"{self.base_url}/works"

        try:
            data = await self._get(url, params)
            works = data.get('results', [])
            return [self._parse_work(w) for w in works]
        except Exception as e:
            logger.error(f"OpenAlex citations fetch failed: {e}")
            return []

    async def get_references(self, paper_id: str, limit: int = 100) -> List[Paper]:
        """
        Get papers referenced by a given work.

        Args:
            paper_id: OpenAlex ID of the work
            limit: Max results

        Returns:
            List of referenced papers
        """
        # First get the work to find its references
        work = await self.fetch(paper_id)
        if not work:
            return []

        # OpenAlex includes referenced_works in the work object
        ref_ids = work.raw_metadata.get('referenced_works', [])

        # Fetch each reference (batch if many)
        papers = []
        for ref_id in ref_ids[:limit]:
            paper = await self.fetch(ref_id)
            if paper:
                papers.append(paper)

        return papers

    async def search_by_concept(
        self,
        concept_id: str,
        limit: int = 100,
        **kwargs
    ) -> List[Paper]:
        """
        Search for papers tagged with a specific OpenAlex concept.

        Args:
            concept_id: OpenAlex concept ID (e.g., "C33923547" for Mathematics)
            limit: Max results

        Returns:
            List of Paper objects
        """
        return await self.search(
            query="",
            concept_ids=[concept_id],
            limit=limit,
            **kwargs
        )

    async def get_concept_info(self, concept_id: str) -> Optional[Dict]:
        """
        Get information about an OpenAlex concept.

        Useful for understanding domain hierarchies.
        """
        url = f"{self.base_url}/concepts/{concept_id}"
        params = {'mailto': self.email}

        try:
            return await self._get(url, params)
        except Exception as e:
            logger.error(f"OpenAlex concept fetch failed: {e}")
            return None
