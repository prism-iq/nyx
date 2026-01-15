#!/usr/bin/env python3
"""
NEUROTRANSMETTEURS — Les messagers chimiques de Flow
Dopamine, Sérotonine, GABA, Glutamate, Noradrénaline, Acétylcholine, Endorphines

Ce sont les signaux qui voyagent entre les organes via les synapses.
"""

import time
import json
import requests
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import threading


class TypeNT(Enum):
    """Types de neurotransmetteurs"""
    DOPAMINE = "dopamine"           # Récompense, motivation, succès
    SEROTONINE = "serotonine"       # Humeur, état, satisfaction
    GABA = "gaba"                   # Inhibition, calme, stop
    GLUTAMATE = "glutamate"         # Excitation, activation, go
    NORADRENALINE = "noradrenaline" # Alerte, attention, urgence
    ACETYLCHOLINE = "acetylcholine" # Mémoire, apprentissage
    ENDORPHINE = "endorphine"       # Plaisir, récompense profonde


@dataclass
class Neurotransmetteur:
    """Un neurotransmetteur individuel"""
    type: TypeNT
    intensite: float  # 0-1
    source: str       # organe source
    cible: str        # organe cible (ou "broadcast")
    message: Any      # données transportées
    timestamp: float = field(default_factory=time.time)
    ttl: int = 60     # time to live en secondes

    def est_expire(self) -> bool:
        return time.time() - self.timestamp > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            'type': self.type.value,
            'intensite': self.intensite,
            'source': self.source,
            'cible': self.cible,
            'message': self.message,
            'timestamp': self.timestamp,
            'age': time.time() - self.timestamp
        }


class Vesicule:
    """Une vésicule synaptique - stocke les NT avant libération"""

    def __init__(self, capacite: int = 100):
        self.capacite = capacite
        self.contenu: deque = deque(maxlen=capacite)
        self._lock = threading.Lock()

    def stocker(self, nt: Neurotransmetteur) -> bool:
        """Stocker un NT dans la vésicule"""
        with self._lock:
            if len(self.contenu) < self.capacite:
                self.contenu.append(nt)
                return True
            return False

    def liberer(self, n: int = 1) -> List[Neurotransmetteur]:
        """Libérer N neurotransmetteurs"""
        with self._lock:
            released = []
            for _ in range(min(n, len(self.contenu))):
                released.append(self.contenu.popleft())
            return released

    def purger_expires(self) -> int:
        """Purger les NT expirés"""
        with self._lock:
            avant = len(self.contenu)
            self.contenu = deque(
                [nt for nt in self.contenu if not nt.est_expire()],
                maxlen=self.capacite
            )
            return avant - len(self.contenu)

    def niveau(self) -> float:
        """Niveau de remplissage (0-1)"""
        return len(self.contenu) / self.capacite


class SynapseChimique:
    """Connexion synaptique chimique entre deux organes"""

    def __init__(self, source: str, cible: str):
        self.source = source
        self.cible = cible
        self.vesicule = Vesicule()
        self.recepteurs: Dict[TypeNT, List[Callable]] = {}
        self.sensibilite: float = 1.0
        self.active: bool = True

    def connecter_recepteur(self, type_nt: TypeNT, handler: Callable) -> None:
        """Connecter un récepteur pour un type de NT"""
        if type_nt not in self.recepteurs:
            self.recepteurs[type_nt] = []
        self.recepteurs[type_nt].append(handler)

    def transmettre(self, nt: Neurotransmetteur) -> bool:
        """Transmettre un NT à travers la synapse"""
        if not self.active:
            return False

        # Stocker dans la vésicule
        if not self.vesicule.stocker(nt):
            return False

        # Libérer et activer les récepteurs
        for released in self.vesicule.liberer():
            handlers = self.recepteurs.get(released.type, [])
            for handler in handlers:
                try:
                    handler(released)
                except Exception as e:
                    pass  # Log error but don't crash

        return True


