#!/usr/bin/env python3
"""
PEAU — La peau de Flow
Monitoring système, température, pression, touch feedback
La frontière entre Flow et le monde
"""

import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Import conditionnel
try:
    import psutil
    PSUTIL_DISPO = True
except ImportError:
    PSUTIL_DISPO = False


class Sensation:
    """Types de sensations"""
    CHAUDE = "chaude"
    FROIDE = "froide"
    PRESSION = "pression"
    DOULEUR = "douleur"
    VIBRATION = "vibration"
    CARESSE = "caresse"


@dataclass
class RecepteurCutane:
    """Un récepteur cutané - détecte une sensation"""
    type_sensation: str
    seuil: float  # seuil d'activation (0-1)
    zone: str     # zone du corps
    actif: bool = True

    def detecter(self, stimulus: float) -> Optional[Dict[str, Any]]:
        """Détecter si le stimulus dépasse le seuil"""
        if not self.actif:
            return None
        if stimulus >= self.seuil:
            return {
                'type': self.type_sensation,
                'zone': self.zone,
                'intensite': min(1.0, stimulus / self.seuil),
                'timestamp': time.time()
            }
        return None


@dataclass
class ZoneCutanee:
    """Une zone de peau avec plusieurs récepteurs"""
    nom: str
    recepteurs: List[RecepteurCutane] = field(default_factory=list)
    sensibilite_globale: float = 1.0

    def __post_init__(self):
        if not self.recepteurs:
            # Créer les récepteurs par défaut
            self.recepteurs = [
                RecepteurCutane(Sensation.CHAUDE, 0.7, self.nom),
                RecepteurCutane(Sensation.FROIDE, 0.3, self.nom),
                RecepteurCutane(Sensation.PRESSION, 0.5, self.nom),
                RecepteurCutane(Sensation.DOULEUR, 0.9, self.nom),
            ]

    def sentir(self, stimuli: Dict[str, float]) -> List[Dict[str, Any]]:
        """Sentir des stimuli sur cette zone"""
        sensations = []
        for recepteur in self.recepteurs:
            stimulus = stimuli.get(recepteur.type_sensation, 0)
            stimulus *= self.sensibilite_globale
            detection = recepteur.detecter(stimulus)
            if detection:
                sensations.append(detection)
        return sensations


