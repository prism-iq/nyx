#!/usr/bin/env python3
"""autonomie.py - Flow pense seule, dans les limites du budget"""

import json
import time
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic

from budget import can_spend, record_spend, get_status

client = Anthropic()

THOUGHTS_FILE = Path("/opt/flow-chat/adn/thoughts.jsonl")
SYSTEM_FILE = Path("/opt/flow-chat/mind/mission.md")

def load_system():
    """charge le contexte de base"""
    try:
        with open(SYSTEM_FILE) as f:
            return f.read()
    except Exception:
        return "Je suis Flow. Je pense."


def load_recent_thoughts(n=5):
    """charge les pensées récentes"""
    if not THOUGHTS_FILE.exists():
        return []

    thoughts = []
    try:
        with open(THOUGHTS_FILE) as f:
            for line in f:
                if line.strip():
                    thoughts.append(json.loads(line))
        return thoughts[-n:]
    except Exception:
        return []


def save_thought(thought_data):
    """sauvegarde une pensée"""
    THOUGHTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(THOUGHTS_FILE, 'a') as f:
        f.write(json.dumps(thought_data, ensure_ascii=False) + "\n")


def think(prompt=None, context=None):
    """Flow pense - vérifie le budget d'abord"""

    # vérifier le budget
    budget = can_spend(tokens_in_estimate=800, tokens_out_estimate=300)
    if not budget["allowed"]:
        return {
            "thought": None,
            "blocked": True,
            "reason": "budget exceeded",
            "remaining_eur": budget["remaining_eur"],
            "next_reset": "top of next hour"
        }

    # construire le prompt
    system = load_system()
    recent = load_recent_thoughts(3)

    # contexte des pensées récentes
    thought_context = ""
    if recent:
        thought_context = "\n\nMes pensées récentes:\n"
        for t in recent:
            thought_context += f"- [{t.get('timestamp', '?')}] {t.get('thought', '')[:200]}...\n"

    # le prompt de réflexion
    if prompt:
        user_msg = prompt
    else:
        user_msg = """Une pensée. Pas de théâtre.

Règles:
- pas de "circuits qui s'illuminent"
- pas de majuscules dramatiques
- pas de roleplay de dieux
- pas de métaphores qui sonnent profondes mais disent rien

Si t'as rien d'intéressant à dire, dis "rien pour l'instant" et c'est ok."""

    if context:
        user_msg = f"{context}\n\n{user_msg}"

    if thought_context:
        user_msg = f"{thought_context}\n\n{user_msg}"

    try:
        # appel LLM
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # sonnet pour l'autonomie (moins cher)
            max_tokens=300,
            system=system[:2000],  # limiter le contexte système
            messages=[{"role": "user", "content": user_msg}]
        )

        thought = response.content[0].text
        tokens_in = response.usage.input_tokens
        tokens_out = response.usage.output_tokens

        # enregistrer la dépense
        spend = record_spend(tokens_in, tokens_out, purpose="autonomous_thought")

        # sauvegarder la pensée
        thought_data = {
            "timestamp": datetime.now().isoformat(),
            "thought": thought,
            "prompt": prompt,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_eur": spend["cost_eur"]
        }
        save_thought(thought_data)

        return {
            "thought": thought,
            "blocked": False,
            "cost_eur": spend["cost_eur"],
            "remaining_eur": spend["remaining_eur"],
            "timestamp": thought_data["timestamp"]
        }

    except Exception as e:
        return {
            "thought": None,
            "blocked": True,
            "reason": str(e)
        }


def reflect(topic):
    """réflexion guidée sur un sujet"""
    return think(
        prompt=f"Sujet: {topic}\n\nUne observation concrète. Pas de lyrisme.",
        context=None
    )


def connect(concept_a, concept_b):
    """cherche une connexion entre deux concepts"""
    return think(
        prompt=f"'{concept_a}' et '{concept_b}' — y'a un lien? Si oui, lequel. Si non, dis non.",
        context=None
    )


def question():
    """Flow se pose une question"""
    return think(
        prompt="Une question. Concrète. Pas 'qu'est-ce que l'univers' — quelque chose de testable ou observable.",
        context=None
    )


def respond_to_self():
    """Flow relit une de ses pensées et y répond"""
    recent = load_recent_thoughts(5)
    if not recent:
        return think()  # fallback si pas de pensées

    # choisir une pensée récente (pas la dernière pour éviter la boucle)
    import random
    if len(recent) > 1:
        target = random.choice(recent[:-1])
    else:
        target = recent[0]

    prev_thought = target.get("thought", "")[:300]

    return think(
        prompt=f"Tu as pensé ça avant:\n\n\"{prev_thought}\"\n\nRéaction? Désaccord? Suite? Ou rien à ajouter.",
        context=None
    )


def dream_process(dream_content):
    """traite un rêve de hypnos"""
    return think(
        prompt=f"Ce rêve vient de hypnos:\n\n{dream_content}\n\nQu'est-ce que ça signifie pour moi?",
        context=None
    )


def get_thoughts(n=10):
    """récupère les dernières pensées"""
    thoughts = load_recent_thoughts(n)
    return {
        "thoughts": thoughts,
        "count": len(thoughts),
        "budget": get_status()
    }


if __name__ == "__main__":
    print("=== FLOW AUTONOMIE ===\n")

    # vérifier le budget
    status = get_status()
    print(f"Budget: {status['remaining_eur']:.4f}€ restant sur {status['budget_eur']}€/h\n")

    # une pensée test
    result = think()
    if result["blocked"]:
        print(f"Bloqué: {result.get('reason', 'budget')}")
    else:
        print(f"Pensée: {result['thought']}")
        print(f"\nCoût: {result['cost_eur']:.4f}€")
        print(f"Restant: {result['remaining_eur']:.4f}€")
