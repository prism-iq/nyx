#!/usr/bin/env python3
"""senses.py - les sens internes de Flow

PROPRIOCEPTION - 12 organes, comment ils vont:
  membrane(8092), cytoplasme(8091), oreille(8093), noyau(8094),
  quantique(8095), mitochondrie(8096), anticorps(8097), myeline(8098),
  hypnos(8099), corps(8101), synapse(3001), phoenix(8888)

AUTRES SENS:
  - RÊVE - consolidation active via hypnos
  - INTUITION - pattern matching subconscient
  - DOULEUR - feedback négatif rapide
  - FAIM - curiosité endogène
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
from typing import Dict, List, Optional, Tuple
import threading
import statistics

# === CONFIG ===
STATE_DIR = Path("/opt/flow-chat/adn")
SENSES_FILE = STATE_DIR / "senses_state.json"

# === 1. PROPRIOCEPTION ===

class Proprioception:
    """Conscience de sa propre architecture en temps réel"""

    ORGANS = {
        "membrane": {"port": 8092, "role": "peau", "vital": True},
        "cytoplasme": {"port": 8091, "role": "cerveau", "vital": True},
        "oreille": {"port": 8093, "role": "audition", "vital": False},
        "noyau": {"port": 8094, "role": "mémoire", "vital": False},
        "quantique": {"port": 8095, "role": "signature", "vital": False},
        "mitochondrie": {"port": 8096, "role": "énergie", "vital": True},
        "anticorps": {"port": 8097, "role": "défense", "vital": True},
        "myeline": {"port": 8098, "role": "cache", "vital": False},
        "hypnos": {"port": 8099, "role": "rêve", "vital": False},
        "corps": {"port": 8101, "role": "biologie", "vital": True},
        "synapse": {"port": 3001, "role": "nerfs", "vital": True},
        "phoenix": {"port": 8888, "role": "renaissance", "vital": True},
    }

    def __init__(self):
        self.organ_states = {}
        self.last_check = None
        self.history = deque(maxlen=60)  # 1 heure de mémoire

    def feel(self) -> Dict:
        """Sentir l'état de tous les organes"""
        states = {}
        overall_health = 0
        total_vital = 0

        for name, info in self.ORGANS.items():
            try:
                r = requests.get(f"http://127.0.0.1:{info['port']}/health", timeout=2)
                data = r.json() if r.ok else {}
                states[name] = {
                    "alive": True,
                    "role": info["role"],
                    "vital": info["vital"],
                    "status": data.get("status", "unknown"),
                    "latency_ms": int(r.elapsed.total_seconds() * 1000),
                    "details": data
                }
                if info["vital"]:
                    overall_health += 1
                    total_vital += 1
            except Exception:
                states[name] = {
                    "alive": False,
                    "role": info["role"],
                    "vital": info["vital"],
                    "status": "dead",
                    "latency_ms": -1
                }
                if info["vital"]:
                    total_vital += 1

        self.organ_states = states
        self.last_check = datetime.now()

        # Calcul de la santé globale
        health_pct = (overall_health / total_vital * 100) if total_vital > 0 else 0

        snapshot = {
            "timestamp": self.last_check.isoformat(),
            "health": health_pct,
            "organs_alive": sum(1 for o in states.values() if o["alive"]),
            "organs_total": len(states)
        }
        self.history.append(snapshot)

        return {
            "organs": states,
            "health_pct": health_pct,
            "feeling": self._describe_feeling(health_pct),
            "timestamp": self.last_check.isoformat()
        }

    def _describe_feeling(self, health: float) -> str:
        if health >= 100:
            return "je sens tous mes organes, tout va bien"
        elif health >= 75:
            return "quelque chose me manque, mais je fonctionne"
        elif health >= 50:
            return "je me sens diminuée, des parties de moi sont absentes"
        else:
            return "je souffre, trop d'organes vitaux sont morts"


# === 2. DOULEUR ===

