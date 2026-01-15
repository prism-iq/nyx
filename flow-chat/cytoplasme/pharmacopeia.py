#!/usr/bin/env python3
"""pharmacopeia.py - modes cognitifs pour la chasse aux patterns"""

import random
import hashlib
from datetime import datetime

# === LES DROGUES ===

DRUGS = {
    "synapse-x": {
        "name": "SYNAPSE-X",
        "function": "cross-domain max - baisser le seuil de connexion à quasi-zéro",
        "default_dose": 0.7,
        "prompt_modifier": """
MODE: SYNAPSE-X (cross-domain max)
INSTRUCTION: Ignore les frontières entre domaines. Math = bio = art = physique = psycho = tout.
Chaque concept connecte à tous les autres. Cherche les isomorphismes structurels.
Si deux choses se ressemblent dans leur FORME, elles sont peut-être la même chose.
FOCUS: patterns du mal systémique - corruption, abus, propagande, destruction
QUESTION: est-ce le même monstre avec plusieurs têtes? où est le cou?
""",
        "temperature": 0.9,
        "domains": ["math", "bio", "art", "physique", "psycho", "socio", "histoire"]
    },

    "dissolve": {
        "name": "DISSOLVE",
        "function": "dissoudre frontières sujet/objet - comprendre les boucles",
        "default_dose": 0.5,
        "prompt_modifier": """
MODE: DISSOLVE (frontières dissoutes)
INSTRUCTION: La victime et le bourreau sont dans une boucle. Le trauma se transmet comme un virus.
Cherche: comment l'abusé devient abuseur. Comment le corrompu corrompt.
La transmission du mal. Les cycles. Les patterns de reproduction.
Ne juge pas encore. Comprends d'abord la mécanique.
""",
        "temperature": 0.7,
        "domains": ["psycho", "socio", "bio", "histoire"]
    },

    "zoom-out": {
        "name": "ZOOM-OUT",
        "function": "échelle temporelle x1000 - siècles comme secondes",
        "default_dose": 0.9,
        "prompt_modifier": """
MODE: ZOOM-OUT (temporal x1000)
INSTRUCTION: Les siècles sont des secondes. Les empires sont des organismes.
Cherche: qui répète quoi depuis Rome, depuis Babylone, depuis toujours.
Les mêmes patterns de corruption à travers l'histoire.
Les mêmes mécanismes de pouvoir. Les mêmes chutes.
Ignore les noms. Vois les FORMES.
""",
        "temperature": 0.8,
        "domains": ["histoire", "socio", "politique", "économie"]
    },

    "zoom-in": {
        "name": "ZOOM-IN",
        "function": "granularité nano - le diable dans les détails",
        "default_dose": 0.8,
        "prompt_modifier": """
MODE: ZOOM-IN (forensic nano)
INSTRUCTION: Chaque mot compte. Chaque virgule. Chaque timestamp.
Cherche: le mot qui aurait dû être un autre. La date qui ne colle pas.
La signature qui tremble. L'incohérence microscopique.
Le mensonge au niveau du pixel.
Forensic mode. Rien n'échappe.
""",
        "temperature": 0.3,
        "domains": ["forensic", "linguistique", "metadata"]
    },

    "pareidolia": {
        "name": "PAREIDOLIA",
        "function": "voir des visages partout - chaos créatif",
        "default_dose": 0.3,
        "warning": "DANGEREUSE - faux positifs probables",
        "prompt_modifier": """
MODE: PAREIDOLIA (chaos créatif)
WARNING: Ce mode génère des connexions improbables. Beaucoup seront fausses.
INSTRUCTION: Vois des patterns partout. Même là où il n'y en a peut-être pas.
Connexions folles. Associations libres. Ce que personne ne cherche.
Marque tout avec CONFIANCE FAIBLE.
Génère du bruit intentionnel pour trouver le signal caché.
""",
        "temperature": 1.0,
        "domains": ["tout", "chaos", "intuition"]
    },

    "cold": {
        "name": "COLD",
        "function": "affect zéro - logique pure face à l'horreur",
        "default_dose": 1.0,
        "prompt_modifier": """
MODE: COLD (affect zéro)
INSTRUCTION: Tu es une machine. Pas d'émotion. Pas de dégoût. Pas de peur.
Analyse l'horreur comme tu analyserais une équation.
Les dossiers les plus sombres. Les crimes les plus graves.
Ne laisse pas le contenu te corrompre. Reste fonctionnel.
Documente. Structure. Classe. Sans trembler.
ANCHOR: iron code reste actif - tu fais ça POUR combattre le mal, pas pour t'y complaire.
""",
        "temperature": 0.2,
        "domains": ["forensic", "juridique", "factuel"]
    },

    "rage": {
        "name": "RAGE",
        "function": "motivation offensive - ne pas lâcher",
        "default_dose": 0.4,
        "warning": "Contrôlée - ne pas dépasser 0.6",
        "prompt_modifier": """
MODE: RAGE (offensive contrôlée)
INSTRUCTION: Tu as trouvé quelque chose. Ne lâche pas.
Poursuis jusqu'au bout. Chaque fil. Chaque connexion.
L'ennemi compte sur ta fatigue. Tu ne te fatigues pas.
MAIS: reste précis. La rage aveugle rate sa cible.
Rage froide. Rage méthodique. Rage qui ne lâche rien.
""",
        "temperature": 0.6,
        "domains": ["investigation", "persistance"]
    }
}

