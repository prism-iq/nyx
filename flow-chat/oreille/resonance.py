#!/usr/bin/env python3
"""resonance.py - connexions cross-domain entre musique et autres organes"""

import json
import requests
from datetime import datetime

# connexions vers les autres organes
CYTOPLASME_URL = "http://localhost:8091"
PANTHEON_URL = "http://localhost:8091/pantheon"

def connect_to_cytoplasme(text, context="music_analysis"):
    """envoie du texte au cytoplasme pour analyse LLM"""
    try:
        r = requests.post(
            f"{CYTOPLASME_URL}/think",
            json={
                "prompt": text,
                "context": context
            },
            timeout=30
        )
        return r.json()
    except Exception as e:
        return {"error": str(e), "fallback": True}

def find_god_resonance(lyrics_analysis):
    """trouve quel dieu du panthéon résonne avec les paroles"""
    themes = lyrics_analysis.get("themes", {}).get("top_3", [])

    # mapping thèmes → dieux
    theme_to_god = {
        "vie_mort": ["KALI", "SHIVA"],  # destruction/renaissance
        "argent_pouvoir": ["ATHENA", "ANANKE"],  # stratégie, nécessité
        "amour_relations": ["DIONYSUS", "SOPHIA"],  # émotion, sagesse
        "systeme_societe": ["ATHENA", "THOTH"],  # stratégie, vérité
        "spiritualite": ["SOPHIA", "APOLLO"],  # gnose, lumière
        "rue_survie": ["KALI", "HEPHAESTUS"],  # shadow, forge
        "art_creation": ["THOTH", "HEPHAESTUS", "DIONYSUS"]  # écriture, craft, création
    }

    gods = []
    for theme in themes:
        if theme in theme_to_god:
            gods.extend(theme_to_god[theme])

    # compter les occurrences
    from collections import Counter
    god_counts = Counter(gods)

    return {
        "resonant_gods": god_counts.most_common(3),
        "primary_god": god_counts.most_common(1)[0][0] if god_counts else None,
        "themes_analyzed": themes
    }

def find_pharmacopeia_mode(audio_features, lyrics_analysis):
    """suggère un mode cognitif basé sur la musique"""
    if not audio_features:
        return {"mode": "default", "reason": "no audio features"}

    energy = audio_features.get("energy", 0.5)
    valence = audio_features.get("valence", 0.5)
    tempo = audio_features.get("tempo", 120)
    speechiness = audio_features.get("speechiness", 0.5)

    # logique de sélection
    if energy > 0.8 and tempo > 140:
        mode = "RAGE"
        reason = "high energy + fast tempo"
    elif valence < 0.3 and energy < 0.4:
        mode = "COLD"
        reason = "dark + low energy"
    elif speechiness > 0.7:
        mode = "ZOOM-IN"
        reason = "high speechiness (focus on words)"
    elif valence > 0.7:
        mode = "SYNAPSE-X"
        reason = "positive vibes = open connections"
    elif energy > 0.6 and valence < 0.5:
        mode = "HUNTER"
        reason = "energetic but dark = pursuit"
    else:
        mode = "DISSOLVE"
        reason = "balanced = exploration"

    # ajuster selon les thèmes
    dominant_theme = lyrics_analysis.get("themes", {}).get("dominant")
    if dominant_theme == "spiritualite":
        mode = "ORACLE"
        reason = "spiritual theme detected"
    elif dominant_theme == "vie_mort":
        mode = "PHOENIX"
        reason = "life/death theme = trauma-safe processing"

    return {
        "suggested_mode": mode,
        "reason": reason,
        "audio_factors": {
            "energy": energy,
            "valence": valence,
            "tempo": tempo
        }
    }

def generate_insight(lyrics, audio_features, lyrics_analysis):
    """génère un insight cross-domain"""
    themes = lyrics_analysis.get("themes", {})
    vocabulary = lyrics_analysis.get("vocabulary", {})

    insight_parts = []

    # thématique
    if themes.get("dominant"):
        insight_parts.append(f"Cette track parle de {themes['dominant'].replace('_', '/')}.")

    # vocabulaire
    if vocabulary.get("lexical_diversity", 0) > 0.5:
        insight_parts.append("Vocabulaire riche.")
    else:
        insight_parts.append("Style répétitif, hypnotique.")

    # audio
    if audio_features:
        if audio_features.get("valence", 0.5) < 0.3:
            insight_parts.append("Sonorité sombre.")
        elif audio_features.get("valence", 0.5) > 0.7:
            insight_parts.append("Vibes positives.")

        if audio_features.get("energy", 0.5) > 0.7:
            insight_parts.append("Haute énergie.")

    # god resonance
    gods = find_god_resonance(lyrics_analysis)
    if gods.get("primary_god"):
        insight_parts.append(f"Résonne avec {gods['primary_god']}.")

    return {
        "insight": " ".join(insight_parts),
        "god_resonance": gods,
        "generated_at": datetime.now().isoformat()
    }

def deep_analysis(lyrics, audio_features, track_info):
    """analyse profonde avec connexions"""
    from analyzer import full_analysis

    # analyse de base
    lyrics_analysis = full_analysis(lyrics, track_info)

    # connexions
    god_resonance = find_god_resonance(lyrics_analysis)
    pharma_mode = find_pharmacopeia_mode(audio_features, lyrics_analysis)
    insight = generate_insight(lyrics, audio_features, lyrics_analysis)

    return {
        "track": track_info,
        "analysis": lyrics_analysis,
        "resonance": {
            "gods": god_resonance,
            "pharmacopeia": pharma_mode,
            "insight": insight["insight"]
        },
        "meta": {
            "analyzed_at": datetime.now().isoformat(),
            "has_audio": audio_features is not None
        }
    }


if __name__ == "__main__":
    # test
    mock_lyrics_analysis = {
        "themes": {
            "dominant": "rue_survie",
            "top_3": ["rue_survie", "argent_pouvoir", "vie_mort"]
        },
        "vocabulary": {"lexical_diversity": 0.45}
    }
    mock_audio = {"energy": 0.75, "valence": 0.35, "tempo": 95}

    result = find_pharmacopeia_mode(mock_audio, mock_lyrics_analysis)
    print(json.dumps(result, indent=2))
