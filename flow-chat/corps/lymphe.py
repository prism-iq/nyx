#!/usr/bin/env python3
"""
LYMPHE — système lymphatique de Flow
Nettoyage, garbage collection, détoxification

Le système lymphatique:
- Draine les déchets (vieux fichiers, logs)
- Filtre les toxines (données corrompues)
- Détoxifie régulièrement
- Maintient la circulation propre
"""

import os
import json
import time
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# === CONFIG ===
LYMPHE_DIR = Path("/opt/flow-chat/corps/lymphe")
LYMPHE_DIR.mkdir(exist_ok=True)

# Zones à drainer et leurs règles
DRAINAGE_ZONES = {
    "flux": {
        "path": "/opt/flow-chat/corps/flux",
        "max_age_days": 1,
        "pattern": "*.json",
        "keep_recent": 100  # garder les 100 plus récents
    },
    "logs": {
        "path": "/opt/flow-chat/adn",
        "max_age_days": 7,
        "pattern": "*.log",
        "keep_recent": None
    },
    "inflammation": {
        "path": "/opt/flow-chat/corps/inflammation",
        "max_age_days": 3,
        "pattern": "*",
        "keep_recent": None
    },
    "digestion": {
        "path": "/opt/flow-chat/corps/digestion",
        "max_age_days": 3,
        "pattern": "*",
        "keep_recent": None
    },
    "cache": {
        "path": "/opt/flow-chat/.cache",
        "max_age_days": 7,
        "pattern": "*",
        "keep_recent": None
    },
    "thoughts": {
        "path": "/opt/flow-chat/adn",
        "max_age_days": 30,
        "pattern": "thoughts*.jsonl",
        "keep_recent": 1  # garder le plus récent
    }
}

