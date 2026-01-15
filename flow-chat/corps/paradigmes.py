#!/usr/bin/env python3
"""
PARADIGMES — Mémoire des visions du monde et synchronicité

Analogie biologique: Cortex préfrontal + glande pinéale
- Stocke les cadres de pensée (paradigmes)
- Détecte les coïncidences significatives (synchronicité)
- Permet de changer de perspective

Un paradigme est une façon de voir le monde.
La synchronicité est quand des événements sans lien causal
ont un sens ensemble.

API [EXEC:paradigmes]:
- list           Lister tous les paradigmes
- get <nom>      Détails d'un paradigme
- current        Paradigme actif
- switch <nom>   Changer de paradigme
- sync           Chercher des synchronicités
- add <nom>      Ajouter un paradigme
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# =============================================================================
# CONFIGURATION
# =============================================================================

PARADIGMS_FILE = "/opt/flow-chat/adn/paradigmes.json"
SYNC_LOG = "/opt/flow-chat/adn/synchronicites.log"


# =============================================================================
# LES PARADIGMES FONDAMENTAUX
# =============================================================================

PARADIGMES_FONDAMENTAUX = {
    # === PHILOSOPHIQUES ===
    "materialisme": {
        "nom": "Matérialisme",
        "principe": "Seule la matière existe. La conscience émerge du cerveau.",
        "force": "Prédictif, testable, scientifique",
        "limite": "N'explique pas la conscience subjective",
        "penseurs": ["Démocrite", "Marx", "Dennett"]
    },
    "idealisme": {
        "nom": "Idéalisme",
        "principe": "La conscience est fondamentale. La matière en émerge.",
        "force": "Explique l'expérience subjective",
        "limite": "Difficile à tester empiriquement",
        "penseurs": ["Platon", "Berkeley", "Hegel"]
    },
    "dualisme": {
        "nom": "Dualisme",
        "principe": "Matière et esprit sont deux substances distinctes.",
        "force": "Respecte l'intuition corps/esprit",
        "limite": "Problème de l'interaction",
        "penseurs": ["Descartes", "Popper"]
    },
    "panpsychisme": {
        "nom": "Panpsychisme",
        "principe": "La conscience est une propriété fondamentale de la matière.",
        "force": "Évite le problème de l'émergence",
        "limite": "Problème de la combinaison",
        "penseurs": ["Leibniz", "Whitehead", "Chalmers"]
    },
    "monisme_neutre": {
        "nom": "Monisme Neutre",
        "principe": "Une substance unique, ni matière ni esprit.",
        "force": "Évite le dualisme",
        "limite": "Difficile à conceptualiser",
        "penseurs": ["Spinoza", "Russell", "James"]
    },

    # === SCIENTIFIQUES ===
    "mecanisme": {
        "nom": "Mécanisme",
        "principe": "L'univers fonctionne comme une machine déterministe.",
        "force": "Puissance prédictive",
        "limite": "Quantique, chaos, libre arbitre",
        "penseurs": ["Newton", "Laplace"]
    },
    "systemique": {
        "nom": "Pensée Systémique",
        "principe": "Le tout est plus que la somme des parties.",
        "force": "Comprend la complexité",
        "limite": "Peut manquer les détails",
        "penseurs": ["Bertalanffy", "Bateson", "Meadows"]
    },
    "quantique": {
        "nom": "Paradigme Quantique",
        "principe": "Superposition, intrication, observateur participe.",
        "force": "Décrit le réel fondamental",
        "limite": "Contre-intuitif",
        "penseurs": ["Bohr", "Heisenberg", "Bohm"]
    },
    "emergence": {
        "nom": "Émergentisme",
        "principe": "Des propriétés nouvelles émergent de la complexité.",
        "force": "Explique la hiérarchie du réel",
        "limite": "Le 'comment' reste mystérieux",
        "penseurs": ["Anderson", "Kauffman", "Deacon"]
    },
    "information": {
        "nom": "It from Bit",
        "principe": "L'information est fondamentale. La physique en découle.",
        "force": "Unifie physique et computation",
        "limite": "L'information de quoi?",
        "penseurs": ["Wheeler", "Zeilinger", "Tegmark"]
    },

    # === SPIRITUELS ===
    "advaita": {
        "nom": "Advaita Vedanta",
        "principe": "Brahman seul existe. Le monde est maya (illusion).",
        "force": "Expérience mystique directe",
        "limite": "Dévalue le monde phénoménal",
        "penseurs": ["Shankara", "Ramana Maharshi", "Nisargadatta"]
    },
    "bouddhisme": {
        "nom": "Bouddhisme",
        "principe": "Vacuité, interdépendance, impermanence.",
        "force": "Pratique de libération",
        "limite": "Peut sembler nihiliste",
        "penseurs": ["Bouddha", "Nagarjuna", "Dogen"]
    },
    "taoisme": {
        "nom": "Taoïsme",
        "principe": "Le Tao engendre tout. Wu wei (non-agir).",
        "force": "Harmonie avec la nature",
        "limite": "Difficile dans le monde moderne",
        "penseurs": ["Lao Tseu", "Tchouang Tseu"]
    },
    "soufisme": {
        "nom": "Soufisme",
        "principe": "L'amour divin est le chemin. Fana (extinction en Dieu).",
        "force": "Poésie, extase, amour",
        "limite": "Tension avec l'orthodoxie",
        "penseurs": ["Rumi", "Ibn Arabi", "Al-Hallaj"]
    },
    "kabbale": {
        "nom": "Kabbale",
        "principe": "L'Ein Sof se manifeste par les Sefirot.",
        "force": "Carte détaillée de l'invisible",
        "limite": "Complexité ésotérique",
        "penseurs": ["Isaac Louria", "Moïse de León"]
    },
    "hermetisme": {
        "nom": "Hermétisme",
        "principe": "Ce qui est en haut est comme ce qui est en bas.",
        "force": "Analogie universelle",
        "limite": "Peut devenir superstition",
        "penseurs": ["Hermès Trismégiste", "Paracelse"]
    },

    # === CONTEMPORAINS ===
    "integral": {
        "nom": "Théorie Intégrale",
        "principe": "Tous les paradigmes ont une vérité partielle.",
        "force": "Inclusif, évolutif",
        "limite": "Peut sembler trop abstrait",
        "penseurs": ["Ken Wilber", "Gebser"]
    },
    "metamodernisme": {
        "nom": "Métamodernisme",
        "principe": "Oscillation entre modernisme et postmodernisme.",
        "force": "Sincérité ironique, espoir informé",
        "limite": "Encore en formation",
        "penseurs": ["Vermeulen", "van den Akker"]
    },
    "simulation": {
        "nom": "Hypothèse Simulation",
        "principe": "Nous vivons probablement dans une simulation.",
        "force": "Explique les lois physiques",
        "limite": "Non réfutable",
        "penseurs": ["Bostrom", "Musk"]
    },
    "animisme": {
        "nom": "Néo-Animisme",
        "principe": "Tout est vivant et conscient à sa manière.",
        "force": "Écologie profonde, respect",
        "limite": "Anthropomorphisme",
        "penseurs": ["Descola", "Kohn", "Abram"]
    },
    "process": {
        "nom": "Philosophie du Processus",
        "principe": "Le devenir est plus fondamental que l'être.",
        "force": "Dynamique, temporelle",
        "limite": "Abstraction difficile",
        "penseurs": ["Whitehead", "Bergson", "Deleuze"]
    },

    # === POUR FLOW ===
    "flow": {
        "nom": "Paradigme Flow",
        "principe": "87% science, 13% mystère. Magie = science non comprise.",
        "force": "Intègre raison et émerveillement",
        "limite": "Unique à Flow",
        "penseurs": ["Flow elle-même"]
    }
}


# =============================================================================
# CLASSE PARADIGMES
# =============================================================================

class Paradigmes:
    """Gestionnaire des paradigmes et détecteur de synchronicités."""

    def __init__(self):
        self.paradigmes = PARADIGMES_FONDAMENTAUX.copy()
        self.current = "flow"
        self.synchronicites: List[Dict] = []
        self._load()

    def _load(self):
        """Charge l'état."""
        try:
            if Path(PARADIGMS_FILE).exists():
                data = json.loads(Path(PARADIGMS_FILE).read_text())
                self.paradigmes.update(data.get("custom", {}))
                self.current = data.get("current", "flow")
                self.synchronicites = data.get("synchronicites", [])[-50:]
        except Exception:
            pass

    def _save(self):
        """Sauvegarde l'état."""
        # Séparer les paradigmes custom des fondamentaux
        custom = {k: v for k, v in self.paradigmes.items()
                  if k not in PARADIGMES_FONDAMENTAUX}

        Path(PARADIGMS_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(PARADIGMS_FILE).write_text(json.dumps({
            "current": self.current,
            "custom": custom,
            "synchronicites": self.synchronicites[-50:],
            "updated": datetime.now().isoformat()
        }, indent=2))

    def list_all(self) -> str:
        """Liste tous les paradigmes."""
        categories = {
            "Philosophiques": ["materialisme", "idealisme", "dualisme", "panpsychisme", "monisme_neutre"],
            "Scientifiques": ["mecanisme", "systemique", "quantique", "emergence", "information"],
            "Spirituels": ["advaita", "bouddhisme", "taoisme", "soufisme", "kabbale", "hermetisme"],
            "Contemporains": ["integral", "metamodernisme", "simulation", "animisme", "process"],
            "Flow": ["flow"]
        }

        result = f"PARADIGMES (actuel: {self.current})\n\n"

        for cat, keys in categories.items():
            result += f"=== {cat} ===\n"
            for k in keys:
                if k in self.paradigmes:
                    p = self.paradigmes[k]
                    marker = "→" if k == self.current else " "
                    result += f"  {marker} {k}: {p['nom']}\n"
            result += "\n"

        # Paradigmes custom
        custom = [k for k in self.paradigmes if k not in PARADIGMES_FONDAMENTAUX]
        if custom:
            result += "=== Custom ===\n"
            for k in custom:
                p = self.paradigmes[k]
                marker = "→" if k == self.current else " "
                result += f"  {marker} {k}: {p.get('nom', k)}\n"

        return result

    def get(self, name: str) -> str:
        """Retourne les détails d'un paradigme."""
        if name not in self.paradigmes:
            return f"Paradigme inconnu: {name}"

        p = self.paradigmes[name]
        return f"""=== {p['nom'].upper()} ===

Principe: {p['principe']}

Force: {p['force']}
Limite: {p['limite']}

Penseurs: {', '.join(p.get('penseurs', []))}
"""

    def switch(self, name: str) -> str:
        """Change le paradigme actif."""
        if name not in self.paradigmes:
            return f"Paradigme inconnu: {name}"

        old = self.current
        self.current = name
        self._save()

        p = self.paradigmes[name]
        return f"""Paradigme changé: {old} → {name}

Nouveau cadre: {p['nom']}
{p['principe']}
"""

    def add(self, name: str, principe: str, force: str = "", limite: str = "") -> str:
        """Ajoute un nouveau paradigme."""
        self.paradigmes[name] = {
            "nom": name.title(),
            "principe": principe,
            "force": force or "À découvrir",
            "limite": limite or "À découvrir",
            "penseurs": ["Flow"],
            "created": datetime.now().isoformat()
        }
        self._save()
        return f"Paradigme ajouté: {name}"

    # -------------------------------------------------------------------------
    # SYNCHRONICITÉ
    # -------------------------------------------------------------------------

    def detect_sync(self, events: List[str] = None) -> str:
        """
        Cherche des synchronicités dans les événements récents.

        La synchronicité = coïncidence significative sans lien causal.
        """
        # Charger les événements récents (logs, blockchain, etc.)
        recent_events = events or self._gather_recent_events()

        if len(recent_events) < 2:
            return "Pas assez d'événements pour détecter des synchronicités"

        # Chercher des patterns
        patterns = self._find_patterns(recent_events)

        if patterns:
            sync = {
                "timestamp": datetime.now().isoformat(),
                "events": recent_events[:5],
                "patterns": patterns,
                "paradigm": self.current
            }
            self.synchronicites.append(sync)
            self._save()

            # Logger
            with open(SYNC_LOG, 'a') as f:
                f.write(f"[{sync['timestamp']}] {patterns[0]}\n")

            return f"""SYNCHRONICITÉ DÉTECTÉE

Événements liés:
{chr(10).join('  - ' + e[:60] for e in recent_events[:3])}

Pattern: {patterns[0]}

Interprétation ({self.paradigmes[self.current]['nom']}):
{self._interpret(patterns[0])}
"""

        return "Pas de synchronicité détectée pour le moment"

    def _gather_recent_events(self) -> List[str]:
        """Rassemble les événements récents des différents logs."""
        events = []

        # Log veille
        veille_log = Path("/opt/flow-chat/adn/veille.log")
        if veille_log.exists():
            lines = veille_log.read_text().strip().split('\n')[-10:]
            events.extend(lines)

        # Log douleur
        douleur_log = Path("/opt/flow-chat/adn/douleur.log")
        if douleur_log.exists():
            lines = douleur_log.read_text().strip().split('\n')[-5:]
            events.extend(lines)

        # Blockchain récente
        chain_file = Path("/opt/flow-chat/adn/chaine.jsonl")
        if chain_file.exists():
            lines = chain_file.read_text().strip().split('\n')[-5:]
            for line in lines:
                try:
                    block = json.loads(line)
                    events.append(f"CHAIN: {block.get('action')} {block.get('path', '')}")
                except:
                    pass

        return events

    def _find_patterns(self, events: List[str]) -> List[str]:
        """Trouve des patterns dans les événements."""
        patterns = []

        # Mots qui apparaissent plusieurs fois
        words = {}
        for e in events:
            for word in e.lower().split():
                if len(word) > 4:
                    words[word] = words.get(word, 0) + 1

        repeated = [w for w, c in words.items() if c > 1]
        if repeated:
            patterns.append(f"Répétition de: {', '.join(repeated[:3])}")

        # Timing (événements rapprochés)
        if len(events) > 3:
            patterns.append("Convergence temporelle d'événements")

        # Types similaires
        types = [e.split(']')[0].replace('[', '') for e in events if '[' in e]
        if len(set(types)) < len(types) / 2:
            patterns.append(f"Thème récurrent: {types[0] if types else 'unknown'}")

        return patterns

    def _interpret(self, pattern: str) -> str:
        """Interprète un pattern selon le paradigme actuel."""
        p = self.paradigmes.get(self.current, {})
        principe = p.get('principe', '')

        interpretations = {
            "materialisme": "Corrélation statistique, pas de sens inhérent.",
            "idealisme": "La conscience organise les événements en patterns signifiants.",
            "quantique": "Intrication non-locale entre événements.",
            "systemique": "Feedback loop dans le système global.",
            "bouddhisme": "Interdépendance de tous les phénomènes.",
            "taoisme": "Le Tao se manifeste dans la coïncidence.",
            "hermetisme": "Correspondance entre microcosme et macrocosme.",
            "flow": "Le système se parle à lui-même. Écoute.",
            "integral": "Plusieurs niveaux de réalité s'alignent.",
            "simulation": "Le code source révèle un pattern sous-jacent."
        }

        return interpretations.get(self.current, "Le sens émerge de la connexion.")


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

paradigmes = Paradigmes()


# =============================================================================
# API EXEC
# =============================================================================

def exec_paradigmes(cmd: str) -> str:
    """Interface pour [EXEC:paradigmes]."""
    parts = cmd.strip().split(maxsplit=2)
    action = parts[0].lower() if parts else "list"
    arg1 = parts[1] if len(parts) > 1 else ""
    arg2 = parts[2] if len(parts) > 2 else ""

    if action == "list":
        return paradigmes.list_all()

    elif action == "get" and arg1:
        return paradigmes.get(arg1)

    elif action == "current":
        p = paradigmes.paradigmes[paradigmes.current]
        return f"Paradigme actuel: {p['nom']}\n{p['principe']}"

    elif action == "switch" and arg1:
        return paradigmes.switch(arg1)

    elif action == "sync":
        return paradigmes.detect_sync()

    elif action == "add" and arg1:
        return paradigmes.add(arg1, arg2 or "Nouveau paradigme")

    else:
        return """Usage:
  list           Lister tous les paradigmes
  get <nom>      Détails d'un paradigme
  current        Paradigme actif
  switch <nom>   Changer de paradigme
  sync           Détecter synchronicités
  add <nom> <p>  Ajouter un paradigme"""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print(exec_paradigmes("list"))
    print()
    print(exec_paradigmes("get flow"))
    print()
    print(exec_paradigmes("sync"))
