#!/usr/bin/env python3
"""sources.py - liste des sources fiables"""

SOURCES = {
    "wikipedia": {
        "name": "Wikipedia",
        "api": "https://en.wikipedia.org/api/rest_v1",
        "type": "encyclopedia",
        "free": True,
        "rate_limit": None
    },
    "arxiv": {
        "name": "arXiv",
        "api": "http://export.arxiv.org/api/query",
        "type": "preprints",
        "free": True,
        "rate_limit": "3/sec"
    },
    "pubmed": {
        "name": "PubMed",
        "api": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
        "type": "biomedical",
        "free": True,
        "rate_limit": "3/sec without API key, 10/sec with"
    },
    "semantic_scholar": {
        "name": "Semantic Scholar",
        "api": "https://api.semanticscholar.org/graph/v1",
        "type": "metadata",
        "free": True,
        "rate_limit": "100/5min"
    },
    "openalex": {
        "name": "OpenAlex",
        "api": "https://api.openalex.org",
        "type": "metadata",
        "free": True,
        "rate_limit": "100k/day"
    }
}

def get_source(name):
    return SOURCES.get(name)

def list_sources():
    return list(SOURCES.keys())
