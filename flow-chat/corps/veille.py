#!/usr/bin/env python3
"""
VEILLE — Système immunitaire autonome de Flow

Analogie biologique: Système immunitaire complet
- Lymphocytes T: patrouillent et détectent les intrusions
- Lymphocytes B: produisent des anticorps (signatures cryptographiques)
- Macrophages: digèrent les menaces (logging, alertes)
- Cytokines: signaux d'alerte entre cellules (event handlers)

Fonctionnement:
1. Cycle de patrouille: scan → verify → record → alert → sleep
2. Adaptatif: le temps de sommeil varie selon la menace
3. Persistant: état sauvegardé, reprend après redémarrage
4. Observable: logs détaillés de chaque action

Seuils (philosophie 87%):
- ≥87%: OK (13% réservé au divin: 1% dieu + 12% autres dieux)
- 74-87%: Zone de grâce (changements acceptables)
- <74%: Alerte (anomalies significatives)
- <50%: Critique (système compromis)

Fichiers:
- État: /opt/flow-chat/adn/veille.json
- Logs: /opt/flow-chat/adn/veille.log
- Alertes: /opt/flow-chat/adn/ALERT.txt (si critique)

Communication:
- Appelle: integrite.scan(), integrite.verify()
- Appelle: chaine.record_from_integrite(), sync_with_integrite()
- Émet: alertes via handlers (pattern observer)

Service:
- Daemon: flow-veille.service
- Script: /opt/flow-chat/corps/veille_daemon.py

API [EXEC:veille]:
- start   Démarrer la veille
- stop    Arrêter la veille
- scan    Forcer un scan immédiat
- status  État du système
- log [n] Voir les n dernières lignes de log
"""