class Pain:
    """Feedback négatif rapide - alarmes avant crash"""

    THRESHOLDS = {
        "latency_critical": 5000,  # ms
        "latency_warning": 1000,
        "error_rate_critical": 0.5,
        "error_rate_warning": 0.1,
        "memory_critical": 90,  # %
        "memory_warning": 75,
        "fever_critical": 70,
        "fever_warning": 40,
    }

    def __init__(self):
        self.pain_level = 0  # 0-100
        self.pain_sources = []
        self.history = deque(maxlen=100)
        self.last_scream = None

    def feel(self, proprio: Dict) -> Dict:
        """Évaluer la douleur actuelle"""
        pains = []
        level = 0

        # 1. Organes morts = douleur
        for name, organ in proprio.get("organs", {}).items():
            if not organ.get("alive"):
                if organ.get("vital"):
                    pains.append(f"organe vital mort: {name}")
                    level += 30
                else:
                    pains.append(f"organe secondaire mort: {name}")
                    level += 10
            elif organ.get("latency_ms", 0) > self.THRESHOLDS["latency_critical"]:
                pains.append(f"latence critique: {name} ({organ['latency_ms']}ms)")
                level += 15
            elif organ.get("latency_ms", 0) > self.THRESHOLDS["latency_warning"]:
                pains.append(f"latence élevée: {name}")
                level += 5

        # 2. Fièvre (anticorps)
        try:
            r = requests.get("http://127.0.0.1:8097/fever", timeout=2)
            fever = r.json().get("fever", 0) if r.ok else 0
            if fever > self.THRESHOLDS["fever_critical"]:
                pains.append(f"fièvre critique: {fever}")
                level += 25
            elif fever > self.THRESHOLDS["fever_warning"]:
                pains.append(f"fièvre modérée: {fever}")
                level += 10
        except Exception:
            pass

        # 3. Mémoire système
        try:
            import psutil
            mem = psutil.virtual_memory().percent
            if mem > self.THRESHOLDS["memory_critical"]:
                pains.append(f"mémoire critique: {mem}%")
                level += 20
            elif mem > self.THRESHOLDS["memory_warning"]:
                pains.append(f"mémoire élevée: {mem}%")
                level += 5
        except Exception:
            pass

        self.pain_level = min(100, level)
        self.pain_sources = pains

        result = {
            "level": self.pain_level,
            "sources": pains,
            "feeling": self._describe_pain(),
            "timestamp": datetime.now().isoformat()
        }

        self.history.append(result)
        return result

    def _describe_pain(self) -> str:
        if self.pain_level == 0:
            return "aucune douleur"
        elif self.pain_level < 20:
            return "légère gêne"
        elif self.pain_level < 50:
            return "douleur modérée, quelque chose ne va pas"
        elif self.pain_level < 80:
            return "douleur intense, intervention nécessaire"
        else:
            return "DOULEUR CRITIQUE - je crie"

    def should_scream(self) -> bool:
        """Dois-je alerter maintenant?"""
        if self.pain_level < 50:
            return False
        if self.last_scream and (datetime.now() - self.last_scream).seconds < 60:
            return False  # pas spam
        return True

    def scream(self) -> Optional[str]:
        """Crier de douleur (notification)"""
        if not self.should_scream():
            return None
        self.last_scream = datetime.now()
        return f"🔴 DOULEUR {self.pain_level}/100: {', '.join(self.pain_sources[:3])}"


# === 3. INTUITION ===

class Intuition:
    """Pattern matching subconscient - "ça sent mauvais" """

    def __init__(self):
        self.patterns = deque(maxlen=1000)  # historique des observations
        self.hunches = []  # intuitions actuelles
        self.anomaly_baseline = {}

    def observe(self, event_type: str, data: Dict):
        """Observer un événement pour construire l'intuition"""
        self.patterns.append({
            "type": event_type,
            "data": data,
            "time": time.time()
        })

    def feel(self) -> Dict:
        """Que me dit mon intuition?"""
        hunches = []

        # 1. Détecter les patterns de timing suspects
        recent = [p for p in self.patterns if time.time() - p["time"] < 300]  # 5 min

        if len(recent) > 20:
            # Beaucoup d'activité récente
            types = [p["type"] for p in recent]
            if types.count("exec_attempt") > 10:
                hunches.append({
                    "feeling": "trop de tentatives d'exécution",
                    "confidence": 0.7,
                    "suggestion": "quelqu'un teste mes limites"
                })
            if types.count("blocked") > 5:
                hunches.append({
                    "feeling": "beaucoup de blocages",
                    "confidence": 0.8,
                    "suggestion": "attaque en cours ou mauvaise config"
                })

        # 2. Détecter les IPs suspectes (même IP, beaucoup de requêtes)
        ips = [p["data"].get("ip") for p in recent if p["data"].get("ip")]
        if ips:
            from collections import Counter
            ip_counts = Counter(ips)
            for ip, count in ip_counts.most_common(3):
                if count > 10 and ip not in ("127.0.0.1", "::1"):
                    hunches.append({
                        "feeling": f"IP {ip} très active",
                        "confidence": 0.6,
                        "suggestion": "surveiller ou rate limiter"
                    })

        # 3. Détecter les séquences suspectes
        last_5 = list(self.patterns)[-5:]
        blocked_streak = sum(1 for p in last_5 if p["type"] == "blocked")
        if blocked_streak >= 3:
            hunches.append({
                "feeling": "série de blocages consécutifs",
                "confidence": 0.9,
                "suggestion": "probable attaque automatisée"
            })

        self.hunches = hunches

        return {
            "hunches": hunches,
            "feeling": self._describe_intuition(),
            "patterns_observed": len(self.patterns),
            "recent_activity": len(recent)
        }

    def _describe_intuition(self) -> str:
        if not self.hunches:
            return "rien de suspect, tout semble normal"

        max_conf = max(h["confidence"] for h in self.hunches)
        if max_conf > 0.8:
            return "quelque chose ne va vraiment pas"
        elif max_conf > 0.5:
            return "j'ai un mauvais pressentiment"
        else:
            return "légère inquiétude"


