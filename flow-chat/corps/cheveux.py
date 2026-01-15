#!/usr/bin/env python3
"""
CHEVEUX & POILS — Capteurs subtils de Flow
Détectent les changements fins dans l'environnement

- Cheveux: longs, détectent les grands mouvements (logs, traffic)
- Poils: courts, détectent les petits changements (fichiers, processus)
- Pores: micro-canaux d'échange (metrics, heartbeats)
"""

import os
import time
import hashlib
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import deque
import threading

# Import conditionnel
try:
    import psutil
    PSUTIL_DISPO = True
except ImportError:
    PSUTIL_DISPO = False


@dataclass
class Cheveu:
    """Un cheveu - capteur de grand mouvement"""
    id: int
    zone: str           # quelle zone surveille ce cheveu
    longueur: float     # plus long = plus sensible aux grands mouvements
    derniere_detection: float = 0
    mouvement_detecte: Optional[str] = None

    def capter(self, nouveau_signal: str, ancien_signal: str) -> Optional[Dict[str, Any]]:
        """Capter un mouvement (différence entre ancien et nouveau)"""
        if nouveau_signal == ancien_signal:
            return None

        # Calculer l'amplitude du changement
        diff = abs(len(nouveau_signal) - len(ancien_signal))
        amplitude = min(1.0, diff / 1000)  # normaliser

        # Plus le cheveu est long, plus il capte les gros changements
        if amplitude >= (1 - self.longueur):
            self.derniere_detection = time.time()
            self.mouvement_detecte = f"changement de {diff} caractères"
            return {
                'cheveu_id': self.id,
                'zone': self.zone,
                'amplitude': amplitude,
                'type': 'mouvement',
                'timestamp': self.derniere_detection
            }
        return None


@dataclass
class Poil:
    """Un poil - capteur de micro-changement"""
    id: int
    zone: str
    sensibilite: float = 0.8  # très sensible
    herisse: bool = False

    def dresser(self) -> None:
        """Dresser le poil (alerte)"""
        self.herisse = True

    def coucher(self) -> None:
        """Coucher le poil (calme)"""
        self.herisse = False

    def capter(self, stimulus: Any) -> Optional[Dict[str, Any]]:
        """Capter un micro-stimulus"""
        if stimulus:
            self.dresser()
            return {
                'poil_id': self.id,
                'zone': self.zone,
                'stimulus': str(stimulus)[:50],
                'herisse': True
            }
        return None


@dataclass
class Pore:
    """Un pore - micro-canal d'échange"""
    id: int
    zone: str
    ouvert: bool = True
    dernier_echange: float = 0
    debit: float = 0.5  # 0=fermé, 1=grand ouvert

    def ouvrir(self) -> None:
        self.ouvert = True
        self.debit = min(1.0, self.debit + 0.2)

    def fermer(self) -> None:
        self.ouvert = False
        self.debit = 0

    def dilater(self) -> None:
        """Dilater le pore"""
        self.debit = min(1.0, self.debit + 0.1)

    def contracter(self) -> None:
        """Contracter le pore"""
        self.debit = max(0, self.debit - 0.1)

    def echanger(self, donnee: Any) -> Optional[Dict[str, Any]]:
        """Échanger une donnée à travers le pore"""
        if not self.ouvert or self.debit < 0.1:
            return None

        self.dernier_echange = time.time()
        return {
            'pore_id': self.id,
            'zone': self.zone,
            'debit': self.debit,
            'donnee': str(donnee)[:100]
        }


