"""
arXiv API Client
https://arxiv.org/help/api/

arXiv provides preprints in physics, mathematics, computer science,
quantitative biology, quantitative finance, statistics, and more.
No API key required. Be gentle with rate limits.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, List, Dict, Any
import re

from .base import AcademicSource, Paper, Author, SourceType

logger = logging.getLogger(__name__)

# arXiv namespaces for XML parsing
ARXIV_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom',
    'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
}


class ArxivClient(AcademicSource):
    """
    arXiv API client.

    arXiv uses an Atom feed format for API responses.
    Categories of interest for Cipher:
    - math.* - Mathematics
    - q-bio.NC - Quantitative Biology / Neurons and Cognition
    - cs.NE - Computer Science / Neural and Evolutionary Computing
    - cs.AI - Artificial Intelligence
    - stat.* - Statistics
    """

    def __init__(self, requests_per_second: float = 1.0):
        """
        Initialize arXiv client.

        arXiv asks for a 3-second delay between requests.
        We're slightly more aggressive but still polite.
        """
        super().__init__(
            base_url="http://export.arxiv.org/api/query",
            requests_per_second=requests_per_second
        )

    @property
    def source_type(self) -> SourceType:
        return SourceType.ARXIV

    def _parse_entry(self, entry: ET.Element) -> Paper:
        """Parse arXiv Atom entry into Paper object."""

        def find_text(tag: str, ns: str = 'atom') -> Optional[str]:
            elem = entry.find(f'{ns}:{tag}', ARXIV_NS)
            return elem.text.strip() if elem is not None and elem.text else None

        def find_all(tag: str, ns: str = 'atom') -> List[ET.Element]:
            return entry.findall(f'{ns}:{tag}', ARXIV_NS)

        # Parse ID (extract arXiv ID from URL)
        arxiv_id = find_text('id')
        if arxiv_id:
            # Extract ID from URL: http://arxiv.org/abs/2301.12345v1
            match = re.search(r'arxiv.org/abs/(.+)$', arxiv_id)
            if match:
                arxiv_id = match.group(1)

        # Parse authors
        authors = []
        for author_elem in find_all('author'):
            name_elem = author_elem.find('atom:name', ARXIV_NS)
            affil_elem = author_elem.find('arxiv:affiliation', ARXIV_NS)
            authors.append(Author(
                name=name_elem.text if name_elem is not None else 'Unknown',
                affiliation=affil_elem.text if affil_elem is not None else None
            ))

        # Parse publication date
        pub_date = None
        published = find_text('published')
        if published:
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Parse categories
        categories = []
        for cat_elem in find_all('category'):
            term = cat_elem.get('term')
            if term:
                categories.append(term)

        # Get PDF link
        pdf_url = None
        for link in find_all('link'):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href')
                break

        # Get abstract page URL
        page_url = None
        for link in find_all('link'):
            if link.get('type') == 'text/html':
                page_url = link.get('href')
                break

        # Parse journal reference if available
        journal_ref = entry.find('arxiv:journal_ref', ARXIV_NS)
        journal = journal_ref.text if journal_ref is not None else None

        # Parse DOI if available
        doi_elem = entry.find('arxiv:doi', ARXIV_NS)
        doi = doi_elem.text if doi_elem is not None else None

        # Get primary category
        primary_cat = entry.find('arxiv:primary_category', ARXIV_NS)
        primary_category = primary_cat.get('term') if primary_cat is not None else None

        return Paper(
            external_id=arxiv_id or '',
            source_type=self.source_type,
            title=find_text('title') or 'Untitled',
            abstract=find_text('summary'),
            authors=authors,
            publication_date=pub_date,
            journal=journal,
            citation_count=0,  # arXiv doesn't provide citations
            concepts=categories,
            url=page_url,
            pdf_url=pdf_url,
            doi=doi,
            raw_metadata={
                'arxiv_id': arxiv_id,
                'primary_category': primary_category,
                'categories': categories,
                'comment': find_text('comment', 'arxiv')
            }
        )

    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        categories: Optional[List[str]] = None,
        sort_by: str = "relevance",
        sort_order: str = "descending"
    ) -> List[Paper]:
        """
        Search arXiv papers.

        Args:
            query: Search query (supports arXiv query syntax)
            limit: Max results (max 2000 per request)
            offset: Start index
            categories: Filter by arXiv categories (e.g., ["math.AG", "cs.AI"])
            sort_by: "relevance", "lastUpdatedDate", or "submittedDate"
            sort_order: "ascending" or "descending"

        Returns:
            List of Paper objects

        Query syntax examples:
            - "all:electron" - Search all fields
            - "ti:neural network" - Title search
            - "au:bengio" - Author search
            - "abs:transformer" - Abstract search
            - "cat:cs.AI" - Category search
        """
        # Build search query
        search_query = query

        # Add category filter if specified
        if categories:
            cat_query = ' OR '.join(f'cat:{cat}' for cat in categories)
            if search_query:
                search_query = f'({search_query}) AND ({cat_query})'
            else:
                search_query = cat_query

        params = {
            'search_query': search_query,
            'start': offset,
            'max_results': min(limit, 2000),
            'sortBy': sort_by,
            'sortOrder': sort_order
        }

        try:
            xml_response = await self._get_xml(self.base_url, params)
            root = ET.fromstring(xml_response)

            papers = []
            for entry in root.findall('atom:entry', ARXIV_NS):
                papers.append(self._parse_entry(entry))

            return papers

        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []

    async def fetch(self, paper_id: str) -> Optional[Paper]:
        """
        Fetch a single paper by arXiv ID.

        Args:
            paper_id: arXiv ID (e.g., "2301.12345" or "math/0211159")

        Returns:
            Paper object or None
        """
        # Clean up ID
        paper_id = paper_id.replace('arXiv:', '').strip()

        params = {
            'id_list': paper_id,
            'max_results': 1
        }

        try:
            xml_response = await self._get_xml(self.base_url, params)
            root = ET.fromstring(xml_response)

            entries = root.findall('atom:entry', ARXIV_NS)
            if entries:
                return self._parse_entry(entries[0])
            return None

        except Exception as e:
            logger.error(f"arXiv fetch failed for {paper_id}: {e}")
            return None

    async def search_by_category(
        self,
        category: str,
        limit: int = 100,
        **kwargs
    ) -> List[Paper]:
        """
        Search for papers in a specific arXiv category.

        Args:
            category: arXiv category (e.g., "math.AG", "cs.AI", "q-bio.NC")
            limit: Max results

        Returns:
            List of Paper objects
        """
        return await self.search(
            query=f'cat:{category}',
            limit=limit,
            **kwargs
        )

    async def search_recent(
        self,
        query: str,
        days: int = 30,
        **kwargs
    ) -> List[Paper]:
        """
        Search for recent papers.

        Note: arXiv doesn't support date range filtering in the API,
        so we sort by submission date and filter client-side.
        """
        papers = await self.search(
            query=query,
            sort_by="submittedDate",
            sort_order="descending",
            **kwargs
        )

        if days > 0:
            cutoff = datetime.now().timestamp() - (days * 86400)
            papers = [
                p for p in papers
                if p.publication_date and p.publication_date.timestamp() >= cutoff
            ]

        return papers

    async def get_paper_versions(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        Get all versions of a paper.

        arXiv keeps all versions - useful for tracking paper evolution.
        """
        # This requires scraping or using arxiv package
        # For now, just return the current version
        paper = await self.fetch(paper_id)
        if paper:
            return [{
                'version': paper_id,
                'date': paper.publication_date,
                'title': paper.title
            }]
        return []
