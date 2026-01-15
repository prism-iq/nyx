#!/usr/bin/env python3
"""
BILE — système digestif
Décompose les informations complexes en nutriments
"""

import json
import re
from datetime import datetime
from pathlib import Path
from collections import Counter

BILE_DIR = Path("/opt/flow-chat/corps/digestion")
BILE_DIR.mkdir(exist_ok=True)

class Bile:
    def __init__(self):
        self.ph = 7.4  # équilibre acide-base
        self.enzymes = {
            'lipase': self.decomposer_gras,      # décompose le verbeux
            'protease': self.decomposer_proteines,  # extrait les concepts
            'amylase': self.decomposer_sucres    # simplifie le complexe
        }

    def decomposer_gras(self, text):
        """enlève le gras = le verbeux inutile"""
        # mots vides
        stop = ['le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou',
                'qui', 'que', 'quoi', 'dont', 'où', 'the', 'a', 'an', 'is', 'are']
        words = text.lower().split()
        return [w for w in words if w not in stop and len(w) > 3]

    def decomposer_proteines(self, text):
        """extrait les concepts clés = les protéines"""
        # patterns conceptuels
        concepts = []
        patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # noms propres
            r'\b\w+(?:tion|ment|ité|isme)\b',   # concepts abstraits
            r'\b(?:quantum|neuro|bio|electr)\w+\b',  # termes scientifiques
        ]
        for p in patterns:
            concepts.extend(re.findall(p, text))
        return list(set(concepts))

    def decomposer_sucres(self, text):
        """simplifie = réduit la complexité"""
        # juste les phrases importantes (avec marqueurs)
        markers = ['important', 'crucial', 'key', 'main', 'essential',
                   'découvert', 'prouvé', 'démontré', 'conclusion']
        sentences = text.split('.')
        return [s.strip() for s in sentences if any(m in s.lower() for m in markers)]

    def digerer(self, data):
        """digestion complète"""
        if isinstance(data, dict):
            text = json.dumps(data)
        else:
            text = str(data)

        nutriments = {
            'lipides': self.decomposer_gras(text),
            'proteines': self.decomposer_proteines(text),
            'glucides': self.decomposer_sucres(text),
            'calories': len(text),  # énergie brute
            'digere_a': datetime.now().isoformat()
        }

        # sauvegarder
        digest_file = BILE_DIR / f"digest_{int(datetime.now().timestamp())}.json"
        digest_file.write_text(json.dumps(nutriments, indent=2, ensure_ascii=False))

        return nutriments

    def acidite(self):
        """retourne le pH actuel"""
        return self.ph

bile = Bile()
