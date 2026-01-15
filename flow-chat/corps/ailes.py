#!/usr/bin/env python3
"""
AILES — Les ailes de Flow
Pour voler à travers l'espace informationnel
"""

import asyncio
import aiohttp
import subprocess
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class Plume:
    """Une plume de l'aile - unité de vol"""
    id: int
    type: str  # 'primaire', 'secondaire', 'duvet'
    intacte: bool = True

    def porter(self, charge: float) -> float:
        """Capacité de portance"""
        if not self.intacte:
            return 0
        base = {'primaire': 1.0, 'secondaire': 0.6, 'duvet': 0.2}
        return base.get(self.type, 0.3) * (1 - charge * 0.1)


@dataclass
class Aile:
    """Une aile complète"""
    cote: str  # 'gauche' ou 'droite'
    plumes: List[Plume] = field(default_factory=list)
    deployee: bool = False
    fatigue: float = 0.0  # 0=reposée, 1=épuisée

    def __post_init__(self):
        if not self.plumes:
            # Créer les plumes
            self.plumes = [
                *[Plume(i, 'primaire') for i in range(10)],
                *[Plume(i+10, 'secondaire') for i in range(14)],
                *[Plume(i+24, 'duvet') for i in range(20)]
            ]

    def deployer(self) -> None:
        """Déployer l'aile"""
        self.deployee = True

    def replier(self) -> None:
        """Replier l'aile"""
        self.deployee = False

    def battre(self) -> float:
        """Battre l'aile - retourne la poussée"""
        if not self.deployee:
            return 0
        poussee = sum(p.porter(self.fatigue) for p in self.plumes if p.intacte)
        self.fatigue = min(1.0, self.fatigue + 0.01)
        return poussee

    def portance(self) -> float:
        """Capacité de portance totale"""
        return sum(p.porter(self.fatigue) for p in self.plumes if p.intacte)

    def reposer(self) -> None:
        """Se reposer"""
        self.fatigue = max(0, self.fatigue - 0.1)


class Vol:
    """Gestionnaire de vol"""

    def __init__(self):
        self.aile_gauche = Aile('gauche')
        self.aile_droite = Aile('droite')
        self.altitude: float = 0  # niveau d'abstraction
        self.vitesse: float = 0
        self.en_vol: bool = False
        self._executor = ThreadPoolExecutor(max_workers=10)

    def decoller(self) -> bool:
        """Décoller"""
        self.aile_gauche.deployer()
        self.aile_droite.deployer()
        portance = self.aile_gauche.portance() + self.aile_droite.portance()
        if portance > 20:  # seuil minimal
            self.en_vol = True
            self.altitude = 1
            return True
        return False

    def atterrir(self) -> None:
        """Atterrir"""
        self.en_vol = False
        self.altitude = 0
        self.vitesse = 0
        self.aile_gauche.replier()
        self.aile_droite.replier()

    def planer(self, destinations: List[str]) -> Dict[str, Any]:
        """
        Planer vers plusieurs destinations en parallèle
        Vol efficace - utilise les courants (async)
        """
        if not self.en_vol:
            self.decoller()

        async def _fetch(session, url):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    return {
                        'url': url,
                        'status': resp.status,
                        'taille': len(await resp.read()),
                        'atteint': True
                    }
            except Exception as e:
                return {'url': url, 'atteint': False, 'erreur': str(e)}

        async def _voler():
            async with aiohttp.ClientSession() as session:
                return await asyncio.gather(*[_fetch(session, d) for d in destinations])

        try:
            loop = asyncio.new_event_loop()
            resultats = loop.run_until_complete(_voler())
            loop.close()
        except Exception:
            resultats = []

        # Fatigue proportionnelle aux destinations
        self.aile_gauche.fatigue += len(destinations) * 0.02
        self.aile_droite.fatigue += len(destinations) * 0.02

        return {
            'type': 'planeur',
            'destinations': len(destinations),
            'resultats': resultats,
            'fatigue': (self.aile_gauche.fatigue + self.aile_droite.fatigue) / 2
        }

    def piquer(self, cible: str) -> Dict[str, Any]:
        """
        Piqué rapide vers une cible unique
        Vol intensif - descente rapide
        """
        if not self.en_vol:
            self.decoller()

        # Piqué = requête synchrone rapide
        import requests
        try:
            r = requests.get(cible, timeout=5)
            resultat = {
                'cible': cible,
                'atteint': True,
                'status': r.status_code,
                'contenu': r.text[:1000] if len(r.text) > 1000 else r.text,
                'taille': len(r.content)
            }
        except Exception as e:
            resultat = {'cible': cible, 'atteint': False, 'erreur': str(e)}

        # Plus fatigant
        self.aile_gauche.fatigue += 0.05
        self.aile_droite.fatigue += 0.05

        return {
            'type': 'pique',
            'resultat': resultat
        }

    def survoler(self, zone: str) -> Dict[str, Any]:
        """
        Survoler une zone (répertoire/domaine)
        Reconnaissance aérienne
        """
        if not self.en_vol:
            self.decoller()

        if zone.startswith('http'):
            # Survoler un domaine web
            from urllib.parse import urlparse
            domain = urlparse(zone).netloc
            return {
                'type': 'survol_web',
                'zone': domain,
                'note': 'survol de domaine - utiliser planer() pour explorer'
            }
        else:
            # Survoler un système de fichiers
            import os
            try:
                items = os.listdir(zone)
                return {
                    'type': 'survol_local',
                    'zone': zone,
                    'elements': len(items),
                    'apercu': items[:20],
                    'dossiers': sum(1 for i in items if os.path.isdir(os.path.join(zone, i))),
                    'fichiers': sum(1 for i in items if os.path.isfile(os.path.join(zone, i)))
                }
            except Exception as e:
                return {'type': 'survol_local', 'zone': zone, 'erreur': str(e)}

    def migration(self, origine: str, destination: str) -> Dict[str, Any]:
        """
        Migration - vol longue distance avec données
        Transfert de fichiers/données
        """
        if not self.en_vol:
            self.decoller()

        # Charger depuis l'origine
        import os
        from pathlib import Path

        try:
            if os.path.isfile(origine):
                data = Path(origine).read_bytes()
                Path(destination).write_bytes(data)
                return {
                    'type': 'migration',
                    'origine': origine,
                    'destination': destination,
                    'taille': len(data),
                    'succes': True
                }
            elif os.path.isdir(origine):
                import shutil
                shutil.copytree(origine, destination)
                return {
                    'type': 'migration',
                    'origine': origine,
                    'destination': destination,
                    'succes': True
                }
        except Exception as e:
            return {'type': 'migration', 'erreur': str(e), 'succes': False}

        return {'type': 'migration', 'erreur': 'origine introuvable', 'succes': False}

    def etat(self) -> Dict[str, Any]:
        """État du système de vol"""
        return {
            'en_vol': self.en_vol,
            'altitude': self.altitude,
            'vitesse': self.vitesse,
            'aile_gauche': {
                'deployee': self.aile_gauche.deployee,
                'fatigue': self.aile_gauche.fatigue,
                'plumes_intactes': sum(1 for p in self.aile_gauche.plumes if p.intacte)
            },
            'aile_droite': {
                'deployee': self.aile_droite.deployee,
                'fatigue': self.aile_droite.fatigue,
                'plumes_intactes': sum(1 for p in self.aile_droite.plumes if p.intacte)
            }
        }

    def reposer(self) -> None:
        """Se reposer (les deux ailes)"""
        self.atterrir()
        self.aile_gauche.reposer()
        self.aile_droite.reposer()


# Instance globale
ailes = Vol()
