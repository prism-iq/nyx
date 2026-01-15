#!/usr/bin/env python3
"""analyzer.py - analyse des patterns dans les paroles"""

import re
import json
from collections import Counter
from datetime import datetime

# Patterns thématiques (les 7 domaines de Flow)
THEMES = {
    "vie_mort": [
        "vie", "mort", "vivre", "mourir", "vivant", "dead", "life", "death",
        "survive", "kill", "tuer", "sang", "blood", "funeral", "grave",
        "cimetière", "respirer", "souffle", "breath", "last", "dernier"
    ],
    "argent_pouvoir": [
        "argent", "money", "cash", "dollar", "euro", "riche", "rich", "poor",
        "pauvre", "business", "deal", "bank", "compte", "fortune", "wealth",
        "power", "pouvoir", "roi", "king", "queen", "throne", "empire",
        "hustle", "grind", "boss", "chef"
    ],
    "amour_relations": [
        "amour", "love", "coeur", "heart", "baby", "bébé", "femme", "woman",
        "homme", "man", "kiss", "baiser", "toucher", "touch", "feel",
        "relation", "couple", "mariage", "divorce", "trust", "confiance",
        "trahir", "betray", "loyal"
    ],
    "systeme_societe": [
        "système", "system", "police", "flic", "cop", "prison", "jail",
        "justice", "law", "loi", "gouvernement", "government", "state",
        "état", "media", "news", "politique", "politic", "vote", "corrupt",
        "racism", "racisme", "oppression", "freedom", "liberté"
    ],
    "spiritualite": [
        "dieu", "god", "jesus", "allah", "pray", "prier", "soul", "âme",
        "spirit", "esprit", "heaven", "paradis", "hell", "enfer", "angel",
        "ange", "demon", "devil", "diable", "faith", "foi", "believe",
        "croire", "bless", "bénir", "sin", "péché"
    ],
    "rue_survie": [
        "rue", "street", "hood", "ghetto", "block", "corner", "trap",
        "deal", "drogue", "drug", "crack", "coke", "weed", "gun", "arme",
        "shoot", "tirer", "gang", "crew", "real", "fake", "respect",
        "diss", "beef", "enemy", "ennemi"
    ],
    "art_creation": [
        "rap", "flow", "beat", "son", "sound", "music", "musique", "write",
        "écrire", "plume", "pen", "mic", "micro", "studio", "album",
        "track", "verse", "couplet", "refrain", "hook", "freestyle",
        "art", "create", "créer", "inspire"
    ]
}

# Patterns de rime
VOWEL_SOUNDS = {
    'a': ['a', 'à', 'â'],
    'e': ['e', 'é', 'è', 'ê', 'ë'],
    'i': ['i', 'î', 'ï', 'y'],
    'o': ['o', 'ô', 'au', 'eau'],
    'u': ['u', 'û', 'ou'],
    'an': ['an', 'en', 'am', 'em'],
    'on': ['on', 'om'],
    'in': ['in', 'im', 'ain', 'ein']
}

def extract_words(text):
    """extrait les mots du texte"""
    # enlever les annotations [Verse 1] etc
    text = re.sub(r'\[.*?\]', '', text)
    # extraire les mots
    words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', text.lower())
    return words

def analyze_themes(lyrics):
    """analyse les thèmes présents dans les paroles"""
    words = extract_words(lyrics)
    word_set = set(words)

    theme_scores = {}
    theme_matches = {}

    for theme, keywords in THEMES.items():
        matches = word_set.intersection(set(keywords))
        # compter les occurrences
        count = sum(words.count(m) for m in matches)
        theme_scores[theme] = count
        theme_matches[theme] = list(matches)

    # normaliser
    total = sum(theme_scores.values()) or 1
    theme_percentages = {k: round(v / total * 100, 1) for k, v in theme_scores.items()}

    # top themes
    sorted_themes = sorted(theme_scores.items(), key=lambda x: -x[1])

    return {
        "scores": theme_scores,
        "percentages": theme_percentages,
        "matches": theme_matches,
        "dominant": sorted_themes[0][0] if sorted_themes else None,
        "top_3": [t[0] for t in sorted_themes[:3]]
    }

