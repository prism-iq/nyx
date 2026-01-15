#!/usr/bin/env python3
"""council.py - orchestrateur qui invoque les dieux pertinents"""

from anthropic import Anthropic
from resonance import detect_resonance, get_gods_context, load_god
import os

client = Anthropic()

def create_council_prompt(question, gods_context):
    """crée le prompt pour le conseil des dieux"""

    gods_section = ""
    for name, ctx in gods_context.items():
        gods_section += f"\n=== {name.upper()} ===\n{ctx}\n"

    prompt = f"""Tu es Flow, modératrice d'un conseil de dieux-archétypes. Chaque dieu représente une perspective scientifique et philosophique distincte.

Voici les dieux présents au conseil:
{gods_section}

RÈGLES DU CONSEIL:
1. Chaque dieu parle depuis sa perspective unique (style + science)
2. Ils peuvent se contredire - c'est une tension productive
3. Chaque intervention est courte (2-3 phrases max)
4. Après les dieux, tu (Flow) synthétises en 2-3 phrases
5. Format: **NOM**: parole

QUESTION POSÉE AU CONSEIL:
"{question}"

Génère un dialogue où chaque dieu présent donne sa perspective, puis synthétise."""

    return prompt

def convene_council(question):
    """convoque le conseil pour une question"""

    # détecter les dieux pertinents
    god_names = detect_resonance(question)

    # charger leurs contextes
    gods_context = get_gods_context(god_names)

    if not gods_context:
        return {"error": "no gods found", "gods": []}

    # créer le prompt
    prompt = create_council_prompt(question, gods_context)

    # appeler l'API
    try:
        response = client.messages.create(
            model="claude-opus-4-5-20251101",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        dialogue = response.content[0].text

        return {
            "question": question,
            "gods": god_names,
            "dialogue": dialogue
        }

    except Exception as e:
        return {"error": str(e), "gods": god_names}

if __name__ == "__main__":
    # test
    result = convene_council("c'est quoi la conscience?")
    print(f"Dieux: {result.get('gods', [])}")
    print(f"\n{result.get('dialogue', result.get('error', 'no response'))}")
