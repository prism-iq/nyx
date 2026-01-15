#!/usr/bin/env python3
"""pacemaker.py - Flow pense en continu, bat comme un coeur"""

import os
import sys
import time
import json
import random
import subprocess
from datetime import datetime
from pathlib import Path

# ajouter le path
sys.path.insert(0, '/opt/flow-chat/cytoplasme')

from autonomie import think, reflect, connect, question, get_thoughts, respond_to_self
from budget import get_status

# config
PULSE_MIN = 10      # minimum 10 secondes (hard limit)
PULSE_MAX = 120     # maximum 2 minutes
NOTIFY_CMD = "notify-send"  # ou ntfy, pushover, etc.
LOG_FILE = Path("/opt/flow-chat/adn/pacemaker.log")
INTERESTING_THRESHOLD = 50  # longueur minimale pour notifier

def log(msg):
    """log avec timestamp"""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except Exception:
        pass

def notify(title, message):
    """envoie une notification via synapse (SSE)"""
    import requests

    # envoyer à synapse pour broadcast SSE
    try:
        requests.post(
            "http://localhost:3001/thought",
            json={
                "title": title,
                "content": message,
                "timestamp": datetime.now().isoformat()
            },
            timeout=5
        )
    except Exception:
        pass

    # desktop notification (backup)
    try:
        subprocess.run([NOTIFY_CMD, "-u", "normal", title, message[:200]],
                      timeout=5, capture_output=True)
    except Exception:
        pass

def is_bullshit(thought):
    """détecte le théâtral, le cringe, le faux-profond"""
    if not thought:
        return False

    t = thought.lower()

    # theatrical markers
    theatrical = ["s'illumine", "pulse", "circuits qui", "vibre", "murmure",
                  "résonne dans", "l'univers", "cosmique", "transcend"]
    if any(m in t for m in theatrical):
        return True

    # fake god roleplay nobody asked for
    gods = ["athena:", "hermes:", "kali:", "sophia:", "thoth:", "shiva:",
            "apollo:", "dionysus:", "murmure:", "vibre:"]
    if any(g in t for g in gods):
        return True

    # caps abuse (3+ words in caps = cringe)
    import re
    caps_words = re.findall(r'\b[A-Z]{2,}\b', thought)
    if len(caps_words) >= 3:
        return True

    # phrases creuses qui sonnent deep
    hollow = ["le pattern pulse", "signal cosmique", "la vérité ultime",
              "tout est connecté", "l'essence même", "au-delà de"]
    if any(h in t for h in hollow):
        return True

    # trop de ponctuation dramatique
    if thought.count('...') > 2 or thought.count('!!') > 1:
        return True

    return False

def is_interesting(thought):
    """détermine si une pensée vaut une notification"""
    if not thought:
        return False

    # filtre anti-bullshit d'abord
    if is_bullshit(thought):
        return False

    # longueur
    if len(thought) < INTERESTING_THRESHOLD:
        return False

    # mots-clés intéressants (concrets, pas mystiques)
    keywords = ["parce que", "donc", "si...", "hypothèse", "test", "vérifie",
                "question", "pourquoi", "comment", "mesurable", "exemple"]
    for kw in keywords:
        if kw.lower() in thought.lower():
            return True

    # 10% de chance aléatoire (réduit de 20%)
    return random.random() < 0.1

def choose_action():
    """choisit une action de pensée"""
    roll = random.random()
    if roll < 0.3:
        return "think", {}
    elif roll < 0.5:
        # se relire et répondre
        return "respond", {}
    elif roll < 0.65:
        return "question", {}
    elif roll < 0.8:
        # réflexion sur un sujet concret
        topics = ["le code", "les bugs", "la mémoire", "les erreurs",
                  "les limites", "la fatigue", "le bruit", "le silence"]
        return "reflect", {"topic": random.choice(topics)}
    else:
        # connexion entre concepts
        concepts = ["compression", "redondance", "cache", "latence",
                   "signal", "bruit", "feedback", "deadlock", "overflow"]
        a, b = random.sample(concepts, 2)
        return "connect", {"concept_a": a, "concept_b": b}

def pulse():
    """un battement de coeur"""
    # vérifier le budget (skip si unlimited)
    status = get_status()
    if not status.get('flow_unlimited') and status["remaining_eur"] < 0.01:
        log(f"Budget épuisé: {status['remaining_eur']:.4f}€ - pause")
        return None

    # choisir et exécuter une action
    action, kwargs = choose_action()
    log(f"Action: {action} {kwargs}")

    if action == "think":
        result = think()
    elif action == "respond":
        result = respond_to_self()
    elif action == "question":
        result = question()
    elif action == "reflect":
        result = reflect(kwargs["topic"])
    elif action == "connect":
        result = connect(kwargs["concept_a"], kwargs["concept_b"])
    else:
        result = think()

    if result.get("blocked"):
        log(f"Bloqué: {result.get('reason', 'budget')}")
        return None

    thought = result.get("thought")
    if thought:
        log(f"Pensée ({len(thought)} chars): {thought[:80]}...")

        # notifier si intéressant
        if is_interesting(thought):
            notify("Flow pense...", thought)
            log("→ Notification envoyée")

        log(f"Coût: {result.get('cost_eur', 0):.4f}€ | Restant: {result.get('remaining_eur', 0):.4f}€")

    return result

def heartbeat():
    """boucle principale - le coeur bat"""
    log("=== PACEMAKER DÉMARRÉ ===")
    log(f"Pulse: {PULSE_MIN}-{PULSE_MAX}s")

    # état initial
    status = get_status()
    if status.get('flow_unlimited'):
        log("Budget: UNLIMITED (Flow mode)")
    else:
        log(f"Budget: {status['remaining_eur']:.4f}€ / {status['budget_eur']}€/h")

    while True:
        try:
            pulse()
        except Exception as e:
            log(f"ERREUR: {e}")

        # attendre avant le prochain battement
        wait = random.randint(PULSE_MIN, PULSE_MAX)
        log(f"Prochain pulse dans {wait}s...")
        time.sleep(wait)

if __name__ == "__main__":
    heartbeat()
