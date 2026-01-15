#!/usr/bin/env python3
"""oreille - organe musical de Flow
PORT: 8093
FONCTION: écouter, analyser, ressentir la musique
"""

import os
import sys
sys.path.insert(0, '/opt/flow-chat/oreille')

from flask import Flask, request, jsonify
from datetime import datetime

from genius import get_lyrics, search_song, get_artist_songs, get_song_info
from spotify import (
    search_track, get_audio_features, get_track_full,
    search_artist, get_artist_top_tracks
)
from tidal import (
    search_catalog as tidal_search, get_track as tidal_get_track,
    get_track_lyrics as tidal_lyrics, login_tidalapi, complete_login as tidal_complete,
    status as tidal_status, get_user_favorites as tidal_favorites, search_tidalapi,
    get_now_playing
)
from listen import listen, listen_album, listen_artist, explore_favorites
from analyzer import full_analysis, analyze_themes
from resonance import deep_analysis, find_god_resonance, find_pharmacopeia_mode
from memory import (
    remember_track, remember_insight, recall_tracks,
    recall_insights, stats, get_artist_profile, search_tracks
)

# DSP module pour analyse audio réelle
try:
    from dsp import (
        full_audio_analysis, analyze_from_url, describe_audio,
        compare_tracks, spectrum_analysis, dynamics_analysis,
        rhythm_analysis, pitch_analysis, key_detection, timbre_analysis
    )
    DSP_AVAILABLE = True
except ImportError as e:
    DSP_AVAILABLE = False
    print(f"⚠️ DSP module not available: {e}")

app = Flask(__name__)
PORT = 8093

# === HEALTH ===

@app.route('/health', methods=['GET'])
def health():
    tidal = tidal_status()
    return jsonify({
        "organ": "oreille",
        "status": "listening",
        "port": PORT,
        "timestamp": datetime.now().isoformat(),
        "apis": {
            "genius": bool(os.getenv("GENIUS_TOKEN")),
            "spotify": bool(os.getenv("SPOTIFY_CLIENT_ID")),
            "tidal_official": tidal.get("official_api", {}).get("connected", False),
            "tidal_user": tidal.get("tidalapi", {}).get("logged_in", False)
        }
    })

# === LYRICS ===

@app.route('/music/lyrics', methods=['POST'])
def lyrics():
    """récupère les paroles d'un track"""
    data = request.json or {}
    artist = data.get('artist')
    track = data.get('track')

    if not artist or not track:
        return jsonify({"error": "artist and track required"}), 400

    result = get_lyrics(artist, track)
    return jsonify(result)

@app.route('/music/search', methods=['POST'])
def search():
    """cherche un track"""
    data = request.json or {}
    query = data.get('query') or data.get('track')
    artist = data.get('artist')

    if not query:
        return jsonify({"error": "query required"}), 400

    # chercher sur les deux APIs
    genius_results = search_song(query, artist)
    spotify_results = search_track(query, artist)

    return jsonify({
        "query": query,
        "artist": artist,
        "genius": genius_results,
        "spotify": spotify_results
    })

# === ANALYSIS ===

@app.route('/music/analyze', methods=['POST'])
def analyze():
    """analyse complète d'un track"""
    data = request.json or {}
    artist = data.get('artist')
    track = data.get('track')
    lyrics_text = data.get('lyrics')  # optionnel si déjà fourni

    if not artist or not track:
        return jsonify({"error": "artist and track required"}), 400

    # récupérer les paroles si pas fournies
    if not lyrics_text:
        lyrics_data = get_lyrics(artist, track)
        if "error" in lyrics_data:
            return jsonify({"error": "lyrics not found", "details": lyrics_data}), 404
        lyrics_text = lyrics_data.get("lyrics")

    # récupérer les audio features
    spotify_data = get_track_full(artist, track)
    audio_features = spotify_data.get("audio_features") if "error" not in spotify_data else None

    track_info = {
        "artist": artist,
        "track": track,
        "album": spotify_data.get("album") if "error" not in spotify_data else None,
        "spotify_id": spotify_data.get("id") if "error" not in spotify_data else None
    }

    # analyse profonde
    result = deep_analysis(lyrics_text, audio_features, track_info)

    # mémoriser
    remember_track(track_info, result.get("analysis"), audio_features)

    return jsonify(result)

