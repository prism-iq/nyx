"""
Semantic Scholar API Client
https://api.semanticscholar.org/

Semantic Scholar provides citation data and AI-extracted information
about academic papers. Free tier available, API key for higher limits.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import AcademicSource, Paper, Author, SourceType

logger = logging.getLogger(__name__)


class SemanticScholarClient(AcademicSource):
    """
    Semantic Scholar Graph API client.

    Provides:
    - Paper search and metadata
    - Citation counts and graphs
    - Author information
    - AI-extracted entities and topics

    Rate limits:
    - Without API key: 100 requests/5 minutes
    - With API key: 1000+ requests/5 minutes
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        requests_per_second: float = 5.0
    ):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: S2 API key (optional, get from https://www.semanticscholar.org/product/api)
            requests_per_second: Rate limit
        """
        super().__init__(
            base_url="https://api.semanticscholar.org/graph/v1",
            requests_per_second=requests_per_second
        )
        self.api_key = api_key

    @property
    def source_type(self) -> SourceType:
        return SourceType.SEMANTIC_SCHOLAR

    def _default_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': 'Cipher/1.0 (mailto:cipher@pwnd.icu)',
            'Accept': 'application/json'
        }
        if self.api_key:
            headers['x-api-key'] = self.api_key
        return headers

    def _parse_paper(self, paper_data: Dict[str, Any]) -> Paper:
        """Parse Semantic Scholar paper data into Paper object."""

        # Parse authors
        authors = []
        for author in paper_data.get('authors', []):
            authors.append(Author(
                name=author.get('name', 'Unknown'),
                affiliation=None,  # S2 doesn't always provide this
                orcid=None
            ))

        # Parse publication date
        pub_date = None
        year = paper_data.get('year')
        pub_date_str = paper_data.get('publicationDate')
        if pub_date_str:
            try:
                pub_date = datetime.fromisoformat(pub_date_str)
            except ValueError:
                pass
        elif year:
            try:
                pub_date = datetime(int(year), 1, 1)
            except (ValueError, TypeError):
                pass

        # Get fields of study as concepts
        concepts = paper_data.get('fieldsOfStudy', []) or []

        # Get external IDs
        external_ids = paper_data.get('externalIds', {}) or {}
        doi = external_ids.get('DOI')
        arxiv_id = external_ids.get('ArXiv')
        pmid = external_ids.get('PubMed')

        # Build paper ID (prefer S2 paperId)
        paper_id = paper_data.get('paperId', '')

        # URLs
        url = paper_data.get('url')
        pdf_url = None
        if paper_data.get('isOpenAccess') and paper_data.get('openAccessPdf'):
            pdf_url = paper_data['openAccessPdf'].get('url')

        return Paper(
            external_id=f"S2:{paper_id}",
            source_type=self.source_type,
            title=paper_data.get('title', 'Untitled'),
            abstract=paper_data.get('abstract'),
            authors=authors,
            publication_date=pub_date,
            journal=paper_data.get('venue') or paper_data.get('journal', {}).get('name'),
            citation_count=paper_data.get('citationCount', 0),
            concepts=concepts,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            raw_metadata={
                's2_paper_id': paper_id,
                'arxiv_id': arxiv_id,
                'pmid': pmid,
                'reference_count': paper_data.get('referenceCount', 0),
                'influential_citation_count': paper_data.get('influentialCitationCount', 0),
                'is_open_access': paper_data.get('isOpenAccess', False),
                'fields_of_study': concepts,
                'tldr': paper_data.get('tldr', {}).get('text') if paper_data.get('tldr') else None
            }
        )

    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        year: Optional[str] = None,
        fields_of_study: Optional[List[str]] = None,
        open_access_only: bool = False,
        min_citation_count: Optional[int] = None
    ) -> List[Paper]:
        """
        Search Semantic Scholar papers.

        Args:
            query: Search query
            limit: Max results (max 100 per request)
            offset: Pagination offset
            year: Filter by year (e.g., "2020", "2019-2021", "-2020", "2020-")
            fields_of_study: Filter by fields (e.g., ["Computer Science", "Medicine"])
            open_access_only: Only return open access papers
            min_citation_count: Minimum citation count

        Returns:
            List of Paper objects
        """
        # Fields to request
        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'publicationDate', 'venue', 'journal', 'citationCount',
            'referenceCount', 'influentialCitationCount', 'isOpenAccess',
            'openAccessPdf', 'fieldsOfStudy', 'url', 'externalIds', 'tldr'
        ]

        params = {
            'query': query,
            'limit': min(limit, 100),
            'offset': offset,
            'fields': ','.join(fields)
        }

        if year:
            params['year'] = year

        if fields_of_study:
            params['fieldsOfStudy'] = ','.join(fields_of_study)

        if open_access_only:
            params['openAccessPdf'] = ''

        if min_citation_count is not None:
            params['minCitationCount'] = min_citation_count

        url = f"{self.base_url}/paper/search"

        try:
            data = await self._get(url, params)
            papers_data = data.get('data', [])
            return [self._parse_paper(p) for p in papers_data]

        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []

    async def fetch(self, paper_id: str) -> Optional[Paper]:
        """
        Fetch a single paper by ID.

        Args:
            paper_id: S2 paper ID, DOI, arXiv ID, or other identifier
                     Formats: "S2:abc123", "DOI:10.1234/...", "arXiv:2301.12345"

        Returns:
            Paper object or None
        """
        # Parse ID format
        if paper_id.startswith('S2:'):
            paper_id = paper_id[3:]
        elif paper_id.startswith('DOI:') or paper_id.startswith('10.'):
            if paper_id.startswith('DOI:'):
                paper_id = paper_id[4:]
            paper_id = f"DOI:{paper_id}"
        elif paper_id.startswith('arXiv:'):
            pass  # Keep as-is
        elif paper_id.startswith('PMID:'):
            paper_id = f"PMID:{paper_id[5:]}"

        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'publicationDate', 'venue', 'journal', 'citationCount',
            'referenceCount', 'influentialCitationCount', 'isOpenAccess',
            'openAccessPdf', 'fieldsOfStudy', 'url', 'externalIds', 'tldr'
        ]

        url = f"{self.base_url}/paper/{paper_id}"
        params = {'fields': ','.join(fields)}

        try:
            data = await self._get(url, params)
            return self._parse_paper(data)

        except Exception as e:
            logger.error(f"Semantic Scholar fetch failed for {paper_id}: {e}")
            return None

    async def get_citations(self, paper_id: str, limit: int = 100) -> List[Paper]:
        """
        Get papers that cite a given paper.

        Args:
            paper_id: S2 paper ID or external ID
            limit: Max results

        Returns:
            List of citing papers
        """
        if paper_id.startswith('S2:'):
            paper_id = paper_id[3:]

        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'fieldsOfStudy', 'url', 'externalIds'
        ]

        url = f"{self.base_url}/paper/{paper_id}/citations"
        params = {
            'fields': ','.join(fields),
            'limit': min(limit, 1000)
        }

        try:
            data = await self._get(url, params)
            citations = data.get('data', [])
            papers = []
            for citation in citations:
                citing_paper = citation.get('citingPaper', {})
                if citing_paper:
                    papers.append(self._parse_paper(citing_paper))
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar citations fetch failed: {e}")
            return []

    async def get_references(self, paper_id: str, limit: int = 100) -> List[Paper]:
        """
        Get papers referenced by a given paper.

        Args:
            paper_id: S2 paper ID or external ID
            limit: Max results

        Returns:
            List of referenced papers
        """
        if paper_id.startswith('S2:'):
            paper_id = paper_id[3:]

        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'fieldsOfStudy', 'url', 'externalIds'
        ]

        url = f"{self.base_url}/paper/{paper_id}/references"
        params = {
            'fields': ','.join(fields),
            'limit': min(limit, 1000)
        }

        try:
            data = await self._get(url, params)
            references = data.get('data', [])
            papers = []
            for ref in references:
                cited_paper = ref.get('citedPaper', {})
                if cited_paper and cited_paper.get('paperId'):
                    papers.append(self._parse_paper(cited_paper))
            return papers

        except Exception as e:
            logger.error(f"Semantic Scholar references fetch failed: {e}")
            return []

    async def get_author(self, author_id: str) -> Optional[Dict[str, Any]]:
        """
        Get author information.

        Args:
            author_id: S2 author ID

        Returns:
            Author info dict or None
        """
        fields = [
            'authorId', 'name', 'affiliations', 'paperCount',
            'citationCount', 'hIndex', 'url'
        ]

        url = f"{self.base_url}/author/{author_id}"
        params = {'fields': ','.join(fields)}

        try:
            return await self._get(url, params)

        except Exception as e:
            logger.error(f"Semantic Scholar author fetch failed: {e}")
            return None

    async def get_author_papers(
        self,
        author_id: str,
        limit: int = 100
    ) -> List[Paper]:
        """
        Get papers by a specific author.

        Args:
            author_id: S2 author ID
            limit: Max results

        Returns:
            List of Paper objects
        """
        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'fieldsOfStudy', 'url', 'externalIds'
        ]

        url = f"{self.base_url}/author/{author_id}/papers"
        params = {
            'fields': ','.join(fields),
            'limit': min(limit, 1000)
        }

        try:
            data = await self._get(url, params)
            papers_data = data.get('data', [])
            return [self._parse_paper(p) for p in papers_data]

        except Exception as e:
            logger.error(f"Semantic Scholar author papers fetch failed: {e}")
            return []

    async def batch_fetch(self, paper_ids: List[str]) -> List[Paper]:
        """
        Fetch multiple papers in a single request.

        Args:
            paper_ids: List of paper IDs (max 500)

        Returns:
            List of Paper objects
        """
        if not paper_ids:
            return []

        # Clean IDs
        clean_ids = []
        for pid in paper_ids[:500]:
            if pid.startswith('S2:'):
                clean_ids.append(pid[3:])
            else:
                clean_ids.append(pid)

        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'publicationDate', 'venue', 'citationCount',
            'fieldsOfStudy', 'url', 'externalIds'
        ]

        url = f"{self.base_url}/paper/batch"
        params = {'fields': ','.join(fields)}

        # POST request for batch
        await self.rate_limiter.acquire()
        session = await self.get_session()

        try:
            async with session.post(
                url,
                params=params,
                json={'ids': clean_ids}
            ) as response:
                response.raise_for_status()
                papers_data = await response.json()

            return [
                self._parse_paper(p) for p in papers_data
                if p is not None
            ]

        except Exception as e:
            logger.error(f"Semantic Scholar batch fetch failed: {e}")
            return []

    async def recommendations(
        self,
        positive_paper_ids: List[str],
        negative_paper_ids: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Paper]:
        """
        Get paper recommendations based on seed papers.

        Args:
            positive_paper_ids: Papers to use as positive examples
            negative_paper_ids: Papers to use as negative examples (optional)
            limit: Max results

        Returns:
            List of recommended papers
        """
        fields = [
            'paperId', 'title', 'abstract', 'authors', 'year',
            'citationCount', 'fieldsOfStudy', 'url', 'externalIds'
        ]

        url = f"{self.base_url}/recommendations"

        # Clean IDs
        positive = [
            pid[3:] if pid.startswith('S2:') else pid
            for pid in positive_paper_ids
        ]

        body = {
            'positivePaperIds': positive,
            'limit': min(limit, 500)
        }

        if negative_paper_ids:
            negative = [
                pid[3:] if pid.startswith('S2:') else pid
                for pid in negative_paper_ids
            ]
            body['negativePaperIds'] = negative

        params = {'fields': ','.join(fields)}

        await self.rate_limiter.acquire()
        session = await self.get_session()

        try:
            async with session.post(url, params=params, json=body) as response:
                response.raise_for_status()
                data = await response.json()

            papers_data = data.get('recommendedPapers', [])
            return [self._parse_paper(p) for p in papers_data]

        except Exception as e:
            logger.error(f"Semantic Scholar recommendations failed: {e}")
            return []