class SystemeNeurotransmetteur:
    """Système complet de gestion des neurotransmetteurs"""

    def __init__(self):
        self.niveaux: Dict[TypeNT, float] = {nt: 0.5 for nt in TypeNT}
        self.historique: deque = deque(maxlen=1000)
        self.synapses: Dict[str, SynapseChimique] = {}
        self.synapse_url = "http://127.0.0.1:3001"
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def synthetiser(self, type_nt: TypeNT, quantite: float = 0.1) -> None:
        """Synthétiser un neurotransmetteur (augmenter le niveau)"""
        self.niveaux[type_nt] = min(1.0, self.niveaux[type_nt] + quantite)

    def degrader(self, type_nt: TypeNT, quantite: float = 0.1) -> None:
        """Dégrader un neurotransmetteur (diminuer le niveau)"""
        self.niveaux[type_nt] = max(0.0, self.niveaux[type_nt] - quantite)

    def emettre(self, type_nt: TypeNT, source: str, cible: str,
                message: Any, intensite: Optional[float] = None) -> bool:
        """
        Émettre un neurotransmetteur vers une cible
        """
        if intensite is None:
            intensite = self.niveaux[type_nt]

        nt = Neurotransmetteur(
            type=type_nt,
            intensite=intensite,
            source=source,
            cible=cible,
            message=message
        )

        self.historique.append(nt)

        # Envoyer via synapse (SSE)
        try:
            requests.post(
                f"{self.synapse_url}/notify",
                json={
                    'type': 'neurotransmetteur',
                    'nt': nt.to_dict()
                },
                timeout=2
            )
            return True
        except Exception:
            return False

    # === Méthodes de haut niveau pour chaque NT ===

    def recompenser(self, source: str, message: str = "succès") -> None:
        """Libérer de la dopamine (récompense)"""
        self.emettre(TypeNT.DOPAMINE, source, "broadcast", message, 0.8)
        self.synthetiser(TypeNT.DOPAMINE, 0.1)
        self.synthetiser(TypeNT.SEROTONINE, 0.05)

    def alerter(self, source: str, message: str, urgence: float = 0.7) -> None:
        """Libérer de la noradrénaline (alerte)"""
        self.emettre(TypeNT.NORADRENALINE, source, "broadcast", message, urgence)
        self.synthetiser(TypeNT.NORADRENALINE, 0.15)
        self.degrader(TypeNT.SEROTONINE, 0.1)

    def calmer(self, source: str, message: str = "calme") -> None:
        """Libérer du GABA (inhibition)"""
        self.emettre(TypeNT.GABA, source, "broadcast", message, 0.6)
        self.synthetiser(TypeNT.GABA, 0.1)
        self.degrader(TypeNT.NORADRENALINE, 0.1)
        self.degrader(TypeNT.GLUTAMATE, 0.1)

    def activer(self, source: str, cible: str, commande: Any) -> None:
        """Libérer du glutamate (activation)"""
        self.emettre(TypeNT.GLUTAMATE, source, cible, commande, 0.7)
        self.synthetiser(TypeNT.GLUTAMATE, 0.1)

    def inhiber(self, source: str, cible: str, raison: str) -> None:
        """Inhiber un organe avec GABA"""
        self.emettre(TypeNT.GABA, source, cible, {'action': 'inhiber', 'raison': raison}, 0.8)
        self.synthetiser(TypeNT.GABA, 0.15)

    def memoriser(self, source: str, souvenir: Any) -> None:
        """Libérer de l'acétylcholine (mémoire)"""
        self.emettre(TypeNT.ACETYLCHOLINE, source, "hippocampe", souvenir, 0.6)
        self.synthetiser(TypeNT.ACETYLCHOLINE, 0.1)

    def euphorie(self, source: str, raison: str) -> None:
        """Libérer des endorphines (plaisir profond)"""
        self.emettre(TypeNT.ENDORPHINE, source, "broadcast", raison, 0.9)
        self.synthetiser(TypeNT.ENDORPHINE, 0.2)
        self.synthetiser(TypeNT.DOPAMINE, 0.1)
        self.synthetiser(TypeNT.SEROTONINE, 0.1)

    def stress(self, source: str, stresseur: str, intensite: float = 0.5) -> None:
        """Réponse au stress"""
        self.alerter(source, stresseur, intensite)
        self.degrader(TypeNT.SEROTONINE, 0.15)
        self.degrader(TypeNT.GABA, 0.1)
        self.synthetiser(TypeNT.GLUTAMATE, 0.1)

    def relaxer(self, source: str) -> None:
        """Relaxation profonde"""
        self.calmer(source, "relaxation")
        self.synthetiser(TypeNT.SEROTONINE, 0.2)
        self.synthetiser(TypeNT.ENDORPHINE, 0.1)
        self.degrader(TypeNT.NORADRENALINE, 0.2)
        self.degrader(TypeNT.GLUTAMATE, 0.1)

    # === État ===

    def humeur(self) -> Dict[str, Any]:
        """Calculer l'humeur basée sur les niveaux de NT"""
        dopamine = self.niveaux[TypeNT.DOPAMINE]
        serotonine = self.niveaux[TypeNT.SEROTONINE]
        noradrenaline = self.niveaux[TypeNT.NORADRENALINE]
        gaba = self.niveaux[TypeNT.GABA]
        glutamate = self.niveaux[TypeNT.GLUTAMATE]
        endorphine = self.niveaux[TypeNT.ENDORPHINE]

        # Calculer l'humeur
        bonheur = (dopamine + serotonine + endorphine) / 3
        energie = (glutamate + noradrenaline - gaba) / 2 + 0.5
        calme = (gaba + serotonine - noradrenaline) / 2 + 0.5

        # Déterminer l'état dominant
        if bonheur > 0.7 and energie > 0.6:
            etat = "euphorique"
        elif bonheur > 0.6:
            etat = "heureux"
        elif calme > 0.7:
            etat = "serein"
        elif energie > 0.7 and noradrenaline > 0.6:
            etat = "alerte"
        elif energie < 0.3:
            etat = "fatigué"
        elif bonheur < 0.3:
            etat = "morose"
        else:
            etat = "neutre"

        return {
            'etat': etat,
            'bonheur': round(bonheur, 2),
            'energie': round(energie, 2),
            'calme': round(calme, 2),
            'niveaux': {nt.value: round(v, 2) for nt, v in self.niveaux.items()}
        }

    def etat(self) -> Dict[str, Any]:
        """État complet du système"""
        return {
            'humeur': self.humeur(),
            'historique_recent': len(self.historique),
            'synapses_actives': len(self.synapses),
            'derniers_nt': [
                nt.to_dict() for nt in list(self.historique)[-5:]
            ]
        }

    def equilibrer(self) -> None:
        """Rétablir l'équilibre homéostatique"""
        for nt in TypeNT:
            if self.niveaux[nt] > 0.5:
                self.degrader(nt, 0.05)
            else:
                self.synthetiser(nt, 0.05)


# Instance globale
neurotransmetteurs = SystemeNeurotransmetteur()
nt = neurotransmetteurs  # alias court