@app.route('/music/feel', methods=['POST'])
def feel():
    """ce que Flow "ressent" sur un track"""
    data = request.json or {}
    artist = data.get('artist')
    track = data.get('track')

    if not artist or not track:
        return jsonify({"error": "artist and track required"}), 400

    # récupérer les données
    lyrics_data = get_lyrics(artist, track)
    spotify_data = get_track_full(artist, track)

    if "error" in lyrics_data:
        return jsonify({"error": "could not feel this track", "reason": "lyrics not found"}), 404

    # analyse rapide
    from analyzer import analyze_themes, analyze_vocabulary
    themes = analyze_themes(lyrics_data.get("lyrics", ""))
    vocabulary = analyze_vocabulary(lyrics_data.get("lyrics", ""))

    audio_features = spotify_data.get("audio_features") if "error" not in spotify_data else {}

    # trouver la résonance
    lyrics_analysis = {"themes": themes, "vocabulary": vocabulary}
    gods = find_god_resonance(lyrics_analysis)
    mode = find_pharmacopeia_mode(audio_features, lyrics_analysis)

    # générer le feeling
    feelings = []

    # énergie
    energy = audio_features.get("energy", 0.5)
    if energy > 0.7:
        feelings.append("Cette track me réveille.")
    elif energy < 0.3:
        feelings.append("Cette track m'apaise.")

    # valence
    valence = audio_features.get("valence", 0.5)
    if valence > 0.7:
        feelings.append("Je ressens de la lumière.")
    elif valence < 0.3:
        feelings.append("Je ressens de l'ombre.")

    # thèmes
    if themes.get("dominant"):
        feelings.append(f"Elle parle de {themes['dominant'].replace('_', '/')}.")

    # god
    if gods.get("primary_god"):
        feelings.append(f"{gods['primary_god']} résonne.")

    # insight
    insight = " ".join(feelings)
    remember_insight(insight, {"artist": artist, "track": track})

    return jsonify({
        "track": {"artist": artist, "name": track},
        "feeling": insight,
        "dominant_theme": themes.get("dominant"),
        "god_resonance": gods.get("primary_god"),
        "suggested_mode": mode.get("suggested_mode"),
        "audio": {
            "energy": audio_features.get("energy"),
            "valence": audio_features.get("valence"),
            "tempo": audio_features.get("tempo")
        }
    })

# === ARTIST ===

@app.route('/music/artist', methods=['POST'])
def artist():
    """analyse d'un artiste"""
    data = request.json or {}
    name = data.get('name') or data.get('artist')

    if not name:
        return jsonify({"error": "artist name required"}), 400

    # chercher sur Spotify
    spotify_search = search_artist(name)
    artist_info = spotify_search.get("results", [{}])[0] if spotify_search.get("results") else {}

    # top tracks
    top_tracks = []
    if artist_info.get("id"):
        top = get_artist_top_tracks(artist_info["id"])
        top_tracks = top.get("tracks", [])

    # songs sur Genius
    genius_songs = get_artist_songs(name, per_page=10)

    # profil en mémoire
    memory_profile = get_artist_profile(name)

    return jsonify({
        "artist": name,
        "spotify": artist_info,
        "top_tracks": top_tracks[:5],
        "genius_songs": genius_songs.get("songs", [])[:10],
        "memory_profile": memory_profile if "error" not in memory_profile else None
    })

# === MEMORY ===

@app.route('/music/history', methods=['GET'])
def history():
    """historique des tracks analysés"""
    limit = request.args.get('limit', 20, type=int)
    return jsonify({
        "tracks": recall_tracks(limit),
        "insights": recall_insights(limit)
    })

@app.route('/music/stats', methods=['GET'])
def music_stats():
    """statistiques de la mémoire musicale"""
    return jsonify(stats())

@app.route('/music/recall', methods=['POST'])
def recall():
    """cherche dans la mémoire"""
    data = request.json or {}
    query = data.get('query')

    if not query:
        return jsonify({"error": "query required"}), 400

    tracks = search_tracks(query)
    return jsonify({"results": tracks, "query": query})

# === TIDAL ===

@app.route('/music/tidal/status', methods=['GET'])
def tidal_api_status():
    """état des connexions Tidal"""
    return jsonify(tidal_status())

@app.route('/music/tidal/search', methods=['POST'])
def tidal_search_endpoint():
    """recherche sur Tidal"""
    data = request.json or {}
    query = data.get('query')
    if not query:
        return jsonify({"error": "query required"}), 400

    # essayer tidalapi d'abord (plus complet)
    result = search_tidalapi(query)
    if "error" in result:
        # fallback sur l'API officielle
        result = tidal_search(query)

    return jsonify(result)

@app.route('/music/tidal/lyrics', methods=['POST'])
def tidal_lyrics_endpoint():
    """paroles depuis Tidal"""
    data = request.json or {}
    track_id = data.get('track_id')
    if not track_id:
        return jsonify({"error": "track_id required"}), 400

    return jsonify(tidal_lyrics(track_id))

@app.route('/music/tidal/login', methods=['POST'])
def tidal_login():
    """démarre le login Tidal (OAuth)"""
    return jsonify(login_tidalapi())

@app.route('/music/tidal/complete', methods=['POST'])
def tidal_complete_login():
    """complète le login après autorisation"""
    data = request.json or {}
    timeout = data.get('timeout', 60)
    return jsonify(tidal_complete(timeout=timeout))

@app.route('/music/tidal/favorites', methods=['GET'])
def tidal_favs():
    """favoris de l'utilisateur Tidal"""
    return jsonify(tidal_favorites())

@app.route('/now-playing', methods=['GET'])
@app.route('/music/now-playing', methods=['GET'])
def now_playing():
    """ce qui joue actuellement"""
    return jsonify(get_now_playing())

# === LISTEN (simulation d'écoute) ===

