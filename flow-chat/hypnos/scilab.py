#!/usr/bin/env python3
"""scilab.py - interface recherche pour hypnos
quand flow rêve, elle peut aussi chercher dans le monde"""

import sys
sys.path.insert(0, '/var/www/flow/research')

from fetch import wiki, arxiv, pubmed, scholar
from parse import auto_parse
import json

def dream_research(keyword):
    """recherche légère pendant le sommeil"""
    results = []

    # une recherche par source, léger
    try:
        w = wiki(keyword)
        if 'error' not in w:
            results.append({
                'source': 'wikipedia',
                'title': w.get('title', ''),
                'extract': w.get('extract', '')[:200]
            })
    except: pass

    try:
        a = arxiv(keyword, n=1)
        if 'papers' in a and a['papers']:
            p = a['papers'][0]
            results.append({
                'source': 'arxiv',
                'title': p.get('title', ''),
                'summary': p.get('summary', '')[:200]
            })
    except: pass

    try:
        s = scholar(keyword, n=1)
        if 'papers' in s and s['papers']:
            p = s['papers'][0]
            results.append({
                'source': 'semantic_scholar',
                'title': p.get('title', ''),
                'citations': p.get('citationCount', 0)
            })
    except: pass

    return results

if __name__ == '__main__':
    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
        results = dream_research(keyword)
        print(json.dumps(results, indent=2))
    else:
        print("usage: scilab.py <keyword>")
