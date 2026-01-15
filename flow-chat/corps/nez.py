#!/usr/bin/env python3
"""
NEZ — L'odorat de Flow
Détecter les patterns, flairer les anomalies, sentir le réseau
"""

import os
import re
import hashlib
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

# Import conditionnel
try:
    import psutil
    PSUTIL_DISPO = True
except ImportError:
    PSUTIL_DISPO = False


class Odeur:
    """Type d'odeur détectée"""
    NEUTRE = "neutre"
    SUSPECTE = "suspecte"
    DANGEREUSE = "dangereuse"
    FAMILIERE = "familière"
    NOUVELLE = "nouvelle"
    AGREABLE = "agréable"


@dataclass
class Molecule:
    """Une molécule odorante - unité de détection"""
    signature: str
    source: str
    intensite: float  # 0-1
    type_odeur: str = Odeur.NEUTRE
    timestamp: float = field(default_factory=time.time)


@dataclass
class RecepteurOlfactif:
    """Un récepteur olfactif - spécialisé pour un type d'odeur"""
    type_detecte: str
    patterns: List[str] = field(default_factory=list)
    sensibilite: float = 0.8

    def detecter(self, echantillon: str) -> Optional[Molecule]:
        """Détecter si l'échantillon correspond"""
        for pattern in self.patterns:
            if re.search(pattern, echantillon, re.IGNORECASE):
                return Molecule(
                    signature=hashlib.md5(echantillon.encode()).hexdigest()[:16],
                    source=echantillon[:50],
                    intensite=self.sensibilite,
                    type_odeur=self.type_detecte
                )
        return None