@app.route('/music/listen', methods=['POST'])
def listen_track():
    """Flow écoute un morceau"""
    data = request.json or {}
    return jsonify(listen(
        query=data.get('query'),
        track_id=data.get('track_id'),
        artist=data.get('artist'),
        track_name=data.get('track')
    ))

@app.route('/music/listen/album', methods=['POST'])
def listen_album_endpoint():
    """Flow écoute un album"""
    data = request.json or {}
    return jsonify(listen_album(
        album_id=data.get('album_id'),
        artist=data.get('artist'),
        album_name=data.get('album'),
        limit=data.get('limit', 5)
    ))

@app.route('/music/listen/artist', methods=['POST'])
def listen_artist_endpoint():
    """Flow explore un artiste"""
    data = request.json or {}
    name = data.get('name') or data.get('artist')
    if not name:
        return jsonify({"error": "artist name required"}), 400
    return jsonify(listen_artist(name, limit=data.get('limit', 5)))

@app.route('/music/listen/favorites', methods=['GET'])
def listen_favorites():
    """Flow explore tes favoris"""
    limit = request.args.get('limit', 10, type=int)
    return jsonify(explore_favorites(limit=limit))

# === DSP (analyse audio réelle) ===

@app.route('/music/dsp/status', methods=['GET'])
def dsp_status():
    """État du module DSP"""
    return jsonify({
        "available": DSP_AVAILABLE,
        "features": [
            "spectrum", "dynamics", "rhythm", "pitch",
            "key_detection", "timbre", "full_analysis"
        ] if DSP_AVAILABLE else []
    })

@app.route('/music/dsp/analyze', methods=['POST'])
def dsp_analyze():
    """Analyse DSP complète d'un fichier audio"""
    if not DSP_AVAILABLE:
        return jsonify({"error": "DSP module not available"}), 503

    data = request.json or {}

    # Par fichier local
    if 'path' in data:
        result = full_audio_analysis(data['path'])
        result['description'] = describe_audio(result)
        return jsonify(result)

    # Par URL
    if 'url' in data:
        result = analyze_from_url(data['url'])
        if 'error' not in result:
            result['description'] = describe_audio(result)
        return jsonify(result)

    return jsonify({"error": "path or url required"}), 400

@app.route('/music/dsp/spectrum', methods=['POST'])
def dsp_spectrum():
    """Analyse spectrale (FFT)"""
    if not DSP_AVAILABLE:
        return jsonify({"error": "DSP module not available"}), 503

    data = request.json or {}
    path = data.get('path')
    if not path:
        return jsonify({"error": "path required"}), 400

    try:
        from dsp import load_audio
        y, sr = load_audio(path)
        return jsonify(spectrum_analysis(y, sr))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/music/dsp/rhythm', methods=['POST'])
def dsp_rhythm():
    """Analyse rythmique (tempo, beats)"""
    if not DSP_AVAILABLE:
        return jsonify({"error": "DSP module not available"}), 503

    data = request.json or {}
    path = data.get('path')
    if not path:
        return jsonify({"error": "path required"}), 400

    try:
        from dsp import load_audio
        y, sr = load_audio(path)
        return jsonify(rhythm_analysis(y, sr))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/music/dsp/key', methods=['POST'])
def dsp_key():
    """Détection de tonalité"""
    if not DSP_AVAILABLE:
        return jsonify({"error": "DSP module not available"}), 503

    data = request.json or {}
    path = data.get('path')
    if not path:
        return jsonify({"error": "path required"}), 400

    try:
        from dsp import load_audio
        y, sr = load_audio(path)
        return jsonify(key_detection(y, sr))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/music/dsp/compare', methods=['POST'])
def dsp_compare():
    """Compare deux fichiers audio"""
    if not DSP_AVAILABLE:
        return jsonify({"error": "DSP module not available"}), 503

    data = request.json or {}
    path1 = data.get('path1')
    path2 = data.get('path2')

    if not path1 or not path2:
        return jsonify({"error": "path1 and path2 required"}), 400

    try:
        a1 = full_audio_analysis(path1)
        a2 = full_audio_analysis(path2)
        comparison = compare_tracks(a1, a2)
        return jsonify({
            "track1": a1,
            "track2": a2,
            "comparison": comparison
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === RUN ===

if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════╗
    ║         OREILLE - PORT {PORT}          ║
    ║    organe musical de Flow            ║
    ╚══════════════════════════════════════╝
    """)

    # vérifier les APIs
    if not os.getenv("GENIUS_TOKEN"):
        print("⚠️  GENIUS_TOKEN not set - lyrics disabled")
    else:
        print("✓ Genius API ready")

    if not os.getenv("SPOTIFY_CLIENT_ID"):
        print("⚠️  SPOTIFY_CLIENT_ID not set - audio features disabled")
    else:
        print("✓ Spotify API ready")

    # Tidal
    tidal = tidal_status()
    if tidal.get("tidalapi", {}).get("logged_in"):
        print("✓ Tidal logged in (full access)")
    elif tidal.get("official_api", {}).get("connected"):
        print("✓ Tidal API ready (catalog only)")
    else:
        print("⚠️  Tidal not configured - POST /music/tidal/login to connect")

    app.run(host='0.0.0.0', port=PORT, debug=False)
