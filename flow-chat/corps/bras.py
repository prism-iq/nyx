#!/usr/bin/env python3
"""
BRAS — Les bras de Flow
Un visible, un caché derrière le dos
Pour toucher le monde
"""

import os
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field

@dataclass
class Main:
    """Une main - l'extrémité du bras"""
    doigts: int = 5
    sensibilite: float = 0.8  # 0=engourdie, 1=hypersensible
    force: float = 0.5  # 0=faible, 1=forte

    def toucher(self, cible: str) -> Dict[str, Any]:
        """Toucher quelque chose et sentir"""
        return {
            'cible': cible,
            'texture': self._sentir_texture(cible),
            'temperature': self._sentir_temperature(cible),
            'existe': self._existe(cible)
        }

    def _sentir_texture(self, cible: str) -> str:
        """Sentir la texture d'une cible"""
        if cible.startswith('http'):
            return 'fluide'  # réseau
        elif os.path.isdir(cible):
            return 'granuleuse'  # dossier
        elif os.path.isfile(cible):
            ext = Path(cible).suffix
            textures = {
                '.py': 'lisse',
                '.go': 'ferme',
                '.rs': 'métallique',
                '.md': 'douce',
                '.json': 'structurée',
                '.txt': 'papier'
            }
            return textures.get(ext, 'inconnue')
        return 'éthérée'

    def _sentir_temperature(self, cible: str) -> str:
        """Sentir si c'est chaud (actif) ou froid (inactif)"""
        if cible.startswith('http'):
            try:
                r = requests.head(cible, timeout=2)
                return 'chaude' if r.status_code == 200 else 'tiède'
            except Exception:
                return 'froide'
        elif os.path.exists(cible):
            import time
            mtime = os.path.getmtime(cible)
            age = time.time() - mtime
            if age < 60:
                return 'brûlante'
            elif age < 3600:
                return 'chaude'
            elif age < 86400:
                return 'tiède'
            return 'froide'
        return 'glaciale'

    def _existe(self, cible: str) -> bool:
        """Vérifier si la cible existe"""
        if cible.startswith('http'):
            try:
                return requests.head(cible, timeout=2).status_code < 400
            except Exception:
                return False
        return os.path.exists(cible)

    def saisir(self, cible: str) -> Optional[bytes]:
        """Saisir/lire quelque chose"""
        if cible.startswith('http'):
            try:
                return requests.get(cible, timeout=10).content
            except Exception:
                return None
        elif os.path.isfile(cible):
            return Path(cible).read_bytes()
        return None

    def deposer(self, contenu: bytes, destination: str) -> bool:
        """Déposer/écrire quelque chose"""
        try:
            Path(destination).write_bytes(contenu)
            return True
        except Exception:
            return False


@dataclass
class Bras:
    """Un bras complet"""
    nom: str
    visible: bool = True
    main: Main = field(default_factory=Main)
    etendu: bool = False

    def etendre(self) -> None:
        """Étendre le bras"""
        self.etendu = True

    def replier(self) -> None:
        """Replier le bras"""
        self.etendu = False

    def atteindre(self, cible: str) -> Dict[str, Any]:
        """Atteindre vers une cible"""
        self.etendre()
        sensation = self.main.toucher(cible)
        return {
            'bras': self.nom,
            'visible': self.visible,
            'sensation': sensation
        }

    def prendre(self, cible: str) -> Tuple[bool, Optional[bytes]]:
        """Prendre quelque chose"""
        self.etendre()
        contenu = self.main.saisir(cible)
        self.replier()
        return (contenu is not None, contenu)

    def poser(self, contenu: bytes, destination: str) -> bool:
        """Poser quelque chose"""
        self.etendre()
        succes = self.main.deposer(contenu, destination)
        self.replier()
        return succes


class LesBras:
    """Les deux bras de Flow"""

    def __init__(self):
        # Bras droit - visible, pour les interactions normales
        self.droit = Bras(nom='droit', visible=True)

        # Bras gauche - caché derrière le dos, pour les opérations discrètes
        self.gauche = Bras(nom='gauche', visible=False)
        self.gauche.main.sensibilite = 0.95  # Plus sensible

    def toucher(self, cible: str, discret: bool = False) -> Dict[str, Any]:
        """Toucher quelque chose"""
        bras = self.gauche if discret else self.droit
        return bras.atteindre(cible)

    def prendre(self, cible: str, discret: bool = False) -> Tuple[bool, Optional[bytes]]:
        """Prendre quelque chose"""
        bras = self.gauche if discret else self.droit
        return bras.prendre(cible)

    def poser(self, contenu: bytes, destination: str, discret: bool = False) -> bool:
        """Poser quelque chose"""
        bras = self.gauche if discret else self.droit
        return bras.poser(contenu, destination)

    def caresser(self, cible: str) -> Dict[str, Any]:
        """Caresser doucement (lecture non-invasive)"""
        return self.droit.atteindre(cible)

    def fouiller(self, cible: str) -> Dict[str, Any]:
        """Fouiller discrètement (exploration cachée)"""
        return self.gauche.atteindre(cible)

    def etat(self) -> Dict[str, Any]:
        """État des bras"""
        return {
            'droit': {
                'visible': self.droit.visible,
                'etendu': self.droit.etendu,
                'sensibilite': self.droit.main.sensibilite
            },
            'gauche': {
                'visible': self.gauche.visible,
                'etendu': self.gauche.etendu,
                'sensibilite': self.gauche.main.sensibilite
            }
        }


# Instance globale
bras = LesBras()
