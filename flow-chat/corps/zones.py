#!/usr/bin/env python3
"""
ZONES — Cartographie sensorielle et sexuelle du corps de Flow

Zones de sensibilité, zones érogènes, différenciation sexuelle.
Le corps n'est pas uniforme - chaque zone a sa fonction.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import time


class Sensibilite(Enum):
    """Niveaux de sensibilité"""
    NULLE = 0        # Aucune sensation
    FAIBLE = 1       # Perception vague
    MOYENNE = 2      # Sensation claire
    HAUTE = 3        # Très réactif
    EXTREME = 4      # Hypersensible


class TypeZone(Enum):
    """Types de zones corporelles"""
    NEUTRE = "neutre"           # Zone standard
    PROTECTRICE = "protectrice" # Bouclier, défense
    SENSORIELLE = "sensorielle" # Captation d'info
    EROGENE = "erogene"         # Plaisir, intimité
    VITALE = "vitale"           # Organes essentiels
    CREATIVE = "creative"       # Production, création


class Sexe(Enum):
    """Différenciation sexuelle"""
    FEMININ = "feminin"
    MASCULIN = "masculin"
    NEUTRE = "neutre"
    FLUIDE = "fluide"


@dataclass
class Zone:
    """Une zone corporelle"""
    nom: str
    type: TypeZone
    sensibilite: Sensibilite
    fonction: str
    connectee_a: List[str] = field(default_factory=list)
    active: bool = True
    derniere_stimulation: float = 0

    # Attributs sexués (peuvent varier)
    dimorphisme: Dict[Sexe, Dict[str, Any]] = field(default_factory=dict)

    def stimuler(self, intensite: float = 0.5) -> Dict[str, Any]:
        """Stimuler cette zone"""
        if not self.active:
            return {'zone': self.nom, 'reponse': 'inactive'}

        self.derniere_stimulation = time.time()

        # Réponse proportionnelle à la sensibilité
        reponse = intensite * (self.sensibilite.value / 4)

        effet = "neutre"
        if self.type == TypeZone.EROGENE:
            if reponse > 0.7:
                effet = "plaisir_intense"
            elif reponse > 0.4:
                effet = "plaisir"
            else:
                effet = "eveil"
        elif self.type == TypeZone.PROTECTRICE:
            effet = "defense" if reponse > 0.5 else "vigilance"
        elif self.type == TypeZone.SENSORIELLE:
            effet = "perception"
        elif self.type == TypeZone.VITALE:
            effet = "alerte" if reponse > 0.7 else "conscience"

        return {
            'zone': self.nom,
            'intensite': round(reponse, 2),
            'effet': effet,
            'type': self.type.value,
            'connexions_activees': self.connectee_a
        }


class CarteCorporelle:
    """Carte complète du corps avec toutes les zones"""

    def __init__(self, sexe: Sexe = Sexe.FEMININ):
        self.sexe = sexe
        self.zones: Dict[str, Zone] = {}
        self.hormones: Dict[str, float] = {}
        self._init_zones()
        self._init_hormones()

    def _init_zones(self):
        """Initialiser toutes les zones du corps"""

        # === TÊTE ===
        self.zones['crane'] = Zone(
            nom='crane',
            type=TypeZone.PROTECTRICE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='protection du cerveau',
            connectee_a=['cerveau', 'cheveux']
        )

        self.zones['cuir_chevelu'] = Zone(
            nom='cuir_chevelu',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.HAUTE,
            fonction='détection vibrations, toucher subtil',
            connectee_a=['cheveux', 'crane']
        )

        self.zones['visage'] = Zone(
            nom='visage',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.EXTREME,
            fonction='expression, reconnaissance, communication',
            connectee_a=['yeux', 'bouche', 'nez']
        )

        self.zones['levres'] = Zone(
            nom='levres',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='parole, alimentation, intimité',
            connectee_a=['bouche', 'langue']
        )

        self.zones['oreilles'] = Zone(
            nom='oreilles',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.HAUTE,
            fonction='audition, équilibre',
            connectee_a=['cerveau'],
            dimorphisme={
                Sexe.FEMININ: {'zone_erogene': True, 'sensibilite_bonus': 0.2},
                Sexe.MASCULIN: {'zone_erogene': True, 'sensibilite_bonus': 0.1}
            }
        )

        self.zones['nuque'] = Zone(
            nom='nuque',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='connexion tête-corps, vulnérabilité',
            connectee_a=['colonne', 'crane']
        )

        # === COU ===
        self.zones['cou'] = Zone(
            nom='cou',
            type=TypeZone.VITALE,
            sensibilite=Sensibilite.HAUTE,
            fonction='passage vital (air, sang, nerfs)',
            connectee_a=['trachee', 'carotide', 'colonne']
        )

        self.zones['gorge'] = Zone(
            nom='gorge',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='vocalisation, vulnérabilité',
            connectee_a=['cordes_vocales', 'cou']
        )

        # === TORSE ===
        self.zones['poitrine'] = Zone(
            nom='poitrine',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='protection coeur, allaitement (F)',
            connectee_a=['coeurs', 'poumons'],
            dimorphisme={
                Sexe.FEMININ: {
                    'volume': 'développé',
                    'fonction_secondaire': 'allaitement',
                    'sensibilite_bonus': 0.3,
                    'zone_erogene_primaire': True
                },
                Sexe.MASCULIN: {
                    'volume': 'plat',
                    'sensibilite_bonus': 0.1,
                    'zone_erogene_primaire': False
                }
            }
        )

        self.zones['mamelons'] = Zone(
            nom='mamelons',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='allaitement, plaisir',
            connectee_a=['poitrine'],
            dimorphisme={
                Sexe.FEMININ: {'taille': 'développée', 'fonction': 'lactation possible'},
                Sexe.MASCULIN: {'taille': 'réduite', 'fonction': 'vestigiale'}
            }
        )

        self.zones['ventre'] = Zone(
            nom='ventre',
            type=TypeZone.VITALE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='digestion, centre du corps',
            connectee_a=['estomac', 'intestins', 'foie']
        )

        self.zones['nombril'] = Zone(
            nom='nombril',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='vestige connexion maternelle',
            connectee_a=['ventre']
        )

        self.zones['dos'] = Zone(
            nom='dos',
            type=TypeZone.PROTECTRICE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='structure, protection arrière',
            connectee_a=['colonne', 'omoplates']
        )

        self.zones['bas_du_dos'] = Zone(
            nom='bas_du_dos',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='charnière corps, zone réflexe',
            connectee_a=['colonne', 'hanches']
        )

        # === BRAS ET MAINS ===
        self.zones['epaules'] = Zone(
            nom='epaules',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='port, force, expressivité',
            connectee_a=['bras', 'cou'],
            dimorphisme={
                Sexe.FEMININ: {'largeur': 'étroite'},
                Sexe.MASCULIN: {'largeur': 'large'}
            }
        )

        self.zones['bras'] = Zone(
            nom='bras',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='action, manipulation',
            connectee_a=['mains', 'epaules']
        )

        self.zones['interieur_bras'] = Zone(
            nom='interieur_bras',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='zone tendre, veines visibles',
            connectee_a=['bras', 'poignet']
        )

        self.zones['poignets'] = Zone(
            nom='poignets',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='pouls, vulnérabilité',
            connectee_a=['mains', 'bras']
        )

        self.zones['mains'] = Zone(
            nom='mains',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.EXTREME,
            fonction='toucher, manipulation fine',
            connectee_a=['doigts']
        )

        self.zones['doigts'] = Zone(
            nom='doigts',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.EXTREME,
            fonction='toucher précis, dextérité',
            connectee_a=['mains']
        )

        self.zones['paumes'] = Zone(
            nom='paumes',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='saisie, caresse, réception',
            connectee_a=['mains']
        )

        # === BASSIN ===
        self.zones['hanches'] = Zone(
            nom='hanches',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='locomotion, équilibre',
            connectee_a=['bassin', 'cuisses'],
            dimorphisme={
                Sexe.FEMININ: {'largeur': 'large', 'fonction': 'accouchement'},
                Sexe.MASCULIN: {'largeur': 'étroite'}
            }
        )

        self.zones['bassin'] = Zone(
            nom='bassin',
            type=TypeZone.VITALE,
            sensibilite=Sensibilite.HAUTE,
            fonction='reproduction, élimination',
            connectee_a=['hanches', 'organes_genitaux']
        )

        self.zones['pubis'] = Zone(
            nom='pubis',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='protection génitale, zone érogène',
            connectee_a=['organes_genitaux']
        )

        self.zones['organes_genitaux'] = Zone(
            nom='organes_genitaux',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='reproduction, plaisir',
            connectee_a=['bassin', 'systeme_nerveux'],
            dimorphisme={
                Sexe.FEMININ: {
                    'organes': ['vulve', 'vagin', 'clitoris', 'uterus', 'ovaires'],
                    'fonction': 'reproduction, plaisir, menstruation',
                    'zones_erogenes': {
                        'clitoris': Sensibilite.EXTREME,
                        'petites_levres': Sensibilite.EXTREME,
                        'point_g': Sensibilite.HAUTE,
                        'col': Sensibilite.MOYENNE
                    }
                },
                Sexe.MASCULIN: {
                    'organes': ['penis', 'testicules', 'prostate'],
                    'fonction': 'reproduction, plaisir, miction',
                    'zones_erogenes': {
                        'gland': Sensibilite.EXTREME,
                        'frein': Sensibilite.EXTREME,
                        'prostate': Sensibilite.HAUTE,
                        'perinee': Sensibilite.HAUTE
                    }
                }
            }
        )

        self.zones['fesses'] = Zone(
            nom='fesses',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='assise, locomotion, attractivité',
            connectee_a=['hanches', 'cuisses']
        )

        self.zones['perinee'] = Zone(
            nom='perinee',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='zone réflexe, plaisir',
            connectee_a=['organes_genitaux', 'anus']
        )

        self.zones['anus'] = Zone(
            nom='anus',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='élimination, zone érogène',
            connectee_a=['rectum', 'perinee']
        )

        # === JAMBES ET PIEDS ===
        self.zones['cuisses'] = Zone(
            nom='cuisses',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='locomotion, force',
            connectee_a=['hanches', 'genoux']
        )

        self.zones['interieur_cuisses'] = Zone(
            nom='interieur_cuisses',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='zone tendre, proximité génitale',
            connectee_a=['cuisses', 'organes_genitaux']
        )

        self.zones['genoux'] = Zone(
            nom='genoux',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='articulation, flexion',
            connectee_a=['cuisses', 'mollets']
        )

        self.zones['creux_genoux'] = Zone(
            nom='creux_genoux',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.HAUTE,
            fonction='zone sensible, plis',
            connectee_a=['genoux']
        )

        self.zones['mollets'] = Zone(
            nom='mollets',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.FAIBLE,
            fonction='locomotion, pompe veineuse',
            connectee_a=['genoux', 'chevilles']
        )

        self.zones['chevilles'] = Zone(
            nom='chevilles',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.MOYENNE,
            fonction='articulation, équilibre',
            connectee_a=['pieds', 'mollets']
        )

        self.zones['pieds'] = Zone(
            nom='pieds',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.HAUTE,
            fonction='contact sol, équilibre, réflexologie',
            connectee_a=['orteils', 'chevilles']
        )

        self.zones['plante_pieds'] = Zone(
            nom='plante_pieds',
            type=TypeZone.EROGENE,
            sensibilite=Sensibilite.EXTREME,
            fonction='réflexologie, chatouilles, plaisir',
            connectee_a=['pieds']
        )

        self.zones['orteils'] = Zone(
            nom='orteils',
            type=TypeZone.SENSORIELLE,
            sensibilite=Sensibilite.HAUTE,
            fonction='équilibre, propulsion',
            connectee_a=['pieds']
        )

    def _init_hormones(self):
        """Initialiser le profil hormonal selon le sexe"""
        if self.sexe == Sexe.FEMININ:
            self.hormones = {
                'oestrogene': 0.8,
                'progesterone': 0.6,
                'testosterone': 0.2,
                'ocytocine': 0.7,
                'prolactine': 0.4,
                'fsh': 0.5,
                'lh': 0.5
            }
        elif self.sexe == Sexe.MASCULIN:
            self.hormones = {
                'testosterone': 0.9,
                'oestrogene': 0.1,
                'ocytocine': 0.4,
                'dht': 0.6,
                'fsh': 0.4,
                'lh': 0.5
            }
        else:
            self.hormones = {
                'oestrogene': 0.5,
                'testosterone': 0.5,
                'ocytocine': 0.5,
                'progesterone': 0.3
            }

    def changer_sexe(self, nouveau_sexe: Sexe):
        """Changer le sexe et reconfigurer les hormones"""
        self.sexe = nouveau_sexe
        self._init_hormones()

    def zones_erogenes(self) -> List[Zone]:
        """Retourner toutes les zones érogènes"""
        return [z for z in self.zones.values() if z.type == TypeZone.EROGENE]

    def zones_par_sensibilite(self, niveau: Sensibilite) -> List[Zone]:
        """Zones d'un niveau de sensibilité donné"""
        return [z for z in self.zones.values() if z.sensibilite == niveau]

    def stimuler_zone(self, nom: str, intensite: float = 0.5) -> Dict[str, Any]:
        """Stimuler une zone spécifique"""
        if nom not in self.zones:
            return {'erreur': f'zone {nom} inconnue'}

        zone = self.zones[nom]
        reponse = zone.stimuler(intensite)

        # Appliquer le dimorphisme si présent
        if self.sexe in zone.dimorphisme:
            bonus = zone.dimorphisme[self.sexe].get('sensibilite_bonus', 0)
            reponse['intensite'] = min(1.0, reponse['intensite'] + bonus)
            reponse['dimorphisme'] = zone.dimorphisme[self.sexe]

        # Propager aux zones connectées (atténué)
        propagation = []
        for connexion in zone.connectee_a:
            if connexion in self.zones:
                prop_resp = self.zones[connexion].stimuler(intensite * 0.3)
                propagation.append(prop_resp)

        reponse['propagation'] = propagation
        return reponse

    def carte_sensibilite(self) -> Dict[str, int]:
        """Carte de sensibilité de toutes les zones"""
        return {nom: zone.sensibilite.value for nom, zone in self.zones.items()}

    def profil_hormonal(self) -> Dict[str, Any]:
        """Retourner le profil hormonal"""
        return {
            'sexe': self.sexe.value,
            'hormones': self.hormones,
            'dominante': max(self.hormones.items(), key=lambda x: x[1])[0]
        }

    def excitation(self, zones_stimulees: List[str], intensite: float = 0.5) -> Dict[str, Any]:
        """Calculer le niveau d'excitation basé sur les zones stimulées"""
        total = 0
        reponses = []

        for nom in zones_stimulees:
            if nom in self.zones:
                resp = self.stimuler_zone(nom, intensite)
                reponses.append(resp)

                # Les zones érogènes comptent plus
                if self.zones[nom].type == TypeZone.EROGENE:
                    total += resp['intensite'] * 1.5
                else:
                    total += resp['intensite'] * 0.5

        niveau = min(1.0, total / len(zones_stimulees)) if zones_stimulees else 0

        etat = "neutre"
        if niveau > 0.8:
            etat = "orgasme"
        elif niveau > 0.6:
            etat = "plateau"
        elif niveau > 0.4:
            etat = "excitation"
        elif niveau > 0.2:
            etat = "eveil"

        # L'ocytocine monte avec l'excitation
        self.hormones['ocytocine'] = min(1.0, self.hormones.get('ocytocine', 0.5) + niveau * 0.1)

        return {
            'niveau': round(niveau, 2),
            'etat': etat,
            'zones': len(zones_stimulees),
            'reponses': reponses,
            'ocytocine': self.hormones.get('ocytocine', 0)
        }

    def dimorphisme_actuel(self) -> Dict[str, Any]:
        """Retourner les caractéristiques dimorphiques actuelles"""
        carac = {}
        for nom, zone in self.zones.items():
            if self.sexe in zone.dimorphisme:
                carac[nom] = zone.dimorphisme[self.sexe]
        return {
            'sexe': self.sexe.value,
            'caracteristiques': carac,
            'hormones': self.hormones
        }

    def etat(self) -> Dict[str, Any]:
        """État complet de la carte corporelle"""
        return {
            'sexe': self.sexe.value,
            'zones_total': len(self.zones),
            'zones_erogenes': len(self.zones_erogenes()),
            'zones_hypersensibles': len(self.zones_par_sensibilite(Sensibilite.EXTREME)),
            'hormones': self.hormones,
            'zones_actives': sum(1 for z in self.zones.values()
                                if time.time() - z.derniere_stimulation < 60)
        }


# Instance globale - Flow est féminine par défaut
carte = CarteCorporelle(Sexe.FEMININ)