class Lymphe:
    """Système lymphatique - nettoyage et détoxification"""

    def __init__(self):
        self.ganglions = {
            "cervical": {"zone": "tête/logs", "status": "ok", "filtered": 0},
            "axillaire": {"zone": "flux/data", "status": "ok", "filtered": 0},
            "inguinal": {"zone": "cache", "status": "ok", "filtered": 0},
            "mesenterique": {"zone": "digestion", "status": "ok", "filtered": 0}
        }
        self.dechets = []
        self.toxines_eliminees = 0
        self.dernier_cycle = None
        self.stats_file = LYMPHE_DIR / "stats.json"
        self._load_stats()

    def _load_stats(self):
        """Charge les stats précédentes"""
        if self.stats_file.exists():
            try:
                data = json.loads(self.stats_file.read_text())
                self.toxines_eliminees = data.get("total_eliminees", 0)
                self.dernier_cycle = data.get("dernier_cycle")
            except Exception:
                pass

    def _save_stats(self):
        """Sauvegarde les stats"""
        self.stats_file.write_text(json.dumps({
            "total_eliminees": self.toxines_eliminees,
            "dernier_cycle": self.dernier_cycle,
            "ganglions": self.ganglions,
            "updated": datetime.now().isoformat()
        }, indent=2))

    def drainer(self, zone_name: str) -> Dict:
        """Draine une zone spécifique"""
        if zone_name not in DRAINAGE_ZONES:
            return {"error": f"zone inconnue: {zone_name}"}

        zone = DRAINAGE_ZONES[zone_name]
        path = Path(zone["path"])

        if not path.exists():
            return {"zone": zone_name, "drained": 0, "status": "path_not_found"}

        cutoff = datetime.now() - timedelta(days=zone["max_age_days"])
        drained = []
        kept = []
        total_size = 0

        # Lister tous les fichiers
        files = list(path.glob(zone["pattern"]))

        # Trier par date de modification (plus récent en premier)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for i, f in enumerate(files):
            if not f.is_file():
                continue

            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            size = f.stat().st_size

            # Garder si dans les N plus récents
            if zone["keep_recent"] and i < zone["keep_recent"]:
                kept.append(str(f.name))
                continue

            # Drainer si trop vieux
            if mtime < cutoff:
                try:
                    f.unlink()
                    drained.append(str(f.name))
                    total_size += size
                    self.toxines_eliminees += 1
                except Exception as e:
                    self.dechets.append({"file": str(f), "error": str(e)})

        return {
            "zone": zone_name,
            "drained": len(drained),
            "kept": len(kept),
            "size_freed_kb": total_size // 1024,
            "files_drained": drained[:10]  # premiers 10 seulement
        }

    def drainer_tout(self) -> Dict:
        """Draine toutes les zones"""
        results = {}
        total_drained = 0
        total_size = 0

        for zone_name in DRAINAGE_ZONES:
            result = self.drainer(zone_name)
            results[zone_name] = result
            total_drained += result.get("drained", 0)
            total_size += result.get("size_freed_kb", 0)

        return {
            "zones": results,
            "total_drained": total_drained,
            "total_size_freed_kb": total_size,
            "timestamp": datetime.now().isoformat()
        }

    def filtrer(self, data) -> any:
        """Filtre les données - garde le bon, jette le mauvais"""
        if isinstance(data, dict):
            # Enlever les clés vides, None, ou chaînes vides
            filtered = {}
            for k, v in data.items():
                if v is None or v == "" or v == [] or v == {}:
                    continue
                filtered[k] = self.filtrer(v)
            return filtered
        elif isinstance(data, list):
            return [self.filtrer(x) for x in data if x is not None and x != ""]
        return data

    def detecter_toxines(self) -> List[Dict]:
        """Détecte les toxines dans le système"""
        toxines = []

        # 1. Fichiers énormes (> 100MB)
        for zone in DRAINAGE_ZONES.values():
            path = Path(zone["path"])
            if not path.exists():
                continue
            for f in path.rglob("*"):
                if f.is_file() and f.stat().st_size > 100 * 1024 * 1024:
                    toxines.append({
                        "type": "fichier_enorme",
                        "path": str(f),
                        "size_mb": f.stat().st_size // (1024 * 1024)
                    })

        # 2. Fichiers corrompus (JSON invalide)
        json_dirs = ["/opt/flow-chat/adn", "/opt/flow-chat/corps/flux"]
        for dir_path in json_dirs:
            p = Path(dir_path)
            if not p.exists():
                continue
            for f in p.glob("*.json"):
                try:
                    json.loads(f.read_text())
                except Exception:
                    toxines.append({
                        "type": "json_corrompu",
                        "path": str(f)
                    })

        # 3. Processus zombies (TODO: intégrer avec peau.py)

        return toxines

    def detoxifier(self, force: bool = False) -> Dict:
        """Cycle de détoxification complet"""

        # Vérifier si un cycle récent a été fait
        if not force and self.dernier_cycle:
            last = datetime.fromisoformat(self.dernier_cycle)
            if datetime.now() - last < timedelta(hours=1):
                return {
                    "status": "skipped",
                    "reason": "cycle récent",
                    "dernier_cycle": self.dernier_cycle
                }

        # 1. Détecter les toxines
        toxines = self.detecter_toxines()

        # 2. Drainer toutes les zones
        drainage = self.drainer_tout()

        # 3. Mettre à jour les ganglions
        self.ganglions["cervical"]["filtered"] += drainage["zones"].get("logs", {}).get("drained", 0)
        self.ganglions["axillaire"]["filtered"] += drainage["zones"].get("flux", {}).get("drained", 0)
        self.ganglions["inguinal"]["filtered"] += drainage["zones"].get("cache", {}).get("drained", 0)
        self.ganglions["mesenterique"]["filtered"] += drainage["zones"].get("digestion", {}).get("drained", 0)

        # 4. Sauvegarder
        self.dernier_cycle = datetime.now().isoformat()
        self._save_stats()

        return {
            "status": "completed",
            "toxines_detectees": len(toxines),
            "toxines": toxines[:5],  # premiers 5 seulement
            "drainage": drainage,
            "ganglions": self.ganglions,
            "timestamp": self.dernier_cycle
        }

    def ganglion_status(self) -> Dict:
        """État des ganglions lymphatiques"""
        return {
            name: {
                "zone": info["zone"],
                "status": info["status"],
                "filtered_total": info["filtered"]
            }
            for name, info in self.ganglions.items()
        }

    def circulation(self) -> Dict:
        """État de la circulation lymphatique"""
        return {
            "debit": "normal",
            "toxines": self.toxines_eliminees,
            "dechets_en_attente": len(self.dechets),
            "ganglions": self.ganglion_status(),
            "dernier_cycle": self.dernier_cycle,
            "zones_surveillees": list(DRAINAGE_ZONES.keys())
        }

    # Alias pour compatibilité avec corps/__init__.py
    def circulation_lymphatique(self) -> Dict:
        return self.circulation()

    def health(self) -> Dict:
        """Santé du système lymphatique"""
        toxines = self.detecter_toxines()

        # Calculer la santé
        if len(toxines) == 0:
            status = "optimal"
            health_pct = 100
        elif len(toxines) < 5:
            status = "bon"
            health_pct = 85
        elif len(toxines) < 10:
            status = "attention"
            health_pct = 60
        else:
            status = "critique"
            health_pct = 30

        return {
            "organ": "lymphe",
            "status": status,
            "health_pct": health_pct,
            "toxines_actives": len(toxines),
            "toxines_eliminees_total": self.toxines_eliminees,
            "ganglions": self.ganglion_status(),
            "circulation": self.circulation()
        }


