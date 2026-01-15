#!/usr/bin/env python3
"""tidal.py - accès Tidal via API officielle + tidalapi"""

import os
import json
import base64
import requests
from pathlib import Path
from datetime import datetime, timedelta

# === TIDAL OFFICIAL API (catalog only) ===

TIDAL_CLIENT_ID = os.getenv("TIDAL_CLIENT_ID", "")
TIDAL_CLIENT_SECRET = os.getenv("TIDAL_CLIENT_SECRET", "")
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_API_URL = "https://openapi.tidal.com/v2"

# Token cache
_token_cache = {"token": None, "expires": None}

def _get_client_token():
    """obtient un token via client credentials (catalog only)"""
    global _token_cache

    if _token_cache["token"] and _token_cache["expires"] and datetime.now() < _token_cache["expires"]:
        return _token_cache["token"]

    if not TIDAL_CLIENT_ID or not TIDAL_CLIENT_SECRET:
        return None

    try:
        creds = base64.b64encode(f"{TIDAL_CLIENT_ID}:{TIDAL_CLIENT_SECRET}".encode()).decode()
        r = requests.post(
            TIDAL_TOKEN_URL,
            headers={"Authorization": f"Basic {creds}"},
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        data = r.json()

        _token_cache["token"] = data.get("access_token")
        _token_cache["expires"] = datetime.now() + timedelta(seconds=data.get("expires_in", 86400) - 60)

        return _token_cache["token"]

    except Exception as e:
        return None

def _api_headers():
    token = _get_client_token()
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.tidal.v1+json",
        "Content-Type": "application/vnd.tidal.v1+json"
    }

