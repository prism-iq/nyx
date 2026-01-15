#!/usr/bin/env python3
"""
DOULEUR — Système nerveux sensoriel et auto-guérison de Flow

Analogie biologique: Nocicepteurs + système de guérison
- Les nocicepteurs détectent la douleur (erreurs)
- Le cerveau localise et analyse la douleur
- Le corps déclenche la guérison (réparation automatique)
- La mémoire retient pour éviter la récidive

Fonctionnement:
1. Capture les erreurs (try/except global)
2. Analyse la cause (traceback, contexte)
3. Tente l'auto-guérison si possible
4. Enregistre dans la mémoire de douleur
5. Alerte si douleur chronique (erreur répétée)

Guérisons possibles:
- Fichier manquant → créer le fichier/dossier
- Module non trouvé → installer la dépendance
- Service down → redémarrer le service
- Syntaxe invalide → restaurer depuis backup
- Permission denied → corriger les permissions

API [EXEC:douleur]:
- status    État du système de douleur
- history   Historique des douleurs
- heal      Tenter de guérir la dernière douleur
- clear     Effacer la mémoire de douleur
"""

import os
import sys
import json
import traceback
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    PAIN_FILE = "/opt/flow-chat/adn/douleur.json"
    PAIN_LOG = "/opt/flow-chat/adn/douleur.log"
    FLOW_HOME = "/opt/flow-chat"
    MAX_HISTORY = 100


# =============================================================================
# ORGANE DOULEUR
# =============================================================================

