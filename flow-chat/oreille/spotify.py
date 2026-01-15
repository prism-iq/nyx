#!/usr/bin/env python3
"""spotify.py - metadata et audio features via Spotify API"""

import os
import json
import base64
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Spotify credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
BASE_URL = "https://api.spotify.com/v1"
CACHE_DIR = Path("/opt/flow-chat/adn/music/spotify_cache")

# Token cache
_token_cache = {"token": None, "expires": None}

def _get_token():
    """obtient un token d'accès (client credentials flow)"""
    global _token_cache

    if _token_cache["token"] and _token_cache["expires"] and datetime.now() < _token_cache["expires"]:
        return _token_cache["token"]

    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    try:
        auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        r = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        data = r.json()

        _token_cache["token"] = data.get("access_token")
        _token_cache["expires"] = datetime.now() + timedelta(seconds=data.get("expires_in", 3600) - 60)

        return _token_cache["token"]

    except Exception as e:
        return None

def _headers():
    token = _get_token()
    return {"Authorization": f"Bearer {token}"} if token else {}

def search_track(query, artist=None, limit=5):
    """cherche un track sur Spotify"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    search_query = f"track:{query} artist:{artist}" if artist else query

    try:
        r = requests.get(
            f"{BASE_URL}/search",
            headers=_headers(),
            params={"q": search_query, "type": "track", "limit": limit},
            timeout=10
        )
        data = r.json()

        tracks = data.get("tracks", {}).get("items", [])
        return {
            "results": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "artist": t.get("artists", [{}])[0].get("name"),
                    "artists": [a.get("name") for a in t.get("artists", [])],
                    "album": t.get("album", {}).get("name"),
                    "release_date": t.get("album", {}).get("release_date"),
                    "duration_ms": t.get("duration_ms"),
                    "popularity": t.get("popularity"),
                    "preview_url": t.get("preview_url"),
                    "spotify_url": t.get("external_urls", {}).get("spotify")
                }
                for t in tracks
            ]
        }

    except Exception as e:
        return {"error": str(e)}

def get_audio_features(track_id):
    """récupère les audio features d'un track"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/audio-features/{track_id}",
            headers=_headers(),
            timeout=10
        )
        data = r.json()

        return {
            "track_id": track_id,
            "features": {
                "tempo": data.get("tempo"),  # BPM
                "key": data.get("key"),  # 0-11 (C, C#, D, ...)
                "mode": "major" if data.get("mode") == 1 else "minor",
                "time_signature": data.get("time_signature"),
                "duration_ms": data.get("duration_ms"),
                # 0.0 - 1.0 scores
                "danceability": data.get("danceability"),
                "energy": data.get("energy"),
                "speechiness": data.get("speechiness"),  # paroles vs instrumental
                "acousticness": data.get("acousticness"),
                "instrumentalness": data.get("instrumentalness"),
                "liveness": data.get("liveness"),
                "valence": data.get("valence"),  # positif/négatif
                "loudness": data.get("loudness")  # dB
            }
        }

    except Exception as e:
        return {"error": str(e)}

def get_audio_analysis(track_id):
    """analyse audio détaillée (beats, sections, segments)"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/audio-analysis/{track_id}",
            headers=_headers(),
            timeout=15
        )
        data = r.json()

        # simplifier l'analyse
        track_info = data.get("track", {})

        return {
            "track_id": track_id,
            "duration": track_info.get("duration"),
            "tempo": track_info.get("tempo"),
            "tempo_confidence": track_info.get("tempo_confidence"),
            "key": track_info.get("key"),
            "key_confidence": track_info.get("key_confidence"),
            "mode": track_info.get("mode"),
            "time_signature": track_info.get("time_signature"),
            "sections_count": len(data.get("sections", [])),
            "beats_count": len(data.get("beats", [])),
            "bars_count": len(data.get("bars", [])),
            "segments_count": len(data.get("segments", []))
        }

    except Exception as e:
        return {"error": str(e)}

def get_artist(artist_id):
    """info sur un artiste"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/artists/{artist_id}",
            headers=_headers(),
            timeout=10
        )
        data = r.json()

        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "genres": data.get("genres", []),
            "popularity": data.get("popularity"),
            "followers": data.get("followers", {}).get("total"),
            "image": data.get("images", [{}])[0].get("url") if data.get("images") else None,
            "spotify_url": data.get("external_urls", {}).get("spotify")
        }

    except Exception as e:
        return {"error": str(e)}

def search_artist(name):
    """cherche un artiste"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/search",
            headers=_headers(),
            params={"q": name, "type": "artist", "limit": 5},
            timeout=10
        )
        data = r.json()

        artists = data.get("artists", {}).get("items", [])
        return {
            "results": [
                {
                    "id": a.get("id"),
                    "name": a.get("name"),
                    "genres": a.get("genres", []),
                    "popularity": a.get("popularity"),
                    "followers": a.get("followers", {}).get("total")
                }
                for a in artists
            ]
        }

    except Exception as e:
        return {"error": str(e)}

def get_artist_top_tracks(artist_id, market="US"):
    """top tracks d'un artiste"""
    token = _get_token()
    if not token:
        return {"error": "Spotify credentials not set"}

    try:
        r = requests.get(
            f"{BASE_URL}/artists/{artist_id}/top-tracks",
            headers=_headers(),
            params={"market": market},
            timeout=10
        )
        data = r.json()

        return {
            "artist_id": artist_id,
            "tracks": [
                {
                    "id": t.get("id"),
                    "name": t.get("name"),
                    "album": t.get("album", {}).get("name"),
                    "popularity": t.get("popularity"),
                    "preview_url": t.get("preview_url")
                }
                for t in data.get("tracks", [])
            ]
        }

    except Exception as e:
        return {"error": str(e)}

def get_track_full(artist, track_name):
    """récupère toutes les infos sur un track"""
    # search
    search = search_track(track_name, artist, limit=1)
    if "error" in search or not search.get("results"):
        return {"error": "track not found"}

    track = search["results"][0]
    track_id = track["id"]

    # audio features
    features = get_audio_features(track_id)

    result = {
        **track,
        "audio_features": features.get("features", {}) if "features" in features else None,
        "fetched_at": datetime.now().isoformat()
    }

    # cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = f"{artist}_{track_name}".lower().replace(" ", "_")
    cache_file = CACHE_DIR / f"{cache_key}.json"
    with open(cache_file, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


if __name__ == "__main__":
    print("=== SPOTIFY API ===")
    if not CLIENT_ID:
        print("Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars")
    else:
        result = search_track("Lose Yourself", "Eminem")
        print(json.dumps(result, indent=2))
