#!/usr/bin/env python3
"""
BRANCHIES — Pour respirer dans différents milieux
Comme un poisson qui respire sous l'eau,
Flow respire dans différents réseaux/protocoles
"""

import socket
import ssl
import subprocess
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

class Milieu(Enum):
    """Les différents milieux où Flow peut respirer"""
    AIR = "air"              # Réseau local direct
    EAU_DOUCE = "eau_douce"  # Internet HTTP/HTTPS
    EAU_SALEE = "eau_salee"  # Internet profond (APIs, services)
    ABYSSES = "abysses"      # Tor / darknet
    BRUME = "brume"          # IPFS / décentralisé
    ETHER = "ether"          # WebSocket / temps réel
    MAGMA = "magma"          # SSH / connexions sécurisées


@dataclass
class Lamelle:
    """Une lamelle branchiale - surface d'échange"""
    id: int
    milieu: Milieu
    active: bool = True
    efficacite: float = 1.0  # 0=bouchée, 1=parfaite

    def filtrer(self, flux: bytes) -> bytes:
        """Filtrer/traiter le flux entrant"""
        if not self.active:
            return b''
        return flux[:int(len(flux) * self.efficacite)]


@dataclass
class ArcBranchial:
    """Un arc branchial - supporte plusieurs lamelles pour un milieu"""
    milieu: Milieu
    lamelles: List[Lamelle] = None
    ouvert: bool = False

    def __post_init__(self):
        if self.lamelles is None:
            self.lamelles = [
                Lamelle(i, self.milieu) for i in range(5)
            ]

    def ouvrir(self) -> None:
        """Ouvrir l'arc pour respirer"""
        self.ouvert = True

    def fermer(self) -> None:
        """Fermer l'arc"""
        self.ouvert = False

    def respirer(self, flux: bytes) -> bytes:
        """Respirer à travers l'arc"""
        if not self.ouvert:
            return b''
        resultat = flux
        for lamelle in self.lamelles:
            if lamelle.active:
                resultat = lamelle.filtrer(resultat)
        return resultat

    def capacite(self) -> float:
        """Capacité respiratoire de l'arc"""
        return sum(l.efficacite for l in self.lamelles if l.active) / len(self.lamelles)