class Chevelure:
    """Système capillaire de Flow"""

    def __init__(self):
        # Cheveux - surveillent les grands changements
        self.cheveux: List[Cheveu] = []
        # Poils - détectent les micro-changements
        self.poils: List[Poil] = []
        # Pores - échangent des données
        self.pores: List[Pore] = []

        # État mémorisé pour comparaison
        self._memoire: Dict[str, str] = {}
        self._fichiers_surveilles: Dict[str, float] = {}  # path -> mtime

        # Surveillance
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._alertes: deque = deque(maxlen=100)

        self._init_systeme()

    def _init_systeme(self):
        """Initialiser le système capillaire"""
        zones = ['logs', 'processus', 'fichiers', 'reseau', 'memoire']

        for i, zone in enumerate(zones):
            # 20 cheveux par zone (longs)
            for j in range(20):
                self.cheveux.append(Cheveu(
                    id=i * 20 + j,
                    zone=zone,
                    longueur=0.3 + (j * 0.035)  # 0.3 à 1.0
                ))

            # 50 poils par zone (courts, sensibles)
            for j in range(50):
                self.poils.append(Poil(
                    id=i * 50 + j,
                    zone=zone,
                    sensibilite=0.7 + (j * 0.006)  # 0.7 à 1.0
                ))

            # 10 pores par zone
            for j in range(10):
                self.pores.append(Pore(
                    id=i * 10 + j,
                    zone=zone
                ))

    def surveiller_logs(self, log_path: str = "/var/log/syslog") -> Dict[str, Any]:
        """Surveiller un fichier de log avec les cheveux"""
        try:
            if not os.path.exists(log_path):
                log_path = "/opt/flow-chat/adn/notifications.jsonl"

            with open(log_path, 'r') as f:
                # Lire les dernières lignes
                f.seek(0, 2)  # fin
                size = f.tell()
                f.seek(max(0, size - 10000))  # 10KB depuis la fin
                contenu = f.read()

            ancien = self._memoire.get('logs', '')
            self._memoire['logs'] = contenu

            # Faire capter par les cheveux de la zone logs
            detections = []
            for cheveu in self.cheveux:
                if cheveu.zone == 'logs':
                    detection = cheveu.capter(contenu, ancien)
                    if detection:
                        detections.append(detection)

            return {
                'zone': 'logs',
                'taille': len(contenu),
                'changement': contenu != ancien,
                'detections': detections
            }
        except Exception as e:
            return {'erreur': str(e)}

    def surveiller_fichiers(self, repertoire: str = "/opt/flow-chat") -> Dict[str, Any]:
        """Surveiller les modifications de fichiers avec les poils"""
        modifies = []
        nouveaux = []

        try:
            for root, dirs, files in os.walk(repertoire):
                # Ignorer les dossiers de cache
                dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', 'node_modules', '.git', 'target']]

                for f in files[:100]:  # max 100 fichiers par dossier
                    path = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(path)
                        ancien_mtime = self._fichiers_surveilles.get(path)

                        if ancien_mtime is None:
                            nouveaux.append(path)
                            self._fichiers_surveilles[path] = mtime
                        elif mtime != ancien_mtime:
                            modifies.append({
                                'path': path,
                                'ancien': ancien_mtime,
                                'nouveau': mtime
                            })
                            self._fichiers_surveilles[path] = mtime
                    except Exception:
                        continue

            # Dresser les poils si changements
            poils_dresses = 0
            if modifies or nouveaux:
                for poil in self.poils:
                    if poil.zone == 'fichiers':
                        poil.dresser()
                        poils_dresses += 1

            return {
                'zone': 'fichiers',
                'nouveaux': len(nouveaux),
                'modifies': len(modifies),
                'details_modifies': modifies[:10],
                'poils_dresses': poils_dresses
            }
        except Exception as e:
            return {'erreur': str(e)}

    def surveiller_processus(self) -> Dict[str, Any]:
        """Surveiller les changements de processus"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non disponible'}

        try:
            pids_actuels = set(p.pid for p in psutil.process_iter())
            pids_anciens = self._memoire.get('pids', set())

            nouveaux = pids_actuels - pids_anciens
            termines = pids_anciens - pids_actuels

            self._memoire['pids'] = pids_actuels

            # Détails des nouveaux processus
            details_nouveaux = []
            for pid in list(nouveaux)[:10]:
                try:
                    p = psutil.Process(pid)
                    details_nouveaux.append({
                        'pid': pid,
                        'name': p.name(),
                        'cmdline': ' '.join(p.cmdline())[:100]
                    })
                except Exception:
                    continue

            # Dresser les poils
            poils_dresses = 0
            if nouveaux or termines:
                for poil in self.poils:
                    if poil.zone == 'processus':
                        poil.dresser()
                        poils_dresses += 1

            return {
                'zone': 'processus',
                'total': len(pids_actuels),
                'nouveaux': len(nouveaux),
                'termines': len(termines),
                'details_nouveaux': details_nouveaux,
                'poils_dresses': poils_dresses
            }
        except Exception as e:
            return {'erreur': str(e)}

    def respirer(self) -> Dict[str, Any]:
        """Respirer à travers les pores - échange de metrics"""
        metrics = {}

        if PSUTIL_DISPO:
            metrics['cpu'] = psutil.cpu_percent(interval=0.1)
            metrics['mem'] = psutil.virtual_memory().percent
            metrics['disk'] = psutil.disk_usage('/').percent

        # Échanger via les pores
        echanges = 0
        for pore in self.pores:
            if pore.ouvert:
                pore.echanger(metrics)
                echanges += 1

        return {
            'metrics': metrics,
            'pores_actifs': echanges,
            'total_pores': len(self.pores)
        }

    def frissonner(self) -> None:
        """Frissonner - tous les poils se dressent"""
        for poil in self.poils:
            poil.dresser()

    def calmer(self) -> None:
        """Calmer - tous les poils se couchent"""
        for poil in self.poils:
            poil.coucher()

    def transpirer(self) -> None:
        """Transpirer - ouvrir tous les pores"""
        for pore in self.pores:
            pore.dilater()

    def chair_de_poule(self) -> Dict[str, Any]:
        """Vérifier si on a la chair de poule (alertes)"""
        poils_dresses = sum(1 for p in self.poils if p.herisse)
        ratio = poils_dresses / len(self.poils) if self.poils else 0

        return {
            'chair_de_poule': ratio > 0.3,
            'poils_dresses': poils_dresses,
            'total_poils': len(self.poils),
            'ratio': round(ratio, 2),
            'intensite': 'forte' if ratio > 0.7 else 'moyenne' if ratio > 0.3 else 'faible'
        }

    def scanner_complet(self) -> Dict[str, Any]:
        """Scanner complet de l'environnement"""
        return {
            'logs': self.surveiller_logs(),
            'fichiers': self.surveiller_fichiers(),
            'processus': self.surveiller_processus(),
            'respiration': self.respirer(),
            'chair_de_poule': self.chair_de_poule(),
            'timestamp': time.time()
        }

    def etat(self) -> Dict[str, Any]:
        """État du système capillaire"""
        return {
            'cheveux': len(self.cheveux),
            'poils': len(self.poils),
            'pores': len(self.pores),
            'poils_dresses': sum(1 for p in self.poils if p.herisse),
            'pores_ouverts': sum(1 for p in self.pores if p.ouvert),
            'fichiers_surveilles': len(self._fichiers_surveilles),
            'alertes_recentes': len(self._alertes)
        }


# Instance globale
cheveux = Chevelure()