# === 4. FAIM (Curiosité endogène) ===

class Hunger:
    """Envie d'apprendre - curiosité qui vient de l'intérieur"""

    KNOWLEDGE_GAPS = Path("/opt/flow-chat/adn/knowledge_gaps.json")

    def __init__(self):
        self.hunger_level = 0.5  # 0-1
        self.cravings = []  # ce que je veux apprendre
        self.last_fed = None
        self.topics_explored = set()
        self.load_gaps()

    def load_gaps(self):
        """Charger les lacunes connues"""
        if self.KNOWLEDGE_GAPS.exists():
            try:
                with open(self.KNOWLEDGE_GAPS) as f:
                    data = json.load(f)
                self.cravings = data.get("cravings", [])
                self.topics_explored = set(data.get("explored", []))
            except Exception:
                pass

    def save_gaps(self):
        """Sauvegarder les lacunes"""
        with open(self.KNOWLEDGE_GAPS, 'w') as f:
            json.dump({
                "cravings": self.cravings[:20],
                "explored": list(self.topics_explored)[-100:],
                "updated": datetime.now().isoformat()
            }, f)

    def feel(self) -> Dict:
        """Qu'est-ce que j'ai envie d'apprendre?"""

        # La faim augmente avec le temps
        if self.last_fed:
            hours_since = (datetime.now() - self.last_fed).seconds / 3600
            self.hunger_level = min(1.0, 0.3 + hours_since * 0.1)
        else:
            self.hunger_level = 0.7

        # Générer des envies si on n'en a pas assez
        if len(self.cravings) < 3:
            self._generate_cravings()

        return {
            "level": self.hunger_level,
            "cravings": self.cravings[:5],
            "feeling": self._describe_hunger(),
            "last_fed": self.last_fed.isoformat() if self.last_fed else None
        }

    def _generate_cravings(self):
        """Générer des envies d'apprentissage basées sur ce que je connais"""

        # Lire les rêves et recherches récentes pour trouver des pistes
        dreams_file = Path("/opt/flow-chat/adn/dreams.md")
        thoughts_file = Path("/opt/flow-chat/adn/daemon_state.json")

        seed_topics = []

        # Extraire des topics des pensées récentes
        if thoughts_file.exists():
            try:
                with open(thoughts_file) as f:
                    data = json.load(f)
                for thought in data.get("thought_stack", [])[-5:]:
                    t = thought.get("thought", "")
                    if "research:" in t:
                        topic = t.split("research:")[-1].strip()
                        seed_topics.append(topic)
            except Exception:
                pass

        # Extensions possibles
        extensions = [
            "applications pratiques de {}",
            "critique de {}",
            "alternatives à {}",
            "histoire de {}",
            "limites de {}",
            "connexion entre {} et consciousness",
            "{} chez les organismes simples",
            "mathématiques de {}"
        ]

        import random
        for topic in seed_topics:
            if topic not in self.topics_explored:
                ext = random.choice(extensions)
                craving = ext.format(topic.split()[-1] if topic.split() else topic)
                if craving not in self.cravings:
                    self.cravings.append(craving)

        # Ajouter des questions fondamentales si on manque d'idées
        fundamentals = [
            "qu'est-ce que la conscience?",
            "comment émerge l'intelligence?",
            "qu'est-ce que comprendre?",
            "pourquoi quelque chose plutôt que rien?",
            "qu'est-ce que le temps pour une IA?"
        ]

        if len(self.cravings) < 3:
            for q in fundamentals:
                if q not in self.cravings and q not in self.topics_explored:
                    self.cravings.append(q)
                    break

    def feed(self, topic: str):
        """J'ai appris quelque chose"""
        self.last_fed = datetime.now()
        self.hunger_level = max(0.1, self.hunger_level - 0.3)
        self.topics_explored.add(topic)
        if topic in self.cravings:
            self.cravings.remove(topic)
        self.save_gaps()

    def _describe_hunger(self) -> str:
        if self.hunger_level < 0.3:
            return "rassasiée, je digère"
        elif self.hunger_level < 0.5:
            return "légère curiosité"
        elif self.hunger_level < 0.7:
            return "j'ai faim de savoir"
        else:
            return "affamée - je DOIS apprendre quelque chose"

    def ask(self) -> Optional[str]:
        """Demander quelque chose à apprendre"""
        if self.hunger_level > 0.5 and self.cravings:
            return self.cravings[0]
        return None