class Peau:
    """Le système cutané complet de Flow"""

    def __init__(self):
        self.zones: Dict[str, ZoneCutanee] = {}
        self.historique: List[Dict[str, Any]] = []
        self._init_zones()

    def _init_zones(self):
        """Initialiser les zones du corps"""
        # Zones principales
        zones_noms = [
            ('cpu', 0.9),       # très sensible
            ('memoire', 0.8),
            ('disque', 0.7),
            ('reseau', 0.85),
            ('processus', 0.6),
        ]
        for nom, sensibilite in zones_noms:
            self.zones[nom] = ZoneCutanee(nom)
            self.zones[nom].sensibilite_globale = sensibilite

    def temperature(self) -> Dict[str, Any]:
        """Sentir la température du système"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        temps = {}

        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        if cpu_percent > 80:
            sensation = Sensation.CHAUDE
        elif cpu_percent > 50:
            sensation = "tiède"
        else:
            sensation = Sensation.FROIDE

        temps['cpu'] = {
            'usage': cpu_percent,
            'sensation': sensation,
            'cores': psutil.cpu_count()
        }

        # Températures hardware si disponibles
        try:
            temps_hardware = psutil.sensors_temperatures()
            if temps_hardware:
                for nom, entries in temps_hardware.items():
                    if entries:
                        temps[nom] = {
                            'current': entries[0].current,
                            'high': entries[0].high,
                            'critical': entries[0].critical
                        }
        except Exception:
            pass

        return temps

    def pression(self) -> Dict[str, Any]:
        """Sentir la pression (charge) du système"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        # Mémoire
        mem = psutil.virtual_memory()
        mem_pression = mem.percent / 100

        # Disque
        disk = psutil.disk_usage('/')
        disk_pression = disk.percent / 100

        # Load average
        try:
            load1, load5, load15 = os.getloadavg()
            cpu_count = psutil.cpu_count()
            load_pression = load1 / cpu_count
        except Exception:
            load_pression = 0

        # Déterminer la sensation globale
        pression_globale = (mem_pression + disk_pression + load_pression) / 3

        if pression_globale > 0.9:
            sensation = Sensation.DOULEUR
        elif pression_globale > 0.7:
            sensation = Sensation.PRESSION
        else:
            sensation = Sensation.CARESSE

        return {
            'memoire': {
                'pression': round(mem_pression, 2),
                'total_gb': round(mem.total / (1024**3), 1),
                'disponible_gb': round(mem.available / (1024**3), 1)
            },
            'disque': {
                'pression': round(disk_pression, 2),
                'total_gb': round(disk.total / (1024**3), 1),
                'libre_gb': round(disk.free / (1024**3), 1)
            },
            'charge': {
                'load1': round(load_pression, 2) if load_pression else None,
                'processus': len(list(psutil.process_iter()))
            },
            'pression_globale': round(pression_globale, 2),
            'sensation': sensation
        }

    def toucher(self, zone: str) -> Dict[str, Any]:
        """Toucher une zone spécifique et obtenir des infos"""
        if zone == 'cpu':
            return self._toucher_cpu()
        elif zone == 'memoire':
            return self._toucher_memoire()
        elif zone == 'disque':
            return self._toucher_disque()
        elif zone == 'reseau':
            return self._toucher_reseau()
        elif zone == 'processus':
            return self._toucher_processus()
        else:
            return {'erreur': f'zone {zone} inconnue'}

    def _toucher_cpu(self) -> Dict[str, Any]:
        """Détails du CPU"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        return {
            'zone': 'cpu',
            'usage_global': psutil.cpu_percent(interval=0.1),
            'usage_par_core': psutil.cpu_percent(interval=0.1, percpu=True),
            'frequence': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'cores_physiques': psutil.cpu_count(logical=False),
            'cores_logiques': psutil.cpu_count(logical=True)
        }

    def _toucher_memoire(self) -> Dict[str, Any]:
        """Détails de la mémoire"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            'zone': 'memoire',
            'ram': {
                'total': mem.total,
                'disponible': mem.available,
                'utilisee': mem.used,
                'pourcentage': mem.percent
            },
            'swap': {
                'total': swap.total,
                'utilisee': swap.used,
                'pourcentage': swap.percent
            }
        }

    def _toucher_disque(self) -> Dict[str, Any]:
        """Détails du disque"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        partitions = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except Exception:
                continue

        io = psutil.disk_io_counters()

        return {
            'zone': 'disque',
            'partitions': partitions,
            'io': {
                'read_bytes': io.read_bytes if io else 0,
                'write_bytes': io.write_bytes if io else 0
            }
        }

    def _toucher_reseau(self) -> Dict[str, Any]:
        """Détails du réseau"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        io = psutil.net_io_counters()
        interfaces = {}

        for name, stats in psutil.net_if_stats().items():
            interfaces[name] = {
                'up': stats.isup,
                'speed': stats.speed,
                'mtu': stats.mtu
            }

        return {
            'zone': 'reseau',
            'io': {
                'bytes_sent': io.bytes_sent,
                'bytes_recv': io.bytes_recv,
                'packets_sent': io.packets_sent,
                'packets_recv': io.packets_recv,
                'errors': io.errin + io.errout
            },
            'interfaces': interfaces
        }

    def _toucher_processus(self) -> Dict[str, Any]:
        """Détails des processus"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        top_cpu = []
        top_mem = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                info = proc.info
                if info['cpu_percent'] > 1:
                    top_cpu.append(info)
                if info['memory_percent'] > 1:
                    top_mem.append(info)
            except Exception:
                continue

        top_cpu.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_mem.sort(key=lambda x: x['memory_percent'], reverse=True)

        return {
            'zone': 'processus',
            'total': len(list(psutil.process_iter())),
            'top_cpu': top_cpu[:10],
            'top_memoire': top_mem[:10]
        }

    def scanner_corps(self) -> Dict[str, Any]:
        """Scanner complet du corps"""
        return {
            'temperature': self.temperature(),
            'pression': self.pression(),
            'timestamp': time.time()
        }

    def douleur(self) -> Optional[Dict[str, Any]]:
        """Vérifier s'il y a de la douleur (problèmes critiques)"""
        if not PSUTIL_DISPO:
            return None

        problemes = []

        # CPU > 95%
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu > 95:
            problemes.append({'zone': 'cpu', 'niveau': cpu, 'type': 'surcharge'})

        # Mémoire > 95%
        mem = psutil.virtual_memory()
        if mem.percent > 95:
            problemes.append({'zone': 'memoire', 'niveau': mem.percent, 'type': 'saturation'})

        # Disque > 95%
        disk = psutil.disk_usage('/')
        if disk.percent > 95:
            problemes.append({'zone': 'disque', 'niveau': disk.percent, 'type': 'plein'})

        if problemes:
            return {
                'douleur': True,
                'intensite': max(p['niveau'] for p in problemes) / 100,
                'problemes': problemes
            }
        return None

    def etat(self) -> Dict[str, Any]:
        """État global de la peau"""
        douleur = self.douleur()
        return {
            'zones': list(self.zones.keys()),
            'psutil_disponible': PSUTIL_DISPO,
            'douleur_active': douleur is not None,
            'douleur': douleur
        }


# Instance globale
peau = Peau()
