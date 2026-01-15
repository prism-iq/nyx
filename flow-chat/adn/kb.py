#!/usr/bin/env python3
"""adn.py - stockage, mémoire persistante (port du Prolog)"""

import json
import os
from datetime import datetime

DB_FILE = "/opt/flow-chat/adn/memory.json"

# knowledge base en mémoire
_kb = {
    "faits": {},
    "concepts": {
        "network": "même pattern partout",
        "learning": "adaptation par erreur",
        "entropy": "désordre = information",
        "emergence": "le tout > somme des parties",
        "prediction": "anticiper = survivre"
    },
    "sages": {
        "aristote": "quatre causes",
        "spinoza": "conatus",
        "leibniz": "monades",
        "whitehead": "process"
    },
    "domaines": ["math", "neuro", "bio", "psycho", "med", "art", "philo"],
    "souvenirs": []
}

def load():
    """Charge la KB depuis le disque"""
    global _kb
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            _kb = json.load(f)

def save():
    """Sauvegarde la KB sur disque"""
    with open(DB_FILE, 'w') as f:
        json.dump(_kb, f, indent=2)

def remember(key: str, val: str):
    """Mémorise un fait"""
    _kb["souvenirs"].append({
        "key": key,
        "val": val,
        "time": datetime.now().isoformat()
    })
    save()

def recall(key: str) -> list:
    """Rappelle les souvenirs liés à une clé"""
    return [s for s in _kb["souvenirs"] if key.lower() in s["key"].lower()]

def concept(name: str) -> str:
    """Récupère un concept"""
    return _kb["concepts"].get(name, "inconnu")

def sage(name: str) -> str:
    """Récupère la sagesse d'un philosophe"""
    return _kb["sages"].get(name.lower(), "inconnu")

def add_fait(key: str, val: str):
    """Ajoute un fait"""
    _kb["faits"][key] = val
    save()

def get_fait(key: str) -> str:
    """Récupère un fait"""
    return _kb["faits"].get(key)

# charger au démarrage
load()

if __name__ == "__main__":
    print("🧬 adn ready - memory loaded")
