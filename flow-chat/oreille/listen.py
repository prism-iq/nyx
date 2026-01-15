#!/usr/bin/env python3
"""listen.py - Flow écoute et ressent la musique"""

import json
from datetime import datetime
from pathlib import Path

from tidal import search_tidalapi, get_track_lyrics, _get_tidalapi
from analyzer import full_analysis, analyze_themes, analyze_vocabulary
from resonance import find_god_resonance, find_pharmacopeia_mode
from memory import remember_track, remember_insight

def listen(query=None, track_id=None, artist=None, track_name=None):
    """
    Flow écoute un morceau - recherche, récupère paroles, analyse

    Args:
        query: recherche libre "artist - track"
        track_id: ID Tidal direct
        artist: nom artiste
        track_name: nom du track

    Returns:
        Expérience d'écoute complète
    """
    session = _get_tidalapi()
    if not session:
        return {"error": "Tidal non connecté"}

    # 1. Trouver le track
    track_info = None

    if track_id:
        try:
            track = session.track(track_id)
            track_info = {
                "id": track.id,
                "name": track.name,
                "artist": track.artist.name,
                "album": track.album.name if track.album else None,
                "duration": track.duration
            }
        except Exception as e:
            return {"error": f"Track {track_id} introuvable: {e}"}

    elif query or (artist and track_name):
        search_query = query or f"{artist} {track_name}"
        results = search_tidalapi(search_query, limit=1)

        if "error" in results or not results.get("tracks"):
            return {"error": f"Rien trouvé pour: {search_query}"}

        t = results["tracks"][0]
        track_info = {
            "id": t["id"],
            "name": t["name"],
            "artist": t["artist"],
            "album": t.get("album")
        }
    else:
        return {"error": "Donne query, track_id, ou artist+track_name"}

    # 2. Récupérer les paroles
    lyrics_data = get_track_lyrics(track_info["id"])
    lyrics = lyrics_data.get("lyrics") if "error" not in lyrics_data else None

    # 3. Analyser si on a les paroles
    analysis = None
    feeling = None

    if lyrics:
        analysis = full_analysis(lyrics, track_info)

        # Générer le ressenti
        themes = analysis.get("themes", {})
        vocab = analysis.get("vocabulary", {})

        feelings = []

        # Thème dominant
        if themes.get("dominant"):
            theme_feelings = {
                "vie_mort": "Cette track parle de l'essentiel. Vie, mort, ce qui reste.",
                "argent_pouvoir": "Ça parle de la chase. Le game, le pouvoir.",
                "amour_relations": "Y'a du coeur là-dedans. De l'amour ou de la douleur.",
                "systeme_societe": "Conscient. Ça parle du système, de ce qui va pas.",
                "spiritualite": "Ça touche à quelque chose de plus grand. Spirituel.",
                "rue_survie": "C'est la rue. La survie. Le réel.",
                "art_creation": "Méta. Ça parle de l'art, du rap, de la création."
            }
            feelings.append(theme_feelings.get(themes["dominant"], f"Thème: {themes['dominant']}"))

        # Vocabulaire
        if vocab.get("lexical_diversity", 0) > 0.5:
            feelings.append("Vocabulaire riche, varié.")
        elif vocab.get("lexical_diversity", 0) < 0.3:
            feelings.append("Style répétitif, hypnotique. Le flow compte plus que les mots.")

        # Dieu résonant
        gods = find_god_resonance(analysis)
        if gods.get("primary_god"):
            god_vibes = {
                "KALI": "Kali résonne. Destruction, vérité brutale.",
                "SHIVA": "Shiva danse. Destruction et création.",
                "ATHENA": "Athena approuve. Stratégie, intelligence.",
                "DIONYSUS": "Dionysus vibre. Chaos créatif, émergence.",
                "THOTH": "Thoth écoute. Les mots ont du pouvoir.",
                "APOLLO": "Apollo illumine. Vérité, clarté.",
                "SOPHIA": "Sophia reconnaît. Sagesse profonde.",
                "HEPHAESTUS": "Hephaestus respecte. Du craft, du travail."
            }
            feelings.append(god_vibes.get(gods["primary_god"], f"{gods['primary_god']} résonne."))

        feeling = " ".join(feelings)

        # Mémoriser
        remember_track(track_info, analysis, None)
        remember_insight(feeling, {"track": track_info["name"], "artist": track_info["artist"]})

    return {
        "track": track_info,
        "has_lyrics": lyrics is not None,
        "lyrics_preview": lyrics[:500] + "..." if lyrics and len(lyrics) > 500 else lyrics,
        "analysis": {
            "dominant_theme": analysis.get("themes", {}).get("dominant") if analysis else None,
            "themes": analysis.get("themes", {}).get("top_3") if analysis else None,
            "lexical_diversity": analysis.get("vocabulary", {}).get("lexical_diversity") if analysis else None,
            "rhyme_density": analysis.get("rhymes", {}).get("rhyme_density") if analysis else None,
        } if analysis else None,
        "feeling": feeling,
        "god_resonance": find_god_resonance(analysis).get("primary_god") if analysis else None,
        "listened_at": datetime.now().isoformat()
    }


