#!/usr/bin/env python3
"""genius.py - accès aux paroles via Genius API + scraping"""

import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime

# Genius API token (gratuit)
GENIUS_TOKEN = os.getenv("GENIUS_TOKEN", "")
BASE_URL = "https://api.genius.com"
CACHE_DIR = Path("/opt/flow-chat/adn/music/lyrics_cache")

def _headers():
    return {"Authorization": f"Bearer {GENIUS_TOKEN}"} if GENIUS_TOKEN else {}

def search_song(query, artist=None):
    """cherche une chanson sur Genius"""
    if not GENIUS_TOKEN:
        return {"error": "GENIUS_TOKEN not set"}

    search_query = f"{artist} {query}" if artist else query

    try:
        r = requests.get(
            f"{BASE_URL}/search",
            headers=_headers(),
            params={"q": search_query},
            timeout=10
        )
        data = r.json()

        hits = data.get("response", {}).get("hits", [])
        results = []

        for hit in hits[:5]:
            song = hit.get("result", {})
            results.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "artist": song.get("primary_artist", {}).get("name"),
                "url": song.get("url"),
                "thumbnail": song.get("song_art_image_thumbnail_url"),
                "annotation_count": song.get("annotation_count", 0)
            })

        return {"results": results, "query": search_query}

    except Exception as e:
        return {"error": str(e)}

def get_song_info(song_id):
    """récupère les infos détaillées d'une chanson"""
    if not GENIUS_TOKEN:
        return {"error": "GENIUS_TOKEN not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/songs/{song_id}",
            headers=_headers(),
            timeout=10
        )
        data = r.json()
        song = data.get("response", {}).get("song", {})

        return {
            "id": song.get("id"),
            "title": song.get("title"),
            "artist": song.get("primary_artist", {}).get("name"),
            "album": song.get("album", {}).get("name") if song.get("album") else None,
            "release_date": song.get("release_date"),
            "url": song.get("url"),
            "description": song.get("description", {}).get("plain") if isinstance(song.get("description"), dict) else None,
            "producers": [p.get("name") for p in song.get("producer_artists", [])],
            "writers": [w.get("name") for w in song.get("writer_artists", [])],
            "featured": [f.get("name") for f in song.get("featured_artists", [])],
            "annotation_count": song.get("annotation_count", 0),
            "pageviews": song.get("stats", {}).get("pageviews")
        }

    except Exception as e:
        return {"error": str(e)}

def scrape_lyrics(url):
    """scrape les paroles depuis la page Genius"""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {"error": "BeautifulSoup not installed: pip install beautifulsoup4"}

    try:
        r = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (compatible; FlowBot/1.0)"
        })
        soup = BeautifulSoup(r.text, "html.parser")

        # Genius utilise des divs avec data-lyrics-container
        lyrics_divs = soup.find_all("div", {"data-lyrics-container": "true"})

        if not lyrics_divs:
            # fallback: chercher la classe Lyrics__Container
            lyrics_divs = soup.find_all("div", class_=re.compile(r"Lyrics__Container"))

        if not lyrics_divs:
            return {"error": "lyrics container not found"}

        lyrics = []
        for div in lyrics_divs:
            # remplacer les <br> par des newlines
            for br in div.find_all("br"):
                br.replace_with("\n")
            lyrics.append(div.get_text())

        full_lyrics = "\n".join(lyrics)

        # nettoyer
        full_lyrics = re.sub(r'\[.*?\]', lambda m: '\n' + m.group(0) + '\n', full_lyrics)
        full_lyrics = re.sub(r'\n{3,}', '\n\n', full_lyrics)

        return {"lyrics": full_lyrics.strip(), "source": "genius", "url": url}

    except Exception as e:
        return {"error": str(e)}

def get_lyrics(artist, track):
    """recherche et récupère les paroles"""
    # check cache
    cache_key = f"{artist}_{track}".lower().replace(" ", "_")
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
            cached["from_cache"] = True
            return cached

    # search
    search = search_song(track, artist)
    if "error" in search or not search.get("results"):
        return {"error": "song not found", "query": f"{artist} - {track}"}

    # prendre le premier résultat
    best = search["results"][0]

    # scrape lyrics
    lyrics_data = scrape_lyrics(best["url"])
    if "error" in lyrics_data:
        return lyrics_data

    # enrichir avec les infos
    result = {
        "artist": best["artist"],
        "track": best["title"],
        "lyrics": lyrics_data["lyrics"],
        "url": best["url"],
        "genius_id": best["id"],
        "fetched_at": datetime.now().isoformat()
    }

    # cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result

def get_artist_songs(artist_name, per_page=20):
    """liste les chansons d'un artiste"""
    if not GENIUS_TOKEN:
        return {"error": "GENIUS_TOKEN not set"}

    try:
        # d'abord chercher l'artiste
        r = requests.get(
            f"{BASE_URL}/search",
            headers=_headers(),
            params={"q": artist_name},
            timeout=10
        )
        data = r.json()

        # extraire l'ID de l'artiste du premier résultat
        hits = data.get("response", {}).get("hits", [])
        if not hits:
            return {"error": "artist not found"}

        artist_id = hits[0].get("result", {}).get("primary_artist", {}).get("id")

        # récupérer les chansons de l'artiste
        r = requests.get(
            f"{BASE_URL}/artists/{artist_id}/songs",
            headers=_headers(),
            params={"per_page": per_page, "sort": "popularity"},
            timeout=10
        )
        data = r.json()

        songs = data.get("response", {}).get("songs", [])
        return {
            "artist": artist_name,
            "artist_id": artist_id,
            "songs": [
                {
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "url": s.get("url")
                }
                for s in songs
            ]
        }

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("=== GENIUS LYRICS ===")
    if not GENIUS_TOKEN:
        print("Set GENIUS_TOKEN env var to use")
    else:
        result = search_song("Lose Yourself", "Eminem")
        print(json.dumps(result, indent=2))
