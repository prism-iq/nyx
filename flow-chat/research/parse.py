#!/usr/bin/env python3
"""parse.py - extrait le contenu pertinent en markdown"""

def parse_wiki(data):
    """convertit Wikipedia en markdown"""
    if 'error' in data:
        return f"*recherche échouée: {data['error']}*"

    md = f"## {data.get('title', 'Sans titre')}\n\n"
    md += data.get('extract', '') + "\n\n"
    if data.get('url'):
        md += f"[Source: Wikipedia]({data['url']})\n"
    return md

def parse_arxiv(data):
    """convertit arXiv en markdown"""
    if 'error' in data:
        return f"*recherche échouée: {data['error']}*"

    papers = data.get('papers', [])
    if not papers:
        return "*aucun résultat arXiv*"

    md = f"## arXiv: {data.get('query', '')}\n\n"
    for p in papers:
        md += f"### {p['title']}\n"
        md += f"*{', '.join(p['authors'][:3])}* ({p['published']})\n\n"
        md += f"{p['summary'][:300]}...\n\n"
        md += f"[lien]({p['url']})\n\n---\n\n"
    return md

def parse_pubmed(data):
    """convertit PubMed en markdown"""
    if 'error' in data:
        return f"*recherche échouée: {data['error']}*"

    papers = data.get('papers', [])
    if not papers:
        return "*aucun résultat PubMed*"

    md = f"## PubMed: {data.get('query', '')}\n\n"
    for p in papers:
        md += f"### {p['title']}\n"
        md += f"*{', '.join(p['authors'])}* - {p['journal']} ({p['date']})\n\n"
        md += f"[PMID:{p['pmid']}]({p['url']})\n\n---\n\n"
    return md

def parse_scholar(data):
    """convertit Semantic Scholar en markdown"""
    if 'error' in data:
        return f"*recherche échouée: {data['error']}*"

    if 'papers' in data:
        papers = data['papers']
        if not papers:
            return "*aucun résultat Scholar*"

        md = f"## Semantic Scholar: {data.get('query', '')}\n\n"
        for p in papers:
            md += f"### {p.get('title', 'Sans titre')}\n"
            authors = [a.get('name', '') for a in p.get('authors', [])[:3]]
            md += f"*{', '.join(authors)}* ({p.get('year', '?')})\n"
            md += f"Citations: {p.get('citationCount', 0)}\n\n"
            if p.get('abstract'):
                md += f"{p['abstract'][:300]}...\n\n"
            md += "---\n\n"
        return md
    else:
        # single paper
        md = f"## {data.get('title', 'Sans titre')}\n"
        authors = [a.get('name', '') for a in data.get('authors', [])[:5]]
        md += f"*{', '.join(authors)}* ({data.get('year', '?')})\n"
        md += f"Citations: {data.get('citationCount', 0)}\n\n"
        if data.get('abstract'):
            md += f"{data['abstract']}\n"
        return md

def auto_parse(data):
    """détecte le type et parse"""
    source = data.get('source', '')
    if source == 'wikipedia':
        return parse_wiki(data)
    elif source == 'arxiv':
        return parse_arxiv(data)
    elif source == 'pubmed':
        return parse_pubmed(data)
    elif source == 'semantic_scholar':
        return parse_scholar(data)
    else:
        return str(data)
