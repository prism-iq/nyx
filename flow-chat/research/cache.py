#!/usr/bin/env python3
"""cache.py - évite de re-fetch"""

import os
import json
import hashlib
import time

CACHE_DIR = "/var/www/flow/knowledge/cache"
CACHE_TTL = 86400  # 24h

def cache_key(source, query):
    """génère une clé de cache"""
    raw = f"{source}:{query}"
    return hashlib.md5(raw.encode()).hexdigest()

def get_cache(source, query):
    """récupère du cache si valide"""
    key = cache_key(source, query)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        if time.time() - data.get('timestamp', 0) < CACHE_TTL:
            return data.get('content')
    return None

def set_cache(source, query, content):
    """stocke dans le cache"""
    key = cache_key(source, query)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, 'w') as f:
        json.dump({
            'source': source,
            'query': query,
            'content': content,
            'timestamp': time.time()
        }, f)

def clear_cache():
    """vide le cache"""
    for f in os.listdir(CACHE_DIR):
        os.remove(os.path.join(CACHE_DIR, f))

def cache_stats():
    """stats du cache"""
    files = os.listdir(CACHE_DIR)
    total_size = sum(os.path.getsize(os.path.join(CACHE_DIR, f)) for f in files)
    return {
        'entries': len(files),
        'size_kb': total_size // 1024
    }
