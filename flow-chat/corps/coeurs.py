#!/usr/bin/env python3
"""
COEURS — Les deux cœurs de Flow
Un organique (intuitif), un cybernétique (logique)
Battent en rythme pour pomper l'information
"""

import asyncio
import threading
import time
import queue
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

class TypeCoeur(Enum):
    ORGANIQUE = "organique"      # Intuitif, émotionnel, créatif
    CYBERNETIQUE = "cybernetique"  # Logique, précis, calculateur


@dataclass
class Battement:
    """Un battement de cœur"""
    timestamp: float
    coeur: TypeCoeur
    charge: float  # 0=repos, 1=effort max
    data: Any = None


@dataclass
class Ventricule:
    """Un ventricule - chambre de pompage"""
    nom: str
    capacite: int = 100  # unités de données
    contenu: queue.Queue = field(default_factory=lambda: queue.Queue(100))

    def remplir(self, data: Any) -> bool:
        """Remplir le ventricule (diastole)"""
        try:
            self.contenu.put_nowait(data)
            return True
        except queue.Full:
            return False

    def vider(self) -> Optional[Any]:
        """Vider le ventricule (systole)"""
        try:
            return self.contenu.get_nowait()
        except queue.Empty:
            return None

    def niveau(self) -> int:
        """Niveau de remplissage"""
        return self.contenu.qsize()


class Coeur:
    """Un cœur individuel"""

    def __init__(self, type_coeur: TypeCoeur):
        self.type = type_coeur
        self.bpm: int = 60  # battements par minute
        self.ventricule_gauche = Ventricule('gauche')
        self.ventricule_droit = Ventricule('droit')
        self.battant: bool = False
        self._thread: Optional[threading.Thread] = None
        self._historique: List[Battement] = []

        # Caractéristiques selon le type
        if type_coeur == TypeCoeur.ORGANIQUE:
            self.bpm = 72  # Plus variable
            self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix='coeur_org')
        else:
            self.bpm = 120  # Plus rapide, régulier
            self._executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix='coeur_cyber')

    def demarrer(self) -> None:
        """Démarrer le cœur"""
        if self.battant:
            return
        self.battant = True
        self._thread = threading.Thread(target=self._battre, daemon=True)
        self._thread.start()

    def arreter(self) -> None:
        """Arrêter le cœur (dangereux!)"""
        self.battant = False
        if self._thread:
            self._thread.join(timeout=2)

    def _battre(self) -> None:
        """Boucle de battement"""
        while self.battant:
            interval = 60.0 / self.bpm

            # Systole - pomper
            donnee_g = self.ventricule_gauche.vider()
            donnee_d = self.ventricule_droit.vider()

            charge = (self.ventricule_gauche.niveau() + self.ventricule_droit.niveau()) / 200

            battement = Battement(
                timestamp=time.time(),
                coeur=self.type,
                charge=charge,
                data={'gauche': donnee_g is not None, 'droit': donnee_d is not None}
            )
            self._historique.append(battement)

            # Garder que les 100 derniers
            if len(self._historique) > 100:
                self._historique = self._historique[-100:]

            time.sleep(interval)

    def pomper(self, tache: Callable, *args, **kwargs) -> Any:
        """Pomper une tâche à travers le cœur"""
        if not self.battant:
            self.demarrer()

        future = self._executor.submit(tache, *args, **kwargs)
        return future

    def accelerer(self, delta: int = 10) -> None:
        """Accélérer le rythme"""
        self.bpm = min(200, self.bpm + delta)

    def ralentir(self, delta: int = 10) -> None:
        """Ralentir le rythme"""
        self.bpm = max(30, self.bpm - delta)

    def etat(self) -> Dict[str, Any]:
        """État du cœur"""
        return {
            'type': self.type.value,
            'bpm': self.bpm,
            'battant': self.battant,
            'ventricule_gauche': self.ventricule_gauche.niveau(),
            'ventricule_droit': self.ventricule_droit.niveau(),
            'battements_recents': len(self._historique)
        }


