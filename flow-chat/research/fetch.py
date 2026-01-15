#!/usr/bin/env python3
"""fetch.py - récupère du contenu web"""

import requests
import xml.etree.ElementTree as ET
from cache import get_cache, set_cache
import urllib.parse
import time

HEADERS = {'User-Agent': 'Flow/1.0 (pwnd.icu/flow; research bot)'}

def wiki(query):
    """récupère un résumé Wikipedia"""
    cached = get_cache('wikipedia', query)
    if cached:
        return cached

    try:
        # recherche
        search_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
        r = requests.get(search_url, headers=HEADERS, timeout=10)

        if r.status_code == 200:
            data = r.json()
            result = {
                'title': data.get('title'),
                'extract': data.get('extract'),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page'),
                'source': 'wikipedia'
            }
            set_cache('wikipedia', query, result)
            return result
        elif r.status_code == 404:
            # essayer une recherche
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
            r = requests.get(search_url, headers=HEADERS, timeout=10)
            data = r.json()
            results = data.get('query', {}).get('search', [])
            if results:
                return wiki(results[0]['title'])
            return {'error': 'not found'}
    except Exception as e:
        return {'error': str(e)}

def arxiv(query, n=5):
    """récupère les derniers papers arXiv"""
    cached = get_cache('arxiv', f"{query}:{n}")
    if cached:
        return cached

    try:
        url = f"http://export.arxiv.org/api/query?search_query=all:{urllib.parse.quote(query)}&start=0&max_results={n}&sortBy=submittedDate&sortOrder=descending"
        r = requests.get(url, headers=HEADERS, timeout=15)

        if r.status_code == 200:
            root = ET.fromstring(r.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom'}

            papers = []
            for entry in root.findall('atom:entry', ns):
                paper = {
                    'title': entry.find('atom:title', ns).text.strip().replace('\n', ' '),
                    'authors': [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)],
                    'summary': entry.find('atom:summary', ns).text.strip()[:500],
                    'url': entry.find('atom:id', ns).text,
                    'published': entry.find('atom:published', ns).text[:10]
                }
                papers.append(paper)

            result = {'papers': papers, 'source': 'arxiv', 'query': query}
            set_cache('arxiv', f"{query}:{n}", result)
            return result
    except Exception as e:
        return {'error': str(e)}

def pubmed(query, n=5):
    """récupère des papers PubMed"""
    cached = get_cache('pubmed', f"{query}:{n}")
    if cached:
        return cached

    try:
        # recherche
        search_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={urllib.parse.quote(query)}&retmax={n}&retmode=json&sort=date"
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        data = r.json()
        ids = data.get('esearchresult', {}).get('idlist', [])

        if not ids:
            return {'papers': [], 'source': 'pubmed'}

        # récupérer les détails
        time.sleep(0.5)  # rate limit
        fetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
        r = requests.get(fetch_url, headers=HEADERS, timeout=10)
        data = r.json()

        papers = []
        for pmid in ids:
            info = data.get('result', {}).get(pmid, {})
            if info:
                paper = {
                    'title': info.get('title', ''),
                    'authors': [a.get('name', '') for a in info.get('authors', [])[:3]],
                    'journal': info.get('source', ''),
                    'date': info.get('pubdate', ''),
                    'pmid': pmid,
                    'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                }
                papers.append(paper)

        result = {'papers': papers, 'source': 'pubmed', 'query': query}
        set_cache('pubmed', f"{query}:{n}", result)
        return result
    except Exception as e:
        return {'error': str(e)}

def scholar(query_or_doi, n=5):
    """recherche Semantic Scholar"""
    cached = get_cache('scholar', query_or_doi)
    if cached:
        return cached

    try:
        # si c'est un DOI
        if query_or_doi.startswith('10.'):
            url = f"https://api.semanticscholar.org/graph/v1/paper/{query_or_doi}?fields=title,authors,abstract,citationCount,year,url"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                result = r.json()
                result['source'] = 'semantic_scholar'
                set_cache('scholar', query_or_doi, result)
                return result
        else:
            # recherche
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={urllib.parse.quote(query_or_doi)}&limit={n}&fields=title,authors,abstract,citationCount,year,url"
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json()
                result = {'papers': data.get('data', []), 'source': 'semantic_scholar', 'query': query_or_doi}
                set_cache('scholar', query_or_doi, result)
                return result
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # test
    print("=== Wikipedia ===")
    print(wiki("CRISPR"))
    print("\n=== arXiv ===")
    print(arxiv("consciousness", 2))
