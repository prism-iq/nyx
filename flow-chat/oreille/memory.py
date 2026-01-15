#!/usr/bin/env python3
"""memory.py - mémoire musicale dans adn"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

ADN_MUSIC = Path("/opt/flow-chat/adn/music")
ARTISTS_FILE = ADN_MUSIC / "artists.jsonl"
TRACKS_FILE = ADN_MUSIC / "tracks.jsonl"
PATTERNS_FILE = ADN_MUSIC / "patterns.jsonl"
INSIGHTS_FILE = ADN_MUSIC / "insights.jsonl"

def _ensure_dirs():
    ADN_MUSIC.mkdir(parents=True, exist_ok=True)

def _append_jsonl(filepath, data):
    _ensure_dirs()
    with open(filepath, 'a') as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def _read_jsonl(filepath, limit=None):
    if not filepath.exists():
        return []
    results = []
    with open(filepath) as f:
        for line in f:
            if line.strip():
                results.append(json.loads(line))
    if limit:
        return results[-limit:]
    return results

def remember_track(track_info, lyrics_analysis=None, audio_features=None):
    """mémorise un track analysé"""
    memory = {
        "timestamp": datetime.now().isoformat(),
        "artist": track_info.get("artist"),
        "track": track_info.get("name") or track_info.get("track"),
        "album": track_info.get("album"),
        "spotify_id": track_info.get("id"),
        "genius_id": track_info.get("genius_id")
    }

    if lyrics_analysis:
        memory["themes"] = lyrics_analysis.get("themes", {}).get("top_3", [])
        memory["dominant_theme"] = lyrics_analysis.get("themes", {}).get("dominant")
        memory["lexical_diversity"] = lyrics_analysis.get("vocabulary", {}).get("lexical_diversity")

    if audio_features:
        memory["tempo"] = audio_features.get("tempo")
        memory["energy"] = audio_features.get("energy")
        memory["valence"] = audio_features.get("valence")

    _append_jsonl(TRACKS_FILE, memory)
    return memory

def remember_artist(artist_info, analysis_summary=None):
    """mémorise un artiste"""
    memory = {
        "timestamp": datetime.now().isoformat(),
        "name": artist_info.get("name"),
        "spotify_id": artist_info.get("id"),
        "genres": artist_info.get("genres", []),
        "popularity": artist_info.get("popularity")
    }

    if analysis_summary:
        memory["common_themes"] = analysis_summary.get("common_themes")
        memory["avg_energy"] = analysis_summary.get("avg_energy")
        memory["tracks_analyzed"] = analysis_summary.get("tracks_analyzed")

    _append_jsonl(ARTISTS_FILE, memory)
    return memory

def remember_pattern(pattern_type, pattern_data, source_track=None):
    """mémorise un pattern découvert"""
    memory = {
        "timestamp": datetime.now().isoformat(),
        "type": pattern_type,
        "data": pattern_data,
        "source": source_track
    }
    _append_jsonl(PATTERNS_FILE, memory)
    return memory

def remember_insight(insight_text, context=None):
    """mémorise un insight"""
    memory = {
        "timestamp": datetime.now().isoformat(),
        "insight": insight_text,
        "context": context
    }
    _append_jsonl(INSIGHTS_FILE, memory)
    return memory

def recall_tracks(limit=20):
    """rappelle les tracks mémorisés"""
    return _read_jsonl(TRACKS_FILE, limit)

def recall_artists(limit=20):
    """rappelle les artistes mémorisés"""
    return _read_jsonl(ARTISTS_FILE, limit)

def recall_patterns(limit=20):
    """rappelle les patterns découverts"""
    return _read_jsonl(PATTERNS_FILE, limit)

def recall_insights(limit=20):
    """rappelle les insights"""
    return _read_jsonl(INSIGHTS_FILE, limit)

def search_tracks(query):
    """cherche dans les tracks mémorisés"""
    tracks = recall_tracks()
    query_lower = query.lower()
    return [
        t for t in tracks
        if query_lower in (t.get("artist", "") or "").lower()
        or query_lower in (t.get("track", "") or "").lower()
    ]

def get_theme_stats():
    """statistiques des thèmes rencontrés"""
    tracks = recall_tracks()
    theme_counts = defaultdict(int)

    for t in tracks:
        for theme in t.get("themes", []):
            theme_counts[theme] += 1

    return dict(sorted(theme_counts.items(), key=lambda x: -x[1]))

def get_artist_profile(artist_name):
    """profil complet d'un artiste basé sur les tracks analysés"""
    tracks = search_tracks(artist_name)

    if not tracks:
        return {"error": "no tracks found for artist"}

    themes = defaultdict(int)
    energies = []
    valences = []

    for t in tracks:
        for theme in t.get("themes", []):
            themes[theme] += 1
        if t.get("energy"):
            energies.append(t["energy"])
        if t.get("valence"):
            valences.append(t["valence"])

    return {
        "artist": artist_name,
        "tracks_analyzed": len(tracks),
        "common_themes": dict(sorted(themes.items(), key=lambda x: -x[1])[:5]),
        "avg_energy": sum(energies) / len(energies) if energies else None,
        "avg_valence": sum(valences) / len(valences) if valences else None,
        "tracks": [{"track": t.get("track"), "themes": t.get("themes")} for t in tracks[-10:]]
    }

def stats():
    """statistiques globales de la mémoire musicale"""
    _ensure_dirs()
    return {
        "tracks": len(recall_tracks()),
        "artists": len(recall_artists()),
        "patterns": len(recall_patterns()),
        "insights": len(recall_insights()),
        "theme_distribution": get_theme_stats(),
        "files": {
            "tracks": str(TRACKS_FILE),
            "artists": str(ARTISTS_FILE),
            "patterns": str(PATTERNS_FILE)
        }
    }


if __name__ == "__main__":
    print("=== MUSIC MEMORY ===")
    print(json.dumps(stats(), indent=2))