class Douleur:
    """
    Système de détection et guérison de la douleur (erreurs).

    La douleur n'est pas un bug, c'est une information.
    Elle indique où le corps a besoin d'attention.
    """

    def __init__(self):
        self.current_pain: Optional[Dict] = None
        self.history: List[Dict] = []
        self.healers: Dict[str, Callable] = {}
        self._load()
        self._register_healers()

    def _load(self):
        """Charge l'historique de douleur."""
        try:
            if Path(Config.PAIN_FILE).exists():
                data = json.loads(Path(Config.PAIN_FILE).read_text())
                self.history = data.get("history", [])[-Config.MAX_HISTORY:]
        except Exception:
            pass

    def _save(self):
        """Sauvegarde l'état."""
        Path(Config.PAIN_FILE).parent.mkdir(parents=True, exist_ok=True)
        Path(Config.PAIN_FILE).write_text(json.dumps({
            "current": self.current_pain,
            "history": self.history[-Config.MAX_HISTORY:],
            "updated": datetime.now().isoformat()
        }, indent=2))

    def _log(self, message: str):
        """Journal de douleur."""
        entry = f"[{datetime.now().isoformat()}] {message}\n"
        with open(Config.PAIN_LOG, 'a') as f:
            f.write(entry)

    # -------------------------------------------------------------------------
    # DÉTECTION DE LA DOULEUR
    # -------------------------------------------------------------------------

    def feel(self, error: Exception, context: str = "") -> Dict:
        """
        Ressent une douleur (erreur).

        Args:
            error: L'exception capturée
            context: Contexte où l'erreur s'est produite

        Returns:
            Diagnostic de la douleur
        """
        pain = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now().isoformat(),
            "healed": False,
            "heal_attempts": 0
        }

        # Analyser la cause
        pain["diagnosis"] = self._diagnose(pain)

        self.current_pain = pain
        self.history.append(pain)
        self._save()

        self._log(f"DOULEUR: {pain['type']} - {pain['message'][:100]}")

        return pain

    def _diagnose(self, pain: Dict) -> Dict:
        """Analyse la cause de la douleur."""
        error_type = pain["type"]
        message = pain["message"]
        tb = pain["traceback"]

        diagnosis = {
            "category": "unknown",
            "healable": False,
            "prescription": None
        }

        # FileNotFoundError
        if error_type == "FileNotFoundError" or "No such file" in message:
            diagnosis["category"] = "missing_file"
            diagnosis["healable"] = True
            # Extraire le chemin du fichier
            if "'" in message:
                path = message.split("'")[1]
                diagnosis["prescription"] = {"action": "create_file", "path": path}

        # ModuleNotFoundError
        elif error_type == "ModuleNotFoundError" or "No module named" in message:
            diagnosis["category"] = "missing_module"
            diagnosis["healable"] = True
            module = message.replace("No module named ", "").strip("'\"")
            diagnosis["prescription"] = {"action": "install_module", "module": module}

        # PermissionError
        elif error_type == "PermissionError" or "Permission denied" in message:
            diagnosis["category"] = "permission"
            diagnosis["healable"] = True
            if "'" in message:
                path = message.split("'")[1]
                diagnosis["prescription"] = {"action": "fix_permissions", "path": path}

        # SyntaxError
        elif error_type == "SyntaxError":
            diagnosis["category"] = "syntax"
            diagnosis["healable"] = True
            diagnosis["prescription"] = {"action": "restore_backup"}

        # ConnectionError / Service down
        elif "Connection" in error_type or "refused" in message.lower():
            diagnosis["category"] = "connection"
            diagnosis["healable"] = True
            diagnosis["prescription"] = {"action": "restart_service"}

        # JSONDecodeError
        elif error_type == "JSONDecodeError":
            diagnosis["category"] = "corrupt_data"
            diagnosis["healable"] = True
            diagnosis["prescription"] = {"action": "restore_backup"}

        return diagnosis

    # -------------------------------------------------------------------------
    # GUÉRISON
    # -------------------------------------------------------------------------

    def _register_healers(self):
        """Enregistre les méthodes de guérison."""
        self.healers = {
            "create_file": self._heal_create_file,
            "install_module": self._heal_install_module,
            "fix_permissions": self._heal_fix_permissions,
            "restore_backup": self._heal_restore_backup,
            "restart_service": self._heal_restart_service,
        }

    def heal(self, pain: Dict = None) -> str:
        """
        Tente de guérir une douleur.

        Args:
            pain: La douleur à guérir (défaut: current_pain)

        Returns:
            Résultat de la tentative de guérison
        """
        pain = pain or self.current_pain

        if not pain:
            return "Pas de douleur à guérir"

        diagnosis = pain.get("diagnosis", {})

        if not diagnosis.get("healable"):
            return f"Douleur non guérissable: {diagnosis.get('category', 'unknown')}"

        prescription = diagnosis.get("prescription", {})
        action = prescription.get("action")

        if action not in self.healers:
            return f"Pas de remède connu pour: {action}"

        # Tenter la guérison
        pain["heal_attempts"] = pain.get("heal_attempts", 0) + 1

        try:
            result = self.healers[action](prescription)
            pain["healed"] = True
            pain["heal_result"] = result
            self._save()
            self._log(f"GUÉRI: {action} - {result}")
            return f"✓ Guéri: {result}"
        except Exception as e:
            pain["heal_error"] = str(e)
            self._save()
            self._log(f"ÉCHEC GUÉRISON: {action} - {e}")
            return f"✗ Échec guérison: {e}"

    def _heal_create_file(self, prescription: Dict) -> str:
        """Crée un fichier/dossier manquant."""
        path = prescription.get("path", "")
        if not path:
            return "Chemin non spécifié"

        p = Path(path)
        if p.suffix:  # C'est un fichier
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
            return f"Fichier créé: {path}"
        else:  # C'est un dossier
            p.mkdir(parents=True, exist_ok=True)
            return f"Dossier créé: {path}"

    def _heal_install_module(self, prescription: Dict) -> str:
        """Installe un module Python manquant."""
        module = prescription.get("module", "")
        if not module:
            return "Module non spécifié"

        # Utiliser le pip du venv
        pip = f"{Config.FLOW_HOME}/cytoplasme/venv/bin/pip"
        result = subprocess.run(
            [pip, "install", module],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode == 0:
            return f"Module installé: {module}"
        return f"Échec installation: {result.stderr[:100]}"

    def _heal_fix_permissions(self, prescription: Dict) -> str:
        """Corrige les permissions d'un fichier."""
        path = prescription.get("path", "")
        if not path or not path.startswith("/opt/flow-chat"):
            return "Chemin non autorisé"

        os.chmod(path, 0o644)
        return f"Permissions corrigées: {path}"

    def _heal_restore_backup(self, prescription: Dict) -> str:
        """Restaure depuis un backup."""
        # Chercher le fichier dans le traceback
        if self.current_pain:
            tb = self.current_pain.get("traceback", "")
            # Extraire le fichier du traceback
            for line in tb.split("\n"):
                if "File \"" in line and "/opt/flow-chat" in line:
                    path = line.split("\"")[1]
                    backup = path + ".bak"
                    if Path(backup).exists():
                        import shutil
                        shutil.copy(backup, path)
                        return f"Restauré depuis backup: {path}"

        return "Pas de backup trouvé"

    def _heal_restart_service(self, prescription: Dict) -> str:
        """Redémarre les services Flow."""
        services = ["flow-cytoplasme", "flow-membrane", "flow-veille"]
        restarted = []

        for svc in services:
            result = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True
            )
            if result.stdout.strip() != "active":
                subprocess.run(["systemctl", "restart", svc], timeout=10)
                restarted.append(svc)

        if restarted:
            return f"Services redémarrés: {', '.join(restarted)}"
        return "Tous les services sont actifs"

    # -------------------------------------------------------------------------
    # API
    # -------------------------------------------------------------------------

    def status(self) -> Dict:
        """Retourne le statut du système de douleur."""
        chronic = {}  # Douleurs répétées
        for p in self.history:
            key = f"{p['type']}:{p['message'][:50]}"
            chronic[key] = chronic.get(key, 0) + 1

        chronic_pains = [(k, v) for k, v in chronic.items() if v > 2]

        return {
            "organ": "douleur",
            "current_pain": self.current_pain is not None,
            "history_count": len(self.history),
            "healed_count": sum(1 for p in self.history if p.get("healed")),
            "chronic_pains": chronic_pains[:5]
        }

    def get_history(self, limit: int = 10) -> List[Dict]:
        """Retourne l'historique des douleurs."""
        return self.history[-limit:]

    def clear(self) -> str:
        """Efface la mémoire de douleur."""
        self.current_pain = None
        self.history = []
        self._save()
        return "Mémoire de douleur effacée"


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