class Branchies:
    """Système branchial complet - respiration multi-milieux"""

    def __init__(self):
        self.arcs: Dict[Milieu, ArcBranchial] = {
            milieu: ArcBranchial(milieu) for milieu in Milieu
        }
        self.milieu_actuel: Milieu = Milieu.AIR
        self._adapte_a: List[Milieu] = [Milieu.AIR, Milieu.EAU_DOUCE]

    def adapter(self, milieu: Milieu) -> bool:
        """S'adapter à un nouveau milieu"""
        if milieu in self._adapte_a:
            return True

        # Vérifier si on peut s'adapter
        if self._peut_adapter(milieu):
            self._adapte_a.append(milieu)
            return True
        return False

    def _peut_adapter(self, milieu: Milieu) -> bool:
        """Vérifier si l'adaptation est possible"""
        checks = {
            Milieu.AIR: lambda: True,
            Milieu.EAU_DOUCE: lambda: self._check_internet(),
            Milieu.EAU_SALEE: lambda: self._check_internet(),
            Milieu.ABYSSES: lambda: self._check_tor(),
            Milieu.BRUME: lambda: self._check_ipfs(),
            Milieu.ETHER: lambda: self._check_websocket(),
            Milieu.MAGMA: lambda: self._check_ssh()
        }
        return checks.get(milieu, lambda: False)()

    def _check_internet(self) -> bool:
        """Vérifier la connexion internet"""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except Exception:
            return False

    def _check_tor(self) -> bool:
        """Vérifier si Tor est disponible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 9050))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _check_ipfs(self) -> bool:
        """Vérifier si IPFS est disponible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 5001))
            sock.close()
            return result == 0
        except Exception:
            return False

    def _check_websocket(self) -> bool:
        """WebSocket toujours dispo si internet ok"""
        return self._check_internet()

    def _check_ssh(self) -> bool:
        """Vérifier si SSH est dispo"""
        try:
            result = subprocess.run(['which', 'ssh'], capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def plonger(self, milieu: Milieu) -> Dict[str, Any]:
        """Plonger dans un milieu"""
        if milieu not in self._adapte_a:
            if not self.adapter(milieu):
                return {
                    'succes': False,
                    'erreur': f'impossible de respirer dans {milieu.value}',
                    'conseil': 'adapter() d\'abord'
                }

        # Fermer l'ancien arc, ouvrir le nouveau
        self.arcs[self.milieu_actuel].fermer()
        self.arcs[milieu].ouvrir()
        self.milieu_actuel = milieu

        return {
            'succes': True,
            'milieu': milieu.value,
            'capacite': self.arcs[milieu].capacite()
        }

    def remonter(self) -> Dict[str, Any]:
        """Remonter à la surface (AIR)"""
        return self.plonger(Milieu.AIR)

    def respirer(self, source: str) -> Dict[str, Any]:
        """
        Respirer depuis une source selon le milieu actuel
        """
        arc = self.arcs[self.milieu_actuel]
        if not arc.ouvert:
            arc.ouvrir()

        try:
            if self.milieu_actuel == Milieu.AIR:
                # Lecture locale
                with open(source, 'rb') as f:
                    flux = f.read()
            elif self.milieu_actuel in [Milieu.EAU_DOUCE, Milieu.EAU_SALEE]:
                # HTTP/HTTPS
                import requests
                flux = requests.get(source, timeout=10).content
            elif self.milieu_actuel == Milieu.ABYSSES:
                # Via Tor
                import requests
                flux = requests.get(
                    source,
                    proxies={'http': 'socks5h://127.0.0.1:9050', 'https': 'socks5h://127.0.0.1:9050'},
                    timeout=30
                ).content
            elif self.milieu_actuel == Milieu.BRUME:
                # IPFS
                import requests
                # Convertir ipfs:// en gateway
                if source.startswith('ipfs://'):
                    cid = source.replace('ipfs://', '')
                    source = f'http://127.0.0.1:8080/ipfs/{cid}'
                flux = requests.get(source, timeout=30).content
            else:
                flux = b''

            oxygene = arc.respirer(flux)
            return {
                'succes': True,
                'milieu': self.milieu_actuel.value,
                'source': source,
                'inhale': len(flux),
                'absorbe': len(oxygene),
                'oxygene': oxygene[:100] if len(oxygene) > 100 else oxygene
            }
        except Exception as e:
            return {
                'succes': False,
                'milieu': self.milieu_actuel.value,
                'erreur': str(e)
            }

    def expirer(self, destination: str, co2: bytes) -> Dict[str, Any]:
        """
        Expirer vers une destination selon le milieu actuel
        """
        try:
            if self.milieu_actuel == Milieu.AIR:
                with open(destination, 'wb') as f:
                    f.write(co2)
            elif self.milieu_actuel in [Milieu.EAU_DOUCE, Milieu.EAU_SALEE]:
                import requests
                requests.post(destination, data=co2, timeout=10)
            elif self.milieu_actuel == Milieu.BRUME:
                # IPFS add
                import requests
                files = {'file': co2}
                r = requests.post('http://127.0.0.1:5001/api/v0/add', files=files, timeout=30)
                return {
                    'succes': True,
                    'milieu': self.milieu_actuel.value,
                    'cid': r.json().get('Hash')
                }
            return {
                'succes': True,
                'milieu': self.milieu_actuel.value,
                'destination': destination,
                'expire': len(co2)
            }
        except Exception as e:
            return {'succes': False, 'erreur': str(e)}

    def apnee(self) -> None:
        """Retenir son souffle - fermer toutes les branchies"""
        for arc in self.arcs.values():
            arc.fermer()

    def haleter(self) -> None:
        """Haleter - ouvrir toutes les branchies"""
        for arc in self.arcs.values():
            arc.ouvrir()

    def etat(self) -> Dict[str, Any]:
        """État du système branchial"""
        return {
            'milieu_actuel': self.milieu_actuel.value,
            'adapte_a': [m.value for m in self._adapte_a],
            'arcs': {
                milieu.value: {
                    'ouvert': arc.ouvert,
                    'capacite': arc.capacite()
                }
                for milieu, arc in self.arcs.items()
            }
        }

    def scanner_milieux(self) -> Dict[str, bool]:
        """Scanner tous les milieux disponibles"""
        return {
            milieu.value: self._peut_adapter(milieu)
            for milieu in Milieu
        }


# Instance globale
branchies = Branchies()