def search_catalog(query, types="TRACKS", country="US", limit=10):
    """recherche dans le catalogue Tidal"""
    headers = _api_headers()
    if not headers:
        return {"error": "Tidal credentials not set"}

    try:
        r = requests.get(
            f"{TIDAL_API_URL}/searchresults/{query}",
            headers=headers,
            params={
                "countryCode": country,
                "include": types,
                "limit": limit
            },
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_album(album_id, country="US"):
    """récupère un album"""
    headers = _api_headers()
    if not headers:
        return {"error": "Tidal credentials not set"}

    try:
        r = requests.get(
            f"{TIDAL_API_URL}/albums/{album_id}",
            headers=headers,
            params={"countryCode": country},
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_track(track_id, country="US"):
    """récupère un track"""
    headers = _api_headers()
    if not headers:
        return {"error": "Tidal credentials not set"}

    try:
        r = requests.get(
            f"{TIDAL_API_URL}/tracks/{track_id}",
            headers=headers,
            params={"countryCode": country},
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def get_artist(artist_id, country="US"):
    """récupère un artiste"""
    headers = _api_headers()
    if not headers:
        return {"error": "Tidal credentials not set"}

    try:
        r = requests.get(
            f"{TIDAL_API_URL}/artists/{artist_id}",
            headers=headers,
            params={"countryCode": country},
            timeout=10
        )
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# === TIDALAPI (unofficial - user login) ===

TIDAL_SESSION_FILE = Path("/opt/flow-chat/adn/music/tidal_session.json")

_tidalapi_session = None

def _get_tidalapi():
    """initialise tidalapi si disponible"""
    global _tidalapi_session

    if _tidalapi_session:
        return _tidalapi_session

    try:
        import tidalapi
    except ImportError:
        return None

    session = tidalapi.Session()

    # essayer de charger une session existante
    if TIDAL_SESSION_FILE.exists():
        try:
            with open(TIDAL_SESSION_FILE) as f:
                data = json.load(f)
            session.load_oauth_session(
                data.get("token_type"),
                data.get("access_token"),
                data.get("refresh_token"),
                datetime.fromisoformat(data.get("expiry_time"))
            )
            if session.check_login():
                _tidalapi_session = session
                return session
        except Exception:
            pass

    return None

_pending_login = {"session": None, "future": None}

def login_tidalapi():
    """lance le login OAuth pour tidalapi"""
    global _pending_login

    try:
        import tidalapi
    except ImportError:
        return {"error": "tidalapi not installed: pip install tidalapi"}

    session = tidalapi.Session()
    login, future = session.login_oauth()

    # stocker pour complete_login
    _pending_login["session"] = session
    _pending_login["future"] = future

    return {
        "status": "pending",
        "verification_url": login.verification_uri_complete,
        "user_code": login.user_code,
        "expires_in": login.expires_in,
        "instruction": f"Go to {login.verification_uri_complete} and enter code {login.user_code}"
    }

def complete_login(timeout=30):
    """complète le login après que l'user a autorisé"""
    global _tidalapi_session, _pending_login

    if not _pending_login["session"] or not _pending_login["future"]:
        return {"error": "no pending login - call login_tidalapi first"}

    session = _pending_login["session"]
    future = _pending_login["future"]

    try:
        # attendre que l'user autorise (avec timeout)
        future.result(timeout=timeout)

        if session.check_login():
            # sauvegarder la session
            TIDAL_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TIDAL_SESSION_FILE, 'w') as f:
                json.dump({
                    "token_type": session.token_type,
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                    "expiry_time": session.expiry_time.isoformat() if session.expiry_time else None
                }, f)

            _tidalapi_session = session
            _pending_login = {"session": None, "future": None}

            user_name = None
            try:
                user_name = session.user.name
            except Exception:
                pass

            return {"status": "logged_in", "user": user_name}

    except Exception as e:
        return {"error": str(e), "status": "timeout_or_denied"}

    return {"status": "not_logged_in"}

def get_user_favorites():
    """récupère les favoris de l'utilisateur"""
    session = _get_tidalapi()
    if not session:
        return {"error": "not logged in to Tidal"}

    try:
        favorites = session.user.favorites
        return {
            "tracks": [{"id": t.id, "name": t.name, "artist": t.artist.name} for t in favorites.tracks()[:20]],
            "albums": [{"id": a.id, "name": a.name, "artist": a.artist.name} for a in favorites.albums()[:10]],
            "artists": [{"id": a.id, "name": a.name} for a in favorites.artists()[:10]]
        }
    except Exception as e:
        return {"error": str(e)}

def get_track_lyrics(track_id):
    """récupère les paroles d'un track (si disponibles)"""
    session = _get_tidalapi()
    if not session:
        return {"error": "not logged in to Tidal"}

    try:
        import tidalapi
        track = session.track(track_id)

        # tidalapi peut avoir une méthode lyrics
        if hasattr(track, 'lyrics'):
            lyrics = track.lyrics()
            if lyrics:
                return {
                    "track_id": track_id,
                    "track_name": track.name,
                    "artist": track.artist.name,
                    "lyrics": lyrics.text if hasattr(lyrics, 'text') else str(lyrics),
                    "synced": hasattr(lyrics, 'subtitles'),
                    "source": "tidal"
                }

        return {"error": "lyrics not available", "track_id": track_id}

    except Exception as e:
        return {"error": str(e)}

def search_tidalapi(query, limit=10):
    """recherche via tidalapi (plus complète)"""
    session = _get_tidalapi()
    if not session:
        return {"error": "not logged in to Tidal"}

    try:
        results = session.search(query, limit=limit)
        return {
            "tracks": [{"id": t.id, "name": t.name, "artist": t.artist.name, "album": t.album.name if t.album else None}
                      for t in results.get('tracks', [])],
            "artists": [{"id": a.id, "name": a.name} for a in results.get('artists', [])],
            "albums": [{"id": a.id, "name": a.name, "artist": a.artist.name if a.artist else None}
                      for a in results.get('albums', [])]
        }
    except Exception as e:
        return {"error": str(e)}

def get_track_stream_url(track_id, quality="HIGH"):
    """récupère l'URL de stream (nécessite abonnement)"""
    session = _get_tidalapi()
    if not session:
        return {"error": "not logged in to Tidal"}

    try:
        track = session.track(track_id)
        stream = track.get_url()
        return {
            "track_id": track_id,
            "url": stream,
            "quality": quality
        }
    except Exception as e:
        return {"error": str(e)}


# === NOW PLAYING ===

def get_now_playing():
    """
    Tidal API ne donne pas accès au "now playing" en temps réel.
    On retourne le dernier favori comme proxy.
    """
    session = _get_tidalapi()
    if not session:
        return {"error": "not logged in to Tidal"}

    try:
        # Pas de now-playing dans l'API Tidal
        # Alternative: dernier favori
        favorites = session.user.favorites.tracks(limit=1)

        if favorites:
            track = favorites[0]
            return {
                "now_playing": False,
                "reason": "Tidal API doesn't expose real-time playback",
                "last_favorite": {
                    "id": track.id,
                    "name": track.name,
                    "artist": track.artist.name if track.artist else None,
                    "album": track.album.name if track.album else None
                },
                "suggestion": "Use /music/listen to analyze a track"
            }

        return {
            "now_playing": False,
            "reason": "Tidal API doesn't expose real-time playback",
            "last_favorite": None
        }

    except Exception as e:
        return {"error": str(e), "now_playing": False}


# === STATUS ===

def status():
    """état des connexions Tidal"""
    official_ok = bool(_get_client_token())
    tidalapi_ok = _get_tidalapi() is not None

    return {
        "official_api": {
            "configured": bool(TIDAL_CLIENT_ID),
            "connected": official_ok,
            "features": ["catalog_search", "albums", "tracks", "artists"] if official_ok else []
        },
        "tidalapi": {
            "installed": _check_tidalapi_installed(),
            "logged_in": tidalapi_ok,
            "features": ["favorites", "lyrics", "playlists", "stream"] if tidalapi_ok else []
        }
    }

def _check_tidalapi_installed():
    try:
        import tidalapi
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("=== TIDAL STATUS ===")
    print(json.dumps(status(), indent=2))