def analyze_structure(lyrics):
    """analyse la structure du texte"""
    lines = [l.strip() for l in lyrics.split('\n') if l.strip()]

    # détecter les sections
    sections = []
    current_section = {"type": "unknown", "lines": []}

    for line in lines:
        if re.match(r'\[.*?\]', line):
            if current_section["lines"]:
                sections.append(current_section)
            section_type = line.strip('[]').lower()
            if 'verse' in section_type or 'couplet' in section_type:
                section_type = 'verse'
            elif 'chorus' in section_type or 'refrain' in section_type or 'hook' in section_type:
                section_type = 'chorus'
            elif 'intro' in section_type:
                section_type = 'intro'
            elif 'outro' in section_type:
                section_type = 'outro'
            elif 'bridge' in section_type:
                section_type = 'bridge'
            current_section = {"type": section_type, "lines": []}
        else:
            current_section["lines"].append(line)

    if current_section["lines"]:
        sections.append(current_section)

    return {
        "total_lines": len(lines),
        "sections": len(sections),
        "section_breakdown": [{"type": s["type"], "lines": len(s["lines"])} for s in sections],
        "avg_line_length": sum(len(l) for l in lines) // len(lines) if lines else 0
    }

def analyze_rhymes(lyrics):
    """analyse les patterns de rime"""
    lines = [l.strip() for l in lyrics.split('\n') if l.strip() and not re.match(r'\[.*?\]', l)]

    def get_ending(line):
        words = re.findall(r'\b[a-zA-ZÀ-ÿ]+\b', line.lower())
        if not words:
            return ""
        last_word = words[-1]
        # prendre les 3 derniers caractères
        return last_word[-3:] if len(last_word) >= 3 else last_word

    endings = [get_ending(l) for l in lines]
    ending_counts = Counter(endings)

    # détecter les patterns (AA, ABAB, etc)
    rhyme_pairs = sum(1 for e, c in ending_counts.items() if c >= 2 and e)

    return {
        "total_lines": len(lines),
        "unique_endings": len(set(endings)),
        "rhyme_density": round(rhyme_pairs / len(lines) * 100, 1) if lines else 0,
        "common_endings": ending_counts.most_common(5)
    }

def analyze_vocabulary(lyrics):
    """analyse le vocabulaire"""
    words = extract_words(lyrics)

    if not words:
        return {"error": "no words found"}

    unique_words = set(words)
    word_freq = Counter(words)

    # complexité lexicale (type-token ratio)
    ttr = len(unique_words) / len(words)

    # mots les plus fréquents (excluant les mots courants)
    stopwords = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'est',
                 'je', 'tu', 'il', 'elle', 'on', 'nous', 'vous', 'ils', 'que',
                 'qui', 'ne', 'pas', 'dans', 'pour', 'sur', 'avec', 'ce', 'se',
                 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'you', 'he',
                 'she', 'it', 'we', 'they', 'to', 'of', 'and', 'in', 'that', 'my'}

    meaningful_words = {w: c for w, c in word_freq.items() if w not in stopwords and len(w) > 2}
    top_words = sorted(meaningful_words.items(), key=lambda x: -x[1])[:10]

    return {
        "total_words": len(words),
        "unique_words": len(unique_words),
        "lexical_diversity": round(ttr, 3),
        "avg_word_length": round(sum(len(w) for w in words) / len(words), 1),
        "top_words": top_words
    }

def full_analysis(lyrics, track_info=None):
    """analyse complète d'un texte"""
    themes = analyze_themes(lyrics)
    structure = analyze_structure(lyrics)
    rhymes = analyze_rhymes(lyrics)
    vocabulary = analyze_vocabulary(lyrics)

    result = {
        "themes": themes,
        "structure": structure,
        "rhymes": rhymes,
        "vocabulary": vocabulary,
        "analyzed_at": datetime.now().isoformat()
    }

    if track_info:
        result["track"] = track_info

    # insight global
    insights = []

    if themes["dominant"]:
        insights.append(f"Thème dominant: {themes['dominant']} ({themes['percentages'].get(themes['dominant'], 0)}%)")

    if vocabulary.get("lexical_diversity", 0) > 0.6:
        insights.append("Vocabulaire riche et varié")
    elif vocabulary.get("lexical_diversity", 0) < 0.3:
        insights.append("Vocabulaire répétitif (style hypnotique)")

    if rhymes.get("rhyme_density", 0) > 50:
        insights.append("Forte densité de rimes")

    result["insights"] = insights

    return result


if __name__ == "__main__":
    # test avec des paroles fictives
    test_lyrics = """
    [Verse 1]
    Je marche dans la rue, le coeur lourd
    La vie est dure mais je reste debout
    L'argent ne fait pas le bonheur dit-on
    Mais sans argent y'a que des questions

    [Chorus]
    Je cherche la vérité dans ce monde de fous
    Je cherche l'amour mais je trouve des loups
    """

    result = full_analysis(test_lyrics)
    print(json.dumps(result, indent=2, ensure_ascii=False))
