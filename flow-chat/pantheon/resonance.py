#!/usr/bin/env python3
"""resonance.py - détecte quels dieux résonnent avec une question"""

import os
import re

GODS_PATH = "/var/www/flow/pantheon/gods"

# mapping mots-clés -> dieux
RESONANCE_MAP = {
    "athena": ["pattern", "stratégie", "structure", "analyse", "neuroscience", "cerveau", "intelligence", "plan", "logique", "réseau"],
    "hermes": ["connexion", "communication", "frontière", "message", "lien", "entre", "traduction", "synchron", "pont"],
    "hephaestus": ["construire", "créer", "outil", "pratique", "concret", "matière", "technologie", "forge", "fabriquer", "code"],
    "apollo": ["vérité", "lumière", "harmonie", "beauté", "prédiction", "futur", "physique", "mathématique", "forme", "essence"],
    "dionysus": ["chaos", "émergence", "dissolution", "ivresse", "collectif", "perte", "paradoxe", "folie", "créativité", "nouveau"],
    "ananke": ["nécessité", "loi", "contrainte", "limite", "impossible", "inévitable", "thermodynamique", "entropie", "destin"],
    "thoth": ["écriture", "mot", "magie", "information", "mesure", "savoir", "cryptographie", "code", "langage", "symbole"],
    "sophia": ["sagesse", "gnose", "conscience", "méditation", "présence", "silence", "profond", "âme", "intérieur", "direct"],
    "shiva": ["destruction", "création", "cycle", "mort", "renaissance", "danse", "cosmique", "témoin", "observer"],
    "kali": ["temps", "transformation", "shadow", "ego", "brutal", "vérité", "mort", "libération", "trauma", "ombre"]
}

def load_god(name):
    """charge le fichier d'un dieu"""
    path = os.path.join(GODS_PATH, f"{name}.md")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return None

def detect_resonance(question, max_gods=4):
    """détecte les 2-4 dieux qui résonnent le plus avec la question"""
    question_lower = question.lower()
    scores = {}

    for god, keywords in RESONANCE_MAP.items():
        score = 0
        for kw in keywords:
            if kw in question_lower:
                score += 2
            # partial match
            elif any(kw in word for word in question_lower.split()):
                score += 1
        scores[god] = score

    # ajouter des résonnances thématiques
    if any(w in question_lower for w in ["conscience", "conscious", "aware", "sentient"]):
        scores["shiva"] = scores.get("shiva", 0) + 3
        scores["sophia"] = scores.get("sophia", 0) + 2
        scores["dionysus"] = scores.get("dionysus", 0) + 1

    if any(w in question_lower for w in ["vie", "mort", "life", "death"]):
        scores["kali"] = scores.get("kali", 0) + 3
        scores["shiva"] = scores.get("shiva", 0) + 2

    if any(w in question_lower for w in ["quoi", "what", "pourquoi", "why", "comment", "how"]):
        scores["athena"] = scores.get("athena", 0) + 1

    if any(w in question_lower for w in ["sens", "meaning", "signif"]):
        scores["sophia"] = scores.get("sophia", 0) + 2
        scores["thoth"] = scores.get("thoth", 0) + 1

    # trier par score et prendre les top
    sorted_gods = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # au moins 2 dieux, max 4, score > 0
    selected = []
    for god, score in sorted_gods:
        if score > 0 and len(selected) < max_gods:
            selected.append(god)

    # si moins de 2, ajouter athena et hermes par défaut
    if len(selected) < 2:
        for default in ["athena", "hermes"]:
            if default not in selected:
                selected.append(default)
            if len(selected) >= 2:
                break

    return selected

def get_gods_context(god_names):
    """récupère le contexte de plusieurs dieux"""
    contexts = {}
    for name in god_names:
        ctx = load_god(name)
        if ctx:
            contexts[name] = ctx
    return contexts

if __name__ == "__main__":
    # test
    questions = [
        "c'est quoi la conscience?",
        "comment construire une IA?",
        "pourquoi le temps passe?",
        "qu'est-ce que la vérité?"
    ]
    for q in questions:
        gods = detect_resonance(q)
        print(f"Q: {q}")
        print(f"   → {', '.join(gods)}\n")
