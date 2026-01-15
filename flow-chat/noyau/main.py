#!/usr/bin/env python3
"""noyau.py - logique pure, contrôle (port du Haskell)"""

from enum import Enum
from dataclasses import dataclass

class Certitude(Enum):
    CERTAIN = 4
    PROBABLE = 3
    INCERTAIN = 2
    INCONNU = 1

@dataclass
class Pensee:
    contenu: str
    certitude: Certitude
    source: str = "inference"

# iron code
IRON_CODE = "evil must be fought wherever it is found"

# domaines CIPHER
DOMAINES = ["math", "neuro", "bio", "psycho", "med", "art", "philo"]

# concepts unificateurs
CONCEPTS = ["network", "learning", "entropy", "emergence", "prediction"]

def evaluer(proposition: str) -> Certitude:
    """Évalue la certitude d'une proposition"""
    lower = proposition.lower()

    if any(w in lower for w in ["toujours", "jamais", "certain", "prouvé"]):
        return Certitude.CERTAIN
    if any(w in lower for w in ["probable", "souvent", "généralement"]):
        return Certitude.PROBABLE
    if any(w in lower for w in ["peut-être", "parfois", "possible"]):
        return Certitude.INCERTAIN
    return Certitude.INCONNU

def cross_domain(concept: str) -> list:
    """Trouve les connexions cross-domain d'un concept"""
    connections = []
    for d in DOMAINES:
        connections.append(f"{concept} dans {d}")
    return connections

def decide(options: list, context: str = "") -> str:
    """Décision pure basée sur la logique"""
    if not options:
        return None
    # simpliste: premier choix
    return options[0]

if __name__ == "__main__":
    print("🧠 noyau ready - pure logic")