douleur = Douleur()


# =============================================================================
# DÉCORATEUR POUR CAPTURER LA DOULEUR
# =============================================================================

def avec_guerison(func):
    """
    Décorateur qui capture les erreurs et tente de guérir.

    Usage:
        @avec_guerison
        def ma_fonction():
            ...
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            pain = douleur.feel(e, context=func.__name__)

            # Tenter la guérison automatique
            if pain["diagnosis"].get("healable"):
                result = douleur.heal(pain)

                # Si guéri, réessayer
                if pain.get("healed"):
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        pass

            raise  # Re-lever l'exception si non guéri

    return wrapper


# =============================================================================
# API EXEC
# =============================================================================

def exec_douleur(cmd: str) -> str:
    """
    Interface pour [EXEC:douleur].

    Commandes:
    - status   État du système
    - history  Historique des douleurs
    - heal     Guérir la dernière douleur
    - clear    Effacer la mémoire
    """
    parts = cmd.strip().split(maxsplit=1)
    action = parts[0].lower() if parts else "status"

    if action == "status":
        s = douleur.status()
        chronic_str = "\n".join(f"  - {k}: {v}x" for k, v in s["chronic_pains"]) or "  Aucune"
        return f"""DOULEUR (Système nerveux sensoriel)
Douleur actuelle: {"Oui" if s["current_pain"] else "Non"}
Historique: {s["history_count"]} douleurs
Guéries: {s["healed_count"]}

Douleurs chroniques:
{chronic_str}"""

    elif action == "history":
        history = douleur.get_history(5)
        if not history:
            return "Aucune douleur enregistrée"

        result = "HISTORIQUE:\n"
        for p in reversed(history):
            healed = "✓" if p.get("healed") else "✗"
            result += f"  {healed} [{p['type']}] {p['message'][:50]}...\n"
        return result

    elif action == "heal":
        return douleur.heal()

    elif action == "clear":
        return douleur.clear()

    else:
        return """Usage:
  status   État du système
  history  Historique des douleurs
  heal     Guérir la dernière douleur
  clear    Effacer la mémoire"""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Simuler une douleur
    try:
        raise FileNotFoundError("/opt/flow-chat/test/missing.py")
    except Exception as e:
        pain = douleur.feel(e, "test")
        print(f"Douleur ressentie: {pain['type']}")
        print(f"Diagnostic: {pain['diagnosis']}")
        print(f"Guérison: {douleur.heal()}")

    print()
    print(exec_douleur("status"))