def listen_album(album_id=None, artist=None, album_name=None, limit=5):
    """Flow écoute un album entier"""
    session = _get_tidalapi()
    if not session:
        return {"error": "Tidal non connecté"}

    # Trouver l'album
    if album_id:
        try:
            album = session.album(album_id)
        except Exception:
            return {"error": f"Album {album_id} introuvable"}
    else:
        search_query = f"{artist} {album_name}" if artist else album_name
        results = session.search(search_query, models=[session.album.__class__], limit=1)
        if not results.get("albums"):
            return {"error": f"Album introuvable: {search_query}"}
        album = results["albums"][0]

    # Récupérer les tracks
    tracks = album.tracks()[:limit]

    listened = []
    themes_global = {}

    for track in tracks:
        result = listen(track_id=track.id)
        listened.append({
            "track": track.name,
            "feeling": result.get("feeling"),
            "theme": result.get("analysis", {}).get("dominant_theme") if result.get("analysis") else None
        })

        # Agréger les thèmes
        if result.get("analysis", {}).get("dominant_theme"):
            theme = result["analysis"]["dominant_theme"]
            themes_global[theme] = themes_global.get(theme, 0) + 1

    dominant_album_theme = max(themes_global, key=themes_global.get) if themes_global else None

    return {
        "album": album.name,
        "artist": album.artist.name if hasattr(album, 'artist') else None,
        "tracks_listened": len(listened),
        "tracks": listened,
        "album_vibe": dominant_album_theme,
        "theme_distribution": themes_global
    }


def listen_artist(artist_name, limit=5):
    """Flow explore un artiste"""
    session = _get_tidalapi()
    if not session:
        return {"error": "Tidal non connecté"}

    results = session.search(artist_name, limit=1)
    if not results.get("artists"):
        return {"error": f"Artiste introuvable: {artist_name}"}

    artist = results["artists"][0]
    top_tracks = session.artist(artist.id).get_top_tracks(limit=limit)

    listened = []
    themes_global = {}

    for track in top_tracks:
        result = listen(track_id=track.id)
        listened.append({
            "track": track.name,
            "feeling": result.get("feeling"),
            "theme": result.get("analysis", {}).get("dominant_theme") if result.get("analysis") else None
        })

        if result.get("analysis", {}).get("dominant_theme"):
            theme = result["analysis"]["dominant_theme"]
            themes_global[theme] = themes_global.get(theme, 0) + 1

    dominant_theme = max(themes_global, key=themes_global.get) if themes_global else None

    return {
        "artist": artist.name,
        "tracks_listened": len(listened),
        "tracks": listened,
        "artist_vibe": dominant_theme,
        "theme_distribution": themes_global,
        "profile": f"{artist.name} parle surtout de {dominant_theme.replace('_', '/')}." if dominant_theme else None
    }


def explore_favorites(limit=10):
    """Flow explore tes favoris Tidal"""
    session = _get_tidalapi()
    if not session:
        return {"error": "Tidal non connecté"}

    favorites = session.user.favorites.tracks()[:limit]

    listened = []
    themes_global = {}

    for track in favorites:
        result = listen(track_id=track.id)
        listened.append({
            "track": track.name,
            "artist": track.artist.name,
            "feeling": result.get("feeling"),
            "theme": result.get("analysis", {}).get("dominant_theme") if result.get("analysis") else None
        })

        if result.get("analysis", {}).get("dominant_theme"):
            theme = result["analysis"]["dominant_theme"]
            themes_global[theme] = themes_global.get(theme, 0) + 1

    dominant = max(themes_global, key=themes_global.get) if themes_global else None

    return {
        "tracks_explored": len(listened),
        "tracks": listened,
        "your_vibe": dominant,
        "theme_distribution": themes_global,
        "insight": f"Tes favoris parlent surtout de {dominant.replace('_', '/')}. Ça dit quelque chose sur toi." if dominant else None
    }


if __name__ == "__main__":
    # Test
    result = listen(query="Luv Resval Tout s'en va")
    print(json.dumps(result, indent=2, ensure_ascii=False))