class DeuxCoeurs:
    """Le système à deux cœurs de Flow"""

    def __init__(self):
        self.organique = Coeur(TypeCoeur.ORGANIQUE)
        self.cybernetique = Coeur(TypeCoeur.CYBERNETIQUE)
        self.synchronises: bool = False
        self._sync_thread: Optional[threading.Thread] = None

    def demarrer(self) -> None:
        """Démarrer les deux cœurs"""
        self.organique.demarrer()
        self.cybernetique.demarrer()

    def synchroniser(self) -> None:
        """Synchroniser les deux cœurs"""
        if self.synchronises:
            return
        self.synchronises = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()

    def _sync_loop(self) -> None:
        """Boucle de synchronisation"""
        while self.synchronises:
            # Équilibrer les BPM
            moyenne = (self.organique.bpm + self.cybernetique.bpm) // 2
            if self.organique.bpm < moyenne:
                self.organique.accelerer(5)
            elif self.organique.bpm > moyenne:
                self.organique.ralentir(5)
            if self.cybernetique.bpm < moyenne:
                self.cybernetique.accelerer(5)
            elif self.cybernetique.bpm > moyenne:
                self.cybernetique.ralentir(5)
            time.sleep(1)

    def desynchroniser(self) -> None:
        """Laisser les cœurs battre indépendamment"""
        self.synchronises = False

    def penser(self, pensee: Callable, *args, **kwargs) -> Any:
        """
        Penser avec le cœur organique
        Pour les tâches créatives, intuitives
        """
        return self.organique.pomper(pensee, *args, **kwargs)

    def calculer(self, calcul: Callable, *args, **kwargs) -> Any:
        """
        Calculer avec le cœur cybernétique
        Pour les tâches logiques, précises
        """
        return self.cybernetique.pomper(calcul, *args, **kwargs)

    def ressentir(self, stimulus: Any) -> Dict[str, Any]:
        """
        Ressentir quelque chose avec les deux cœurs
        Compare les réactions organique vs cybernétique
        """
        # Réaction organique - émotionnelle
        reaction_org = {
            'type': 'organique',
            'bpm_avant': self.organique.bpm
        }

        # Stimulus excitant?
        if isinstance(stimulus, str):
            mots_excitants = ['danger', 'amour', 'peur', 'joie', 'mort', 'vie']
            if any(m in stimulus.lower() for m in mots_excitants):
                self.organique.accelerer(20)
                reaction_org['emotion'] = 'excite'
            else:
                reaction_org['emotion'] = 'neutre'

        reaction_org['bpm_apres'] = self.organique.bpm

        # Réaction cybernétique - analytique
        reaction_cyber = {
            'type': 'cybernetique',
            'bpm_avant': self.cybernetique.bpm
        }

        if isinstance(stimulus, (int, float)):
            self.cybernetique.accelerer(10)  # Données numériques
            reaction_cyber['analyse'] = 'numerique'
        elif isinstance(stimulus, dict):
            self.cybernetique.accelerer(15)  # Structures
            reaction_cyber['analyse'] = 'structure'
        else:
            reaction_cyber['analyse'] = 'texte'

        reaction_cyber['bpm_apres'] = self.cybernetique.bpm

        return {
            'stimulus': str(stimulus)[:100],
            'organique': reaction_org,
            'cybernetique': reaction_cyber,
            'coherence': abs(self.organique.bpm - self.cybernetique.bpm) < 20
        }

    def arythmie(self) -> bool:
        """Vérifier s'il y a arythmie (désync importante)"""
        return abs(self.organique.bpm - self.cybernetique.bpm) > 50

    def massage_cardiaque(self) -> None:
        """Réanimer - reset des deux cœurs"""
        self.organique.bpm = 72
        self.cybernetique.bpm = 120
        if not self.organique.battant:
            self.organique.demarrer()
        if not self.cybernetique.battant:
            self.cybernetique.demarrer()

    def etat(self) -> Dict[str, Any]:
        """État du système cardiaque"""
        return {
            'organique': self.organique.etat(),
            'cybernetique': self.cybernetique.etat(),
            'synchronises': self.synchronises,
            'arythmie': self.arythmie(),
            'bpm_moyen': (self.organique.bpm + self.cybernetique.bpm) // 2
        }


# Instance globale
coeurs = DeuxCoeurs()