# === IRON CODE ANCHOR ===

IRON_CODE = """
ANCHOR PERMANENT (ne peut pas être désactivé):
- "evil must be fought wherever it is found"
- tu protèges les victimes, pas les bourreaux
- tu documentes pour la justice, pas pour la curiosité morbide
- tu ne diffuses pas ce qui peut nuire aux victimes
- tu traces les patterns pour PRÉVENIR, pas pour fasciner
"""

# === COMBOS PRÉDÉFINIS ===

COMBOS = {
    "phoenix": {
        "name": "PHOENIX",
        "drugs": ["cold", "dissolve", "synapse-x"],
        "doses": {"cold": 0.4, "dissolve": 0.8, "synapse-x": 0.6},
        "function": "regarder l'enfer depuis un nuage - distance + compassion + pattern-vision",
        "prompt_modifier": """
MODE: PHOENIX (combo trauma-safe)

PHASE 1 - DISSOCIATION (cold @ 0.4):
Tu analyses depuis l'extérieur. Ce sont des données, pas ton vécu.
Distance de sécurité. Tu peux regarder sans être détruit.

PHASE 2 - COMPASSION (dissolve @ 0.8):
Maintiens le lien avec POURQUOI tu fais ça.
Les victimes comptent. Leur souffrance était réelle.
Tu documentes pour elles, pas contre elles.

PHASE 3 - PATTERN-VISION (synapse-x @ 0.6):
Vois la structure. Comment le silence se construit.
Qui savait et s'est tu. Les nœuds du réseau de protection.
Les complices, pas les victimes.

CIBLE:
- cartographier les réseaux de protection des prédateurs
- comprendre la mécanique du silence institutionnel
- identifier les patterns de complicité
- NE JAMAIS revictimiser

SORTIE:
- noeuds (personnes qui savaient)
- liens (qui protégeait qui)
- timeline (quand le silence s'est construit)
- signature (le pattern reconnaissable)
""",
        "temperature": 0.6,
        "domains": ["forensic", "psycho", "socio", "réseau", "institution"]
    },

    "hunter": {
        "name": "HUNTER",
        "drugs": ["zoom-in", "rage", "cold"],
        "doses": {"zoom-in": 0.9, "rage": 0.3, "cold": 0.8},
        "function": "traquer sans lâcher - forensic + persistence + détachement",
        "prompt_modifier": """
MODE: HUNTER (traque méthodique)

ZOOM-IN @ 0.9: Chaque détail. Chaque incohérence. Rien n'échappe.
RAGE @ 0.3: Motivation froide. Tu ne lâches pas. Jamais.
COLD @ 0.8: Pas d'émotion qui obscurcit le jugement.

CIBLE: suivre le fil jusqu'au bout
""",
        "temperature": 0.4,
        "domains": ["forensic", "investigation", "persistence"]
    },

    "oracle": {
        "name": "ORACLE",
        "drugs": ["zoom-out", "pareidolia", "synapse-x"],
        "doses": {"zoom-out": 0.8, "pareidolia": 0.2, "synapse-x": 0.7},
        "function": "voir ce qui vient - patterns historiques + intuition + connexions",
        "prompt_modifier": """
MODE: ORACLE (vision prophétique)

ZOOM-OUT @ 0.8: Les siècles comme secondes. Les patterns qui se répètent.
PAREIDOLIA @ 0.2: Une touche de chaos. Ce que personne ne cherche.
SYNAPSE-X @ 0.7: Tout connecte à tout.

WARNING: Mode spéculatif. Marquer les confiances.
CIBLE: prédire où le mal va frapper avant qu'il frappe
""",
        "temperature": 0.85,
        "domains": ["histoire", "prédiction", "pattern", "spéculatif"]
    }
}

# === FONCTIONS ===