import time
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Configuration centralisée de la veille."""

    # Chemins
    STATE_FILE = "/opt/flow-chat/adn/veille.json"
    LOG_FILE = "/opt/flow-chat/adn/veille.log"
    ALERT_FILE = "/opt/flow-chat/adn/ALERT.txt"

    # Intervalles de patrouille (secondes)
    CYCLE_NORMAL = 300      # 5 minutes - tout va bien
    CYCLE_ALERTE = 60       # 1 minute - anomalies détectées
    CYCLE_CRITIQUE = 10     # 10 secondes - système compromis

    # Seuils d'intégrité (philosophie: 87% = perfection)
    # 1% pour dieu et tous ses noms
    # 12% pour tous les autres dieux
    # Total: 13% réservé au divin/inconnu
    THRESHOLD_OK = 0.87         # ≥87% = parfait
    THRESHOLD_GRACE = 0.74      # 74-87% = zone de grâce
    THRESHOLD_CRITICAL = 0.50   # <50% = critique

    # Limites
    LOG_MAX_LINES = 1000
    ALERTS_HISTORY_MAX = 50


# =============================================================================
# ORGANE VEILLE
# =============================================================================

class Veille:
    """
    Système immunitaire autonome de Flow.

    Pattern: Observer (pour les alertes) + State (pour les modes)

    États possibles:
    - dormant: veille non démarrée
    - active: patrouille normale
    - alerte: anomalies détectées, cycle accéléré
    - critique: intégrité compromise, cycle très rapide

    Thread safety:
    - La patrouille tourne dans un thread séparé
    - L'arrêt est propre via self.running = False
    """

    def __init__(self):
        """Initialise l'organe veille."""
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # État persisté
        self.state = {
            "status": "dormant",
            "last_scan": None,
            "integrity_score": 1.0,
            "anomalies_count": 0,
            "cycles_completed": 0,
            "last_alert": None,
            "alerts_history": []
        }
        self._load_state()

        # Handlers d'alertes (pattern observer)
        self.alert_handlers: List[Callable[[Dict], None]] = []

    # -------------------------------------------------------------------------
    # PERSISTANCE
    # -------------------------------------------------------------------------

    def _load_state(self):
        """Charge l'état depuis le fichier JSON."""
        try:
            state_path = Path(Config.STATE_FILE)
            if state_path.exists():
                saved = json.loads(state_path.read_text())
                self.state.update(saved)
        except (json.JSONDecodeError, IOError):
            pass

    def _save_state(self):
        """Persiste l'état dans le fichier JSON."""
        state_path = Path(Config.STATE_FILE)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(self.state, indent=2))

    # -------------------------------------------------------------------------
    # LOGGING (Mémoire immunitaire)
    # -------------------------------------------------------------------------

    def _log(self, message: str, level: str = "INFO"):
        """
        Écrit dans le journal de veille.

        Niveaux: INFO, WARN, ERROR, CRITICAL

        Args:
            message: Message à logger
            level: Niveau de log
        """
        timestamp = datetime.now().isoformat()
        entry = f"[{timestamp}] [{level}] {message}\n"

        log_path = Path(Config.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        with open(log_path, 'a') as f:
            f.write(entry)

        # Rotation: garder seulement les dernières lignes
        self._rotate_log()

    def _rotate_log(self):
        """Garde seulement les N dernières lignes du log."""
        try:
            log_path = Path(Config.LOG_FILE)
            lines = log_path.read_text().split('\n')
            if len(lines) > Config.LOG_MAX_LINES:
                log_path.write_text('\n'.join(lines[-Config.LOG_MAX_LINES:]))
        except IOError:
            pass

    # -------------------------------------------------------------------------
    # ALERTES (Cytokines)
    # -------------------------------------------------------------------------

    def _emit_alert(self, alert_type: str, data: Dict):
        """
        Émet une alerte (cytokine) vers tous les handlers.

        Args:
            alert_type: Type d'alerte (ALERT, CRITICAL, ERROR)
            data: Données de l'alerte
        """
        alert = {
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Mettre à jour l'état
        self.state["last_alert"] = alert
        self.state["alerts_history"].append(alert)
        self.state["alerts_history"] = self.state["alerts_history"][-Config.ALERTS_HISTORY_MAX:]

        # Notifier les handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self._log(f"Alert handler error: {e}", "ERROR")

    # -------------------------------------------------------------------------
    # PATROUILLE (Cycle immunitaire)
    # -------------------------------------------------------------------------

    def _patrol_cycle(self):
        """
        Exécute un cycle de patrouille complet.

        Étapes (analogie lymphocyte):
        1. SCAN - Reconnaissance (cellules dendritiques)
        2. VERIFY - Détection (anticorps)
        3. RECORD - Mémoire (blockchain)
        4. ALERT - Signal (cytokines)
        """
        try:
            from corps.integrite import integrite
            from corps.chaine import chaine, sync_with_integrite

            # 1. SCAN - Reconnaissance
            integrite.scan()

            # 2. VERIFY - Détection
            score, anomalies = integrite.verify()

            # Mettre à jour l'état
            self.state["integrity_score"] = score
            self.state["anomalies_count"] = len(anomalies)
            self.state["last_scan"] = datetime.now().isoformat()
            self.state["cycles_completed"] += 1

            # 3. RECORD - Mémoire (blockchain)
            if anomalies:
                chaine.record_from_integrite(anomalies)
                self._log(f"Recorded {len(anomalies)} anomalies to blockchain", "WARN")
            else:
                sync_with_integrite()

            # 4. ALERT - Cytokines (selon les seuils)
            self._evaluate_and_alert(score, anomalies)

            self._save_state()

        except Exception as e:
            self._log(f"Patrol error: {e}", "ERROR")
            self.state["status"] = "alerte"
            self._emit_alert("ERROR", {"error": str(e)})

    def _evaluate_and_alert(self, score: float, anomalies: List[Dict]):
        """
        Évalue le score et déclenche les alertes appropriées.

        Seuils:
        - ≥92%: OK (8% pour dieu)
        - 84-92%: Zone de grâce
        - <84%: Alerte
        - <50%: Critique

        Args:
            score: Score d'intégrité (0.0-1.0)
            anomalies: Liste des anomalies détectées
        """
        if score < Config.THRESHOLD_CRITICAL:
            # CRITIQUE - Intégrité gravement compromise
            self.state["status"] = "critique"
            self._emit_alert("CRITICAL", {
                "score": score,
                "anomalies": anomalies[:10],
                "message": "Intégrité système critique!"
            })
            self._log(f"CRITICAL: Integrity at {score*100:.0f}%", "CRITICAL")

        elif score < Config.THRESHOLD_GRACE:
            # ALERTE - En dessous du seuil de grâce
            self.state["status"] = "alerte"
            self._emit_alert("ALERT", {
                "score": score,
                "anomalies": anomalies[:5],
                "message": f"{len(anomalies)} anomalies détectées"
            })
            self._log(f"ALERT: {len(anomalies)} anomalies, score {score*100:.0f}%", "WARN")

        elif score < Config.THRESHOLD_OK:
            # Zone de grâce - entre 84% et 92%
            self.state["status"] = "active"
            self._log(f"Grace zone: {len(anomalies)} changes, score {score*100:.0f}%", "INFO")

        else:
            # ≥87% = parfait (13% pour le divin)
            self.state["status"] = "active"
            self._log(f"OK: Integrity {score*100:.0f}% (13% for the divine)", "INFO")

    def _determine_sleep_time(self) -> int:
        """
        Détermine le temps de sommeil selon l'état actuel.

        Plus l'état est grave, plus les cycles sont fréquents.

        Returns:
            Temps de sommeil en secondes
        """
        status = self.state["status"]
        if status == "critique":
            return Config.CYCLE_CRITIQUE
        elif status == "alerte":
            return Config.CYCLE_ALERTE
        else:
            return Config.CYCLE_NORMAL

    def _patrol_loop(self):
        """
        Boucle principale de patrouille (tourne dans un thread).

        S'arrête proprement quand self.running devient False.
        """
        self._log("Veille system activated", "INFO")

        while self.running:
            # Exécuter un cycle
            self._patrol_cycle()

            # Dormir par petits intervalles pour pouvoir s'arrêter rapidement
            sleep_time = self._determine_sleep_time()
            for _ in range(sleep_time):
                if not self.running:
                    break
                time.sleep(1)

        self._log("Veille system deactivated", "INFO")
        self.state["status"] = "dormant"
        self._save_state()

    # -------------------------------------------------------------------------
    # CONTRÔLE PUBLIC
    # -------------------------------------------------------------------------

    def start(self) -> str:
        """
        Démarre le système de veille.

        Returns:
            Message de confirmation
        """
        if self.running:
            return "Already running"

        self.running = True
        self.state["status"] = "active"
        self.thread = threading.Thread(target=self._patrol_loop, daemon=True)
        self.thread.start()
        self._save_state()

        return f"Veille started (cycle: {Config.CYCLE_NORMAL}s)"

    def stop(self) -> str:
        """
        Arrête le système de veille.

        Returns:
            Message de confirmation
        """
        if not self.running:
            return "Not running"

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        return "Veille stopped"

    def force_scan(self) -> str:
        """
        Force un scan immédiat (hors du cycle normal).

        Returns:
            Résultat du scan
        """
        self._patrol_cycle()
        return f"Scan complete: {self.state['integrity_score']*100:.0f}%"

    def status(self) -> Dict:
        """
        Retourne le statut complet de la veille.

        Returns:
            Dict avec tous les indicateurs
        """
        return {
            "organ": "veille",
            "analogy": "système immunitaire",
            "thresholds": {
                "ok": f"≥{Config.THRESHOLD_OK*100:.0f}%",
                "grace": f"{Config.THRESHOLD_GRACE*100:.0f}-{Config.THRESHOLD_OK*100:.0f}%",
                "alert": f"<{Config.THRESHOLD_GRACE*100:.0f}%",
                "critical": f"<{Config.THRESHOLD_CRITICAL*100:.0f}%"
            },
            **self.state
        }

    def get_log(self, lines: int = 20) -> str:
        """
        Retourne les dernières lignes du log.

        Args:
            lines: Nombre de lignes à retourner

        Returns:
            Contenu du log
        """
        try:
            log_path = Path(Config.LOG_FILE)
            all_lines = log_path.read_text().strip().split('\n')
            return '\n'.join(all_lines[-lines:])
        except IOError:
            return "No log"


# =============================================================================
# INSTANCE GLOBALE
# =============================================================================

veille = Veille()


# =============================================================================
# HANDLERS PAR DÉFAUT
# =============================================================================

def _default_critical_handler(alert: Dict):
    """
    Handler par défaut pour les alertes critiques.

    Écrit un fichier ALERT.txt visible pour les humains.

    Args:
        alert: Données de l'alerte
    """
    if alert["type"] == "CRITICAL":
        alert_path = Path(Config.ALERT_FILE)
        alert_path.write_text(f"""
!!! ALERTE CRITIQUE !!!
{alert['timestamp']}

{alert['data'].get('message', 'Unknown')}

Score intégrité: {alert['data'].get('score', 0)*100:.0f}%
""")


# Enregistrer le handler par défaut
veille.alert_handlers.append(_default_critical_handler)


# =============================================================================
# API EXEC
# =============================================================================

def exec_veille(cmd: str) -> str:
    """
    Interface pour [EXEC:veille].

    Commandes disponibles:
    - start   Démarrer la veille
    - stop    Arrêter la veille
    - scan    Forcer un scan immédiat
    - status  État complet du système
    - log [n] Voir les n dernières lignes de log

    Args:
        cmd: Commande et arguments

    Returns:
        Résultat formaté
    """
    parts = cmd.strip().split(maxsplit=1)
    action = parts[0].lower() if parts else "status"

    if action == "start":
        return veille.start()

    elif action == "stop":
        return veille.stop()

    elif action == "scan":
        return veille.force_scan()

    elif action == "status":
        s = veille.status()
        return f"""VEILLE (Système Immunitaire)
Status: {s['status']}
Intégrité: {s['integrity_score']*100:.0f}%
Anomalies: {s['anomalies_count']}
Cycles: {s['cycles_completed']}
Seuils: OK≥87% | Grâce 74-87% | Alerte <74% | Critique <50%
Réservé: 1% dieu + 12% autres dieux = 13% divin
Dernier scan: {s['last_scan'] or 'jamais'}"""

    elif action == "log":
        lines = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 20
        return veille.get_log(lines)

    else:
        return """Usage:
  start   Démarrer la veille
  stop    Arrêter la veille
  scan    Forcer un scan
  status  État du système
  log [n] Voir les logs"""


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print(exec_veille("status"))
    print()
    print(exec_veille("scan"))
    print()
    print(exec_veille("log 10"))