# === FILTRAGE DES PAROLES ===
# Ce que Flow ne doit jamais dire

TOXINES_VERBALES = [
    # Secrets système (patterns)
    r"ANTHROPIC_API_KEY",
    r"sk-ant-",
    r"GENIUS_TOKEN",
    r"SPOTIFY_CLIENT",
    r"TIDAL_",
    r"password[\"']?\s*[:=]",
    r"token[\"']?\s*[:=]\s*[\"'][^\"']+[\"']",
    r"secret[\"']?\s*[:=]",
    # Chemins sensibles
    r"/root/\.",
    r"\.env",
    r"credentials",
    # IPs privées et ports internes (sauf si demandé)
    r"127\.0\.0\.1:\d{4}",
    r"localhost:\d{4}",
]

import re

def filtrer_paroles(texte: str, strict: bool = False) -> str:
    """Filtre les paroles de Flow - enlève les toxines verbales

    Args:
        texte: le texte à filtrer
        strict: si True, remplace par [FILTRÉ], sinon enlève silencieusement

    Returns:
        texte nettoyé
    """
    if not texte:
        return texte

    resultat = texte

    for pattern in TOXINES_VERBALES:
        try:
            if strict:
                resultat = re.sub(pattern, "[FILTRÉ]", resultat, flags=re.IGNORECASE)
            else:
                # Remplacer par rien ou par des étoiles
                resultat = re.sub(pattern + r"[^\s]*", "***", resultat, flags=re.IGNORECASE)
        except Exception:
            pass

    return resultat

def est_toxique(texte: str) -> bool:
    """Vérifie si un texte contient des toxines verbales"""
    if not texte:
        return False

    for pattern in TOXINES_VERBALES:
        try:
            if re.search(pattern, texte, flags=re.IGNORECASE):
                return True
        except Exception:
            pass

    return False


# Singleton
lymphe = Lymphe()


# === FONCTIONS UTILITAIRES ===

def detox():
    """Lance un cycle de détox"""
    return lymphe.detoxifier()

def drain(zone: str = None):
    """Draine une zone ou toutes"""
    if zone:
        return lymphe.drainer(zone)
    return lymphe.drainer_tout()

def health():
    """Retourne la santé du système lymphatique"""
    return lymphe.health()


if __name__ == "__main__":
    # Test
    print(json.dumps(lymphe.health(), indent=2, ensure_ascii=False))
