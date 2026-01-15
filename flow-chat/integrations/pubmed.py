"""
PubMed/NCBI API Client
https://www.ncbi.nlm.nih.gov/books/NBK25501/

PubMed provides access to biomedical literature from MEDLINE,
life science journals, and online books.
API key optional but recommended for higher rate limits.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio

from .base import AcademicSource, Paper, Author, SourceType

logger = logging.getLogger(__name__)


class PubMedClient(AcademicSource):
    """
    PubMed E-utilities API client.

    Uses two main endpoints:
    - esearch: Search for PMIDs
    - efetch: Fetch paper details by PMID

    Rate limits:
    - Without API key: 3 requests/second
    - With API key: 10 requests/second
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        email: str = "cipher@pwnd.icu",
        requests_per_second: float = 3.0
    ):
        """
        Initialize PubMed client.

        Args:
            api_key: NCBI API key (optional, get from https://www.ncbi.nlm.nih.gov/account/)
            email: Contact email (required by NCBI)
            requests_per_second: Rate limit
        """
        super().__init__(
            base_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
            requests_per_second=10.0 if api_key else requests_per_second
        )
        self.api_key = api_key
        self.email = email

    @property
    def source_type(self) -> SourceType:
        return SourceType.PUBMED

    def _base_params(self) -> Dict[str, str]:
        """Base parameters for all requests."""
        params = {
            'tool': 'cipher',
            'email': self.email
        }
        if self.api_key:
            params['api_key'] = self.api_key
        return params

    def _parse_article(self, article: ET.Element) -> Paper:
        """Parse PubMed article XML into Paper object."""

        def find_text(elem: ET.Element, path: str) -> Optional[str]:
            found = elem.find(path)
            return found.text if found is not None and found.text else None

        # Get PMID
        pmid_elem = article.find('.//PMID')
        pmid = pmid_elem.text if pmid_elem is not None else ''

        # Get article data
        medline = article.find('.//MedlineCitation')
        article_data = medline.find('.//Article') if medline else None

        if article_data is None:
            return Paper(
                external_id=f"PMID:{pmid}",
                source_type=self.source_type,
                title='Unknown',
                raw_metadata={'pmid': pmid}
            )

        # Parse title
        title_elem = article_data.find('.//ArticleTitle')
        title = ''.join(title_elem.itertext()) if title_elem is not None else 'Untitled'

        # Parse abstract
        abstract_parts = []
        for abstract_text in article_data.findall('.//AbstractText'):
            label = abstract_text.get('Label', '')
            text = ''.join(abstract_text.itertext())
            if label:
                abstract_parts.append(f"{label}: {text}")
            else:
                abstract_parts.append(text)
        abstract = ' '.join(abstract_parts) if abstract_parts else None

        # Parse authors
        authors = []
        author_list = article_data.find('.//AuthorList')
        if author_list is not None:
            for author_elem in author_list.findall('.//Author'):
                last_name = find_text(author_elem, './/LastName') or ''
                fore_name = find_text(author_elem, './/ForeName') or ''
                name = f"{fore_name} {last_name}".strip() or 'Unknown'

                # Get affiliation
                affil = author_elem.find('.//AffiliationInfo/Affiliation')
                affiliation = affil.text if affil is not None else None

                # Get ORCID if available
                orcid = None
                for identifier in author_elem.findall('.//Identifier'):
                    if identifier.get('Source') == 'ORCID':
                        orcid = identifier.text

                authors.append(Author(
                    name=name,
                    affiliation=affiliation,
                    orcid=orcid
                ))

        # Parse publication date
        pub_date = None
        pub_date_elem = article_data.find('.//ArticleDate')
        if pub_date_elem is None:
            pub_date_elem = medline.find('.//DateCompleted') if medline else None
        if pub_date_elem is None:
            pub_date_elem = article_data.find('.//Journal/JournalIssue/PubDate')

        if pub_date_elem is not None:
            year = find_text(pub_date_elem, './/Year')
            month = find_text(pub_date_elem, './/Month') or '01'
            day = find_text(pub_date_elem, './/Day') or '01'

            # Handle month names
            month_map = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            if month.lower() in month_map:
                month = month_map[month.lower()]

            if year:
                try:
                    pub_date = datetime(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    pass

        # Parse journal
        journal_elem = article_data.find('.//Journal/Title')
        journal = journal_elem.text if journal_elem is not None else None

        # Parse MeSH terms
        mesh_terms = []
        mesh_list = medline.find('.//MeshHeadingList') if medline else None
        if mesh_list is not None:
            for mesh in mesh_list.findall('.//MeshHeading/DescriptorName'):
                if mesh.text:
                    mesh_terms.append(mesh.text)

        # Parse keywords
        keywords = []
        keyword_list = medline.find('.//KeywordList') if medline else None
        if keyword_list is not None:
            for kw in keyword_list.findall('.//Keyword'):
                if kw.text:
                    keywords.append(kw.text)

        # Get DOI
        doi = None
        for article_id in article.findall('.//ArticleIdList/ArticleId'):
            if article_id.get('IdType') == 'doi':
                doi = article_id.text
                break

        # Get PMC ID for free full text
        pmc_id = None
        for article_id in article.findall('.//ArticleIdList/ArticleId'):
            if article_id.get('IdType') == 'pmc':
                pmc_id = article_id.text
                break

        # Build URLs
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/" if pmc_id else None

        return Paper(
            external_id=f"PMID:{pmid}",
            source_type=self.source_type,
            title=title,
            abstract=abstract,
            authors=authors,
            publication_date=pub_date,
            journal=journal,
            citation_count=0,  # PubMed doesn't provide citation counts directly
            concepts=keywords,
            mesh_terms=mesh_terms,
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            raw_metadata={
                'pmid': pmid,
                'pmc_id': pmc_id,
                'mesh_terms': mesh_terms
            }
        )

    async def _search_ids(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        sort: str = "relevance",
        mindate: Optional[str] = None,
        maxdate: Optional[str] = None
    ) -> List[str]:
        """
        Search for PMIDs matching a query.

        Returns list of PMID strings.
        """
        params = {
            **self._base_params(),
            'db': 'pubmed',
            'term': query,
            'retmax': min(limit, 10000),
            'retstart': offset,
            'retmode': 'json',
            'sort': sort
        }

        if mindate:
            params['mindate'] = mindate
            params['datetype'] = 'pdat'  # Publication date

        if maxdate:
            params['maxdate'] = maxdate
            params['datetype'] = 'pdat'

        url = f"{self.base_url}/esearch.fcgi"

        try:
            data = await self._get(url, params)
            return data.get('esearchresult', {}).get('idlist', [])
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    async def _fetch_details(self, pmids: List[str]) -> List[Paper]:
        """
        Fetch paper details for a list of PMIDs.
        """
        if not pmids:
            return []

        params = {
            **self._base_params(),
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'full'
        }

        url = f"{self.base_url}/efetch.fcgi"

        try:
            xml_response = await self._get_xml(url, params)
            root = ET.fromstring(xml_response)

            papers = []
            for article in root.findall('.//PubmedArticle'):
                papers.append(self._parse_article(article))

            return papers

        except Exception as e:
            logger.error(f"PubMed fetch failed: {e}")
            return []

    async def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        mesh_terms: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sort: str = "relevance"
    ) -> List[Paper]:
        """
        Search PubMed papers.

        Args:
            query: Search query (supports PubMed query syntax)
            limit: Max results
            offset: Pagination offset
            mesh_terms: Filter by MeSH terms
            from_date: Filter by date (YYYY/MM/DD)
            to_date: Filter by date (YYYY/MM/DD)
            sort: "relevance" or "pub_date"

        Returns:
            List of Paper objects

        Query syntax examples:
            - "cancer" - Simple term search
            - "cancer[Title]" - Title field search
            - "Smith J[Author]" - Author search
            - "Nature[Journal]" - Journal search
            - "neuroscience[MeSH Terms]" - MeSH term search
        """
        # Add MeSH terms to query if specified
        if mesh_terms:
            mesh_query = ' AND '.join(f'{term}[MeSH Terms]' for term in mesh_terms)
            if query:
                query = f'({query}) AND ({mesh_query})'
            else:
                query = mesh_query

        # Search for IDs first
        pmids = await self._search_ids(
            query=query,
            limit=limit,
            offset=offset,
            sort=sort,
            mindate=from_date,
            maxdate=to_date
        )

        if not pmids:
            return []

        # Fetch details in batches of 200
        papers = []
        batch_size = 200

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            batch_papers = await self._fetch_details(batch)
            papers.extend(batch_papers)

            # Small delay between batches
            if i + batch_size < len(pmids):
                await asyncio.sleep(0.1)

        return papers

    async def fetch(self, paper_id: str) -> Optional[Paper]:
        """
        Fetch a single paper by PMID.

        Args:
            paper_id: PubMed ID (e.g., "12345678" or "PMID:12345678")

        Returns:
            Paper object or None
        """
        # Clean up ID
        pmid = paper_id.replace('PMID:', '').strip()

        papers = await self._fetch_details([pmid])
        return papers[0] if papers else None

    async def search_by_mesh(
        self,
        mesh_term: str,
        limit: int = 100,
        **kwargs
    ) -> List[Paper]:
        """
        Search for papers tagged with a specific MeSH term.

        Args:
            mesh_term: MeSH term (e.g., "Neurosciences", "Brain")
            limit: Max results

        Returns:
            List of Paper objects
        """
        return await self.search(
            query=f'{mesh_term}[MeSH Terms]',
            limit=limit,
            **kwargs
        )

    async def get_related(self, pmid: str, limit: int = 20) -> List[Paper]:
        """
        Get papers related to a given PMID.

        Uses PubMed's "similar articles" feature.
        """
        params = {
            **self._base_params(),
            'dbfrom': 'pubmed',
            'db': 'pubmed',
            'id': pmid,
            'cmd': 'neighbor_score',
            'retmode': 'json'
        }

        url = f"{self.base_url}/elink.fcgi"

        try:
            data = await self._get(url, params)
            link_sets = data.get('linksets', [])

            related_pmids = []
            for link_set in link_sets:
                for link in link_set.get('linksetdbs', []):
                    if link.get('linkname') == 'pubmed_pubmed':
                        related_pmids.extend(
                            str(l['id']) for l in link.get('links', [])[:limit]
                        )

            if related_pmids:
                return await self._fetch_details(related_pmids[:limit])
            return []

        except Exception as e:
            logger.error(f"PubMed related search failed: {e}")
            return []