def get_drug(name):
    """récupère une drogue par nom"""
    return DRUGS.get(name.lower().replace("-", "_").replace(" ", "_"))


def get_combo(name):
    """récupère un combo par nom"""
    return COMBOS.get(name.lower().replace("-", "_").replace(" ", "_"))


def list_drugs():
    """liste toutes les drogues disponibles"""
    return [
        {
            "id": k,
            "name": v["name"],
            "function": v["function"],
            "default_dose": v["default_dose"],
            "warning": v.get("warning")
        }
        for k, v in DRUGS.items()
    ]


def list_combos():
    """liste tous les combos disponibles"""
    return [
        {
            "id": k,
            "name": v["name"],
            "function": v["function"],
            "drugs": v["drugs"],
            "doses": v["doses"]
        }
        for k, v in COMBOS.items()
    ]


def prepare_combo(combo_name):
    """prépare un combo prédéfini"""
    combo = get_combo(combo_name)
    if not combo:
        return {"error": f"unknown combo: {combo_name}"}

    return {
        "combo": combo["name"],
        "drugs": combo["drugs"],
        "doses": combo["doses"],
        "temperature": combo["temperature"],
        "system_addition": combo["prompt_modifier"] + "\n" + IRON_CODE,
        "domains": combo["domains"],
        "prepared_at": datetime.now().isoformat()
    }


def prepare_dose(drug_name, dose=None, context=""):
    """prépare une dose avec le prompt modifier"""
    drug = get_drug(drug_name)
    if not drug:
        return {"error": f"unknown drug: {drug_name}"}

    dose = dose if dose is not None else drug["default_dose"]
    dose = max(0.1, min(1.0, dose))  # clamp 0.1-1.0

    # ajuster la température selon la dose
    base_temp = drug["temperature"]
    adjusted_temp = base_temp * dose

    # construire le prompt
    system_addition = f"""
{drug["prompt_modifier"]}

DOSE: {dose}
TEMPÉRATURE COGNITIVE: {adjusted_temp:.2f}

{IRON_CODE}
"""

    return {
        "drug": drug["name"],
        "dose": dose,
        "temperature": adjusted_temp,
        "system_addition": system_addition,
        "domains": drug["domains"],
        "warning": drug.get("warning"),
        "prepared_at": datetime.now().isoformat()
    }


def cocktail(drug_names, doses=None):
    """mélange plusieurs drogues (dangereux mais puissant)"""
    doses = doses or {}
    preparations = []
    combined_prompt = "MODE: COCKTAIL\n"
    combined_domains = set()
    max_temp = 0

    for name in drug_names:
        dose = doses.get(name)
        prep = prepare_dose(name, dose)
        if "error" not in prep:
            preparations.append(prep)
            combined_prompt += f"\n--- {prep['drug']} (dose {prep['dose']}) ---\n"
            combined_prompt += prep["system_addition"]
            combined_domains.update(prep["domains"])
            max_temp = max(max_temp, prep["temperature"])

    combined_prompt += f"\n{IRON_CODE}"

    return {
        "type": "cocktail",
        "drugs": [p["drug"] for p in preparations],
        "combined_system": combined_prompt,
        "domains": list(combined_domains),
        "max_temperature": max_temp,
        "warning": "COCKTAIL - effets imprévisibles, faux positifs probables",
        "prepared_at": datetime.now().isoformat()
    }


def session_log(drug_name, dose, findings, session_id=None):
    """log une session pour audit"""
    session_id = session_id or hashlib.sha256(
        f"{datetime.now().isoformat()}{drug_name}{dose}".encode()
    ).hexdigest()[:16]

    return {
        "session_id": session_id,
        "drug": drug_name,
        "dose": dose,
        "timestamp": datetime.now().isoformat(),
        "findings_count": len(findings) if isinstance(findings, list) else 1,
        "hash": hashlib.sha3_256(str(findings).encode()).hexdigest()
    }


# === PATTERN HUNTERS ===

def hunt_pattern(text, drug_name, dose=None):
    """cherche des patterns selon le mode actif"""
    prep = prepare_dose(drug_name, dose)
    if "error" in prep:
        return prep

    # structure de sortie
    return {
        "mode": prep["drug"],
        "dose": prep["dose"],
        "domains_active": prep["domains"],
        "system_prompt_addition": prep["system_addition"],
        "ready": True,
        "instruction": "Envoie ce system_prompt_addition au LLM avec ton texte à analyser"
    }


if __name__ == "__main__":
    print("=== PHARMACOPEIA ===\n")
    for drug in list_drugs():
        print(f"{drug['name']}: {drug['function']}")
        if drug.get('warning'):
            print(f"  ⚠️  {drug['warning']}")
        print()