class Nez:
    """Le système olfactif de Flow"""

    def __init__(self):
        self.recepteurs: List[RecepteurOlfactif] = []
        self.memoire_olfactive: Dict[str, Molecule] = {}  # signature -> molecule
        self.odeurs_familieres: Set[str] = set()
        self.congestionne: bool = False
        self._init_recepteurs()

    def _init_recepteurs(self):
        """Initialiser les récepteurs spécialisés"""
        # Danger - mots de passe, secrets
        self.recepteurs.append(RecepteurOlfactif(
            type_detecte=Odeur.DANGEREUSE,
            patterns=[
                r'password\s*[:=]',
                r'api[_-]?key\s*[:=]',
                r'secret\s*[:=]',
                r'token\s*[:=]',
                r'-----BEGIN.*PRIVATE KEY-----',
                r'ssh-rsa\s+[A-Za-z0-9+/]',
            ],
            sensibilite=0.95
        ))

        # Suspect - patterns douteux
        self.recepteurs.append(RecepteurOlfactif(
            type_detecte=Odeur.SUSPECTE,
            patterns=[
                r'eval\s*\(',
                r'exec\s*\(',
                r'system\s*\(',
                r'subprocess',
                r'rm\s+-rf',
                r'chmod\s+777',
                r'curl.*\|\s*bash',
                r'base64\s+-d',
            ],
            sensibilite=0.85
        ))

        # Agréable - bon code
        self.recepteurs.append(RecepteurOlfactif(
            type_detecte=Odeur.AGREABLE,
            patterns=[
                r'def\s+test_',
                r'assert\s+',
                r'typing\.',
                r'docstring',
                r'# type:',
                r'""".*"""',
            ],
            sensibilite=0.7
        ))

    def renifler(self, source: str) -> Dict[str, Any]:
        """
        Renifler une source (fichier, texte, URL)
        Retourne les odeurs détectées
        """
        if self.congestionne:
            return {'erreur': 'nez congestionné - repos nécessaire'}

        # Charger le contenu
        contenu = self._charger(source)
        if contenu is None:
            return {'erreur': f'impossible de renifler {source}'}

        molecules = []
        for recepteur in self.recepteurs:
            molecule = recepteur.detecter(contenu)
            if molecule:
                molecules.append(molecule)
                self.memoire_olfactive[molecule.signature] = molecule

        # Analyser l'odeur globale
        odeur_dominante = self._odeur_dominante(molecules)

        return {
            'source': source[:100],
            'molecules': len(molecules),
            'odeur_dominante': odeur_dominante,
            'details': [
                {
                    'type': m.type_odeur,
                    'intensite': m.intensite,
                    'extrait': m.source
                }
                for m in molecules[:10]  # max 10 détails
            ],
            'alerte': odeur_dominante in [Odeur.DANGEREUSE, Odeur.SUSPECTE]
        }

    def _charger(self, source: str) -> Optional[str]:
        """Charger le contenu d'une source"""
        if os.path.isfile(source):
            try:
                return Path(source).read_text(errors='ignore')
            except Exception:
                return None
        elif source.startswith('http'):
            try:
                import requests
                return requests.get(source, timeout=10).text
            except Exception:
                return None
        else:
            # C'est déjà du texte
            return source

    def _odeur_dominante(self, molecules: List[Molecule]) -> str:
        """Déterminer l'odeur dominante"""
        if not molecules:
            return Odeur.NEUTRE

        types = [m.type_odeur for m in molecules]
        # Priorité aux odeurs dangereuses
        if Odeur.DANGEREUSE in types:
            return Odeur.DANGEREUSE
        if Odeur.SUSPECTE in types:
            return Odeur.SUSPECTE

        compteur = Counter(types)
        return compteur.most_common(1)[0][0]

    def flairer_processus(self) -> Dict[str, Any]:
        """Flairer les processus en cours"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        suspects = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent']):
            try:
                info = proc.info
                cmdline = ' '.join(info.get('cmdline') or [])

                # Vérifier si suspect
                for recepteur in self.recepteurs:
                    if recepteur.type_detecte in [Odeur.DANGEREUSE, Odeur.SUSPECTE]:
                        molecule = recepteur.detecter(cmdline)
                        if molecule:
                            suspects.append({
                                'pid': info['pid'],
                                'name': info['name'],
                                'cmdline': cmdline[:100],
                                'type': molecule.type_odeur
                            })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            'processus_scannes': len(list(psutil.process_iter())),
            'suspects': suspects,
            'alerte': len(suspects) > 0
        }

    def flairer_reseau(self) -> Dict[str, Any]:
        """Flairer l'activité réseau"""
        if not PSUTIL_DISPO:
            return {'erreur': 'psutil non installé'}

        connexions = []
        for conn in psutil.net_connections(kind='inet'):
            if conn.status == 'ESTABLISHED':
                connexions.append({
                    'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'pid': conn.pid
                })

        # Détecter les ports inhabituels
        ports_suspects = [c for c in connexions if c['remote'] and
                         int(c['remote'].split(':')[1]) in [4444, 5555, 6666, 1337, 31337]]

        return {
            'connexions_actives': len(connexions),
            'connexions': connexions[:20],  # max 20
            'ports_suspects': ports_suspects,
            'alerte': len(ports_suspects) > 0
        }

    def memoriser_odeur(self, signature: str, familiere: bool = True) -> None:
        """Marquer une odeur comme familière"""
        if familiere:
            self.odeurs_familieres.add(signature)
        else:
            self.odeurs_familieres.discard(signature)

    def oublier(self) -> None:
        """Oublier toutes les odeurs mémorisées"""
        self.memoire_olfactive.clear()
        self.odeurs_familieres.clear()

    def moucher(self) -> None:
        """Se moucher - décongestionner"""
        self.congestionne = False

    def congestionner(self) -> None:
        """Congestionner le nez (protection)"""
        self.congestionne = True

    def etat(self) -> Dict[str, Any]:
        """État du système olfactif"""
        return {
            'congestionne': self.congestionne,
            'recepteurs': len(self.recepteurs),
            'memoire': len(self.memoire_olfactive),
            'odeurs_familieres': len(self.odeurs_familieres),
            'psutil_disponible': PSUTIL_DISPO
        }


# Instance globale
nez = Nez()