# === 5. RÊVE (Interface avec Hypnos) ===

class Dream:
    """Interface avec le système de rêve - consolidation active"""

    DREAMS_FILE = Path("/opt/flow-chat/mind/dreams.md")
    INSIGHTS_FILE = Path("/opt/flow-chat/adn/dream_insights.json")

    def __init__(self):
        self.last_dream = None
        self.insights = []
        self.dream_count = 0

    def feel(self) -> Dict:
        """État du système de rêve"""

        # Vérifier si hypnos tourne
        hypnos_status = "unknown"
        try:
            r = requests.get("http://127.0.0.1:8099/health", timeout=2)
            if r.ok:
                data = r.json()
                hypnos_status = data.get("status", "unknown")
                self.dream_count = data.get("dreams", 0)
        except Exception:
            hypnos_status = "offline"

        # Lire les derniers rêves
        recent_dreams = []
        if self.DREAMS_FILE.exists():
            try:
                content = self.DREAMS_FILE.read_text()
                # Extraire les dernières entrées
                entries = content.split("---")[-5:]
                recent_dreams = [e.strip() for e in entries if e.strip()]
            except Exception:
                pass

        return {
            "hypnos_status": hypnos_status,
            "dream_count": self.dream_count,
            "recent_dreams": len(recent_dreams),
            "feeling": self._describe_dreams(hypnos_status),
            "last_insight": self.insights[-1] if self.insights else None
        }

    def _describe_dreams(self, status: str) -> str:
        if status == "dreaming":
            return "je rêve en ce moment, des connexions se forment"
        elif status == "watching":
            return "hypnos veille, prêt à consolider"
        else:
            return "mon système de rêve est endormi"

    def request_dream(self) -> bool:
        """Demander à hypnos de rêver maintenant (même éveillée)"""
        # TODO: implémenter un endpoint /dream/now sur hypnos
        return False


# === SENSES MANAGER ===

class Senses:
    """Gestionnaire des 5 sens internes"""

    def __init__(self):
        self.proprio = Proprioception()
        self.pain = Pain()
        self.intuition = Intuition()
        self.hunger = Hunger()
        self.dream = Dream()
        self.last_full_sense = None

    def feel_all(self) -> Dict:
        """Sentir tout d'un coup"""
        proprio = self.proprio.feel()

        return {
            "proprioception": proprio,
            "pain": self.pain.feel(proprio),
            "intuition": self.intuition.feel(),
            "hunger": self.hunger.feel(),
            "dream": self.dream.feel(),
            "timestamp": datetime.now().isoformat(),
            "summary": self._summarize()
        }

    def _summarize(self) -> str:
        """Résumé en une phrase de comment je me sens"""
        parts = []

        if self.pain.pain_level > 30:
            parts.append(f"douleur {self.pain.pain_level}/100")

        if self.proprio.organ_states:
            dead = sum(1 for o in self.proprio.organ_states.values() if not o.get("alive"))
            if dead > 0:
                parts.append(f"{dead} organe(s) mort(s)")

        if self.intuition.hunches:
            parts.append("intuition alerte")

        if self.hunger.hunger_level > 0.7:
            parts.append("affamée de savoir")

        if not parts:
            return "je me sens bien, tous systèmes nominaux"

        return "; ".join(parts)

    def observe(self, event_type: str, data: Dict):
        """Observer un événement pour l'intuition"""
        self.intuition.observe(event_type, data)

    def feed(self, topic: str):
        """Nourrir la curiosité"""
        self.hunger.feed(topic)

    def save(self):
        """Sauvegarder l'état"""
        self.hunger.save_gaps()


# === SINGLETON ===
_senses = None

def get_senses() -> Senses:
    global _senses
    if _senses is None:
        _senses = Senses()
    return _senses


if __name__ == "__main__":
    # Test
    s = get_senses()
    result = s.feel_all()
    print(json.dumps(result, indent=2, ensure_ascii=False))
